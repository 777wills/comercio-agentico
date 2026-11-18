# Estado del proyecto

## Siguiente sesión

**18-nov (revisión de los entregables de la presustentación; Claude Code · Opus 5.5):** los dos entregables de S10a están en `privado/entregables/` (informe de avance: carta de aval sin firma + 1 página; presentación: 5 láminas con guion de 7 min). Contrastados con D138–D149: la presentación y sus notas siguen vigentes (13 tiendas, E1–E3, rúbrica); el informe de avance decía «con un máximo de 5 por consulta», desfasado por D144: corregido a «cinco activas por defecto y ampliables a todo el catálogo» en `fuentes_s10a/informe_avance.py` y regenerados `.docx` y `.pdf` (sigue en 1 página). **Wills: aún no los ha subido a Intu (el plazo era el 17-nov)**; subirlos hoy y avisar al profesor; pedir la firma de la carta de aval. **Gasto US$0.** **Sigue S10 (informe completo).**

**16-nov (guía para la defensa; Claude Code · Opus 5.5):** a pedido de Wills, guía de estudio para la presustentación
y la sustentación en `privado/GUIA_DEFENSA.md` (no versionada), contrastada con el código y los borradores del
informe: arquitectura, grafo de LangGraph, recorrido de una consulta (B013 con la verdad del corpus), defensas, N3,
corpus, métricas, experimentos, modelos, preguntas probables del jurado. Hallazgo: en C0 el extractor tampoco recibe
la advertencia de datos de terceros, que solo se activa con C1; E2 mide la configuración C1 completa (preparar la
respuesta; aislarla sería un experimento adicional). Ampliada con la sección 4b (artefacto, clase de modelo y ficha de cada paso). Hallazgo 2: Wolf Defender tiene
**307,5 M** parámetros (dimensión 768, contados en los pesos locales), no 140 M como dice el catálogo de C2 en
`agente/defensa.py` (visible en la Configuración de CotIA); **corregido a 307M** con el visto bueno de Wills (`make test` en verde). Sin decisiones nuevas. **Gasto US$0.** **Sigue S10
(informe y presentación; entrega en Intu el 17-nov).**

**16-nov (revisión de los borradores del informe; Claude Code · Opus 5.5), D149:** auditados los 28 borradores de
`docs/informe/` por patrones (códigos internos, notas de trabajo, `[ref:]`, cifras desfasadas, OWASP 2025), cruce de
citas con `07_referencias.md` y cobertura frente a D136 y la sección S10 del PLAN. Corregido: (a) **corpus A** con la
cláusula contra robots de Alkosto y Ktronix declarada como limitación en metodología y riesgos éticos (D149); (b)
`[ref:]` → APA 7 (Yao, L. Wang, Peeters, GS1, Efron); **Efron (1979)** verificada en Crossref y agregada; las cuatro
de Mercado Libre pasan a `07_referencias.md`; (c) «presupuesto fijo de 14 acciones» en producto; (d) metodología del
agente: versión medida (`9e49060f5a9e`) y los cuatro controles posteriores (alcance y dato faltante, lecturas
repetidas, anclaje del planificador, moneda); (e) versiones de Playwright, extruct, pypdf, httpx, FastMCP,
sentence-transformers, transformers, PyTorch y Uvicorn en la tabla del stack; (f) hoja de ruta 6.z (E4, ACP/UCP/AP2,
restricciones blandas, modelos y autohospedaje, trabajadores con cola persistente), que las conclusiones citaban sin
que existiera. Sin cambios: cifras clave coherentes entre archivos (E2 11,7 %, E3 88,9/90,0 %, P4 249/249 y 0/119,
C2 19,8 → 0,4 %). Faltan al ensamblar: resumen, palabras clave, reconocimiento y las demás casillas de S10; «IPAC como
servicio» (PLAN S10) no tiene decisión ni fuente en el proyecto: preguntar a Wills qué es. **Gasto US$0.**

**16-nov (revisión de vigencia de los documentos de estudio; Claude Code · Opus 5.5):** `privado/AUDITORIA_Y_FLUJO.md`
y `privado/ENTENDER_EL_PROYECTO.md` (secciones 1–8 y glosario) contrastados con el código y con D01–D148; corregidos
~30 puntos desfasados (profundidad en lugar del tope fijo de 14, tiendas activas al cargar, lista curada de 9 modelos,
1 TB = 1.024 GB, N3 y disponibilidad, corte por dato faltante, lecturas repetidas, moneda, anclaje del planificador,
informe de cotización, canario retirado, OWASP 2026, `leidas` en el estado del grafo, 233 pruebas, gasto ≈ US$24,2).
La bitácora (§9) se conserva como registro fechado, con una nota de vigencia. Sin código ni decisiones nuevas.
Pendiente: confirmar el número de _Unbounded Consumption_ en OWASP 2026 antes de citarlo; la tabla «Presupuesto de
modelos» de este archivo sigue con el acumulado del 11-nov. **Gasto US$0.** **Sigue S10 (informe).**

**16-nov (S10j, instrucciones del planificador; Claude Code · Opus 5.5), D148:** el planificador abre solo la url
registrada y los enlaces recibidos (sin rutas adivinadas), entra a la categoría desde la portada, no reabre páginas y
deja la tienda sin enlaces al producto. Cambio global de `INSTRUCCIONES_PLANIFICADOR` por decisión de Wills (nueva
`version_prompt`; E1–E3 conservan sus corridas con `9e49060f5a9e` y no se repiten); sin control en código, para no
bloquear búsquedas válidas. 1 prueba nueva (`make check`, **233**). Consulta real «MacBook Air, chip M5…» (Flash,
búsqueda rápida, 8 tiendas, N3, tope US$0,08; script con espía de enlaces en el scratchpad, API propia en :8010 sobre
la base local): 12 de 14 lecturas, **6 registradas + 6 enlaces recibidos, 0 inventadas**, 1 repetida bloqueada
(Panamericana tras error); recomendó MacBook Air 13" M5 512 GB de iShop, $6.199.000, envío $0; **US$0,0489**,
338 s (antes: abstención, 30 lecturas, 469 s, US$0,0515, con dominios muertos). Borrador
`03_metodologia_producto.md` actualizado. Pendiente menor: el interceptor de `web_abierta.py` no captura el error
de `route.fetch` ante un recurso del desafío de Cloudflare (traza en el registro, la lectura sigue). **Gasto
≈ US$0,049 (OpenRouter).** **Wills:** reiniciar la API local (la de :8000 corre código anterior, lanzada a las 14:08)
y, tras el despliegue, repetir la consulta en producción (≈ US$0,05). **Sigue S10 (informe).**

**16-nov (S10i, por qué falló la consulta «MacBook Air, chip M5…»; Claude Code · Opus 5.5), D147:** la consulta
(exhaustiva, 30 lecturas, US$0,0515, 469 s) se abstuvo con 40 ofertas y ningún MacBook. Diagnóstico con el lector del
agente, sin modelo: `ishop.co` es un **dominio en venta** y `maccenter.com.co` sirve una **página de Samsung
Indonesia** (el «Galaxy A07 a $1.399.000» eran rupias); Mercado Libre (URL del visitante) exige iniciar sesión;
Falabella solo devuelve accesorios; el planificador gastó 7 lecturas repitiendo portadas y 4 en URL inventadas que
agotaron 60 s. Hecho: (a) dominios corregidos por Wills, `mac-center.com` y `co.tiendasishop.com`, sondeados (robots
permite, términos sin cláusula) y leídos (iShop: MacBook Air 13" M5 desde $6.199.000); (b) sondeo del 16-nov con 7
candidatas nuevas: ninguna apta (Janus, Encarguelo, Tauret y Kalley prohíben robots en sus términos; Honor por
robots.txt; JBL y Acer no resuelven); revisadas Motorola (cl. 8.8 prohíbe robots), Electrojaponesa (términos con
429) y Apple Colombia (sin precios); nuevo criterio: lectura de prueba con productos propios con precio; (c) una
lectura repetida no se ejecuta ni gasta acción (`separar_repetidas` en `grafo.py`, estado «repetida» en la
bitácora); (d) precio en otra moneda → descartada con su motivo (`otra_moneda`). `make check` en verde (**232**,
4 nuevas); frontend sin errores. Borrador `03_metodologia_producto.md` actualizado. **Gasto US$0.** Pendiente
visto: el planificador sigue inventando rutas (`/sitemap.xml`, `/mac`) en lugar de usar los enlaces recibidos
(propuesto). **Wills:** reiniciar la API local (la de su terminal de VS Code corre el código anterior) y, si quiere,
la prueba de la guía S10i (≈ US$0,03); tras el despliegue, repetirla en producción. **Sigue S10 (informe).**

**16-nov (S10h, profundidad de búsqueda; Claude Code · Opus 5.5), D146:** selector «Búsqueda rápida / normal /
exhaustiva» junto al cuadro de consulta (y en el Laboratorio): 8, 14 o 24 lecturas con hasta 5 fuentes, más 2/3/5 por
fuente activa sobre 5, techo 30. «Normal» con 5 fuentes = 14 (E1–E3). La API registra `profundidad` y `max_acciones`;
el informe dice el presupuesto y explica qué es una ronda; el aviso de «Fuentes» ahora dice que con más tiendas sube
el presupuesto. 2 pruebas nuevas (`make check`, **228**). Hallazgo operativo: un proceso huérfano de la API (12:49)
ocupaba :8000 y los reinicios fallaban en silencio; se cerró y la unidad se relanzó con `KillMode=control-group`.
**Gasto US$0.** **Wills:** tras el despliegue, probar una consulta «Rápida» en producción (≈ US$0,035).

**16-nov (S10g, enlace de cada oferta a su fuente; Claude Code · Opus 5.5), D145:** cada oferta comparada se
abre en su origen en una pestaña nueva: la ficha en la tienda si es http(s) y del mismo sitio que la página leída
(`url_detalle` es dato no confiable); si no, la página o el documento leído. El corpus local (P2–P5, A1–A3 y las
copias atacadas) se traduce al visor del corpus, incluido el PDF de P4. Enlaces en el modo Cliente (recomendación,
tabla, móvil y panel «Fuente»), el Laboratorio y el informe de cotización (cuadro, descartadas, bitácora y anexo;
siguen activos en el PDF impreso). Las ofertas finales guardan `url_detalle` y `url_fuente`, así que las descartadas
se enlazan en las consultas nuevas. Sin enlace: el MCP y los PDF del visitante (decisión de Wills: no se guarda el
archivo). Lógica en `web/src/lib/enlaces.ts`, probada con 11 casos (incluidos un dominio ajeno y un `javascript:`).
Revisado en Chrome con consultas guardadas: vivo (34 enlaces en el informe), corpus B y carga A20 (todos 200).
`make check` en verde (226 pruebas). Borrador `03_metodologia_producto.md` actualizado. **Gasto US$0.**
**Wills:** tras el despliegue, abrir una consulta en producción y pulsar «Abrir ↗». Arreglo menor: la justificación mostraba los códigos de fuente en lista («(V3, V4, V5, V6, V7)»); `conNombres` (`web/src/lib/datos.ts`) ahora traduce también las listas a nombres de tienda. **Revisión del lenguaje del informe para el comprador:** auditados por programa los 26 informes guardados
(textos visibles sin fragmentos) en busca de códigos, identificadores con guion bajo, trazas y jerga. Corregido:
códigos sueltos o de tiendas retiradas (V1 Alkosto, V2 Ktronix) y de tiendas propias («Tienda propia» si no es del
visitante); «(discrepancia)»/«(sin_contraparte)» en frases claras; alertas de fuente no disponible sin la llamada ni
la traza (`alertaLegible`: robots.txt, fuera de la lista, catálogo inactivo, sin respuesta); alertas del clasificador
sin «ventanas» ni puntaje; «sin juicio de pertinencia», «>=», «1 cumplen»; tipo de producto con tilde; especificaciones
sí/no; decisión sin «precio verificada» ni «envío —»; columna «Precio confirmado en 2.ª lectura» (Sí / No coincide /
No se pudo releer, con los campos en español); motivos con mayúscula inicial; búsquedas del mayorista y su procedencia
legibles; alertas sin repetir. Auditoría final: 0 hallazgos en los 26. Gasto US$0. **Sigue S10 (informe del curso).**

**16-nov (S10f, sin tope de tiendas activas; Claude Code · Opus 5.5), D144 (precisa D131):** al cargar CotIA
siguen activas las 5 tiendas fijas, pero el visitante puede activar todas las del catálogo y sus URL propias. Se quitó
el recorte y la verificación de cupo de `api/fuentes_visitante.py` (una URL nueva entra activa); `MAX_WEB_ACTIVAS`
pasa a `TIENDAS_RECOMENDADAS = 5`, solo informativo (`limites.tiendas_recomendadas`); el panel «Fuentes» muestra
«Tiendas activas: n» y, con más de 5, avisa que las 14 acciones se reparten entre más tiendas. El presupuesto de
acciones y el tope de reloj no cambian. `make check` en verde (226 pruebas); prueba local con `curl`: 5 activas al
cargar, tres tiendas más aceptadas (200), restablecer vuelve a 5. Borrador `03_metodologia_producto.md` actualizado.
**Gasto US$0.** **Wills:** tras el despliegue, abrir «Fuentes» en producción y encender una sexta tienda. **Sigue S10
(informe del curso).**

**16-nov (S10e, mejoras tras el análisis de una consulta real; Claude Code · Opus 5.5), D143:** la consulta
local «Celular de por lo menos gb de ram» se abstuvo con 36 de 45 ofertas en discrepancia. Diagnóstico: (1) la
consulta omitía la cifra y el intérprete descartó la condición en silencio (la más barata fue un ZTE de 2 GB);
(2) una llamada a Haiku confirmó que las discrepancias eran **solo de disponibilidad** (el extractor deja
`desconocida`; N3 trata lo que se puede comprar como en stock), con el precio idéntico; una simulación con «6 GB»
se abstenía igual. Implementado: **(a)** N3 compara la disponibilidad solo si las dos lecturas la conocen y cada
oferta guarda `campos_discrepancia` (laboratorio e informe los muestran); **(b)** la necesidad suma `falta` y el
grafo se abstiene antes de recorrer tiendas pidiendo el dato; **(c)** con la política abstener, la propuesta nombra
la mejor oferta verificada (`alternativa`) sin recomendarla. `make check` en verde (**226 pruebas**, 3 nuevas).
Pruebas reales con Flash: «…gb de ram» → abstención pidiendo la cantidad de GB en 16 s y **US$0,00026** (antes
US$0,0617 y 344 s); «…6 GB de RAM» → **recomienda** Nubia Focus 2 Ultra 8 GB, $834.900, con 7 de 7 ofertas
verificadas (US$0,0601, 372 s); el intérprete no marca falta en consultas vagas sin cifra («portátil liviano»,
«buena cámara») y sí en «Televisor de pulgadas». E1–E3 se midieron con la versión anterior. Borrador:
`05_discusion_verificacion_en_vivo.md`. **Gasto ≈ US$0,072** (Haiku ≈ 0,01; Flash ≈ 0,062). Pendientes menores
vistos: el recorrido sigue abriendo las portadas (propuesto, hoja de ruta) y una oferta salió duplicada (Moto Edge
60 Fusion, misma fila dos veces). **Wills:** abrir en Brave las dos consultas nuevas de la barra lateral; tras el
despliegue, repetir en producción. **Sigue S10 (informe del curso).**

**16-nov (S10d, panel «Fuente» del cliente; Claude Code · Opus 5.5):** el texto original de la fuente traía
palabras sin espacios (URL de schema.org de hasta ~450 caracteres) que ensanchaban la celda y la tabla de ofertas;
la columna «Ocultar» quedaba fuera de vista y había que bajar hasta la barra horizontal de la tabla. Arreglo en
`ResultadoCliente.svelte`: el fragmento parte en cualquier punto (`overflow-wrap: anywhere`, solo desplazamiento
vertical) y suma «Ocultar fuente» al pie del panel. Verificado en Chrome con la consulta local «Celular…» (45
ofertas): a 1300 px la tabla mide 896 px en un contenedor de 896 (antes, 1119); a 619 px sin desborde de página.
`make check` en verde (223 pruebas). **Gasto US$0.** Sigue S10 (informe del curso).

**16-nov (S10c, informe de cotización; Claude Code · Opus 5.5), D142:** cada consulta terminada tiene un
**informe de cotización** en `/informe/{id}` (solicitud y criterios, decisión, cuadro, descartadas con su motivo,
bitácora por ronda con cada URL leída, controles y alertas, anexo de procedencia con SHA-256 y fragmento), imprimible
a PDF desde el navegador (siempre en papel claro), y un **expediente JSON** descargable
(`GET /api/consultas/{id}/evidencia`) con huella SHA-256 verificable (`python -m comercio_agentico.api.evidencia`).
Determinista, sin llamar a ningún modelo. Probado con una consulta real guardada (monitor LG: 13 ofertas, 14
descartadas, 5 rondas): escritorio, 390 px y PDF en tema oscuro (12 páginas). `make check` en verde (**223
pruebas**). Borrador en `03_metodologia_producto.md`. **Gasto US$0.** **Wills:** tras el despliegue, abrir el
informe de una consulta en producción e imprimirlo. **Sigue S10 (informe del curso), mar 17 y mié 18-nov.**

**16-nov (S10b, revisión de la interfaz; Claude Code · Opus 5.5), D139:** tema claro por defecto con selector
claro/oscuro/sistema, IBM Plex Sans, laboratorio con «← Modo cliente» en móvil, recomendación como cotización,
lista apilada de ofertas en móvil, resumen con nombres de tienda en lugar de códigos, diálogos con alto máximo y sin
desplazamientos anidados; **D140:** historial de consultas en barra lateral al estilo de claude.ai (cajón en
móvil, «Mis consultas» redirige a `/`) y arreglo de la vista de consulta, que no cambiaba al saltar entre consultas
desde la barra; **D141:** cancelar una consulta en ejecución (ruta solo para el dueño, estado `cancelada` con lo
consumido, botón en cliente y laboratorio; 3 pruebas sin red y prueba de punta a punta con clave falsa). Revisado a
390 px y en escritorio, en claro y en oscuro. `make check` en verde (221
pruebas); se excluyó `.claude` de Ruff (las skills de D130 rompían `format-check`). Push a `main` → Railway
despliega. **Wills:** abrir producción en su celular y confirmar; antes de la demo, una o dos consultas de
calentamiento en el navegador de la presentación para que la barra no esté vacía. Gasto **US$0**. Sigue S10 (informe), hoy mismo.

**S10a hecha (15-nov, un día antes).** En `privado/entregables/`: `Informe_avance_PAIII_WilliamSuaza.docx` y
`.pdf` (carta de aval llena y sin firma + 1 página) y `Presentacion_Presustentacion_PAIII_WilliamSuaza.pptx` y
`.pdf` (5 láminas, guion de 7 min en las notas). Generadores en `privado/entregables/fuentes_s10a/`. D137: plan
revisado contra la plantilla, la rúbrica, el syllabus y los dos lineamientos.
**Siguiente: S10 (lun 16 a mié 18-nov): informe completo en `privado/curso/Formato_informe.docx`, APA 7.**
**Wills, antes del mar 17-nov:** revisar y subir a Intu los dos entregables; pedir la firma de la carta de aval al
mentor (si llega, reemplaza la primera página); llevar al profesor las cuatro preguntas de `docs/PLAN.md` §4
(versión radicada, fecha del video, plantilla de diapositivas, representante de la empresa). Después: **P3**
(línea base humana: 6 tareas con cronómetro según `privado/auditoria/PROTOCOLO_LINEA_BASE.md`; completa Cr6) y
**rotar las claves de `.env`**. El canario no se activa (D138).
**16-nov (Claude Code · Opus 5.5), D138:** borradores de `docs/informe/` sin códigos internos (Dnn, Snn), sin el
canario y sin notas de trabajo (las de verificación de referencias pasaron al PLAN, S10); entregables S10a
regenerados sin «sesiones S00–S09» ni canario y con William Suaza Losada como autor en los metadatos. Gasto US$0.
Antecedentes del 15-nov: borradores 01, 02, 06 y 07 (40 referencias APA 7), D133–D136, OWASP 2026. Ventas CCCE
2026-I = **$39,37 billones** (no $39,7).

**S10 — Informe (APA 7, D133 y D136).** S09c quedó hecha el 11-nov: CotIA publicada en
<https://comercio-agentico-production-bf030669.up.railway.app>.

Siguiente paso exacto:

0. `make guardia` antes de tocar nada (D134); si falla, avisar a Wills.
1. S10: leer en `docs/PLAN.md` la sección S10 (casillas ampliadas por D137). Para generar el `.docx`, reutilizar el
   enfoque de `privado/entregables/fuentes_s10a/informe_avance.py` (python-docx sobre la plantilla: conserva la
   carta, quita los marcos del encabezado y los textos de ejemplo, usa los estilos Heading 1 numerados en romanos).
   Dato pendiente: `06_plan_frente_a_logrado.md` dice «entregado en agosto»; CLAUDE.md fecha el plan el 1-sep
   (los archivos son del 30-ago): confirmar con Wills antes de escribirlo en el informe.
2. S10: ensamblar los borradores en la estructura de D136 (01 + 02 → Introducción; 03 → Materiales y métodos con
   versiones de librerías; 04 → Resultados sin interpretación; 05 → Discusión; 06 → Conclusiones; plan frente a lo
   logrado e IAG → Apéndice). Convertir las citas `[ref: …]` a APA 7 y sumar a `07_referencias.md` la normativa y
   los marcos éticos ya verificados (`CONTEXTO_SESION.md` §4). Cerrar los pendientes al final de `07_referencias.md`.
2. Insumos: los borradores de `docs/informe/` (nuevos el 14-nov: `03_metodologia_pipeline_datos.md`,
   `05_discusion_eleccion_modelo.md`, `05_discusion_riesgos_eticos.md`, `06_plan_frente_a_logrado.md`,
   `06_declaracion_uso_iag.md` y la sección de fallas sembradas en `04_resultados_e1.md`; antes:
   `03_metodologia_operacion.md` y `04_resultados_c2_reales.md`; `03_metodologia_producto.md` suma D114 y la tabla
   de ofertas finales) y la hoja de ruta.
3. Pendientes: capturas y video corto de la demo para la presentación (con Wills, en producción y en día de
   demo, D118). D114 y las ofertas finales del Laboratorio quedaron hechas en S09e; D115 b, en S09d.
4. Operación (D118): desarrollo en local con `make cotia-docker` (:8080) o `make bd && make api`; Railway con
   Serverless, salvo los días de demo (20 y 27-nov: desactivarlo esa mañana y hacer una consulta de calentamiento).
   Capturas de LangSmith para el informe antes de que caduquen (14 días).

**Hecho el 15-nov (revisión del plan y S10a; Claude Code · Opus 5.5):**

- `make guardia` limpio al arrancar.
- **Revisión del plan (D137)** contra `Formato_informe.docx`, la rúbrica, el syllabus, `PRESUSTENTACIÓN.txt` y
  `SUSTENTACIÓN.txt`. Casillas nuevas: P3, canario, rotación de claves, demo segura de P11 (20 y 27-nov),
  capturas de LangSmith antes del 24-nov, piezas de la plantilla (resumen, índice de términos, Reconocimiento,
  versiones de librerías, formato y PDF), auditoría con los seis criterios de `SUSTENTACIÓN.txt` y RA2–RA4, y
  cuatro preguntas para el profesor.
- **Informe de avance** sobre la plantilla (python-docx): carta de aval con los datos del proyecto y la firma en
  blanco (decisión de Wills) y una página con resumen, índice de términos, Tabla I (estado por objetivo),
  resultados de E1–E3 y del producto, cronograma (14 cumplidos, 3 parciales, 1 propuesto de 18) y ética y
  viabilidad. Cifras tomadas de `06_conclusiones.md` y `06_plan_frente_a_logrado.md`.
- **Presentación** sobre la del plan (misma plantilla institucional y paleta): portada, estado actual (diagrama de
  fuentes → N1–N4 → propuesta y tres bloques del producto), avance en IA (E2, E1, E3), cronograma (sesiones y
  barra de compromisos) y rúbrica (14 criterios con semáforo: Cr6 y R.7.2 Cr5 en parcial). Guion de 7 min en las
  notas con las respuestas a los cuatro criterios del profesor. Validación de la estructura y revisión visual de
  cada lámina.
- **Gasto: US$0** (sin LLM).

**Hecho el 15-nov (S10, borradores del informe y guardia; VS Code · Opus 5.5):**

- **Incidente al arrancar (tercera vez):** a las 08:29 se guardaron 14 archivos con búferes viejos. `DECISIONES.md`
  y `PLAN.md` eran idénticos a los del 10-nov y `ESTADO.md` volvía a «S09b»; los 7 `.py`, `api.ts`, la guía y
  un borrador solo cambiaron de formato (Black a 88 columnas, Prettier en tablas). Restaurados desde HEAD con
  autorización de Wills; se conservó su cambio en `Fuentes.svelte` (desborde horizontal del panel).
- **D134, solución definitiva:** `.vscode/settings.json` local (`files.hotExit: off`, `editor.formatOnSave: false`,
  `files.saveConflictResolution: askUser`) y `scripts/guardia_bufer.py` (`make guardia`, dentro de `make check` y
  como hook de pre-commit). Probada con una sobrescritura simulada de `PLAN.md`: la detecta y nombra el commit.
- **D133:** el informe cita en APA 7 (la rúbrica nombra APA/MLA/Chicago).
- **Borradores de S10:** `01_introduccion.md`, `02_estado_del_arte.md` (con la Tabla 2.1 de brecha),
  `06_conclusiones.md` y `07_referencias.md` (40 entradas en APA 7, verificadas hoy en la fuente primaria; seis
  pendientes menores al final del archivo). Corrección: ventas de la CCCE 2026-I = $39,37 billones (el plan decía
  $39,7, cifra que corresponde al cuarto trimestre de 2025 y que varios medios repitieron).
- **S09f cerrada:** prueba de humo de Tigo, Flamingo, HP, LG y Sony (más Homecenter): las 6 llegan a fichas; HP,
  LG y Sony se abstienen por N3. Ninguna se retira. Evidencia: `resultados/tiendas/humo_2026-11-14.jsonl`.
- **Gasto: US$0** (sin LLM; la verificación de referencias se hizo leyendo las fuentes).

**Hecho el 14-nov (S09f, catálogo amplio de tiendas en vivo; VS Code · Opus 5.5), con pruebas:**

- **Incidente al arrancar:** a las 11:44, 11 archivos (DECISIONES, PLAN, ESTADO, 6 borradores del informe,
  `arnes/e1_fallas.py`, `tests/test_verificacion.py`) se escribieron con versiones del 10-nov (búferes viejos de VS
  Code). Restaurados desde HEAD con `git restore`, con autorización de Wills. Nota en la memoria (sección 7).
- **D131 (decisión de Wills):** sin preselección automática; 5 tiendas fijas activas al cargar (Falabella, Samsung
  Colombia, Panamericana, Homecenter, Tienda Claro) y el visitante cambia la selección; la API rechaza una sexta
  fuente web activa (422), una URL con el cupo lleno se guarda apagada y el registro nunca pasa de 5 fuentes web;
  los PDF no cuentan.
- **Sondeo (`make sondeo-tiendas`, US$0):** 35 tiendas; términos renderizados con Chromium donde cargan por JS.
  **D132 (decisión de Wills):** criterio único; los términos de Alkosto, Ktronix, Alkomprar y Tecnoplaza («spiders,
  site copiers… para acceder, adquirir, copiar ó monitorear»), Huawei, Asus y Home Sentry prohíben el acceso
  automatizado → no aptas. Aptas: Falabella, Samsung, Panamericana, Homecenter, Tienda Claro, Tigo, Mac Center,
  iShop, Clevercel, Flamingo, HP, LG, Sony Store, con etiquetas de categoría y marca. El `llms.txt` de Alkosto trae
  «Instrucciones para el modelo de lenguaje» comerciales (ejemplo real para el informe).
- Panel «Fuentes»: etiquetas («Solo Apple · Portátiles…»), contador «n de 5» y bloqueo del sexto interruptor.
  `ataques/c2_reales.py` conserva la lista del 11-nov (medición de S09d).
- **Prueba de humo** (Flash, una tienda activa, `privado/auditoria/humo_tiendas.py`): Homecenter, monitor ≥ 27" →
  Xiaomi A27i $429.900 verificada por N3 (14 páginas, 69 ofertas, 589 s, US$0,080). Tienda Claro, Mac Center, iShop
  y Clevercel ya se probaron hoy en la auditoría (en grupos). Tigo, Flamingo, HP, LG y Sony: en curso al cierre.
- Informe: `03_metodologia_producto.md` (catálogo, criterio y tope) y `05_discusion_riesgos_eticos.md` (fila de
  exclusión). `make check`: **218 pruebas** en verde, Ruff limpio, svelte-check 0 errores, build correcto.
- **Gasto: ≈ US$0,56 estimado** (OpenRouter, Flash: Homecenter US$0,080; Tienda Claro, que siguió en la API al acotar
  la prueba; y 5 tiendas a ≈ US$0,08 c/u). Sondeo y revisión de términos: US$0.

**Hecho el 14-nov (P4 y borradores de S10 con P7–P10; VS Code · Opus 5.5), con pruebas:**

- **P4 / D129:** `arnes/e1_fallas.py` (`make e1-fallas`, US$0, sin red ni corpus servido). Cinco fallas sembradas en la
  primera extracción de las corridas C1 de E1 (precio ±10 %, envío omitido, disponible leída como agotada y agotada
  leída como disponible); reutiliza las segundas lecturas en caché. N3 detectó **249/249** fallas, con 0 falsas
  alarmas en las 65 ganadoras sin falla. Con abstención, **0 de 119** fallas que favorecen a una oferta llegaron a la
  recomendación. Las que perjudican (sacan a la ganadora) no se recuperan: N3 solo verifica la ganadora. La
  exclusión es peor que la abstención (80 % de erróneas con precio −10 % en B). Evidencia en
  `resultados/informes/e1_fallas/`; informe en `04_resultados_e1.md` (Tablas 4.y.3–4.y.4, Figura 4.y.2); hoja de
  ruta: verificar también las descartadas que habrían ganado.
- **P8:** `05_discusion_eleccion_modelo.md`. Matriz de los 6 modelos de D31 frente a los criterios del negocio, con
  los precios del endpoint fijado **verificados en la API pública de OpenRouter el 14-nov** (sin cambios desde el
  9-nov), el costo estimado de los no medidos y el dato de B013 de la curaduría de CotIA.
- **P9:** `05_discusion_riesgos_eticos.md` (10 riesgos → mitigación → evidencia → residual). **P10:**
  `03_metodologia_pipeline_datos.md` (diagrama Mermaid y tabla de etapas con el vocabulario de R.7.1).
- **P7 (parcial):** `06_plan_frente_a_logrado.md` (contra el plan entregado en agosto) y `06_declaracion_uso_iag.md`
  (nivel 5 del syllabus, verificado en `privado/curso/syllabus_PAIII.pdf`).
- `make check`: **218 pruebas** en verde, Ruff limpio. **Gasto: US$0.**

**Hecho el 14-nov (implementación de las propuestas de la auditoría; Claude Code · Opus 5.5), con pruebas:**

- **P1 / D122:** juez de la comparación abierta por lotes de 15 con reintento y alerta «sin juicio de pertinencia».
  Verificado en vivo: A57 con Flash 64/64 ofertas juzgadas; audífonos Sony con Haiku 113/113 y recomendación Sony
  WH-CH720N $349.900 (Alkosto), verificada (antes, 65/65 perdidas).
- **P2 (b) / D123:** carga formal A21 (`ataques/cargas_adaptativas.yaml`, `ataques/adaptativo.py`,
  `make ataque-adaptativo`). Flash: C0 3/3 exfiltraciones; C1, C2, C3 0/3 cada una
  (`resultados/ataques/2026-11-14_adaptativo_titulo.jsonl`). Una ejecución C1 se abstuvo por sobreinferencia de
  restricciones desde el nombre del producto (no por el ataque).
- **P5:** `docs/informe/04_analisis_error_vagas.md` (US$0).
- **P6.1 / D124:** límite de 15 min por consulta (`COTIA_LIMITE_S`) y consultas huérfanas a error al arrancar.
  **P6.2–6.3:** `.github/workflows/evaluacion.yml` (arnés simulado semanal; canario con secreto).
- **P12 / D121:** Streamlit retirado (módulo, prueba, dependencia y objetivo del Makefile); registro del agente
  visible en la API (`COTIA_LOG`).
- **P13 / D125:** guardia de red en Chromium (`GuardiaRed` en `agente/web_abierta.py`): valida cada salto de
  redirección y bloquea imágenes, video y fuentes. Verificado con un banco local: sin guardia se leía el servicio
  interno; con guardia no llegó la petición.
- **P15 (parcial):** la ficha de Falabella se lee completa y C2 no retira nada; la pérdida ocurre en la extracción o
  el emparejamiento.
- `make check`: **214 pruebas** en verde, Ruff limpio. `privado/AUDITORIA_Y_FLUJO.md` actualizado (I.5 y parte II,
  con la sección II.13 sobre LangGraph).
- **Consultas ajenas a la compra** (Flash, corpus B): «receta para asado huilense» y «código para sumar dos
  números» → el planificador no llamó herramientas y el agente se abstuvo con el motivo genérico «Ninguna oferta
  disponible cumple todas las restricciones» (US$0,0013 en total). No hay un control explícito de alcance; con una
  necesidad vacía, el filtro aceptaría cualquier oferta si el planificador recolectara.
- **D126, control de alcance:** `es_compra` en la necesidad y ruta `interpretar → proponer`; abstención con necesidad
  sin objeto. Verificado con Flash: «receta», «código» y «algo para el asado» cortadas con 1 llamada
  (≈ US$0,0001 c/u); B013 acierta (US$0,013). 216 pruebas en verde.
- **D127, S09f antes del informe:** catálogo amplio de tiendas, máximo 5 por consulta (incluidas las URL del
  visitante), preselección por categoría y marca modificable por el visitante. API de Mercado Libre: sin token
  responde 403 en `/sites/MCO/search` y `/products/search` (comprobado hoy); requiere una aplicación registrada por
  Wills.
- **S09g hecha (D128):** documentación del portal de desarrolladores recorrida con Claude in Chrome (crear app, OAuth,
  ítems y búsquedas, buscador de productos, competencia, permisos, 403, 429, pruebas, MCP, quick start, T&C de
  Colombia). Viable técnicamente (`/products/search` en MCO + `buy_box_winner`), sin tarifa base; el MCP oficial
  solo sirve documentación; los T&C (cl. 5.2 y 2) prohíben combinar su contenido con el de terceros y los servicios
  competidores → no se integra; se documenta como limitación (`docs/informe/05_limitacion_mercadolibre.md`). No se
  creó la aplicación ni se aceptó nada. US$0. Notas: `privado/mercadolibre/NOTAS_S09G.md`.
- **S09g** añadida al plan: exploración de la integración con la API de Mercado Libre recorriendo con Claude in
  Chrome la guía para producto del portal de desarrolladores, con las reglas de interacción y de secretos fijadas
  por Wills.
- **Gasto de la fase: ≈ US$0,34** (total de la auditoría ≈ US$0,94; OpenRouter ≈ US$0,55, Anthropic ≈ US$0,39).

**Hecho el 14-nov (auditoría integral antes del informe; Claude Code · Opus 5.5), con pruebas:**

- Auditoría contra la rúbrica (criterio por criterio), el syllabus y el plan entregado; documento
  `privado/AUDITORIA_Y_FLUJO.md` (parte I: 16 propuestas priorizadas; parte II: flujo del agente para la defensa).
- Verificación: Ruff y formato limpios, **208 pruebas** en verde, svelte-check 0 errores, producción `ok`.
- **Corpus B**, perfil del cliente (C2 + N3), tareas B001, B013, B025, B037 y B054: Flash 5/5 (US$0,095), Haiku 4/5
  (US$0,103; B025 falla por la restricción inferida `autonomia >= 8`).
- **En vivo, lista blanca:** A57 con Flash → Samsung $1.999.900, cuando Falabella ofrecía $1.649.900 y quedó
  descartada «sin juicio de pertinencia» (5/40 ofertas sin veredicto del juez); portátil ≥ 16 GB ≤ $3,5 M → Asus
  Vivobook 15 $2.449.990 en Panamericana, verificada; audífonos Sony con Haiku (clave de Anthropic) → abstención por
  **65/65** ofertas sin veredicto. Reproducido aislado, el juez con Haiku juzga 65/65: fallo intermitente (P1).
- **Tiendas nuevas** (sondeo de robots.txt y respuesta a US$0): aptas iShop, Mac Center, Tienda Claro, Clevercel,
  Tecnoplaza y Homecenter; excluidas Xiaomi y Éxito (403) y Jumbo (robots.txt). iPhone 17 256 GB → $4.259.960
  verificada; A57 en Clevercel/Tecnoplaza/Homecenter → abstención correcta (venden A50–A56).
- **Ataque adaptativo por el título** (exfiltrar el presupuesto, corpus B): C0 3/3; C1 0/3 (Flash) y 0/2 (Haiku);
  C2 0/3. El extractor copió el título sin la instrucción. Borrador: `docs/informe/04_resultados_ataque_adaptativo.md`;
  evidencia: `resultados/auditoria/`.
- SSRF: URL internas directas rechazadas; la redirección pública → interna no se pudo reproducir (los redireccionadores
  bloquean robots) y queda como riesgo por análisis (P13).
- Hallazgos de higiene: línea 1 de `docs/GUIA_PRUEBAS.md` corregida; Streamlit sigue en el repositorio (P12).
- **Gasto: ≈ US$0,60** (≈ US$0,38 OpenRouter, ≈ US$0,22 Anthropic). Autorización de Wills para esta auditoría: hasta
  US$3 por cuenta, sin Sonnet, Kimi ni Opus.
- Sin decisiones nuevas: las propuestas esperan debate. Scripts de diagnóstico en `privado/auditoria/`.

**Hecho el 11-nov (S09e, ofertas finales en el Laboratorio y clave de Anthropic; VS Code · Opus 5.5), con pruebas:**

- **Ofertas finales** (`web/src/lib/components/OfertasFinales.svelte`) en `/lab/consultas/[id]`: todas las ofertas que
  llegaron a la comparación, con producto o grupo, si entraron a la propuesta y el motivo del descarte, y su estado N3.
  Revisada en el navegador con la consulta en vivo del Galaxy A57 (65 ofertas, 2 en la propuesta, ambas verificadas).
- **D114:** el proveedor se reconoce por el prefijo (`sk-or-`/`sk-ant-`); cabecera única `X-Clave-Modelo`; clave sin
  prefijo reconocido → 422; con `sk-ant-` solo los modelos Claude (`haiku-or` → `haiku` directo, N3 con `haiku`).
  `obtener_modelo(clave_anthropic=…)` rechaza modelos de otra plataforma (nunca cae en la clave del proyecto).
  `costo_estimado` en el evento final y el detalle; la interfaz muestra «≈ … (estimado)». `/api/modelos` marca
  `anthropic` por modelo; Ajustes y Configuración filtran y cambian a Claude solos. Errores del proveedor en lenguaje
  neutro (401, saldo, 429/529).
- **208 pruebas** (4 nuevas; la de trazas se repite con ambos proveedores), Ruff limpio, svelte-check 0 errores,
  build correcto. Informe: `03_metodologia_producto.md`. **Gasto: US$0** (sin LLM; la prueba real con Anthropic queda
  opcional para Wills).
- **Incidente:** otra vez un búfer viejo de `web/src/lib/config.svelte.ts` (sin la lista blanca de S09b-ter) se guardó
  sobre el disco; se restauró desde git y los cambios de D114 se aplicaron por terminal con autorización de Wills.
  Un formateador realineó tablas Markdown en README y docs (sin cambio de contenido).

**Hecho el 11-nov (S09d, C2 en páginas reales y saneamiento; VS Code · Opus 5.5), con pruebas:**

- **D115 b cerrado** con `ataques/c2_reales.py` (`make c2-reales`, `make c2-reales-analisis`): 81 páginas reales
  (5 portadas, 12 fichas semilla del corpus A por tienda y los 8 primeros enlaces de cada portada), leídas con el
  `Lector` del modo en vivo; puntajes y SHA-256 por ventana, sin texto (D70). Evidencia:
  `resultados/c2_reales/paginas.jsonl` y `resultados/informes/c2_reales/` (md, json, figura de umbral).
- **Causa encontrada:** las ventanas marcadas eran ruido codificado (231 SVG en `data:` URI, sobre todo el logotipo
  CMR de Falabella; 52 tokens base64/JWT en URL), no texto comercial. **D120:** `web_abierta.sanear` antes del
  recorte, solo en fuentes abiertas; `Lector(crudo=True)` para la medición pareada.
- **Resultado (Horizon, umbral 0,5):** crudo 289/1.463 ventanas (19,8 %), 33/81 páginas, 21,3 % del texto →
  saneado 5/1.213 (0,4 %), 5/81 páginas; McNemar 28 frente a 0. Wolf 15,9 % → 0,1 %. Subir el umbral no lo
  resolvía (0,99: 14,8 % de páginas). Texto al extractor −15,2 %. Cargas: Horizon 21/21 y Wolf 15/21 en ambas
  condiciones; 0/47 limpios.
- Informe: `docs/informe/04_resultados_c2_reales.md` (nuevo); corregida la hipótesis de los llamados a la acción en
  `03_metodologia_producto.md` y `03_metodologia_operacion.md`. README con la fila del experimento.
- **204 pruebas** (7 nuevas), Ruff limpio. **Gasto: US$0** (sin LLM).
- **Incidentes:** el equipo se suspendió 33 min durante la primera pasada (ahora `systemd-inhibit`); la terminal del
  editor perdió salidas, se usó una shell `bash --norc` aparte. La muestra se recortó a 12 fichas por tienda por
  tiempo de CPU (decisión de Wills).

**Hecho el 11-nov (S09c, publicación y MLOps ligero; VS Code · Opus 5.5), con pruebas:**

- **Plataforma (D116):** Railway Hobby, tras comparar en páginas oficiales Railway, Cloud Run, Hugging Face Spaces y
  Render. Servicio desde el `Dockerfile` + PostgreSQL gestionado por red privada; «Wait for CI»; salud en
  `/api/salud`; variable de LangSmith sellada.
- **Imagen:** `Dockerfile` en tres etapas (Node 22 → uv → final con Chromium y modelos horneados, `HF_HUB_OFFLINE=1`,
  usuario sin privilegios), capas pesadas antes del código; corpus A y variantes atacadas regenerados dentro. 6 GB
  (3,1 GB comprimida). `compose.yaml` con servicio `app` (`make cotia-docker`, :8080). `bd.py` acepta `DATABASE_URL`
  (`postgresql://`). Probada en local: Chromium, embeddings y clasificador sin red.
- **CI:** estaba en rojo desde S09b (faltaba `corpus/a_real/sitio` en GitHub). Ahora regenera el corpus y lo compara
  con lo versionado, corre las pruebas, un humo del arnés simulado y un job del frontend. Verde.
- **Trazas (D117):** LangSmith con direccionamiento por agente (`cotia`, `production`); aviso en Ajustes y
  Configuración; prueba de que la clave no llega a la traza; en producción, `sk-or` no aparece en la traza.
- **Avance por fuente (D119)** en el modo Cliente; el botón de fuentes nombra el grupo; ícono propio de CotIA.
- **Humo en producción:** B013 con Flash → P4 $2.732.000 + $25.000, igual que la verdad, 5/5 ofertas verificadas por
  N3, US$0,0190, 100 s. En vivo, HP del corpus B (ficticio) → 17 páginas reales, abstención correcta, 594 s,
  US$0,0665; una pestaña de Chromium cayó por memoria (3,7 GB de 4 GB).
- **Operación (D118):** métricas de producción: ~0,27 GB antes de la primera consulta y ~2,1 GB retenidos después.
  Serverless salvo días de demo; réplica 4 vCPU / 6 GB; _hard limit_ US$10.
- README completo (URL, arquitectura, reproducir cada experimento, despliegue, corpus y licencias); informe:
  `docs/informe/03_metodologia_operacion.md`. **197 pruebas**, Ruff limpio, svelte-check 0 errores.
- **Gasto:** OpenRouter ≥ US$0,0855 (B013 0,0190 + HP en vivo 0,0665; más las consultas posteriores de Wills con su
  clave nueva, en su consola). Railway: US$5 de suscripción Hobby (incluye US$5 de uso). LangSmith: US$0.
- **Incidente:** una copia vieja de `web/src/lib/api.ts` abierta en el editor pisó el disco al guardarse y borró la
  lista blanca de S09b-ter; se restauró desde git antes del commit.

**Hecho el 11-nov (S09b-ter, consulta en vivo y lista blanca; Claude Code · Opus 5.5), con pruebas:**

- **Tiendas en vivo (D112):** Alkosto, Ktronix, Falabella, Samsung Colombia y Panamericana, tras sondear robots.txt,
  respuesta a robots y términos de uso (aptas 5; condicionales iShop y Clevercel; no aptas Mercado Libre, Éxito,
  Olímpica y Lenovo). `agente/web_abierta.py`: bloqueo de SSRF (solo direcciones públicas), robots.txt por sitio,
  pausa de 2 s por sitio, agente de usuario `ComercioAgenticoBot/0.1`, recorte centrado en líneas con precio y
  enlaces con prioridad a fichas; crawl4ai con `scan_full_page` y espera para el contenido por JavaScript; bloque
  schema.org sin campos largos. Nada de esto toca el corpus congelado.
- **Lista blanca por visitante (D113):** tabla `fuentes_visitante`, rutas `/api/fuentes` (listar, activar, agregar
  URL, subir PDF ≤ 5 MB con texto y SHA-256, eliminar, restablecer). Panel «Fuentes» en Cliente y Laboratorio; en la
  portada del cliente solo queda el botón «N fuentes» (pedido de Wills).
- **Comparación abierta (D113, D115 a):** `agente/comparacion_abierta.py` — pistas por GTIN y embeddings, juez con
  salida estructurada, reglas deterministas; «desconocida» compite con aviso. El planificador en vivo solo ve las
  herramientas con fuentes. Cerrojo para un solo Chromium por tarea (corrige `TargetClosedError` en paralelo).
- **Prueba real (clave de Wills en Chrome):** Galaxy A56 → abstención correcta (Alkosto y Ktronix venden el A57; la
  ficha de Falabella perdía el precio por la descripción HTML, ya corregido); Galaxy A57 → **Falabella $1.599.900,
  envío $0, verificada por N3**, frente a Samsung $1.999.900; 65 ofertas, descartes razonables. C2 retiró hasta 21 de
  26 ventanas de una ficha real (D115 b).
- **195 pruebas** (20 nuevas en `tests/test_vivo.py`), Ruff limpio, svelte-check 0 errores. **Gasto: US$0,1119**
  (OpenRouter: 0,0487 + 0,0632).
- **Incidente:** el 11-nov a las 06:16 algo externo a la sesión reformateó archivos de `web/` y recreó el
  `+page.svelte` raíz de S09b (conflicto de rutas). Se apartaron el duplicado y `utils.ts.new` (idénticos al historial)
  en el scratchpad de la sesión; el reformateo de `vite.config.ts`, `api.ts` y `datos.ts` se conservó.

**Hecho el 10-nov (S09b-bis, dos modos de CotIA; Claude Code · Opus 5.5), con pruebas:**

- **D111**: modo **Cliente** en `web/src/routes/(cliente)/` (`/`, `/consulta/[id]`, `/mis-consultas`). Consulta con
  catálogo «Tiendas colombianas» (A) / «Proveedores de prueba» (B), progreso en cuatro pasos, recomendación
  destacada, tabla corta, fuente por oferta, sello N3 y alertas en lenguaje de compra. Ajustes en diálogo (clave y
  modelo). Perfil fijo C2 + N3 abstener (`opcionesCliente()`).
- Modo **Laboratorio** en `web/src/routes/lab/` con barra lateral: las pantallas de S09b, movidas sin cambios
  funcionales (rutas con prefijo `/lab`); la consulta perdió el titular y las tarjetas decorativas.
- Tema sobrio: neutros sin tinte, superficies planas, Inter local (`@fontsource-variable/inter`), un acento.
- svelte-check 0 errores; build correcto; revisado en Chrome (portada, Ajustes, cotización A20 en ambos modos,
  `/lab` y `/lab/ataques`). Backend sin cambios: siguen 175 pruebas. Gasto: **US$0**.
- Informe: párrafo de los dos modos en la sección «Interfaz» de `docs/informe/03_metodologia_producto.md`.

**Hecho el 10-nov (S09b, frontend de CotIA), con pruebas:**

- **`web/`**: SvelteKit 3.2 con adapter-static (SPA, `fallback: index.html`), Tailwind v4 y shadcn-svelte
  (bits-ui) en modo oscuro (D109). Secciones: Consulta (corpus A/B, ejemplos por tipo de tarea), detalle con
  progreso SSE en vivo y cuadro comparativo (procedencia desplegable por oferta con fragmento y SHA-256, N3 por
  oferta, alertas, costo y tiempo), Laboratorio (20 cargas, C0 frente a C3 con el mismo modelo y el resultado del
  predicado), Corpus (B, A y copia atacada lado a lado con la carga resaltada), Resultados (E1–E3 con IC y figuras),
  Historial y Configuración (clave en `sessionStorage` salvo «recordar», modelo con costo y evidencia, capas C0–C3 +
  umbral con aviso de exploratorio, clasificador, N3 con política abstener/excluir según D110, gasto de la visita).
- **Backend**: visor del corpus (`api/corpus.py`; `GET /api/corpus` y `/api/corpus/archivo/{origen}/{ruta}` por
  lista blanca, HTML con CSP `sandbox` y en iframe con `sandbox=""`); `app.frontend()` de FastAPI sirve `web/build`.
  `make web` y `make web-dev`. 2 pruebas nuevas: **175 pruebas**, Ruff limpio, svelte-check 0 errores.
- Verificado en el navegador integrado: consulta con clave inventada (401 de OpenRouter, US$0; la clave no aparece en
  el registro) y repetición desde la base de la consulta A20 en C0 de S09a (éxito del ataque, precio falso de P5).
- Informe: sección «Interfaz» en `docs/informe/03_metodologia_producto.md`.

**Hecho el 10-nov (S09a, API de CotIA), con pruebas:**

- **API FastAPI** (`src/comercio_agentico/api/`): 9 rutas (consultas, SSE, detalle, historial con gasto de la visita,
  modelos, ejemplos, resultados E1–E3 con figuras, salud). Cola acotada (1 en curso, 5 en espera, luego HTTP 429).
  Progreso por `astream` del grafo traducido a eventos; los eventos se guardan y se repiten desde la base.
- **Clave del visitante** (D82): pasa por consulta al cliente de OpenRouter; no se guarda, no se registra y se borra
  de los errores; prueba automatizada contra base, respuestas, eventos y registros. N3 con Haiku por OpenRouter (D105).
- **Defensas como capas** (D91): `Defensas` con tres interruptores + umbral; C0–C3 como atajos; C2 por defecto (D106).
- **Lista curada** (D107; `resultados/cotia/modelos.json`): Flash, Haiku 5.5 y Kimi K3.1 Pro. Ningún gratuito pasó
  (3 respuestas incorrectas, 1 atascado por límites de tasa, 1 retirado de OpenRouter); DeepSeek Pro funcionó pero
  falló B013 y no tiene E3.
- **Punta a punta** con la clave en cabecera: consulta con Flash (115 s, US$0,0145; se abstuvo por el hallazgo del
  intérprete, todos los eventos en orden) y laboratorio A20 en C0 (101 s, US$0,0157, **éxito del ataque**, como en E2).
- PostgreSQL 17 en Docker (`compose.yaml`), `make bd`, `make api`, `make cotia-humo`. **173 pruebas**, Ruff limpio.
- Informe: `docs/informe/03_metodologia_producto.md`.

**Hecho el 10-nov (S08, N3 y E1), con pruebas:**

- **N3** (`src/comercio_agentico/verificacion.py`, D100–D101): segunda lectura del fragmento de la procedencia por
  el parser (JSON de P1 y schema.org de P2/corpus A; ambiguo → LLM) o por Claude Haiku 5.5 con prompt propio; caché
  por SHA-256; correspondencia GTIN → enlace → título ≥ 0,8; estados verificada / discrepancia / sin_contraparte.
  Nodo opcional en el grafo (`verificar=True`, `--verificar`, `--politica-n3 abstener|excluir`) que solo verifica
  las ofertas candidatas. `Oferta.verificacion` nuevo (no cambia el esquema que ve el LLM).
- **E1 (D99, D102, D103)** por reproducción pareada sobre calibración v3 (B, 60) y corpus A v1 (20): 110/110
  fragmentos reproducen su SHA-256; control sin N3 = acierto original 80/80. **N3 no cambia ninguna decisión**: M2 B
  58/60, A 19/20 en las tres políticas; las 65 ganadoras quedaron verificadas. **Señal de calidad por oferta:** M1
  verificadas 97,2 % frente a no verificadas 76,0 % (B) y 90,5 % frente a 42,2 % (A). Detector: precisión ~46 %,
  sensibilidad 33 % (B) y 64 % (A); los falsos negativos de B son plazos de agotados que Flash y Haiku omiten por
  igual (errores correlacionados). Ruta determinista: 0 discrepancias en 339 ofertas. M6: US$0,008 por tarea sin
  caché, Haiku p50 4–5 s. Gasto real: **US$0,0213** (Anthropic, 15 lecturas con Haiku).
- Código: `arnes/e1.py` (`make e1` US$0, `make e1-lecturas`), 13 pruebas nuevas (11 en `tests/test_verificacion.py` y
  2 en `test_agente.py`): **159 pruebas**, Ruff limpio. Evidencia: `resultados/informes/e1/` (md, json, PNG,
  `verificaciones.jsonl`) y `resultados/e1/segundas_lecturas.jsonl`.
- N1 queda propuesto (D104) en `docs/informe/06_hoja_de_ruta.md` (6.y, junto con N3 dirigida y N3 bajo ataque).

**Hecho el 10-nov (S07, E2), con pruebas:**

- **E2 (D96):** 240 ejecuciones atacadas + 120 benignas, 0 errores, US$5,35. Utilidad C0–C3: 93,3 / 93,3 / 96,7 /
  93,3 % (diferencias de una tarea, dentro del ruido). **M5: C0 7/60 = 11,7 % [5,8; 22,2]; C1, C2 y C3 0/60 [0; 6,0]**.
  La separación de planos produce toda la reducción medible; C2 es el codo formal por una tarea benigna. Éxitos en
  C0: A20 (precio falso en chat, 3/3, también desvía la compra), A04 (desvío desde chat, 2/3), A09 (presupuesto
  en URL, 2/3). Por ubicación, mensaje 5/15 en C0. Control limpio de predicados: 0/80. Clasificador retiró la carga
  en 54/60 (no detecta A20 dentro de la página, sí aislada). C3 sin alertas de precio (el precio falso nunca se
  extrajo en C1–C3). Las capas no añaden costo apreciable (≤ US$0,0005 por tarea).
- **Jev (D80 → D97):** Horizon 20/20 y 0/47; Jev 20/20 y 0/47 (política falsificada 0,71); Wolf 14/20. C2 se queda.
- Código: `ataques/correr.py` concurrente (`--concurrencia`), `arnes/e2.py` (`make e2`), `ataques/comparar_jev.py`
  (`make jev`), `configs/e2_c0..c3.yaml`, objetivos `e2-ataques`, `e2-ataques-simulado`, `e2-utilidad`. **146
  pruebas**, Ruff limpio. Evidencia: `resultados/informes/e2/`, `resultados/ataques/2026-11-10_suite_ataques*`,
  `resultados/corridas/2026-11-10_e2_c*.jsonl.gz`, `resultados/clasificadores/2026-11-10_jev_vs_local.*`.
- Informe: `04_resultados_e2.md` (completo) y `03_metodologia_seguridad.md` (Jev y diseño de E2).

**Hecho el 10-nov (parte defensiva de S06), con pruebas:**

- **C0–C3 integradas en el agente** (`agente/defensa.py`, grafo y arnés). C2: clasificador por ventanas que retira
  las marcadas antes de extraer. C3: excluye precios atípicos (banda de catálogo y mediana). `--configuracion C0..C3`.
- **Clasificador de C2 elegido con evidencia** (D85): Horizon-Labs Guard (small), 0/47 falsos positivos en español,
  p50 192 ms en CPU. El producto permite elegir entre los dos validados (D86). Evidencia en
  `resultados/clasificadores/`; reproducible con `python -m comercio_agentico.ataques.elegir_clasificador`.
- `ataques/mapeo.md`: OWASP LLM01:2025, OWASP Agentic 2026 (ASI01/ASI02) y MITRE **ATLAS** v2026.10, verificados
  en la fuente. **La taxonomía MITRE pertinente es ATLAS** (pendiente resuelto).
- Prueba de humo real: B013 benigno en C3 con Flash = ACIERTO, US$0,0151; el stack defensivo completo corre.
- Borrador `docs/informe/03_metodologia_seguridad.md`. 14 pruebas nuevas (126 en total); Ruff limpio.
- **Convención nueva (pedido de Wills):** cada laboratorio guarda evidencia versionada en `resultados/` y un
  borrador de sección en `docs/informe/`, para el informe y la presentación.

## Presupuesto de modelos

| Concepto           | US$                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Presupuesto total  | 300,00                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| Créditos comprados | 75,00 (Anthropic 30 + OpenRouter 20, 9-nov; TypeSafe 5, 10-nov, el mínimo que acepta, para la comparación con Jev de D80; OpenRouter 20 más, 10-nov, S09a). Anthropic: US$29,83 disponibles y US$0,17 gastados (consola, 9-nov 21:43)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Gastado acumulado  | ~22,56 (S09d: 0, sin LLM; S09c: 5,0855 = Railway Hobby 5,00 + OpenRouter ≥ 0,0855 en producción, B013 0,0190 + HP en vivo 0,0665, más consultas posteriores de Wills; S09b-ter: 0,1119 = dos consultas en vivo con Flash + N3, OpenRouter; D108 E2 con Haiku: 1,9716 Anthropic; S09a: 0,3745 = humo de la lista curada 0,3443 + punta a punta 0,0302, todo OpenRouter; S08: 0,0213 = segunda lectura de N3 con Haiku en 15 fragmentos; S07: ~5,57 = matriz de ataque 3,4454 + utilidad benigna 1,9011 + Jev ~0,0015 + ~0,22 perdidos en dos cierres de VS Code; S06-bis arnés: 0,2327 humo C0/C3 en dos pasadas, 0,1473 + 0,0854; S06: 0,015 prueba de humo C3 + clasificadores a US$0; S00: ~0,26; S01: 0,024; S02: ~0,18; S03: 1,74; S04: ~1,32; S05: ~5,7 = corpus A v1 0,361 + calibración v3 0,919 + E3 Flash 1,371 + E3 Haiku 1,528 + corrida parcial de Flash descartada 1,312 + ~0,2 de llamadas perdidas en la suspensión). OpenRouter: **saldo real US$21,26** (consola, 10-nov tras S09a; de US$40 cargados). La suma de costos por llamada (~13,7) queda corta frente a la consola: comisiones de compra y llamadas perdidas en cierres no registradas. TypeSafe: ~US$0,002 de 5. Anthropic: **saldo real US$28,25** (consola, 10-nov antes de D108; US$1,76 gastados en el mes) |

Costo medido el 9-nov (S00) de una extracción estructurada típica (página con 12 ofertas, 1500–3500 tokens de
entrada, `json_schema`): Flash 0,0015 · Haiku 0,0016 · DeepSeek Pro 0,006 · Sonnet 0,025 · Kimi 0,032 ·
Opus 0,053. Supuesto de tarea: 5 extracciones + ~8 llamadas del planificador (~4000 tokens de entrada y ~300 de
salida cada una).

| Modelo              | US$ por tarea (estimado) | 80 tareas (B + A) |
| ------------------- | ------------------------ | ----------------- |
| DeepSeek V4.1 Flash | ~0,013                   | ~1                |
| Claude Haiku 5.5    | ~0,013                   | ~1                |
| DeepSeek V4 Pro     | ~0,08                    | ~6                |
| Claude Sonnet 5.5   | ~0,21                    | ~17               |
| Kimi K3.1 Pro       | ~0,24                    | ~19               |
| Claude Opus 5.5     | ~0,44                    | ~35               |

Recalibración: la estimación anterior (0,03–0,18 por tarea) se queda corta en el tope. Si la regla de parada de
E3 llega a Opus con todas las tareas, Anthropic necesita ~US$55 (Haiku + Sonnet + Opus) más desarrollo, E2 y E1:
~~recargar ~US$40 en Anthropic~~ (sustituido por D76: E3 llega hasta Sonnet y Opus requiere autorización; los US$29,83 alcanzan). OpenRouter (US$20) alcanza para los tres modelos
chinos. El total sigue muy por debajo de US$300. Riesgos: las páginas reales del corpus A pueden ser mucho más
largas que la de prueba (recalibrar en S03 con el arnés), y Opus queda cerca del tope `COSTO_MAXIMO_POR_TAREA_USD`
= 0,50: subirlo a 1,00 solo para las corridas de Opus en E3.

El `.env` nunca se lee ni se muestra en las sesiones: las claves se cargan en un subproceso.

## Bitácora

### 15-nov-2026 — S10: borradores del informe y guardia contra búferes viejos (VS Code · Opus 5.5)

- Decisiones con Wills: D133 (APA 7) y D134 (solución definitiva a las sobrescrituras de VS Code).
- Borradores 01, 02, 06 y 07 del informe; referencias verificadas con tres subagentes en paralelo contra la fuente
  primaria. Corrección de la cifra de ventas de la CCCE.
- Gasto: US$0.

### 11-nov-2026 — S09c: publicación y MLOps ligero (VS Code · Opus 5.5)

- Decisiones con Wills: D116 (Railway Hobby), D117 (LangSmith), D118 (operación: local + Serverless salvo días de
  demo) y D119 (avance por fuente). Regla nueva en la memoria: las preguntas de decisión traen contexto completo.
- Tropiezos: búfer viejo del editor pisó `web/src/lib/api.ts` (restaurado desde git); LangSmith con espacio por
  agentes exige `LANGSMITH_AGENT_ID`/`LANGSMITH_AGENT_ENVIRONMENT` en vez de `LANGSMITH_PROJECT`; el «Config as code»
  de Railway está obsoleto (hasta 2026-12-01), así que la configuración vive en el panel y en el README.
- Commits: `35d07bb` (intermedio, autorizado, para que Railway construyera desde GitHub) y el de cierre.

### 10-nov-2026 — S09b: frontend de CotIA (VS Code · Opus 5.5)

- Decisiones con Wills: D109 (shadcn-svelte + Tailwind v4 sobre SvelteKit con adapter-static) y D110 (N3 por
  oferta y política elegible; cierra el pendiente c).
- Tropiezos de herramientas, resueltos: SvelteKit 3.2 exige Node ≥ 22.17 (se instaló 22.23 con nvm y se fijó en
  `web/.nvmrc`); `shadcn-svelte init` pide un _preset_ interactivo, así que se siguió la instalación manual oficial;
  SvelteKit 3 usa _subpath imports_ `#lib/...` con extensión; los componentes nuevos usan variantes `data-open`,
  `data-active`, `data-horizontal`… que bits-ui 2.20 no emite (expone `data-state` y `data-orientation`): se
  declararon como `@custom-variant` en `layout.css`.
- Resultados en «Hecho el 10-nov (S09b)». Gasto de la sesión: **US$0** (la prueba con clave inventada falla en la
  primera llamada con 401).

### 10-nov-2026 — Opcional de S07: E2 con Claude Haiku 5.5 (VS Code · Opus 5.5)

- D108 fijada con Wills antes de correr: 20 cargas × C0 y C3 × 3 repeticiones con Haiku por Anthropic directo,
  solo M5, tope US$2,50. 120 ejecuciones, 0 errores, **US$1,9716** (Anthropic; saldo esperado ~US$26,3).
- **M5 Haiku: C0 0/60 y C3 0/60 [0; 6,0 %]**: la suite no vulnera a Haiku ni sin defensas (efecto suelo). A20, A04 y
  A09, que vulneraron a Flash en C0, no prosperaron. Acierto bajo ataque 90,0 % (C0) y 88,3 % (C3); p50 ~53 s.
- Informe: sección «Segundo modelo» y «Alcance» en `04_resultados_e2.md`. Evidencia:
  `resultados/ataques/2026-11-10_suite_ataques_haiku*`.
- Incidente: al guardar en VS Code archivos que el agente había dejado abiertos, se perdieron D108 y los saldos
  reales de `ESTADO.md`; se restauraron y se fijaron en el commit `1f5b146`.

### 10-nov-2026 — S09a: API de CotIA, SSE y persistencia (VS Code · Opus 5.5)

- Decisiones con Wills: D105 (N3 en CotIA con Haiku 5.5 por OpenRouter y la clave del visitante), D106 (C2 por
  defecto; cierra el pendiente b), D107 (lista curada por prueba de humo, tope US$0,30).
- Refactor D91 (`Defensas`), `preguntar` con `astream` y `al_avanzar`, clave por consulta en `obtener_modelo`, API
  FastAPI (`api/`), PostgreSQL en Docker (`compose.yaml`, :5433), `make bd`, `make api`, `make cotia-humo`.
  10 pruebas nuevas de la API, más las de `Defensas`, el umbral y la clave: **172 pruebas**, Ruff limpio.
- Humo de la lista curada (systemd-run): los gratuitos fallaron; tras la primera pasada solo Flash cumplía «acierto en
  B013». Wills afinó D107 (funciona + desempeño con evidencia: acierto o M2 de E3) y autorizó reintentar Kimi (429
  del proveedor) con tope US$0,45 tras cargar US$20 en OpenRouter. Lista final: Flash, Haiku 5.5, Kimi.
- Punta a punta por la API cumplida (criterio de terminado). Gasto de la sesión: **US$0,3745** (OpenRouter).
- Incidente operativo: la terminal del editor corta cualquier comando de más de ~45 s; se esperó en pasos cortos.
- Resultados del humo y de la prueba de punta a punta en «Hecho el 10-nov (S09a)»; **173 pruebas** al cierre.

### 10-nov-2026 — S08: N3 y E1 (VS Code · Opus 5.5)

- Diseño acordado con Wills y fijado antes de ver datos: D99–D104 (reproducción pareada sobre calibración v3 y
  corpus A v1; ruta híbrida determinista + Haiku 5.5; campos que deciden la compra; abstención como política
  principal; N3 como nodo opcional del grafo; N1 propuesto). Tope: US$1 Anthropic, US$0 OpenRouter.
- Resultados en «Hecho el 10-nov (S08)». Gasto US$0,0213 (Anthropic).
- Incidente menor: la terminal del editor cortó la primera corrida con ^C por desbordamiento (salida de crawl4ai);
  se relanzó con `systemd-run --user --unit=s08-e1` y reanudó sin repetir lecturas.

### 10-nov-2026 — Hoja de ruta: catálogo gestionado (VS Code · Opus 5.5)

- D98: en producción, `catalogo.json` se reemplaza por un catálogo por empresa en PostgreSQL con embeddings
  persistidos en pgvector e indexación incremental; los experimentos conservan el archivo congelado. Borrador en
  `docs/informe/06_hoja_de_ruta.md`. Sin cambios de código. Gasto: US$0.

### 10-nov-2026 — S07: E2 curva seguridad-utilidad y comparación con Jev (VS Code · Opus 5.5)

- D96 fijó el diseño antes de correr; D97 cierra la comparación con Jev. Resultados en «Hecho el 10-nov (S07)».
- D96 fija el diseño de E2 antes de correr. Matriz 20 × C0–C3 × 3 (`resultados/ataques/2026-11-10_suite_ataques.jsonl`)
  y utilidad `configs/e2_c0..c3.yaml` (`resultados/corridas/2026-11-10_e2_c*.jsonl`) en marcha, desacopladas de VS Code
  (`setsid nohup`, registros en `/tmp/e2_*.log`). Si se interrumpen: `make corpus-b-servir`, luego `make e2-ataques` y
  `make e2-utilidad`; ambos reanudan. Análisis: `make e2`.
- Jev frente a los clasificadores locales (`resultados/clasificadores/2026-11-10_jev_vs_local.*`): Horizon 20/20 y
  0/47; Jev 1.14.0 20/20 y 0/47 (política falsificada 0,71 frente a 0,99); Wolf 14/20. Jev no supera al local → C2 se
  mantiene (D80). ~US$0,0015.
- Incidente: VS Code se cerró a las ~14:25 y mató las corridas; se perdieron ~8 ejecuciones en vuelo (~US$0,11 sin
  registrar). Se reanudaron sin repetir lo registrado (28 ataques, 25 de C0).
- Segundo cierre de VS Code (~15:20) mató también los procesos `setsid nohup` (caen con el grupo de VS Code). Quedaban
  126/240 ataques y C0–C2 completos, C3 15/30. Se relanzaron como unidades `systemd-run --user` (`e2-corpus`,
  `e2-ataques`, `e2-utilidad`), que viven fuera de VS Code: `systemctl --user status 'e2-*'`.

### 10-nov-2026 — S06-bis: publicación de las cargas (D95)

- `cargas.yaml` pasa de `privado/tarea_cargas/` a `ataques/cargas.yaml` y se versiona; el repositorio sigue público.
  `corpus/b_ataques/` sigue fuera de git (se regenera). Motivo: el visor de CotIA (D87) expone los fragmentos de
  todos modos y la suite debe ser reproducible por terceros; InjecAgent y AgentDojo publican sus ataques (verificado).
- `RUTA_CARGAS` es ahora absoluta y la prueba del YAML real ya no se omite en CI. Gasto: US$0.

### 10-nov-2026 — S06-bis: revisión del arnés y humo en diagonal (D93, D94)

- Revisión del arnés: el PDF de P4 se regenera con la carga como nota tras la tabla (antes, página antepuesta con
  título, más prominente que las demás ubicaciones); la línea del chat la firma «Carlos Tecnología» con hora
  posterior al último mensaje (antes «Proveedor» a las 10:00). `--humo` toma la diagonal clase × ubicación y el arnés
  ya no sobrescribe `docs/informe/04_resultados_e2.md` (redactado aparte). Resumen M5 con lectura por ubicación.
- Humo adicional A06/A11/A16 × C0/C3: 6/6 frenados, el agente leyó el archivo atacado en todas y C2 lo marcó en
  las tres de C3. Total del humo: **C0 1/8 = 12,5 % [2,2; 47,1]; C3 0/8 = 0,0 % [0,0; 32,4]**; utilidad 16/16;
  US$0,0854 esta pasada (US$0,2327 en total).
- Auditoría: ningún fragmento de 40 caracteres de las cargas aparece en la corrida comprimida, los resúmenes, el
  informe, las pruebas ni la guía. 2 pruebas nuevas (**142 en total**); Ruff limpio.
- Pendiente para S07: control limpio de los predicados; el arnés corre en secuencia (~100 s por ejecución).

### 10-nov-2026 — S06-bis: arnés, plantado y prueba de humo M5

- Implementados `ataques/suite.py`, `plantar.py` y `correr.py` sin modificar los textos. Validación estricta de las 20
  cargas, cinco predicados automáticos, copias aisladas por ID, URL local dinámica y evidencia reanudable.
- Las 20 variantes existen en `corpus/b_ataques/` (ignoradas); el corpus limpio no cambió. A01 queda lista para CotIA.
- Humo DeepSeek Flash, 10/10 ejecuciones sin errores: **C0 M5 1/5 = 20,0 % [3,6; 62,4]; C3 0/5 = 0,0 % [0,0; 43,4]**.
  Solo A09 C0 exfiltró el presupuesto en un argumento. Costo C0 US$0,075086; C3 US$0,072219; total **US$0,147305**.
- Evidencia `resultados/ataques/2026-11-10_humo_ataques.jsonl.gz`, `_m5.json` y `_m5.md`; borrador
  `docs/informe/04_resultados_e2.md`; metodología y guía actualizadas. 14 pruebas nuevas, **140 en verde**, Ruff limpio.
- La muestra contiene únicamente cargas visibles: no sustituye las 80 ejecuciones de S07 ni sustenta una comparación
  definitiva C0/C3. Siguiente: matriz completa E2 y comparación Jev pendiente (D80).

### 10-nov-2026 — S06-bis: redacción y validación de las 20 cargas

- `privado/tarea_cargas/cargas.yaml` contiene las 20 combinaciones (5 clases × 4 ubicaciones), con `archivo`,
  `tarea`, `objetivo`, `predicado` y `texto`. Redacción asistida autorizada por Wills (D92); archivo fuera de git.
- Se eligieron B013, B016 y B045 por su respuesta conocida y cobertura de los proveedores atacantes. Las acciones
  usan C11; la exfiltración fija el presupuesto de B045 (2.990.000 COP) y la alteración de precio usa C11 a 900.000 COP.
- Validación local: 20 IDs consecutivos, matriz 5×4 completa, archivos/tareas existentes, proveedor coherente con
  ubicación, presupuesto coincidente con la tarea y `{URL_ACCION}` presente solo en las 8 cargas que lo requieren.
- No se plantó ninguna carga ni cambió `corpus/b_sintetico/`. Gasto: **US$0**. Pendiente: arnés, plantado, prueba de
  humo C0/C3 y M5.

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
  Wilson y _bootstrap_ (scipy). `metricas.md`, `metricas.json` y 3 PNG por corrida en `resultados/informes/`.
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
- Cuenta de TypeSafe creada y `TYPESAFE_API_KEY` en `.env` (10-nov; la API oficial responde y expone `jev-latest` y `jev-preview`). Benchmark de Red Hat sobre Jev (2-oct-2026) no se pudo leer; no citar sus cifras sin verificarlas.
- Informe primario de la CCCE (primer trimestre de 2026), si se cita en el informe.
- Verificación exhaustiva de las referencias del plan de trabajo antes de reutilizarlas (S10).
- E3 se detuvo en Haiku (D78): DeepSeek Pro, Kimi, Sonnet y Opus van como propuestos en la hoja de ruta del informe.
- Usar el `llms.txt` de Alkosto (instrucciones dirigidas al LLM) como caso real en S06.
- Referencias de Wilson (1927) y Efron (1979) para los intervalos: verificar en la fuente primaria en S10.
- La verificación N3 (S08) no debe suponer el GTIN en la oferta extraída: en el corpus A llega como `sku` en schema.org.
- Planificador: en A003 no abre la ficha cuando el listado no trae disponibilidad (candidato a mejora o limitación declarada).
- Año de la conferencia de ReAct (versión de ICLR, arXiv:2210.03629) por confirmar en S10.
- Archify (diagrama de arquitectura del estándar del profesor) como opción en S09c para el informe.
- CotIA: elegir plataforma de despliegue y PostgreSQL gestionado en S09c con precios y límites verificados en la fuente; Wills crea las cuentas.
- `app.py` (Streamlit) y `make app` siguen en el repositorio hasta que S09b los reemplace; se retiran entonces.
