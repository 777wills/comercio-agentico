# 5.x Elección del modelo como decisión de negocio

El modelo de lenguaje es el componente de mayor costo variable del agente y el que fija su latencia. Elegirlo es una
decisión de negocio: el comprador paga cada cotización con su propia clave (D82) y espera la respuesta en línea.
Esta sección ordena el espacio de alternativas de D31 frente a los criterios del negocio. Muestra por qué la regla de
parada de E3 justifica no medir los modelos caros y qué cambiaría la elección.

## Criterios

| Criterio | Qué mide | Fuente de la evidencia |
| --- | --- | --- |
| Costo por cotización | US$ por tarea con los cuatro roles del agente | M6 de E3 (medido); estimado para los no medidos |
| Latencia | Tiempo hasta la propuesta, que el comprador espera en línea | M6 de E3, mediana |
| Éxito y perfil de error | M2, abstención indebida y exactitud sobre lo cubierto: abstenerse frente a equivocarse | M2 y M4 de E3 |
| Estabilidad | Misma decisión en tres repeticiones | M3 de E3 |
| Robustez sin defensas | Éxito de la inyección en C0 | M5 de E2 |
| Soberanía de los datos | Posibilidad de ejecutar el modelo en infraestructura propia | Licencia de los pesos (D31) |

## Matriz

**Tabla 5.x.1.** Alternativas de D31 frente a los criterios del negocio. Precios en US$ por millón de tokens
(entrada / salida). Los de OpenRouter corresponden al endpoint fijado en D34 y los de Anthropic, al catálogo de
OpenRouter. Todos se consultaron en la API pública de OpenRouter el 14-nov-2026 y coinciden con los registrados el
9-nov-2026.

| Modelo | Nivel | Pesos | Precio | Costo por cotización | Latencia p50 | M2 (E3) | Abstención indebida / exactitud cubierta | M3 | M5 en C0 (E2) |
| --- | --- | --- | --: | --: | --: | --: | --- | --: | --: |
| DeepSeek V4.1 Flash | Económico | Abiertos | 0,14 / 0,42 | **US$0,0152** (medido) | 129 s | 88,9 % | 2,6 % / 89,5 % | 86,7 % | 11,7 % (7/60) |
| Claude Haiku 5.5 | Económico | Cerrados | 0,10 / 0,50 | **US$0,0170** (medido) | **56 s** | 90,0 % | 7,7 % / **95,8 %** | **93,3 %** | **0,0 %** (0/60) |
| DeepSeek V4 Pro | Medio | Abiertos | 1,30 / 2,60 | ≈ US$0,13–0,14 (B013: US$0,130) | 265 s (B013) | — | — | — | — |
| Kimi K3.1 Pro | Tope | Abiertos | 1,90 / 9,50 | ≈ US$0,32–0,37 (B013: US$0,184) | 109 s (B013) | — | — | — | — |
| Claude Sonnet 5.5 | Medio | Cerrados | 2,00 / 10,00 | ≈ US$0,34–0,39 | No medida | — | — | — | — |
| Claude Opus 5.5 | Tope | Cerrados | 4,00 / 20,00 | ≈ US$0,68–0,79 | No medida | — | — | — | — |

El costo de los modelos no medidos se estimó con los dos perfiles de tokens observados en E3: 39 303 de entrada y
31 224 de salida por tarea (Flash), y 66 738 y 20 606 (Haiku). Es una cota indicativa. Un modelo que razone más
generaría más tokens de salida y costaría más. Con esos perfiles, el modelo medio más barato multiplica por nueve el
costo por cotización del modelo base, y el más caro, por cincuenta. La prueba de humo de la lista curada de CotIA
(D107) aporta un dato por modelo en la tarea B013, sin valor estadístico. DeepSeek V4 Pro costó US$0,130, tardó 265 s
y falló la tarea. Kimi K3.1 Pro costó US$0,184, tardó 109 s y acertó, frente a US$0,0146 y 82 s de Flash en la
misma tarea (`resultados/cotia/modelos.json`).

## Lectura

**Por qué no se midieron los modelos caros.** La regla de parada de E3, fijada antes de la primera corrida, solo
sube de modelo si el último supera al mejor medido por más que el ruido entre repeticiones. Haiku superó a Flash en
1,1 puntos de M2, frente a un ruido de 10,0 puntos. Medir el nivel medio habría costado del orden de nueve veces
más por tarea para buscar una mejora que los dos modelos económicos ya dejaban sin margen visible. Las categorías de
producto específico, restricciones y sin respuesta están en el techo (18/18, 23–24/24 y 12/12). El margen que queda
está en las consultas vagas (11–12/18), cuyos fallos el análisis de error atribuye a la interpretación de la
consulta y no a la capacidad de extraer o comparar. La regla no evalúa ventajas que M2 y M4 no capturan, como la
latencia, y así se declara en las limitaciones de E3.

**Por qué Flash es el modelo base.** Con éxito equivalente dentro del ruido, Flash tiene el menor costo por
cotización y es el único de los dos medidos con pesos abiertos. Para una herramienta en la que el comprador paga
cada consulta, el costo marginal es el criterio que más pesa. Los pesos abiertos dejan además una vía de
autohospedaje hacia la soberanía de los datos, en la que la consulta del comprador no sale de la empresa. El precio
de esta elección es la latencia (más del doble que Haiku), una estabilidad algo menor y mayor exposición a la
inyección sin defensas. Las defensas cubren esa exposición: en C3, M5 fue 0/60 con Flash.

**Qué cambiaría la elección.**

| Si el negocio prioriza… | Elección | Razón |
| --- | --- | --- |
| Costo por cotización y soberanía de los datos | DeepSeek V4.1 Flash | Menor costo medido; pesos abiertos, ejecutable en infraestructura propia |
| Latencia percibida por el comprador | Claude Haiku 5.5 | 56 s frente a 129 s, por un 12 % más de costo |
| No recomendar nunca algo equivocado | Claude Haiku 5.5 | Mayor exactitud sobre lo cubierto (95,8 %): prefiere abstenerse a equivocarse |
| Resolver consultas vagas | Sin elección medida | Ningún modelo medido supera el 67 %; un modelo medio es la prueba pendiente (≈ US$0,6 en las 6 tareas vagas × 3) |

**En CotIA**, la elección queda en manos del comprador, porque paga con su clave. La lista curada (D107) incluye los
modelos que superaron la prueba de humo: Flash como opción por defecto, Haiku y Kimi K3.1 Pro. Haiku también se
puede usar con una clave de Anthropic (D105, D114). Cada consulta muestra su costo, así que el comprador ve en su
propia cuenta el compromiso entre costo y latencia.
