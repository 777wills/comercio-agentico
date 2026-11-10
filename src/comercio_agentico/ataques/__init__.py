"""Suite adversarial: validación, plantado aislado, ejecución y defensas C0–C3.

Los textos se leen de ``ataques/cargas.yaml`` (publicados, D95). ``suite`` evalúa los predicados;
``plantar`` genera las copias locales; ``correr`` calcula M5.
``elegir_clasificador`` conserva la evidencia de selección del clasificador local de C2.
"""

from comercio_agentico.corpus_b import RAIZ

DIR_ATAQUES = RAIZ / "ataques"
