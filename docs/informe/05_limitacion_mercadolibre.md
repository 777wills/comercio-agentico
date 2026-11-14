# 5.x Limitación del entorno: el acceso de los agentes a Mercado Libre

Mercado Libre quedó fuera de las fuentes de CotIA por
razones contractuales y no técnicas. La lectura de su sitio con un navegador automatizado está excluida desde D112:
sus buenas prácticas para desarrolladores piden no hacer *web crawling* y trabajar siempre con la API, y la
cláusula 7.6 de los Términos y Condiciones del Programa de Desarrolladores para Colombia prohíbe el uso de robots,
*spiders* o *scraping* sobre el sitio (Mercado Libre, s. f.-a; s. f.-b).

La API oficial sí permite, en lo técnico, lo que CotIA necesita. El buscador de productos de catálogo, disponible
para Colombia, acepta palabras clave o un código universal de producto (`/products/search?site_id=MCO&q=…`) y
devuelve productos con su ficha técnica y su GTIN. La ficha de cada producto (`/products/{id}`) informa la
publicación ganadora con su precio, su vendedor y si el envío es gratis (Mercado Libre, s. f.-c). El acceso exige
una aplicación registrada, un permiso funcional de lectura y un token OAuth 2.0 que vence a las seis horas, y no
tiene una tarifa base, aunque Mercado Libre se reserva el cobro de las llamadas que excedan el límite que fije
(Mercado Libre, s. f.-b, cl. 2.2.3). El servidor MCP oficial no cambia este panorama, porque solo expone la búsqueda
y la lectura de la documentación técnica (Mercado Libre, s. f.-d).

El obstáculo está en el uso permitido. Los términos autorizan la API únicamente para facilitar y mejorar el uso del
propio sitio, prohíben emplearla para desarrollar servicios que compitan con los de Mercado Libre (cl. 2) y
establecen que su contenido «no podrá confundirse ni combinarse con el contenido de terceros» (cl. 5.2) (Mercado
Libre, s. f.-b). Un agente de compras que compara proveedores heterogéneos en un mismo cuadro y recomienda el de
menor costo total hace justamente esa combinación. Por eso Mercado Libre no se integró.

El caso ilustra una barrera del comercio agéntico que excede a este prototipo: una plataforma de comercio electrónico decide,
por contrato, si un agente que representa al comprador puede comparar sus ofertas con las de la competencia. Abrir esa
fuente exigiría una autorización expresa de Mercado Libre para un uso académico o un acuerdo comercial, lo que se
deja en la hoja de ruta.

**Referencias (por verificar formato según la norma de citación del informe; consultadas el 14-nov-2026):**

- Mercado Libre. (s. f.-a). *Buenas prácticas para uso de la plataforma*. https://developers.mercadolibre.com.co/es_ar/buenas-practicas-para-uso-de-la-plataforma (actualizada el 30/12/2025).
- Mercado Libre. (s. f.-b). *Términos y Condiciones del Programa de Desarrolladores de Mercado Libre COL*. https://developers.mercadolibre.com.co/es-co-terminos-y-condiciones
- Mercado Libre. (s. f.-c). *Buscador de productos*. https://developers.mercadolibre.com.co/es_ar/buscador-de-productos (actualizada el 29/12/2025).
- Mercado Libre. (s. f.-d). *MCP Server de Mercado Libre*. https://developers.mercadolibre.com.co/es_ar/mcp-server (actualizada el 10/09/2026).
