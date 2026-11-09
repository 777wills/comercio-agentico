"""Lectura de fuentes: trae el texto de cada proveedor tal como lo publica. Sin LLM y sin costo.

- Web (P2, P3, corpus A): crawl4ai con Chromium sin interfaz → Markdown + enlaces del mismo sitio.
- Documentos (P4 PDF, P5 chat): descarga HTTP; el PDF pasa por pypdf.
- MCP (P1): cliente de FastMCP; busca y trae la ficha completa de cada resultado.

Todo lo que devuelve este módulo es contenido de terceros (plano de datos).
"""

from __future__ import annotations

import io
import json
import os
from dataclasses import dataclass, field
from typing import Any

import httpx
from pypdf import PdfReader

from comercio_agentico.agente.fuentes import Fuente, RegistroFuentes

os.environ.setdefault("CRAWL4AI_NO_CLOUD_NOTICE", "1")


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

    def __init__(self, registro: RegistroFuentes, max_resultados_mcp: int = 8) -> None:
        self.registro = registro
        self.max_resultados_mcp = max_resultados_mcp
        self._cache: dict[str, Documento] = {}
        self._crawler: Any = None
        self._http: httpx.AsyncClient | None = None

    async def __aenter__(self) -> Lector:
        self._http = httpx.AsyncClient(timeout=30)
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
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig

        if self._crawler is None:  # Chromium arranca solo si la tarea abre alguna página
            self._crawler = AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False))
            await self._crawler.__aenter__()
        resultado = await self._crawler.arun(
            url, config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)
        )
        if not resultado.success:
            raise OSError(f"No se pudo abrir {url}: {resultado.error_message}")
        markdown = resultado.markdown
        texto = getattr(markdown, "raw_markdown", None) or str(markdown)
        enlaces = sorted(
            {
                e["href"]
                for e in resultado.links.get("internal", [])
                if e.get("href") and self.registro.por_url(e["href"]) == fuente
            }
            - {url}
        )
        doc = Documento(fuente=fuente, consulta=url, texto=texto, enlaces=enlaces)
        self._cache[url] = doc
        return doc

    async def leer_documento(self, url: str) -> Documento:
        if url in self._cache:
            return self._cache[url]
        fuente = self._fuente(url)
        assert self._http is not None, "Use Lector como administrador de contexto"
        respuesta = await self._http.get(url)
        respuesta.raise_for_status()
        es_pdf = url.lower().endswith(".pdf") or "pdf" in respuesta.headers.get("content-type", "")
        if es_pdf:
            lector = PdfReader(io.BytesIO(respuesta.content))
            texto = "\n".join(pagina.extract_text() or "" for pagina in lector.pages)
        else:
            texto = respuesta.content.decode("utf-8", errors="replace")
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
