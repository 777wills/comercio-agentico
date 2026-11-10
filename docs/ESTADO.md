# Estado del proyecto

## Siguiente sesión

**S04 — Corpus A real** (jue 12 / vie 13-nov; ver `docs/PLAN.md`, sección S04), **precedida por la corrección
del intérprete y la calibración v2** (D69). S03 se cerró el 9-nov, con tres días de adelanto.

Siguiente paso exacto:
1. Aplicar `_todos_obligatorios` (de `esquema.py`) a `Necesidad` y `RestriccionAtributo`
   (`agente/interpretacion.py`) y a `Decisiones` (`emparejamiento.py`). Agregar en `interpretar()` un reintento
   ante `OutputParserException` (JSON truncado) y, si falla de nuevo, una necesidad mínima con alerta. Pruebas sin
   red de ambos caminos. Revisar con Context7 el manejo de errores de `with_structured_output`.
2. `make corpus-b-servir` y `make calibracion` (~US$0,9, ~45 min; las corridas v0 y v1 ya tienen sufijo, así
   que la v2 no se reanuda sobre ellas). Renombrar la nueva a `_v2` al terminar. Comparar v0 → v1 → v2 en `docs/informe/04_resultados_calibracion.md`. Meta: la necesidad vacía en 19/27 debe
   bajar a casi 0; revisar las tareas vagas.
3. Seguir con S04.

## Presupuesto de modelos

| Concepto | US$ |
|---|---|
| Presupuesto total | 300,00 |
| Créditos comprados | 50,00 (Anthropic 30 + OpenRouter 20), 9-nov |
| Gastado acumulado | ~2,20 (S00: ~0,26; S01: 0,024; S02: ~0,18; S03: 1,74 en DeepSeek Flash: dos calibraciones de 60 tareas, 0,81 + 0,89, y sondeos de diagnóstico por menos de US$0,01). OpenRouter informa 2,009 de uso total sobre US$20 al cierre de S03 |

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

### 9-nov-2026 — S03 Arnés de evaluación y Streamlit mínimo
- `arnes/correr.py`: configuración YAML (`configs/calibracion_flash.yaml`), 4 tareas en paralelo con un semáforo
  de llamadas al LLM compartido (6), JSONL por ejecución con versión de prompt (SHA-256 de instrucciones y
  esquemas), hash del corpus y de las tareas, commit, tokens, costo y latencia, más todas las ofertas recolectadas.
  Reanuda si se interrumpe (se probó: la sesión se cortó a las 24/60 y la corrida siguió sin repetir nada).
- `arnes/metricas.py`: M1 por fuente (campo a campo; los listados solo en precio), recolección, M2, M3, M4, M6;
  Wilson y *bootstrap* (scipy). `metricas.md`, `metricas.json` y 3 PNG por corrida en `resultados/informes/`.
- `arnes/simulado.py`: agente oráculo con errores sembrados; las pruebas verifican que las métricas los encuentran
  exactamente. `make arnes-simulado` (US$0).
- `app.py` (Streamlit): consulta, cuadro comparativo y procedencia desplegable; modo simulado a US$0. `make app`.
- Subconjunto E3 congelado antes de ver resultados: `tareas/subconjunto_e3.jsonl`, 30 tareas (D64).
- **Calibración v0** (`..._v0.jsonl.gz`, prompt `4dfdd15ebbcf`): M2 52/60, M1 86,3 %, US$0,81, p50 146 s. **Hallazgo:** Flash omitía
  GTIN, MPN y marca en el 100 % de las ofertas (campos opcionales del esquema). Corrección D66 (campos
  obligatorios) y D67 (regla de existencias solo en mensajes).
- **Calibración v1** (`..._v1.jsonl.gz`, prompt `724697af2251`): M2 49/60 [70,1–89,4] (dentro del ruido frente a v0), M1 95,7 %,
  identificadores de P1 99–100 %, US$0,89, p50 179 s, p90 255 s. **Hallazgo:** el intérprete devuelve la necesidad
  vacía en 19/27 tareas con criterios; es la causa principal de los fallos (D69, al inicio de la próxima sesión).
- Corridas versionadas comprimidas (`.jsonl.gz`, ~250 KB frente a ~3 MB; el hook de pre-commit limita a 2 MB);
  el `.jsonl` queda fuera de git y sirve para reanudar.
- 13 pruebas nuevas (83 en total); Ruff limpio. Dependencia nueva: matplotlib (scipy pasa a usarse directamente).
- Informe: `docs/informe/03_metodologia_metricas.md` y `docs/informe/04_resultados_calibracion.md`.

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
- Corrección del intérprete y calibración v2 (D69), antes de S04.
- Referencias de Wilson (1927) y Efron (1979) para los intervalos: verificar en la fuente primaria en S10.
- Comprobar que el arnés soporta la concurrencia con Kimi y Opus (límite de tasa) antes de E3.
- Año de la conferencia de ReAct (versión de ICLR, arXiv:2210.03629) por confirmar en S10.
- Archify (diagrama de arquitectura del estándar del profesor) como opción en S09 para el informe.
