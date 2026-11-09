# Estado del proyecto

## Siguiente sesión

**S03 — Arnés de evaluación y Streamlit mínimo** (jue 12-nov; ver `docs/PLAN.md`, sección S03).
S02 se cerró el 9-nov, con dos días de adelanto.

Siguiente paso exacto: escribir `arnes/correr.py` reutilizando `comercio_agentico.agente.grafo.preguntar` y
`preguntar.evaluar`/`registro_jsonl` (ya producen el JSONL por tarea). **Tareas en paralelo** (p. ej. 4 a la vez,
con un semáforo global de llamadas al LLM compartido entre tareas): una tarea tarda ~195 s con DeepSeek Flash, así
que 60 tareas en serie tomarían ~3 h. Después, M1 campo a campo contra `verdad.json` (las ofertas emparejadas
están en `Resultado.ofertas`), M2–M4 y M6, y la corrida de calibración de 60 tareas (~US$0,90). Consultar
Context7 para Streamlit antes de la app mínima.

## Presupuesto de modelos

| Concepto | US$ |
|---|---|
| Presupuesto total | 300,00 |
| Créditos comprados | 50,00 (Anthropic 30 + OpenRouter 20), 9-nov |
| Gastado acumulado | ~0,46 (S00: ~0,26 en ping, diagnóstico y mediciones de extracción; S01: 0,024 en el catálogo del corpus B; S02: ~0,18 en DeepSeek Flash, de ellos 0,076 la prueba de humo). OpenRouter informa 0,267 de uso total sobre US$20 al cierre de S02 |

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

### 9-nov-2026 — S02 Agente N2 y emparejamiento
- Herramientas: `abrir_pagina` (crawl4ai → Markdown + enlaces del mismo sitio), `leer_documento` (pypdf/texto),
  `consultar_mcp` (cliente de FastMCP: busca y trae la ficha completa). `langchain-mcp-adapters` 0.3.x se descartó
  por exigir `mcp<2` (D63). Registro de fuentes autorizadas en `fuentes/corpus_b.yaml`.
- `extraer_ofertas` con JSON Schema y validación por oferta (un GTIN inválido se descarta sin perder la oferta).
- Grafo LangGraph interpretar → planificar ⇄ herramientas → emparejar → proponer (D59): ReAct con datos
  estructurados en C1 y texto crudo en C0 (`--c0`); selección determinista del menor costo total (D61).
- Emparejamiento (D62): GTIN/MPN → `multilingual-e5-small` (CPU; PyTorch solo-CPU) top-5 → confirmación del LLM
  por lote. La interpretación resuelve el producto pedido con los mismos candidatos.
- Razonamiento con esfuerzo bajo en todos los modelos (D60); máximo 8000 tokens de salida y 120 s por llamada;
  3 llamadas simultáneas al LLM y reintento ante 429 en 5/15/30 s (DeepInfra limitó la tasa de Flash y de Kimi
  durante la sesión).
- `python -m comercio_agentico.preguntar` (consulta libre o `--tareas`), `make humo`, `make candidatos`.
- **Prueba de humo: 5/5 aciertos** (B001, B013, B025, B037, B054), procedencia completa en todas las ofertas,
  US$0,076 en total (~0,015 por tarea, ~195 s por tarea). Resultados en `resultados/humo_s02.jsonl`.
- Hallazgos: DeepSeek Flash con razonamiento por defecto gastó ~3000 tokens ocultos en una interpretación y, en una
  ocasión, entró en un bucle de generación (414 KB repitiendo el prompt en un campo de texto libre). Se eliminó el
  campo y se acotaron los tokens. Las variantes quedan casi empatadas en coseno (0,931 frente a 0,929).
- 18 pruebas nuevas (70 en total), incluida la de separación de planos; Ruff limpio.
- Informe: `docs/informe/03_metodologia_agente.md` (diagrama del grafo y tabla de la prueba de humo).

### 9-nov-2026 — S01 Corpus B sintético y tareas
- Catálogo de 40 productos (8 por categoría) generado con DeepSeek Flash en 5 llamadas (US$0,024). El LLM dejó
  copias de los alias dentro de `atributos` y escribió los TB decimales (1000 GB). Lo corrige `reparar()` de
  forma determinista, sin volver a llamar al modelo. El GTIN-13 lo asigna el código con el prefijo GS1 952, de demostración, verificado en la tabla oficial de prefijos (D58).
- Perfil ampliado a las 5 categorías (8 atributos nuevos).
- Generador determinista (semilla 20261110): 95 ofertas, 36 productos ofrecidos (18 en 3+ proveedores),
  4 sin oferta y 3 solo agotados. P1 por FastMCP 4.1.6, P2 HTML con JSON-LD, P3 HTML plano, P4 PDF (fpdf2,
  reproducible byte a byte) y P5 chat tipo WhatsApp. `make corpus-b-servir` sirve todo (probado en vivo).
- 60 tareas en `tareas/tareas_b.jsonl` (12/12/15/12/9), con respuesta de `calcular_respuesta()` sobre la verdad.
- 18 pruebas nuevas (52 en total) en verde; Ruff limpio. Dependencias nuevas: fastmcp, fpdf2, pypdf, jinja2.
- Informe: `docs/informe/03_metodologia_corpus.md`.

### 9-nov-2026 — Reorganización (entre S00 y S01)
- La raíz queda solo con el proyecto de código. Material del curso, entregables y contexto histórico movidos a
  `privado/` (fuera de git): `privado/curso/`, `privado/entregables/`, `privado/contexto_claude/` (D55).
- Nuevo pedido de Wills: cada sesión explica lo construido y deja instrucciones de prueba sin costo en
  `docs/GUIA_PRUEBAS.md` (D56). Sección de S00 ya escrita y verificada (demo sin red y 34 pruebas en verde).
- Nuevo documento `privado/ENTENDER_EL_PROYECTO.md` con la explicación de todo lo hecho (planeación y S00); cada
  sesión agrega su entrada (D57).

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
- Latencia: ~195 s por tarea con DeepSeek Flash. E3 necesita tareas en paralelo (S03) y reintentos ante el límite de
  tasa de DeepInfra (Kimi devolvió 429 durante S02).
- Año de la conferencia de ReAct (versión de ICLR, arXiv:2210.03629) por confirmar en S10.
- Archify (diagrama de arquitectura del estándar del profesor) como opción en S09 para el informe.
