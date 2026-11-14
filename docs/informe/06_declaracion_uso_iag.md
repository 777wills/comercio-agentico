# Declaración de uso de inteligencia artificial generativa

El programa del curso clasifica el proyecto en el nivel 5 de la escala de uso de IA generativa, «Exploración con
IAG». En ese nivel, el estudiante integra tecnologías emergentes en el diseño de la solución y evalúa su impacto
ético, técnico y académico. En este proyecto la IA generativa cumple dos papeles distintos, que se declaran por
separado.

## Como objeto de estudio

El agente de compras es un sistema de IA generativa. Los modelos de lenguaje DeepSeek V4.1 Flash y Claude Haiku 5.5
interpretan la consulta, planifican la búsqueda, extraen las ofertas, confirman el emparejamiento y verifican los
datos. Un clasificador de inyección de Hugging Face y un modelo local de embeddings completan los componentes
aprendidos. Su comportamiento se midió con verdad de referencia conocida, sin juicio de un LLM sobre los
resultados, en los experimentos E1, E2 y E3.

## Como herramienta de desarrollo

| Uso | Herramienta | Cómo se verificó |
| --- | --- | --- |
| Escritura y revisión de código | Asistentes de programación basados en modelos de lenguaje (Claude Code y GitHub Copilot en Visual Studio Code) | Más de 200 pruebas automatizadas sin red, análisis estático con Ruff, integración continua y revisión del autor de cada cambio; cada decisión de diseño quedó registrada con su justificación |
| Generación del corpus B sintético (descripciones, fichas, PDF y mensajes de los proveedores) | Modelos de lenguaje sobre un catálogo propio | Los datos que deciden la compra (precio, envío, disponibilidad, GTIN y su dígito de control) los fija el código, no el modelo, de modo que la verdad de referencia se conoce por construcción |
| Redacción de las 20 cargas de la suite adversarial y de la carga adaptativa A21 | Asistente de programación, bajo supervisión y autorización académica del autor | Plantadas solo en copias locales del corpus sintético, nunca en sitios reales; éxito evaluado por predicados programáticos; cargas publicadas en el repositorio |
| Apoyo a la redacción y revisión del informe | Asistentes basados en modelos de lenguaje | Cada cifra se rastrea a la corrida de `resultados/` que la produjo; cada referencia se verificó contra la fuente primaria; el contenido fue revisado y asumido por el autor |
| Búsqueda de documentación técnica | Servicio de documentación de librerías consultado por el asistente | Contraste con la documentación oficial vigente de cada librería antes de usar su API |

## Límites y responsabilidad

Las decisiones de diseño, el planteamiento de los experimentos, sus reglas fijadas antes de ver datos y la
interpretación de los resultados son del autor. La IA generativa no se usó para evaluar los resultados del agente:
toda métrica se calcula por programa contra la verdad de referencia. El autor asume la responsabilidad por la
totalidad del contenido del informe, del código y de los datos.
