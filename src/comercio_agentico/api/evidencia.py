"""Expediente de evidencia de una consulta (D142).

Reúne, sin llamar a ningún modelo, todo lo que la consulta dejó guardado: la necesidad interpretada,
las lecturas que hizo el agente (eventos), las ofertas encontradas y descartadas con su motivo, el
cuadro comparativo, la recomendación o la abstención, la procedencia por dato y el costo. El
informe de cotización del navegador se arma con este documento y el comprador puede descargarlo.

La huella es el SHA-256 del expediente en forma canónica (claves ordenadas, UTF-8, sin espacios),
calculada sin el campo ``huella_sha256``: quien recibe el archivo la recalcula con :func:`huella`
y comprueba que nadie lo alteró después de generarlo.

    uv run python -m comercio_agentico.api.evidencia expediente.json   # verifica la huella
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from comercio_agentico.api.bd import ConsultaBD

VERSION = 1
CAMPO_HUELLA = "huella_sha256"


def huella(expediente: dict[str, Any]) -> str:
    """SHA-256 del expediente canónico, sin el propio campo de la huella."""
    sin_huella = {k: v for k, v in expediente.items() if k != CAMPO_HUELLA}
    canonico = json.dumps(sin_huella, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()


def expediente(fila: ConsultaBD, generado: datetime | None = None) -> dict[str, Any]:
    """Documento completo de la consulta, con su huella. Exige una consulta con propuesta."""
    doc: dict[str, Any] = {
        "version": VERSION,
        "generado": (generado or datetime.now(UTC)).isoformat(),
        "consulta": {
            "id": fila.id,
            "texto": fila.consulta,
            "corpus": fila.corpus,
            "carga": fila.carga,
            "modelo": fila.modelo,
            "opciones": fila.opciones,
            "estado": fila.estado,
            "creada": fila.creada.isoformat(),
            "costo_usd": fila.costo_usd,
            "segundos": fila.segundos,
        },
        "propuesta": fila.propuesta,
        "detalle": fila.detalle,
        "eventos": fila.eventos or [],
    }
    doc[CAMPO_HUELLA] = huella(doc)
    return doc


def verificar(expediente: dict[str, Any]) -> bool:
    return expediente.get(CAMPO_HUELLA) == huella(expediente)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Uso: python -m comercio_agentico.api.evidencia expediente.json")
    doc = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if verificar(doc):
        print(f"Huella válida: {doc[CAMPO_HUELLA]}")
    else:
        sys.exit(f"Huella NO válida: dice {doc.get(CAMPO_HUELLA)}, calculada {huella(doc)}")
