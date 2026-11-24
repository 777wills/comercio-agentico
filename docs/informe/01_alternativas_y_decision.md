# 1.x Alternativas de solución y decisión

## Alternativas de solución en el mercado

Entre 2025 y 2026, las principales plataformas lanzaron funciones de compra delegada (Tabla I). OpenAI incorporó la compra dentro de la conversación de ChatGPT mediante el Agentic Commerce Protocol, desarrollado con Stripe (OpenAI, 2025; Weinstein y Kaliski, 2025). Google agregó a su buscador una compra agéntica que, a partir de una alerta de precio, completa el pago con Google Pay en comercios elegibles (Srinivasan, 2025), y publicó el Universal Commerce Protocol con varios minoristas (Handa y Gupta, 2026). PayPal y Perplexity habilitaron la compra dentro de las respuestas del buscador conversacional (PayPal, 2025), y Amazon probó con un subconjunto de usuarios un agente que compra en sitios de terceros desde su aplicación (Zeff, 2025).

**TABLA I. Soluciones comerciales de compra delegada**

| Solución | Qué hace | Alcance anunciado | Condición del proveedor |
| --- | --- | --- | --- |
| ChatGPT Instant Checkout (OpenAI, 2025) | Compra de un artículo dentro de la conversación, con confirmación del usuario | Estados Unidos | Comercio integrado al protocolo ACP |
| Compra agéntica de Google (Srinivasan, 2025) | Compra con Google Pay cuando el precio entra en el presupuesto, previa confirmación | Estados Unidos | Comercio elegible |
| Instant Buy de Perplexity y PayPal (PayPal, 2025) | Pago dentro de la respuesta del buscador | Estados Unidos | Comercio habilitado en PayPal |
| Buy for Me de Amazon (Zeff, 2025) | El agente completa la compra en el sitio de un tercero | Prueba con un subconjunto de usuarios | Sitio de marca seleccionado por la plataforma |

Estas soluciones comparten tres rasgos que limitan su uso para el problema planteado. Requieren que el proveedor esté integrado o seleccionado por la plataforma, mientras que la mayoría de los comercios colombianos solo publica páginas para personas. Se orientan a ejecutar la compra de un artículo ya elegido, no a comparar y justificar la elección entre proveedores. Y los anuncios revisados no exponen la procedencia de cada dato ni una evaluación pública de su resistencia a la inyección indirecta.

## Alternativas en la literatura

La literatura ofrece cuatro familias de soluciones. Los extractores por sitio, escritos a mano o generados por un modelo (Huang et al., 2024), son precisos mientras el sitio no cambia, pero exigen mantenimiento por proveedor. Los agentes web generales siguen el patrón ReAct, que intercala razonamiento y acciones (Yao et al., 2023), y se evalúan en entornos como WebShop (Yao et al., 2022), WebArena (Zhou et al., 2024) o WebMall, el primer banco de compras comparativas entre tiendas, donde los mejores agentes no superan el 65 % de tareas completadas (Peeters et al., 2026). Los protocolos de comercio agéntico (MCP, AP2, ACP y UCP) estandarizan el acceso a catálogos y pagos (Anthropic, 2024; Parikh y Surapaneni, 2025), pero suponen proveedores preparados y trasladan el riesgo al pago (Aviv et al., 2026).

Frente a la inyección, las defensas se agrupan en clasificadores que examinan el texto antes del modelo (Meta, 2025; Horizon Labs, 2026), marcas en el prompt que distinguen el contenido no confiable (Hines et al., 2024), entrenamiento que separa instrucciones y datos (Chen et al., 2025) y defensas arquitectónicas que impiden que el contenido de terceros altere el flujo de control. Entre estas últimas, el patrón de dos modelos aísla en cuarentena la lectura de contenido no confiable (Willison, 2023), y CaMeL resuelve el 77 % de las tareas de AgentDojo con seguridad demostrable, frente al 84 % de un sistema sin defensas (Debenedetti et al., 2025). Los bancos de inyección muestran que los agentes con herramientas son vulnerables (Zhan et al., 2024; Debenedetti et al., 2024) y que ningún objetivo de ataque se resiste de forma confiable en agentes web reales (Z. Wang et al., 2026). En los trabajos revisados, el desempeño de la compra, la verificación del dato extraído y la seguridad se estudian por separado.

## Solución elegida y justificación

La solución adoptada es un agente ReAct con un contrato único de fuente, que trata del mismo modo un servidor MCP, una página con schema.org, una página plana, un PDF y un mensaje, y que entrega una propuesta de compra trazable sin ejecutar pagos. La seguridad descansa en una defensa arquitectónica, la separación de planos: el texto de los proveedores solo llega a un extractor sin herramientas y con salida restringida a un esquema, y el modelo que decide recibe ofertas tipadas, nunca prosa de terceros. Sobre ella se acumulan un clasificador local de inyección, un control de precios atípicos y una verificación de la oferta ganadora por una segunda ruta.

La elección responde a las restricciones del caso. El mercado colombiano es mayoritariamente web para personas, lo que descarta depender de protocolos o de comercios integrados. Un extractor por sitio no escala con el número de tiendas. El entrenamiento de separación de canales no es aplicable a modelos consumidos por API, y una defensa como CaMeL exige reescribir la consulta como programa con una pérdida de utilidad reportada. La separación de planos, en cambio, se implementa con la salida estructurada que ya ofrecen los proveedores de modelos, no requiere reentrenar y su costo puede medirse.
