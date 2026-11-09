# 3. Metodología — Plataforma técnica

## 3.x Stack y criterio de simplicidad

El prototipo se construye sobre componentes existentes y ampliamente adoptados, de modo que el esfuerzo de
desarrollo se concentra en lo que constituye la contribución del trabajo —el agente, la extracción con
procedencia, la defensa frente a inyección indirecta y su evaluación— y no en infraestructura. La Tabla X resume
el stack y la versión fijada de cada componente; todas las dependencias se resuelven con `uv` y quedan congeladas
en un archivo de bloqueo versionado, lo que hace reproducible el entorno de cada corrida.

| Función | Componente | Versión |
|---|---|---|
| Lenguaje | CPython | 3.13.16 |
| Orquestación del agente | LangGraph / LangChain | 1.2.20 / 1.4.9 |
| Acceso a modelos | langchain-anthropic / langchain-openrouter | 1.7.10 / 0.2.9 |
| Conversión de páginas a Markdown | crawl4ai | 0.9.5 |
| Esquema y validación | Pydantic | 2.12.5 |
| Interfaz | Streamlit | 1.67.0 |
| Pruebas y calidad | pytest / Ruff | 9.2.0 / 0.17.4 |

La calidad del código se automatiza con un mismo conjunto de verificaciones en local y en integración continua:
análisis estático y formato con Ruff, ganchos de pre-commit (incluida la detección de llaves privadas, pertinente
en un repositorio público) y pruebas unitarias que no requieren red ni claves.

## 3.y Modelos y control de la variabilidad

Se comparan seis modelos en tres niveles de costo, pareando un modelo comercial de Anthropic con uno de pesos
abiertos en cada nivel: DeepSeek V4.1 Flash y Claude Haiku 5.5 (económico), DeepSeek V4 Pro y Claude Sonnet 5.5
(medio), y Kimi K3.1 Pro y Claude Opus 5.5 (tope). Los modelos de Anthropic se consumen por su API directa; los de
pesos abiertos, a través del agregador OpenRouter.

Un mismo modelo de pesos abiertos es servido en OpenRouter por decenas de proveedores de inferencia, con
cuantizaciones que van de 4 a 16 bits y precios que difieren en más de un orden de magnitud. Si el enrutamiento
quedara libre, dos corridas del mismo experimento podrían ejecutarse sobre infraestructuras y precisiones
distintas, y una diferencia de calidad entre modelos podría deberse a la cuantización y no al modelo. Por ello
cada modelo se fija a un único proveedor, sin respaldo automático hacia otros, y se elige el mismo proveedor
(DeepInfra) para los tres, con cuantización de 8 bits o superior (FP8 para DeepSeek, BF16 para Kimi). Que el
enrutamiento se respeta se comprobó consultando la API de generaciones de OpenRouter, que informa el proveedor que
atendió cada solicitud.

La salida estructurada se obtiene en los seis modelos por el mismo mecanismo, el esquema JSON nativo de cada
plataforma, para que la comparación no mezcle métodos de extracción. El mecanismo alternativo —forzar la llamada
a una herramienta— no es admitido por DeepSeek V4 Pro en el proveedor fijado. La temperatura se fija en cero en
los modelos que la aceptan; los modelos Claude de la generación 5.5 no admiten el parámetro, de modo que la
variabilidad entre ejecuciones se mide repitiendo corridas, como prevé la regla de parada del experimento E3.

## 3.z Contrato de datos con procedencia obligatoria

Toda oferta circula en un esquema canónico inspirado en los tipos `Product` y `Offer` de schema.org: título,
precio, moneda ISO 4217, GTIN, referencia del fabricante, marca, modelo, disponibilidad, condiciones de entrega y
atributos técnicos. El esquema distingue dos objetos. El modelo de lenguaje produce únicamente la oferta extraída;
la procedencia —fuente, consulta, marca de tiempo, fragmento original, ruta de extracción, modelo empleado y suma
de verificación SHA-256 del fragmento— la escribe el código. El modelo no puede, por tanto, declarar de dónde
proviene un dato, y cualquier cifra de la propuesta final puede re-extraerse y auditarse contra el fragmento que
la originó. El GTIN se valida por su dígito de control (módulo 10 de GS1), lo que descarta en la ingesta los
códigos mal transcritos o inventados.

Los atributos comparables de cada categoría, sus unidades canónicas y factores de conversión, las variantes de
escritura de los valores categóricos, las restricciones duras y el orden de los identificadores de emparejamiento
se declaran en un perfil de categoría en YAML. Cambiar de dominio consiste en escribir un nuevo perfil, sin
modificar el código.

## 3.w Registro de costo

Cada llamada a un modelo registra tokens de entrada y salida, costo y proveedor. En OpenRouter el costo es el que
la propia API reporta en la respuesta; en Anthropic se calcula a partir de los tokens y la tarifa publicada. Un
tope de gasto por tarea detiene la ejecución si se excede, lo que protege el presupuesto frente a bucles del
agente y alimenta la métrica de costo por tarea (M6).

En una extracción representativa —una página de catálogo con doce ofertas, entre 1500 y 3500 tokens de entrada
según el tokenizador de cada modelo— el costo osciló entre US$0,0015 (DeepSeek V4.1 Flash y Claude Haiku 5.5) y
US$0,053 (Claude Opus 5.5), con DeepSeek V4 Pro en US$0,006 y Claude Sonnet 5.5 y Kimi K3.1 Pro entre US$0,025 y
US$0,032.
