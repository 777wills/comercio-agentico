# Métricas de la corrida `2026-11-09_calibracion_flash_v0`

Modelo `deepseek-flash` · C1 · prompt `4dfdd15ebbcf` · corpus `761e13ff945f` · commit d097e70-sucio · 60 ejecuciones · 0 con error.

Proporciones: valor [IC 95 % de Wilson] (aciertos/total). Costo y latencia: valor [IC 95 % bootstrap].

## M2 Éxito por categoría de tarea

| Categoría | Éxito |
|---|---|
| especifica | 100,0 % [75,8–100,0] (12/12) |
| mas_barato | 100,0 % [75,8–100,0] (12/12) |
| restricciones | 80,0 % [54,8–93,0] (12/15) |
| vaga | 58,3 % [32,0–80,7] (7/12) |
| sin_respuesta | 100,0 % [70,1–100,0] (9/9) |
| **Global** | **86,7 % [75,8–93,1] (52/60)** |

Procedencia completa en el cuadro: 100,0 % [94,0–100,0] (60/60).

## M1 Exactitud de extracción por ruta

| Fuente | Ofertas (de listado) | Exactitud por campo | Sin correspondencia |
|---|---|---|---|
| P1 MCP | 189 (0) | 57,1 % [54,5–59,8] (756/1323) | 0,0 % [0,0–2,0] (0/189) |
| P2 HTML + JSON-LD | 1106 (999) | 74,4 % [72,4–76,3] (1427/1918) | 0,0 % [0,0–0,3] (0/1106) |
| P3 HTML plano | 243 (0) | 80,0 % [77,6–82,2] (964/1205) | 0,8 % [0,2–3,0] (2/243) |
| P4 PDF | 1320 (0) | 96,3 % [95,7–96,8] (5084/5280) | 0,0 % [0,0–0,3] (0/1320) |
| P5 mensaje | 780 (0) | 91,3 % [90,3–92,3] (2846/3116) | 0,1 % [0,0–0,7] (1/780) |
| **Todas** | | **86,3 % [85,6–86,8] (11077/12842)** | 0,1 % [0,0–0,2] (3/3638) |

Recolección (ofertas válidas de la tarea que llegaron al cuadro): 99,2 % [97,2–99,8] (259/261).

Exactitud por campo y fuente:

| Campo | P1 MCP | P2 HTML + JSON-LD | P3 HTML plano | P4 PDF | P5 mensaje |
|---|---|---|---|---|---|
| precio | 100 % (189/189) | 100 % (1106/1106) | 100 % (241/241) | 100 % (1320/1320) | 100 % (779/779) |
| costo_envio | 100 % (189/189) | 100 % (107/107) | 100 % (241/241) | 100 % (1316/1320) | 88 % (689/779) |
| disponibilidad | 100 % (189/189) | 39 % (107/277) | 100 % (241/241) | 100 % (1320/1320) | 100 % (779/779) |
| plazo_entrega_dias | 100 % (189/189) | 100 % (107/107) | 100 % (241/241) | 85 % (1128/1320) | 77 % (599/779) |
| gtin | 0 % (0/189) | 0 % (0/107) | — | — | — |
| mpn | 0 % (0/189) | 0 % (0/107) | — | — | — |
| marca | 0 % (0/189) | 0 % (0/107) | 0 % (0/241) | — | — |

## M3 Acuerdo entre ejecuciones

No aplica: la corrida tiene una sola repetición.

## M4 Abstención

- Abstención correcta (se abstiene cuando debe): 100,0 % [70,1–100,0] (9/9)
- Abstención indebida (se abstiene habiendo respuesta): 0,0 % [0,0–7,0] (0/51)
- Cobertura (responde cuando hay respuesta): 100,0 % [93,0–100,0] (51/51)
- Exactitud sobre lo cubierto: 84,3 % [72,0–91,8] (43/51)

## M6 Costo y latencia

- Costo total: US$0,8079
- Costo por tarea: media US$0,0135 [0,0130–0,0139]; p50 US$0,0133 [0,0127–0,0138]; p90 US$0,0161 [0,0146–0,0167]
- Latencia: p50 146 [138–159] s; p90 209 [178–244] s
- Por tarea: 39680 tokens de entrada, 26731 de salida, 14,6 llamadas al LLM, 9,0 herramientas
