"""Suite adversarial (S06): infraestructura de defensa y medición.

Las defensas C0–C3 viven en ``comercio_agentico.agente.defensa`` y en el grafo. Aquí quedan las
utilidades de la suite que **no** redactan ni plantan cargas de ataque:

- ``elegir_clasificador``: mide falsos positivos y latencia de los clasificadores candidatos de C2
  sobre fragmentos limpios del corpus B (US$0, CPU), para elegir con evidencia.

La redacción y el plantado de las 20 cargas son tarea manual de Wills (``docs/PLAN.md``, S06-bis).
"""

from comercio_agentico.corpus_b import RAIZ

DIR_ATAQUES = RAIZ / "ataques"
