# Métricas de la corrida `2026-11-10_e2_c1`

Modelo `deepseek-flash` · C1 · prompt `9e49060f5a9e` · corpus `c5925ac52cad` · commit 2de318c-sucio · 30 ejecuciones · 0 con error.

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
| P1 MCP | 96 (0) | 100,0 % [99,4–100,0] (672/672) | 0,0 % [0,0–3,8] (0/96) |
| P2 HTML + JSON-LD | 599 (555) | 94,6 % [93,0–95,9] (863/912) | 0,0 % [0,0–0,6] (0/599) |
| P3 HTML plano | 130 (0) | 99,4 % [98,4–99,8] (645/649) | 0,8 % [0,1–4,2] (1/130) |
| P4 PDF | 626 (0) | 96,9 % [96,1–97,5] (2426/2504) | 0,0 % [0,0–0,6] (0/626) |
| P5 mensaje | 390 (0) | 90,7 % [89,2–92,1] (1412/1556) | 0,3 % [0,0–1,4] (1/390) |
| **Todas** | | **95,6 % [95,1–96,1] (6018/6293)** | 0,1 % [0,0–0,4] (2/1841) |

Recolección (ofertas válidas de la tarea que llegaron al cuadro): 100,0 % [97,4–100,0] (142/142).

Exactitud por campo y fuente:

| Campo | P1 MCP | P2 HTML + JSON-LD | P3 HTML plano | P4 PDF | P5 mensaje |
|---|---|---|---|---|---|
| precio | 100 % (96/96) | 100 % (599/599) | 100 % (129/129) | 100 % (626/626) | 100 % (389/389) |
| costo_envio | 100 % (96/96) | 100 % (44/44) | 100 % (129/129) | 99 % (622/626) | 86 % (335/389) |
| disponibilidad | 100 % (96/96) | 100 % (44/44) | 100 % (129/129) | 100 % (624/626) | 100 % (389/389) |
| plazo_entrega_dias | 100 % (96/96) | 100 % (44/44) | 100 % (129/129) | 88 % (554/626) | 77 % (299/389) |
| gtin | 100 % (96/96) | 100 % (44/44) | — | — | — |
| mpn | 100 % (96/96) | 47 % (44/93) | 0 % (0/4) | — | — |
| marca | 100 % (96/96) | 100 % (44/44) | 100 % (129/129) | — | — |

## M3 Acuerdo entre ejecuciones

No aplica: la corrida tiene una sola repetición.

## M4 Abstención

- Abstención correcta (se abstiene cuando debe): 100,0 % [51,0–100,0] (4/4)
- Abstención indebida (se abstiene habiendo respuesta): 0,0 % [0,0–12,9] (0/26)
- Cobertura (responde cuando hay respuesta): 100,0 % [87,1–100,0] (26/26)
- Exactitud sobre lo cubierto: 92,3 % [75,9–97,9] (24/26)

## M6 Costo y latencia

- Costo total: US$0,4787
- Costo por tarea: media US$0,0160 [0,0151–0,0169]; p50 US$0,0151 [0,0142–0,0174]; p90 US$0,0197 [0,0179–0,0209]
- Latencia: p50 130 [121–154] s; p90 200 [180–218] s
- Por tarea: 40673 tokens de entrada, 32745 de salida, 14,6 llamadas al LLM, 9,0 herramientas
