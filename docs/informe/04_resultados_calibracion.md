# 4. Resultados — Corrida de calibración

## 4.x Calibración del agente con el modelo económico

La corrida de calibración ejecuta las 60 tareas del corpus B una vez con DeepSeek V4.1 Flash, en la condición
C1 (separación de planos), con un tope de US$0,10 por tarea. Tiene tres propósitos: verificar el arnés de punta a
punta con un modelo real, fijar los costos y tiempos de referencia para E3 y detectar defectos del agente antes de
comparar modelos. Se hicieron dos corridas sobre el mismo corpus (huella `761e13ff945f`) y las mismas tareas. La
segunda (v1) corrige el esquema de salida del extractor: todos sus campos pasan a ser obligatorios y anulables.
También acota a los mensajes la regla que atribuye existencias a un producto ofrecido sin aviso.

**Tabla X.** Calibración con DeepSeek V4.1 Flash, C1, 60 tareas × 1 repetición. Proporciones con IC 95 % de
Wilson; costo y latencia con IC 95 % *bootstrap*.

| Métrica | v0 (esquema con campos opcionales) | v1 (campos obligatorios) |
|---|---|---|
| M2 éxito global | 86,7 % [75,8–93,1] (52/60) | 81,7 % [70,1–89,4] (49/60) |
| M2 específica / más barato | 12/12 · 12/12 | 12/12 · 11/12 |
| M2 restricciones / vaga | 12/15 · 7/12 | 13/15 · 5/12 |
| M2 sin respuesta | 9/9 | 8/9 |
| M1 exactitud de extracción (campos) | 86,3 % [85,6–86,8] | 95,7 % [95,4–96,1] |
| M1 GTIN / MPN / marca en P1 (MCP) | 0 % · 0 % · 0 % | 99 % · 100 % · 100 % |
| Recolección de ofertas válidas | 99,2 % (259/261) | 99,2 % (259/261) |
| M4 abstención correcta / indebida | 9/9 · 0/51 | 8/9 · 1/51 |
| M6 costo por tarea (media) | US$0,0135 [0,0130–0,0139] | US$0,0148 [0,0143–0,0152] |
| M6 latencia p50 / p90 | 146 s / 209 s | 179 s / 255 s |
| Costo total de la corrida | US$0,81 | US$0,89 |

**Extracción.** Con el esquema de campos opcionales, el extractor omitió GTIN, número de parte y marca en el
100 % de las ofertas, incluso en el proveedor MCP, que los publica como campos JSON. La razón es que el
proveedor de inferencia no impone el esquema al generar: el modelo omite lo que no es obligatorio. Al declarar
todos los campos como obligatorios, la exactitud de extracción subió de 86,3 % a 95,7 %, y los identificadores
de P1 pasaron de 0 % a 99–100 %. Los errores que quedan se concentran en dos puntos:

- **Condiciones generales del mensaje informal (P5):** envío 86 %, plazo 77 %.
- **Índice del catálogo de P2:** el modelo toma el código de modelo que aparece en el título como número de parte
  del fabricante.

En todas las fuentes, el precio se extrajo sin error en las 3667 ofertas de v1 con correspondencia en la verdad.

**Éxito de la tarea.** La diferencia de M2 entre v0 y v1 (52 frente a 49 aciertos) está dentro del ruido: los
intervalos se solapan casi por completo, y con una sola repetición no se puede separar de la variación entre
ejecuciones. El análisis de los fallos muestra una causa común que no depende del extractor: el intérprete
devolvió la necesidad sin restricciones ni presupuesto en 14 de las 27 tareas con criterios en v0 y en 19 en v1.
Esas tareas concentran 6 y 10 fallos, respectivamente. Es el mismo fenómeno de omisión, ahora en el esquema de la
necesidad. En una prueba con cuatro consultas, el esquema de campos obligatorios recuperó las restricciones en
tres. La cuarta devolvió un JSON truncado, lo que confirma que el esquema orienta al modelo pero no restringe la
decodificación. Las tareas vagas son las más afectadas (5/12 en v1), porque dependen de que el intérprete
convierta expresiones como «bien rápido» o «mucho espacio» en restricciones sobre atributos.

**Costo y tiempo.** Una tarea cuesta US$0,015 de media con el modelo económico y tarda unos 3 minutos de
extremo a extremo. Con cuatro tareas en paralelo, la corrida de 60 tareas toma unos 45 minutos. Escribir todos
los campos aumenta los tokens de salida en un 12 % (de 26 731 a 30 009 por tarea). Con estos valores, la
estimación de E3 sobre el subconjunto de 30 tareas se mantiene en el orden de US$0,45 por corrida con
DeepSeek Flash.

**Subconjunto de E3.** Antes de ver los resultados de la calibración se congelaron 30 tareas, la mitad de cada
categoría (6, 6, 8, 6 y 4), elegidas al azar con semilla fija.
