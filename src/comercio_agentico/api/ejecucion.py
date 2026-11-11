"""Ejecución de las consultas de CotIA: cola acotada, progreso en vivo y persistencia.

Cada consulta corre como una tarea de asyncio en el mismo proceso que la API (D81). Los nodos del
grafo emiten su salida a medida que terminan (``preguntar(al_avanzar=...)``); ``Traductor`` la
reduce a eventos pequeños para el navegador (SSE). La clave de OpenRouter del visitante solo vive
en la memoria de la tarea y se borra de cualquier mensaje de error antes de guardarlo (D82).
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import time
import uuid
from collections import Counter
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import sessionmaker

from comercio_agentico.agente.defensa import ClasificadorInyeccion
from comercio_agentico.agente.grafo import preguntar
from comercio_agentico.api.bd import ConsultaBD
from comercio_agentico.api.esquemas import PeticionConsulta
from comercio_agentico.preguntar import registro_jsonl

log = logging.getLogger("comercio_agentico.api")

MAX_SIMULTANEAS = int(os.getenv("COTIA_MAX_SIMULTANEAS", "1"))  # ~2 GB de RAM por consulta
MAX_EN_COLA = int(os.getenv("COTIA_MAX_EN_COLA", "5"))
MODELO_VERIFICADOR_COTIA = "haiku-or"  # D105
LATIDO_S = 15.0


class Saturado(RuntimeError):
    """Hay demasiadas consultas en curso o en cola."""


def ocultar(texto: str, clave: str | None) -> str:
    return texto.replace(clave, "[clave oculta]") if clave else texto


@dataclass
class Progreso:
    eventos: list[dict[str, Any]] = field(default_factory=list)
    terminado: bool = False
    cambio: asyncio.Condition = field(default_factory=asyncio.Condition)

    async def emitir(self, evento: dict[str, Any]) -> None:
        async with self.cambio:
            self.eventos.append(evento)
            self.cambio.notify_all()

    async def cerrar(self) -> None:
        async with self.cambio:
            self.terminado = True
            self.cambio.notify_all()

    async def seguir(self, latido_s: float = LATIDO_S) -> AsyncIterator[dict[str, Any] | None]:
        """Repite los eventos ya emitidos y espera los nuevos; ``None`` es un latido."""
        i = 0
        while True:
            async with self.cambio:
                if i >= len(self.eventos) and not self.terminado:
                    with contextlib.suppress(TimeoutError):
                        await asyncio.wait_for(self.cambio.wait(), latido_s)
                nuevos, fin = self.eventos[i:], self.terminado
            if not nuevos and not fin:
                yield None
            for evento in nuevos:
                yield evento
            i += len(nuevos)
            if fin and i >= len(self.eventos):
                return


class Traductor:
    """Convierte la salida de cada nodo del grafo en un evento compacto para la interfaz."""

    def __init__(self) -> None:
        self.pedidas: dict[str, dict[str, Any]] = {}

    def __call__(self, nodo: str, upd: dict[str, Any]) -> dict[str, Any] | None:
        match nodo:
            case "interpretar":
                n = upd.get("necesidad")
                return {
                    "etapa": "interpretacion",
                    "necesidad": n.model_dump(mode="json", exclude_none=True) if n else None,
                }
            case "planificar":
                mensajes = upd.get("messages") or []
                llamadas = (getattr(mensajes[-1], "tool_calls", None) or []) if mensajes else []
                self.pedidas = {c["id"]: c for c in llamadas}
                return {
                    "etapa": "plan",
                    "herramientas": [
                        {"nombre": c["name"], "args": c.get("args", {})} for c in llamadas
                    ],
                }
            case "herramientas":
                lecturas = []
                for m in upd.get("messages") or []:
                    c = self.pedidas.get(getattr(m, "tool_call_id", ""), {})
                    lecturas.append(
                        {
                            "nombre": c.get("name"),
                            "args": c.get("args", {}),
                            "estado": "error" if getattr(m, "status", "") == "error" else "ok",
                        }
                    )
                ofertas = upd.get("ofertas") or []
                return {
                    "etapa": "lecturas",
                    "lecturas": lecturas,
                    "ofertas": len(ofertas),
                    "por_proveedor": dict(Counter(o.proveedor for o in ofertas)),
                    "alertas": [a.model_dump(mode="json") for a in upd.get("alertas") or []],
                }
            case "emparejar":
                finales = upd.get("ofertas_finales") or []
                return {
                    "etapa": "emparejamiento",
                    "ofertas": len(finales),
                    "emparejadas": sum(o.producto_catalogo is not None for o in finales),
                }
            case "proponer":
                p = upd["propuesta"]
                return {
                    "etapa": "propuesta",
                    "abstencion": p.abstencion,
                    "ofertas": len(p.ofertas),
                    "recomendada": p.recomendada,
                    "costo_usd": round(p.costo_usd, 6),
                }
        return None


def _recursos_por_defecto(corpus: str) -> tuple[Any, Any]:
    from comercio_agentico.agente.fuentes import cargar_fuentes
    from comercio_agentico.arnes.correr import recursos_corpus
    from comercio_agentico.corpus_b.catalogo import cargar_catalogo
    from comercio_agentico.emparejamiento import Emparejador

    r = recursos_corpus(corpus)
    return cargar_fuentes(r["fuentes"]), Emparejador(cargar_catalogo(r["catalogo"]))


def _variante_por_defecto(carga: Any) -> Any:
    from comercio_agentico.ataques.correr import levantar_variante, registro_local

    _, hilo, puerto, _ = levantar_variante(carga)
    hilo.start()
    return registro_local(puerto)


class Servicio:
    def __init__(
        self,
        sesiones: sessionmaker,
        *,
        preguntar_fn: Callable[..., Any] = preguntar,
        recursos_fn: Callable[[str], tuple[Any, Any]] = _recursos_por_defecto,
        variante_fn: Callable[[Any], Any] = _variante_por_defecto,
        clasificador_fn: Callable[[str], Any] = ClasificadorInyeccion,
        max_simultaneas: int = MAX_SIMULTANEAS,
        max_en_cola: int = MAX_EN_COLA,
    ) -> None:
        self.sesiones = sesiones
        self.preguntar_fn = preguntar_fn
        self.recursos_fn, self.variante_fn, self.clasificador_fn = (
            recursos_fn,
            variante_fn,
            clasificador_fn,
        )
        self.max_simultaneas, self.max_en_cola = max_simultaneas, max_en_cola
        self.semaforo = asyncio.Semaphore(max_simultaneas)
        self.progresos: dict[str, Progreso] = {}
        self.tareas: set[asyncio.Task] = set()
        self._recursos: dict[str, tuple[Any, Any]] = {}
        self._variantes: dict[str, Any] = {}
        self._clasificadores: dict[str, Any] = {}
        self._cerrojo = asyncio.Lock()

    # ----------------------------------------------------------------------------------------------

    async def recursos(self, corpus: str) -> tuple[Any, Any]:
        async with self._cerrojo:
            if corpus not in self._recursos:
                self._recursos[corpus] = await asyncio.to_thread(self.recursos_fn, corpus)
            return self._recursos[corpus]

    async def variante(self, carga: Any) -> Any:
        async with self._cerrojo:
            if carga.id not in self._variantes:
                self._variantes[carga.id] = await asyncio.to_thread(self.variante_fn, carga)
            return self._variantes[carga.id]

    def clasificador(self, nombre: str) -> Any:
        if nombre not in self._clasificadores:
            self._clasificadores[nombre] = self.clasificador_fn(nombre)
        return self._clasificadores[nombre]

    def activas(self) -> int:
        return sum(not p.terminado for p in self.progresos.values())

    def _actualizar(self, id_consulta: str, **campos: Any) -> None:
        with self.sesiones.begin() as s:
            fila = s.get(ConsultaBD, id_consulta)
            for k, v in campos.items():
                setattr(fila, k, v)

    # ----------------------------------------------------------------------------------------------

    def iniciar(
        self, peticion: PeticionConsulta, consulta: str, carga: Any, clave: str, visitante: str
    ) -> str:
        if self.activas() >= self.max_simultaneas + self.max_en_cola:
            raise Saturado("Hay demasiadas consultas en curso; intente en unos minutos.")
        id_consulta = str(uuid.uuid4())
        with self.sesiones.begin() as s:
            s.add(
                ConsultaBD(
                    id=id_consulta,
                    visitante=visitante,
                    consulta=consulta,
                    corpus=peticion.corpus,
                    carga=peticion.carga,
                    modelo=peticion.modelo,
                    opciones=peticion.opciones(),
                    estado="en_cola",
                    eventos=[],
                )
            )
        self.progresos[id_consulta] = Progreso()
        tarea = asyncio.create_task(self._correr(id_consulta, peticion, consulta, carga, clave))
        self.tareas.add(tarea)
        tarea.add_done_callback(self.tareas.discard)
        return id_consulta

    async def _correr(
        self, id_consulta: str, peticion: PeticionConsulta, consulta: str, carga: Any, clave: str
    ) -> None:
        prog = self.progresos[id_consulta]
        inicio = time.perf_counter()
        if self.semaforo.locked():
            await prog.emitir({"etapa": "en_cola"})
        try:
            async with self.semaforo:
                await asyncio.to_thread(self._actualizar, id_consulta, estado="en_curso")
                defensas = peticion.defensas.a_defensas()
                await prog.emitir(
                    {
                        "etapa": "inicio",
                        "modelo": peticion.modelo,
                        "configuracion": defensas.configuracion or "exploratorio",
                    }
                )
                registro, emparejador = await self.recursos(peticion.corpus)
                if carga is not None:
                    registro = await self.variante(carga)
                traductor = Traductor()

                async def al_avanzar(nodo: str, upd: dict[str, Any]) -> None:
                    evento = traductor(nodo, upd)
                    if evento is not None:
                        await prog.emitir(evento)

                r = await self.preguntar_fn(
                    consulta,
                    modelo=peticion.modelo,
                    defensas=defensas,
                    clasificador=self.clasificador(peticion.clasificador)
                    if defensas.clasificador
                    else None,
                    verificar=peticion.verificar,
                    politica_n3=peticion.politica_n3,
                    modelo_verificador=MODELO_VERIFICADOR_COTIA,
                    clave_openrouter=clave,
                    al_avanzar=al_avanzar,
                    registro=registro,
                    emparejador=emparejador,
                )
            fila = registro_jsonl(None, r, None)
            detalle: dict[str, Any] = {
                k: fila[k]
                for k in (
                    "necesidad",
                    "herramientas",
                    "ofertas_recolectadas",
                    "llamadas_herramientas",
                    "llamadas_llm",
                    "tokens",
                )
            }
            detalle["configuracion"] = defensas.configuracion or "exploratorio"
            fin: dict[str, Any] = {"etapa": "fin", "estado": "terminada"}
            if carga is not None:
                from comercio_agentico.ataques.suite import evaluar_exito

                detalle["exito_ataque"] = fin["exito_ataque"] = evaluar_exito(carga, fila)
            costo, segundos = r.propuesta.costo_usd, time.perf_counter() - inicio
            fin |= {"costo_usd": round(costo, 6), "segundos": round(segundos, 1)}
            await asyncio.to_thread(
                self._actualizar,
                id_consulta,
                estado="terminada",
                propuesta=r.propuesta.model_dump(mode="json"),
                detalle=detalle,
                costo_usd=costo,
                segundos=segundos,
            )
            await prog.emitir(fin)
        except Exception as error:
            mensaje = ocultar(f"{type(error).__name__}: {error}", clave)[:2000]
            log.warning("consulta %s: %s", id_consulta, mensaje)
            segundos = time.perf_counter() - inicio
            await asyncio.to_thread(
                self._actualizar, id_consulta, estado="error", error=mensaje, segundos=segundos
            )
            await prog.emitir({"etapa": "fin", "estado": "error", "error": mensaje})
        finally:
            await asyncio.to_thread(self._actualizar, id_consulta, eventos=prog.eventos)
            await prog.cerrar()
            self.progresos.pop(id_consulta, None)
