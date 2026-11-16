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
    # Solo informativas para el visitante (D127): categorías del perfil y marca exclusiva.
    categorias: list[str] = []
    marca: str | None = None

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


TODAS = ["portatil", "monitor", "celular", "audifonos", "almacenamiento"]
APPLE = ["portatil", "monitor", "celular", "audifonos"]
SAMSUNG = ["monitor", "celular", "audifonos", "almacenamiento"]

# Tiendas reales aptas (D112, D132: robots.txt, respuesta a un cliente automatizado y términos sin
# prohibición expresa del acceso automatizado; sondeo del 14-nov-2026 en resultados/tiendas/).
# La URL es el punto de entrada; el agente sigue enlaces del mismo sitio.
TIENDAS_EN_VIVO: list[Fuente] = [
    Fuente(
        id=i,
        nombre=n,
        tipo_fuente="web_schema",
        herramienta="abrir_pagina",
        url=u,
        origen="vivo",
        categorias=c,
        marca=m,
    )
    for i, n, u, c, m in (
        ("V3", "Falabella", "https://www.falabella.com.co/falabella-co", TODAS, None),
        ("V4", "Samsung Colombia", "https://www.samsung.com/co/", SAMSUNG, "Samsung"),
        ("V5", "Panamericana", "https://www.panamericana.com.co/", TODAS, None),
        ("V6", "Homecenter", "https://www.homecenter.com.co/homecenter-co/", TODAS, None),
        ("V7", "Tienda Claro", "https://tienda.claro.com.co/", ["celular", "audifonos"], None),
        ("V8", "Tigo", "https://compras.tigo.com.co/", ["celular"], None),
        ("V9", "Mac Center", "https://www.maccenter.com.co/", APPLE, "Apple"),
        ("V10", "iShop", "https://www.ishop.co/", APPLE, "Apple"),
        ("V11", "Clevercel", "https://www.clevercel.co/", ["celular", "audifonos"], None),
        ("V12", "Flamingo", "https://www.flamingo.com.co/", TODAS, None),
        ("V13", "HP Colombia", "https://www.hp.com/co-es/shop/", ["portatil", "monitor"], "HP"),
        ("V14", "LG Colombia", "https://www.lg.com/co/", ["monitor", "audifonos"], "LG"),
        ("V15", "Sony Store", "https://store.sony.com.co/", ["audifonos"], "Sony"),
    )
]
# Activas al cargar CotIA (D131); el visitante activa las que quiera, sin tope (D144).
EN_VIVO_POR_DEFECTO = {"V3", "V4", "V5", "V6", "V7"}
# Por encima de esta cifra la interfaz avisa que las acciones se reparten entre más tiendas.
TIENDAS_RECOMENDADAS = 5
