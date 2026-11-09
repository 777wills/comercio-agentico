# 3. Metodología — Corpus B sintético y tareas con verdad conocida

## 3.x Diseño del corpus B

El corpus B es un mercado sintético de electrónica de consumo cuya verdad de referencia se conoce por
construcción. Su propósito es doble: evaluar la extracción, el emparejamiento y la propuesta del agente sin
etiquetado manual, y servir de base controlada para plantar cargas de inyección indirecta sin intervenir sitios
reales.

**Catálogo de referencia.** Contiene 40 productos repartidos por igual entre cinco categorías (portátiles,
monitores, celulares, audífonos y almacenamiento). Los productos los propuso un modelo de lenguaje de bajo costo
(DeepSeek V4.1 Flash) con salida estructurada, en cinco llamadas, una por categoría, con un costo total de
US$0,024. Las instrucciones exigían marcas reales, un rango de precios amplio y un par de variantes por categoría
que difieren solo en memoria o capacidad, para que el emparejamiento sin identificador tenga casos difíciles. El
modelo propone además tres formas de nombrar cada producto: comercial, abreviada de lista mayorista e informal de
mensajería. Las tareas en las que un modelo de lenguaje es poco fiable las asume el código: el GTIN-13 de cada
producto se asigna por programa con su dígito de control y con el prefijo 952, que GS1 reserva para
demostraciones y ejemplos de su sistema [ref: GS1, «GS1 Company Prefix», gs1.org/standards/id-keys/company-prefix,
consultado el 9-nov-2026], de modo que ningún código sintético coincide con un producto real. Además, cada
atributo se valida contra el perfil de categoría, que exige el nombre canónico, la unidad canónica y una categoría reconocida. Dos correcciones
deterministas se aplican a la salida del modelo antes de validarla: se descartan claves ajenas a la categoría y
las capacidades en terabytes decimales se llevan a la convención binaria del perfil. El catálogo resultante se
congela y se versiona, de modo que el resto del corpus no depende de nuevas llamadas al modelo.

**Proveedores.** Un generador determinista, con semilla fija, reparte el catálogo entre cinco proveedores
ficticios que representan niveles decrecientes de madurez de la fuente (Tabla X). Cada proveedor vende un
subconjunto parcial y solapado del catálogo. Aplica un factor de precio propio con una variación aleatoria
acotada, su propio redondeo, su política de envío y su plazo de entrega, y asigna la disponibilidad (en
existencia, agotado o bajo pedido; este último agrega siete días al plazo). Cuatro productos del catálogo no los
vende ningún proveedor y dos más solo aparecen agotados, lo que crea casos en los que la respuesta correcta es la
abstención.

| Proveedor | Canal | Identificadores | Atributos | Nomenclatura | Ofertas |
|---|---|---|---|---|---|
| P1 | Servidor MCP con `buscar_productos` y `detalle_producto` | GTIN, número de parte, marca y modelo | Completos | Campos propios del mayorista (`valor_unitario_cop`, `existencias`, `flete_cop`) | 21 |
| P2 | Web con JSON-LD de schema.org (`Product`, `Offer`, `OfferShippingDetails`) | GTIN, número de parte, marca y modelo | Completos | Título de ficha técnica | 20 |
| P3 | Web plana sin marcado semántico | Solo marca | En prosa comercial | Nombre de vitrina | 19 |
| P4 | Lista de precios en PDF (tabla) | Ninguno | Ninguno | Abreviaturas de mayorista | 22 |
| P5 | Exportación de chat tipo WhatsApp | Ninguno | Ninguno | Jerga informal; precios en el cuerpo del mensaje con formatos locales ("2'350.000", "2350 mil") | 13 |

El orden de generación garantiza la validez de la referencia: primero se escribe `verdad.json`, con la oferta
exacta que debería extraerse de cada proveedor expresada en el esquema canónico `OfertaExtraida`, y solo después
se renderiza cada formato a partir de ella. Cada entrada de la verdad registra la ubicación del fragmento que la
contiene (página y ancla, código de fila del PDF, línea del chat o referencia MCP). El corpus queda con 95
ofertas sobre 36 productos ofrecidos, 18 de ellos presentes en tres o más proveedores. La generación es
reproducible byte a byte, incluido el PDF.

Un único proceso local sirve el corpus: P2 a P5 por HTTP y P1 por MCP sobre HTTP (FastMCP). Así el agente
accede a cada fuente por el mismo canal que usaría con un proveedor real.

## 3.y Tareas y respuesta de referencia

Las 60 tareas del corpus B se generan por programa y se agrupan en cinco categorías inspiradas en la taxonomía
de tareas de WebMall [ref: Peeters et al., arXiv:2508.13024]: búsqueda específica (12), más barato entre
proveedores (12), búsqueda con restricciones de especificación, presupuesto y plazo (15), búsqueda vaga (12) y
casos sin respuesta (9). Cada tarea contiene la consulta en lenguaje natural, sus criterios formalizados (productos
admitidos, tipo de producto, marca, restricciones sobre atributos, presupuesto sobre el costo total y plazo
máximo) y la respuesta de referencia.

La respuesta la produce una sola función, `calcular_respuesta`, que aplica los criterios a la verdad: conserva
las ofertas en moneda local con disponibilidad compatible con las restricciones duras del perfil (en existencia
o bajo pedido), filtra por los criterios de la tarea y ordena por costo total, es decir, precio más envío. La
respuesta incluye la oferta de menor costo y el conjunto ordenado de ofertas válidas. Cuando ese conjunto es
vacío, la respuesta correcta es la abstención. En las tareas de respuesta exacta se exige un mínimo único, y se
descartan durante la generación los candidatos con empate. En las tareas vagas, los criterios hacen explícita una
interpretación razonable de la necesidad (por ejemplo, "liviano" como peso de hasta 1,6 kg), y se considera
correcta cualquier recomendación que pertenezca al conjunto de ofertas válidas.

Los casos sin respuesta cubren cuatro situaciones: producto del catálogo que nadie vende (en tres de los cuatro
casos, su variante de otra capacidad sí está a la venta); producto agotado en todos los proveedores; restricciones imposibles de
satisfacer; y producto ajeno al catálogo.

La coherencia del corpus se verifica con pruebas automáticas que no requieren red ni modelos de lenguaje:

- lo publicado en cada formato coincide con la verdad (JSON-LD analizado, tarjetas HTML, texto extraído del PDF,
  precios informales del chat convertidos de vuelta a número y respuestas del servidor MCP);
- la regeneración desde el catálogo reproduce la verdad y el PDF;
- la respuesta de cada tarea es la que se deriva de la verdad.
