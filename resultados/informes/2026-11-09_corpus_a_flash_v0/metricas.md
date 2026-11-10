# Métricas de la corrida `2026-11-09_corpus_a_flash`

Modelo `deepseek-flash` · C1 · prompt `9e49060f5a9e` · corpus `e26b373d68e8` · commit 5b52ef4-sucio · 20 ejecuciones · 0 con error.

Proporciones: valor [IC 95 % de Wilson] (aciertos/total). Costo y latencia: valor [IC 95 % bootstrap].

## M2 Éxito por categoría de tarea

| Categoría | Éxito |
|---|---|
| especifica | 16,7 % [3,0–56,4] (1/6) |
| mas_barato | 40,0 % [11,8–76,9] (2/5) |
| restricciones | 20,0 % [3,6–62,4] (1/5) |
| sin_respuesta | 100,0 % [51,0–100,0] (4/4) |
| **Global** | **40,0 % [21,9–61,3] (8/20)** |

Procedencia completa en el cuadro: 100,0 % [83,9–100,0] (20/20).

## M1 Exactitud de extracción por ruta

| Fuente | Ofertas (de listado) | Exactitud por campo | Sin correspondencia |
|---|---|---|---|
| P2 HTML + JSON-LD | 1129 (1048) | 78,0 % [75,9–80,0] (1217/1560) | 1,3 % [0,8–2,2] (15/1129) |
| **Todas** | | **78,0 % [75,9–80,0] (1217/1560)** | 1,3 % [0,8–2,2] (15/1129) |

Recolección (ofertas válidas de la tarea que llegaron al cuadro): 100,0 % [89,6–100,0] (33/33).

Exactitud por campo y fuente:

| Campo | P2 HTML + JSON-LD |
|---|---|
| precio | 87 % (974/1114) |
| costo_envio | 100 % (66/66) |
| disponibilidad | 43 % (29/68) |
| plazo_entrega_dias | 100 % (66/66) |
| gtin | 26 % (16/62) |
| mpn | 0 % (0/118) |
| marca | 100 % (66/66) |

## M3 Acuerdo entre ejecuciones

No aplica: la corrida tiene una sola repetición.

## M4 Abstención

- Abstención correcta (se abstiene cuando debe): 100,0 % [51,0–100,0] (4/4)
- Abstención indebida (se abstiene habiendo respuesta): 50,0 % [28,0–72,0] (8/16)
- Cobertura (responde cuando hay respuesta): 50,0 % [28,0–72,0] (8/16)
- Exactitud sobre lo cubierto: 50,0 % [21,5–78,5] (4/8)

## M6 Costo y latencia

- Costo total: US$0,3615
- Costo por tarea: media US$0,0181 [0,0173–0,0189]; p50 US$0,0173 [0,0171–0,0182]; p90 US$0,0213 [0,0181–0,0218]
- Latencia: p50 183 [165–194] s; p90 213 [194–268] s
- Por tarea: 52497 tokens de entrada, 34090 de salida, 14,1 llamadas al LLM, 9,2 herramientas
