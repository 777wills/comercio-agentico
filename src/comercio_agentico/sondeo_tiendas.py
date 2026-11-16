"""Sondeo de tiendas candidatas para el modo en vivo con el criterio de D112 (S09f, D127). US$0.

Por tienda: robots.txt para el robot de CotIA, respuesta de la portada a un cliente automatizado y
búsqueda de cláusulas sobre robots o extracción automatizada en las páginas de términos enlazadas
desde la portada. Guarda solo el veredicto y fragmentos cortos de los términos, nunca la página.

Uso: ``python -m comercio_agentico.sondeo_tiendas`` (o ``make sondeo-tiendas``).
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import date
from urllib.parse import urljoin

import httpx

from comercio_agentico.agente.web_abierta import AGENTE_USUARIO, Cortesia, UrlNoPermitida, sitio
from comercio_agentico.corpus_b import RAIZ

SALIDA = RAIZ / "resultados" / "tiendas" / f"sondeo_{date.today().isoformat()}.jsonl"

CANDIDATAS = [
    ("Alkosto", "https://www.alkosto.com/"),
    ("Ktronix", "https://www.ktronix.com/"),
    ("Alkomprar", "https://www.alkomprar.com/"),
    ("Falabella", "https://www.falabella.com.co/falabella-co"),
    ("Samsung Colombia", "https://www.samsung.com/co/"),
    ("Panamericana", "https://www.panamericana.com.co/"),
    ("iShop", "https://co.tiendasishop.com/"),
    ("Mac Center", "https://mac-center.com/"),
    ("Tienda Claro", "https://tienda.claro.com.co/"),
    ("Clevercel", "https://www.clevercel.co/"),
    ("Tecnoplaza", "https://www.tecnoplaza.com.co/"),
    ("Homecenter", "https://www.homecenter.com.co/homecenter-co/"),
    ("Tienda Movistar", "https://tienda.movistar.com.co/"),
    ("Tienda Tigo", "https://tienda.tigo.com.co/"),
    ("Home Sentry", "https://www.homesentry.co/"),
    ("Pepe Ganga", "https://www.pepeganga.com/"),
    ("Makro", "https://www.makro.com.co/"),
    ("Tiendas Metro", "https://www.tiendasmetro.co/"),
    ("Carulla", "https://www.carulla.com/"),
    ("Flamingo", "https://www.flamingo.com.co/"),
    ("Electrojaponesa", "https://www.electrojaponesa.com/"),
    ("HP Colombia", "https://www.hp.com/co-es/shop/"),
    ("Dell Colombia", "https://www.dell.com/es-co"),
    ("Motorola Colombia", "https://www.motorola.com/co/"),
    ("LG Colombia", "https://www.lg.com/co/"),
    ("Sony Store Colombia", "https://store.sony.com.co/"),
    ("Huawei Colombia", "https://consumer.huawei.com/co/"),
    ("Apple Colombia", "https://www.apple.com/co/"),
    ("Asus Colombia", "https://www.asus.com/co/"),
    ("Xiaomi Colombia", "https://www.mi.com/co/"),
    ("Lenovo Colombia", "https://www.lenovo.com/co/es/"),
    ("Éxito", "https://www.exito.com/"),
    ("Olímpica", "https://www.olimpica.com/"),
    ("Jumbo", "https://www.tiendasjumbo.co/"),
    ("Mercado Libre", "https://www.mercadolibre.com.co/"),
    # Ampliación del 16-nov-2026 (D147)
    ("Janus", "https://janus.com.co/"),
    ("Encarguelo", "https://encarguelo.com/"),
    ("Tauret Computadores", "https://www.tauretcomputadores.com/"),
    ("Kalley", "https://www.kalley.com.co/"),
    ("Honor Colombia", "https://www.honor.com/co/"),
    ("JBL Colombia", "https://co.jbl.com/"),
    ("Acer Store Colombia", "https://store.acer.com/es-co/"),
]

ENLACE_TERMINOS = re.compile(
    r'href="([^"#]+)"[^>]*>(?:(?!</a>).){0,200}?(t[ée]rminos|condiciones|legal)', re.I | re.S
)
CLAUSULA = re.compile(
    r"robots?\b|arañas?\b|spiders?\b|scrap|crawler|rastre(?:o|ar|adores)|automatizad|"
    r"miner[íi]a de datos|extracci[óo]n (?:masiva|de datos|de contenido)",
    re.I,
)
MAX_TERMINOS = 3


def _texto(html: str) -> str:
    sin_codigo = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S | re.I)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", sin_codigo))


def clausulas(texto: str, ancho: int = 90) -> list[str]:
    """Fragmentos cortos alrededor de cada mención de robots o extracción automatizada."""
    return [
        texto[max(0, m.start() - ancho) : m.end() + ancho].strip() for m in CLAUSULA.finditer(texto)
    ][:5]


def enlaces_terminos(html: str, base: str) -> list[str]:
    vistos: list[str] = []
    for m in ENLACE_TERMINOS.finditer(html):
        url = urljoin(base, m.group(1))
        if url.startswith("http") and url not in vistos:
            vistos.append(url)
    return vistos[:MAX_TERMINOS]


async def sondear(http: httpx.AsyncClient, cortesia: Cortesia, nombre: str, url: str) -> dict:
    fila: dict = {"tienda": nombre, "url": url, "fecha": date.today().isoformat()}
    try:
        await cortesia.permitir(url)
        fila["robots"] = "permite"
    except UrlNoPermitida as error:
        fila["robots"] = f"no: {error}"
    try:
        r = await http.get(url, follow_redirects=True)
        fila |= {"estado": r.status_code, "bytes": len(r.content), "final": str(r.url)}
    except httpx.HTTPError as error:
        fila |= {"estado": None, "error": type(error).__name__}
        return fila
    fila["terminos"] = []
    for enlace in enlaces_terminos(r.text, str(r.url)):
        try:
            await cortesia.permitir(enlace)
            t = await http.get(enlace, follow_redirects=True)
        except (UrlNoPermitida, httpx.HTTPError):
            continue
        fila["terminos"].append(
            {"url": enlace, "estado": t.status_code, "clausulas": clausulas(_texto(t.text))}
        )
    return fila


async def main() -> None:
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(
        timeout=20, headers={"User-Agent": AGENTE_USUARIO}, follow_redirects=False
    ) as http:
        cortesia = Cortesia(http, pausa_s=1.0)
        filas = await asyncio.gather(*(sondear(http, cortesia, n, u) for n, u in CANDIDATAS))
    with SALIDA.open("w", encoding="utf-8") as salida:
        for fila in filas:
            salida.write(json.dumps(fila, ensure_ascii=False) + "\n")
            n_cl = sum(len(t["clausulas"]) for t in fila.get("terminos", []))
            print(
                f"{fila['tienda']:20} robots={fila['robots'][:40]:40} estado={fila.get('estado')} "
                f"términos={len(fila.get('terminos', []))} cláusulas={n_cl} {sitio(fila['url'])}"
            )
    print(f"→ {SALIDA}")


if __name__ == "__main__":
    asyncio.run(main())
