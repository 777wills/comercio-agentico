# 1. Introducción

## 1.1 Necesidad de negocio

Comparar una compra entre varios proveedores es una tarea costosa y repetitiva. El precio vigente, la
disponibilidad, la especificación y las condiciones de entrega están dispersos en sitios con estructuras y
nomenclaturas incompatibles que cambian con frecuencia. En una organización, esa dispersión se traduce en tiempo de
analista, en decisiones tomadas con información parcial y en la ausencia de un registro de por qué se eligió una
alternativa. Este trabajo aborda la reducción del costo y del error de la comparación de ofertas entre proveedores
heterogéneos, con trazabilidad de cada dato y sin sustituir la decisión humana.

La delegación de la compra en agentes de inteligencia artificial ya forma parte de las expectativas del consumidor.
En una encuesta en línea a 25 590 personas de 16 países, realizada en enero de 2026, el 74 % declaró que confiaría
en un agente personal de inteligencia artificial más que en su mejor amigo para hacer una compra en su nombre, y el
61 % quiere un agente que compre por él en varios comercios de víveres (Accenture, 2026). El estudio es de alcance
internacional y no permite aislar el mercado colombiano, por lo que se emplea como indicador de tendencia.

En Colombia, el comercio electrónico registró 186,35 millones de transacciones y ventas por $39,37 billones de pesos
corrientes en el primer trimestre de 2026, con un crecimiento de 22,2 % en el número de transacciones y de 14,5 %
en el valor frente al mismo trimestre de 2025 (Cámara Colombiana de Comercio Electrónico [CCCE], 2026). Con esas
cifras, el valor medio por transacción pasó de cerca de $225 500 a cerca de $211 300, una reducción del 6,3 %: el
número de compras crece más rápido que su valor, y con él el número de decisiones de comparación por unidad de
gasto.

## 1.2 El problema técnico

La comparación automática entre fuentes heterogéneas enfrenta cuatro obstáculos. Las fuentes emplean nomenclaturas
incompatibles para el mismo producto; las presentaciones y las unidades de venta no son conmensurables de forma
directa; el precio y la disponibilidad cambian con alta frecuencia; y en buena parte del mercado no hay un
identificador común que permita afirmar que dos ofertas corresponden al mismo artículo. Un sistema que compare debe
extraer, normalizar, emparejar y verificar antes de decidir, y cada uno de esos pasos admite fallos silenciosos que
solo una verificación explícita hace visibles.

Los modelos de lenguaje permiten, por primera vez, leer páginas de estructura arbitraria y convertirlas en datos
tipados sin escribir un extractor por sitio. Esa misma capacidad abre una superficie de ataque. Un agente que lee
contenido de terceros puede recibir instrucciones escondidas en ese contenido: la **inyección indirecta de
instrucciones** (Greshake et al., 2023), que encabeza la clasificación de riesgos de aplicaciones con modelos de
lenguaje de OWASP (OWASP Gen AI Security Project, 2024) y que, en su forma agéntica, corresponde al secuestro de
objetivos del agente (OWASP Gen AI Security Project, 2025). En un agente de compras, el atacante es cualquier
tienda o vendedor capaz de escribir en una página que el agente consultará, y su objetivo es comercial: desviar la
recomendación, falsear un precio o extraer el presupuesto del comprador.

El lado del proveedor agrega un tercer frente. Los protocolos de comercio agéntico (Model Context Protocol, Agent
Payments Protocol, Agentic Commerce Protocol y Universal Commerce Protocol) definen cómo un agente descubre
catálogos y ejecuta pagos con proveedores preparados para ello (Anthropic, 2024; Handa y Gupta, 2026; Parikh y
Surapaneni, 2025; Weinstein y Kaliski, 2025). La mayoría de los comercios, en cambio, solo publica páginas web para
personas, y existen instrumentos que puntúan cuán preparado está un sitio para ser leído por agentes (Jesus y
Morrison, 2026). Un agente de compras útil hoy debe operar sobre ese mercado mixto: fuentes estructuradas junto a
páginas planas, documentos y mensajes.

## 1.3 Objetivos

**Objetivo general.** Construir y evaluar un prototipo de agente de compras verificable sobre proveedores
heterogéneos, con defensa medida frente a la inyección indirecta de instrucciones.

**Objetivos específicos.**

1. Diseñar una arquitectura de orquestación con un contrato único de fuente y perfiles de categoría declarativos,
   que integre la navegación agéntica, la verificación y una política de seguridad.
2. Construir dos corpus de evaluación: uno de tiendas reales, congelado y versionado, y uno sintético controlado,
   con verdad conocida por construcción, que habilite el experimento adversarial.
3. Cuantificar el aporte de la verificación, el costo de la seguridad sobre la utilidad y la frontera de
   costo-desempeño entre modelos de lenguaje.
4. Caracterizar el nivel de preparación de las fuentes evaluadas y su relación con el desempeño del agente.

## 1.4 Aportes

1. **Una arquitectura de agente de compras con procedencia obligatoria y separación de planos.** Cada oferta lleva
   la fuente, la consulta, la marca de tiempo, el fragmento original con su huella SHA-256 y la ruta de
   extracción. El contenido de terceros solo llega al modelo en la extracción tipada; el planificador recibe datos
   estructurados y nunca texto de las páginas.
2. **Un banco de evaluación reproducible.** Un corpus sintético de cinco proveedores en niveles crecientes de
   madurez digital (servidor MCP, web con schema.org, web plana, PDF y mensaje), con 60 tareas de verdad conocida;
   un corpus real de tres tiendas colombianas con 20 tareas; y una suite pública de 20 cargas de inyección en
   cinco clases y cuatro ubicaciones, cuyo éxito se evalúa por programa.
3. **Evidencia cuantitativa sobre tres preguntas.** El aporte de la verificación por una ruta independiente (E1), la
   curva de seguridad frente a utilidad de tres defensas acumulativas (E2) y la frontera de costo-desempeño entre
   modelos con una regla de parada fijada antes de medir (E3).
4. **CotIA, un producto mínimo viable en producción.** Una aplicación web pública en la que cada visitante usa su
   propia clave, elige el modelo y consulta tanto el corpus de evaluación como tiendas colombianas reales, con las
   defensas medidas activas por defecto.

## 1.5 Alcance

El entregable es un prototipo evaluado, no un producto en operación comercial. El agente entrega una propuesta de
compra trazable y se detiene: no ejecuta pagos, y toda acción irreversible queda en manos del comprador. Opera sobre
un dominio de producto (electrónica de consumo) y solo sobre las fuentes que el usuario autoriza. La transferencia a
un segundo dominio, los adaptadores a los protocolos de comercio agéntico y el descubrimiento abierto de proveedores
se documentan en la hoja de ruta.

## 1.6 Organización del documento

La sección 2 revisa el estado del arte en agentes web y de compras, extracción y emparejamiento con modelos de
lenguaje, inyección indirecta y sus defensas, y protocolos de comercio agéntico. La sección 3 describe la
metodología: arquitectura, corpus, métricas, defensas y producto. La sección 4 presenta los resultados de los
experimentos, y la sección 5, su discusión, incluidos los riesgos éticos y legales. La sección 6 cierra con las
conclusiones, el contraste del plan con lo logrado y la hoja de ruta.
