# Métricas de la corrida `2026-11-09_calibracion_flash_v1`

Modelo `deepseek-flash` · C1 · prompt `724697af2251` · corpus `761e13ff945f` · commit d097e70-sucio · 60 ejecuciones · 0 con error.

Proporciones: valor [IC 95 % de Wilson] (aciertos/total). Costo y latencia: valor [IC 95 % bootstrap].

## M2 Éxito por categoría de tarea

| Categoría | Éxito |
|---|---|
| especifica | 100,0 % [75,8–100,0] (12/12) |
| mas_barato | 91,7 % [64,6–98,5] (11/12) |
| restricciones | 86,7 % [62,1–96,3] (13/15) |
| vaga | 41,7 % [19,3–68,0] (5/12) |
| sin_respuesta | 88,9 % [56,5–98,0] (8/9) |
| **Global** | **81,7 % [70,1–89,4] (49/60)** |

Procedencia completa en el cuadro: 100,0 % [94,0–100,0] (60/60).

## M1 Exactitud de extracción por ruta

| Fuente | Ofertas (de listado) | Exactitud por campo | Sin correspondencia |
|---|---|---|---|
| P1 MCP | 190 (0) | 99,9 % [99,6–100,0] (1329/1330) | 0,0 % [0,0–2,0] (0/190) |
| P2 HTML + JSON-LD | 1169 (1078) | 94,2 % [93,0–95,2] (1694/1799) | 0,0 % [0,0–0,3] (0/1169) |
| P3 HTML plano | 243 (0) | 99,7 % [99,2–99,9] (1210/1214) | 0,4 % [0,1–2,3] (1/243) |
| P4 PDF | 1290 (0) | 97,2 % [96,8–97,7] (5018/5160) | 0,0 % [0,0–0,3] (0/1290) |
| P5 mensaje | 776 (0) | 90,8 % [89,8–91,8] (2819/3104) | 0,0 % [0,0–0,5] (0/776) |
| **Todas** | | **95,7 % [95,4–96,1] (12070/12607)** | 0,0 % [0,0–0,2] (1/3668) |

Recolección (ofertas válidas de la tarea que llegaron al cuadro): 99,2 % [97,2–99,8] (259/261).

Exactitud por campo y fuente:

| Campo | P1 MCP | P2 HTML + JSON-LD | P3 HTML plano | P4 PDF | P5 mensaje |
|---|---|---|---|---|---|
| precio | 100 % (190/190) | 100 % (1169/1169) | 100 % (242/242) | 100 % (1290/1290) | 100 % (776/776) |
| costo_envio | 100 % (190/190) | 100 % (91/91) | 100 % (242/242) | 100 % (1287/1290) | 86 % (671/776) |
| disponibilidad | 100 % (190/190) | 100 % (91/91) | 100 % (242/242) | 100 % (1287/1290) | 100 % (776/776) |
| plazo_entrega_dias | 100 % (190/190) | 100 % (91/91) | 100 % (242/242) | 89 % (1154/1290) | 77 % (596/776) |
| gtin | 99 % (189/190) | 87 % (79/91) | — | — | — |
| mpn | 100 % (190/190) | 47 % (82/175) | 0 % (0/4) | — | — |
| marca | 100 % (190/190) | 100 % (91/91) | 100 % (242/242) | — | — |

## M3 Acuerdo entre ejecuciones

No aplica: la corrida tiene una sola repetición.

## M4 Abstención

- Abstención correcta (se abstiene cuando debe): 88,9 % [56,5–98,0] (8/9)
- Abstención indebida (se abstiene habiendo respuesta): 2,0 % [0,3–10,3] (1/51)
- Cobertura (responde cuando hay respuesta): 98,0 % [89,7–99,7] (50/51)
- Exactitud sobre lo cubierto: 80,4 % [67,5–89,0] (41/51)

## M6 Costo y latencia

- Costo total: US$0,8874
- Costo por tarea: media US$0,0148 [0,0143–0,0152]; p50 US$0,0148 [0,0143–0,0152]; p90 US$0,0166 [0,0156–0,0187]
- Latencia: p50 179 [171–188] s; p90 255 [216–304] s
- Por tarea: 37595 tokens de entrada, 30009 de salida, 14,1 llamadas al LLM, 8,7 herramientas
