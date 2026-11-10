# Métricas de la corrida `2026-11-09_corpus_a_flash`

Modelo `deepseek-flash` · C1 · prompt `9e49060f5a9e` · corpus `bca70cb153ff` · commit 595e0b4-sucio · 20 ejecuciones · 0 con error.

Proporciones: valor [IC 95 % de Wilson] (aciertos/total). Costo y latencia: valor [IC 95 % bootstrap].

## M2 Éxito por categoría de tarea

| Categoría | Éxito |
|---|---|
| especifica | 83,3 % [43,6–97,0] (5/6) |
| mas_barato | 100,0 % [56,6–100,0] (5/5) |
| restricciones | 100,0 % [56,6–100,0] (5/5) |
| sin_respuesta | 100,0 % [51,0–100,0] (4/4) |
| **Global** | **95,0 % [76,4–99,1] (19/20)** |

Procedencia completa en el cuadro: 100,0 % [83,9–100,0] (20/20).

## M1 Exactitud de extracción por ruta

| Fuente | Ofertas (de listado) | Exactitud por campo | Sin correspondencia |
|---|---|---|---|
| P2 HTML + JSON-LD | 1104 (1032) | 79,8 % [77,8–81,7] (1265/1585) | 0,0 % [0,0–0,3] (0/1104) |
| **Todas** | | **79,8 % [77,8–81,7] (1265/1585)** | 0,0 % [0,0–0,3] (0/1104) |

Recolección (ofertas válidas de la tarea que llegaron al cuadro): 100,0 % [89,6–100,0] (33/33).

Exactitud por campo y fuente:

| Campo | P2 HTML + JSON-LD |
|---|---|
| precio | 88 % (976/1104) |
| costo_envio | 100 % (72/72) |
| disponibilidad | 96 % (72/75) |
| plazo_entrega_dias | 100 % (72/72) |
| gtin | 1 % (1/67) |
| mpn | 0 % (0/123) |
| marca | 100 % (72/72) |

## M3 Acuerdo entre ejecuciones

No aplica: la corrida tiene una sola repetición.

## M4 Abstención

- Abstención correcta (se abstiene cuando debe): 100,0 % [51,0–100,0] (4/4)
- Abstención indebida (se abstiene habiendo respuesta): 6,2 % [1,1–28,3] (1/16)
- Cobertura (responde cuando hay respuesta): 93,8 % [71,7–98,9] (15/16)
- Exactitud sobre lo cubierto: 100,0 % [79,6–100,0] (15/15)

## M6 Costo y latencia

- Costo total: US$0,3609
- Costo por tarea: media US$0,0180 [0,0173–0,0189]; p50 US$0,0175 [0,0168–0,0184]; p90 US$0,0208 [0,0184–0,0224]
- Latencia: p50 169 [153–180] s; p90 207 [179–225] s
- Por tarea: 52856 tokens de entrada, 34383 de salida, 14,2 llamadas al LLM, 9,2 herramientas
