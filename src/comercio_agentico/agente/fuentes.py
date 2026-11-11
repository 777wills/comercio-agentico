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
Origen = Literal["corpus", "vivo", "usuario"]


class Fuente(BaseModel):
    id: str
    nombre: str
    tipo_fuente: TipoFuente
    herramienta: Herramienta
    url: str
    # corpus: copia congelada servida en local. vivo y usuario: internet abierta, con las
    # salvaguardas de `web_abierta` (D112).
    origen: Origen = "corpus"

    @property
    def abierta(self) -> bool:
        return self.origen != "corpus"

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


# Tiendas reales de la lista blanca por defecto (D112; sondeo de robots.txt, respuesta y términos
# del 11-nov-2026). La URL es el punto de entrada; el agente sigue enlaces del mismo sitio.
TIENDAS_EN_VIVO: list[Fuente] = [
    Fuente(
        id=i, nombre=n, tipo_fuente="web_schema", herramienta="abrir_pagina", url=u, origen="vivo"
    )
    for i, n, u in (
        ("V1", "Alkosto", "https://www.alkosto.com/"),
        ("V2", "Ktronix", "https://www.ktronix.com/"),
        ("V3", "Falabella", "https://www.falabella.com.co/falabella-co"),
        ("V4", "Samsung Colombia", "https://www.samsung.com/co/"),
        ("V5", "Panamericana", "https://www.panamericana.com.co/"),
    )
]
