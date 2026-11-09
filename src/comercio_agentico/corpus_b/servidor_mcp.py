"""P1 — proveedor mayorista expuesto por MCP (D13).

Dos herramientas, como las de un catálogo B2B real: ``buscar_productos`` (resumen) y
``detalle_producto`` (ficha completa). Los nombres de campo son los del mayorista, no los del
esquema canónico: traducirlos es trabajo del agente.

Uso: ``uv run python -m comercio_agentico.corpus_b.servidor_mcp [--puerto 8801]``
(HTTP en ``/mcp``).
"""

from __future__ import annotations

import argparse
import json
import unicodedata
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from comercio_agentico.corpus_b import DIR_CORPUS

RUTA_INVENTARIO = DIR_CORPUS / "p1_mcp" / "inventario.json"
CAMPOS_RESUMEN = ("referencia", "descripcion", "familia", "valor_unitario_cop", "existencias")


def _sin_tildes(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn"
    )


def crear_servidor(ruta: Path = RUTA_INVENTARIO) -> FastMCP:
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    articulos: list[dict[str, Any]] = datos["articulos"]
    por_referencia = {a["referencia"]: a for a in articulos}
    servidor = FastMCP(
        "Mayorista Digital",
        instructions=f"Catálogo mayorista de electrónica. {datos['condiciones']}",
    )

    @servidor.tool
    def buscar_productos(
        texto: str, familia: str | None = None, limite: int = 10
    ) -> list[dict[str, Any]]:
        """Busca artículos cuya descripción contenga todas las palabras de `texto`.

        `familia` filtra por portatil, monitor, celular, audifonos o almacenamiento.
        Devuelve un resumen; use detalle_producto para la ficha completa.
        """
        palabras = _sin_tildes(texto).split()
        hallados = [
            {k: a[k] for k in CAMPOS_RESUMEN}
            for a in articulos
            if (familia is None or a["familia"] == familia)
            and all(p in _sin_tildes(f"{a['descripcion']} {a['fabricante']}") for p in palabras)
        ]
        return hallados[: max(1, limite)]

    @servidor.tool
    def detalle_producto(referencia: str) -> dict[str, Any]:
        """Ficha completa de un artículo: EAN, número de parte, precio, existencias, flete,
        días de despacho y especificaciones."""
        if referencia not in por_referencia:
            return {"error": f"Referencia no encontrada: {referencia}"}
        return por_referencia[referencia]

    return servidor


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--puerto", type=int, default=8801)
    crear_servidor().run(transport="http", host="127.0.0.1", port=parser.parse_args().puerto)
