"""Salvaguardas para leer internet abierta: tiendas en vivo y fuentes del visitante (D112).

- **SSRF:** solo se abren URL http(s) cuyo host resuelve a direcciones públicas; nunca
  ``localhost``, redes privadas, enlace local ni metadatos de la nube.
- **robots.txt:** se consulta una vez por sitio y se respeta para el agente de usuario del robot.
- **Cortesía:** pausa mínima entre peticiones a un mismo sitio.
- **Tamaño:** tope de texto y de enlaces por página, para no inflar los tokens del extractor ni
  del planificador.
- **Saneamiento (D120):** imágenes, ``data:`` URI, parámetros de URL y cadenas base64 largas
  salen del texto antes de C2 y del extractor: no informan la compra y disparan el clasificador.

El corpus congelado (servido en local) no pasa por aquí: es configuración de confianza.
"""

from __future__ import annotations

import asyncio
import ipaddress
import re
import socket
import time
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx

AGENTE_USUARIO = "ComercioAgenticoBot/0.1"
PAUSA_POR_SITIO_S = 2.0
MAX_TEXTO_ABIERTA = 30_000  # caracteres por página o documento
MAX_ENLACES_ABIERTA = 150


class UrlNoPermitida(ValueError):
    """La URL no es pública, no es http(s) o robots.txt la prohíbe."""


def sitio(url: str) -> str:
    partes = urlsplit(url)
    return f"{partes.scheme}://{partes.netloc}"


def validar_url_publica(url: str) -> str:
    """Devuelve la URL si es http(s) y todas las direcciones de su host son públicas."""
    partes = urlsplit(url)
    if partes.scheme not in ("http", "https") or not partes.hostname:
        raise UrlNoPermitida("Solo se aceptan direcciones http o https.")
    try:
        direcciones = {info[4][0] for info in socket.getaddrinfo(partes.hostname, None)}
    except socket.gaierror as error:
        raise UrlNoPermitida(f"No se pudo resolver {partes.hostname}.") from error
    for d in direcciones:
        if not ipaddress.ip_address(d.split("%")[0]).is_global:
            raise UrlNoPermitida(f"{partes.hostname} apunta a una dirección no pública.")
    return url


class Cortesia:
    """robots.txt en caché y pausa por sitio, compartidos por las lecturas de una tarea."""

    def __init__(self, http: httpx.AsyncClient, pausa_s: float = PAUSA_POR_SITIO_S) -> None:
        self.http = http
        self.pausa_s = pausa_s
        self._robots: dict[str, RobotFileParser] = {}
        self._ultima: dict[str, float] = {}
        self._cerrojos: dict[str, asyncio.Lock] = {}

    async def _reglas(self, base: str) -> RobotFileParser:
        if base not in self._robots:
            reglas = RobotFileParser()
            try:
                r = await self.http.get(
                    f"{base}/robots.txt", headers={"User-Agent": AGENTE_USUARIO}, timeout=15
                )
                # Sin robots.txt (4xx) todo está permitido; un 5xx o un fallo de red, nada.
                reglas.parse(r.text.splitlines() if r.status_code < 400 else [])
                if r.status_code >= 500:
                    reglas.disallow_all = True
            except httpx.HTTPError:
                reglas.disallow_all = True
            self._robots[base] = reglas
        return self._robots[base]

    async def permitir(self, url: str) -> None:
        """Valida la URL y espera su turno; levanta ``UrlNoPermitida`` si no se puede leer."""
        validar_url_publica(url)
        base = sitio(url)
        if not (await self._reglas(base)).can_fetch(AGENTE_USUARIO, url):
            raise UrlNoPermitida(f"El robots.txt de {base} no permite leer {url}.")
        cerrojo = self._cerrojos.setdefault(base, asyncio.Lock())
        async with cerrojo:
            espera = self._ultima.get(base, 0.0) + self.pausa_s - time.monotonic()
            if espera > 0:
                await asyncio.sleep(espera)
            self._ultima[base] = time.monotonic()


PATRON_PRECIO = re.compile(r"\$\s?\d{1,3}(?:[.,]\d{3})+")
MARCA_CONTENIDO = "Contenido de la página:\n"
ANTES, DESPUES = 4, 2  # líneas alrededor de cada precio (título arriba, envío o stock abajo)
IMAGEN_MD = re.compile(r"!\[([^\]]*)\]\((?:\\.|[^()\\])*\)")
DATA_URI = re.compile(r"data:[\w.+-]+/[\w.+-]+[,;]\S*")
PARAMETROS_URL = re.compile(r"(https?://[^\s?#()\"'<>]+)[?#][^\s()\"'<>]*")
BASE64_LARGO = re.compile(r"[A-Za-z0-9+/]{40,}={0,2}")


def sanear(texto: str) -> str:
    """Quita del Markdown el ruido codificado que no informa la compra (D120).

    Las imágenes quedan como su texto alternativo; los ``data:`` URI y los parámetros de las URL
    se eliminan; las cadenas base64 largas pasan a «…». Los precios, títulos y rutas de las fichas
    no cambian (las rutas con guiones no son base64).
    """
    texto = IMAGEN_MD.sub(lambda m: m.group(1), texto)
    texto = DATA_URI.sub("", texto)
    texto = PARAMETROS_URL.sub(r"\1", texto)
    return BASE64_LARGO.sub("…", texto)


def _foco_en_precios(texto: str) -> str:
    """En páginas largas, el menú ocupa el inicio: se conservan las líneas cerca de un precio."""
    lineas = texto.splitlines()
    marcadas = [i for i, linea in enumerate(lineas) if PATRON_PRECIO.search(linea)]
    if not marcadas:
        return texto
    guardar = sorted({j for i in marcadas for j in range(i - ANTES, i + DESPUES + 1)})
    partes, previa = [], -2
    for j in guardar:
        if 0 <= j < len(lineas):
            if j != previa + 1:
                partes.append("…")
            partes.append(lineas[j])
            previa = j
    return "\n".join(partes)


def _prioridad(enlace: str) -> int:
    e = enlace.lower()
    if any(k in e for k in ("/p/", "/product/", "/producto", "/buy/")) or e.endswith("/p"):
        return 0  # ficha de producto
    if any(k in e for k in ("/c/", "/category/", "/categoria")):
        return 1
    return 2


def recortar(texto: str, enlaces: list[str], saneado: bool = True) -> tuple[str, list[str]]:
    """Tope de tamaño para páginas reales: foco en los productos y en sus enlaces."""
    if saneado:
        texto = sanear(texto)
    if len(texto) > MAX_TEXTO_ABIERTA:
        cabeza, marca, cuerpo = texto.partition(MARCA_CONTENIDO)
        if not marca:  # sin bloque schema.org
            cabeza, cuerpo = "", texto
        texto = cabeza + marca + _foco_en_precios(cuerpo)
        if len(texto) > MAX_TEXTO_ABIERTA:
            texto = texto[:MAX_TEXTO_ABIERTA] + "\n…(recortado)"
    limpios = [e for e in enlaces if "?" not in e] or enlaces
    return texto, sorted(limpios, key=_prioridad)[:MAX_ENLACES_ABIERTA]
