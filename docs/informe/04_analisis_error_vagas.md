# 4.x Análisis de error: las tareas vagas

En E3, los dos modelos fallaron casi únicamente en las tareas vagas (Flash 11/18 y Haiku 12/18 aciertos; en las demás
categorías, 69/72 y 69/72). El análisis compara, en cada ejecución fallida, las restricciones que el intérprete
infirió con los criterios que fija la verdad de la tarea. Fuente: `resultados/corridas/2026-11-10_e3_flash.jsonl.gz`
y `resultados/corridas/2026-11-09_e3_haiku.jsonl.gz`; el cálculo no requiere nuevas llamadas al modelo.

**Tabla 4.x.1.** Fallos en tareas vagas de E3 por tarea, modelo y mecanismo (tres repeticiones por tarea).

| Tarea | Consulta (resumen) | Criterio de la verdad | Inferencia del modelo | Flash | Haiku | Mecanismo |
| --- | --- | --- | --- | ---: | ---: | --- |
| B035 | «Guardar todas las fotos de la familia, con mucho espacio» | almacenamiento ≥ 2.048 GB | almacenamiento ≥ 1.000 GB | 3/3 | 3/3 | Subinferencia: elige un disco válido para su cifra, pero menor que el de la verdad |
| B029 | «Pantalla grande con muy buena resolución para diseño gráfico» | 4K y ≥ 27 pulgadas | solo ≥ 27 pulgadas | 3/3 | 0/3 | Subinferencia: omite la resolución |
| B025 | «Portátil liviano para cargarlo todo el día» | peso ≤ 1,6 kg | peso ≤ 1,6 kg y autonomía ≥ 8 h | 0/3 | 3/3 | Sobreinferencia: añade una restricción y se abstiene |
| B031 | «Celular al que le dure mucho la batería» | batería ≥ 5.000 mAh | autonomía ≥ 24 h | 1/3 | 0/3 | Sobreinferencia: atributo equivocado y abstención |

Los fallos son **sistemáticos**: doce de los trece pertenecen a combinaciones de tarea y modelo que fallan en las
tres ejecuciones. No proceden de la
variabilidad del muestreo sino de una traducción estable, y distinta en cada modelo, de la misma expresión vaga.
Coinciden con los perfiles de error medidos en E3: Haiku tiende a añadir restricciones y abstenerse (abstención
indebida de 7,7 %), mientras que Flash tiende a quedarse corto y responder (exactitud sobre lo cubierto de 89,5 %).

Dos lecturas se desprenden del análisis. La primera es metodológica: en las tareas vagas, la verdad fija una
convención («mucho espacio» = 2 TB) que no es la única traducción razonable, de modo que parte de lo que M2 cuenta
como error es una discrepancia de convención y no un fallo del agente. Por eso el informe reporta las tareas vagas
por separado. La segunda es de diseño: el sistema trata igual una restricción que el comprador escribió y una que
el modelo infirió. Marcar las inferidas como blandas, relajarlas cuando ninguna oferta cumple e informar al
comprador del ajuste («no hay portátiles con 8 h de batería; el más barato de menos de 1,6 kg es…») eliminaría las
abstenciones por sobreinferencia sin tocar la regla de decisión. Queda como mejora propuesta en la hoja de ruta,
porque cambiaría el agente medido en E1–E3.
