"""Prueba de humo: una llamada con tool-calling a cada modelo.

Imprime latencia, tokens, costo y proveedor.

uv run python -m comercio_agentico.ping            # los seis modelos
uv run python -m comercio_agentico.ping haiku kimi  # solo algunos
"""

from __future__ import annotations

import sys
import time

from langchain_core.tools import tool

from comercio_agentico.modelos import MODELOS, RegistroCosto, obtener_modelo


@tool
def consultar_precio(gtin: str) -> str:
    """Consulta el precio vigente de un producto por su código GTIN/EAN."""
    return "1.299.900 COP"


PREGUNTA = "¿Cuánto cuesta el producto con GTIN 7702004003508? Usa la herramienta disponible."


def ping(nombre: str) -> tuple[bool, str]:
    registro = RegistroCosto(tope_usd=0.05)
    modelo = obtener_modelo(nombre).bind_tools([consultar_precio])
    inicio = time.perf_counter()
    respuesta = modelo.invoke(PREGUNTA, config={"callbacks": [registro]})
    latencia = time.perf_counter() - inicio
    llamadas = respuesta.tool_calls
    ok = bool(llamadas) and llamadas[0]["name"] == "consultar_precio"
    gtin = llamadas[0]["args"].get("gtin") if llamadas else None
    llamada = registro.llamadas[-1] if registro.llamadas else None
    detalle = (
        f"{latencia:5.1f} s | {llamada.tokens_entrada:>4} → {llamada.tokens_salida:>4} tok | "
        f"US${llamada.costo_usd:.6f} ({llamada.costo_fuente}) | proveedor={llamada.proveedor} | "
        f"gtin={gtin}"
        if llamada
        else f"{latencia:5.1f} s | sin registro de uso"
    )
    return ok, detalle


def main(argv: list[str]) -> int:
    nombres = argv or list(MODELOS)
    fallos = 0
    for nombre in nombres:
        try:
            ok, detalle = ping(nombre)
        except Exception as error:  # se reporta y se sigue con el siguiente modelo
            ok, detalle = False, f"ERROR {type(error).__name__}: {error}"
        fallos += not ok
        print(f"{'OK  ' if ok else 'FALLA'} {nombre:<15} {detalle}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
