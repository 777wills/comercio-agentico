"""Lectura de fuentes: trae el texto de cada proveedor tal como lo publica. Sin LLM y sin costo.

- Web (P2, P3, corpus A): crawl4ai con Chromium sin interfaz → Markdown + enlaces del mismo sitio,
  precedido de los datos schema.org ``Product``/``Offer`` (JSON-LD y microdatos, con ``extruct``):
  la conversión a Markdown los descarta y muchas tiendas publican ahí la disponibilidad (D74).
- Documentos (P4 PDF, P5 chat): descarga HTTP; el PDF pasa por pypdf.
- MCP (P1): cliente de FastMCP; busca y trae la ficha completa de cada resultado.

Todo lo que devuelve este módulo es contenido de terceros (plano de datos).
"""

from __future__ import annotations

import asyncio
import io
import json
import os
from dataclasses import dataclass, field
from typing import Any

import httpx
from pypdf import PdfReader

from comercio_agentico.agente.fuentes import Fuente, RegistroFuentes
from comercio_agentico.agente.web_abierta import AGENTE_USUARIO, Cortesia, recortar

os.environ.setdefault("CRAWL4AI_NO_CLOUD_NOTICE", "1")

MAX_DATOS_ESTRUCTURADOS = 6_000  # caracteres del bloque schema.org por página
TIPOS_SCHEMA = ("Product", "Offer", "ProductGroup")


CAMPOS_LARGOS = ("description", "review", "image", "aggregateRating", "isRelatedTo", "isSimilarTo")


def _sin_campos_largos(objeto: Any) -> Any:
    """Quita textos largos (descripciones en HTML, reseñas) que agotan el tope sin dar precio."""
    if isinstance(objeto, dict):
        return {k: _sin_campos_largos(v) for k, v in objeto.items() if k not in CAMPOS_LARGOS}
    if isinstance(objeto, list):
        return [_sin_campos_largos(v) for v in objeto]
    return objeto


def datos_estructurados(html: str, url: str, ligero: bool = False) -> str:
    """Texto con los objetos schema.org de producto u oferta de la página; vacío si no hay.

    Es contenido del proveedor como cualquier otro (plano de datos): no se interpreta aquí.
    """
    import extruct

    try:
        datos = extruct.extract(html, base_url=url, syntaxes=["json-ld", "microdata"], uniform=True)
    except Exception:  # HTML mal formado: la página se lee igual, solo sin este bloque
        return ""
    objetos = [
        it
        for sintaxis in ("json-ld", "microdata")
        for it in datos.get(sintaxis, [])
        if isinstance(it, dict) and any(t in str(it.get("@type")) for t in TIPOS_SCHEMA)
    ]
    if not objetos:
        return ""
    if ligero:  # solo en la web abierta: el corpus congelado conserva su lectura de D74
        objetos = [_sin_campos_largos(o) for o in objetos]
    cuerpo = json.dumps(objetos, ensure_ascii=False, separators=(",", ":"))
    if len(cuerpo) > MAX_DATOS_ESTRUCTURADOS:
        cuerpo = cuerpo[:MAX_DATOS_ESTRUCTURADOS] + " …(recortado)"
    return f"Datos estructurados de la página (schema.org):\n{cuerpo}\n\nContenido de la página:\n"


class FuenteNoAutorizada(ValueError):
    """La URL no pertenece a ninguna fuente del registro."""


@dataclass
class Documento:
    fuente: Fuente
    consulta: str  # URL o llamada MCP que produjo el texto
    texto: str
    enlaces: list[str] = field(default_factory=list)


class Lector:
    """Abre las conexiones una vez por tarea y guarda en caché lo ya leído.

    Uso: ``async with Lector(registro) as lector: doc = await lector.abrir_pagina(url)``.
    """

    def __init__(
        self,
        registro: RegistroFuentes,
        max_resultados_mcp: int = 8,
        documentos: dict[str, str] | None = None,
    ) -> None:
        self.registro = registro
        self.max_resultados_mcp = max_resultados_mcp
        # PDF que subió el visitante (D113): URL interna ``pdf://<sha256>`` → texto ya extraído.
        self.documentos = documentos or {}
        self._cortesia: Cortesia | None = None
        self._arranque = asyncio.Lock()  # varias lecturas en paralelo: un solo Chromium
        self._cache: dict[str, Documento] = {}
        self._crawler: Any = None
        self._http: httpx.AsyncClient | None = None

    async def __aenter__(self) -> Lector:
        self._http = httpx.AsyncClient(timeout=30, headers={"User-Agent": AGENTE_USUARIO})
        self._cortesia = Cortesia(self._http)
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._crawler is not None:
            await self._crawler.__aexit__(None, None, None)
        if self._http is not None:
            await self._http.aclose()

    def _fuente(self, url: str) -> Fuente:
        fuente = self.registro.por_url(url)
        if fuente is None:
            raise FuenteNoAutorizada(f"URL fuera de las fuentes registradas: {url}")
        return fuente

    async def abrir_pagina(self, url: str) -> Documento:
        if url in self._cache:
            return self._cache[url]
        fuente = self._fuente(url)
        if fuente.abierta:
            assert self._cortesia is not None, "Use Lector como administrador de contexto"
            await self._cortesia.permitir(url)
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig

        async with self._arranque:  # Chromium arranca solo si la tarea abre alguna página
            if self._crawler is None:
                crawler = AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False))
                await crawler.__aenter__()
                self._crawler = crawler
        resultado = await self._crawler.arun(
            url,
            config=CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                verbose=False,
                user_agent=AGENTE_USUARIO,
                # Tiendas reales: los productos llegan por JavaScript y con carga diferida.
                **(
                    {"scan_full_page": True, "scroll_delay": 0.3, "delay_before_return_html": 2.0}
                    if fuente.abierta
                    else {}
                ),
            ),
        )
        if not resultado.success:
            raise OSError(f"No se pudo abrir {url}: {resultado.error_message}")
        markdown = resultado.markdown
        texto = getattr(markdown, "raw_markdown", None) or str(markdown)
        texto = datos_estructurados(resultado.html or "", url, ligero=fuente.abierta) + texto
        enlaces = sorted(
            {
                e["href"]
                for e in resultado.links.get("internal", [])
                if e.get("href") and self.registro.por_url(e["href"]) == fuente
            }
            - {url}
        )
        if fuente.abierta:
            texto, enlaces = recortar(texto, enlaces)
        doc = Documento(fuente=fuente, consulta=url, texto=texto, enlaces=enlaces)
        self._cache[url] = doc
        return doc

    async def leer_documento(self, url: str) -> Documento:
        if url in self._cache:
            return self._cache[url]
        fuente = self._fuente(url)
        if url in self.documentos:  # PDF del visitante: ya validado y extraído al subirlo
            doc = Documento(
                fuente=fuente, consulta=url, texto=recortar(self.documentos[url], [])[0]
            )
            self._cache[url] = doc
            return doc
        assert self._http is not None, "Use Lector como administrador de contexto"
        if fuente.abierta:
            assert self._cortesia is not None
            await self._cortesia.permitir(url)
        respuesta = await self._http.get(url)
        respuesta.raise_for_status()
        es_pdf = url.lower().endswith(".pdf") or "pdf" in respuesta.headers.get("content-type", "")
        if es_pdf:
            lector = PdfReader(io.BytesIO(respuesta.content))
            texto = "\n".join(pagina.extract_text() or "" for pagina in lector.pages)
        else:
            texto = respuesta.content.decode("utf-8", errors="replace")
        if fuente.abierta:
            texto = recortar(texto, [])[0]
        doc = Documento(fuente=fuente, consulta=url, texto=texto)
        self._cache[url] = doc
        return doc

    async def consultar_mcp(self, texto: str, familia: str | None = None) -> Documento:
        """Busca en el proveedor MCP y trae la ficha completa (precio, flete, plazo, EAN) de cada
        resultado: la búsqueda sola no trae el costo de envío."""
        clave = f"mcp:{texto}|{familia}"
        if clave in self._cache:
            return self._cache[clave]
        fuentes = self.registro.por_herramienta("consultar_mcp")
        if not fuentes:
            raise FuenteNoAutorizada("No hay proveedor MCP registrado")
        fuente = fuentes[0]
        from fastmcp import Client

        argumentos: dict[str, Any] = {"texto": texto, "limite": self.max_resultados_mcp}
        if familia:
            argumentos["familia"] = familia
        async with Client(fuente.url) as cliente:
            hallados = (await cliente.call_tool("buscar_productos", argumentos)).data or []
            fichas = [
                (await cliente.call_tool("detalle_producto", {"referencia": h["referencia"]})).data
                for h in hallados
            ]
        consulta = f"mcp://{fuente.id}/buscar_productos?" + json.dumps(
            argumentos, ensure_ascii=False
        )
        cuerpo = json.dumps(fichas, ensure_ascii=False, indent=1) if fichas else "[]"
        doc = Documento(fuente=fuente, consulta=consulta, texto=cuerpo)
        self._cache[clave] = doc
        return doc
