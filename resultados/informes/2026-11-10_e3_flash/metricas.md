# Métricas de la corrida `2026-11-10_e3_flash`

Modelo `deepseek-flash` · C1 · prompt `9e49060f5a9e` · corpus `c5925ac52cad` · commit 595e0b4-sucio · 90 ejecuciones · 0 con error.

Proporciones: valor [IC 95 % de Wilson] (aciertos/total). Costo y latencia: valor [IC 95 % bootstrap].

## M2 Éxito por categoría de tarea

| Categoría | Éxito |
|---|---|
| especifica | 100,0 % [82,4–100,0] (18/18) |
| mas_barato | 88,9 % [67,2–96,9] (16/18) |
| restricciones | 95,8 % [79,8–99,3] (23/24) |
| vaga | 61,1 % [38,6–79,7] (11/18) |
| sin_respuesta | 100,0 % [75,8–100,0] (12/12) |
| **Global** | **88,9 % [80,7–93,9] (80/90)** |

Procedencia completa en el cuadro: 100,0 % [95,9–100,0] (90/90).

## M1 Exactitud de extracción por ruta

| Fuente | Ofertas (de listado) | Exactitud por campo | Sin correspondencia |
|---|---|---|---|
| P1 MCP | 284 (0) | 100,0 % [99,8–100,0] (1988/1988) | 0,0 % [0,0–1,3] (0/284) |
| P2 HTML + JSON-LD | 1755 (1609) | 92,7 % [91,7–93,6] (2631/2838) | 0,0 % [0,0–0,2] (0/1755) |
| P3 HTML plano | 390 (0) | 99,1 % [98,6–99,5] (1945/1962) | 0,3 % [0,0–1,4] (1/390) |
| P4 PDF | 1900 (0) | 96,3 % [95,8–96,7] (7316/7600) | 0,0 % [0,0–0,2] (0/1900) |
| P5 mensaje | 1170 (0) | 90,8 % [90,0–91,6] (4243/4672) | 0,2 % [0,0–0,6] (2/1170) |
| **Todas** | | **95,1 % [94,8–95,4] (18123/19060)** | 0,1 % [0,0–0,2] (3/5499) |

Recolección (ofertas válidas de la tarea que llegaron al cuadro): 98,8 % [97,3–99,5] (421/426).

Exactitud por campo y fuente:

| Campo | P1 MCP | P2 HTML + JSON-LD | P3 HTML plano | P4 PDF | P5 mensaje |
|---|---|---|---|---|---|
| precio | 100 % (284/284) | 100 % (1755/1755) | 100 % (389/389) | 100 % (1899/1900) | 100 % (1168/1168) |
| costo_envio | 100 % (284/284) | 100 % (146/146) | 100 % (389/389) | 99 % (1879/1900) | 86 % (1009/1168) |
| disponibilidad | 100 % (284/284) | 100 % (146/146) | 100 % (389/389) | 99 % (1890/1900) | 100 % (1168/1168) |
| plazo_entrega_dias | 100 % (284/284) | 100 % (146/146) | 100 % (389/389) | 87 % (1648/1900) | 77 % (898/1168) |
| gtin | 100 % (284/284) | 100 % (146/146) | — | — | — |
| mpn | 100 % (284/284) | 41 % (146/353) | 0 % (0/17) | — | — |
| marca | 100 % (284/284) | 100 % (146/146) | 100 % (389/389) | — | — |

## M3 Acuerdo entre ejecuciones

3 repeticiones. Misma decisión en todas: 86,7 % [70,3–94,7] (26/30).
M2 por repetición: 83,3 %, 90,0 %, 93,3 % (rango 10,0 puntos, desviación 5,1).

## M4 Abstención

- Abstención correcta (se abstiene cuando debe): 100,0 % [75,8–100,0] (12/12)
- Abstención indebida (se abstiene habiendo respuesta): 2,6 % [0,7–8,9] (2/78)
- Cobertura (responde cuando hay respuesta): 97,4 % [91,1–99,3] (76/78)
- Exactitud sobre lo cubierto: 89,5 % [80,6–94,6] (68/76)

## M6 Costo y latencia

- Costo total: US$1,3712
- Costo por tarea: media US$0,0152 [0,0149–0,0156]; p50 US$0,0151 [0,0145–0,0154]; p90 US$0,0176 [0,0165–0,0189]
- Latencia: p50 129 [123–136] s; p90 177 [162–190] s
- Por tarea: 39303 tokens de entrada, 31224 de salida, 14,4 llamadas al LLM, 8,9 herramientas
