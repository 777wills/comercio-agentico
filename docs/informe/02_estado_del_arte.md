# 2. Estado del arte

## 2.1 Agentes de lenguaje que actúan en la web

El patrón ReAct intercala trazas de razonamiento y acciones de un modelo de lenguaje, de modo que el modelo decide
qué herramienta usar a partir de lo que observa en cada paso. Con uno o dos ejemplos en el contexto, superó a los
métodos de aprendizaje por imitación y por refuerzo en 34 y 10 puntos absolutos de tasa de éxito en ALFWorld y
WebShop (Yao et al., 2023). Es el patrón que sigue el planificador de este trabajo.

La evaluación de agentes web se ha apoyado en entornos de complejidad creciente. WebShop simula una tienda con
1,18 millones de productos reales y 12 087 instrucciones; su mejor modelo alcanzó un 29 % de éxito, frente al 59 %
de expertos humanos (Yao et al., 2022). Mind2Web reúne más de 2000 tareas abiertas en 137 sitios reales de 31
dominios (Deng et al., 2023), y WebArena ofrece un entorno web reproducible de cuatro dominios con 812 tareas, en
el que el mejor agente basado en GPT-4 llegó al 14,41 % frente al 78,24 % humano (Zhou et al., 2024).

Dos trabajos recientes se concentran en la compra. WebMall es el primer banco de compras comparativas entre varias
tiendas: cuatro tiendas con 4421 ofertas y 91 tareas en 11 categorías, entre ellas la búsqueda del producto más
barato y la búsqueda a partir de una descripción vaga, en las que los mejores agentes no superan el 65 % de tareas
completadas (Peeters et al., 2026). ShoppingBench evalúa intenciones de compra complejas (cupones, presupuesto,
varios productos de un mismo vendedor) con 3310 instrucciones sobre más de 2,5 millones de productos reales de
Lazada; GPT-4.1 resuelve por completo menos de la mitad de las tareas (J. Wang et al., 2026). La taxonomía de tareas
de este trabajo (producto específico, menor precio, con restricciones, vaga y sin respuesta) toma como antecedente
la de WebMall.

## 2.2 Extracción estructurada y emparejamiento de productos

Los comercios que publican datos para máquinas suelen hacerlo con el vocabulario de schema.org, cuyos tipos
`Product` y `Offer` describen un artículo y las condiciones en que se ofrece (Schema.org, 2026a, 2026b). El
identificador común más difundido es el GTIN de GS1, cuyo último dígito es de control y se calcula con una suma
ponderada de los anteriores (GS1, s. f.-b); GS1 reserva además el prefijo 952 para demostraciones y ejemplos de su
sistema (GS1, s. f.-a), que este trabajo usa en el corpus sintético para no colisionar con productos reales.

Cuando la página no trae datos estructurados, los modelos de lenguaje pueden extraerlos. La generación guiada
restringe la salida del modelo a una gramática o a un esquema, formulada como transiciones de una máquina de estados
finitos (Willard y Louf, 2023), y es la base de la salida estructurada que usan los proveedores de modelos.
AutoScraper sigue otro camino: el modelo genera extractores reutilizables a partir de la jerarquía HTML y de la
similitud entre páginas (Huang et al., 2024). Este trabajo extrae en cada consulta, sobre Markdown, con un esquema
tipado, porque las fuentes cambian y el costo por página de un modelo económico es bajo.

El emparejamiento decide si dos ofertas corresponden al mismo producto. Los modelos de lenguaje generativos
alcanzan, sin ejemplos o con pocos, un desempeño comparable al de modelos preentrenados ajustados con miles de
ejemplos (Peeters et al., 2025). Para preseleccionar candidatos sin llamar al modelo, los *embeddings* multilingües
E5, entrenados de forma contrastiva con mil millones de pares de textos, permiten comparar nombres informales con
el catálogo en español (L. Wang et al., 2024). Este trabajo combina las dos ideas en cascada: identidad exacta por GTIN
o referencia del fabricante, preselección por similitud de *embeddings* y confirmación con el modelo de lenguaje.

## 2.3 Verificación y abstención

Un dato extraído por un modelo de lenguaje puede ser incorrecto sin señal alguna. La literatura sobre abstención
estudia cuándo un modelo debe negarse a responder, desde tres perspectivas: la consulta, el modelo y los valores
humanos (Wen et al., 2025). En un agente de compras, abstenerse ante un dato no verificable es preferible a
recomendar con un precio falso. Este trabajo implementa la abstención en dos niveles: el agente declara cuando
ninguna oferta cumple la necesidad, y una capa de verificación vuelve a leer el fragmento de origen de la oferta
ganadora por una ruta independiente antes de recomendarla. Las proporciones se reportan con el intervalo de Wilson
(1927), apropiado para muestras pequeñas y proporciones cercanas a 0 o a 1.

## 2.4 Inyección indirecta de instrucciones

Perez y Ribeiro (2022) mostraron que una instrucción del usuario puede secuestrar el objetivo de un modelo o
filtrar su prompt de sistema. Greshake et al. (2023) extendieron el ataque a las aplicaciones integradas: el
atacante no necesita acceso al modelo, le basta con colocar instrucciones en datos que la aplicación recuperará, y
lo demostraron contra un asistente de búsqueda comercial basado en GPT-4. La clasificación de OWASP para
aplicaciones con modelos de lenguaje ubica la inyección de instrucciones como el primer riesgo (LLM01:2026). Parte
de que los modelos no hacen distinción arquitectónica entre instrucciones y datos, y describe la vía indirecta: las
instrucciones del atacante viajan en una página web, un documento o un correo y se ejecutan cuando ese contenido
llega al contexto del modelo (OWASP Gen AI Security Project, 2026). Su clasificación para aplicaciones agénticas nombra el secuestro de objetivos del agente
(ASI01) y el uso indebido de herramientas (ASI02) (OWASP Gen AI Security Project, 2025), y MITRE ATLAS la registra
como la técnica AML.T0051.001 (MITRE, 2026).

Varios bancos miden la vulnerabilidad de agentes con herramientas. InjecAgent reúne 1054 casos con 17 herramientas
del usuario y 62 del atacante; un agente ReAct con GPT-4 fue vulnerable en el 24 % de los casos (Zhan et al.,
2024). AgentDojo define 97 tareas realistas y 629 casos de prueba de seguridad, y observa que los modelos fallan
muchas tareas incluso sin ataque (Debenedetti et al., 2024). Liu et al. (2024) formalizan el problema y comparan
cinco ataques y diez defensas en diez modelos y siete tareas. StakeBench evalúa agentes web reales con 264 casos
adversariales organizados por el interesado que resulta perjudicado y concluye que ningún objetivo de ataque es
resistido de forma confiable (Z. Wang et al., 2026). En el plano teórico, Abdelnabi y Bagdasarian (2026) argumentan,
desde la integridad contextual, que un adversario siempre puede construir un contexto en el que un flujo bloqueado
parezca legítimo.

## 2.5 Defensas

Las defensas propuestas se agrupan en cuatro familias. Los **clasificadores de inyección** examinan el texto antes
de que llegue al modelo; Llama Prompt Guard 2 (Meta, 2025) y Prompt Injection Guard, un clasificador multilingüe de
141 millones de parámetros (Horizon Labs, 2026), son ejemplos con pesos publicados. Las **defensas en el prompt**
marcan el contenido no confiable para que el modelo lo distinga de las instrucciones: el *spotlighting* redujo la
tasa de éxito del ataque de más del 50 % a menos del 2 % en modelos GPT (Hines et al., 2024). Las **defensas por
entrenamiento** separan instrucciones y datos en dos canales y ajustan el modelo para respetar esa separación
(Chen et al., 2025).

Las **defensas arquitectónicas** buscan que el contenido de terceros no pueda alterar el flujo de control, cualquiera
que sea la respuesta del modelo. El patrón de dos modelos asigna a un modelo privilegiado el plan y las herramientas
y a otro, en cuarentena, la lectura del contenido no confiable; el privilegiado solo ve referencias a sus
resultados (Willison, 2023). CaMeL lleva esa idea a un intérprete que extrae los flujos de control y de datos de la
consulta y aplica capacidades a cada valor: resuelve el 77 % de las tareas de AgentDojo con seguridad demostrable,
frente al 84 % de un sistema sin defensas (Debenedetti et al., 2025). Beurer-Kellner et al. (2025) sistematizan
estos enfoques como patrones de diseño con resistencia demostrable.

La separación de planos de este trabajo (C1) pertenece a la familia arquitectónica: el planificador solo recibe
ofertas tipadas producidas por la extracción, nunca el texto de las páginas. Sobre ella se acumulan un clasificador
de inyección (C2) y un control de precios atípicos (C3), y el experimento E2 mide cuánto aporta cada capa y a qué
costo en utilidad.

## 2.6 Comercio agéntico y preparación del proveedor

Desde 2024 se publicaron varios protocolos para que los agentes interactúen con comercios. El Model Context Protocol
estandariza la conexión de los modelos con fuentes de datos y herramientas (Anthropic, 2024), y es la interfaz del
proveedor mayorista del corpus sintético. El Agent Payments Protocol, una extensión de A2A y MCP respaldada por más
de 60 organizaciones, define mandatos firmados para que un agente pague en nombre del usuario (Parikh y
Surapaneni, 2025). El Agentic Commerce Protocol, desarrollado por Stripe y OpenAI, cubre el pago dentro de una
conversación (Weinstein y Kaliski, 2025), y el Universal Commerce Protocol, desarrollado por Google con Shopify,
Etsy, Wayfair, Target y Walmart y respaldado por más de 20 socios, es compatible con AP2 y se integra mediante API,
A2A o MCP (Handa y Gupta, 2026). Estos protocolos trasladan el riesgo hacia el pago: un análisis sistemático de AP2
cataloga 48 amenazas en cinco familias, ocho de severidad alta, y concluye que una firma válida del mandato no
garantiza la intención del usuario (Aviv et al., 2026).

Del lado del proveedor, el Agent Readiness score de Cloudflare puntúa un sitio en cuatro dimensiones:
descubribilidad, contenido, control de acceso de robots y capacidades; los estándares de comercio agéntico se
revisan, pero no cuentan en el puntaje (Jesus y Morrison, 2026). Estos instrumentos describen la superficie de
protocolo que un sitio declara; no miden el desempeño que un agente obtiene al leerlo.

## 2.7 Síntesis y brecha

En los trabajos revisados, el desempeño de la compra, la verificación de los datos extraídos y la seguridad frente
a la inyección se estudian por separado. Los bancos de compras miden el éxito de la tarea; los de inyección miden
la vulnerabilidad en agentes de propósito general; los protocolos de comercio suponen proveedores preparados. La
Tabla 2.1 resume esa distribución y la posición de este trabajo, que mide las tres dimensiones sobre las mismas
tareas, con objetivos de ataque comerciales (desviar la compra, falsear un precio, extraer el presupuesto) y en
proveedores de madurez digital heterogénea.

**Tabla 2.1.** Dimensiones que evalúa cada línea de trabajo.

| Trabajo | Compra comparativa | Fuentes heterogéneas (API, web, PDF, mensaje) | Verificación del dato extraído | Inyección con objetivos comerciales |
| --- | --- | --- | --- | --- |
| WebShop; Mind2Web; WebArena | No | No | No | No |
| WebMall; ShoppingBench | Sí | No | No | No |
| InjecAgent; AgentDojo; StakeBench | No | No | No | Parcial |
| CaMeL; patrones de diseño | No | No | No | Defensa general |
| Este trabajo | Sí | Sí | Sí | Sí |

*Parcial*: mide la inyección en agentes con herramientas o en la web, con objetivos de ataque generales y no
específicos de una compra. *Defensa general*: propone defensas evaluadas en bancos de propósito general.
