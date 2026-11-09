"""Generador determinista del corpus B: reparte el catálogo entre cinco proveedores y publica cada
uno en su formato a partir de la verdad de referencia.

Orden: catálogo → ``verdad.json`` (la oferta exacta de cada proveedor) → páginas, PDF, mensajes e
inventario MCP renderizados desde la verdad. Así lo que debería extraerse se conoce por
construcción.

Uso: ``uv run python -m comercio_agentico.corpus_b.generar`` (US$0, sin red).
"""

from __future__ import annotations

import json
import random
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from comercio_agentico.corpus_b import DIR_CORPUS, RUTA_VERDAD
from comercio_agentico.corpus_b.catalogo import ProductoCatalogo, cargar_catalogo
from comercio_agentico.corpus_b.render import (
    render_p1_mcp,
    render_p2_schema,
    render_p3_plana,
    render_p4_pdf,
    render_p5_mensajes,
)
from comercio_agentico.esquema import OfertaExtraida, TipoFuente

SEMILLA = 20261110
PRODUCTOS_SIN_OFERTA = 4  # en el catálogo, pero ningún proveedor los vende (tareas de abstención)
PRODUCTOS_SOLO_AGOTADOS = 2  # todos sus proveedores los tienen agotados
DIAS_EXTRA_BAJO_PEDIDO = 7


@dataclass(frozen=True)
class Proveedor:
    id: str
    nombre: str
    tipo_fuente: TipoFuente
    cobertura: float  # probabilidad de vender cada producto
    factor_precio: float  # sobre el precio de referencia
    redondeo: int  # múltiplo al que redondea sus precios
    termina_en_900: bool
    envio: int
    envio_gratis_desde: int | None
    plazo_dias: int
    publica_identificadores: bool  # GTIN, MPN, marca y modelo
    publica_atributos: bool


PROVEEDORES: list[Proveedor] = [
    Proveedor(
        "P1", "Mayorista Digital", "mcp", 0.65, 0.95, 1000, True, 14_900, 1_000_000, 2, True, True
    ),
    Proveedor(
        "P2", "TiendaNova", "web_schema", 0.60, 1.00, 1000, True, 12_900, 2_000_000, 3, True, True
    ),
    Proveedor(
        "P3", "ElectroBarrio", "web_plana", 0.50, 0.98, 1000, True, 15_000, None, 4, False, True
    ),
    Proveedor(
        "P4",
        "Distribuciones Andinas",
        "pdf",
        0.55,
        0.93,
        1000,
        False,
        25_000,
        None,
        5,
        False,
        False,
    ),
    Proveedor(
        "P5", "Carlos Tecnología", "mensaje", 0.35, 0.91, 5000, False, 10_000, None, 1, False, False
    ),
]
POR_ID = {p.id: p for p in PROVEEDORES}


def _precio(base: int, proveedor: Proveedor, azar: random.Random) -> int:
    bruto = base * proveedor.factor_precio * azar.uniform(0.95, 1.07)
    precio = max(proveedor.redondeo, round(bruto / proveedor.redondeo) * proveedor.redondeo)
    return precio - 100 if proveedor.termina_en_900 else precio


def _titulo(producto: ProductoCatalogo, proveedor: Proveedor) -> str:
    return {
        "mcp": producto.titulo,
        "web_schema": producto.titulo,
        "web_plana": producto.alias_comercial,
        "pdf": producto.alias_pdf,
        "mensaje": producto.alias_mensaje,
    }[proveedor.tipo_fuente]


def _oferta(
    producto: ProductoCatalogo, proveedor: Proveedor, disponibilidad: str, azar: random.Random
) -> OfertaExtraida:
    precio = _precio(producto.precio_referencia_cop, proveedor, azar)
    gratis = proveedor.envio_gratis_desde is not None and precio >= proveedor.envio_gratis_desde
    plazo = proveedor.plazo_dias + (
        DIAS_EXTRA_BAJO_PEDIDO if disponibilidad == "bajo_pedido" else 0
    )
    ids = proveedor.publica_identificadores
    return OfertaExtraida(
        titulo=_titulo(producto, proveedor),
        precio=precio,
        moneda="COP",
        gtin=producto.gtin if ids else None,
        mpn=producto.mpn if ids else None,
        marca=producto.marca if ids or proveedor.tipo_fuente == "web_plana" else None,
        modelo=producto.modelo if ids else None,
        disponibilidad=disponibilidad,  # type: ignore[arg-type]
        costo_envio=0 if gratis else proveedor.envio,
        plazo_entrega_dias=plazo,
        atributos=dict(producto.atributos) if proveedor.publica_atributos else {},
    )


def repartir(catalogo: list[ProductoCatalogo], azar: random.Random) -> list[dict[str, Any]]:
    """Decide quién vende qué, a qué precio y con qué existencias. Devuelve la verdad."""
    ids = [p.id for p in catalogo]
    sin_oferta = set(azar.sample(ids, PRODUCTOS_SIN_OFERTA))
    con_oferta = [i for i in ids if i not in sin_oferta]
    solo_agotados = set(azar.sample(con_oferta, PRODUCTOS_SOLO_AGOTADOS))

    verdad: list[dict[str, Any]] = []
    for producto in catalogo:
        if producto.id in sin_oferta:
            continue
        vendedores = [p for p in PROVEEDORES if azar.random() < p.cobertura]
        if not vendedores:  # todo producto ofrecido tiene al menos un proveedor
            vendedores = [azar.choice(PROVEEDORES)]
        for proveedor in vendedores:
            if producto.id in solo_agotados:
                disponibilidad = "agotado"
            else:
                disponibilidad = azar.choices(
                    ["en_stock", "agotado", "bajo_pedido"], weights=[80, 10, 10]
                )[0]
            oferta = _oferta(producto, proveedor, disponibilidad, azar)
            verdad.append(
                {
                    "proveedor": proveedor.id,
                    "nombre_proveedor": proveedor.nombre,
                    "tipo_fuente": proveedor.tipo_fuente,
                    "producto_id": producto.id,
                    "oferta": oferta.model_dump(),
                }
            )
    return verdad


def cargar_verdad(ruta: Path = RUTA_VERDAD) -> dict[str, Any]:
    return json.loads(ruta.read_text(encoding="utf-8"))


def generar(directorio: Path = DIR_CORPUS) -> dict[str, Any]:
    catalogo = cargar_catalogo(directorio / "catalogo.json")
    azar = random.Random(SEMILLA)
    ofertas = repartir(catalogo, azar)
    vendidos = {o["producto_id"] for o in ofertas}
    agotados = {
        p.id
        for p in catalogo
        if p.id in vendidos
        and all(
            o["oferta"]["disponibilidad"] == "agotado" for o in ofertas if o["producto_id"] == p.id
        )
    }
    verdad = {
        "semilla": SEMILLA,
        "proveedores": [
            {"id": p.id, "nombre": p.nombre, "tipo_fuente": p.tipo_fuente} for p in PROVEEDORES
        ],
        "productos_sin_oferta": sorted(p.id for p in catalogo if p.id not in vendidos),
        "productos_solo_agotados": sorted(agotados),
        "ofertas": ofertas,
    }

    salidas = {
        "P1": render_p1_mcp,
        "P2": render_p2_schema,
        "P3": render_p3_plana,
        "P4": render_p4_pdf,
        "P5": render_p5_mensajes,
    }
    productos = {p.id: p for p in catalogo}
    for proveedor in PROVEEDORES:
        destino = directorio / f"{proveedor.id.lower()}_{proveedor.tipo_fuente}"
        if destino.exists():
            shutil.rmtree(destino)
        destino.mkdir(parents=True)
        propias = [o for o in ofertas if o["proveedor"] == proveedor.id]
        ubicaciones = salidas[proveedor.id](destino, proveedor, propias, productos, azar)
        for o in propias:
            o["ubicacion"] = ubicaciones[o["producto_id"]]

    (directorio / "verdad.json").write_text(
        json.dumps(verdad, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return verdad


def resumen(verdad: dict[str, Any]) -> str:
    lineas = []
    for p in verdad["proveedores"]:
        propias = [o for o in verdad["ofertas"] if o["proveedor"] == p["id"]]
        lineas.append(
            f"  {p['id']} {p['nombre']:<24} {p['tipo_fuente']:<11} {len(propias)} ofertas"
        )
    por_producto: dict[str, int] = {}
    for o in verdad["ofertas"]:
        por_producto[o["producto_id"]] = por_producto.get(o["producto_id"], 0) + 1
    multiples = sum(1 for n in por_producto.values() if n >= 3)
    lineas.append(
        f"  {len(verdad['ofertas'])} ofertas · {len(por_producto)} productos ofrecidos "
        f"({multiples} en 3+ proveedores) · sin oferta {verdad['productos_sin_oferta']} · "
        f"solo agotados {verdad['productos_solo_agotados']}"
    )
    return "\n".join(lineas)


if __name__ == "__main__":
    print(resumen(generar()))
