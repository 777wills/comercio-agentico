"""Construcción del corpus A a partir de los hechos (S04, D70). Determinista, sin red y sin LLM.

Entradas (versionadas): ``hechos.jsonl`` (lo leído de las tiendas) y ``equivalencias.yaml``
(qué ficha de Falabella es el mismo producto). Salidas:

- ``catalogo.json``: un producto por EAN de Alkosto/Ktronix, con los atributos de su título.
- ``verdad.json``: las ofertas de cada tienda, en el formato del corpus B.
- ``sitio/a1|a2|a3/``: las tiendas reconstruidas. Reproducen la *estructura* de cada sitio
  (microdatos en A1 y A2; en A3, JSON-LD con dos ofertas sin etiqueta y tres precios visibles,
  uno de ellos solo con la tarjeta de la tienda), sin textos, imágenes ni diseño de la tienda.

Uso: ``uv run python -m comercio_agentico.corpus_a.construir`` (US$0).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment

from comercio_agentico.corpus_a import RAIZ, RUTA_HECHOS, TIENDAS
from comercio_agentico.corpus_b.catalogo import ProductoCatalogo
from comercio_agentico.esquema import gtin_valido

RUTA_EQUIVALENCIAS = RAIZ / "equivalencias.yaml"
RUTA_CATALOGO_A = RAIZ / "catalogo.json"
RUTA_VERDAD_A = RAIZ / "verdad.json"
DIR_SITIO = RAIZ / "sitio"
FECHA_HECHOS = "9-nov-2026"
NOMBRES = {"A1": "Alkosto", "A2": "Ktronix", "A3": "Falabella"}


# --------------------------------------------------------------------------------------------------
# Hechos → catálogo


def gtin13(codigo: str) -> str | None:
    """EAN-13 o UPC-12 (se completa con un cero) con dígito de control válido."""
    codigo = codigo.zfill(13) if len(codigo) == 12 else codigo
    return codigo if len(codigo) == 13 and gtin_valido(codigo) else None


def atributos_del_titulo(titulo: str, categoria: str) -> dict[str, Any]:
    """Solo lo que el título dice de forma explícita; lo demás queda sin dato."""
    t = titulo.replace(",", ".")
    attrs: dict[str, Any] = {}
    if m := re.search(r'(\d+(?:\.\d+)?)"\s*Pulgadas', t):
        attrs["tamano_pantalla"] = float(m.group(1))
    if m := re.search(r"RAM\s*(\d+)\s*GB", t, re.I):
        attrs["memoria_ram"] = int(m.group(1))
    capacidades = re.findall(r"(\d+)\s*(GB|TB)\b", re.sub(r"RAM\s*\d+\s*GB", "", t, flags=re.I))
    if capacidades and categoria in ("celular", "portatil", "almacenamiento"):
        n, u = capacidades[-1]
        attrs["almacenamiento"] = int(n) * (1024 if u.upper() == "TB" else 1)
    for etiqueta, canonico in (("4K", "4K"), ("QHD", "QHD"), ("FHD", "FHD")):
        if categoria == "monitor" and re.search(rf"\b{etiqueta}\b", t):
            attrs["resolucion"] = canonico
            break
    if categoria == "audifonos":
        if re.search(r"\bAlámbric", t):
            attrs["inalambrico"] = False
        elif re.search(r"Inalámbric", t):
            attrs["inalambrico"] = True
        if re.search(r"Cancelación de", t):
            attrs["cancelacion_ruido"] = True
    if categoria == "portatil" and (
        m := re.search(r"(Intel Core Ultra \d+(?: \w+)?|Ryzen \d+)", t)
    ):
        attrs["procesador"] = m.group(1)
    if categoria == "almacenamiento":
        if re.search(r"Micro SD", t, re.I):
            attrs["tipo_almacenamiento"] = "microSD"
        elif re.search(r"USB", t):
            attrs["tipo_almacenamiento"] = "USB"
        elif re.search(r"Disco Estado Solido Externo|SSD", t, re.I) or re.search(
            r"Estado Solido", t, re.I
        ):
            attrs["tipo_almacenamiento"] = "SSD"
    return attrs


def _modelo(titulo: str) -> str:
    """Nombre comercial: el título sin la categoría ni lo que va después del primer guion."""
    base = re.split(r"\s+-\s+", titulo)[0]
    return re.sub(
        r"^(Computador Portátil( 2 en 1)?|Monitor|Audífonos( de Diadema)?|Memoria|Disco|Unidad)\s+",
        "",
        base,
    ).strip()


def _por_producto(hechos: list[dict]) -> dict[str, dict[str, dict]]:
    salida: dict[str, dict[str, dict]] = {}
    for h in hechos:
        salida.setdefault(h["producto"], {})[h["tienda"]] = h
    return salida


def _precio_a3(h: dict) -> float | None:
    """Precio para cualquier comprador: el menor no tachado que no exija la tarjeta de la tienda."""
    libres = [
        p["precio"]
        for p in h.get("precios_etiquetados", [])
        if not p["tachado"] and p["tipo"] != "cmrPrice"
    ]
    if libres:
        return min(libres)
    return min((o["precio"] for o in h.get("ofertas", [])), default=None)


def construir_catalogo(hechos: list[dict], semillas: dict[str, str]) -> list[ProductoCatalogo]:
    productos = []
    for pid, tiendas in sorted(_por_producto(hechos).items()):
        base = tiendas.get("A1") if tiendas.get("A1", {}).get("titulo") else tiendas.get("A2")
        if not base or not base.get("titulo"):
            continue
        titulo, categoria = base["titulo"], semillas[pid]
        gtin = gtin13(base["gtin_url"])
        if gtin is None:
            raise ValueError(f"{pid}: EAN inválido en la URL ({base['gtin_url']})")
        precio = min((o["precio"] for o in base.get("ofertas", [])), default=1.0)
        productos.append(
            ProductoCatalogo(
                id=pid,
                categoria=categoria,  # type: ignore[arg-type]
                gtin=gtin,
                marca=(base.get("marca") or "").title(),
                modelo=_modelo(titulo),
                mpn="",  # las tiendas no publican la referencia del fabricante
                titulo=titulo,
                precio_referencia_cop=int(precio),
                atributos=atributos_del_titulo(titulo, categoria),
                alias_comercial=titulo,
                alias_pdf=titulo.upper(),
                alias_mensaje=titulo.lower(),
            )
        )
    return productos


# --------------------------------------------------------------------------------------------------
# Hechos → verdad


def _oferta_verdad(tienda: str, pid: str | None, h: dict, url: str) -> dict | None:
    if not h.get("titulo") or not h.get("ofertas"):
        return None  # la ficha existe pero no tiene oferta: el producto no se puede comprar ahí
    o = h["ofertas"][0]
    precio = _precio_a3(h) if tienda == "A3" else o["precio"]
    return {
        "proveedor": tienda,
        "nombre_proveedor": NOMBRES[tienda],
        "tipo_fuente": "web_schema",
        "producto_id": pid,
        "oferta": {
            "titulo": h["titulo"],
            "precio": precio,
            "moneda": o["moneda"],
            "gtin": gtin13(h["gtin_url"]) if h.get("gtin_url") else None,
            "mpn": None,
            "marca": (h.get("marca") or "").title() or None,
            "modelo": None,
            "disponibilidad": o["disponibilidad"],
            "costo_envio": o["costo_envio"],
            "plazo_entrega_dias": o["entrega_dias_max"],
            "condiciones_entrega": None,
            "atributos": {},
        },
        "ubicacion": url,
        "url_original": h["url"],
    }


def _ruta_ficha(tienda: str, pid: str) -> str:
    return f"{tienda.lower()}/{pid.lower()}.html"


def construir_verdad(
    hechos: list[dict], equivalencias: dict, catalogo: list[ProductoCatalogo], base_url: str
) -> dict:
    en_catalogo = {p.id for p in catalogo}
    iguales = set(equivalencias.get("igual", []))
    ofertas = []
    for pid, tiendas in sorted(_por_producto(hechos).items()):
        if pid not in en_catalogo:
            continue
        for tienda, h in sorted(tiendas.items()):
            producto = pid if tienda != "A3" or pid in iguales else None
            o = _oferta_verdad(tienda, producto, h, f"{base_url}/{_ruta_ficha(tienda, pid)}")
            if o:
                ofertas.append(o)
    return {
        "fecha_hechos": FECHA_HECHOS,
        "proveedores": NOMBRES,
        "equivalencias": equivalencias,
        "ofertas": ofertas,
    }


# --------------------------------------------------------------------------------------------------
# Reconstrucción de las tiendas


def pesos(valor: float) -> str:
    return "$ " + f"{round(valor):,}".replace(",", ".")


_BASE = """<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>{{ titulo }} | {{ tienda }}</title></head><body>
<p><small>Reconstrucción para evaluación a partir de datos públicos del {{ fecha }}.
No es el sitio de {{ tienda }}.</small></p>
<nav><a href="index.html">Inicio</a></nav>
{% block cuerpo %}{% endblock %}
</body></html>"""

# Plantillas HTML: líneas largas a propósito (el HTML no se parte).
FICHA_MICRODATOS = """{% extends "base" %}{% block cuerpo %}
<div itemscope itemtype="https://schema.org/Product">
  <h1 itemprop="name">{{ h.titulo }}</h1>
  <p>Marca: <span itemprop="brand" itemscope itemtype="https://schema.org/Brand">
    <span itemprop="name">{{ h.marca }}</span></span> · Código: <span itemprop="sku">{{ h.sku }}</span></p>
  {% for o in h.ofertas[:1] %}
  <div itemprop="offers" itemscope itemtype="https://schema.org/Offer">
    <meta itemprop="priceCurrency" content="{{ o.moneda }}">
    <meta itemprop="price" content="{{ o.precio }}">
    <link itemprop="availability" href="https://schema.org/{{ disp[o.disponibilidad] }}">
    <p class="precio">{{ pesos(o.precio) }}</p>
    {% if o.disponibilidad == "agotado" %}<p><strong>Agotado</strong></p>
    {% else %}<p>Agregar al carrito</p>{% endif %}
    {% if o.costo_envio == 0 %}<p>Envío gratis{% if o.entrega_dias_max %} · Recíbelo en
      {{ o.entrega_dias_max }} día{{ "s" if o.entrega_dias_max > 1 }} hábil{{ "es" if o.entrega_dias_max > 1 }}{% endif %}</p>{% endif %}
  </div>
  {% endfor %}
</div>
{% endblock %}"""

FICHA_JSONLD = """{% extends "base" %}{% block cuerpo %}
<script type="application/ld+json">{{ jsonld | safe }}</script>
<h1>{{ h.titulo }}</h1>
<p>Marca: {{ h.marca }} · Código del vendedor: {{ h.sku }}</p>
<ol class="precios">
{% for p in h.precios_etiquetados %}
  {% if p.tipo == "cmrPrice" %}<li>{{ pesos(p.precio) }} con tarjeta CMR{% if p.vigencia %} (válido hasta {{ p.vigencia }}){% endif %}</li>
  {% elif p.tachado %}<li><del>Normal: {{ pesos(p.precio) }}</del></li>
  {% else %}<li>{{ pesos(p.precio) }}</li>{% endif %}
{% endfor %}
</ol>
{% if agotado %}<p><strong>Producto sin stock</strong></p>{% else %}<p>Agregar a la bolsa</p>{% endif %}
{% endblock %}"""

FICHA_SIN_OFERTA = """{% extends "base" %}{% block cuerpo %}
<h1>{{ h.titulo }}</h1><p>Este producto no está disponible en este momento.</p>
{% endblock %}"""

INDICE = """{% extends "base" %}{% block cuerpo %}
<h1>Tecnología</h1>
<ul>{% for f in fichas %}<li><a href="{{ f.ruta }}">{{ f.titulo }}</a>{% if f.precio %} · {{ pesos(f.precio) }}{% endif %}</li>
{% endfor %}</ul>
{% endblock %}"""

_DISP = {
    "en_stock": "InStock",
    "agotado": "OutOfStock",
    "bajo_pedido": "PreOrder",
    "desconocida": "InStock",
}


def _entorno() -> Environment:
    from jinja2 import DictLoader

    env = Environment(
        loader=DictLoader(
            {
                "base": _BASE,
                "microdatos": FICHA_MICRODATOS,
                "jsonld": FICHA_JSONLD,
                "sin_oferta": FICHA_SIN_OFERTA,
                "indice": INDICE,
            }
        ),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals.update(pesos=pesos, disp=_DISP, fecha=FECHA_HECHOS)
    return env


def _jsonld_a3(h: dict) -> str:
    """Como en la tienda: dos ofertas con precio y sin decir cuál exige la tarjeta."""
    disponibilidad = _DISP[h["ofertas"][0]["disponibilidad"]] if h.get("ofertas") else "OutOfStock"
    no_tachados = [p for p in h.get("precios_etiquetados", []) if not p["tachado"]]
    precios = [p["precio"] for p in no_tachados] or [o["precio"] for o in h.get("ofertas", [])]
    tachado = [p["precio"] for p in h.get("precios_etiquetados", []) if p["tachado"]]
    if len(precios) == 1 and tachado:  # la tienda repite el precio normal como segunda oferta
        precios.append(tachado[0])
    datos = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": h["titulo"],
        "sku": h.get("sku"),
        "gtin13": "null",
        "brand": {"@type": "Brand", "name": h.get("marca")},
        "offers": [
            {
                "@type": "Offer",
                "priceCurrency": "COP",
                "price": str(int(p)),
                "availability": f"https://schema.org/{disponibilidad}",
                "seller": {"@type": "Organization", "name": "Falabella"},
            }
            for p in precios
        ],
    }
    return json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")


def construir_sitio(hechos: list[dict], catalogo: list[ProductoCatalogo], directorio: Path) -> int:
    env = _entorno()
    en_catalogo = {p.id for p in catalogo}
    paginas = 0
    for tienda in TIENDAS:
        (directorio / tienda.lower()).mkdir(parents=True, exist_ok=True)
        fichas = []
        for h in sorted(hechos, key=lambda x: x["producto"]):
            if h["tienda"] != tienda or h["producto"] not in en_catalogo or not h.get("titulo"):
                continue
            ruta = _ruta_ficha(tienda, h["producto"])
            comun = {"titulo": h["titulo"], "tienda": NOMBRES[tienda], "h": h}
            if not h.get("ofertas"):
                html = env.get_template("sin_oferta").render(**comun)
                precio = None
            elif tienda == "A3":
                agotado = h["ofertas"][0]["disponibilidad"] == "agotado"
                html = env.get_template("jsonld").render(
                    **comun, jsonld=_jsonld_a3(h), agotado=agotado
                )
                precio = _precio_a3(h)
            else:
                html = env.get_template("microdatos").render(**comun)
                precio = h["ofertas"][0]["precio"]
            (directorio / ruta).write_text(html, encoding="utf-8")
            fichas.append({"ruta": Path(ruta).name, "titulo": h["titulo"], "precio": precio})
            paginas += 1
        indice = env.get_template("indice").render(
            titulo="Tecnología", tienda=NOMBRES[tienda], fichas=fichas
        )
        (directorio / tienda.lower() / "index.html").write_text(indice, encoding="utf-8")
    return paginas


def construir(base_url: str = "http://127.0.0.1:8802") -> dict[str, int]:
    hechos = [json.loads(linea) for linea in RUTA_HECHOS.read_text(encoding="utf-8").splitlines()]
    equivalencias = yaml.safe_load(RUTA_EQUIVALENCIAS.read_text(encoding="utf-8"))
    semillas = {
        s["id"]: s["categoria"]
        for s in yaml.safe_load((RAIZ / "semillas.yaml").read_text(encoding="utf-8"))["productos"]
    }
    catalogo = construir_catalogo(hechos, semillas)
    RUTA_CATALOGO_A.write_text(
        json.dumps(
            {"fecha_hechos": FECHA_HECHOS, "productos": [p.model_dump() for p in catalogo]},
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    verdad = construir_verdad(hechos, equivalencias, catalogo, base_url)
    RUTA_VERDAD_A.write_text(
        json.dumps(verdad, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    paginas = construir_sitio(hechos, catalogo, DIR_SITIO)
    return {"productos": len(catalogo), "ofertas": len(verdad["ofertas"]), "paginas": paginas}


if __name__ == "__main__":
    print(construir())
