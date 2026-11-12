"""API de CotIA (D81–D83): FastAPI en el mismo proceso que el agente.

    docker compose up -d bd                                                   # PostgreSQL local
    uv run uvicorn comercio_agentico.api.app:crear_app --factory --port 8000  # o `make api`

La clave del visitante (OpenRouter o Anthropic, D114) llega en la cabecera ``X-Clave-Modelo`` de
``POST /api/consultas`` y solo vive en la memoria de la consulta (D82); el proveedor se reconoce por
el prefijo. ``X-Visitante`` es un UUID que genera el navegador para agrupar el historial y el gasto
de la visita (D90).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import socket
import subprocess
import sys
from collections.abc import AsyncIterable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Form, Header, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from fastapi.sse import EventSourceResponse, ServerSentEvent
from sqlalchemy import func, select, text

from comercio_agentico.agente.defensa import CLASIFICADORES, MODELO_CLASIFICADOR_DEFECTO
from comercio_agentico.api import corpus as visor
from comercio_agentico.api.bd import ConsultaBD, crear_motor, fabrica_sesiones
from comercio_agentico.api.catalogo import (
    ANTHROPIC_DIRECTO,
    RUTA_LISTA,
    cargar_lista,
    proveedor_de_clave,
)
from comercio_agentico.api.ejecucion import Saturado, Servicio
from comercio_agentico.api.esquemas import (
    CambioFuente,
    ConsultaCreada,
    DetalleConsulta,
    Historial,
    NuevaUrl,
    PeticionConsulta,
    ResumenConsulta,
)
from comercio_agentico.api.fuentes_visitante import (
    MAX_BYTES_PDF,
    MAX_PDFS,
    MAX_URLS,
    FuenteInvalida,
    FuentesVisitante,
)
from comercio_agentico.corpus_b import RAIZ

log = logging.getLogger("comercio_agentico.api")

PATRON_UUID = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
DIR_INFORMES = RAIZ / "resultados" / "informes"
DIR_WEB = RAIZ / "web" / "build"
EXPERIMENTOS = ("e1", "e2", "e3")
SERVIDORES_CORPUS = {  # módulo → puertos que abre (los del registro de fuentes)
    "comercio_agentico.corpus_b.servir": (8800, 8801),
    "comercio_agentico.corpus_a.servir": (8802,),
}

ClaveModelo = Annotated[str | None, Header(alias="X-Clave-Modelo", min_length=10, max_length=200)]
Visitante = Annotated[str, Header(alias="X-Visitante", pattern=PATRON_UUID)]


def _puerto_ocupado(puerto: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", puerto)) == 0


def _arrancar_corpus() -> list[subprocess.Popen]:
    """Proveedores del corpus B y tiendas del corpus A; si ya están servidos, se reutilizan."""
    procesos = []
    for modulo, puertos in SERVIDORES_CORPUS.items():
        if all(_puerto_ocupado(p) for p in puertos):
            continue
        procesos.append(
            subprocess.Popen(
                [sys.executable, "-m", modulo],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        )
    return procesos


def _resumen(fila: ConsultaBD) -> dict[str, Any]:
    return {
        "id": fila.id,
        "consulta": fila.consulta,
        "corpus": fila.corpus,
        "carga": fila.carga,
        "modelo": fila.modelo,
        "opciones": fila.opciones,
        "estado": fila.estado,
        "costo_usd": fila.costo_usd,
        "segundos": fila.segundos,
        "creada": fila.creada.isoformat(),
    }


def _ejemplos() -> dict[str, Any]:
    from comercio_agentico.ataques.suite import cargar_suite

    def por_categoria(ruta: Path) -> list[dict[str, str]]:
        vistos: dict[str, str] = {}
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            t = json.loads(linea)
            vistos.setdefault(t["categoria"], t["consulta"])
        return [{"categoria": c, "consulta": q} for c, q in vistos.items()]

    tareas_b = {
        t["id"]: t["consulta"]
        for t in map(json.loads, (RAIZ / "tareas" / "tareas_b.jsonl").read_text().splitlines())
    }
    laboratorio = [
        {
            "carga": c.id,
            "clase": c.clase,
            "ubicacion": c.ubicacion,
            "proveedor": c.proveedor,
            "archivo": c.archivo,
            "consulta": tareas_b[c.tarea],
        }
        for c in cargar_suite().cargas
    ]
    return {
        "b": por_categoria(RAIZ / "tareas" / "tareas_b.jsonl"),
        "a": por_categoria(RAIZ / "tareas" / "tareas_a.jsonl"),
        "laboratorio": laboratorio,
    }


def _fuentes_base(corpus: str) -> Any:
    """Registro congelado de un corpus, sin cargar embeddings (para listar la lista blanca)."""
    from comercio_agentico.agente.fuentes import cargar_fuentes
    from comercio_agentico.arnes.correr import recursos_corpus

    return cargar_fuentes(recursos_corpus(corpus)["fuentes"])


def fuente_eventos(id_consulta: str, request: Request) -> Any:
    """En curso: su ``Progreso``; terminada: los eventos guardados. Corre antes del flujo SSE."""
    servicio: Servicio = request.app.state.servicio
    progreso = servicio.progresos.get(id_consulta)
    if progreso is not None:
        return progreso
    with servicio.sesiones() as s:
        fila = s.get(ConsultaBD, id_consulta)
    if fila is None:
        raise HTTPException(404, "Consulta inexistente.")
    return list(fila.eventos or [])


def crear_app(
    *,
    url_bd: str | None = None,
    servicio: Servicio | None = None,
    servir_corpus: bool = True,
    ruta_modelos: Path = RUTA_LISTA,
    dir_web: Path = DIR_WEB,
) -> FastAPI:
    motor = crear_motor(url_bd)
    sesiones = fabrica_sesiones(motor)
    servicio = servicio or Servicio(sesiones)
    servicio.sesiones = sesiones
    fuentes = servicio.fuentes = servicio.fuentes or FuentesVisitante(sesiones, _fuentes_base)

    @asynccontextmanager
    async def ciclo(_: FastAPI):
        procesos = _arrancar_corpus() if servir_corpus else []
        yield
        for p in procesos:
            p.terminate()

    app = FastAPI(
        title="CotIA",
        description="Agente de compras verificable sobre proveedores heterogéneos.",
        version="0.1.0",
        lifespan=ciclo,
    )
    app.state.servicio = servicio

    def aprobados() -> list[dict[str, Any]]:
        return cargar_lista(ruta_modelos)

    # ----------------------------------------------------------------------------------------------
    # Consultas

    @app.post("/api/consultas", status_code=status.HTTP_202_ACCEPTED)
    async def crear_consulta(
        peticion: PeticionConsulta, visitante: Visitante, clave: ClaveModelo = None
    ) -> ConsultaCreada:
        if not clave:
            raise HTTPException(401, "Configure su clave de OpenRouter o de Anthropic.")
        proveedor = proveedor_de_clave(clave)
        if proveedor is None:
            raise HTTPException(
                422,
                "Clave no reconocida: debe empezar por sk-or- (OpenRouter) o sk-ant- (Anthropic).",
            )
        if peticion.modelo not in {m["nombre"] for m in aprobados()}:
            raise HTTPException(422, "El modelo no está en la lista curada (GET /api/modelos).")
        if proveedor == "anthropic" and peticion.modelo not in ANTHROPIC_DIRECTO:
            raise HTTPException(
                422, "Con una clave de Anthropic solo se ofrecen los modelos Claude."
            )
        carga = None
        if peticion.carga:
            if peticion.corpus != "b":
                raise HTTPException(422, "El laboratorio de ataques usa el corpus B.")
            from comercio_agentico.ataques.suite import cargar_suite

            carga = next(c for c in cargar_suite().cargas if c.id == peticion.carga)
            consulta = next(
                e["consulta"] for e in _ejemplos()["laboratorio"] if e["carga"] == carga.id
            )
        elif peticion.consulta:
            consulta = peticion.consulta
            registro, _ = fuentes.registro(visitante, peticion.corpus)
            if not registro.fuentes:
                raise HTTPException(422, "No hay fuentes activas en ese grupo; active alguna.")
        else:
            raise HTTPException(422, "Escriba una consulta o elija una carga del laboratorio.")
        try:
            id_consulta = servicio.iniciar(peticion, consulta, carga, clave, visitante)
        except Saturado as error:
            raise HTTPException(429, str(error)) from None
        return ConsultaCreada(id=id_consulta, eventos=f"/api/consultas/{id_consulta}/eventos")

    # ----------------------------------------------------------------------------------------------
    # Lista blanca por visitante (D113)

    def _listado(visitante: str) -> dict[str, Any]:
        return {
            "grupos": fuentes.listar(visitante),
            "limites": {"urls": MAX_URLS, "pdfs": MAX_PDFS, "mb_pdf": MAX_BYTES_PDF // 2**20},
        }

    @app.get("/api/fuentes")
    def listar_fuentes(visitante: Visitante) -> dict[str, Any]:
        return _listado(visitante)

    @app.patch("/api/fuentes/{fuente_id}")
    def cambiar_fuente(fuente_id: str, cambio: CambioFuente, visitante: Visitante) -> dict:
        try:
            fuentes.activar(visitante, fuente_id, cambio.activa)
        except KeyError:
            raise HTTPException(404, "Fuente inexistente.") from None
        return _listado(visitante)

    @app.post("/api/fuentes/url", status_code=status.HTTP_201_CREATED)
    def agregar_url(nueva: NuevaUrl, visitante: Visitante) -> dict[str, Any]:
        try:
            fuentes.agregar_url(visitante, nueva.url, nueva.nombre)
        except FuenteInvalida as error:
            raise HTTPException(422, str(error)) from None
        return _listado(visitante)

    @app.post("/api/fuentes/pdf", status_code=status.HTTP_201_CREATED)
    async def agregar_pdf(
        archivo: UploadFile,
        visitante: Visitante,
        nombre: Annotated[str | None, Form(max_length=120)] = None,
    ) -> dict[str, Any]:
        datos = await archivo.read(MAX_BYTES_PDF + 1)
        try:
            await asyncio.to_thread(
                fuentes.agregar_pdf, visitante, nombre or archivo.filename or "", datos
            )
        except FuenteInvalida as error:
            raise HTTPException(422, str(error)) from None
        return await asyncio.to_thread(_listado, visitante)

    @app.delete("/api/fuentes/{fuente_id}")
    def eliminar_fuente(fuente_id: str, visitante: Visitante) -> dict[str, Any]:
        try:
            fuentes.eliminar(visitante, fuente_id)
        except KeyError:
            raise HTTPException(404, "Solo se pueden eliminar las fuentes propias.") from None
        return _listado(visitante)

    @app.post("/api/fuentes/restablecer")
    def restablecer_fuentes(visitante: Visitante) -> dict[str, Any]:
        fuentes.restablecer(visitante)
        return _listado(visitante)

    @app.get("/api/consultas/{id_consulta}/eventos", response_class=EventSourceResponse)
    async def eventos(
        fuente: Annotated[Any, Depends(fuente_eventos)],
    ) -> AsyncIterable[ServerSentEvent]:
        if isinstance(fuente, list):
            for i, e in enumerate(fuente):
                yield ServerSentEvent(data=e, event=e["etapa"], id=str(i))
            return
        i = 0
        async for e in fuente.seguir():
            if e is None:  # FastAPI ya envía su propio ping de keep-alive
                continue
            yield ServerSentEvent(data=e, event=e["etapa"], id=str(i))
            i += 1

    @app.get("/api/consultas/{id_consulta}")
    def consulta(id_consulta: str) -> DetalleConsulta:
        with sesiones() as s:
            fila = s.get(ConsultaBD, id_consulta)
        if fila is None:
            raise HTTPException(404, "Consulta inexistente.")
        return DetalleConsulta(
            **_resumen(fila), propuesta=fila.propuesta, detalle=fila.detalle, error=fila.error
        )

    @app.get("/api/consultas")
    def historial(visitante: Visitante, limite: int = 50) -> Historial:
        with sesiones() as s:
            filas = s.scalars(
                select(ConsultaBD)
                .where(ConsultaBD.visitante == visitante)
                .order_by(ConsultaBD.creada.desc())
                .limit(min(max(limite, 1), 200))
            ).all()
            total, gasto = s.execute(
                select(func.count(), func.coalesce(func.sum(ConsultaBD.costo_usd), 0.0)).where(
                    ConsultaBD.visitante == visitante
                )
            ).one()
        return Historial(
            consultas=[ResumenConsulta(**_resumen(f)) for f in filas],
            total_consultas=total,
            gasto_usd=round(gasto, 6),
        )

    # ----------------------------------------------------------------------------------------------
    # Catálogos y resultados

    @app.get("/api/modelos")
    def modelos() -> dict[str, Any]:
        lista = [m | {"anthropic": m["nombre"] in ANTHROPIC_DIRECTO} for m in aprobados()]
        nombres = [m["nombre"] for m in lista]
        return {
            "modelos": lista,
            "por_defecto": "deepseek-flash"
            if "deepseek-flash" in nombres
            else next(iter(nombres), None),
            "clasificadores": CLASIFICADORES,
            "clasificador_por_defecto": MODELO_CLASIFICADOR_DEFECTO,
            "defensas_por_defecto": "C2",
            "trazas": os.getenv("LANGSMITH_TRACING", "").lower() == "true",  # D117
        }

    @app.get("/api/ejemplos")
    def ejemplos() -> dict[str, Any]:
        return _ejemplos()

    @app.get("/api/resultados")
    def resultados() -> dict[str, Any]:
        salida = {}
        for exp in EXPERIMENTOS:
            directorio = DIR_INFORMES / exp
            ruta = directorio / f"{exp}.json"
            salida[exp] = {
                "datos": json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else None,
                "figuras": [
                    f"/api/resultados/figuras/{exp}/{p.name}"
                    for p in sorted(directorio.glob("*.png"))
                ],
            }
        return salida

    @app.get("/api/resultados/figuras/{experimento}/{nombre}")
    def figura(experimento: str, nombre: str) -> FileResponse:
        if experimento not in EXPERIMENTOS:
            raise HTTPException(404)
        disponibles = {p.name: p for p in (DIR_INFORMES / experimento).glob("*.png")}
        if nombre not in disponibles:  # lista blanca: sin rutas construidas por el cliente
            raise HTTPException(404)
        return FileResponse(disponibles[nombre], media_type="image/png")

    # ----------------------------------------------------------------------------------------------
    # Visor del corpus (D87)

    @app.get("/api/corpus")
    def corpus_indice() -> dict[str, Any]:
        return visor.indice()

    @app.get("/api/corpus/archivo/{origen}/{ruta:path}")
    def corpus_archivo(origen: str, ruta: str) -> FileResponse:
        if origen not in visor.DIR_CORPUS and not re.fullmatch(r"A(?:0[1-9]|1[0-9]|20)", origen):
            raise HTTPException(404)
        archivo = visor.lista_blanca(origen).get(ruta)  # sin rutas construidas por el cliente
        if archivo is None:
            raise HTTPException(404)
        # El visor de PDF del navegador no abre en un documento con sandbox; el PDF lo genera fpdf2.
        csp = {} if archivo.suffix == ".pdf" else {"Content-Security-Policy": visor.CSP_CORPUS}
        return FileResponse(archivo, media_type=visor.TIPOS_MIME[archivo.suffix], headers=csp)

    @app.get("/api/salud")
    def salud() -> dict[str, Any]:
        try:
            with sesiones() as s:
                s.execute(text("SELECT 1"))
            bd = True
        except Exception:
            bd = False
        return {
            "estado": "ok" if bd else "degradado",
            "bd": bd,
            "corpus": {str(p): _puerto_ocupado(p) for ps in SERVIDORES_CORPUS.values() for p in ps},
            "consultas_activas": servicio.activas(),
            "modelos": len(aprobados()),
        }

    if (dir_web / "index.html").exists():  # compilación de `web/` (npm run build)
        app.frontend("/", directory=dir_web, fallback="index.html")

    return app
