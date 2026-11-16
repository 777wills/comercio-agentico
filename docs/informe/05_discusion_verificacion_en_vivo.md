# 5.x La verificación frente a las tiendas en vivo: falsos positivos y consultas incompletas

La verificación por una segunda ruta de extracción (N3) se diseñó y midió sobre corpus controlados (E1). Su
operación sobre tiendas en vivo expuso un modo de falla que E1 no cubría: la discrepancia por un campo que una de
las dos rutas desconoce. Esta sección describe el caso, su corrección y el límite de la evidencia.

## El caso

La consulta «Celular de por lo menos gb de ram» terminó en abstención. De 45 ofertas que cumplían la necesidad,
7 quedaron verificadas, 36 en discrepancia y 2 sin contraparte. Concurrieron dos causas independientes.

| Causa | Efecto | Evidencia |
| --- | --- | --- |
| La consulta anuncia una especificación sin su cifra y el intérprete la descarta sin advertirlo | La oferta de menor costo es un equipo de 2 GB de RAM, contrario a la intención | Necesidad interpretada sin restricciones |
| La primera extracción deja la disponibilidad como desconocida en los listados; la segunda la infiere de la opción de compra | Toda oferta de un listado queda en discrepancia aunque el precio coincida | Segunda lectura de una ficha con siete ofertas: seis discrepancias, todas solo en disponibilidad |

Una simulación sobre las mismas ofertas con la consulta completa («por lo menos 6 GB») también terminaba en
abstención: las seis ofertas que cumplían provenían de un listado y estaban en discrepancia. La ambigüedad
explicaba qué oferta se eligió; la abstención la explicaba N3.

## Corrección

| Cambio | Regla |
| --- | --- |
| Comparación de la disponibilidad | Solo cuenta como discrepancia si ambas rutas la conocen y difieren. Desconocer un dato no contradice al otro. Precio, envío, plazo y GTIN conservan la comparación estricta |
| Campos de la discrepancia | Cada oferta registra los campos que no coincidieron; el informe de cotización los muestra |
| Dato faltante | El intérprete identifica una especificación anunciada sin cifra; el agente se abstiene antes de consultar proveedores y pide el dato. Una necesidad sin cifra («liviano») se sigue traduciendo a un valor razonable |
| Alternativa verificada | Si la ganadora no queda verificada, la propuesta nombra la mejor oferta verificada que cumple, sin recomendarla; la política de abstención no cambia |

## Resultado

| Consulta | Antes | Después |
| --- | --- | --- |
| «…de por lo menos gb de ram» | Abstención tras recorrer las tiendas: US$0,0617 y 344 s | Abstención que pide la cantidad de GB, sin consultar proveedores: US$0,00026 y 16 s |
| «…de por lo menos 6 GB de RAM» | Abstención (simulada) | Recomendación de un equipo de 8 GB a $834.900, con 7 de 7 ofertas verificadas: US$0,0601 y 372 s |

## Alcance y límites

E1, E2 y E3 se midieron con la versión anterior de N3 y del intérprete; sus cifras no incorporan esta corrección,
y la huella de las instrucciones distingue ambas versiones. La corrección reduce la cobertura perdida por falsos
positivos, pero no cambia el principio de predicción selectiva: una discrepancia de precio, envío o plazo sigue
impidiendo la recomendación. El caso se observó en una sola consulta con verificación en vivo y no constituye una
medición; cuantificar la tasa de falsos positivos de N3 en tiendas reales queda en la hoja de ruta.
