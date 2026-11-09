"""Corpus B sintético: catálogo de referencia, cinco proveedores heterogéneos y tareas (D21).

La verdad de referencia se conoce por construcción: cada página, PDF o mensaje se genera desde
``verdad.json``, nunca al revés.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
DIR_CORPUS = RAIZ / "corpus" / "b_sintetico"
RUTA_CATALOGO = DIR_CORPUS / "catalogo.json"
RUTA_VERDAD = DIR_CORPUS / "verdad.json"
RUTA_TAREAS = RAIZ / "tareas" / "tareas_b.jsonl"
RUTA_PERFIL = RAIZ / "perfiles" / "electronica.yaml"
