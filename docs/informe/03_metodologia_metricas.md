# 3. Metodología — Arnés de evaluación y métricas

## 3.x Arnés de evaluación

Toda configuración del agente se evalúa con un mismo procedimiento automático, sin juicio humano ni modelo de
lenguaje como juez. Una configuración es un archivo declarativo que fija el modelo, la condición de separación de
planos (C0 o C1), el límite de llamadas a herramientas, el tope de gasto por tarea y la concurrencia. El arnés la
ejecuta sobre un conjunto de tareas, con N repeticiones, y anexa cada ejecución (tarea × repetición) a un registro
JSONL. Cada línea contiene:

- **Reproducibilidad:** modelo, identificador del modelo en la plataforma, proveedor de inferencia fijado,
  versión del prompt (huella SHA-256 de las instrucciones de los cuatro roles del modelo: intérprete,
  planificador, extractor y confirmador), huella del corpus (todos los archivos de proveedores, la verdad y el
  archivo de tareas) y *commit* del código.
- **Resultado:** la necesidad interpretada, la propuesta de compra completa con la procedencia de cada oferta y
  todas las ofertas recolectadas y emparejadas, válidas o no.
- **Consumo:** tokens de entrada y salida, número de llamadas al modelo y a herramientas, costo informado por la
  plataforma y latencia de extremo a extremo.

Las tareas se ejecutan en paralelo (cuatro a la vez en la calibración), con un único semáforo de llamadas
simultáneas al modelo compartido por todas. El semáforo acota la presión sobre el límite de tasa del proveedor de
inferencia; ante una respuesta HTTP 429 se reintenta con esperas de 5, 15 y 30 s. Un error en una tarea no
detiene la corrida: queda registrado y cuenta como fallo. Una corrida interrumpida se reanuda con el mismo comando,
porque el arnés omite las ejecuciones ya registradas.

Para validar el propio arnés se usa un agente simulado que responde desde la verdad del corpus e introduce errores
conocidos y deterministas: precios desviados un 10 % en una fracción de las ofertas, la oferta más cara en una de
cada seis tareas con respuesta y abstenciones omitidas en la mitad de las tareas sin respuesta. Las pruebas
automáticas verifican que cada métrica encuentre exactamente los errores sembrados.

## 3.y Métricas

Las métricas se calculan desde el registro, contra la verdad del corpus B, que se conoce por construcción.

**M1 — Exactitud de extracción por ruta.** Cada oferta recolectada y emparejada con un producto del catálogo se
compara campo a campo con la oferta del mismo proveedor y producto en la verdad. Los campos son precio, costo de
envío, disponibilidad y plazo de entrega, siempre, más GTIN, número de parte y marca cuando la fuente los publica
o la extracción los produce. Un identificador inventado para una fuente que no lo publica cuenta como error. Los
importes y plazos se comparan numéricamente y los textos sin distinguir mayúsculas. La exactitud se informa por
tipo de fuente (MCP, HTML con JSON-LD, HTML plano, PDF y mensaje). Se informan además dos medidas
complementarias: la fracción de ofertas **sin correspondencia** en la verdad (emparejamiento erróneo o
invención) y la **recolección**, es decir, la fracción de las ofertas válidas de cada tarea que llegó al cuadro
comparativo.

**M2 — Éxito por categoría de tarea.** Una tarea con respuesta se acierta cuando la oferta recomendada coincide
con la de referencia (proveedor y producto). En las tareas vagas basta con recomendar cualquier oferta válida. En
las tareas sin respuesta, el acierto es abstenerse. Se informa por categoría y en total.

**M3 — Acuerdo entre ejecuciones.** Con R ≥ 2 repeticiones, se mide la fracción de tareas en las que el agente
toma la misma decisión en todas las repeticiones (la misma oferta, abstenerse o fallar), y la dispersión de M2
entre repeticiones (rango y desviación estándar). Esta dispersión es el umbral de ruido de la regla de parada de E3.

**M4 — Abstención.** Se informan la abstención correcta (se abstiene cuando no hay respuesta válida), la
abstención indebida (se abstiene habiendo respuesta), la cobertura (responde cuando hay respuesta) y la exactitud
sobre lo cubierto (aciertos entre las tareas en las que no se abstuvo).

**M6 — Costo y latencia.** Costo por tarea (media, mediana y percentil 90) con el costo que informa la plataforma
en cada respuesta, y latencia de extremo a extremo (mediana y percentil 90).

**Intervalos.** Las proporciones se reportan con intervalo de confianza del 95 % de Wilson [ref: E. B. Wilson,
1927, por verificar en S10]. Para la media y los percentiles de costo y latencia se usa un *bootstrap* percentil
con 5000 remuestreos y semilla fija [ref: B. Efron, 1979, por verificar en S10]. La unidad de M1 es la
observación de extracción: si dos tareas extraen la misma página, la página cuenta dos veces. Como esas
observaciones no son independientes, el intervalo de M1 es optimista y se interpreta solo como orden de magnitud.
