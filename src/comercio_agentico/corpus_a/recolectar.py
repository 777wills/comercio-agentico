"""Recolector de hechos del corpus A (S04). Sin LLM y sin costo de modelos.

Lee cada ficha de ``semillas.yaml`` con crawl4ai en modo HTTP (sin navegador), con agente de usuario
identificable, robots.txt respetado y una pausa de 4–8 s entre peticiones a la misma tienda. De la
ficha se extraen de forma determinista los datos estructurados (microdatos y JSON-LD de schema.org,
con ``extruct``) y se descarta el HTML: solo quedan los hechos y su SHA-256.

Uso: ``uv run python -m comercio_agentico.corpus_a.recolectar``.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import random
import re
from datetime import UTC, datetime
from typing import Any

import extruct
import yaml

from comercio_agentico.corpus_a import (
    AGENTE_USUARIO,
    RUTA_HECHOS,
    RUTA_MANIFIESTO,
    RUTA_SEMILLAS,
    TIENDAS,
)

PAUSA_S = (4.0, 8.0)


def _texto(valor: Any) -> str | None:
    if isinstance(valor, dict):
        valor = valor.get("name")
    if isinstance(valor, list):
        valor = valor[0] if valor else None
    if valor is None or str(valor).strip().lower() in {"", "null", "none"}:
        return None
    return str(valor).strip()


def _disponibilidad(valor: Any) -> str:
    v = str(valor or "").lower()
    if "instock" in v:
        return "en_stock"
    if "outofstock" in v or "soldout" in v:
        return "agotado"
    if "preorder" in v or "backorder" in v:
        return "bajo_pedido"
    return "desconocida"


def _envio(oferta: dict) -> tuple[float | None, int | None]:
    """Costo y días hábiles máximos de entrega desde ``shippingDetails`` (si los publica)."""
    detalles = oferta.get("shippingDetails") or []
    detalles = detalles if isinstance(detalles, list) else [detalles]
    for d in detalles:
        costo = (d.get("shippingRate") or {}).get("value")
        tiempo = d.get("deliveryTime") or {}
        dias = [(tiempo.get(k) or {}).get("maxValue") for k in ("handlingTime", "transitTime")]
        dias_num = [int(float(x)) for x in dias if x not in (None, "")]
        return (float(costo) if costo not in (None, "") else None), (
            sum(dias_num) if dias_num else None
        )
    return None, None


def extraer_hechos(html: str, url: str) -> dict:
    """Datos de la ficha según schema.org ``Product``; vacío si la página no lo publica."""
    datos = extruct.extract(html, base_url=url, syntaxes=["microdata", "json-ld"], uniform=True)
    productos = [
        (sintaxis, it)
        for sintaxis in ("json-ld", "microdata")
        for it in datos.get(sintaxis, [])
        if "Product" in str(it.get("@type"))
    ]
    if not productos:
        return {}
    sintaxis, p = productos[0]
    ofertas = p.get("offers") or []
    ofertas = ofertas if isinstance(ofertas, list) else [ofertas]
    precios = []
    for o in ofertas:
        try:
            precio = float(o.get("price"))
        except (TypeError, ValueError):
            continue
        costo_envio, dias = _envio(o)
        precios.append(
            {
                "precio": precio,
                "moneda": o.get("priceCurrency") or "COP",
                "disponibilidad": _disponibilidad(o.get("availability")),
                "vendedor": _texto(o.get("seller")),
                "costo_envio": costo_envio,
                "entrega_dias_max": dias,
            }
        )
    gtin = next(
        (
            _texto(p.get(k))
            for k in ("gtin13", "gtin", "gtin12", "gtin14", "gtin8")
            if _texto(p.get(k))
        ),
        None,
    )
    return {
        "sintaxis": sintaxis,
        "titulo": _texto(p.get("name")),
        "marca": _texto(p.get("brand")),
        "gtin": gtin,
        "mpn": _texto(p.get("mpn")),
        "sku": _texto(p.get("sku")),
        "categoria_tienda": _texto(p.get("category")),
        "ofertas": precios,
    }


def precios_etiquetados(html: str, precios_ld: list[float] | None = None) -> list[dict]:
    """Falabella publica en el JSON-LD dos ofertas sin decir cuál es cuál; los datos de la página
    sí las etiquetan: ``normalPrice`` (tachado), ``eventPrice``/``internetPrice`` (para cualquiera)
    y ``cmrPrice`` (solo con su tarjeta). La página trae un arreglo ``prices`` por variante: se
    toma el primero que contiene todos los precios del JSON-LD (el de la variante publicada)."""
    objetivo = set(precios_ld or [])
    decodificador = json.JSONDecoder()
    for m in re.finditer(r'"prices":\[\{', html):
        try:
            lista, _ = decodificador.raw_decode(html, m.start() + len('"prices":'))
        except json.JSONDecodeError:
            continue
        salida = []
        for p in lista:
            try:
                valor = float(str(p["price"][0]).replace(".", "").replace(",", "."))
            except (KeyError, IndexError, ValueError):
                continue
            salida.append(
                {
                    "tipo": p.get("type"),
                    "precio": valor,
                    "tachado": bool(p.get("crossed")),
                    "vigencia": p.get("validity"),
                }
            )
        if objetivo <= {x["precio"] for x in salida}:
            return salida
    return []


def gtin_en_url(url: str) -> str | None:
    m = re.search(r"/p/(\d{8,14})$", url)
    return m.group(1) if m else None


async def _recorrer_tienda(crawler: Any, config: Any, tareas: list[tuple[str, str, str]]) -> list:
    salida = []
    for i, (producto, tienda, url) in enumerate(tareas):
        if i:
            await asyncio.sleep(random.uniform(*PAUSA_S))
        r = await crawler.arun(url, config=config)
        html = r.html or ""
        registro = {
            "producto": producto,
            "tienda": tienda,
            "url": url,
            "fecha": datetime.now(UTC).isoformat(timespec="seconds"),
            "http": r.status_code,
            "bytes": len(html.encode()),
            "sha256": hashlib.sha256(html.encode()).hexdigest() if html else None,
            "error": None if r.success else (r.error_message or "")[:300],
        }
        hechos = extraer_hechos(html, url) if r.success and html else {}
        if hechos and tienda == "A3":
            precios_ld = [o["precio"] for o in hechos.get("ofertas", [])]
            hechos["precios_etiquetados"] = precios_etiquetados(html, precios_ld)
        salida.append((registro, {**registro, "gtin_url": gtin_en_url(url), **hechos}))
        print(f"{tienda} {producto} {r.status_code} {len(hechos.get('ofertas', []))} ofertas")
    return salida


async def recolectar(solo: set[str] | None = None) -> None:
    from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig, HTTPCrawlerConfig
    from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy

    semillas = yaml.safe_load(RUTA_SEMILLAS.read_text())["productos"]
    por_tienda: dict[str, list] = {t: [] for t in TIENDAS}
    for s in semillas:
        for tienda, url in s["urls"].items():
            if solo is None or tienda in solo:
                por_tienda[tienda].append((s["id"], tienda, url))

    estrategia = AsyncHTTPCrawlerStrategy(
        browser_config=HTTPCrawlerConfig(
            method="GET", headers={"User-Agent": AGENTE_USUARIO}, follow_redirects=True
        )
    )
    # El agente de usuario va en las cabeceras: con la estrategia HTTP, ``user_agent`` en
    # CrawlerRunConfig falla (crawl4ai 0.9.5). robots.txt se evalúa con las reglas de ``*``,
    # que son las únicas que aplican al robot en las tres tiendas.
    config = CrawlerRunConfig(check_robots_txt=True, cache_mode=CacheMode.BYPASS, verbose=False)
    async with AsyncWebCrawler(crawler_strategy=estrategia) as crawler:
        # Las tres tiendas en paralelo; dentro de cada una, en serie y con pausa.
        lotes = await asyncio.gather(
            *(_recorrer_tienda(crawler, config, t) for t in por_tienda.values())
        )
    filas = [f for lote in lotes for f in lote]
    if solo is not None and RUTA_HECHOS.exists():  # conserva las lecturas de las demás tiendas
        previos = [json.loads(linea) for linea in RUTA_HECHOS.read_text().splitlines()]
        lecturas = json.loads(RUTA_MANIFIESTO.read_text())["lecturas"]
        filas = [
            (r, h) for r, h in zip(lecturas, previos, strict=True) if h["tienda"] not in solo
        ] + filas
    filas.sort(key=lambda f: (f[1]["producto"], f[1]["tienda"]))
    RUTA_HECHOS.write_text(
        "".join(json.dumps(h, ensure_ascii=False) + "\n" for _, h in filas), encoding="utf-8"
    )
    RUTA_MANIFIESTO.write_text(
        json.dumps(
            {
                "descripcion": "Lectura única de fichas públicas; el HTML no se conserva (D70).",
                "agente_usuario": AGENTE_USUARIO,
                "robots_txt_respetado": True,
                "pausa_s": PAUSA_S,
                "lecturas": [r for r, _ in filas],
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"{len(filas)} fichas → {RUTA_HECHOS.name}, {RUTA_MANIFIESTO.name}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tiendas", nargs="*", help="Releer solo estas tiendas (p. ej. A3).")
    args = parser.parse_args()
    asyncio.run(recolectar(set(args.tiendas) if args.tiendas else None))
