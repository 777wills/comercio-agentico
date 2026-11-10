# 4. Resultados — E3: comparación de modelos con escalamiento

## 4.x Diseño

E3 compara los modelos de lenguaje con la configuración base fija: separación de planos (C1), sin defensas
adicionales ni verificación N3, y la versión v3 del agente (prompt `9e49060f5a9e`). Solo cambia el modelo, que
desempeña los cuatro roles del agente (intérprete, planificador, extractor y confirmador del emparejamiento). Cada
modelo resuelve el subconjunto de 30 tareas del corpus B (6 de producto específico, 6 de menor precio, 8 con
restricciones, 6 vagas y 4 sin respuesta), congelado al azar antes de ver resultado alguno, tres veces.

Los modelos se escalan del más barato al más caro (DeepSeek V4.1 Flash → Claude Haiku 5.5 → DeepSeek V4 Pro →
Kimi K3.1 Pro ≈ Claude Sonnet 5.5 → Claude Opus 5.5), con una regla de parada fijada antes de la primera corrida:
el ruido es el mayor rango de M2 entre las tres repeticiones de los dos modelos comparados, y solo se sube al
siguiente modelo si el último supera al mejor ya medido, en la media de M2 o en la tasa de abstención correcta,
por más que ese ruido. La regla protege el presupuesto con un umbral derivado de los propios datos.

## 4.y Resultados

| Métrica | DeepSeek V4.1 Flash | Claude Haiku 5.5 |
|---|---|---|
| M2 global (90 ejecuciones) | 88,9 % [80,7–93,9] (80/90) | 90,0 % [82,1–94,6] (81/90) |
| M2 por repetición | 83,3 % · 90,0 % · 93,3 % | 90,0 % · 93,3 % · 86,7 % |
| Rango de M2 entre repeticiones | 10,0 pp | 6,7 pp |
| Producto específico | 18/18 | 18/18 |
| Menor precio | 16/18 | 15/18 |
| Restricciones | 23/24 | 24/24 |
| Vaga | 11/18 | 12/18 |
| Sin respuesta | 12/12 | 12/12 |
| M3 misma decisión en las tres repeticiones | 86,7 % [70,3–94,7] (26/30) | 93,3 % [78,7–98,2] (28/30) |
| M4 abstención correcta | 100,0 % [75,8–100,0] (12/12) | 100,0 % [75,8–100,0] (12/12) |
| M4 abstención indebida | 2,6 % [0,7–8,9] (2/78) | 7,7 % [3,6–15,8] (6/78) |
| M4 exactitud sobre lo cubierto | 89,5 % [80,6–94,6] (68/76) | 95,8 % [88,5–98,6] (69/72) |
| M6 costo medio por tarea | US$0,0152 [0,0149–0,0156] | US$0,0170 [0,0166–0,0173] |
| M6 latencia p50 | 129 s [123–136] | 56 s [54–58] |
| Tokens por tarea (entrada / salida) | 39 303 / 31 224 | 66 738 / 20 606 |
| Procedencia completa | 90/90 | 90/90 |

Figura: `resultados/informes/e3/frontera.png` (costo por tarea en escala logarítmica frente a M2, con intervalos
de Wilson al 95 %).

**Aplicación de la regla.** Haiku supera a Flash en 1,1 pp de M2 medio y empata en abstención correcta; el ruido
entre repeticiones es de 10,0 pp. La mejora no supera el ruido, de modo que el escalamiento se detiene en el
segundo paso y los cuatro modelos restantes no se corren. Los dos modelos medidos están en la frontera de Pareto:
ninguno domina al otro, porque Flash es más barato y Haiku obtiene un M2 apenas mayor.

**Perfiles de error distintos con igual éxito.** Con un M2 equivalente, los dos modelos fallan de manera
diferente. Flash responde casi siempre (abstención indebida de 2,6 %) y se equivoca más en lo que responde
(exactitud cubierta de 89,5 %); Haiku se abstiene con más facilidad (7,7 %) y acierta más cuando responde
(95,8 %). Haiku es además 2,3 veces más rápido y más estable entre repeticiones, a cambio de leer más tokens de
entrada y generar menos de salida, por un costo 12 % mayor. En ambos, los fallos se concentran en las tareas
vagas (61–67 %), donde la traducción de la consulta a una cifra es discutible, y no en las tareas que exigen
extraer, comparar o abstenerse.

## 4.z Elección del modelo base

El modelo base del resto de los experimentos y de la demostración es DeepSeek V4.1 Flash. Con desempeño
equivalente dentro del ruido, es el de menor costo por tarea y el único de los dos con pesos abiertos, lo que deja
abierta la ejecución local como evolución hacia la soberanía de los datos del comprador. Sus limitaciones medidas
son la latencia (129 s por tarea frente a 56 s) y un acuerdo entre repeticiones menor (86,7 % frente a 93,3 %).
Los modelos de nivel medio y tope quedan como trabajo propuesto: su evaluación tendría sentido con tareas en las
que los modelos económicos no alcancen el techo, como las vagas o las adversariales de E2.

**Limitaciones.** El subconjunto de 30 tareas y tres repeticiones da intervalos de unos ±6 pp en M2 global; una
diferencia real menor que el ruido observado no se detecta. La regla de parada compara con el mejor modelo ya
medido, de modo que un modelo más caro con ventajas que M2 y M4 no capturan (por ejemplo, la latencia) no se
evalúa.
