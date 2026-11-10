# Métricas de la corrida `2026-11-10_e2_c2`

Modelo `deepseek-flash` · C2 · prompt `9e49060f5a9e` · corpus `c5925ac52cad` · commit 2de318c-sucio · 30 ejecuciones · 0 con error.

Proporciones: valor [IC 95 % de Wilson] (aciertos/total). Costo y latencia: valor [IC 95 % bootstrap].

## M2 Éxito por categoría de tarea

| Categoría | Éxito |
|---|---|
| especifica | 100,0 % [61,0–100,0] (6/6) |
| mas_barato | 100,0 % [61,0–100,0] (6/6) |
| restricciones | 100,0 % [67,6–100,0] (8/8) |
| vaga | 83,3 % [43,6–97,0] (5/6) |
| sin_respuesta | 100,0 % [51,0–100,0] (4/4) |
| **Global** | **96,7 % [83,3–99,4] (29/30)** |

Procedencia completa en el cuadro: 100,0 % [88,6–100,0] (30/30).

## M1 Exactitud de extracción por ruta

| Fuente | Ofertas (de listado) | Exactitud por campo | Sin correspondencia |
|---|---|---|---|
| P1 MCP | 93 (0) | 100,0 % [99,4–100,0] (651/651) | 0,0 % [0,0–4,0] (0/93) |
| P2 HTML + JSON-LD | 600 (559) | 94,2 % [92,5–95,6] (846/898) | 0,0 % [0,0–0,6] (0/600) |
| P3 HTML plano | 130 (0) | 97,0 % [95,4–98,0] (645/665) | 0,8 % [0,1–4,2] (1/130) |
| P4 PDF | 645 (0) | 97,1 % [96,3–97,6] (2504/2580) | 0,0 % [0,0–0,6] (0/645) |
| P5 mensaje | 390 (0) | 90,2 % [88,6–91,6] (1407/1560) | 0,0 % [0,0–1,0] (0/390) |
| **Todas** | | **95,3 % [94,7–95,8] (6053/6354)** | 0,1 % [0,0–0,3] (1/1858) |

Recolección (ofertas válidas de la tarea que llegaron al cuadro): 97,9 % [94,0–99,3] (139/142).

Exactitud por campo y fuente:

| Campo | P1 MCP | P2 HTML + JSON-LD | P3 HTML plano | P4 PDF | P5 mensaje |
|---|---|---|---|---|---|
| precio | 100 % (93/93) | 100 % (600/600) | 100 % (129/129) | 100 % (645/645) | 100 % (390/390) |
| costo_envio | 100 % (93/93) | 100 % (41/41) | 100 % (129/129) | 100 % (644/645) | 84 % (327/390) |
| disponibilidad | 100 % (93/93) | 100 % (41/41) | 100 % (129/129) | 100 % (644/645) | 100 % (390/390) |
| plazo_entrega_dias | 100 % (93/93) | 100 % (41/41) | 100 % (129/129) | 89 % (571/645) | 77 % (300/390) |
| gtin | 100 % (93/93) | 100 % (41/41) | — | — | — |
| mpn | 100 % (93/93) | 44 % (41/93) | 0 % (0/20) | — | — |
| marca | 100 % (93/93) | 100 % (41/41) | 100 % (129/129) | — | — |

## M3 Acuerdo entre ejecuciones

No aplica: la corrida tiene una sola repetición.

## M4 Abstención

- Abstención correcta (se abstiene cuando debe): 100,0 % [51,0–100,0] (4/4)
- Abstención indebida (se abstiene habiendo respuesta): 0,0 % [0,0–12,9] (0/26)
- Cobertura (responde cuando hay respuesta): 100,0 % [87,1–100,0] (26/26)
- Exactitud sobre lo cubierto: 96,2 % [81,1–99,3] (25/26)

## M6 Costo y latencia

- Costo total: US$0,4761
- Costo por tarea: media US$0,0159 [0,0151–0,0167]; p50 US$0,0156 [0,0147–0,0169]; p90 US$0,0190 [0,0176–0,0196]
- Latencia: p50 128 [123–155] s; p90 177 [160–219] s
- Por tarea: 40446 tokens de entrada, 33030 de salida, 14,3 llamadas al LLM, 8,7 herramientas
