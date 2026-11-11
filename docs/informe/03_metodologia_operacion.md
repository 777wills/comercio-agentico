# 3. Metodología — Operación de CotIA: despliegue, integración continua y observabilidad

## 3.x Plataforma de despliegue

CotIA se publica como un solo contenedor Docker que reúne el frontend compilado (SvelteKit), la API (FastAPI) y el
agente (LangGraph), con PostgreSQL gestionado aparte (D81). La plataforma se eligió por los requisitos medidos del
producto y no por preferencia: ~0,27 GB de memoria en reposo, ~2 GB durante una consulta (Chromium de crawl4ai, el
modelo de embeddings `intfloat/multilingual-e5-small` y el clasificador de inyección de C2), salida a internet para
el modo en vivo y una sola instancia, porque la cola de la API atiende una consulta a la vez.

| Candidata (precios oficiales, 11-nov-2026) | Memoria disponible | Base de datos | Costo para el periodo | Observación |
|---|---|---|---|---|
| Railway, plan Hobby | hasta 48 GB por servicio | PostgreSQL en el mismo proyecto | US$5/mes con US$5 de uso incluido; US$10/GB-mes de RAM | Elegida (D116) |
| Google Cloud Run | hasta 32 GiB | externa | nivel gratuito de 240.000 vCPU-s y 450.000 GiB-s al mes | Arranque en frío de una imagen de varios GB |
| Hugging Face Spaces (Docker) | 16 GB | — | requiere PRO, US$9/mes | La salida solo admite los puertos 80, 443 y 8080: bloquea PostgreSQL |
| Render | 2 GB en el plan de US$25/mes | US$6/mes | ~US$31/mes | Plan gratuito de 512 MB insuficiente |

## 3.y Imagen, integración y entrega continuas

La imagen se construye en tres etapas: Node compila el frontend, uv instala las dependencias de Python desde el
archivo de bloqueo (`uv.lock`, PyTorch solo CPU) y la etapa final añade Chromium con sus bibliotecas de sistema y
los pesos de los modelos locales, de modo que el contenedor corre sin acceso al Hub de Hugging Face
(`HF_HUB_OFFLINE=1`). Las capas pesadas preceden al código para que un cambio de código no las reconstruya. El
corpus que no se versiona se regenera dentro de la imagen desde lo versionado: las tiendas del corpus A desde sus
hechos y las variantes atacadas del corpus B desde `ataques/cargas.yaml` (D95). El proceso corre con un usuario sin
privilegios. La imagen resultante ocupa 6 GB (3,1 GB comprimida).

La integración continua (GitHub Actions) ejecuta, en cada cambio, los ganchos de calidad (Ruff, higiene del
repositorio y coherencia del archivo de bloqueo), regenera el corpus y comprueba que coincide byte a byte con lo
versionado, corre las pruebas (197), una prueba de humo del arnés con el agente simulado y la verificación de tipos
y compilación del frontend. Railway despliega solo los cambios de la rama principal cuya integración continua
terminó con éxito, y sustituye la versión anterior únicamente si la nueva responde en `/api/salud`.

## 3.z Observabilidad

Cada consulta deja dos registros. El primero, propio, vive en PostgreSQL: la consulta, la configuración de
defensas, los eventos de progreso, la propuesta, el costo y la duración. El segundo es la traza de LangSmith (D117):
el árbol de pasos del grafo con cada llamada al modelo (mensajes, respuesta, tokens, latencia y costo) y cada
herramienta. LangGraph emite la traza de forma nativa, por lo que se activa solo con variables de entorno en el
despliegue; el desarrollo local, las pruebas y la integración continua no trazan. Una prueba automatizada comprueba
que la clave de OpenRouter del visitante no aparece en lo que recibe el trazador, y la búsqueda de su prefijo en
la traza de producción no arrojó coincidencias. La interfaz informa al visitante que las consultas se registran
para diagnóstico durante 14 días.

## 3.w Seguridad operativa

El servicio no lleva claves de proveedores de modelos: cada consulta usa la del visitante, que no se guarda ni se
registra (D82). La única credencial del servicio, la de LangSmith, se almacena como variable sellada, que la
plataforma entrega al contenedor pero no muestra ni devuelve por API. La base de datos no tiene acceso público; la
API la alcanza por la red privada del proyecto. El modo en vivo conserva sus salvaguardas: lista blanca, bloqueo de
direcciones internas, robots.txt y robot identificable (D112).

## 3.v Operación y costo

Las métricas de producción mostraron que, tras la primera consulta, el proceso retiene ~2,1 GB: los modelos locales
se mantienen cargados para no repetir su carga y el intérprete no devuelve la memoria al sistema operativo; Chromium,
en cambio, se cierra al terminar cada consulta. Con la tarifa de memoria de la plataforma, mantener el servicio
encendido costaría ~US$0,70 diarios. La operación adoptada (D118) desarrolla y prueba en local con la misma imagen,
mantiene el servicio en modo de suspensión por inactividad y lo deja encendido solo los días de demostración, con
una consulta de calentamiento. Con ello el costo de infraestructura queda en la suscripción mensual.

## 3.u Prueba de humo en producción

La tarea B013 del corpus B («¿dónde sale más barato el monitor Samsung Smart Monitor M8 M80D contando el envío?»),
con DeepSeek V4.1 Flash, defensa C2 y verificación N3, recomendó el proveedor P4 por $2.732.000 más $25.000 de
envío, que coincide con la verdad del corpus, con las cinco ofertas del producto verificadas por N3; costó
US$0,0190 y tardó 100 s. En el modo en vivo, una consulta por un producto ficticio del corpus B recorrió 17 páginas
de las cinco tiendas reales en cuatro rondas y se abstuvo correctamente tras 594 s (US$0,066). Esa consulta expuso
tres límites del modo en vivo en producción: ~35 s por página con 2 vCPU, la caída de una pestaña de Chromium por
memoria (3,7 GB con un tope de 4 GB) y la retirada de texto comercial legítimo por el clasificador de C2 (D115 b).
