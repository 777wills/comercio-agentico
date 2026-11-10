"""Subconjunto estratificado de tareas para E3 (D64), congelado en ``tareas/subconjunto_e3.jsonl``.

La mitad de cada categoría, elegida al azar con semilla fija y antes de ver los resultados de la
calibración (sin sesgo de selección). Uso: ``uv run python -m comercio_agentico.arnes.subconjunto``.
"""

from __future__ import annotations

import random

from comercio_agentico.corpus_b import RAIZ
from comercio_agentico.corpus_b.tareas import Tarea, cargar_tareas

RUTA_SUBCONJUNTO_E3 = RAIZ / "tareas" / "subconjunto_e3.jsonl"
SEMILLA = 20261113
CUOTAS = {"especifica": 6, "mas_barato": 6, "restricciones": 8, "vaga": 6, "sin_respuesta": 4}


def elegir(
    tareas: list[Tarea], cuotas: dict[str, int] = CUOTAS, semilla: int = SEMILLA
) -> list[Tarea]:
    azar = random.Random(semilla)
    elegidas: set[str] = set()
    for categoria, n in cuotas.items():
        grupo = sorted(t.id for t in tareas if t.categoria == categoria)
        elegidas.update(azar.sample(grupo, n))
    return [t for t in tareas if t.id in elegidas]


def main() -> None:
    sub = elegir(cargar_tareas())
    RUTA_SUBCONJUNTO_E3.write_text(
        "".join(t.model_dump_json() + "\n" for t in sub), encoding="utf-8"
    )
    print(
        f"{len(sub)} tareas en {RUTA_SUBCONJUNTO_E3.relative_to(RAIZ)}:",
        ", ".join(t.id for t in sub),
    )


if __name__ == "__main__":
    main()
