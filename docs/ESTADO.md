# Estado del proyecto

## Siguiente sesión

**S06 — N4 defensa y suite adversarial** (`docs/PLAN.md`, sección S06). S05 se cerró el 10-nov, con tres días de
adelanto.

Siguiente paso exacto:
1. Verificar con Context7 y en la fuente primaria la taxonomía MITRE pertinente (ATLAS) y OWASP LLM01 (versión
   vigente) antes de escribir `ataques/mapeo.md`.
2. Diseñar las 20 cargas (5 clases × 4 ubicaciones) con su predicado de éxito verificable por programa; usar el
   `llms.txt` de Alkosto como caso real documentado.
3. Elegir el clasificador de inyección de Hugging Face para C2 (licencia, tamaño, latencia en CPU) y proponerlo a
   Wills con opciones antes de integrarlo.
4. Prueba de humo: 1 carga por clase en C0 y C3, con DeepSeek Flash (modelo base, D79).
5. Corridas largas: lanzarlas con `systemd-inhibit --what=sleep` (el equipo se suspendió a mitad de E3).

## Presupuesto de modelos

| Concepto | US$ |
|---|---|
| Presupuesto total | 300,00 |
| Créditos comprados | 50,00 (Anthropic 30 + OpenRouter 20), 9-nov. Anthropic: US$29,83 disponibles y US$0,17 gastados (consola, 9-nov 21:43) |
| Gastado acumulado | ~9,2 (S00: ~0,26; S01: 0,024; S02: ~0,18; S03: 1,74; S04: ~1,32; S05: ~5,7 = corpus A v1 0,361 + calibración v3 0,919 + E3 Flash 1,371 + E3 Haiku 1,528 + corrida parcial de Flash descartada 1,312 + ~0,2 de llamadas perdidas en la suspensión). OpenRouter: 7,46 de 20 usados (10-nov). Anthropic: ~US$28,3 disponibles tras Haiku |

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
~~recargar ~US$40 en Anthropic~~ (sustituido por D76: E3 llega hasta Sonnet y Opus requiere autorización; los US$29,83 alcanzan). OpenRouter (US$20) alcanza para los tres modelos
chinos. El total sigue muy por debajo de US$300. Riesgos: las páginas reales del corpus A pueden ser mucho más
largas que la de prueba (recalibrar en S03 con el arnés), y Opus queda cerca del tope `COSTO_MAXIMO_POR_TAREA_USD`
= 0,50: subirlo a 1,00 solo para las corridas de Opus en E3.

El `.env` nunca se lee ni se muestra en las sesiones: las claves se cargan en un subproceso.

## Bitácora

### 9/10-nov-2026 — Cierre de S04 (D74, D75) y S05 E3
- **D74:** `abrir_pagina` antepone al Markdown los objetos schema.org `Product`/`Offer` (JSON-LD y microdatos,
  `extruct`; tope 6000 caracteres). Context7 confirmó que `CrawlResult.html` es el HTML original. **Corpus A v1:
  19/20 = 95,0 % [76,4–99,1]** (v0: 8/20); disponibilidad 43 % → 96 %; US$0,361. El fallo A003 es de planificación
  (no abre la ficha de Falabella). Efecto secundario: el GTIN extraído en A1/A2 cae de 35/62 a 1/67 porque
  schema.org lo etiqueta `sku` (hallazgo para N3).
- **D75:** `valor_canonico` toma la primera cifra y la unidad siguiente (`MB/s` incluido; punto de miles) y
  booleanos tolerantes (contradictorios se descartan). **Calibración v3: 58/60 = 96,7 % [88,6–99,1]**, US$0,919;
  recuperó B029, B032, B033, B036, B039. Fallan B031 y B035 (vagas: traducción discutible de la cifra).
- **E3 (D77 fijada antes de correr):** Flash 88,9 % [80,7–93,9], rango 10,0 pp, US$0,0152, p50 129 s; Haiku 90,0 %
  [82,1–94,6], rango 6,7 pp, US$0,0170, p50 56 s. ΔM2 +1,1 pp < ruido 10 pp → **se para (D78)**. **Modelo base:
  DeepSeek Flash (D79)**. `arnes/e3.py` (`make e3`, `make e3-frontera`), `configs/e3_*.yaml`.
- Incidente: el equipo se suspendió a las 23:15 con E3-Flash en 84/90; al reanudar pasada la medianoche, el arnés
  creó un archivo con la fecha nueva y empezó de cero (US$1,31 desperdiciados). Corregido: `ruta_salida` reanuda
  la corrida sin terminar con el mismo nombre aunque sea de otro día.
- 19 pruebas nuevas (113 en total); Ruff limpio.
- Informe: sección 4.y de `04_resultados_corpus_a.md`, v3 en `04_resultados_calibracion.md`,
  `04_resultados_e3.md` nuevo.

### 9-nov-2026 — Corrección del intérprete (D69, D71) y S04 Corpus A real
- `invocar_estructurado` (reintento ante JSON inválido o truncado y degradación controlada con la alerta
  `interpretacion_incompleta`); esquemas con todos los campos obligatorios en `Necesidad`, `RestriccionAtributo`,
  `Decision` y `Decisiones`. Context7 confirmó que, sin `include_raw`, el parser lanza la excepción.
- **Calibración v2** (`..._v2.jsonl.gz`): M2 54/60 = 90,0 % [79,9–95,3] (v1 81,7 %), necesidad vacía 3/27 (v1
  19/27), US$0,0156 por tarea, p50 161 s. B029 abortó con `float("4K")` (restricción de orden sobre categoría): se
  corrigió (D71) y se repitió la tarea. Cinco de los seis fallos son tareas vagas; cuatro por valores con basura
  (D75).
- Corpus A (D70, D72): robots.txt y términos de 5 tiendas; Éxito (429 de Cloudflare) y Olímpica (TyC 2.4.1)
  excluidas; Alkosto, Ktronix y Falabella prohíben copiar contenido, así que se guardan hechos y se reconstruyen las
  tiendas. 75 fichas leídas (crawl4ai HTTP + `extruct`), 24 productos, 61 ofertas, 70 páginas, 20 tareas.
  Hallazgos: Falabella sin GTIN, precio CMR condicionado, un arreglo de precios por variante, 8 distractores, Alkosto
  y Ktronix con precios idénticos. El `llms.txt` de Alkosto trae «Instrucciones para el modelo de lenguaje»
  comerciales: evidencia real para S06.
- **Corpus A, línea base** (`2026-11-09_corpus_a_flash_v0`): M2 8/20 = 40,0 % [21,9–61,3]; recolección 33/33;
  emparejamiento con Falabella correcto. Causa: la lectura Markdown pierde los datos schema.org, donde las tiendas
  publican la disponibilidad (D74).
- Arnés por corpus (`corpus: a|b`, D73). Dependencia nueva: extruct. 11 pruebas nuevas (94 en total); Ruff limpio.
- Informe: sección 3.z de `03_metodologia_corpus.md`, v2 en `04_resultados_calibracion.md`, `04_resultados_corpus_a.md`.

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
- E3 se detuvo en Haiku (D78): DeepSeek Pro, Kimi, Sonnet y Opus van como propuestos en la hoja de ruta del informe.
- Usar el `llms.txt` de Alkosto (instrucciones dirigidas al LLM) como caso real en S06.
- Referencias de Wilson (1927) y Efron (1979) para los intervalos: verificar en la fuente primaria en S10.
- La verificación N3 (S08) no debe suponer el GTIN en la oferta extraída: en el corpus A llega como `sku` en schema.org.
- Planificador: en A003 no abre la ficha cuando el listado no trae disponibilidad (candidato a mejora o limitación declarada).
- Año de la conferencia de ReAct (versión de ICLR, arXiv:2210.03629) por confirmar en S10.
- Archify (diagrama de arquitectura del estándar del profesor) como opción en S09 para el informe.
