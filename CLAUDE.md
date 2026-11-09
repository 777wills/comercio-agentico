# Proyecto III de Innovación Tecnológica en IA — Maestría en IA Aplicada, Universidad Icesi (2026-2)

Carpeta de trabajo y repositorio de William Suaza Losada ("Wills"). Proyecto **individual**.

## Arranque obligatorio de cada sesión

1. Lee `docs/ESTADO.md` (dónde quedamos y cuál es la siguiente sesión).
2. Lee en `docs/PLAN.md` **solo** la sección de la sesión que toca, más la sección 1 (principios) si no la tienes presente.
3. Consulta `docs/DECISIONES.md` cuando una tarea toque una decisión ya tomada. **No reabras decisiones sin
   debatirlas con Wills**; si cambian, se registra la nueva con su porqué.
4. Antes de escribir código, propón a Wills en 3–5 líneas lo que harás en la sesión y espera su visto bueno.
5. `privado/contexto_claude/CONTEXTO_SESION.md` es histórico (sep-2026). Úsalo solo para las referencias ya verificadas
   (sección 4), los errores ya cometidos (sección 5) y los conceptos explicados (sección 7). Donde contradiga a
   `docs/DECISIONES.md`, manda DECISIONES.

## Principios que rigen todo el trabajo

- **Simplicidad por encima de la sobreingeniería.** Primero un producto mínimo viable que funcione de punta a punta
  con librerías y componentes existentes (LangChain/LangGraph, crawl4ai, Streamlit, FastMCP, Hugging Face); luego se
  profesionaliza. Antes de escribir algo propio, pregunta si una librería ya lo hace.
- **La IA primero.** Se prioriza lo que corresponde a la maestría: agentes, scraping y crawling con LLM, extracción,
  defensa frente a inyección, evaluación. Lo determinista (API de catálogo N1, despliegue) va al final.
- **Lo que no cabe se declara como propuesto**, en la hoja de ruta del informe; no se improvisa a medias.
- **Cuidar los créditos.** Desarrollo con el modelo más barato; los modelos caros solo en experimentos y según la
  regla de parada de E3. Registra el gasto en `docs/ESTADO.md`.
- **Documentación de librerías:** usa Context7 antes de escribir código contra cualquier API de librería (LangGraph,
  LangChain, crawl4ai, Streamlit, FastMCP...). No escribas de memoria firmas que cambian entre versiones.

## Cierre obligatorio de cada sesión (corte limpio)

Haz esto al terminar la sesión, o antes si el contexto se está llenando (no esperes a que se sature):

1. Actualiza `docs/ESTADO.md`: qué se hizo, qué quedó pendiente, gasto de la sesión, **siguiente paso exacto**.
2. Marca las casillas cumplidas en `docs/PLAN.md`.
3. Registra en `docs/DECISIONES.md` cualquier decisión nueva o cambiada.
4. Si la sesión produjo resultados, deja su borrador de sección en `docs/informe/` (así el informe se escribe por
   partes).
5. Actualiza `privado/ENTENDER_EL_PROYECTO.md`: entrada nueva en la sección 9 (bitácora explicada) y, si cambió
   algo, las secciones 3–8 y el glosario. Agrega la sección de la sesión en `docs/GUIA_PRUEBAS.md` (ver "Explicar y
   enseñar a probar").
6. Commit con mensaje descriptivo (Wills autorizó un commit por sesión). Push si el remoto existe.
7. Mensaje final a Wills: qué se hizo y por qué, en lenguaje claro; cómo probarlo él mismo (remite a la sección
   de la guía); gasto de la sesión; qué necesitas de él; siguiente sesión.

## Explicar y enseñar a probar (pedido de Wills)

Wills quiere entender lo que se construye y poder correrlo él mismo. En cada sesión:

- **Documenta para entender** en `privado/ENTENDER_EL_PROYECTO.md`, en lenguaje claro: qué se hizo, por qué, archivo
  por archivo, los conceptos de IA nuevos explicados con ejemplos (y al glosario) y los hallazgos. Mismo formato que
  la entrada de S00. Mantén vigentes las secciones 6 (modelos y dinero) y 8 (dónde estamos).

- **Explica** lo construido: qué hace cada componente nuevo, cómo encaja en la arquitectura de cuatro capas y qué
  concepto de IA aplica (por ejemplo, salida estructurada, ReAct, embeddings, separación de planos). Nivel de
  desarrollador senior: sin explicar programación básica, sí explicando las decisiones de IA.
- **Deja instrucciones de prueba** en `docs/GUIA_PRUEBAS.md`, una sección por sesión, con comandos copiables, qué
  debe ver si funciona y cómo interpretarlo.
- **Las pruebas manuales no deben mover el presupuesto.** Orden de preferencia: (1) sin red y sin costo
  (`make test`, datos de ejemplo, modelo simulado); (2) modelo gratuito de OpenRouter (`:free`) cuando la función
  lo soporte; (3) el modelo más barato (`deepseek-flash` o `haiku`) con una sola llamada. Nunca Sonnet, Kimi ni Opus
  en una prueba manual. **Cada comando declara su costo estimado** (p. ej. "US$0", "< US$0,01").
- Si una prueba con costo es inevitable, ofrece el tope por comando (`COSTO_MAXIMO_POR_TAREA_USD`) y dilo.

## Cómo trabajar con Wills (lo que ha pedido explícitamente)

- Español. Primero la respuesta, luego la justificación; sin preámbulos.
- Creativo pero muy profesional: es trabajo de maestría.
- Las decisiones se debaten y se acuerdan entre los dos. No inicies un entregable grande (informe, presentación,
  video) sin su autorización explícita.
- Para preguntas de decisión usa la herramienta de preguntas con opciones, una recomendada y siempre una opción libre.
- Los documentos deben leerse como escritos por él. **Cero metacomentario**: nada que delate la conversación o que
  discuta la decisión. Registro declarativo y académico.
- **La información bibliográfica es crítica.** Verifica cada referencia y cada cifra contra la fuente primaria antes
  de escribirla. Nunca escribas de memoria DOI, páginas, fechas, porcentajes ni precios.
- Cuando pida revisar algo contra la consigna o la rúbrica, audita de verdad (criterio por criterio) y reporta lo
  que falla.
- Presentaciones: máximo 5 láminas, poco texto, diagramas e imágenes, plantilla institucional, guion completo en las
  notas del orador.
- Es desarrollador senior con mucha experiencia en IA (stack diario .NET, SvelteKit, SQL Server/PostgreSQL). No le
  expliques lo básico de programación.

## El proyecto en una línea

Prototipo de agente de compras verificable sobre proveedores heterogéneos, con defensa medida frente a inyección
indirecta de instrucciones. Título: *Comercio agéntico: del comprador al proveedor*.

## Fechas

| Hito | Fecha | Peso |
|---|---|---|
| Plan de trabajo | 1-sep-2026 | 20 % (entregado) |
| **Todo listo: informe PDF + presentación** | **19-nov-2026** | — |
| Presustentación y radicación del informe y la presentación finales | 20-nov-2026 | 30 % |
| Video de 10 min y ensayo de la defensa | 21–26-nov-2026 | — |
| Sustentación final | 27-nov-2026 | 50 % |

El aula virtual exige entregar el documento y la presentación al menos una semana antes de la sustentación final.

## Repositorio público

El repositorio de GitHub es **público** (`777wills/comercio-agentico`). La raíz contiene solo el proyecto de código.
Todo lo que no es código va en **`privado/`**, que está fuera de git: material del curso, entregables (plan,
presentaciones, informe final en PDF) y el contexto histórico. Nunca se versionan: claves (`.env`), `privado/`,
documentos de oficina (`.docx`, `.pptx`, `.pdf`, `.xlsx`) ni las copias de tiendas reales del corpus A (solo su
manifiesto con sumas de verificación). Revisa `git status` antes de cada commit.

**Claves secretas:** nunca leas, muestres ni imprimas `.env` ni el valor de una clave. El código las carga con
python-dotenv o variables de entorno; para pruebas en la terminal, cárgalas en un subproceso (`set -a; . ./.env`) y
muestra solo códigos de respuesta y resultados.

## Archivos

| Ruta | Qué es |
|---|---|
| `docs/PLAN.md` | Plan por sesiones con entregables y criterios de terminado |
| `docs/ESTADO.md` | Bitácora y siguiente paso |
| `docs/DECISIONES.md` | Registro de decisiones con su porqué |
| `docs/PROMPT_SESION.md` | Prompt único de arranque de sesión |
| `docs/GUIA_PRUEBAS.md` | Qué se construyó en cada sesión y cómo probarlo sin gastar presupuesto |
| `docs/informe/` | Borradores de secciones del informe (versionados), escritos sesión a sesión |
| `CONSTITUTION.md`, `README.md`, `Makefile` | Estándar del proyecto, presentación pública y tareas (`make help`) |

Carpeta `privado/` (no versionada):

| Ruta | Qué es |
|---|---|
| `privado/ENTENDER_EL_PROYECTO.md` | Explicación en lenguaje claro del proyecto y de cada sesión (para Wills; no se versiona) |
| `privado/contexto_claude/CONTEXTO_SESION.md` | Contexto histórico de sep-2026 |
| `privado/curso/syllabus_PAIII.pdf`, `privado/curso/Rubrica_PAIII_2026.xlsx` | Programa y rúbrica del curso |
| `privado/curso/Plantilla presentacion institucional Icesi -2026.pptx` | Plantilla obligatoria de diapositivas |
| `privado/curso/Tema_ ... Intu.html` (2) | Páginas del aula virtual (fechas y lineamientos de entrega) |
| `privado/curso/Challenges_MCD_MIAA_2026_2 - Retos disponibles.csv` | Banco de retos de la universidad |
| `privado/curso/` | Aquí va también la plantilla institucional del informe (IEEE) cuando Wills la descargue |
| `privado/entregables/Plan_de_trabajo_PAIII_WilliamSuaza.docx` / `.pdf` | Plan de trabajo entregado |
| `privado/entregables/Presentacion_Plan_PAIII_WilliamSuaza.pptx` | Presentación del plan (5 láminas, guion en notas) |
| `privado/entregables/Trabajo_final_Etica_WilliamSuaza.docx` | Ensayo de Ética (otra asignatura, trabajo en grupo; mismo caso) |
| `privado/entregables/` | Aquí van el informe final (PDF), la presentación final y el guion del video |
