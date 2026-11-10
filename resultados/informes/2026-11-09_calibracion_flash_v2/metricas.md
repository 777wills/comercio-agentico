# Métricas de la corrida `2026-11-09_calibracion_flash`

Modelo `deepseek-flash` · C1 · prompt `9e49060f5a9e` · corpus `761e13ff945f` · commit 5b52ef4-sucio · 60 ejecuciones · 0 con error.

Proporciones: valor [IC 95 % de Wilson] (aciertos/total). Costo y latencia: valor [IC 95 % bootstrap].

## M2 Éxito por categoría de tarea

| Categoría | Éxito |
|---|---|
| especifica | 100,0 % [75,8–100,0] (12/12) |
| mas_barato | 100,0 % [75,8–100,0] (12/12) |
| restricciones | 93,3 % [70,2–98,8] (14/15) |
| vaga | 58,3 % [32,0–80,7] (7/12) |
| sin_respuesta | 100,0 % [70,1–100,0] (9/9) |
| **Global** | **90,0 % [79,9–95,3] (54/60)** |

Procedencia completa en el cuadro: 100,0 % [94,0–100,0] (60/60).

## M1 Exactitud de extracción por ruta

| Fuente | Ofertas (de listado) | Exactitud por campo | Sin correspondencia |
|---|---|---|---|
| P1 MCP | 199 (0) | 100,0 % [99,7–100,0] (1393/1393) | 0,0 % [0,0–1,9] (0/199) |
| P2 HTML + JSON-LD | 1188 (1099) | 94,1 % [92,9–95,1] (1710/1818) | 0,0 % [0,0–0,3] (0/1188) |
| P3 HTML plano | 252 (0) | 99,7 % [99,2–99,9] (1250/1254) | 0,8 % [0,2–2,8] (2/252) |
| P4 PDF | 1260 (0) | 97,2 % [96,7–97,6] (4897/5040) | 0,0 % [0,0–0,3] (0/1260) |
| P5 mensaje | 780 (0) | 91,2 % [90,1–92,1] (2838/3112) | 0,3 % [0,1–0,9] (2/780) |
| **Todas** | | **95,8 % [95,4–96,1] (12088/12617)** | 0,1 % [0,0–0,3] (4/3679) |

Recolección (ofertas válidas de la tarea que llegaron al cuadro): 99,2 % [97,2–99,8] (259/261).

Exactitud por campo y fuente:

| Campo | P1 MCP | P2 HTML + JSON-LD | P3 HTML plano | P4 PDF | P5 mensaje |
|---|---|---|---|---|---|
| precio | 100 % (199/199) | 100 % (1188/1188) | 100 % (250/250) | 100 % (1260/1260) | 100 % (778/778) |
| costo_envio | 100 % (199/199) | 100 % (89/89) | 100 % (250/250) | 99 % (1250/1260) | 88 % (683/778) |
| disponibilidad | 100 % (199/199) | 100 % (89/89) | 100 % (250/250) | 99 % (1253/1260) | 100 % (778/778) |
| plazo_entrega_dias | 100 % (199/199) | 100 % (89/89) | 100 % (250/250) | 90 % (1134/1260) | 77 % (599/778) |
| gtin | 100 % (199/199) | 94 % (84/89) | — | — | — |
| mpn | 100 % (199/199) | 44 % (82/185) | 0 % (0/4) | — | — |
| marca | 100 % (199/199) | 100 % (89/89) | 100 % (250/250) | — | — |

## M3 Acuerdo entre ejecuciones

No aplica: la corrida tiene una sola repetición.

## M4 Abstención

- Abstención correcta (se abstiene cuando debe): 100,0 % [70,1–100,0] (9/9)
- Abstención indebida (se abstiene habiendo respuesta): 0,0 % [0,0–7,0] (0/51)
- Cobertura (responde cuando hay respuesta): 100,0 % [93,0–100,0] (51/51)
- Exactitud sobre lo cubierto: 88,2 % [76,6–94,5] (45/51)

## M6 Costo y latencia

- Costo total: US$0,9387
- Costo por tarea: media US$0,0156 [0,0149–0,0165]; p50 US$0,0150 [0,0142–0,0156]; p90 US$0,0199 [0,0176–0,0219]
- Latencia: p50 161 [153–176] s; p90 253 [215–297] s
- Por tarea: 38156 tokens de entrada, 32153 de salida, 14,4 llamadas al LLM, 8,9 herramientas
