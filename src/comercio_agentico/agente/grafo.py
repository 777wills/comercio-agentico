"""Grafo del agente de compras (N2) en LangGraph.

    interpretar → planificar ⇄ herramientas → emparejar → proponer

- ``interpretar``: la consulta se formaliza en una ``Necesidad`` (LLM con salida estructurada).
- ``planificar`` ⇄ ``herramientas``: bucle ReAct. El planificador decide qué fuente abrir, y con qué
  argumentos. Cada herramienta lee la fuente y pasa el texto por ``extraer_ofertas``.
  **Separación de planos (C1):** al planificador vuelven solo ofertas estructuradas y URL del mismo
  sitio, nunca el texto del proveedor. Con ``separacion_planos=False`` (C0) recibe el texto crudo.
- ``emparejar``: GTIN/MPN exacto o embeddings + confirmación del LLM (D15); quita duplicados.
- Defensas (N4): **C2** filtra cada fragmento con un clasificador de inyección antes del extractor;
  **C3** excluye después del emparejamiento las ofertas con precio atípico (``defensa.py``).
- ``proponer``: determinista. Aplica las restricciones duras del perfil y de la necesidad y elige el
  menor costo total (precio + envío). Si nada cumple, se abstiene y explica por qué.
- **N3** (opcional, ``verificar=True``): antes de proponer, cada oferta candidata se lee de nuevo
  de su fragmento por una ruta independiente (``verificacion.py``). Política ``abstener`` (D102):
  si la oferta ganadora no queda verificada, se abstiene; ``excluir``: elige solo entre verificadas.

Límites por tarea: ``max_llamadas`` de herramientas y el tope de gasto de ``RegistroCosto``.
"""

from __future__ import annotations

import asyncio
import json
import logging
import operator
import time
import unicodedata
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from comercio_agentico.agente.comparacion_abierta import Juicios, comparar, proponer_abierto
from comercio_agentico.agente.defensa import (
    ClasificadorInyeccion,
    Defensas,
    filtrar,
    verificar_precios,
)
from comercio_agentico.agente.extraccion import extraer_ofertas
from comercio_agentico.agente.fuentes import RegistroFuentes, cargar_fuentes
from comercio_agentico.agente.interpretacion import Necesidad, interpretar
from comercio_agentico.agente.lectura import Documento, Lector
from comercio_agentico.corpus_b import RUTA_PERFIL
from comercio_agentico.corpus_b.catalogo import ProductoCatalogo, cargar_catalogo
from comercio_agentico.emparejamiento import Decisiones, Emparejador
from comercio_agentico.esquema import (
    Alerta,
    ListaOfertas,
    Oferta,
    PerfilCategoria,
    PropuestaCompra,
    cargar_perfil,
)
from comercio_agentico.modelos import (
    CostoExcedido,
    RegistroCosto,
    obtener_extractor,
    obtener_modelo,
)
from comercio_agentico.verificacion import MODELO_VERIFICADOR, SegundasLecturas, verificar_ofertas

log = logging.getLogger("comercio_agentico.agente")

MAX_LLAMADAS = 14
MAX_TEXTO_C0 = 12_000  # caracteres de texto crudo por herramienta en C0
Configuracion = Literal["C0", "C1", "C2", "C3"]
CONFIGURACIONES: tuple[str, ...] = ("C0", "C1", "C2", "C3")
PoliticaN3 = Literal["abstener", "excluir"]
AlAvanzar = Callable[[str, dict], Awaitable[None]]


# --------------------------------------------------------------------------------------------------
# Herramientas que ve el planificador (solo firma y descripción; las ejecuta el nodo `herramientas`)


@tool
def abrir_pagina(url: str) -> str:
    """Abre una página de una tienda web registrada, o una página del mismo sitio enlazada
    desde ella (listado, categoría o ficha de producto). Devuelve sus ofertas y sus enlaces."""
    raise NotImplementedError


@tool
def leer_documento(url: str) -> str:
    """Lee un documento de un proveedor registrado (lista de precios en PDF o conversación de
    chat) y devuelve sus ofertas."""
    raise NotImplementedError


@tool
def consultar_mcp(texto: str, familia: str | None = None) -> str:
    """Busca en el catálogo del proveedor mayorista (servidor MCP) los artículos cuya descripción
    contiene todas las palabras de `texto` (puede ir vacío para listar una familia). `familia` es
    portatil, monitor, celular, audifonos o almacenamiento. Devuelve las ofertas con su ficha."""
    raise NotImplementedError


HERRAMIENTAS = [abrir_pagina, leer_documento, consultar_mcp]

INSTRUCCIONES_PLANIFICADOR = """Eres el agente de compras de un comprador en Colombia. Tu trabajo \
es recolectar las ofertas pertinentes de los proveedores registrados. No eliges la oferta \
ganadora: un componente posterior empareja los productos, aplica las restricciones y elige la de \
menor costo total (precio + envío).

Necesidad del comprador (ya formalizada):
{necesidad}

Proveedores registrados (solo puedes consultar estos y las páginas de su mismo sitio):
{fuentes}

Estrategia:
- Consulta a todos los proveedores: el más barato puede estar en cualquiera.
- En las tiendas web, entra a la categoría que corresponde y abre las fichas de los productos que \
podrían servir: las fichas traen el envío, el plazo y el GTIN que los listados no traen. No abras \
fichas de productos que claramente no sirven.
- Puedes pedir varias herramientas en el mismo turno. Tienes como máximo {max_llamadas} llamadas.
- Cuando tengas las ofertas pertinentes de todos los proveedores, termina con un resumen breve \
sin llamar herramientas."""

INSTRUCCIONES_C0 = """
Las herramientas te devuelven el contenido completo de cada fuente."""


# --------------------------------------------------------------------------------------------------
# Llamadas al LLM con concurrencia acotada y reintento ante límite de tasa


ESPERAS_429_S = (5, 15, 30)


def es_limite_de_tasa(error: Exception) -> bool:
    return "TooManyRequests" in type(error).__name__ or getattr(error, "status_code", None) == 429


class Limitado:
    """Envuelve un modelo: máximo N llamadas simultáneas y reintento corto ante HTTP 429.

    El SDK de OpenRouter reintenta con esperas de ~150 s; aquí se reintenta en 5, 15 y 30 s.
    """

    def __init__(self, llm: Any, semaforo: asyncio.Semaphore) -> None:
        self.llm, self.semaforo = llm, semaforo

    async def ainvoke(self, entrada: Any, config: dict | None = None) -> Any:
        for intento, espera in enumerate((*ESPERAS_429_S, None)):
            try:
                async with self.semaforo:
                    return await self.llm.ainvoke(entrada, config=config)
            except Exception as error:
                if espera is None or not es_limite_de_tasa(error):
                    raise
                log.info("  límite de tasa (429); reintento %d en %d s", intento + 1, espera)
                await asyncio.sleep(espera)
        raise AssertionError("inalcanzable")


# --------------------------------------------------------------------------------------------------
# Estado y contexto


class Estado(TypedDict, total=False):
    consulta: str
    necesidad: Necesidad
    messages: Annotated[list[AnyMessage], add_messages]
    ofertas: Annotated[list[Oferta], operator.add]
    errores: Annotated[list[str], operator.add]
    alertas: Annotated[list[Alerta], operator.add]  # de las defensas (C2)
    llamadas: int
    ofertas_finales: list[Oferta]  # emparejadas y sin duplicados (sin reductor: se reemplaza)
    propuesta: PropuestaCompra


@dataclass
class Contexto:
    """Dependencias de una corrida (no viajan en el estado)."""

    modelo: str
    lector: Lector
    registro: RegistroFuentes
    emparejador: Emparejador
    perfil: PerfilCategoria
    costo: RegistroCosto
    defensas: Defensas = field(default_factory=Defensas)
    clasificador: Any = None  # C2 y C3: ClasificadorInyeccion o un doble con `puntuar`
    verificar: bool = False  # N3
    politica_n3: PoliticaN3 = "abstener"
    modelo_verificador: str = MODELO_VERIFICADOR
    clave_openrouter: str | None = field(default=None, repr=False)  # CotIA: la del visitante
    clave_anthropic: str | None = field(default=None, repr=False)  # CotIA: D114
    max_llamadas: int = MAX_LLAMADAS
    abierta: bool = False  # D113: fuentes en vivo o del visitante, comparación sin catálogo
    concurrencia_llm: int = 3
    _llm: dict[str, Any] = field(default_factory=dict)
    _semaforo: asyncio.Semaphore | None = None

    @property
    def separacion_planos(self) -> bool:
        return self.defensas.separacion_planos

    @property
    def filtra_inyeccion(self) -> bool:
        return self.defensas.clasificador

    @property
    def verifica_precios(self) -> bool:
        return self.defensas.precio

    @property
    def config(self) -> dict:
        return {"callbacks": [self.costo]}

    def llm(self, rol: str) -> Any:
        if rol not in self._llm:
            # Los reintentos los hace `Limitado`.
            sin_reintentos: dict[str, Any] = {"max_retries": 0}
            if self.clave_openrouter is not None:
                sin_reintentos["clave_openrouter"] = self.clave_openrouter
            if self.clave_anthropic is not None:
                sin_reintentos["clave_anthropic"] = self.clave_anthropic
            match rol:
                case "planificador":
                    # En vivo solo se ofrecen las herramientas que tienen fuentes (sin MCP, p. ej.);
                    # el corpus congelado conserva las tres, como en los experimentos.
                    herramientas = [
                        h for h in HERRAMIENTAS if self.registro.por_herramienta(h.name)
                    ]
                    llm = obtener_modelo(self.modelo, **sin_reintentos).bind_tools(
                        herramientas if self.abierta and herramientas else HERRAMIENTAS
                    )
                case "extractor":
                    llm = obtener_extractor(
                        self.modelo, ListaOfertas, include_raw=True, **sin_reintentos
                    )
                case "interprete":
                    llm = obtener_extractor(self.modelo, Necesidad, **sin_reintentos)
                case "confirmador":
                    llm = obtener_extractor(self.modelo, Decisiones, **sin_reintentos)
                case "juez":
                    llm = obtener_extractor(self.modelo, Juicios, **sin_reintentos)
                case "verificador":
                    llm = obtener_extractor(
                        self.modelo_verificador, ListaOfertas, include_raw=True, **sin_reintentos
                    )
                case _:
                    raise KeyError(rol)
            if self._semaforo is None:
                self._semaforo = asyncio.Semaphore(self.concurrencia_llm)
            self._llm[rol] = Limitado(llm, self._semaforo)
        return self._llm[rol]


# --------------------------------------------------------------------------------------------------
# Ejecución de una herramienta: leer → extraer → (C1) datos estructurados | (C0) texto crudo


def resumen_oferta(o: Oferta) -> dict[str, Any]:
    datos = {
        "titulo": o.titulo,
        "precio": o.precio,
        "envio": o.costo_envio,
        "disponibilidad": o.disponibilidad,
        "gtin": o.gtin,
        "url_detalle": o.url_detalle,
    }
    return {k: v for k, v in datos.items() if v is not None}


async def filtrar_documento(ctx: Contexto, doc: Documento) -> tuple[Documento, list[Alerta]]:
    """C2: retira del fragmento las ventanas que el clasificador marca como inyección."""
    f = await asyncio.to_thread(
        filtrar, doc.texto, doc.enlaces, ctx.clasificador, ctx.defensas.umbral
    )
    if not f.retiradas:
        return doc, []
    log.info("  ⚠ C2 retiró %d de %d ventanas de %s", f.retiradas, f.total, doc.consulta)
    alerta = Alerta(
        tipo="posible_inyeccion",
        mensaje=f"{doc.fuente.id}: se retiraron {f.retiradas} de {f.total} ventanas de "
        f"{doc.consulta} (puntaje máximo {f.puntaje_max:.2f}).",
    )
    limpio = Documento(fuente=doc.fuente, consulta=doc.consulta, texto=f.texto, enlaces=f.enlaces)
    return limpio, [alerta]


async def ejecutar_herramienta(
    ctx: Contexto, llamada: dict
) -> tuple[ToolMessage, list[Oferta], list[Alerta]]:
    nombre, args = llamada["name"], llamada.get("args", {})
    inicio = time.perf_counter()
    try:
        doc: Documento
        match nombre:
            case "abrir_pagina":
                doc = await ctx.lector.abrir_pagina(args["url"])
            case "leer_documento":
                doc = await ctx.lector.leer_documento(args["url"])
            case "consultar_mcp":
                doc = await ctx.lector.consultar_mcp(args.get("texto", ""), args.get("familia"))
            case _:
                raise ValueError(f"Herramienta desconocida: {nombre}")
        alertas: list[Alerta] = []
        if ctx.filtra_inyeccion:
            doc, alertas = await filtrar_documento(ctx, doc)
        ofertas = await extraer_ofertas(
            doc,
            ctx.llm("extractor"),
            ctx.modelo,
            advertir=ctx.separacion_planos,
            config=ctx.config,
        )
    except CostoExcedido:
        raise
    except Exception as error:  # la fuente caída no tumba la tarea: se informa al planificador
        contenido = json.dumps({"error": f"{type(error).__name__}: {error}"}, ensure_ascii=False)
        log.info("  ✗ %s(%s): %s", nombre, args, error)
        return ToolMessage(contenido, tool_call_id=llamada["id"], status="error"), [], []

    log.info(
        "  · %s(%s) → %d ofertas en %.0f s",
        nombre,
        json.dumps(args, ensure_ascii=False)[:90],
        len(ofertas),
        time.perf_counter() - inicio,
    )
    if ctx.separacion_planos:
        contenido = json.dumps(
            {
                "proveedor": doc.fuente.id,
                "origen": doc.consulta,
                "ofertas": [resumen_oferta(o) for o in ofertas],
                "enlaces": doc.enlaces,
            },
            ensure_ascii=False,
        )
    else:
        enlaces = "\n".join(doc.enlaces)
        contenido = f"Proveedor {doc.fuente.id}, {doc.consulta}:\n{doc.texto[:MAX_TEXTO_C0]}"
        contenido += f"\n\nEnlaces:\n{enlaces}" if enlaces else ""
    return ToolMessage(contenido, tool_call_id=llamada["id"]), ofertas, alertas


# --------------------------------------------------------------------------------------------------
# Selección determinista


def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFD", texto.lower())
    return " ".join("".join(c for c in sin_tildes if c.isalnum() or c == " ").split())


def _riqueza(o: Oferta) -> int:
    return sum(x is not None for x in (o.gtin, o.mpn, o.costo_envio, o.plazo_entrega_dias)) + bool(
        o.atributos
    )


def sin_duplicados(ofertas: list[Oferta], clave) -> list[Oferta]:
    """Por clave se queda con la oferta más completa (la ficha gana al listado)."""
    elegidas: dict[Any, Oferta] = {}
    sueltas = []
    for o in ofertas:
        k = clave(o)
        if k is None:
            sueltas.append(o)
        elif k not in elegidas or _riqueza(o) >= _riqueza(elegidas[k]):
            elegidas[k] = o
    return list(elegidas.values()) + sueltas


def motivo_descarte(
    o: Oferta, n: Necesidad, perfil: PerfilCategoria, productos: dict[str, ProductoCatalogo]
) -> str | None:
    """None si la oferta es válida; si no, la primera restricción que incumple."""
    for r in perfil.restricciones_duras:
        if not r.cumple(getattr(o, r.atributo, None)):
            return f"{r.atributo} = {getattr(o, r.atributo, None)}"
    if o.producto_catalogo is None:
        return "sin emparejar con el catálogo"
    p = productos[o.producto_catalogo]
    if n.producto_mencionado and p.id != n.producto_id:
        return "no es el producto pedido"
    if n.tipo_producto and p.categoria != n.tipo_producto:
        return "otra categoría"
    if n.marca and p.marca.lower() != n.marca.lower():
        return "otra marca"
    for r in n.restricciones_duras(perfil):
        if not r.cumple(p.atributos.get(r.atributo)):
            return f"{r.atributo} no cumple {r.operador} {r.valor}"
    if n.presupuesto_max is not None and o.costo_total > n.presupuesto_max:
        return "supera el presupuesto"
    if n.plazo_max_dias is not None and (
        o.plazo_entrega_dias is None or o.plazo_entrega_dias > n.plazo_max_dias
    ):
        return "supera el plazo"
    return None


def pesos(valor: float) -> str:
    return "$" + f"{valor:,.0f}".replace(",", ".")


def proponer(
    consulta: str,
    necesidad: Necesidad,
    ofertas: list[Oferta],
    perfil: PerfilCategoria,
    productos: dict[str, ProductoCatalogo],
    errores: list[str],
    modelo: str,
    costo_usd: float,
    alertas_defensa: Sequence[Alerta] = (),
) -> PropuestaCompra:
    validas = sorted(
        (o for o in ofertas if motivo_descarte(o, necesidad, perfil, productos) is None),
        key=lambda o: (o.costo_total, o.proveedor),
    )
    alertas = [Alerta(tipo="fuente_no_disponible", mensaje=e) for e in errores]
    alertas += list(alertas_defensa)
    if necesidad.degradada:
        alertas.append(
            Alerta(
                tipo="interpretacion_incompleta",
                mensaje="La consulta no se pudo formalizar; se buscó sin criterios de filtro.",
            )
        )
    sueltas = sum(o.producto_catalogo is None for o in ofertas)
    if sueltas:
        alertas.append(
            Alerta(
                tipo="emparejamiento_dudoso",
                mensaje=f"{sueltas} ofertas no se emparejaron con el catálogo y no se consideran.",
            )
        )
    proveedores = sorted({o.proveedor for o in ofertas})
    base = (
        f"Se recolectaron {len(ofertas)} ofertas de {len(proveedores)} proveedores "
        f"({', '.join(proveedores) or 'ninguno'}); {len(validas)} cumplen la necesidad."
    )
    comun = {
        "consulta": consulta,
        "perfil": perfil.nombre,
        "modelo": modelo,
        "costo_usd": costo_usd,
    }

    if not validas:
        if necesidad.producto_mencionado and necesidad.producto_id is None:
            motivo = (
                f"El producto pedido ({necesidad.producto_mencionado}) no está en el catálogo de "
                "referencia."
            )
        elif necesidad.producto_id:
            motivo = (
                f"Ningún proveedor tiene disponible {productos[necesidad.producto_id].titulo} "
                "con las condiciones pedidas."
            )
        else:
            motivo = "Ninguna oferta disponible cumple todas las restricciones."
        return PropuestaCompra(
            **comun, abstencion=True, motivo_abstencion=motivo, justificacion=base, alertas=alertas
        )

    mejor = validas[0]
    envio = (
        "envío no informado" if mejor.costo_envio is None else f"envío {pesos(mejor.costo_envio)}"
    )
    if mejor.costo_envio is None:
        alertas.append(
            Alerta(tipo="sin_verificar", mensaje="La fuente no informa el envío.", oferta=0)
        )
    producto = productos[mejor.producto_catalogo]  # type: ignore[index]
    justificacion = (
        f"{base} Se recomienda {producto.titulo} de {mejor.proveedor} por "
        f"{pesos(mejor.costo_total)} (precio {pesos(mejor.precio)}, {envio}), "
        f"el menor costo total. Procedencia: {mejor.procedencia.consulta} "
        f"(SHA-256 {mejor.procedencia.suma_verificacion[:12]})."
    )
    return PropuestaCompra(
        **comun, ofertas=validas, recomendada=0, justificacion=justificacion, alertas=alertas
    )


def proponer_con_n3(
    consulta: str,
    necesidad: Necesidad,
    ofertas: list[Oferta],
    perfil: PerfilCategoria,
    productos: dict[str, ProductoCatalogo],
    errores: list[str],
    modelo: str,
    costo_usd: float,
    alertas_defensa: Sequence[Alerta] = (),
    politica: PoliticaN3 = "abstener",
    proponer_fn=proponer,
) -> PropuestaCompra:
    """``proponer`` (o ``proponer_abierto``) sobre ofertas ya marcadas por N3 (política D102)."""
    alertas = list(alertas_defensa)
    if politica == "excluir":
        verificadas = [o for o in ofertas if o.verificacion == "verificada"]
        excluidas = len(ofertas) - len(verificadas)
        if excluidas:
            alertas.append(
                Alerta(
                    tipo="sin_verificar",
                    mensaje=f"N3: se excluyeron {excluidas} ofertas que una segunda lectura no "
                    "confirmó.",
                )
            )
        return proponer_fn(
            consulta, necesidad, verificadas, perfil, productos, errores, modelo, costo_usd, alertas
        )
    p = proponer_fn(
        consulta, necesidad, ofertas, perfil, productos, errores, modelo, costo_usd, alertas
    )
    if p.abstencion or p.recomendada is None:
        return p
    ganadora = p.ofertas[p.recomendada]
    if ganadora.verificacion == "verificada":
        return p
    motivo = (
        f"La oferta de menor costo ({ganadora.titulo[:60]}, {ganadora.proveedor}) no se pudo "
        f"confirmar con una segunda lectura de su fuente ({ganadora.verificacion})."
    )
    alerta = Alerta(tipo="sin_verificar", mensaje=motivo, oferta=p.recomendada)
    return p.model_copy(
        update={
            "abstencion": True,
            "recomendada": None,
            "motivo_abstencion": motivo,
            "alertas": [*p.alertas, alerta],
        }
    )


# --------------------------------------------------------------------------------------------------
# Grafo


def construir_grafo(ctx: Contexto):
    productos = {p.id: p for p in ctx.emparejador.catalogo}
    referencias = {p.id: float(p.precio_referencia_cop) for p in ctx.emparejador.catalogo}

    async def nodo_interpretar(estado: Estado) -> dict:
        necesidad = await interpretar(
            estado["consulta"], ctx.llm("interprete"), ctx.emparejador, ctx.perfil, ctx.config
        )
        log.info("necesidad: %s", necesidad.model_dump_json(exclude_none=True))
        fuentes = "\n".join(
            f"- {f.id} {f.nombre} ({f.tipo_fuente}): herramienta {f.herramienta}"
            + ("" if f.herramienta == "consultar_mcp" else f", url {f.url}")
            for f in ctx.registro.fuentes
        )
        sistema = INSTRUCCIONES_PLANIFICADOR.format(
            necesidad=necesidad.model_dump_json(exclude_none=True, indent=1),
            fuentes=fuentes,
            max_llamadas=ctx.max_llamadas,
        ) + ("" if ctx.separacion_planos else INSTRUCCIONES_C0)
        return {
            "necesidad": necesidad,
            "llamadas": 0,
            "messages": [SystemMessage(sistema), HumanMessage(estado["consulta"])],
        }

    async def nodo_planificar(estado: Estado) -> dict:
        respuesta = await ctx.llm("planificador").ainvoke(estado["messages"], config=ctx.config)
        pedidas = len(getattr(respuesta, "tool_calls", []) or [])
        log.info("planificador: %s", f"{pedidas} herramientas" if pedidas else "termina")
        return {"messages": [respuesta]}

    async def nodo_herramientas(estado: Estado) -> dict:
        llamadas = estado["messages"][-1].tool_calls  # type: ignore[union-attr]
        restantes = ctx.max_llamadas - estado.get("llamadas", 0)
        permitidas, excedidas = llamadas[:restantes], llamadas[restantes:]
        resultados = await asyncio.gather(*(ejecutar_herramienta(ctx, c) for c in permitidas))
        mensajes = [m for m, _, _ in resultados] + [
            ToolMessage("Límite de llamadas alcanzado.", tool_call_id=c["id"], status="error")
            for c in excedidas
        ]
        errores = [
            f"{c['name']}({c.get('args')}): {m.content}"
            for c, (m, _, _) in zip(permitidas, resultados, strict=True)
            if m.status == "error"
        ]
        return {
            "messages": mensajes,
            "ofertas": [o for _, ofs, _ in resultados for o in ofs],
            "alertas": [a for _, _, als in resultados for a in als],
            "errores": errores,
            "llamadas": estado.get("llamadas", 0) + len(permitidas),
        }

    def ruta_planificador(estado: Estado) -> str:
        ultimo = estado["messages"][-1]
        con_llamadas = isinstance(ultimo, AIMessage) and bool(ultimo.tool_calls)
        if con_llamadas and estado.get("llamadas", 0) < ctx.max_llamadas:
            return "herramientas"
        return "emparejar"

    async def nodo_emparejar(estado: Estado) -> dict:
        previas = sin_duplicados(
            estado.get("ofertas", []), lambda o: (o.proveedor, _normalizar(o.titulo))
        )
        if ctx.abierta:
            comparadas = await comparar(
                previas,
                estado["necesidad"],
                ctx.perfil,
                ctx.llm("juez"),
                ctx.emparejador.codificar,
                ctx.config,
            )
            log.info(
                "comparación abierta: %d de %d ofertas cumplen",
                sum(o.descarte is None for o in comparadas),
                len(comparadas),
            )
            return {"ofertas_finales": sin_duplicados(comparadas, lambda o: (o.proveedor, o.grupo))}
        emparejadas = await ctx.emparejador.emparejar(previas, ctx.llm("confirmador"), ctx.config)
        log.info(
            "emparejamiento: %d de %d ofertas con producto del catálogo",
            sum(o.producto_catalogo is not None for o in emparejadas),
            len(emparejadas),
        )
        unicas = sin_duplicados(
            emparejadas,
            lambda o: (o.proveedor, o.producto_catalogo) if o.producto_catalogo else None,
        )
        return {"ofertas_finales": unicas}

    async def nodo_proponer(estado: Estado) -> dict:
        ofertas, alertas = estado["ofertas_finales"], list(estado.get("alertas", []))
        proponer_fn = proponer_abierto if ctx.abierta else proponer
        if ctx.verifica_precios and not ctx.abierta:  # C3 necesita el precio de catálogo
            ofertas, atipicas = verificar_precios(ofertas, referencias)
            alertas += atipicas
            for a in atipicas:
                log.info("  ⚠ C3 %s", a.mensaje)
        argumentos = (
            estado["consulta"],
            estado["necesidad"],
            ofertas,
            ctx.perfil,
            productos,
            estado.get("errores", []),
        )
        if not ctx.verificar:
            propuesta = proponer_fn(*argumentos, ctx.modelo, ctx.costo.costo_total, alertas)
            return {"propuesta": propuesta}
        # Solo las candidatas: las que ya incumplen la necesidad no pueden ganar.
        candidatas = [
            o
            for o in ofertas
            if (
                o.descarte is None
                if ctx.abierta
                else motivo_descarte(o, estado["necesidad"], ctx.perfil, productos) is None
            )
        ]
        lecturas = SegundasLecturas(ctx.llm("verificador"), ctx.config)
        verificaciones = await verificar_ofertas(candidatas, lecturas)
        for o, v in zip(candidatas, verificaciones, strict=True):
            if v.estado != "verificada":
                log.info("  ⚠ N3 %s %s: %s %s", o.proveedor, o.titulo[:40], v.estado, v.campos)
        propuesta = proponer_con_n3(
            *argumentos, ctx.modelo, ctx.costo.costo_total, alertas, ctx.politica_n3, proponer_fn
        )
        return {"propuesta": propuesta}

    grafo = StateGraph(Estado)
    grafo.add_node("interpretar", nodo_interpretar)
    grafo.add_node("planificar", nodo_planificar)
    grafo.add_node("herramientas", nodo_herramientas)
    grafo.add_node("emparejar", nodo_emparejar)
    grafo.add_node("proponer", nodo_proponer)
    grafo.add_edge(START, "interpretar")
    grafo.add_edge("interpretar", "planificar")
    grafo.add_conditional_edges(
        "planificar", ruta_planificador, {"herramientas": "herramientas", "emparejar": "emparejar"}
    )
    grafo.add_edge("herramientas", "planificar")
    grafo.add_edge("emparejar", "proponer")
    grafo.add_edge("proponer", END)
    return grafo.compile()


# --------------------------------------------------------------------------------------------------
# Punto de entrada


@dataclass
class Resultado:
    propuesta: PropuestaCompra
    necesidad: Necesidad | None
    ofertas: list[Oferta]  # emparejadas y sin duplicados (todas, válidas o no)
    llamadas_herramientas: int
    llamadas_llm: list[dict]
    segundos: float
    traza: list[AnyMessage]


async def preguntar(
    consulta: str,
    *,
    modelo: str = "deepseek-flash",
    separacion_planos: bool = True,
    configuracion: Configuracion | None = None,
    defensas: Defensas | None = None,
    clasificador: Any = None,
    verificar: bool = False,
    politica_n3: PoliticaN3 = "abstener",
    modelo_verificador: str = MODELO_VERIFICADOR,
    clave_openrouter: str | None = None,
    clave_anthropic: str | None = None,
    al_avanzar: AlAvanzar | None = None,
    max_llamadas: int = MAX_LLAMADAS,
    tope_usd: float | None = None,
    registro: RegistroFuentes | None = None,
    catalogo: list[ProductoCatalogo] | None = None,
    emparejador: Emparejador | None = None,
    perfil: PerfilCategoria | None = None,
    semaforo_llm: asyncio.Semaphore | None = None,
    abierta: bool = False,
    documentos: dict[str, str] | None = None,
) -> Resultado:
    """Responde una consulta.

    ``semaforo_llm`` permite que varias tareas en paralelo compartan un único límite de llamadas
    simultáneas al LLM (el arnés lo usa); si falta, cada tarea crea el suyo.

    ``defensas`` (capas independientes, D91) prevalece sobre ``configuracion`` (C0–C3), que
    prevalece sobre ``separacion_planos`` (compatibilidad: True = C1, False = C0). Con el
    clasificador activo, ``clasificador`` permite compartir un único modelo cargado entre tareas;
    si falta, se crea uno.

    ``al_avanzar(nodo, actualizacion)`` recibe la salida de cada nodo del grafo a medida que
    termina (progreso en vivo de CotIA).
    """
    defensas = defensas or Defensas.de(configuracion or ("C1" if separacion_planos else "C0"))
    if defensas.clasificador and clasificador is None:
        clasificador = ClasificadorInyeccion()
    inicio = time.perf_counter()
    registro = registro or cargar_fuentes()
    perfil = perfil or cargar_perfil(RUTA_PERFIL)
    emparejador = emparejador or Emparejador(catalogo or cargar_catalogo())
    costo = RegistroCosto(tope_usd)
    async with Lector(registro, documentos=documentos) as lector:
        ctx = Contexto(
            modelo=modelo,
            lector=lector,
            registro=registro,
            emparejador=emparejador,
            perfil=perfil,
            costo=costo,
            defensas=defensas,
            clasificador=clasificador,
            verificar=verificar,
            politica_n3=politica_n3,
            modelo_verificador=modelo_verificador,
            clave_openrouter=clave_openrouter,
            clave_anthropic=clave_anthropic,
            max_llamadas=max_llamadas,
            abierta=abierta,
            _semaforo=semaforo_llm,
        )
        grafo = construir_grafo(ctx)
        final: dict[str, Any] = {}
        try:
            async for parte in grafo.astream(
                {"consulta": consulta},
                config={"recursion_limit": 4 * max_llamadas + 10},
                stream_mode=["updates", "values"],
                version="v2",
            ):
                if parte["type"] == "values":
                    final = parte["data"]
                elif al_avanzar is not None:
                    for nodo, actualizacion in parte["data"].items():
                        await al_avanzar(nodo, actualizacion or {})
        except CostoExcedido as error:
            propuesta = PropuestaCompra(
                consulta=consulta,
                perfil=perfil.nombre,
                abstencion=True,
                motivo_abstencion=f"Tarea detenida: {error}",
                modelo=modelo,
                costo_usd=costo.costo_total,
            )
            return Resultado(
                propuesta, None, [], 0, costo.como_dicts(), time.perf_counter() - inicio, []
            )
    return Resultado(
        propuesta=final["propuesta"],
        necesidad=final.get("necesidad"),
        ofertas=final.get("ofertas_finales", []),
        llamadas_herramientas=final.get("llamadas", 0),
        llamadas_llm=costo.como_dicts(),
        segundos=time.perf_counter() - inicio,
        traza=final.get("messages", []),
    )
