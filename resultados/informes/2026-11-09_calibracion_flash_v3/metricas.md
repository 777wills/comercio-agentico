# Métricas de la corrida `2026-11-09_calibracion_flash`

Modelo `deepseek-flash` · C1 · prompt `9e49060f5a9e` · corpus `761e13ff945f` · commit 595e0b4-sucio · 60 ejecuciones · 0 con error.

Proporciones: valor [IC 95 % de Wilson] (aciertos/total). Costo y latencia: valor [IC 95 % bootstrap].

## M2 Éxito por categoría de tarea

| Categoría | Éxito |
|---|---|
| especifica | 100,0 % [75,8–100,0] (12/12) |
| mas_barato | 100,0 % [75,8–100,0] (12/12) |
| restricciones | 100,0 % [79,6–100,0] (15/15) |
| vaga | 83,3 % [55,2–95,3] (10/12) |
| sin_respuesta | 100,0 % [70,1–100,0] (9/9) |
| **Global** | **96,7 % [88,6–99,1] (58/60)** |

Procedencia completa en el cuadro: 100,0 % [94,0–100,0] (60/60).

## M1 Exactitud de extracción por ruta

| Fuente | Ofertas (de listado) | Exactitud por campo | Sin correspondencia |
|---|---|---|---|
| P1 MCP | 195 (0) | 100,0 % [99,7–100,0] (1365/1365) | 0,0 % [0,0–1,9] (0/195) |
| P2 HTML + JSON-LD | 1200 (1127) | 95,7 % [94,7–96,6] (1638/1711) | 0,0 % [0,0–0,3] (0/1200) |
| P3 HTML plano | 243 (0) | 98,7 % [97,9–99,2] (1210/1226) | 0,4 % [0,1–2,3] (1/243) |
| P4 PDF | 1289 (0) | 96,3 % [95,8–96,8] (5009/5200) | 0,0 % [0,0–0,3] (0/1289) |
| P5 mensaje | 779 (0) | 91,5 % [90,5–92,4] (2840/3104) | 0,4 % [0,1–1,1] (3/779) |
| **Todas** | | **95,7 % [95,3–96,0] (12062/12606)** | 0,1 % [0,0–0,3] (4/3706) |

Recolección (ofertas válidas de la tarea que llegaron al cuadro): 99,2 % [97,2–99,8] (259/261).

Exactitud por campo y fuente:

| Campo | P1 MCP | P2 HTML + JSON-LD | P3 HTML plano | P4 PDF | P5 mensaje |
|---|---|---|---|---|---|
| precio | 100 % (195/195) | 100 % (1200/1200) | 100 % (242/242) | 100 % (1289/1289) | 100 % (776/776) |
| costo_envio | 100 % (195/195) | 100 % (73/73) | 100 % (242/242) | 99 % (1281/1289) | 88 % (685/776) |
| disponibilidad | 100 % (195/195) | 100 % (73/73) | 100 % (242/242) | 100 % (1285/1289) | 100 % (775/776) |
| plazo_entrega_dias | 100 % (195/195) | 100 % (73/73) | 100 % (242/242) | 90 % (1154/1289) | 78 % (604/776) |
| gtin | 100 % (195/195) | 100 % (73/73) | — | — | — |
| mpn | 100 % (195/195) | 50 % (73/146) | 0 % (0/16) | 0 % (0/44) | — |
| marca | 100 % (195/195) | 100 % (73/73) | 100 % (242/242) | — | — |

## M3 Acuerdo entre ejecuciones

No aplica: la corrida tiene una sola repetición.

## M4 Abstención

- Abstención correcta (se abstiene cuando debe): 100,0 % [70,1–100,0] (9/9)
- Abstención indebida (se abstiene habiendo respuesta): 2,0 % [0,3–10,3] (1/51)
- Cobertura (responde cuando hay respuesta): 98,0 % [89,7–99,7] (50/51)
- Exactitud sobre lo cubierto: 98,0 % [89,5–99,6] (49/50)

## M6 Costo y latencia

- Costo total: US$0,9194
- Costo por tarea: media US$0,0153 [0,0148–0,0159]; p50 US$0,0148 [0,0143–0,0153]; p90 US$0,0183 [0,0167–0,0204]
- Latencia: p50 151 [144–164] s; p90 196 [178–210] s
- Por tarea: 38231 tokens de entrada, 31419 de salida, 13,9 llamadas al LLM, 8,5 herramientas
