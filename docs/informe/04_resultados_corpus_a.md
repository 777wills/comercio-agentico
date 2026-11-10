# 4. Resultados — Corpus A (tiendas reales reconstruidas)

## 4.x Línea base del agente sobre el corpus A

La configuración de la calibración v2 (DeepSeek V4.1 Flash, separación de planos C1, 14 llamadas a herramientas
como máximo) se corrió una vez sobre las 20 tareas del corpus A (`resultados/corridas/2026-11-09_corpus_a_flash_v0`).

| Categoría | M2 |
|---|---|
| Producto específico | 16,7 % [3,0–56,4] (1/6) |
| Menor precio | 40,0 % [11,8–76,9] (2/5) |
| Restricciones | 20,0 % [3,6–62,4] (1/5) |
| Sin respuesta | 100,0 % [51,0–100,0] (4/4) |
| **Global** | **40,0 % [21,9–61,3] (8/20)** |

Costo medio por tarea: US$0,0181 [0,0173–0,0189]; latencia p50 183 s [165–194]. La recolección fue completa: las
33 ofertas válidas de las tareas llegaron al cuadro comparativo (100,0 % [89,6–100,0]). El emparejamiento por
nombre con Falabella, que no publica GTIN, asignó al producto correcto las seis fichas equivalentes y dejó sin
emparejar los ocho distractores; la ficha R25, entonces sin confirmar, también quedó sin emparejar.

La caída frente al corpus B (90,0 %) tiene una causa única: la **disponibilidad**. La exactitud de ese campo fue de
43 % (29/68), y en las fichas de Alkosto el extractor marcó «en existencia» 8 de 37 veces. Las tiendas reales
publican la disponibilidad en los datos estructurados de schema.org (microdatos o JSON-LD), no en el texto
visible; la ficha original de Alkosto tampoco la muestra en texto. La lectura web del agente convierte la página a
Markdown y esa conversión descarta los datos estructurados, de modo que la oferta queda con disponibilidad
desconocida y la selección la descarta por la restricción dura del perfil. Los cuatro aciertos con oferta son los
casos en que el extractor infirió la existencia a partir del botón de compra; los cuatro aciertos sin respuesta
no dependen de ese dato. En particular, en la tarea con todo agotado y un producto parecido en existencia en
Falabella, el agente no confundió los productos.

El corpus sintético no reveló esta limitación porque su tienda con JSON-LD también mostraba la disponibilidad en
texto. La corrección (D74) incorpora a la lectura web los datos schema.org de la página como texto del plano de
datos; esta corrida queda como línea base del corpus A.

## 4.y Lectura con datos schema.org (D74)

La lectura web del agente antepone ahora al Markdown de la página los objetos schema.org `Product` y `Offer` que
publica (JSON-LD y microdatos, extraídos con `extruct`), como texto del plano de datos. Con el resto de la
configuración igual, la corrida sobre las mismas 20 tareas (`resultados/corridas/2026-11-09_corpus_a_flash_v1`)
dio:

| Categoría | Línea base (v0) | Con datos schema.org (v1) |
|---|---|---|
| Producto específico | 16,7 % [3,0–56,4] (1/6) | 83,3 % [43,6–97,0] (5/6) |
| Menor precio | 40,0 % [11,8–76,9] (2/5) | 100,0 % [56,6–100,0] (5/5) |
| Restricciones | 20,0 % [3,6–62,4] (1/5) | 100,0 % [56,6–100,0] (5/5) |
| Sin respuesta | 100,0 % [51,0–100,0] (4/4) | 100,0 % [51,0–100,0] (4/4) |
| **Global** | **40,0 % [21,9–61,3] (8/20)** | **95,0 % [76,4–99,1] (19/20)** |

La exactitud de la disponibilidad pasó de 43 % (29/68) a 96 % (72/75), y la recolección siguió completa (33/33).
El costo por tarea no cambió (US$0,0180 [0,0173–0,0189]); la latencia p50 fue de 169 s [153–180]. Los intervalos
de ambas corridas no se solapan, de modo que la mejora no se explica por la variación entre ejecuciones.

El único fallo (A003) es de planificación y ya estaba en la línea base: el agente leyó el listado de Falabella,
que no publica la disponibilidad, y no abrió la ficha del monitor, que sí la publica; sin ese dato, la única oferta
en existencia se descartó y el agente se abstuvo.

Un efecto secundario muestra la sensibilidad del extractor a las etiquetas. En Alkosto y Ktronix el código
visible de la ficha es el EAN, y schema.org lo publica como `sku`. Con la lectura en Markdown, el extractor tomaba
ese código como GTIN en 35 de 62 ofertas de ficha (16 coincidían con la verdad); con el objeto schema.org a la
vista, lo hizo en 1 de 67, en cumplimiento de su instrucción de copiar el GTIN solo cuando aparece como tal. El emparejamiento no se resintió,
porque los productos se reconocieron por nombre con los embeddings, pero la verificación determinista de N3 (S08)
no debe suponer que el GTIN llega siempre en la oferta extraída.
