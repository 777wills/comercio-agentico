# Proyecto III de Innovación Tecnológica en IA — Maestría en IA Aplicada, Universidad Icesi (2026-2)

Carpeta de trabajo y repositorio de William Suaza Losada ("Wills"). Proyecto **individual**.

## Arranque obligatorio de cada sesión

1. Lee `docs/ESTADO.md` (dónde quedamos y cuál es la siguiente sesión).
2. Lee en `docs/PLAN.md` **solo** la sección de la sesión que toca, más la sección 1 (principios) si no la tienes presente.
3. Consulta `docs/DECISIONES.md` cuando una tarea toque una decisión ya tomada. **No reabras decisiones sin
   debatirlas con Wills**; si cambian, se registra la nueva con su porqué.
4. Antes de escribir código, propón a Wills en 3–5 líneas lo que harás en la sesión y espera su visto bueno.
5. `contexto_claude/CONTEXTO_SESION.md` es histórico (sep-2026). Úsalo solo para las referencias ya verificadas
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
5. Commit con mensaje descriptivo (Wills autorizó un commit por sesión). Push si el remoto existe.

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

El repositorio de GitHub es **público**. Nunca se versionan: claves (`.env`), material del curso y de la
universidad, documentos personales (`.docx`, `.pptx`, `.pdf`, `.xlsx`), `contexto_claude/` ni las copias de
tiendas reales del corpus A (solo su manifiesto con sumas de verificación). Revisa `git status` antes de cada commit.

## Archivos

| Ruta | Qué es |
|---|---|
| `docs/PLAN.md` | Plan por sesiones con entregables y criterios de terminado |
| `docs/ESTADO.md` | Bitácora y siguiente paso |
| `docs/DECISIONES.md` | Registro de decisiones con su porqué |
| `docs/PROMPT_SESION.md` | Prompt único de arranque de sesión |
| `docs/informe/` | Borradores de secciones del informe, escritos sesión a sesión |
| `contexto_claude/CONTEXTO_SESION.md` | Contexto histórico de sep-2026 (no versionado) |
| `Plan_de_trabajo_PAIII_WilliamSuaza.docx` / `.pdf` | Plan de trabajo entregado |
| `Presentacion_Plan_PAIII_WilliamSuaza.pptx` | Presentación del plan (5 láminas, guion en notas) |
| `Trabajo_final_Etica_WilliamSuaza.docx` | Ensayo de Ética (otra asignatura, trabajo en grupo; mismo caso) |
| `Plantilla presentacion institucional Icesi -2026.pptx` | Plantilla obligatoria de diapositivas |
| `syllabus_PAIII.pdf`, `Rubrica_PAIII_2026.xlsx` | Programa y rúbrica del curso |
| `Tema_ ... Intu.html` (2) | Páginas del aula virtual (fechas y lineamientos de entrega) |
