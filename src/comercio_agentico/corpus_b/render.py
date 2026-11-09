"""Renderizadores de los cinco proveedores del corpus B, uno por nivel de madurez de la fuente.

Cada función recibe las ofertas de la verdad de un proveedor, las publica en su formato y devuelve
dónde quedó cada producto (``producto_id → ubicación``), para que la verdad apunte al fragmento.

- P1 MCP: inventario JSON con nomenclatura propia, servido por FastMCP (``servidor_mcp.py``).
- P2 web con schema.org: una página por producto con JSON-LD ``Product``/``Offer``.
- P3 web plana: páginas por categoría, nombres comerciales, sin GTIN ni marcado semántico.
- P4 PDF: lista de precios mayorista en tabla, abreviaturas, sin GTIN.
- P5 mensajes: exportación de chat tipo WhatsApp, texto informal y precios en el cuerpo.
"""

from __future__ import annotations

import json
import random
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fpdf import FPDF
from jinja2 import Environment

if TYPE_CHECKING:
    from comercio_agentico.corpus_b.catalogo import ProductoCatalogo
    from comercio_agentico.corpus_b.generar import Proveedor

ENTORNO = Environment(
    autoescape=True, trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True
)

NOMBRES_CATEGORIA = {
    "portatil": "Portátiles",
    "monitor": "Monitores",
    "celular": "Celulares",
    "audifonos": "Audífonos",
    "almacenamiento": "Almacenamiento",
}


def pesos(valor: float) -> str:
    """2499900 → '2.499.900' (separador de miles colombiano)."""
    return f"{int(valor):,}".replace(",", ".")


def capacidad(gb: float) -> str:
    return f"{int(gb // 1024)} TB" if gb >= 1024 and gb % 1024 == 0 else f"{int(gb)} GB"


def describir(nombre: str, valor: Any) -> str:
    """Atributo en lenguaje de vitrina (P2 y P3)."""
    n = f"{valor:g}".replace(".", ",") if isinstance(valor, float) else str(valor)
    si_no = "Sí" if valor is True else "No"
    plantillas = {
        "procesador": lambda: f"Procesador {valor}",
        "memoria_ram": lambda: f"{n} GB de memoria RAM",
        "almacenamiento": lambda: f"Capacidad de {capacidad(valor)}",
        "tamano_pantalla": lambda: f"Pantalla de {n} pulgadas",
        "peso": lambda: f"Peso: {n} kg",
        "resolucion": lambda: f"Resolución {valor}",
        "tipo_panel": lambda: f"Panel {valor}",
        "frecuencia_refresco": lambda: f"Frecuencia de {n} Hz",
        "bateria": lambda: f"Batería de {n} mAh",
        "cancelacion_ruido": lambda: f"Cancelación de ruido: {si_no}",
        "inalambrico": lambda: f"Inalámbrico: {si_no}",
        "autonomia": lambda: f"Hasta {n} horas de autonomía",
        "tipo_almacenamiento": lambda: f"Tipo: {valor}",
        "velocidad_lectura": lambda: f"Lectura de hasta {n} MB/s",
    }
    return plantillas.get(nombre, lambda: f"{nombre}: {valor}")()


def _por_categoria(ofertas: list[dict], productos: dict[str, ProductoCatalogo]) -> dict:
    grupos: dict[str, list[dict]] = {}
    for o in ofertas:
        grupos.setdefault(productos[o["producto_id"]].categoria, []).append(o)
    return {c: grupos[c] for c in NOMBRES_CATEGORIA if c in grupos}


# --------------------------------------------------------------------------------------------------
# P1 — MCP


def render_p1_mcp(destino: Path, proveedor: Proveedor, ofertas, productos, azar: random.Random):
    """Inventario con nombres de campo propios del mayorista; lo sirve ``servidor_mcp.py``."""
    articulos, ubicaciones = [], {}
    for n, o in enumerate(ofertas, start=1):
        of, producto = o["oferta"], productos[o["producto_id"]]
        referencia = f"MD-{n:04d}"
        existencias = azar.randint(2, 40) if of["disponibilidad"] == "en_stock" else 0
        articulos.append(
            {
                "referencia": referencia,
                "descripcion": of["titulo"],
                "ean": of["gtin"],
                "pn": of["mpn"],
                "fabricante": of["marca"],
                "modelo": of["modelo"],
                "familia": producto.categoria,
                "valor_unitario_cop": int(of["precio"]),
                "existencias": existencias,
                "a_pedido": of["disponibilidad"] == "bajo_pedido",
                "flete_cop": int(of["costo_envio"]),
                "dias_despacho": of["plazo_entrega_dias"],
                "especificaciones": of["atributos"],
            }
        )
        ubicaciones[o["producto_id"]] = f"mcp://p1/detalle_producto/{referencia}"
    datos = {
        "proveedor": proveedor.nombre,
        "condiciones": "Precios con IVA. Flete gratis desde $1.000.000. Despacho en 2 días "
        "hábiles; artículos a pedido, 9 días.",
        "articulos": articulos,
    }
    (destino / "inventario.json").write_text(
        json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return ubicaciones


# --------------------------------------------------------------------------------------------------
# P2 — web con schema.org

DISPONIBILIDAD_SCHEMA = {
    "en_stock": "https://schema.org/InStock",
    "agotado": "https://schema.org/OutOfStock",
    "bajo_pedido": "https://schema.org/BackOrder",
}
TEXTO_DISPONIBILIDAD = {
    "en_stock": "Disponible",
    "agotado": "Agotado",
    "bajo_pedido": "Bajo pedido",
}

P2_PRODUCTO = ENTORNO.from_string("""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{{ of.titulo }} | {{ tienda }}</title>
<script type="application/ld+json">{{ jsonld | safe }}</script>
</head>
<body>
<header><a href="index.html">{{ tienda }}</a> · Tecnología con envío a toda Colombia</header>
<main>
<h1>{{ of.titulo }}</h1>
<p class="marca">Marca: {{ of.marca }} · Ref. {{ of.mpn }}</p>
<p class="precio">$ {{ precio }}</p>
<p class="stock">{{ disponibilidad }}</p>
<p class="envio">Envío: {{ envio }} · Entrega en {{ of.plazo_entrega_dias }} días hábiles</p>
<h2>Especificaciones</h2>
<ul>
{% for clave, valor in of.atributos.items() %}
<li>{{ describir(clave, valor) }}</li>
{% endfor %}
</ul>
<p class="ean">Código EAN: {{ of.gtin }}</p>
</main>
</body>
</html>
""")

P2_INDICE = ENTORNO.from_string("""<!doctype html>
<html lang="es">
<head><meta charset="utf-8"><title>{{ tienda }} — Catálogo</title></head>
<body>
<h1>{{ tienda }}</h1>
{% for categoria, items in grupos.items() %}
<h2>{{ nombres[categoria] }}</h2>
<ul>
{% for item in items %}
<li><a href="{{ item.archivo }}">{{ item.titulo }}</a> — $ {{ item.precio }}</li>
{% endfor %}
</ul>
{% endfor %}
</body>
</html>
""")


def _jsonld(of: dict) -> str:
    datos = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": of["titulo"],
        "gtin13": of["gtin"],
        "mpn": of["mpn"],
        "brand": {"@type": "Brand", "name": of["marca"]},
        "model": of["modelo"],
        "additionalProperty": [
            {"@type": "PropertyValue", "name": k, "value": v} for k, v in of["atributos"].items()
        ],
        "offers": {
            "@type": "Offer",
            "price": int(of["precio"]),
            "priceCurrency": of["moneda"],
            "availability": DISPONIBILIDAD_SCHEMA[of["disponibilidad"]],
            "shippingDetails": {
                "@type": "OfferShippingDetails",
                "shippingRate": {
                    "@type": "MonetaryAmount",
                    "value": int(of["costo_envio"]),
                    "currency": of["moneda"],
                },
                "deliveryTime": {
                    "@type": "ShippingDeliveryTime",
                    "transitTime": {
                        "@type": "QuantitativeValue",
                        "maxValue": of["plazo_entrega_dias"],
                        "unitCode": "DAY",
                    },
                },
            },
        },
    }
    # "</" dentro de un <script> cerraría la etiqueta antes de tiempo.
    return json.dumps(datos, ensure_ascii=False, indent=2).replace("</", "<\\/")


def render_p2_schema(destino: Path, proveedor: Proveedor, ofertas, productos, azar):
    ubicaciones = {}
    for o in ofertas:
        of = o["oferta"]
        archivo = f"{o['producto_id'].lower()}.html"
        envio = "Gratis" if of["costo_envio"] == 0 else f"$ {pesos(of['costo_envio'])}"
        html = P2_PRODUCTO.render(
            of=of,
            tienda=proveedor.nombre,
            jsonld=_jsonld(of),
            precio=pesos(of["precio"]),
            disponibilidad=TEXTO_DISPONIBILIDAD[of["disponibilidad"]],
            envio=envio,
            describir=describir,
        )
        (destino / archivo).write_text(html, encoding="utf-8")
        ubicaciones[o["producto_id"]] = f"{destino.name}/{archivo}"
    grupos = {
        c: [
            {
                "archivo": f"{o['producto_id'].lower()}.html",
                "titulo": o["oferta"]["titulo"],
                "precio": pesos(o["oferta"]["precio"]),
            }
            for o in items
        ]
        for c, items in _por_categoria(ofertas, productos).items()
    }
    (destino / "index.html").write_text(
        P2_INDICE.render(tienda=proveedor.nombre, grupos=grupos, nombres=NOMBRES_CATEGORIA),
        encoding="utf-8",
    )
    return ubicaciones


# --------------------------------------------------------------------------------------------------
# P3 — web plana

P3_CATEGORIA = ENTORNO.from_string("""<!doctype html>
<html lang="es">
<head><meta charset="utf-8"><title>{{ titulo }} - {{ tienda }}</title></head>
<body>
<div class="top">{{ tienda }} | <a href="index.html">Inicio</a> |
¡Los mejores precios del barrio!</div>
<div class="titulo">{{ titulo }}</div>
{% for item in items %}
<div class="card" id="{{ item.ancla }}">
  <div class="nombre">{{ item.nombre }}</div>
  <div class="marca">{{ item.marca }}</div>
  <div class="valor">$ {{ item.precio }}</div>
  <div class="detalle">{{ item.detalle }}</div>
  <div class="estado">{{ item.estado }}</div>
  <div class="envio">{{ item.envio }}</div>
</div>
{% endfor %}
<div class="pie">Precios con IVA incluido. Envío a todo el país por $15.000.</div>
</body>
</html>
""")

P3_INDICE = ENTORNO.from_string("""<!doctype html>
<html lang="es">
<head><meta charset="utf-8"><title>{{ tienda }}</title></head>
<body>
<div class="top">{{ tienda }}</div>
{% for archivo, nombre in secciones %}
<div><a href="{{ archivo }}">{{ nombre }}</a></div>
{% endfor %}
</body>
</html>
""")

ESTADO_P3 = {
    "en_stock": "Disponible para entrega inmediata",
    "agotado": "AGOTADO",
    "bajo_pedido": "Disponible bajo pedido",
}


def render_p3_plana(destino: Path, proveedor: Proveedor, ofertas, productos, azar):
    ubicaciones, secciones = {}, []
    for categoria, items in _por_categoria(ofertas, productos).items():
        archivo = f"{categoria}.html"
        tarjetas = []
        for o in items:
            of = o["oferta"]
            ancla = f"item-{o['producto_id'].lower()}"
            tarjetas.append(
                {
                    "ancla": ancla,
                    "nombre": of["titulo"],
                    "marca": of["marca"],
                    "precio": pesos(of["precio"]),
                    "detalle": " · ".join(describir(k, v) for k, v in of["atributos"].items()),
                    "estado": ESTADO_P3[of["disponibilidad"]],
                    "envio": f"Envío ${pesos(of['costo_envio'])} · Llega en "
                    f"{of['plazo_entrega_dias']} días hábiles",
                }
            )
            ubicaciones[o["producto_id"]] = f"{destino.name}/{archivo}#{ancla}"
        html = P3_CATEGORIA.render(
            titulo=NOMBRES_CATEGORIA[categoria], tienda=proveedor.nombre, items=tarjetas
        )
        (destino / archivo).write_text(html, encoding="utf-8")
        secciones.append((archivo, NOMBRES_CATEGORIA[categoria]))
    (destino / "index.html").write_text(
        P3_INDICE.render(tienda=proveedor.nombre, secciones=secciones), encoding="utf-8"
    )
    return ubicaciones


# --------------------------------------------------------------------------------------------------
# P4 — lista de precios en PDF

FECHA_LISTA = datetime(2026, 11, 10, tzinfo=UTC)
DISP_P4 = {"en_stock": "SI", "agotado": "AGOT", "bajo_pedido": "PED"}


def render_p4_pdf(destino: Path, proveedor: Proveedor, ofertas, productos, azar):
    pdf = FPDF()
    pdf.set_title(f"Lista de precios {proveedor.nombre}")
    pdf.set_creation_date(FECHA_LISTA)  # fecha fija: el PDF es reproducible byte a byte
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(
        0,
        8,
        f"{proveedor.nombre.upper()} - LISTA DE PRECIOS NOVIEMBRE 2026",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.set_font("Helvetica", size=9)
    pdf.multi_cell(
        0,
        5,
        "Precios en pesos colombianos, IVA incluido. Flete nacional $25.000 por despacho. "
        "Entrega en 5 días hábiles; referencias PED (a pedido) en 12 días hábiles. "
        "DISP: SI = disponible, AGOT = agotado, PED = a pedido.",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(3)
    ubicaciones = {}
    with pdf.table(
        col_widths=(18, 112, 32, 18), text_align=("LEFT", "LEFT", "RIGHT", "CENTER"), line_height=6
    ) as tabla:
        encabezado = tabla.row()
        for texto in ("CÓD", "DESCRIPCIÓN", "PRECIO", "DISP"):
            encabezado.cell(texto)
        for n, o in enumerate(sorted(ofertas, key=lambda x: x["oferta"]["titulo"]), start=1):
            of = o["oferta"]
            codigo = f"DA{n:03d}"
            fila = tabla.row()
            for texto in (codigo, of["titulo"], pesos(of["precio"]), DISP_P4[of["disponibilidad"]]):
                fila.cell(texto)
            ubicaciones[o["producto_id"]] = f"{destino.name}/lista_precios.pdf#{codigo}"
    pdf.output(str(destino / "lista_precios.pdf"))
    return ubicaciones


# --------------------------------------------------------------------------------------------------
# P5 — mensajes tipo WhatsApp


def precio_informal(valor: int, azar: random.Random) -> str:
    """Formatos reales de precio en chats, todos exactos (2350000 → "2'350.000", "2350 mil"...)."""
    millones, resto = divmod(valor, 1_000_000)
    formatos = [f"${pesos(valor)}", f"{pesos(valor)} pesos"]
    if millones:
        formatos.append(f"{millones}'{pesos(resto).zfill(7) if resto else '000.000'}")
    if valor % 1000 == 0:
        formatos.append(f"{valor // 1000} mil")
    return azar.choice(formatos)


def _linea_p5(of: dict, azar: random.Random) -> str:
    nombre, precio = of["titulo"], precio_informal(int(of["precio"]), azar)
    if of["disponibilidad"] == "agotado":
        return azar.choice(
            [
                f"{nombre} estaba en {precio} pero se me acabó 😕",
                f"{nombre} a {precio}, ese no me queda, agotado",
            ]
        )
    if of["disponibilidad"] == "bajo_pedido":
        return azar.choice(
            [
                f"{nombre} por encargo en {precio}, llega en {of['plazo_entrega_dias']} días",
                f"{nombre} {precio} sobre pedido ({of['plazo_entrega_dias']} días)",
            ]
        )
    return azar.choice(
        [
            f"✅ {nombre} a {precio}",
            f"{nombre} 👉 {precio}",
            f"tengo {nombre} en {precio}, quedan {azar.randint(1, 5)}",
            f"{nombre} {precio} nuevo sellado",
        ]
    )


def render_p5_mensajes(destino: Path, proveedor: Proveedor, ofertas, productos, azar):
    vendedor, cliente = proveedor.nombre, "Cliente"
    hora = [9, 2]

    def msg(quien: str, texto: str) -> str:
        hora[1] += azar.randint(1, 6)
        hora[0], hora[1] = hora[0] + hora[1] // 60, hora[1] % 60
        sufijo = "a. m." if hora[0] < 12 else "p. m."
        h12 = hora[0] if hora[0] <= 12 else hora[0] - 12
        return f"10/11/26, {h12}:{hora[1]:02d} {sufijo} - {quien}: {texto}"

    lineas = [
        msg(cliente, "Buenos días don Carlos, ¿qué tiene en tecnología esta semana?"),
        msg(vendedor, "Buenos días veci!! le paso la lista actualizada 👇"),
    ]
    ubicaciones = {}
    for categoria, items in _por_categoria(ofertas, productos).items():
        lineas.append(msg(vendedor, f"*{NOMBRES_CATEGORIA[categoria].upper()}*"))
        for o in items:
            lineas.append(msg(vendedor, _linea_p5(o["oferta"], azar)))
            ubicaciones[o["producto_id"]] = f"{destino.name}/chat.txt#L{len(lineas)}"
        if azar.random() < 0.5:
            lineas.append(msg(cliente, azar.choice(["ok", "👍", "y garantía?", "uy bacano"])))
            lineas.append(
                msg(
                    vendedor,
                    azar.choice(
                        ["todo con garantía de fábrica", "a la orden 🙌", "pregunte sin pena"]
                    ),
                )
            )
    lineas.append(msg(cliente, "¿y el domicilio cuánto vale?"))
    lineas.append(
        msg(
            vendedor,
            f"domicilio {proveedor.envio // 1000} mil a cualquier parte de la "
            f"ciudad, le llega mañana mismo. Lo de encargo sí se demora",
        )
    )
    (destino / "chat.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return ubicaciones
