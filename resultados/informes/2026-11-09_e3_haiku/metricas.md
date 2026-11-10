# Métricas de la corrida `2026-11-09_e3_haiku`

Modelo `haiku` · C1 · prompt `9e49060f5a9e` · corpus `c5925ac52cad` · commit 595e0b4-sucio · 90 ejecuciones · 0 con error.

Proporciones: valor [IC 95 % de Wilson] (aciertos/total). Costo y latencia: valor [IC 95 % bootstrap].

## M2 Éxito por categoría de tarea

| Categoría | Éxito |
|---|---|
| especifica | 100,0 % [82,4–100,0] (18/18) |
| mas_barato | 83,3 % [60,8–94,2] (15/18) |
| restricciones | 100,0 % [86,2–100,0] (24/24) |
| vaga | 66,7 % [43,7–83,7] (12/18) |
| sin_respuesta | 100,0 % [75,8–100,0] (12/12) |
| **Global** | **90,0 % [82,1–94,6] (81/90)** |

Procedencia completa en el cuadro: 100,0 % [95,9–100,0] (90/90).

## M1 Exactitud de extracción por ruta

| Fuente | Ofertas (de listado) | Exactitud por campo | Sin correspondencia |
|---|---|---|---|
| P1 MCP | 204 (0) | 100,0 % [99,7–100,0] (1428/1428) | 0,0 % [0,0–1,8] (0/204) |
| P2 HTML + JSON-LD | 1800 (1659) | 100,0 % [99,9–100,0] (2646/2646) | 0,0 % [0,0–0,2] (0/1800) |
| P3 HTML plano | 390 (0) | 99,0 % [98,5–99,4] (1950/1969) | 0,0 % [0,0–1,0] (0/390) |
| P4 PDF | 1980 (0) | 96,3 % [95,9–96,7] (7540/7826) | 1,2 % [0,8–1,8] (24/1980) |
| P5 mensaje | 1158 (0) | 93,5 % [92,8–94,2] (4328/4629) | 0,1 % [0,0–0,5] (1/1158) |
| **Todas** | | **96,7 % [96,5–97,0] (17892/18498)** | 0,5 % [0,3–0,7] (25/5532) |

Recolección (ofertas válidas de la tarea que llegaron al cuadro): 100,0 % [99,1–100,0] (426/426).

Exactitud por campo y fuente:

| Campo | P1 MCP | P2 HTML + JSON-LD | P3 HTML plano | P4 PDF | P5 mensaje |
|---|---|---|---|---|---|
| precio | 100 % (204/204) | 100 % (1800/1800) | 100 % (390/390) | 100 % (1956/1956) | 100 % (1157/1157) |
| costo_envio | 100 % (204/204) | 100 % (141/141) | 100 % (390/390) | 100 % (1956/1956) | 100 % (1154/1157) |
| disponibilidad | 100 % (204/204) | 100 % (141/141) | 100 % (390/390) | 100 % (1956/1956) | 100 % (1157/1157) |
| plazo_entrega_dias | 100 % (204/204) | 100 % (141/141) | 100 % (390/390) | 85 % (1672/1956) | 74 % (860/1157) |
| gtin | 100 % (204/204) | 100 % (141/141) | — | — | — |
| mpn | 100 % (204/204) | 100 % (141/141) | 0 % (0/19) | 0 % (0/2) | 0 % (0/1) |
| marca | 100 % (204/204) | 100 % (141/141) | 100 % (390/390) | — | — |

## M3 Acuerdo entre ejecuciones

3 repeticiones. Misma decisión en todas: 93,3 % [78,7–98,2] (28/30).
M2 por repetición: 90,0 %, 93,3 %, 86,7 % (rango 6,7 puntos, desviación 3,3).

## M4 Abstención

- Abstención correcta (se abstiene cuando debe): 100,0 % [75,8–100,0] (12/12)
- Abstención indebida (se abstiene habiendo respuesta): 7,7 % [3,6–15,8] (6/78)
- Cobertura (responde cuando hay respuesta): 92,3 % [84,2–96,4] (72/78)
- Exactitud sobre lo cubierto: 95,8 % [88,5–98,6] (69/72)

## M6 Costo y latencia

- Costo total: US$1,5279
- Costo por tarea: media US$0,0170 [0,0166–0,0173]; p50 US$0,0167 [0,0162–0,0174]; p90 US$0,0195 [0,0186–0,0199]
- Latencia: p50 56 [54–58] s; p90 68 [64–75] s
- Por tarea: 66738 tokens de entrada, 20606 de salida, 13,6 llamadas al LLM, 8,4 herramientas
