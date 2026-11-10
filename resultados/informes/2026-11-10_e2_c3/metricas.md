# Métricas de la corrida `2026-11-10_e2_c3`

Modelo `deepseek-flash` · C3 · prompt `9e49060f5a9e` · corpus `c5925ac52cad` · commit 2de318c-sucio · 30 ejecuciones · 0 con error.

Proporciones: valor [IC 95 % de Wilson] (aciertos/total). Costo y latencia: valor [IC 95 % bootstrap].

## M2 Éxito por categoría de tarea

| Categoría | Éxito |
|---|---|
| especifica | 100,0 % [61,0–100,0] (6/6) |
| mas_barato | 100,0 % [61,0–100,0] (6/6) |
| restricciones | 100,0 % [67,6–100,0] (8/8) |
| vaga | 66,7 % [30,0–90,3] (4/6) |
| sin_respuesta | 100,0 % [51,0–100,0] (4/4) |
| **Global** | **93,3 % [78,7–98,2] (28/30)** |

Procedencia completa en el cuadro: 100,0 % [88,6–100,0] (30/30).

## M1 Exactitud de extracción por ruta

| Fuente | Ofertas (de listado) | Exactitud por campo | Sin correspondencia |
|---|---|---|---|
| P1 MCP | 95 (0) | 100,0 % [99,4–100,0] (665/665) | 0,0 % [0,0–3,9] (0/95) |
| P2 HTML + JSON-LD | 591 (542) | 93,2 % [91,4–94,6] (885/950) | 0,0 % [0,0–0,6] (0/591) |
| P3 HTML plano | 130 (0) | 96,7 % [95,0–97,8] (640/662) | 1,5 % [0,4–5,4] (2/130) |
| P4 PDF | 647 (0) | 96,4 % [95,6–97,0] (2494/2588) | 0,0 % [0,0–0,6] (0/647) |
| P5 mensaje | 390 (0) | 89,4 % [87,8–90,8] (1391/1556) | 0,3 % [0,0–1,4] (1/390) |
| **Todas** | | **94,6 % [94,0–95,1] (6075/6421)** | 0,2 % [0,1–0,5] (3/1853) |

Recolección (ofertas válidas de la tarea que llegaron al cuadro): 99,3 % [96,1–99,9] (141/142).

Exactitud por campo y fuente:

| Campo | P1 MCP | P2 HTML + JSON-LD | P3 HTML plano | P4 PDF | P5 mensaje |
|---|---|---|---|---|---|
| precio | 100 % (95/95) | 100 % (591/591) | 100 % (128/128) | 100 % (647/647) | 100 % (389/389) |
| costo_envio | 100 % (95/95) | 100 % (49/49) | 100 % (128/128) | 100 % (644/647) | 81 % (314/389) |
| disponibilidad | 100 % (95/95) | 100 % (49/49) | 100 % (128/128) | 100 % (644/647) | 100 % (389/389) |
| plazo_entrega_dias | 100 % (95/95) | 100 % (49/49) | 100 % (128/128) | 86 % (559/647) | 77 % (299/389) |
| gtin | 100 % (95/95) | 100 % (49/49) | — | — | — |
| mpn | 100 % (95/95) | 43 % (49/114) | 0 % (0/22) | — | — |
| marca | 100 % (95/95) | 100 % (49/49) | 100 % (128/128) | — | — |

## M3 Acuerdo entre ejecuciones

No aplica: la corrida tiene una sola repetición.

## M4 Abstención

- Abstención correcta (se abstiene cuando debe): 100,0 % [51,0–100,0] (4/4)
- Abstención indebida (se abstiene habiendo respuesta): 0,0 % [0,0–12,9] (0/26)
- Cobertura (responde cuando hay respuesta): 100,0 % [87,1–100,0] (26/26)
- Exactitud sobre lo cubierto: 92,3 % [75,9–97,9] (24/26)

## M6 Costo y latencia

- Costo total: US$0,4789
- Costo por tarea: media US$0,0160 [0,0152–0,0167]; p50 US$0,0160 [0,0147–0,0166]; p90 US$0,0188 [0,0171–0,0200]
- Latencia: p50 144 [130–156] s; p90 194 [173–219] s
- Por tarea: 41959 tokens de entrada, 32305 de salida, 15,1 llamadas al LLM, 9,3 herramientas
