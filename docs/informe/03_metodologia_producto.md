# 3.x Del prototipo al producto: la API de CotIA

CotIA expone el agente como un servicio web sin modificar su lógica de decisión. La API se construyó con FastAPI y
corre en el mismo proceso que el agente (D81). Así, el contrato OpenAPI se genera desde los mismos modelos Pydantic
que el agente ya usa para su salida estructurada, y no hace falta una capa de traducción ni un intermediario de
colas.

## Progreso en vivo por eventos del servidor

Una consulta tarda del orden de dos minutos, porque el planificador abre varias fuentes y cada fuente pasa por el
extractor. Para que esa espera sea observable, el grafo de LangGraph se ejecuta en modo de *streaming*
(`astream`, modos `updates` y `values`): cada nodo (interpretar, planificar, herramientas, emparejar, proponer)
entrega su actualización del estado en cuanto termina. Un traductor reduce cada actualización a un evento compacto:
la necesidad formalizada, las herramientas que pidió el planificador, las fuentes leídas con su número de ofertas y
las alertas de defensa, el emparejamiento con el catálogo y la propuesta. Los eventos llegan al navegador por
*Server-Sent Events* (SSE), un canal HTTP unidireccional que no requiere WebSocket ni infraestructura adicional.
Cuando el agente pasa más de 15 s sin emitir eventos, el servidor envía un latido para que los intermediarios no
cierren la conexión. Al terminar, la secuencia de eventos se guarda junto con la consulta y puede repetirse desde
la base.

## Persistencia

Las consultas, sus opciones, la propuesta completa (con la procedencia de cada dato: fuente, URL, fecha, fragmento
y SHA-256) y los eventos se guardan en PostgreSQL mediante SQLAlchemy 2. Las pruebas usan SQLite en memoria con el
mismo código, de modo que el contrato de la API se verifica sin red y sin costo. El historial y el gasto acumulado se
agrupan por un identificador anónimo que genera el navegador (D90).

## Llave propia del visitante

El producto no gasta créditos del proyecto (D82). La clave de OpenRouter del visitante llega en una cabecera en cada
consulta y se pasa al cliente de OpenRouter solo para esa consulta. No se escribe en variables de entorno, no se
guarda en la base y se elimina de cualquier mensaje de error antes de registrarlo. La segunda lectura de N3 usa
Claude Haiku 5.5 por OpenRouter con la misma clave (D105). Así conserva el diseño de E1, con un lector de otra familia
distinta de la del extractor por defecto. Una prueba automatizada provoca un error del proveedor que repite la clave
y comprueba que la clave no aparece en la base, en las respuestas, en los eventos ni en los registros.

## Defensas como capas independientes

Las defensas se exponen como tres interruptores independientes (separación de planos, clasificador de inyección y
verificación de precio) más el umbral del clasificador (D91). C0–C3 son atajos que fijan las combinaciones medidas en
E2, y CotIA usa C2 por defecto (D106), el codo de la curva seguridad-utilidad. Cualquier otra combinación, o un
umbral distinto de 0,5 con el clasificador activo, se marca como exploratoria porque no tiene cifras propias. El
clasificador se carga una sola vez y lo comparten todas las consultas; el umbral se aplica por consulta.

## Laboratorio de ataques

Una consulta puede apuntar a una de las 20 variantes del corpus B con una carga plantada (S06-bis). La API planta la
carga en su copia aislada, la sirve en un puerto local, ejecuta la tarea asociada a la carga con las defensas elegidas
y evalúa el predicado de éxito del ataque con el mismo código de E2, sin juicio humano. En la prueba de punta a punta,
la carga A20 (precio falso en el chat) tuvo éxito en C0, como en las tres repeticiones de E2.

## Lista curada de modelos

Solo se ofrecen modelos que superan una prueba de humo del agente completo (D107). Con la tarea B013 del corpus B
en C2, se comprueba que el modelo **funciona**: termina sin errores, recolecta ofertas, formaliza la necesidad y
responde en menos de 10 minutos. Además, el modelo debe tener **desempeño con evidencia**: haber acertado esa tarea
o tener M2 medido en E3. Una sola tarea mide mal el acierto: Claude Haiku 5.5, con M2 de 90,0 % en E3, eligió mal
en B013. Por eso el desempeño se toma de E3 cuando existe, y un modelo sin E3 debe acertar. La evidencia está en
`resultados/cotia/modelos.json`.

| Modelo (OpenRouter) | Funciona | Acierto en B013 | M2 en E3 | US$ | Segundos | En la lista |
|---|---|---|---|---:|---:|---|
| DeepSeek V4.1 Flash | sí | sí | 88,9 % | 0,0146 | 82 | sí |
| Claude Haiku 5.5 | sí | no | 90,0 % | 0,0159 | 53 | sí |
| Kimi K3.1 Pro | sí | sí | — | 0,1841 | 109 | sí |
| DeepSeek V4 Pro | sí | no | — | 0,1298 | 265 | no |
| NVIDIA Nemotron 3.5 Super VL (gratuito) | sí | no | — | 0 | 113 | no |
| Dots3-Note Preview (gratuito) | sí | no | — | 0 | 236 | no |
| LiquidAI LFM2.5 2.6B (gratuito) | sí | no | — | 0 | 303 | no |
| LiquidAI LFM3 1.7B (gratuito) | no: límite de tasa, no terminó en 10 min | — | — | 0 | — | no |
| XingChen Xing4.0 29B (gratuito) | no: retirado de OpenRouter | — | — | 0 | — | no |

Ningún modelo gratuito superó la prueba. Los tres que funcionaron eligieron mal en la tarea, y los gratuitos están
sujetos a límites de tasa que hacen impredecible la latencia. La prueba costó US$0,3443 en total.

## Límites de operación

Cada consulta ocupa del orden de 2 GB de memoria (clasificador, modelo de *embeddings* y navegador sin interfaz).
Por eso la API ejecuta una consulta a la vez y deja en cola hasta cinco más; por encima de ese límite responde con
HTTP 429. Los dos valores son configurables según la memoria del despliegue (S09c).
