# Estado del proyecto

## Siguiente sesión

**S01 — Corpus B sintético y tareas** (mar 10-nov; ver `docs/PLAN.md`, sección S01).

Siguiente paso exacto: generar el catálogo de referencia (~40 productos: portátiles, monitores, celulares,
audífonos, almacenamiento) con `obtener_extractor("deepseek-flash", ...)` o Haiku, validarlo con `OfertaExtraida`
y `gtin_valido`, y ampliar `perfiles/electronica.yaml` con los atributos que falten para esas categorías (p. ej.
procesador, frecuencia de refresco, cancelación de ruido). Antes de escribir FastMCP, consultar Context7.

## Presupuesto de modelos

| Concepto | US$ |
|---|---|
| Presupuesto total | 300,00 |
| Créditos comprados | 50,00 (Anthropic 30 + OpenRouter 20), 9-nov |
| Gastado acumulado | ~0,26 (S00: ping de los 6 modelos, diagnóstico y dos mediciones de extracción en los 6) |

Costo medido el 9-nov (S00) de una extracción estructurada típica (página con 12 ofertas, 1500–3500 tokens de
entrada, `json_schema`): Flash 0,0015 · Haiku 0,0016 · DeepSeek Pro 0,006 · Sonnet 0,025 · Kimi 0,032 ·
Opus 0,053. Supuesto de tarea: 5 extracciones + ~8 llamadas del planificador (~4000 tokens de entrada y ~300 de
salida cada una).

| Modelo | US$ por tarea (estimado) | 80 tareas (B + A) |
|---|---|---|
| DeepSeek V4.1 Flash | ~0,013 | ~1 |
| Claude Haiku 5.5 | ~0,013 | ~1 |
| DeepSeek V4 Pro | ~0,08 | ~6 |
| Claude Sonnet 5.5 | ~0,21 | ~17 |
| Kimi K3.1 Pro | ~0,24 | ~19 |
| Claude Opus 5.5 | ~0,44 | ~35 |

Recalibración: la estimación anterior (0,03–0,18 por tarea) se queda corta en el tope. Si la regla de parada de
E3 llega a Opus con todas las tareas, Anthropic necesita ~US$55 (Haiku + Sonnet + Opus) más desarrollo, E2 y E1:
**recargar ~US$40 en Anthropic antes de correr Sonnet en S05**. OpenRouter (US$20) alcanza para los tres modelos
chinos. El total sigue muy por debajo de US$300. Riesgos: las páginas reales del corpus A pueden ser mucho más
largas que la de prueba (recalibrar en S03 con el arnés), y Opus queda cerca del tope `COSTO_MAXIMO_POR_TAREA_USD`
= 0,50: subirlo a 1,00 solo para las corridas de Opus en E3.

El `.env` nunca se lee ni se muestra en las sesiones: las claves se cargan en un subproceso.

## Bitácora

### 9-nov-2026 — Reorganización (entre S00 y S01)
- La raíz queda solo con el proyecto de código. Material del curso, entregables y contexto histórico movidos a
  `privado/` (fuera de git): `privado/curso/`, `privado/entregables/`, `privado/contexto_claude/` (D55).
- Nuevo pedido de Wills: cada sesión explica lo construido y deja instrucciones de prueba sin costo en
  `docs/GUIA_PRUEBAS.md` (D56). Sección de S00 ya escrita y verificada (demo sin red y 34 pruebas en verde).

### 9-nov-2026 — S00 Arranque técnico
- Proyecto `uv` en Python 3.13.16 (D53) con LangGraph 1.2.20, LangChain 1.4.9, langchain-anthropic 1.7.10,
  langchain-openrouter 0.2.9, crawl4ai 0.9.5, Streamlit 1.67.0, Pydantic 2.12.5; `uv.lock` versionado.
- `modelos.py`: fábrica de los 6 modelos, proveedor DeepInfra fijado sin respaldo (D34, verificado con la API de
  generaciones), `RegistroCosto` (tokens, costo de la API o de la tabla, proveedor, tope por tarea) y
  `obtener_extractor` con `json_schema` (D35). Claude 5.5 no acepta `temperature` (D36).
- `make ping`: los 6 modelos responden con tool-calling (latencia 1,5–3,6 s).
- `esquema.py`: `OfertaExtraida` (lo que produce el LLM), `Procedencia` (la escribe el código; SHA-256 del
  fragmento), `Oferta`, `PerfilCategoria` con normalización de unidades y categorías, `PropuestaCompra` con
  abstención coherente; GTIN validado por dígito de control. `perfiles/electronica.yaml`.
- 34 pruebas sin red, Ruff y pre-commit en verde.
- Revisión de la skill `jan-project-standard` del profesor Jan Polanco: adopción parcial (D52): Ruff,
  pre-commit, Makefile, CI, LICENSE MIT, README con badges, CONSTITUTION breve.
- Observación útil para E3: con `json_schema`, DeepSeek Flash extrajo 13 ofertas en vez de 12 y no marcó las
  agotadas; los otros cinco acertaron 12/12.
- Repositorio público `777wills/comercio-agentico` (D54).
- Informe: `docs/informe/03_metodologia_stack.md`.

### 9-nov-2026 — Sesión de planeación
- Entrevista completa con Wills; todas las decisiones registradas en `docs/DECISIONES.md` (D01–D51).
- Revisión de la rúbrica `Rubrica_PAIII_2026.xlsx`: mismos criterios que la versión CSV usada en septiembre.
- Confirmado en el aula virtual: documento y presentación finales se radican al menos una semana antes del 27-nov.
- Investigación de modelos chinos y plataformas de créditos (precios del 9-nov en DECISIONES, D30–D33).
- Revisión de los cursos de la maestría en Moodle; aportes aplicables en DECISIONES.
- Creados: `CLAUDE.md` actualizado, `docs/PLAN.md`, `docs/DECISIONES.md`, `docs/ESTADO.md`,
  `docs/PROMPT_SESION.md`, `.gitignore`; repositorio git local inicializado.

## Pendientes abiertos

- Plantilla institucional de trabajo escrito (IEEE): Wills la descarga del aula y la pone en `privado/curso/` antes de S10.
- Verificar en S06 si la taxonomía MITRE pertinente es ATLAS.
- Informe primario de la CCCE (primer trimestre de 2026), si se cita en el informe.
- Verificación exhaustiva de las referencias del plan de trabajo antes de reutilizarlas (S10).
- Recargar ~US$40 en Anthropic antes de Sonnet en S05 (Wills).
- Archify (diagrama de arquitectura del estándar del profesor) como opción en S09 para el informe.
