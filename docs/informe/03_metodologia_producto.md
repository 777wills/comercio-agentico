# 3.x Del prototipo al producto: la API de CotIA

CotIA expone el agente como un servicio web sin modificar su lógica de decisión. La API se construyó con FastAPI y
corre en el mismo proceso que el agente (D81). Así, el contrato OpenAPI se genera desde los mismos modelos Pydantic
que el agente ya usa para su salida estructurada, y no hace falta una capa de traducción ni un intermediario de
colas.

## Progreso en vivo por eventos del servidor

Una consulta tarda del orden de dos minutos, porque el planificador abre varias fuentes y cada fuente pasa por el
extractor. Para que esa espera sea observable, el grafo de LangGraph se ejecuta en modo de _streaming_
(`astream`, modos `updates` y `values`): cada nodo (interpretar, planificar, herramientas, emparejar, proponer)
entrega su actualización del estado en cuanto termina. Un traductor reduce cada actualización a un evento compacto:
la necesidad formalizada, las herramientas que pidió el planificador, las fuentes leídas con su número de ofertas y
las alertas de defensa, el emparejamiento con el catálogo y la propuesta. Los eventos llegan al navegador por
_Server-Sent Events_ (SSE), un canal HTTP unidireccional que no requiere WebSocket ni infraestructura adicional.
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

| Modelo (OpenRouter)                     | Funciona                                 | Acierto en B013 | M2 en E3 |    US$ | Segundos | En la lista |
| --------------------------------------- | ---------------------------------------- | --------------- | -------- | -----: | -------: | ----------- |
| DeepSeek V4.1 Flash                     | sí                                       | sí              | 88,9 %   | 0,0146 |       82 | sí          |
| Claude Haiku 5.5                        | sí                                       | no              | 90,0 %   | 0,0159 |       53 | sí          |
| Kimi K3.1 Pro                           | sí                                       | sí              | —        | 0,1841 |      109 | sí          |
| DeepSeek V4 Pro                         | sí                                       | no              | —        | 0,1298 |      265 | no          |
| NVIDIA Nemotron 3.5 Super VL (gratuito) | sí                                       | no              | —        |      0 |      113 | no          |
| Dots3-Note Preview (gratuito)           | sí                                       | no              | —        |      0 |      236 | no          |
| LiquidAI LFM2.5 2.6B (gratuito)         | sí                                       | no              | —        |      0 |      303 | no          |
| LiquidAI LFM3 1.7B (gratuito)           | no: límite de tasa, no terminó en 10 min | —               | —        |      0 |        — | no          |
| XingChen Xing4.0 29B (gratuito)         | no: retirado de OpenRouter               | —               | —        |      0 |        — | no          |

Ningún modelo gratuito superó la prueba. Los tres que funcionaron eligieron mal en la tarea, y los gratuitos están
sujetos a límites de tasa que hacen impredecible la latencia. La prueba costó US$0,3443 en total.

## Límites de operación

Cada consulta ocupa del orden de 2 GB de memoria (clasificador, modelo de _embeddings_ y navegador sin interfaz).
Por eso la API ejecuta una consulta a la vez y deja en cola hasta cinco más; por encima de ese límite responde con
HTTP 429. Los dos valores son configurables según la memoria del despliegue (S09c).

## Interfaz

La interfaz es una aplicación de página única construida con SvelteKit, compilada a archivos estáticos y servida por
la misma API, de modo que el producto sigue siendo un solo proceso y un solo contenedor (D81). Usa Tailwind CSS y
componentes de shadcn-svelte sobre bits-ui, en modo oscuro (D109). Sin clave se puede recorrer todo el producto; solo
la ejecución de consultas la exige.

- **Consulta.** El visitante escribe una necesidad en lenguaje natural o parte de un ejemplo por tipo de tarea, sobre
  el corpus B (proveedores sintéticos) o el corpus A (tiendas reconstruidas). Mientras el agente trabaja, una línea de
  tiempo muestra cada evento SSE: la necesidad formalizada, las herramientas que pide el planificador, las ofertas
  extraídas por proveedor y las alertas de defensa. La propuesta final presenta el cuadro comparativo (precio, envío,
  costo total, plazo y disponibilidad), la recomendación o la abstención con su justificación, las alertas, el costo y
  el tiempo. Cada oferta despliega su procedencia: fuente, consulta que la produjo, ruta de extracción y modelo, fecha,
  SHA-256 y el fragmento original. Con la verificación activa, cada oferta muestra su estado N3 y la política
  (abstenerse o excluir) se elige en la configuración (D110).
- **Laboratorio de ataques.** El visitante elige una de las 20 cargas, ve su clase, ubicación, objetivo y texto, y
  ejecuta la misma tarea en C0 y en C3 con su modelo. Cada lado muestra su progreso y su propuesta, junto con el
  veredicto del predicado de éxito del ataque. Las cifras de M5 de E2 acompañan la comparación como referencia.
- **Corpus.** Un visor muestra las fuentes del corpus B y del corpus A en su formato original (página web, PDF, chat,
  catálogo MCP) y, para cada carga, la página limpia y la atacada lado a lado con el texto plantado resaltado en el
  código fuente. Esto hace visible el caso de la ubicación oculta, que no aparece en la página renderizada pero sí en
  el bloque JSON-LD que lee el agente (D87). Los archivos se sirven por lista blanca; las páginas HTML llevan una
  política de seguridad de contenido con `sandbox` y se muestran en un marco aislado, sin scripts ni recursos externos.
- **Resultados** presenta E1, E2 y E3 con sus intervalos de Wilson y figuras, leídos de la evidencia versionada.
  **Historial** lista las consultas de la visita con su costo.
- **Configuración** reúne lo que controla el visitante: la clave de OpenRouter, guardada solo en el navegador (en la
  sesión de la pestaña, salvo que pida recordarla); el modelo de la lista curada, con su costo medido y su evidencia de
  desempeño; las capas de defensa con los presets C0–C3, el umbral del clasificador con aviso de modo exploratorio y la
  elección entre los dos clasificadores validados (D86); la verificación N3, y el gasto acumulado de la visita (D90).
