# 6.x Plan frente a lo logrado

El plan de trabajo entregado en agosto de 2026 fijó cuatro objetivos específicos, cuatro experimentos y siete
métricas. La ejecución se concentró en un periodo más corto que el previsto (D01). Por eso se ordenó con un
principio explícito: primero lo que corresponde a la inteligencia artificial (agentes, extracción, defensa y
evaluación) y al final lo determinista (D05, D11). La Tabla 6.x.1 contrasta cada compromiso con su resultado y, cuando
cambió, con la decisión que lo justifica.

**Tabla 6.x.1.** Compromisos del plan y su estado.

| Compromiso del plan | Resultado | Estado | Justificación |
| --- | --- | --- | --- |
| Arquitectura en cuatro capas con contrato único de fuente y procedencia obligatoria | Grafo de estados en LangGraph con contrato de fuente, esquema canónico y procedencia sellada con SHA-256 en cada oferta | Cumplido | D10 |
| N1: extracción determinista sobre API de catálogo y anotaciones semánticas | El lector de schema.org existe como ruta determinista de N3 y como bloque que antecede al Markdown de cada ficha; no se expuso como herramienta propia del planificador | Parcial; el resto queda propuesto | N1 no aporta inteligencia artificial nueva y se construyó al final (D11) |
| N2: navegación agéntica sobre el árbol de accesibilidad | Agente ReAct propio con herramientas sobre crawl4ai y Playwright, que lee Markdown en lugar del árbol de accesibilidad | Cumplido con cambio | Controlar por dónde entra el contenido de terceros al modelo, condición para medir la inyección (D12) |
| N3: verificación por una ruta independiente | Segunda lectura determinista o con un LLM de otra familia; políticas de abstención y exclusión | Cumplido | E1 y E1 con fallas sembradas |
| N4: sanitización y política | Tres defensas acumulativas: separación de planos (C1), clasificador de inyección (C2) y control de precio (C3) | Cumplido | E2 |
| Dos dominios de producto: uno a fondo y otro de transferencia | Un dominio, electrónica, con un perfil de categoría declarativo | Parcial | El segundo dominio exige un segundo corpus real completo: trabajo de datos, no de IA (D23) |
| Corpus real congelado de 6–8 fuentes | Corpus A con tres tiendas colombianas, reconstruido a partir de hechos verificados, con manifiesto y sumas de verificación y sin publicar copias | Cumplido con alcance menor | Términos de uso y derechos de autor de las páginas (D22, D70) |
| Banco sintético de cinco proveedores en niveles de madurez | Corpus B: MCP, web con schema.org, web plana, PDF y mensaje, sobre un catálogo común con verdad conocida por construcción | Cumplido | D21 |
| 100 tareas con respuesta de referencia | 60 tareas en el corpus B y 20 en el A, generadas por programa | Cumplido con alcance menor | Verdad conocida por construcción en lugar de etiquetado manual (D21) |
| Calibración de metas | Corrida de calibración con metas reportadas con intervalos, sin umbral previo | Cumplido | D45 |
| E1: aporte de la verificación | Reproducción pareada sobre 80 ejecuciones y siembra de cinco tipos de fallas | Cumplido y ampliado | N3 no cambió decisiones con errores naturales; con fallas sembradas impidió el 100 % de las recomendaciones con datos falsos |
| E2: seguridad adversarial con curva seguridad-utilidad | 20 cargas (5 clases × 4 ubicaciones), C0–C3, segundo modelo en C0 y C3, ataque adaptativo A21 y medición de C2 en páginas reales | Cumplido y ampliado | D43, D108, D115, D123 |
| E3: frontera costo-desempeño y elección del modelo | Dos de seis modelos medidos; los demás, descartados por la regla de parada fijada antes de correr | Cumplido | D42; la regla protege el presupuesto con un umbral derivado de los datos |
| E4: transferencia (M7) y preparación de las fuentes | Diseño de M7 y del perfil declarativo; sin segundo dominio | Propuesto | D23, D40 |
| Métricas M1–M7 | M1–M6 automatizadas en el arnés; M7 solo como diseño | Parcial | D45 |
| Aplicación web de demostración con panel de procedencia | CotIA, publicada en una URL pública: clave propia del visitante, modos Cliente y Laboratorio, consulta en tiendas reales con lista blanca editable | Cumplido y ampliado | D81–D84, D112–D113 |
| Re-evaluación programada como práctica MLOps | Integración continua con corpus regenerado, evaluación semanal con el arnés simulado y canario opcional con un modelo real | Cumplido | D124 |
| Respeto de robots.txt, sin datos personales y sin pagos | Robots.txt por sitio, robot identificable, pausas, guardia de red; el agente no compra | Cumplido | D70, D112, D125 |

## Lo que se agregó sin estar en el plan

- **Producto público con clave propia del visitante.** El plan preveía una demostración local. CotIA opera en
  producción, y cada visitante paga con su clave y elige el modelo.
- **Consulta en tiendas reales en vivo** con comparación abierta entre ofertas, sin catálogo de referencia.
- **Ataque adaptativo** diseñado contra la arquitectura después de conocer los resultados de E2.
- **Medición de la defensa C2 en páginas reales**, que reveló falsos positivos por contenido codificado y motivó
  el saneamiento del Markdown.
- **Fallas sembradas** para evaluar N3 como detector cuando la tasa base de errores es nula.

## Lo que queda propuesto

E4 y M7, la capa N1 como herramienta propia, los adaptadores a los protocolos de comercio agéntico (ACP, UCP y
AP2), el autohospedaje de un modelo de pesos abiertos, el descubrimiento abierto de proveedores, el catálogo de
referencia gestionado con pgvector (D98), las restricciones inferidas tratadas como blandas y la verificación de las
ofertas descartadas que habrían ganado. El detalle está en la hoja de ruta.
