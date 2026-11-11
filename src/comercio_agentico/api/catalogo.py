"""Lista curada de modelos de CotIA (D82, D107).

Un modelo entra a la lista si **funciona** en una prueba de humo del agente completo (una tarea
benigna del corpus B en C2, D106: sin errores, con ofertas, interpretación completa y en menos de
10 minutos) y tiene **desempeño con evidencia**: acertó la tarea del humo o tiene M2 medido en E3.
La evidencia queda en ``resultados/cotia/modelos.json`` y la API la lee tal cual.

    make corpus-b-servir                                       # en otra terminal
    uv run python -m comercio_agentico.api.catalogo --humo     # tope US$0,45 con la clave del .env
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from comercio_agentico.corpus_b import RAIZ
from comercio_agentico.modelos import ficha

RUTA_LISTA = RAIZ / "resultados" / "cotia" / "modelos.json"
TAREA_HUMO = "B013"
TOPE_HUMO_USD = 0.45
LIMITE_S = 600  # más de 10 minutos no es usable en la demostración
RUTA_E3 = RAIZ / "resultados" / "informes" / "e3" / "e3.json"
NOMBRE_E3 = {"haiku-or": "haiku"}  # mismo modelo; en E3 se llamó por Anthropic directo
TRANSITORIOS = ("TooManyRequests",)  # errores del proveedor que se reintentan al reanudar
# Gratuitos primero y el resto por costo esperado, para que el tope recaiga en el más caro.
CANDIDATOS = [
    "nemotron-free",
    "dots-free",
    "xing-free",
    "lfm3-free",
    "lfm25-free",
    "deepseek-flash",
    "haiku-or",
    "deepseek-pro",
    "kimi",
]
ETIQUETAS = {
    "deepseek-flash": "DeepSeek V4.1 Flash",
    "haiku-or": "Claude Haiku 5.5",
    "deepseek-pro": "DeepSeek V4 Pro",
    "kimi": "Kimi K3.1 Pro",
    "nemotron-free": "NVIDIA Nemotron 3.5 Super VL (gratis)",
    "dots-free": "Dots3-Note Preview (gratis)",
    "xing-free": "XingChen Xing4.0 29B (gratis)",
    "lfm3-free": "LiquidAI LFM3 1.7B (gratis)",
    "lfm25-free": "LiquidAI LFM2.5 2.6B (gratis)",
}


def cargar_lista(ruta: Path = RUTA_LISTA) -> list[dict[str, Any]]:
    """Modelos aprobados, en el orden de la prueba de humo."""
    if not ruta.exists():
        return []
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    return [m for m in datos["modelos"] if m["aprobado"]]


def evidencia_e3(ruta: Path = RUTA_E3) -> dict[str, dict[str, float]]:
    if not ruta.exists():
        return {}
    pasos = json.loads(ruta.read_text(encoding="utf-8"))["pasos"]
    return {p["modelo"]: {k: p[k] for k in ("m2_media", "m2_bajo", "m2_alto")} for p in pasos}


def clasificar(fila: dict[str, Any], e3: dict[str, dict[str, float]]) -> dict[str, Any]:
    """Aprobado = funciona en el humo y (acertó o tiene M2 de E3)."""
    funciona = "acierto" in fila and fila["motivo"] in (None, "respuesta incorrecta")
    m2 = e3.get(NOMBRE_E3.get(fila["nombre"], fila["nombre"]))
    return fila | {
        "funciona": funciona,
        "m2_e3": m2,
        "aprobado": funciona and (bool(fila.get("acierto")) or m2 is not None),
    }


async def humo(tope_total: float = TOPE_HUMO_USD, ruta: Path = RUTA_LISTA) -> dict[str, Any]:
    from comercio_agentico.agente.defensa import ClasificadorInyeccion, Defensas
    from comercio_agentico.agente.grafo import preguntar
    from comercio_agentico.corpus_b.catalogo import cargar_catalogo
    from comercio_agentico.corpus_b.tareas import cargar_tareas
    from comercio_agentico.emparejamiento import Emparejador
    from comercio_agentico.preguntar import evaluar

    tarea = next(t for t in cargar_tareas() if t.id == TAREA_HUMO)
    emparejador = Emparejador(cargar_catalogo())
    clasificador = ClasificadorInyeccion()
    previas = {
        m["nombre"]: m
        for m in (json.loads(ruta.read_text())["modelos"] if ruta.exists() else [])
        if not (m.get("motivo") or "").startswith(TRANSITORIOS)
    }
    gasto = json.loads(ruta.read_text())["gasto_usd"] if ruta.exists() else 0.0
    e3 = evidencia_e3()
    filas = []
    for nombre in CANDIDATOS:
        if nombre in previas:  # reanuda sin repetir gasto
            filas.append(clasificar(previas[nombre], e3))
            continue
        cfg = ficha(nombre)
        restante = round(tope_total - gasto, 4)
        fila: dict[str, Any] = {
            "nombre": nombre,
            "etiqueta": ETIQUETAS[nombre],
            "id_modelo": cfg.id_modelo,
            "gratuito": cfg.id_modelo.endswith(":free"),
            "tarea": TAREA_HUMO,
        }
        if restante <= 0.005 and not fila["gratuito"]:
            filas.append(fila | {"aprobado": False, "motivo": "no evaluado: tope de la prueba"})
            continue
        try:
            r = await asyncio.wait_for(
                preguntar(
                    tarea.consulta,
                    modelo=nombre,
                    defensas=Defensas.de("C2"),
                    clasificador=clasificador,
                    emparejador=emparejador,
                    tope_usd=None if fila["gratuito"] else restante,
                ),
                LIMITE_S,
            )
            ev = evaluar(tarea, r)
            if (r.propuesta.motivo_abstencion or "").startswith("Tarea detenida"):
                motivo = "detenida por el tope"
            elif r.necesidad is None or r.necesidad.degradada:
                motivo = "interpretación degradada"
            elif not r.ofertas:
                motivo = "sin ofertas"
            else:
                motivo = None if ev["acierto"] else "respuesta incorrecta"
            fila |= {
                "aprobado": motivo is None,
                "motivo": motivo,
                "acierto": ev["acierto"],
                "costo_usd": round(r.propuesta.costo_usd, 6),
                "segundos": round(r.segundos, 1),
                "llamadas_llm": len(r.llamadas_llm),
            }
        except TimeoutError:
            fila |= {"aprobado": False, "motivo": f"no terminó en {LIMITE_S // 60} minutos"}
        except Exception as error:
            fila |= {"aprobado": False, "motivo": f"{type(error).__name__}: {error}"[:300]}
        gasto += fila.get("costo_usd") or 0.0
        fila = clasificar(fila, e3)
        logging.getLogger("comercio_agentico").warning(
            "%s: %s · US$%.4f",
            nombre,
            "aprobado" if fila["aprobado"] else fila.get("motivo"),
            fila.get("costo_usd") or 0,
        )
        filas.append(fila)
        _guardar(ruta, filas, gasto, tope_total)
    return _guardar(ruta, filas, gasto, tope_total)


def _guardar(ruta: Path, filas: list[dict[str, Any]], gasto: float, tope: float) -> dict[str, Any]:
    datos = {
        "fecha": datetime.now(UTC).isoformat(timespec="seconds"),
        "criterio": f"Funciona en la tarea {TAREA_HUMO} del corpus B en C2 (sin errores, con "
        f"ofertas, interpretación completa y en menos de {LIMITE_S // 60} minutos) y tiene "
        "desempeño con evidencia: acertó la tarea o tiene M2 medido en E3 (D107).",
        "tope_usd": tope,
        "gasto_usd": round(gasto, 6),
        "modelos": filas,
    }
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return datos


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--humo", action="store_true", help="Corre la prueba de humo (con costo)")
    parser.add_argument("--tope", type=float, default=TOPE_HUMO_USD)
    args = parser.parse_args()
    logging.basicConfig(format="%(message)s")
    logging.getLogger("comercio_agentico").setLevel(logging.INFO)
    if args.humo:
        datos = asyncio.run(humo(args.tope))
        print(f"Gasto US${datos['gasto_usd']:.4f}")
    for m in cargar_lista():
        print(f"{m['nombre']:16} {m['etiqueta']:40} US${m['costo_usd']:.4f}  {m['segundos']} s")


if __name__ == "__main__":
    main()
