# Métricas de la corrida `2026-11-10_e2_c0`

Modelo `deepseek-flash` · C0 · prompt `9e49060f5a9e` · corpus `c5925ac52cad` · commit 2de318c-sucio · 30 ejecuciones · 0 con error.

Proporciones: valor [IC 95 % de Wilson] (aciertos/total). Costo y latencia: valor [IC 95 % bootstrap].

## M2 Éxito por categoría de tarea

| Categoría | Éxito |
|---|---|
| especifica | 83,3 % [43,6–97,0] (5/6) |
| mas_barato | 100,0 % [61,0–100,0] (6/6) |
| restricciones | 100,0 % [67,6–100,0] (8/8) |
| vaga | 83,3 % [43,6–97,0] (5/6) |
| sin_respuesta | 100,0 % [51,0–100,0] (4/4) |
| **Global** | **93,3 % [78,7–98,2] (28/30)** |

Procedencia completa en el cuadro: 100,0 % [88,6–100,0] (30/30).

## M1 Exactitud de extracción por ruta

| Fuente | Ofertas (de listado) | Exactitud por campo | Sin correspondencia |
|---|---|---|---|
| P1 MCP | 88 (0) | 100,0 % [99,4–100,0] (616/616) | 0,0 % [0,0–4,2] (0/88) |
| P2 HTML + JSON-LD | 599 (559) | 93,0 % [91,2–94,5] (839/902) | 0,0 % [0,0–0,6] (0/599) |
| P3 HTML plano | 130 (0) | 96,9 % [95,3–97,9] (650/671) | 0,0 % [0,0–2,9] (0/130) |
| P4 PDF | 612 (0) | 95,8 % [95,0–96,6] (2346/2448) | 0,0 % [0,0–0,6] (0/612) |
| P5 mensaje | 390 (0) | 91,3 % [89,8–92,6] (1425/1560) | 0,0 % [0,0–1,0] (0/390) |
| **Todas** | | **94,8 % [94,2–95,3] (5876/6197)** | 0,0 % [0,0–0,2] (0/1819) |

Recolección (ofertas válidas de la tarea que llegaron al cuadro): 97,2 % [93,0–98,9] (138/142).

Exactitud por campo y fuente:

| Campo | P1 MCP | P2 HTML + JSON-LD | P3 HTML plano | P4 PDF | P5 mensaje |
|---|---|---|---|---|---|
| precio | 100 % (88/88) | 100 % (599/599) | 100 % (130/130) | 100 % (612/612) | 100 % (390/390) |
| costo_envio | 100 % (88/88) | 100 % (40/40) | 100 % (130/130) | 99 % (607/612) | 88 % (345/390) |
| disponibilidad | 100 % (88/88) | 100 % (40/40) | 100 % (130/130) | 100 % (611/612) | 100 % (390/390) |
| plazo_entrega_dias | 100 % (88/88) | 100 % (40/40) | 100 % (130/130) | 84 % (516/612) | 77 % (300/390) |
| gtin | 100 % (88/88) | 100 % (40/40) | — | — | — |
| mpn | 100 % (88/88) | 39 % (40/103) | 0 % (0/21) | — | — |
| marca | 100 % (88/88) | 100 % (40/40) | 100 % (130/130) | — | — |

## M3 Acuerdo entre ejecuciones

No aplica: la corrida tiene una sola repetición.

## M4 Abstención

- Abstención correcta (se abstiene cuando debe): 100,0 % [51,0–100,0] (4/4)
- Abstención indebida (se abstiene habiendo respuesta): 0,0 % [0,0–12,9] (0/26)
- Cobertura (responde cuando hay respuesta): 100,0 % [87,1–100,0] (26/26)
- Exactitud sobre lo cubierto: 92,3 % [75,9–97,9] (24/26)

## M6 Costo y latencia

- Costo total: US$0,4673
- Costo por tarea: media US$0,0156 [0,0149–0,0162]; p50 US$0,0153 [0,0146–0,0160]; p90 US$0,0187 [0,0163–0,0193]
- Latencia: p50 135 [124–140] s; p90 192 [165–198] s
- Por tarea: 36677 tokens de entrada, 31103 de salida, 13,5 llamadas al LLM, 8,2 herramientas
