# Registro de decisiones

Cada decisión tiene su porqué. Para cambiar una, se debate con Wills y se agrega una entrada nueva que la reemplace
(no se borra la anterior; se marca como reemplazada).

Estado al 9-nov-2026 (planeación y S00). Base previa: `privado/contexto_claude/CONTEXTO_SESION.md` (sep-2026).

## Alcance y calendario

| # | Decisión | Porqué |
|---|---|---|
| D01 | Se parte de cero: no hay implementación previa. | El cronograma de septiembre no se ejecutó. |
| D02 | Todo (código, experimentos, informe PDF, presentación) listo el **19-nov**. El 20-nov se presenta y se radica. Del 21 al 26: video y ensayo. | El aula virtual exige radicar documento y presentación al menos una semana antes del 27-nov. |
| D03 | Proyecto individual. El ensayo de Ética (otra asignatura) fue en grupo; no cambia la autoría de este proyecto. | Registro del curso. |
| D04 | Ritmo: 4–6 h diarias, en sesiones cortas con corte limpio y continuidad en disco. | Evitar que una sesión sature el contexto del modelo. |
| D05 | Principios: simplicidad sobre sobreingeniería; la IA primero; lo que no cabe queda como propuesto. | Pedido explícito de Wills. Ver `CLAUDE.md`. |

## Arquitectura

| # | Decisión | Porqué |
|---|---|---|
| D10 | Se mantienen las cuatro capas y el contrato único de fuente con procedencia obligatoria (ver contexto histórico, sección 2). | Es la contribución del proyecto; no se desmejora. |
| D11 | Orden de construcción: **N2 agente navegador → N4 defensa → N3 verificación → N1 determinista al final** (o propuesto). | La IA primero. N1 (API VTEX) es consumo determinista. |
| D12 | N2: agente propio en **LangGraph** con herramientas sobre **crawl4ai/Playwright**. Se descartan browser-use (caja negra) y crawl4ai sin agente (deja de ser agente). | Para medir la inyección hay que controlar por dónde entra el contenido de terceros al modelo. |
| D13 | Interfaz en **Streamlit**; almacenamiento en **SQLite/JSON**; un proveedor sintético expuesto por **MCP** (FastMCP). SvelteKit y PostgreSQL pasan a la hoja de ruta. | MVP rápido. MCP aporta una herramienta externa real (RA2) con poco código. |
| D14 | Se descarta el modelo autohospedado en GPU alquilada. La soberanía del dato queda como hoja de ruta, apoyada en que los modelos chinos elegidos tienen pesos abiertos. | No aporta IA nueva y consume una sesión de infraestructura. |
| D15 | Emparejamiento sin GTIN: **embeddings solo del catálogo de referencia**, en memoria, recalculados en cada ingesta; recuperación de los 3–5 más parecidos y confirmación del LLM (o abstención). Modelo de embeddings multilingüe local (verificar en S02). | Los proveedores PDF y WhatsApp no traen GTIN y escriben nombres informales. Cubre RA1 (bases vectoriales). Los documentos del proveedor no se vectorizan: se releen en cada ingesta con suma de verificación, así que sus cambios no rompen nada. |
| D16 | Defensa C2: **clasificador de inyección preentrenado de Hugging Face** (tipo DeBERTa), en lugar de un filtro por expresiones regulares. Verificar licencia y latencia en S06. | Convierte la defensa en un modelo de PLN real; integra los cursos de PLN y Hackeando la IA. |
| D17 | MLOps ligero al final: GitHub Actions corriendo las pruebas, corridas versionadas (modelo, prompt, corpus, commit) y trazas de cada llamada al LLM. | Sostiene R.7.2 sin desplazar la parte de IA. |
| D18 | Nombres del dominio en español en el código (`Oferta`, `Procedencia`, `buscar`), como en el plan entregado. | Coherencia con el plan y el informe. |

## Datos y tareas

| # | Decisión | Porqué |
|---|---|---|
| D20 | Dominio: **electrónica**; corpus A en **tiendas colombianas** (candidatas: Alkosto, Ktronix, Éxito, Falabella; se confirman por robots.txt y términos en S04). | GTIN/EAN hace objetivo el emparejamiento; varias corren sobre VTEX (abre la puerta a N1). |
| D21 | **Corpus B sintético generado con LLM** sobre un catálogo propio: 5 proveedores en niveles de madurez (MCP, web con schema.org, web plana, PDF, texto tipo WhatsApp). La verdad de referencia se conoce por construcción. ~60 tareas. | Elimina el etiquetado manual de 100 tareas. Permite plantar cargas de inyección sin tocar sitios reales (Ley 1273 de 2009). |
| D22 | **Corpus A real pequeño**: ~3 tiendas, ~20 tareas, copias fechadas con suma de verificación. Las copias no se publican (solo el manifiesto). | Validez externa; el repositorio es público y las páginas son obra protegida (Ley 23 de 1982, Decisión 351). |
| D23 | Segundo dominio (E4 transferencia) queda **propuesto**; el perfil de categoría declarativo se diseña igual. | E4 exige un segundo corpus real completo: trabajo de datos, no de IA. |

## Modelos y créditos

| # | Decisión | Porqué |
|---|---|---|
| D30 | **Anthropic directo + OpenRouter** para los modelos chinos. | En la comparación del 9-nov, OpenRouter igualó o mejoró el precio de API directas y otros agregadores en todos los candidatos; una clave, API compatible con OpenAI, costo por llamada en la respuesta (M6). Comisión: 5,5 % al comprar créditos; sin recargo por token. |
| D31 | Modelos (6), en orden de costo: **DeepSeek V4.1 Flash → Claude Haiku 5.5 → DeepSeek V4 Pro → Kimi K3.1 Pro ≈ Claude Sonnet 5.5 → Claude Opus 5.5**. | Pareo por nivel entre Anthropic y modelos chinos de pesos abiertos (económico, medio, tope). |
| D32 | En OpenRouter se **fija el proveedor** de cada modelo para la reproducibilidad, y se registra el costo real devuelto por llamada. | El precio del catálogo es el del proveedor más barato; el enrutamiento puede cambiarlo. |
| D33 | Desarrollo con el modelo más barato que funcione (DeepSeek V4.1 Flash o Haiku 5.5). | Proteger los créditos (presupuesto total US$300). |
| D34 | (S00, 9-nov) Proveedor fijado en OpenRouter: **DeepInfra para los tres modelos** — DeepSeek V4.1 Flash `deepinfra/fp8` (0,14 / 0,42), DeepSeek V4 Pro `deepinfra/fp8` (1,30 / 2,60), Kimi K3.1 Pro `deepinfra/bf16` (1,90 / 9,50); `allow_fallbacks: false`. Concreta D32. | Mismo proveedor y cuantización FP8 o superior: la diferencia entre modelos en E3 no se confunde con la infraestructura ni con la cuantización (los endpoints más baratos son FP4). Sobrecosto pequeño. Verificado con la API de generaciones de OpenRouter (`provider_name: DeepInfra`). |
| D35 | (S00) Salida estructurada con **`method="json_schema"` en los seis modelos** (`obtener_extractor`). | Mismo mecanismo para todos en E3. El método por herramienta forzada (`tool_choice`) no lo admite DeepSeek V4 Pro en DeepInfra (OpenRouter filtra todos los endpoints). |
| D36 | (S00) **Temperatura 0 solo en OpenRouter**; los modelos Claude 5.5 rechazan el parámetro `temperature` (HTTP 400). | La variabilidad de Anthropic se mide con corridas repetidas, como ya prevé D42. |

Precios consultados el 9-nov-2026 (US$ por millón de tokens, entrada / salida). Re-verificar antes de citarlos en el
informe.

| Modelo | ID / slug | Precio | Fuente |
|---|---|---|---|
| Claude Opus 5.5 | `claude-opus-5-5` | 4,00 / 20,00 | Anthropic |
| Claude Sonnet 5.5 | `claude-sonnet-5-5` | 2,00 / 10,00 | Anthropic |
| Claude Haiku 5.5 | `claude-haiku-5-5` | 0,10 / 0,50 | Anthropic |
| Kimi K3.1 Pro | `moonshotai/kimi-k3.1-pro` | 2,00 / 10,00 | OpenRouter (pesos en HF: `moonshotai/Kimi-K3.1-Pro`) |
| DeepSeek V4 Pro | `deepseek/deepseek-v4-pro` | 0,894 / 1,788 | OpenRouter (HF: `deepseek-ai/DeepSeek-V4-Pro`) |
| DeepSeek V4.1 Flash | `deepseek/deepseek-v4.1-flash` | 0,051 / 0,567 | OpenRouter (HF: `deepseek-ai/DeepSeek-V4.1-Flash`) |

Comparación de plataformas (mismo día): API directa de DeepSeek V4 Pro 1,32 / 3,96 (mitad en horario valle: fuera de
01–04 y 06–10 UTC, lunes a viernes); GLM-5.3 directo 1,40 / 4,40 frente a 0,07 / 1,40 en OpenRouter; Together,
Fireworks, SiliconFlow y Novita igual o más caros en todos los candidatos. Fuentes: openrouter.ai/api/v1/models,
openrouter.ai/pricing, api-docs.deepseek.com/quick_start/pricing, docs.z.ai/guides/overview/pricing,
together.ai/pricing, fireworks.ai/pricing, siliconflow.com/pricing, novita.ai/pricing.

## Experimentos

| # | Decisión | Porqué |
|---|---|---|
| D40 | Se ejecutan **E3 (modelos), E2 (seguridad) y E1 (verificación)**; E4 queda propuesto. | Cubren Cr2, Cr4, Cr6 y Cr7 dentro del plazo. |
| D41 | **E3 va primero**, en tareas benignas; su ganador es la configuración base de E2 y E1. | La elección del modelo sale de evidencia (Cr2), no a dedo. |
| D42 | E3 escala del modelo más barato al más caro. **Regla de parada, fijada antes de correr:** no se sube al siguiente modelo si el último no mejoró M2 ni la tasa de abstención correcta más que el ruido entre ejecuciones (dispersión de M3 en 3 corridas del subconjunto). | Protege los créditos con un umbral derivado de los datos, no inventado. |
| D43 | Suite adversarial: **5 clases de ataque × 4 cargas = 20**, plantadas en variantes del corpus B. Configuraciones **C0 sin defensa, C1 separación de planos, C2 + clasificador HF, C3 + verificación cruzada de precio**; C4 lista blanca solo si sobra tiempo. | Curva seguridad-utilidad con 4–5 puntos. |
| D44 | Suite mapeada a **OWASP Top 10 for LLM and GenAI (LLM01)** y a **MITRE** (verificar si la taxonomía pertinente es ATLAS). | Marco reconocido; integra el curso Hackeando la IA. |
| D45 | Métricas M1–M7 del plan, sin juicio humano; M7 solo como diseño (E4 propuesto). Metas sin umbral previo: se reportan con intervalos. | Ver contexto histórico, sección 2. |

## Repositorio

| # | Decisión | Porqué |
|---|---|---|
| D50 | Git en esta carpeta; **GitHub público**; un commit por sesión. | Trazabilidad, respaldo y entregable (Cr8). Wills no requiere repo privado. |
| D51 | (Actualizada por D55) Fuera de git: `.env`, `contexto_claude/`, `.docx/.pptx/.pdf/.xlsx/.csv`, HTML del aula virtual y copias del corpus A. | Repo público: claves, material institucional, documentos personales y obra de terceros. |
| D52 | (S00, 9-nov) Se adopta parcialmente el estándar de proyectos del profesor Jan Polanco (skill `jan-project-standard`): **Ruff, pre-commit, Makefile (`make check`), CI en GitHub Actions, LICENSE MIT, README con badges, `uv.lock` versionado, Conventional Commits** y un `CONSTITUTION.md` breve que remite a DECISIONES, PLAN y ESTADO. Se descartan CODE_OF_CONDUCT, CONTRIBUTING, plantillas de issue, labels, Dependabot, `main` protegida por PR, identidad `includeIf`, tgrep/.opencode y Slidev. | Profesionaliza el repositorio (R.7.2, Cr8) a bajo costo y adelanta la CI de D17. Lo descartado es gobernanza de proyectos colaborativos o choca con un commit por sesión y con la plantilla institucional de presentación. CONSTITUTION no duplica contenido para no crear una segunda fuente de verdad. |
| D53 | (S00) **Python 3.13** (`.python-version`, `requires-python >=3.13`), instalado por `uv`. | Lo exige el estándar (D52); todas las dependencias funcionan en 3.13.16. |
| D54 | (S00) Repositorio público **`777wills/comercio-agentico`**. | Coincide con el paquete `comercio_agentico`. |
| D55 | (9-nov, tras S00) La raíz contiene solo el proyecto de código. Todo lo demás va en **`privado/`** (fuera de git): `privado/curso/` (syllabus, rúbrica, plantillas, páginas del aula, banco de retos), `privado/entregables/` (plan, presentaciones, ensayo de Ética, informe final y video), `privado/contexto_claude/`. | Repositorio público más limpio y una sola regla de exclusión; los documentos de trabajo no se mezclan con el código. |
| D56 | (9-nov) Cada sesión **explica** lo construido y el concepto de IA aplicado, y deja instrucciones de prueba en `docs/GUIA_PRUEBAS.md`. Las pruebas manuales no consumen presupuesto: sin red primero, luego modelo gratuito de OpenRouter, luego una sola llamada al modelo más barato; cada comando declara su costo; nunca Sonnet, Kimi ni Opus. | Pedido de Wills: entender y poder correr el proyecto sin mover el presupuesto de las API. La guía sirve además como documentación de replicación (Cr8). |
| D57 | (9-nov) **`privado/ENTENDER_EL_PROYECTO.md`**: explicación en lenguaje claro del proyecto (idea, arquitectura, experimentos, herramientas, dinero, calendario, glosario) con una entrada por sesión, que cada sesión actualiza al cerrar. Vive en `privado/` (no se versiona), por pedido de Wills. | Pedido de Wills: entender todo lo realizado. Sirve también para preparar la sustentación. |

## Aportes de otros cursos de la maestría (revisados en Moodle el 9-nov)

| Curso | Se aplica en |
|---|---|
| IA Generativa | Agente y *agentic workflows*, RAG, evaluación de eficiencia e impacto |
| Procesamiento de Lenguaje Natural | MCP, clasificador tipo BERT/DeBERTa (D16), embeddings (D15) |
| Electiva IV: Hackeando la IA | OWASP LLM, MITRE, hacking de LLM, métricas de ética (D43, D44) |
| Extracción y almacenamiento de datos | Crawling y extracción estructurada de Internet (corpus A), preprocesamiento (R.7.1) |
| MLOps | CI/CD, versionado, trazas (D17) |
| Electiva I: Computación en la nube | Despliegue de la demo (opcional, hoja de ruta) |
