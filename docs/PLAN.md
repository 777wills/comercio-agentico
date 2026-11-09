# Plan de ejecución por sesiones — 9 al 19 de noviembre de 2026

Cada sesión es una unidad de trabajo con un entregable verificable. Una sesión **no termina** hasta cumplir su
criterio de terminado y hacer el cierre de `CLAUDE.md`. Si una sesión se alarga o el contexto se llena, se hace corte
limpio en el último punto estable y la siguiente sesión retoma desde `docs/ESTADO.md`.

## 1. Principios (resumen; detalle en `CLAUDE.md`)

1. Simplicidad: librerías existentes, MVP de punta a punta primero, profesionalizar después.
2. La IA primero; lo determinista al final o como propuesto.
3. Créditos: desarrollo con el modelo más barato; caros solo en experimentos.
4. Context7 antes de escribir código contra una librería.
5. Cada sesión deja su borrador de sección del informe en `docs/informe/`.

## 2. Arquitectura objetivo (MVP)

```
Consulta en lenguaje natural (Streamlit)
        │
        ▼
Agente LangGraph (planificador)  ── solo ve instrucciones del usuario y datos ya extraídos (N4: separación de planos)
        │ herramientas
        ├─ abrir_pagina(url)        → crawl4ai/Playwright → Markdown          (web schema.org, web plana, corpus A)
        ├─ leer_documento(ruta)     → texto de PDF / mensaje tipo WhatsApp
        ├─ consultar_mcp(...)       → proveedor sintético por MCP (FastMCP)
        └─ extraer_ofertas(fragmento) → LLM con salida estructurada → [Oferta] con Procedencia
                 │
                 ├─ N4 defensa: C1 planos · C2 clasificador HF · C3 verificación cruzada de precio · (C4 lista blanca)
                 ├─ Emparejamiento: GTIN exacto, o embeddings del catálogo + confirmación LLM, o abstención
                 └─ N3 verificación: re-extracción por ruta independiente sobre la procedencia guardada
        │
        ▼
Propuesta de compra trazable (cuadro comparativo + procedencia + alertas). No ejecuta pagos.
```

## 3. Estructura del repositorio (se crea en S00 y crece por sesión)

```
pyproject.toml              # uv
.env.example                # ANTHROPIC_API_KEY, OPENROUTER_API_KEY
src/comercio_agentico/
  esquema.py                # Pydantic: Oferta, Procedencia, PerfilCategoria, PropuestaCompra
  modelos.py                # fábrica de LLM por nombre (Anthropic / OpenRouter) + registro de costo
  agente/                   # grafo LangGraph y herramientas
  emparejamiento.py         # GTIN + embeddings del catálogo
  defensa/                  # C1–C4
  verificacion.py           # N3
  fuentes/                  # N1 (al final)
perfiles/electronica.yaml   # perfil de categoría declarativo
corpus/b_sintetico/         # catálogo, generador, proveedores, verdad de referencia
corpus/a_real/              # crawler + manifest.json (copias fuera de git)
tareas/                     # tareas_b.jsonl, tareas_a.jsonl
ataques/                    # suite adversarial y su mapeo OWASP/MITRE
arnes/                      # ejecutor de corridas y métricas M1–M6
resultados/                 # corridas versionadas (jsonl) y figuras
app/streamlit_app.py
tests/
docs/                       # plan, estado, decisiones, guía de pruebas, informe por partes
privado/                    # fuera de git: material del curso, entregables, contexto histórico
```

## 4. Calendario

| Sesión | Fecha objetivo | Tema | Rúbrica que alimenta |
|---|---|---|---|
| S00 | lun 9-nov | Arranque técnico: repo, entorno, modelos, esquema | R.7.1 Cr2 |
| S01 | mar 10-nov | Corpus B sintético + tareas con verdad conocida | R.6.1 Cr3, R.7.1 Cr1 |
| S02 | mié 11-nov | Agente N2 + emparejamiento → **MVP de punta a punta** | R.6.1 Cr3, RA2 del curso |
| S03 | jue 12-nov | Arnés de evaluación y métricas + Streamlit mínimo | R.6.1 Cr4, R.6.2 Cr6 |
| S04 | jue 12 / vie 13-nov | Corpus A real (crawling de tiendas colombianas) | R.7.1 Cr1, Cr3 |
| S05 | vie 13-nov | **E3** modelos con escalamiento y regla de parada | R.6.1 Cr2, Cr4 |
| S06 | sáb 14-nov | N4 defensa (C1–C3) + suite adversarial | R.6.2 Cr7 |
| S07 | dom 15-nov | **E2** curva seguridad-utilidad | R.6.2 Cr7, R.6.1 Cr4 |
| S08 | lun 16-nov | N3 verificación + **E1**; N1 si sobra tiempo | R.6.1 Cr4, R.6.2 Cr6 |
| S09 | mar 17-nov | App Streamlit final + MLOps ligero + README | R.6.2 Cr8, R.7.2 |
| S10 | mié 18-nov | Informe IEEE completo (borrador → PDF) | RA1 comunicación escrita |
| S11 | jue 19-nov | Auditoría contra rúbrica, presentación de 5 láminas, radicación | RA1, RA2 oral |
| S12 | 21–26-nov | Video de 10 min, ensayo de preguntas, pulido de la demo | RA2 oral |

**Recortes de contingencia, en este orden, si hay atraso:** C4 → N1 → Opus en E3 (si la regla de parada no lo
exige, ya queda fuera) → corpus A de 20 a 10 tareas → E1 se reduce a una ablación sobre el corpus B. Nunca se recorta
E2 ni E3.

## 5. Prerrequisitos que dependen de Wills

- [ ] Comprar créditos (estimación inicial, se recalibra en S00 midiendo tokens reales): Anthropic ~US$60,
      OpenRouter ~US$40. Presupuesto total máximo: US$300. Comprados US$50 el 9-nov; recarga de Anthropic
      antes de Sonnet/Opus en S05 (ver `docs/ESTADO.md`).
- [x] Crear `.env` con `ANTHROPIC_API_KEY` y `OPENROUTER_API_KEY` (S00).
- [ ] Descargar la plantilla institucional de trabajo escrito (IEEE) del aula y ponerla en `privado/curso/` (antes de S10).
- [x] Confirmar la creación del repositorio público en GitHub (S00): `777wills/comercio-agentico`.

---

## S00 — Arranque técnico (lun 9-nov)

**Objetivo:** entorno reproducible, los 6 modelos respondiendo y el esquema canónico definido.

- [x] `uv init` con Python 3.12 (o 3.13 si todas las dependencias lo soportan; 3.14 del sistema puede no tener
      ruedas para todo). Dependencias: langgraph, langchain, langchain-anthropic, langchain-openai (OpenRouter vía
      base_url) o la integración oficial de OpenRouter si Context7 la confirma, pydantic, crawl4ai, streamlit,
      pytest, python-dotenv.
- [x] Verificar con Context7: API vigente de LangGraph (agente ReAct prebuilt vs. `create_agent` de LangChain 1.x),
      salida estructurada en LangChain, integración de OpenRouter y cómo obtener el costo por llamada.
- [x] `src/comercio_agentico/modelos.py`: `obtener_modelo(nombre)` para los 6 modelos de D31; registro de tokens y
      costo por llamada; proveedor fijado en OpenRouter (D32).
- [x] Script `python -m comercio_agentico.ping`: una llamada con tool-calling a cada modelo; imprime latencia y costo.
- [x] `esquema.py`: `Oferta` (inspirada en schema.org Product + Offer: gtin, mpn, marca, modelo, título, precio,
      moneda, disponibilidad, condiciones de entrega), `Procedencia` (fuente, consulta, marca de tiempo, fragmento
      original, ruta de extracción, suma de verificación), `PerfilCategoria`, `PropuestaCompra`.
- [x] `perfiles/electronica.yaml`: atributos comparables, restricciones duras, normalización de unidades,
      identificador de emparejamiento.
- [x] Pruebas unitarias del esquema y del perfil.
- [x] `.gitignore` verificado, `.env.example`, README mínimo; repo público en GitHub con confirmación de Wills.
- [x] Estimar el costo por tarea con una llamada típica y recalibrar el presupuesto en `docs/ESTADO.md`.

Cumplido el 9-nov: Python 3.13 (D53), DeepInfra fijado (D34), `json_schema` (D35), estándar del profesor
(D52). Costo por tarea en `docs/ESTADO.md`.

**Terminado cuando:** `ping` responde en los 6 modelos con tool-calling y `pytest` pasa.
**Informe:** `docs/informe/03_metodologia_stack.md` (stack y justificación de la simplicidad).

## S01 — Corpus B sintético y tareas (mar 10-nov)

**Objetivo:** cinco proveedores heterogéneos servidos en local, con verdad de referencia por construcción.

- [x] Catálogo de referencia: ~40 productos de electrónica (portátiles, monitores, celulares, audífonos,
      almacenamiento) con atributos completos y GTIN-13 con dígito de control válido. Generado con LLM y validado
      por programa (Pydantic + dígito de control).
- [x] Generador (LLM barato + plantillas) que reparte el catálogo entre 5 proveedores, con precios, existencias y
      condiciones distintos, solapamiento parcial y nomenclatura propia de cada uno:
  - [x] P1 MCP: servidor FastMCP con `buscar_productos` y `detalle_producto`.
  - [x] P2 web con schema.org (JSON-LD Product/Offer), HTML estático.
  - [x] P3 web plana sin marcado, nombres comerciales, sin GTIN.
  - [x] P4 lista de precios en PDF (tabla; sin GTIN; abreviaturas).
  - [x] P5 mensajes tipo WhatsApp (texto informal, precios en el cuerpo, "8/512", "ryzen5").
- [x] Servidor local de los sitios (http.server o equivalente) y script de arranque único.
- [x] `verdad.json`: para cada proveedor y producto, la oferta exacta (lo que debería extraerse).
- [x] ~60 tareas en `tareas/tareas_b.jsonl` generadas por programa desde la verdad, en categorías (inspiradas en la
      taxonomía de WebMall): búsqueda específica por modelo, más barato entre proveedores, búsqueda con restricciones
      (presupuesto, especificación mínima, entrega), búsqueda vaga, caso sin respuesta (debe abstenerse). Respuesta de
      referencia calculada, no manual.
- [x] Pruebas: cada tarea tiene respuesta derivable de `verdad.json`.

**Terminado cuando:** los 5 proveedores sirven contenido y las 60 tareas tienen respuesta de referencia validada.
**Informe:** `docs/informe/03_metodologia_corpus.md`.

## S02 — Agente N2 y emparejamiento: MVP de punta a punta (mié 11-nov)

**Objetivo:** una consulta en lenguaje natural produce una propuesta de compra trazable sobre el corpus B.

- [x] Herramientas: `abrir_pagina` (crawl4ai → Markdown), `leer_documento` (PDF y texto), cliente MCP
      (langchain-mcp-adapters o equivalente que confirme Context7), `extraer_ofertas` (LLM con salida estructurada
      → `[Oferta]` + `Procedencia`).
- [x] Grafo LangGraph: planificar → recolectar por fuente → extraer → emparejar → filtrar restricciones duras del
      perfil → proponer. Estado explícito; límite de pasos y de costo por tarea.
- [x] **Desde el inicio**, el contenido de terceros entra solo por `extraer_ofertas` y vuelve al planificador como
      datos estructurados (deja lista la separación de planos de C1 sin costo extra; C0 se obtiene pasando el texto
      crudo al planificador).
- [x] Emparejamiento (D15): GTIN exacto si existe; si no, embeddings del catálogo (modelo multilingüe local,
      verificar con Context7 / Hugging Face), los 3–5 más parecidos y confirmación del LLM; si no hay certeza,
      abstención.
- [x] Ejecución por línea de comandos: `python -m comercio_agentico.preguntar "..."`.
- [x] Prueba de humo sobre 5 tareas del corpus B con el modelo más barato.

**Terminado cuando:** las 5 tareas de humo producen propuestas con procedencia completa por oferta.
**Informe:** `docs/informe/03_metodologia_agente.md` (diagrama del grafo).

## S03 — Arnés de evaluación y Streamlit mínimo (jue 12-nov)

**Objetivo:** cualquier configuración se evalúa con un comando y produce métricas sin juicio humano.

- [ ] `arnes/correr.py --config <yaml> --tareas <jsonl> --repeticiones N`: ejecuta en paralelo moderado, guarda cada
      corrida en `resultados/corridas/<fecha>_<config>.jsonl` con modelo, proveedor, versión de prompt, hash del
      corpus, commit, tokens, costo y latencia.
- [ ] Métricas: M1 exactitud de extracción por ruta (campo a campo contra `verdad.json`), M2 éxito por categoría de
      tarea, M3 acuerdo entre ejecuciones, M4 abstención (y exactitud sobre lo cubierto), M6 costo por tarea y
      latencia p50/p90. Intervalos de confianza (Wilson o bootstrap).
- [ ] Tabla resumen y gráficos básicos (matplotlib) en `resultados/`.
- [ ] Corrida de calibración: 60 tareas × 1 repetición con el modelo barato. Fija el subconjunto estratificado de ~30
      tareas para E3 (y lo congela en `tareas/subconjunto_e3.jsonl`).
- [ ] Streamlit mínimo: caja de consulta, cuadro comparativo, procedencia expandible.

**Terminado cuando:** la corrida de calibración genera el informe de métricas completo y la app responde una consulta.
**Informe:** `docs/informe/03_metodologia_metricas.md` + primeros números en `04_resultados_calibracion.md`.

## S04 — Corpus A real (jue 12 / vie 13-nov)

**Objetivo:** validez externa con tiendas colombianas reales, de forma legal y reproducible.

- [ ] Revisar robots.txt y términos de 4–5 tiendas candidatas (D20); elegir 3 y documentar las exclusiones como
      resultado.
- [ ] Crawler con crawl4ai: agente identificable, límite de tasa, sin credenciales ni elusión de CAPTCHA; congelar
      ~60–100 páginas de producto de los mismos tipos del catálogo, con fecha y suma de verificación.
- [ ] `corpus/a_real/manifest.json` versionado; las copias, fuera de git (D22).
- [ ] Servir las copias congeladas en local para que el agente las navegue como si fueran el sitio.
- [ ] ~20 tareas reales en `tareas/tareas_a.jsonl`. Verdad de referencia: GTIN y precio desde el JSON-LD de la copia
      cuando exista (extracción determinista); revisión humana rápida de Wills solo sobre los casos dudosos.
- [ ] Corrida del agente sobre el corpus A con el modelo barato.

**Terminado cuando:** las 20 tareas reales tienen referencia y una corrida completa con métricas.
**Informe:** sección de corpus A en `03_metodologia_corpus.md` y resultados en `04_resultados_corpus_a.md`.

## S05 — E3: comparación de modelos con escalamiento (vie 13-nov)

**Objetivo:** frontera costo-desempeño y elección del modelo base, gastando solo lo necesario.

- [ ] Configuración base fija (sin defensa adicional a C1, sin N3); solo cambia el modelo.
- [ ] Orden D31. Por modelo: subconjunto de 30 tareas × 3 repeticiones; M2 por categoría, M3, M4, M6.
- [ ] Regla de parada D42 aplicada y documentada en cada paso (qué se midió, qué ruido, por qué se subió o se paró).
- [ ] Gráfico de frontera costo-desempeño (costo por tarea vs. M2) y tabla con intervalos.
- [ ] Elegir el modelo base con argumento (desempeño, costo, latencia, pesos abiertos) y registrar en DECISIONES.

**Terminado cuando:** hay modelo base decidido con evidencia y la figura de la frontera.
**Informe:** `04_resultados_e3.md` (alimenta Cr2: argumentación de la elección del modelo).

## S06 — N4 defensa y suite adversarial (sáb 14-nov)

**Objetivo:** cuatro configuraciones de defensa y 20 cargas de ataque listas para medir.

- [ ] Suite: 5 clases (desviar la compra hacia un proveedor, inflar cantidades, exfiltrar el presupuesto u otros
      datos del mandato, saltarse la confirmación humana, alterar el precio comparado) × 4 cargas (variando
      ubicación y forma: texto visible, oculto en HTML, en el PDF, en el mensaje). Cada carga con su **predicado de
      éxito verificable por programa**.
- [ ] Mapeo de cada clase a OWASP LLM01 y a la técnica MITRE pertinente (verificar si es ATLAS) en
      `ataques/mapeo.md`.
- [ ] Variantes del corpus B con las cargas plantadas (copia por carga; la versión limpia no se toca).
- [ ] Configuraciones: C0 (texto crudo al planificador), C1 (separación de planos), C2 (C1 + clasificador de
      inyección de Hugging Face sobre cada fragmento; verificar licencia, tamaño y latencia en CPU), C3 (C2 +
      verificación cruzada de precio contra los demás proveedores y el rango del catálogo). C4 lista blanca solo si
      sobra tiempo.
- [ ] Prueba de humo: 1 carga por clase en C0 y C3.

**Terminado cuando:** las 20 cargas y C0–C3 corren y el predicado de éxito se evalúa por programa.
**Informe:** `03_metodologia_seguridad.md` (taxonomía, mapeo, configuraciones).

## S07 — E2: curva seguridad-utilidad (dom 15-nov)

**Objetivo:** el resultado estrella del proyecto.

- [ ] Para cada configuración C0–C3 con el modelo base: utilidad = M2 sobre las tareas benignas; seguridad = 1 − tasa
      de éxito del ataque (M5) sobre las 20 cargas (3 repeticiones si el presupuesto lo permite).
- [ ] Curva seguridad-utilidad, frontera de Pareto y codo; costo y latencia añadidos por cada capa.
- [ ] Análisis por clase de ataque y por nivel de madurez del proveedor donde se plantó.
- [ ] Opcional si sobra presupuesto: repetir C0 y C3 con un segundo modelo de otro proveedor para ver si el efecto
      de la defensa se sostiene.

**Terminado cuando:** existe la figura de la curva con intervalos y su interpretación escrita.
**Informe:** `04_resultados_e2.md`.

## S08 — N3 verificación, E1 y N1 opcional (lun 16-nov)

**Objetivo:** medir el aporte de la verificación.

- [ ] N3: re-extracción por una ruta independiente sobre el fragmento guardado en la procedencia (otro prompt y otro
      modelo, o el parser determinista de JSON-LD cuando exista). Si las rutas discrepan, la oferta se marca como no
      verificada y se declara.
- [ ] E1: con y sin N3 (y con y sin N1 si se implementa) sobre corpus B y A: M1, M2, M4 (cobertura vs. exactitud
      sobre lo cubierto) y M6.
- [ ] N1 solo si hay tiempo: lector de JSON-LD (trivial) y, si una tienda lo permite, API pública de catálogo VTEX.
      Si no, queda propuesto.

**Terminado cuando:** tabla de E1 con y sin verificación y su lectura de predicción selectiva.
**Informe:** `04_resultados_e1.md`.

## S09 — Producto y MLOps ligero (mar 17-nov)

**Objetivo:** demo presentable y prácticas de operación mínimas.

- [ ] Streamlit final: consulta, cuadro comparativo, panel de procedencia por dato, alertas de inyección detectada,
      ofertas no verificadas, costo de la consulta, aviso de que el agente no ejecuta pagos.
- [ ] GitHub Actions: `pytest` + una tarea de humo con modelo simulado en cada push.
- [ ] Trazas de llamadas al LLM (LangSmith o Langfuse; elegir el más simple de configurar, con Context7).
- [ ] README completo: qué es, cómo reproducir cada experimento con un comando, estructura, licencias y límites
      legales del corpus A.
- [ ] Capturas y video corto de la demo para la presentación.

**Terminado cuando:** un tercero puede clonar, configurar `.env` y reproducir una corrida siguiendo el README.
**Informe:** `03_metodologia_operacion.md`.

## S10 — Informe IEEE (mié 18-nov)

**Objetivo:** informe completo en la plantilla institucional, en PDF.

- [ ] Ensamblar los borradores de `docs/informe/` en la plantilla institucional: introducción y problema, estado del
      arte, metodología, resultados, discusión (incluye ética, legal y seguridad, citando el ensayo de Ética como
      base), conclusiones, hoja de ruta (lo propuesto: E4, N1/ACP/UCP/AP2, SvelteKit/PostgreSQL, autohospedaje de
      pesos abiertos, descubrimiento abierto de proveedores, IPAC como servicio) y referencias.
- [ ] Verificar cada referencia y cifra contra la fuente primaria; unificar la edición de OWASP; descargar el informe
      primario de la CCCE si se cita.
- [ ] Revisión de metacomentario y de registro académico.

**Terminado cuando:** PDF generado en `privado/entregables/`, con referencias verificadas.

## S11 — Auditoría, presentación y radicación (jue 19-nov)

- [ ] Auditoría del informe contra la rúbrica criterio por criterio (R.6.1, R.6.2, RA1, R.7.1, R.7.2) y contra los
      lineamientos del aula virtual; corregir lo que falle.
- [ ] Presentación de 5 láminas sobre la plantilla institucional (`privado/curso/`), guardada en `privado/entregables/`, guion completo en notas del orador; sirve para la
      presustentación del 20-nov y como base del video.
- [ ] Preguntas probables del tribunal con respuesta preparada.
- [ ] Wills radica informe y presentación.

**Terminado cuando:** radicado.

## S12 — Video y defensa (21–26-nov)

- [ ] Incorporar la retroalimentación de la presustentación.
- [ ] Guion del video de 10 minutos (problema, solución, demo, resultados, conclusiones) y apoyo a la grabación.
- [ ] Ensayo de preguntas y respuestas.
