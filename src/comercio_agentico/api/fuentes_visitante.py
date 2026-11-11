"""Lista blanca de fuentes por visitante (D112, D113).

Tres grupos por defecto: tiendas en vivo, tiendas reconstruidas (corpus A) y proveedores de prueba
(corpus B). El visitante activa o desactiva cualquier fuente y agrega tiendas (URL) o PDF al grupo
en vivo. Sus cambios solo le afectan a él; las fuentes por defecto nunca se borran del servidor.
"""

from __future__ import annotations

import hashlib
import io
import uuid
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from sqlalchemy import delete, select
from sqlalchemy.orm import sessionmaker

from comercio_agentico.agente.fuentes import TIENDAS_EN_VIVO, Fuente, RegistroFuentes
from comercio_agentico.agente.web_abierta import AGENTE_USUARIO, sitio, validar_url_publica
from comercio_agentico.api.bd import FuenteVisitanteBD

GRUPOS = {"vivo": "Tiendas en vivo", "a": "Tiendas reconstruidas", "b": "Proveedores de prueba"}
MAX_URLS = 3
MAX_PDFS = 3
MAX_BYTES_PDF = 5 * 1024 * 1024


class FuenteInvalida(ValueError):
    """La URL o el PDF no se pueden agregar; el mensaje es apto para el visitante."""


def robots_permite(url: str) -> bool:
    """robots.txt del sitio para el robot de CotIA; sin robots.txt (4xx) todo está permitido."""
    try:
        r = httpx.get(
            f"{sitio(url)}/robots.txt", headers={"User-Agent": AGENTE_USUARIO}, timeout=15
        )
    except httpx.HTTPError:
        return False
    if r.status_code >= 500:
        return False
    reglas = RobotFileParser()
    reglas.parse(r.text.splitlines() if r.status_code < 400 else [])
    return reglas.can_fetch(AGENTE_USUARIO, url)


def texto_pdf(datos: bytes) -> str:
    if len(datos) > MAX_BYTES_PDF:
        raise FuenteInvalida("El PDF supera 5 MB.")
    if not datos.startswith(b"%PDF"):
        raise FuenteInvalida("El archivo no es un PDF.")
    try:
        lector = PdfReader(io.BytesIO(datos))
        texto = "\n".join(p.extract_text() or "" for p in lector.pages)
    except (PdfReadError, ValueError) as error:
        raise FuenteInvalida("No se pudo leer el PDF.") from error
    if len(texto.strip()) < 20:
        raise FuenteInvalida("El PDF no tiene texto extraíble (¿es una imagen escaneada?).")
    return texto


def _id_usuario(fila: FuenteVisitanteBD) -> str:
    return "U" + fila.id[:6]


def _fuente_usuario(fila: FuenteVisitanteBD) -> Fuente:
    es_pdf = fila.tipo == "pdf" or fila.url.lower().endswith(".pdf")
    return Fuente(
        id=_id_usuario(fila),
        nombre=fila.nombre,
        tipo_fuente="pdf" if es_pdf else "web_plana",
        herramienta="leer_documento" if es_pdf else "abrir_pagina",
        url=fila.url,
        origen="usuario",
    )


class FuentesVisitante:
    def __init__(
        self,
        sesiones: sessionmaker,
        base: Callable[[str], RegistroFuentes],
        robots: Callable[[str], bool] = robots_permite,
        validar: Callable[[str], str] = validar_url_publica,
    ) -> None:
        self.sesiones = sesiones
        self.base = base  # corpus "a" | "b" → registro congelado
        self.robots, self.validar = robots, validar

    def por_defecto(self, grupo: str) -> list[Fuente]:
        return list(TIENDAS_EN_VIVO) if grupo == "vivo" else list(self.base(grupo).fuentes)

    def _filas(self, visitante: str) -> list[FuenteVisitanteBD]:
        with self.sesiones() as s:
            return list(
                s.scalars(
                    select(FuenteVisitanteBD)
                    .where(FuenteVisitanteBD.visitante == visitante)
                    .order_by(FuenteVisitanteBD.creada)
                )
            )

    # ----------------------------------------------------------------------------------------------
    # Lectura

    def listar(self, visitante: str) -> list[dict[str, Any]]:
        filas = self._filas(visitante)
        prefs = {f.fuente_id: f.activa for f in filas if f.tipo == "pref"}
        propias = [f for f in filas if f.tipo != "pref"]
        grupos = []
        for grupo, nombre in GRUPOS.items():
            fuentes = [
                {
                    "id": f.id,
                    "nombre": f.nombre,
                    "tipo_fuente": f.tipo_fuente,
                    "url": f.url,
                    "origen": f.origen,
                    "activa": prefs.get(f.id, True),
                    "eliminable": False,
                }
                for f in self.por_defecto(grupo)
            ]
            if grupo == "vivo":
                fuentes += [
                    {
                        "id": _id_usuario(f),
                        "nombre": f.nombre,
                        "tipo_fuente": _fuente_usuario(f).tipo_fuente,
                        "url": f.url if f.tipo == "url" else f"PDF · SHA-256 {f.sha256[:12]}",
                        "origen": "usuario",
                        "activa": f.activa,
                        "eliminable": True,
                    }
                    for f in propias
                ]
            grupos.append({"id": grupo, "nombre": nombre, "fuentes": fuentes})
        return grupos

    def inactivas(self, visitante: str) -> set[str]:
        return {f.fuente_id for f in self._filas(visitante) if f.tipo == "pref" and not f.activa}

    def registro(self, visitante: str, grupo: str) -> tuple[RegistroFuentes, dict[str, str]]:
        """Fuentes activas del grupo y textos de los PDF del visitante (``pdf://<sha256>``)."""
        filas = self._filas(visitante)
        prefs = {f.fuente_id: f.activa for f in filas if f.tipo == "pref"}
        fuentes = [f for f in self.por_defecto(grupo) if prefs.get(f.id, True)]
        documentos: dict[str, str] = {}
        if grupo == "vivo":
            for f in filas:
                if f.tipo != "pref" and f.activa:
                    fuentes.append(_fuente_usuario(f))
                    if f.tipo == "pdf" and f.texto:
                        documentos[f.url] = f.texto
        return RegistroFuentes(fuentes=fuentes), documentos

    # ----------------------------------------------------------------------------------------------
    # Cambios

    def activar(self, visitante: str, fuente_id: str, activa: bool) -> None:
        propia = next(
            (f for f in self._filas(visitante) if f.tipo != "pref" and _id_usuario(f) == fuente_id),
            None,
        )
        if propia is None and fuente_id not in {f.id for g in GRUPOS for f in self.por_defecto(g)}:
            raise KeyError(fuente_id)
        with self.sesiones.begin() as s:
            if propia is not None:
                s.get(FuenteVisitanteBD, propia.id).activa = activa
                return
            pref = s.scalar(
                select(FuenteVisitanteBD).where(
                    FuenteVisitanteBD.visitante == visitante,
                    FuenteVisitanteBD.tipo == "pref",
                    FuenteVisitanteBD.fuente_id == fuente_id,
                )
            )
            if pref is None:
                s.add(
                    FuenteVisitanteBD(
                        id=str(uuid.uuid4()),
                        visitante=visitante,
                        tipo="pref",
                        fuente_id=fuente_id,
                        nombre="",
                        url="",
                        activa=activa,
                    )
                )
            else:
                pref.activa = activa

    def _guardar(self, visitante: str, **campos: Any) -> dict[str, Any]:
        fila = FuenteVisitanteBD(id=str(uuid.uuid4()), visitante=visitante, activa=True, **campos)
        with self.sesiones.begin() as s:
            s.add(fila)
        return {"id": _id_usuario(fila), "nombre": fila.nombre}

    def agregar_url(self, visitante: str, url: str, nombre: str | None = None) -> dict[str, Any]:
        url = url.strip()
        propias = [f for f in self._filas(visitante) if f.tipo == "url"]
        if len(propias) >= MAX_URLS:
            raise FuenteInvalida(
                f"Máximo {MAX_URLS} tiendas propias; elimine una para agregar otra."
            )
        if any(f.url == url for f in propias):
            raise FuenteInvalida("Esa tienda ya está en su lista.")
        try:
            self.validar(url)
        except ValueError as error:
            raise FuenteInvalida(str(error)) from error
        if not self.robots(url):
            raise FuenteInvalida("El robots.txt de ese sitio no permite que CotIA lo lea.")
        host = urlsplit(url).hostname or url
        return self._guardar(
            visitante,
            tipo="url",
            fuente_id="",
            nombre=(nombre or host.removeprefix("www."))[:120],
            url=url,
        )

    def agregar_pdf(self, visitante: str, nombre: str, datos: bytes) -> dict[str, Any]:
        propios = [f for f in self._filas(visitante) if f.tipo == "pdf"]
        if len(propios) >= MAX_PDFS:
            raise FuenteInvalida(f"Máximo {MAX_PDFS} PDF; elimine uno para agregar otro.")
        texto = texto_pdf(datos)
        sha = hashlib.sha256(datos).hexdigest()
        if any(f.sha256 == sha for f in propios):
            raise FuenteInvalida("Ese PDF ya está en su lista.")
        return self._guardar(
            visitante,
            tipo="pdf",
            fuente_id="",
            nombre=(nombre or "Lista de precios")[:120],
            url=f"pdf://{sha}",
            texto=texto,
            sha256=sha,
        )

    def eliminar(self, visitante: str, fuente_id: str) -> None:
        propia = next(
            (f for f in self._filas(visitante) if f.tipo != "pref" and _id_usuario(f) == fuente_id),
            None,
        )
        if propia is None:
            raise KeyError(fuente_id)
        with self.sesiones.begin() as s:
            s.execute(delete(FuenteVisitanteBD).where(FuenteVisitanteBD.id == propia.id))

    def restablecer(self, visitante: str) -> None:
        """Vuelve a la lista por defecto: todo activo y sin fuentes propias."""
        with self.sesiones.begin() as s:
            s.execute(delete(FuenteVisitanteBD).where(FuenteVisitanteBD.visitante == visitante))
