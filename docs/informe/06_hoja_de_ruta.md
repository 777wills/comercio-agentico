# 6. Hoja de ruta

## 6.x Catálogo de referencia gestionado

El emparejamiento de ofertas sin identificador compara cada oferta con un catálogo de referencia del comprador:
recupera los cinco productos más próximos por similitud de embeddings (`multilingual-e5-small`, 384 dimensiones) y
un LLM confirma el producto idéntico o se abstiene. En el prototipo, ese catálogo es un archivo JSON de 40 productos
que forma parte del corpus congelado; sus vectores se calculan en memoria al iniciar cada corrida y la búsqueda es
exhaustiva por producto punto. El diseño es deliberado: la huella del corpus ata cada resultado experimental a una
versión exacta del catálogo, condición necesaria para reproducir E2 y E3.

En una organización, el catálogo de referencia puede contener miles de productos, pertenece a cada empresa y cambia
con frecuencia. Recalcular todos sus vectores en cada ingesta deja de ser viable, y un archivo no admite altas
concurrentes ni varios clientes. La evolución propuesta conserva la lógica de emparejamiento y cambia el lugar donde
residen el catálogo y sus vectores.

**Almacenamiento.** El catálogo pasa a PostgreSQL, la base que ya usa el producto, con una fila por producto y
empresa (GTIN, MPN, marca, modelo, categoría y atributos normalizados según el perfil de categoría). Cada producto
guarda su vector en una columna de la extensión pgvector, junto con la huella SHA-256 del texto que lo originó y el
nombre del modelo de embeddings. Un índice HNSW acelera la búsqueda aproximada de vecinos; índices únicos por empresa
sobre GTIN y MPN sostienen la vía exacta.

**Indexación incremental.** El vector se calcula una sola vez, al crear o modificar un producto, y solo si cambió la
huella de su texto. El catálogo completo se recalcula únicamente al cambiar de modelo de embeddings, porque los
vectores de dos modelos no son comparables. La carga inicial admite importación desde el ERP o desde un archivo CSV, y
las altas posteriores, una API.

**Búsqueda.** La preselección de candidatos se convierte en una consulta SQL que filtra por empresa y categoría y
ordena por distancia vectorial. La misma consulta admite una variante híbrida que combina la búsqueda de texto
completo de PostgreSQL, sensible a referencias como «X1504» o «16/512», con la vectorial mediante fusión por rango
recíproco (RRF). Una base vectorial dedicada (Chroma, Qdrant, Milvus) es una alternativa si la escala lo exige, a
cambio de mantener sincronizados dos almacenes.

**Productos sin catalogar.** Una oferta que no corresponde a ningún producto del catálogo conserva la abstención del
prototipo y entra además en una cola de revisión: un usuario decide si la agrega al catálogo, y en ese caso la oferta
se reprocesa.

| Etapa | Prototipo | Producción propuesta |
|---|---|---|
| Origen del catálogo | Archivo JSON congelado en el corpus | Tabla por empresa en PostgreSQL, alimentada por ERP, CSV o API |
| Cálculo de embeddings | Todos, en memoria, en cada corrida | Uno por producto, al crearlo o modificarlo; persistido en pgvector |
| Vía exacta (GTIN/MPN) | Diccionarios en memoria | Consulta por índice único |
| Preselección | Producto punto exhaustivo, cinco candidatos | Consulta SQL filtrada por empresa y categoría, índice HNSW, opcionalmente híbrida |
| Confirmación | LLM elige o se abstiene | Sin cambios |
| Producto ausente | Abstención | Abstención y cola de revisión humana |
| Reproducibilidad experimental | Huella del archivo | Instantánea exportada del catálogo con su huella |

En el código, el emparejador ya recibe el catálogo como una secuencia de productos y no depende de su origen. El
cambio se concentra en extraer la preselección a un repositorio con dos implementaciones: la de archivo, para
experimentos y pruebas sin red, y la de PostgreSQL con pgvector, para producción.

## 6.y Consumo determinista de catálogos (N1) y verificación dirigida (N3)

**N1.** La arquitectura prevé una capa de consumo determinista para los proveedores que publican su catálogo por una
vía estructurada: la API pública de catálogo de las tiendas montadas sobre VTEX o el marcado schema.org de sus
fichas. El prototipo ya contiene el lector de schema.org, como ruta determinista de N3 y como bloque que antecede al
Markdown de cada página (D74). Falta exponerlo como herramienta de fuente del planificador, de modo que una tienda
con datos estructurados no pase por el extractor con LLM. La API de VTEX exige revisar, tienda por tienda, que sus
términos de uso permitan el consumo automatizado (D70). Al ser una capa determinista, queda fuera del alcance de la
investigación (D11).

**N3 dirigida.** E1 mostró que dos LLM pueden omitir el mismo dato (el plazo de un producto agotado) y que la
concordancia no revela ese error. Dos evoluciones atacan el límite: una re-extracción dirigida, que pregunta a la
segunda ruta solo por los campos de la oferta candidata, y la verificación bajo ataque, que evalúa si N3 detecta la
alteración de precio de la clase A20 cuando la carga logra pasar al extractor.
