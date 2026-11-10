"""Corpus A: tiendas colombianas reales reconstruidas a partir de hechos (D70).

Las fichas públicas se leen una vez con un robot identificable; se conservan solo los hechos
(título, precios, GTIN, disponibilidad, envío) y la suma de verificación del HTML leído. Las páginas
que navega el agente se reconstruyen con la estructura de cada tienda, sin copiar su contenido.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3] / "corpus" / "a_real"
RUTA_SEMILLAS = RAIZ / "semillas.yaml"
RUTA_HECHOS = RAIZ / "hechos.jsonl"
RUTA_MANIFIESTO = RAIZ / "manifest.json"
AGENTE_USUARIO = "ComercioAgenticoBot/0.1 (+https://github.com/777wills/comercio-agentico)"
TIENDAS = {"A1": "alkosto.com", "A2": "ktronix.com", "A3": "falabella.com.co"}
