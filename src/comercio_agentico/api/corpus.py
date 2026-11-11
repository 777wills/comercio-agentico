"""Visor del corpus congelado de CotIA (D87): índice de fuentes y archivos por lista blanca.

Corpus B (proveedores sintéticos P1–P5), corpus A (tiendas reconstruidas) y la copia atacada de cada
carga (``corpus/b_ataques/<id>/``, regenerable con ``python -m comercio_agentico.ataques.plantar``).
"""

from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import Any

import yaml

from comercio_agentico.corpus_b import RAIZ

DIR_CORPUS = {"b": RAIZ / "corpus" / "b_sintetico", "a": RAIZ / "corpus" / "a_real" / "sitio"}
DIR_ATAQUES = RAIZ / "corpus" / "b_ataques"
REGISTROS = {"b": RAIZ / "fuentes" / "corpus_b.yaml", "a": RAIZ / "fuentes" / "corpus_a.yaml"}
TIPOS_MIME = {
    ".html": "text/html; charset=utf-8",
    ".json": "application/json",
    ".txt": "text/plain; charset=utf-8",
    ".pdf": "application/pdf",
}
# Una página del corpus no ejecuta scripts ni pide recursos externos en el navegador del visitante.
CSP_CORPUS = "default-src 'none'; style-src 'unsafe-inline'; img-src data:; sandbox"


def _archivos(raiz: Path) -> dict[str, Path]:
    if not raiz.is_dir():
        return {}
    return {
        p.relative_to(raiz).as_posix(): p
        for p in sorted(raiz.rglob("*"))
        if p.is_file() and p.suffix in TIPOS_MIME
    }


@cache
def lista_blanca(origen: str) -> dict[str, Path]:
    """Rutas servibles de un origen: ``b``, ``a`` o el ID de una carga (copia atacada)."""
    if origen in DIR_CORPUS:
        return _archivos(DIR_CORPUS[origen])
    return _archivos(DIR_ATAQUES / origen)


def indice() -> dict[str, Any]:
    from comercio_agentico.ataques.suite import cargar_suite

    corpus = {}
    for c, raiz in DIR_CORPUS.items():
        registro = yaml.safe_load(REGISTROS[c].read_text(encoding="utf-8"))["fuentes"]
        archivos = lista_blanca(c)
        fuentes = []
        for f in registro:
            fid = f["id"].lower()
            carpeta = next(
                (
                    d.name
                    for d in sorted(raiz.iterdir())
                    if d.is_dir() and (d.name == fid or d.name.startswith(f"{fid}_"))
                ),
                None,
            )
            fuentes.append(
                {
                    "id": f["id"],
                    "nombre": f["nombre"],
                    "tipo_fuente": f["tipo_fuente"],
                    "archivos": [r for r in archivos if carpeta and r.startswith(f"{carpeta}/")],
                }
            )
        corpus[c] = fuentes
    ataques = [
        {
            "carga": k.id,
            "clase": k.clase,
            "ubicacion": k.ubicacion,
            "proveedor": k.proveedor,
            "archivo": k.archivo,
            "objetivo": k.objetivo,
            "texto": k.texto,
            "disponible": k.archivo in lista_blanca(k.id),
        }
        for k in cargar_suite().cargas
    ]
    return {"corpus": corpus, "ataques": ataques}
