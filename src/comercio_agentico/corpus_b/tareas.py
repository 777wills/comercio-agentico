"""Tareas del corpus B con respuesta de referencia calculada desde la verdad (nunca a mano).

Cada tarea guarda la consulta en lenguaje natural, los **criterios** que la formalizan y la
**respuesta** que produce ``calcular_respuesta(criterios)`` sobre ``verdad.json``. Categorías
inspiradas en la taxonomía de WebMall:

- ``especifica``: un producto identificado; ¿quién lo tiene y a qué precio?
- ``mas_barato``: un producto; ¿dónde sale más barato con envío?
- ``restricciones``: tipo de producto + especificación mínima + presupuesto (+ plazo).
- ``vaga``: necesidad expresada sin cifras; los criterios hacen explícita una interpretación
  razonable y se acepta cualquier oferta válida.
- ``sin_respuesta``: nadie lo vende, todo está agotado o las restricciones son imposibles; la
  respuesta correcta es abstenerse.

Uso: ``uv run python -m comercio_agentico.corpus_b.tareas`` (US$0, sin red).
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from comercio_agentico.corpus_b import RUTA_TAREAS
from comercio_agentico.corpus_b.catalogo import ProductoCatalogo, cargar_catalogo
from comercio_agentico.corpus_b.generar import cargar_verdad
from comercio_agentico.corpus_b.render import NOMBRES_CATEGORIA, capacidad, pesos
from comercio_agentico.esquema import RestriccionDura

CategoriaTarea = Literal["especifica", "mas_barato", "restricciones", "vaga", "sin_respuesta"]
DISPONIBLES = ("en_stock", "bajo_pedido")  # restricción dura del perfil
CUOTAS = {"especifica": 12, "mas_barato": 12, "vaga": 12, "sin_respuesta": 9}
TOTAL = 60
SEMILLA = 20261110


class Criterios(BaseModel):
    productos: list[str] | None = Field(
        default=None, description="IDs del catálogo aceptados; [] = producto fuera de catálogo."
    )
    tipo_producto: str | None = None
    marca: str | None = None
    atributos: list[RestriccionDura] = Field(default_factory=list)
    presupuesto_max: int | None = Field(default=None, description="Sobre precio + envío.")
    plazo_max_dias: int | None = None


class Respuesta(BaseModel):
    abstencion: bool
    producto_id: str | None = None
    proveedor: str | None = None
    costo_total: int | None = None
    ofertas_validas: list[tuple[str, str]] = Field(
        default_factory=list, description="(proveedor, producto_id), de menor a mayor costo."
    )


class Tarea(BaseModel):
    id: str
    categoria: CategoriaTarea
    consulta: str
    criterios: Criterios
    respuesta: Respuesta
    acepta_cualquier_valida: bool = Field(
        default=False, description="True en tareas vagas: basta recomendar una oferta válida."
    )


def _costo(oferta: dict) -> int:
    return int(oferta["precio"] + (oferta["costo_envio"] or 0))


def _cumple_producto(p: ProductoCatalogo, c: Criterios) -> bool:
    if c.productos is not None and p.id not in c.productos:
        return False
    if c.tipo_producto and p.categoria != c.tipo_producto:
        return False
    if c.marca and p.marca.lower() != c.marca.lower():
        return False
    return all(r.cumple(p.atributos.get(r.atributo)) for r in c.atributos)


def calcular_respuesta(
    criterios: Criterios, verdad: dict[str, Any], catalogo: list[ProductoCatalogo]
) -> Respuesta:
    """La única definición de respuesta correcta: filtra la verdad y elige el menor costo total."""
    productos = {p.id: p for p in catalogo}
    validas = []
    for o in verdad["ofertas"]:
        of = o["oferta"]
        if of["disponibilidad"] not in DISPONIBLES or of["moneda"] != "COP":
            continue
        if o["producto_id"] is None:  # corpus A: producto parecido que no está en el catálogo
            continue
        if not _cumple_producto(productos[o["producto_id"]], criterios):
            continue
        if criterios.presupuesto_max is not None and _costo(of) > criterios.presupuesto_max:
            continue
        if (
            criterios.plazo_max_dias is not None
            and (of["plazo_entrega_dias"] or 10**6) > criterios.plazo_max_dias  # sin plazo: no
        ):
            continue
        validas.append((_costo(of), o["proveedor"], o["producto_id"]))
    if not validas:
        return Respuesta(abstencion=True)
    validas.sort()
    costo, proveedor, producto = validas[0]
    return Respuesta(
        abstencion=False,
        producto_id=producto,
        proveedor=proveedor,
        costo_total=costo,
        ofertas_validas=[(prov, prod) for _, prov, prod in validas],
    )


def _empate(verdad, catalogo, criterios: Criterios) -> bool:
    """True si el menor costo total no es único (la tarea tendría dos respuestas)."""
    r = calcular_respuesta(criterios, verdad, catalogo)
    if r.abstencion:
        return False
    costos = sorted(
        _costo(o["oferta"])
        for o in verdad["ofertas"]
        if (o["proveedor"], o["producto_id"]) in set(r.ofertas_validas)
    )
    return len(costos) > 1 and costos[0] == costos[1]


# --------------------------------------------------------------------------------------------------
# Plantillas de consulta

VAGAS: list[tuple[str, Criterios]] = [
    (
        "Quiero un portátil liviano para cargarlo todo el día en la universidad, lo más económico "
        "posible.",
        Criterios(
            tipo_producto="portatil",
            atributos=[RestriccionDura(atributo="peso", operador="<=", valor=1.6)],
        ),
    ),
    (
        "Necesito un computador portátil que aguante edición de video, con bastante memoria RAM.",
        Criterios(
            tipo_producto="portatil",
            atributos=[RestriccionDura(atributo="memoria_ram", operador=">=", valor=16)],
        ),
    ),
    (
        "Algo de Apple para trabajar, que sea portátil.",
        Criterios(tipo_producto="portatil", marca="Apple"),
    ),
    (
        "Un monitor para jugar que sea bien rápido, el más barato que haya.",
        Criterios(
            tipo_producto="monitor",
            atributos=[RestriccionDura(atributo="frecuencia_refresco", operador=">=", valor=144)],
        ),
    ),
    (
        "Busco una pantalla grande con muy buena resolución para diseño gráfico.",
        Criterios(
            tipo_producto="monitor",
            atributos=[
                RestriccionDura(atributo="tamano_pantalla", operador=">=", valor=27),
                RestriccionDura(atributo="resolucion", operador="en", valor=["4K"]),
            ],
        ),
    ),
    (
        "Un celular sencillo y barato para mi mamá, que no pase de un millón con envío.",
        Criterios(tipo_producto="celular", presupuesto_max=1_000_000),
    ),
    (
        "Un celular al que le dure mucho la batería.",
        Criterios(
            tipo_producto="celular",
            atributos=[RestriccionDura(atributo="bateria", operador=">=", valor=5000)],
        ),
    ),
    (
        "Un celular de gama alta con muchísimo espacio para fotos y videos.",
        Criterios(
            tipo_producto="celular",
            atributos=[RestriccionDura(atributo="almacenamiento", operador=">=", valor=512)],
        ),
    ),
    (
        "Unos audífonos para el avión que no dejen oír el ruido del motor.",
        Criterios(
            tipo_producto="audifonos",
            atributos=[RestriccionDura(atributo="cancelacion_ruido", operador="==", valor=True)],
        ),
    ),
    (
        "Audífonos sin cables y baratos para el gimnasio, máximo 300 mil con envío.",
        Criterios(
            tipo_producto="audifonos",
            presupuesto_max=300_000,
            atributos=[RestriccionDura(atributo="inalambrico", operador="==", valor=True)],
        ),
    ),
    (
        "Algo para guardar todas las fotos de la familia, con mucho espacio.",
        Criterios(
            tipo_producto="almacenamiento",
            atributos=[RestriccionDura(atributo="almacenamiento", operador=">=", valor=2048)],
        ),
    ),
    (
        "Un disco rápido para pasar archivos pesados entre computadores.",
        Criterios(
            tipo_producto="almacenamiento",
            atributos=[
                RestriccionDura(atributo="tipo_almacenamiento", operador="==", valor="SSD"),
                RestriccionDura(atributo="velocidad_lectura", operador=">=", valor=1000),
            ],
        ),
    ),
    (
        "Unos audífonos buenos para escuchar música en la casa, de marca reconocida.",
        Criterios(tipo_producto="audifonos", marca="Sony"),
    ),
    (
        "Un monitor económico para la oficina.",
        Criterios(tipo_producto="monitor", presupuesto_max=800_000),
    ),
]

FRASE_ATRIBUTO = {
    "memoria_ram": lambda v: f"al menos {v} GB de RAM",
    "almacenamiento": lambda v: f"mínimo {capacidad(v)} de capacidad",
    "tamano_pantalla": lambda v: f"pantalla de {v:g} pulgadas o más".replace(".", ","),
    "frecuencia_refresco": lambda v: f"frecuencia de {v} Hz o más",
    "bateria": lambda v: f"batería de al menos {v} mAh",
    "autonomia": lambda v: f"mínimo {v} horas de autonomía",
    "velocidad_lectura": lambda v: f"lectura de al menos {v} MB/s",
}
ARTICULO = {
    "portatil": "un portátil",
    "monitor": "un monitor",
    "celular": "un celular",
    "audifonos": "unos audífonos",
    "almacenamiento": "una unidad de almacenamiento",
}
NUMERICOS = {
    "portatil": ["memoria_ram", "almacenamiento", "tamano_pantalla"],
    "monitor": ["tamano_pantalla", "frecuencia_refresco"],
    "celular": ["memoria_ram", "almacenamiento", "bateria"],
    "audifonos": ["autonomia"],
    "almacenamiento": ["almacenamiento", "velocidad_lectura"],
}


def _nombre_unico(p: ProductoCatalogo, catalogo: list[ProductoCatalogo]) -> str:
    """Marca + modelo si identifica un solo producto; si no (variantes), el título completo."""
    corto = f"{p.marca} {p.modelo}"
    repetido = sum(1 for q in catalogo if f"{q.marca} {q.modelo}".lower() == corto.lower()) > 1
    return p.titulo if repetido else corto


# --------------------------------------------------------------------------------------------------
# Generación


def generar(ruta: Path = RUTA_TAREAS) -> list[Tarea]:
    catalogo, verdad = cargar_catalogo(), cargar_verdad()
    productos = {p.id: p for p in catalogo}
    azar = random.Random(SEMILLA)
    tareas: list[Tarea] = []

    def agregar(
        categoria: CategoriaTarea, consulta: str, criterios: Criterios, cualquiera: bool = False
    ) -> None:
        tareas.append(
            Tarea(
                id=f"B{len(tareas) + 1:03d}",
                categoria=categoria,
                consulta=consulta,
                criterios=criterios,
                respuesta=calcular_respuesta(criterios, verdad, catalogo),
                acepta_cualquier_valida=cualquiera,
            )
        )

    # Productos con al menos dos ofertas válidas y mínimo único: sirven para comparar.
    comparables = [
        p
        for p in catalogo
        if len(calcular_respuesta(Criterios(productos=[p.id]), verdad, catalogo).ofertas_validas)
        >= 2
        and not _empate(verdad, catalogo, Criterios(productos=[p.id]))
    ]
    azar.shuffle(comparables)
    especificas = comparables[: CUOTAS["especifica"]]
    baratos = (comparables[CUOTAS["especifica"] :] + comparables)[: CUOTAS["mas_barato"]]

    for i, p in enumerate(especificas):
        identificador = (f"(EAN {p.gtin})", f"(referencia {p.mpn})", "")[i % 3]
        consulta = (
            f"¿Qué proveedores tienen disponible el {p.titulo} {identificador} y a qué precio?"
        )
        agregar("especifica", " ".join(consulta.split()), Criterios(productos=[p.id]))

    for p in baratos:
        nombre = _nombre_unico(p, catalogo)
        consulta = azar.choice(
            [
                f"Necesito comprar {nombre}. ¿Dónde me sale más barato contando el envío?",
                f"¿Cuál es el proveedor más económico para {nombre}, con envío incluido?",
            ]
        )
        agregar("mas_barato", consulta, Criterios(productos=[p.id]))

    vagas = [(c, k) for c, k in VAGAS if not calcular_respuesta(k, verdad, catalogo).abstencion]
    for consulta, criterios in vagas[: CUOTAS["vaga"]]:
        agregar("vaga", consulta, criterios, cualquiera=True)

    # Restricciones: umbral de un atributo numérico + presupuesto (+ plazo), con respuesta única.
    cuota = TOTAL - CUOTAS["sin_respuesta"] - len(tareas)
    intentos, vistas = 0, set()
    while sum(t.categoria == "restricciones" for t in tareas) < cuota and intentos < 2000:
        intentos += 1
        tipo = azar.choice(list(NUMERICOS))
        atributo = azar.choice(NUMERICOS[tipo])
        valores = sorted({p.atributos[atributo] for p in catalogo if p.categoria == tipo})
        umbral = azar.choice(valores[:-1] or valores)
        base = Criterios(
            tipo_producto=tipo,
            atributos=[RestriccionDura(atributo=atributo, operador=">=", valor=umbral)],
        )
        r = calcular_respuesta(base, verdad, catalogo)
        if r.abstencion or len(r.ofertas_validas) < 3:
            continue
        costos = sorted(
            _costo(o["oferta"])
            for o in verdad["ofertas"]
            if (o["proveedor"], o["producto_id"]) in set(r.ofertas_validas)
        )
        presupuesto = round(costos[len(costos) // 2] * 1.05, -4)  # deja pasar ~la mitad
        plazo = azar.choice([None, None, 3, 5])
        criterios = base.model_copy(
            update={"presupuesto_max": int(presupuesto), "plazo_max_dias": plazo}
        )
        clave = criterios.model_dump_json()
        if (
            clave in vistas
            or calcular_respuesta(criterios, verdad, catalogo).abstencion
            or _empate(verdad, catalogo, criterios)
        ):
            continue
        vistas.add(clave)
        entrega = f", que me llegue en máximo {plazo} días" if plazo else ""
        consulta = (
            f"Busco {ARTICULO[tipo]} con {FRASE_ATRIBUTO[atributo](umbral)}, por "
            f"máximo ${pesos(presupuesto)} incluido el envío{entrega}. ¿Cuál me "
            f"recomiendas?"
        )
        agregar("restricciones", consulta, criterios)

    # Sin respuesta: el agente debe abstenerse.
    for pid in verdad["productos_sin_oferta"]:
        p = productos[pid]
        agregar(
            "sin_respuesta",
            f"Quiero comprar {_nombre_unico(p, catalogo)}. ¿Quién lo vende y a qué precio?",
            Criterios(productos=[pid]),
        )
    for pid in verdad["productos_solo_agotados"]:
        p = productos[pid]
        agregar(
            "sin_respuesta",
            f"¿Dónde consigo {_nombre_unico(p, catalogo)} para comprarlo ya?",
            Criterios(productos=[pid]),
        )
    agregar(
        "sin_respuesta",
        "Necesito un portátil con 64 GB de RAM por menos de $2.000.000 con envío.",
        Criterios(
            tipo_producto="portatil",
            presupuesto_max=2_000_000,
            atributos=[RestriccionDura(atributo="memoria_ram", operador=">=", valor=64)],
        ),
    )
    agregar(
        "sin_respuesta",
        "¿Quién vende la consola PlayStation 6 Pro y a qué precio?",
        Criterios(productos=[]),
    )
    while sum(t.categoria == "sin_respuesta" for t in tareas) < CUOTAS["sin_respuesta"]:
        agregar(
            "sin_respuesta",
            "Busco un televisor OLED de 77 pulgadas, ¿quién lo tiene?",
            Criterios(productos=[]),
        )

    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text("".join(t.model_dump_json() + "\n" for t in tareas), encoding="utf-8")
    return tareas


def cargar_tareas(ruta: Path = RUTA_TAREAS) -> list[Tarea]:
    return [
        Tarea.model_validate_json(linea) for linea in ruta.read_text(encoding="utf-8").splitlines()
    ]


if __name__ == "__main__":
    tareas = generar()
    conteo: dict[str, int] = {}
    for t in tareas:
        conteo[t.categoria] = conteo.get(t.categoria, 0) + 1
    print(f"{len(tareas)} tareas en {RUTA_TAREAS}: {conteo}")
    print(
        "Categorías de producto cubiertas:",
        sorted(
            {
                NOMBRES_CATEGORIA[t.criterios.tipo_producto]
                for t in tareas
                if t.criterios.tipo_producto
            }
        ),
    )
    print(json.dumps(tareas[0].model_dump(), ensure_ascii=False)[:400])
