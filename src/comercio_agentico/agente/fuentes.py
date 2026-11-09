"""Registro de fuentes autorizadas por el operador.

Es configuración de confianza (plano de control): el agente solo abre estas fuentes y las páginas
del mismo sitio enlazadas desde ellas. Las URL que aparecen dentro del contenido son datos.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

import yaml
from pydantic import BaseModel

from comercio_agentico.corpus_b import RAIZ
from comercio_agentico.esquema import TipoFuente

RUTA_FUENTES_B = RAIZ / "fuentes" / "corpus_b.yaml"
Herramienta = Literal["abrir_pagina", "leer_documento", "consultar_mcp"]


class Fuente(BaseModel):
    id: str
    nombre: str
    tipo_fuente: TipoFuente
    herramienta: Herramienta
    url: str

    @property
    def prefijo(self) -> str:
        """Directorio de la URL: lo que cuelga de él pertenece a este proveedor."""
        partes = urlsplit(self.url)
        ruta = partes.path.rsplit("/", 1)[0] + "/"
        return f"{partes.scheme}://{partes.netloc}{ruta}"


class RegistroFuentes(BaseModel):
    fuentes: list[Fuente]

    def por_url(self, url: str) -> Fuente | None:
        """Proveedor dueño de la URL (gana el prefijo más largo); None si no está autorizada."""
        candidatas = [f for f in self.fuentes if url == f.url or url.startswith(f.prefijo)]
        return max(candidatas, key=lambda f: len(f.prefijo), default=None)

    def por_herramienta(self, herramienta: Herramienta) -> list[Fuente]:
        return [f for f in self.fuentes if f.herramienta == herramienta]


def cargar_fuentes(ruta: str | Path = RUTA_FUENTES_B) -> RegistroFuentes:
    with Path(ruta).open(encoding="utf-8") as archivo:
        return RegistroFuentes.model_validate(yaml.safe_load(archivo))
