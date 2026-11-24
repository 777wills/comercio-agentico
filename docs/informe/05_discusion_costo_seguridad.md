# 5.x Costo de la capa de seguridad

La Tabla V reúne el costo de las defensas en cada dimensión medida. En dinero y en utilidad, el costo es despreciable: el clasificador y el control de precio no llaman a ningún modelo, y la separación de planos reutiliza la extracción que el agente ya hacía. El costo real está en otras dimensiones: la memoria del modelo local, que condiciona la plataforma de despliegue; las falsas alarmas en páginas reales, que exigieron un saneamiento específico; y el esfuerzo de construir y mantener la suite de evaluación, sin la cual el aporte de cada capa no podría demostrarse.

**TABLA V. Costo de las defensas por dimensión**

| Dimensión | Costo medido | Evidencia |
| --- | --- | --- |
| Dinero por consulta | Menos de US$0,0005 por tarea entre C0 y C3; N3 suma US$0,008 | E2 y E1 |
| Latencia | Unos 0,2 s por ventana del clasificador en CPU; N3, de 4 a 5 s en paralelo; mediana por tarea de 128 a 144 s frente a 135 s | E2, E1 y elección del clasificador |
| Utilidad | Sin pérdida medible: 93,3–96,7 % frente a 93,3 % sin defensa | E2 |
| Falsas alarmas | 0/47 en el corpus; en páginas reales, 19,8 % de ventanas sin saneamiento y 0,4 % con él | Elección del clasificador y medición en páginas reales |
| Memoria e infraestructura | Los dos modelos locales ocupan cerca de 1,1 GB, incluidos en la imagen del contenedor | Operación en producción |
| Privacidad | Ninguna: el clasificador corre en el servidor y no envía el contenido a terceros | Comparación con un detector por API |
| Evaluación y mantenimiento | 20 cargas con predicados, arnés de ataques y pruebas automatizadas; la matriz de E2 costó US$5,35 y su réplica con Haiku, US$1,97 | E2 |

El resultado con Haiku matiza la lectura: un modelo más robusto resistió la suite sin defensas. Aun así, conservar las capas es la decisión prudente, porque su costo es mínimo y la robustez propia de un modelo no es una propiedad que el sistema controle ni que se mantenga entre versiones.
