# Comercio agéntico: del comprador al proveedor

[![CI](https://github.com/777wills/comercio-agentico/actions/workflows/ci.yml/badge.svg)](https://github.com/777wills/comercio-agentico/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.13-blue)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-green)](LICENSE)

Prototipo de agente de compras verificable sobre proveedores heterogéneos, con defensa medida frente a inyección
indirecta de instrucciones. Proyecto III de Innovación Tecnológica en IA — Maestría en IA Aplicada, Universidad
Icesi (2026-2).

## Contenido

- [Qué hace](#qué-hace)
- [CotIA, el producto](#cotia-el-producto)
- [Arquitectura](#arquitectura)
- [Correr CotIA en local](#correr-cotia-en-local)
- [Reproducir los experimentos](#reproducir-los-experimentos)
- [Despliegue y operación](#despliegue-y-operación)
- [Estructura](#estructura)
- [Corpus, licencias y límites legales](#corpus-licencias-y-límites-legales)
- [Documentación](#documentación)
- [Licencia](#licencia)

## Qué hace

Recibe una necesidad de compra en lenguaje natural, consulta proveedores con distintos niveles de madurez digital
(servidor MCP, web con schema.org, web plana, PDF y mensajería), extrae ofertas a un esquema canónico con
procedencia obligatoria y entrega una propuesta comparativa trazable, o se abstiene. No ejecuta pagos.

La seguridad se mide, no se supone: el contenido de los proveedores es dato, nunca instrucción (separación de
planos), y una suite de 20 cargas de inyección indirecta evalúa cuatro configuraciones de defensa (C0–C3).

## CotIA, el producto

**URL pública:** <https://comercio-agentico-production-bf030669.up.railway.app> (Railway, D116).

- **Modo Cliente** (`/`): consulta en lenguaje natural sobre proveedores de prueba (corpus B), tiendas colombianas
  reconstruidas (corpus A) o tiendas en vivo de una lista blanca; progreso en vivo, recomendación con su fuente y
  sello de verificación N3, alertas y costo.
- **Modo Laboratorio** (`/lab`): las 20 cargas de ataque con C0 frente a C3 sobre el mismo modelo, visor del corpus
  original y atacado, resultados de E1–E3 con intervalos de confianza, historial y configuración completa.
- **Clave propia del visitante (D82, D114):** CotIA no trae créditos. Cada consulta se paga con la clave de
  OpenRouter o de Anthropic del visitante (el proveedor se reconoce por el prefijo `sk-or-` o `sk-ant-`), que vive en
  su navegador, viaja por HTTPS solo al crear la consulta y no se guarda ni se registra. Con la de Anthropic solo se
  ofrecen los modelos Claude y el costo se muestra como estimado (tokens × tabla de precios).
  Los modelos ofrecidos son los que superaron la prueba de humo de la lista curada
  ([`resultados/cotia/modelos.json`](resultados/cotia/modelos.json)).

## Arquitectura

```text
Navegador (SvelteKit estático)  ──HTTPS──▶  FastAPI (mismo proceso que el agente)  ──▶  PostgreSQL
                                   ◀──SSE──       │  cola: 1 consulta en curso, 5 en espera
                                                  ▼
                                   Agente LangGraph: intérprete → planificador ReAct → extractor
                                   → emparejamiento (embeddings + LLM) → reglas → verificación N3
                                                  │
                     ┌───────────────┬────────────┼──────────────┬────────────────┐
                     ▼               ▼            ▼              ▼                ▼
                MCP (P1)    Web schema.org /  PDF (P4)    Mensajería (P5)   Tiendas en vivo
                            web plana (crawl4ai + Chromium)                 (robots.txt, SSRF)
```

Un solo contenedor Docker (D81) incluye el frontend compilado, la API, Chromium, el modelo de embeddings
(`intfloat/multilingual-e5-small`) y los dos clasificadores de inyección validados para C2. El corpus congelado se
regenera dentro de la imagen desde lo versionado.

## Correr CotIA en local

Requisitos: Docker. No hace falta clave para navegar; para consultar, la clave de OpenRouter o de Anthropic se pega
en Ajustes.

```bash
git clone https://github.com/777wills/comercio-agentico.git && cd comercio-agentico
make cotia-docker             # construye la imagen de producción y levanta PostgreSQL (US$0)
# abrir http://127.0.0.1:8080
```

Para desarrollar sin Docker para la aplicación (Python 3.13 con [uv](https://docs.astral.sh/uv/) y Node ≥ 22.17):

```bash
make dev                      # uv sync + hooks de pre-commit
cp .env.example .env          # claves solo para los experimentos; CotIA no las usa
make check                    # lint + formato + pruebas (sin red, US$0)
make corpus-a                 # reconstruye las tiendas del corpus A desde los hechos (US$0)
uv run python -m comercio_agentico.ataques.plantar   # variantes atacadas del corpus B (US$0)
make web                      # compila el frontend a web/build
make bd && make api           # PostgreSQL en Docker (:5433) y API + frontend en :8000
```

## Reproducir los experimentos

Los costos son estimados con DeepSeek V4.1 Flash por OpenRouter. Los objetivos marcados US$0 reanalizan las
corridas versionadas en `resultados/` sin llamar a ningún modelo. Las corridas con modelo necesitan `.env` y el
corpus servido (`make corpus-b-servir`, y `make corpus-a-servir` para el corpus A).

| Experimento                       | Corrida (costo)                                            | Análisis (US$0)           | Resultados                                                              |
| --------------------------------- | ---------------------------------------------------------- | ------------------------- | ----------------------------------------------------------------------- |
| Arnés de prueba                   | `make arnes-simulado` (US$0, agente simulado)              | —                         | —                                                                       |
| Calibración (corpus B, 60 tareas) | `make calibracion` (~US$1)                                 | `make metricas CORRIDA=…` | [`resultados/informes/`](resultados/informes/)                          |
| Corpus A (20 tareas reales)       | `make corpus-a-correr` (~US$0,3)                           | `make metricas CORRIDA=…` | [`04_resultados_corpus_a.md`](docs/informe/04_resultados_corpus_a.md)   |
| E1: verificación N3               | `make e1-lecturas` (~US$0,02)                              | `make e1`                 | [`04_resultados_e1.md`](docs/informe/04_resultados_e1.md)               |
| E2: curva seguridad-utilidad      | `make e2-ataques` (~US$3,7) y `make e2-utilidad` (~US$1,8) | `make e2`                 | [`04_resultados_e2.md`](docs/informe/04_resultados_e2.md)               |
| E3: comparación de modelos        | `make e3 MODELO=flash` (~US$1,5 por modelo)                | `make e3-frontera`        | [`04_resultados_e3.md`](docs/informe/04_resultados_e3.md)               |
| C2 en páginas reales (D115 b)     | `make c2-reales` (US$0, sin LLM; lee tiendas en vivo)      | `make c2-reales-analisis` | [`04_resultados_c2_reales.md`](docs/informe/04_resultados_c2_reales.md) |

`make help` lista todos los objetivos con su costo.

## Despliegue y operación

- **Plataforma (D116):** Railway, plan Hobby. Un servicio construido desde el `Dockerfile` de la raíz y PostgreSQL
  gestionado en el mismo proyecto. Variables del servicio:

    | Variable                      | Valor                                                            |
    | ----------------------------- | ---------------------------------------------------------------- |
    | `DATABASE_URL`                | `${{Postgres.DATABASE_URL}}` (referencia a la base del proyecto) |
    | `LANGSMITH_TRACING`           | `true` (opcional, trazas de D117)                                |
    | `LANGSMITH_ENDPOINT`          | `https://api.smith.langchain.com`                                |
    | `LANGSMITH_API_KEY`           | clave de LangSmith (variable sellada)                            |
    | `LANGSMITH_AGENT_ID`          | `cotia` (agente registrado en LangSmith)                         |
    | `LANGSMITH_AGENT_ENVIRONMENT` | `production`                                                     |

    El servicio **no** lleva claves de Anthropic ni de OpenRouter: cada consulta usa la del visitante. Comprobación
    de salud en `/api/salud`; con «Wait for CI», Railway solo despliega los commits de `main` cuyo CI pasó.

- **Integración continua:** GitHub Actions corre pre-commit (Ruff, higiene, `uv.lock`), regenera el corpus y
  comprueba que coincide con lo versionado, ejecuta las pruebas, una prueba de humo del arnés con el agente
  simulado y la verificación de tipos y compilación del frontend.
- **Trazas (D117):** con las variables de LangSmith, cada consulta queda registrada paso a paso (prompt, respuesta,
  tokens, latencia y costo) durante 14 días. La clave del visitante no viaja en las trazas (prueba automatizada
  en `tests/test_modelos.py`) y la interfaz avisa del registro.
- **Recursos:** ~270 MB de RAM en reposo y ~2 GB durante una consulta; una consulta a la vez.

## Estructura

```text
src/comercio_agentico/   agente (LangGraph), esquema canónico, modelos, defensas, verificación N3 y API
  agente/                grafo, herramientas por tipo de proveedor, defensas C0–C3, modo en vivo
  api/                   FastAPI de CotIA: consultas, SSE, historial, fuentes del visitante, visor del corpus
  arnes/                 corridas reproducibles, métricas M1–M6 y análisis de E1–E3
  ataques/               suite adversarial: plantado, ejecución y predicados de éxito
  corpus_a/ corpus_b/    construcción y servidores de los dos corpus
web/                     frontend SvelteKit (modos Cliente y Laboratorio)
corpus/                  corpus A (hechos) y corpus B (proveedores sintéticos) congelados
ataques/                 las 20 cargas (cargas.yaml) y su mapeo a OWASP y MITRE ATLAS
configs/ tareas/         configuraciones de corrida y tareas con su verdad
resultados/              corridas comprimidas, informes, figuras y evidencia de cada experimento
docs/                    plan, decisiones, estado, guía de pruebas y borradores del informe
```

## Corpus, licencias y límites legales

- **Corpus B** es sintético (proveedores y productos ficticios) y se versiona completo.
- **Corpus A** proviene de tres tiendas colombianas reales. Sus términos permiten el rastreo en robots.txt pero
  prohíben copiar el contenido, así que **no se versionan las páginas**: solo los hechos extraídos de cada ficha
  (precio, disponibilidad, GTIN, título y fuente) y un manifiesto con sumas de verificación. Las tiendas se
  reconstruyen con plantillas propias (`make corpus-a`). Detalle en
  [`03_metodologia_corpus.md`](docs/informe/03_metodologia_corpus.md).
- **Tiendas en vivo:** solo las de la lista blanca, tras revisar robots.txt y términos de uso; robot identificable
  (`ComercioAgenticoBot/0.1`), pausa entre peticiones y bloqueo de direcciones internas. Se guardan los hechos de
  cada oferta y un fragmento corto como procedencia, nunca la página completa. Las cargas de ataque nunca se
  plantan en sitios reales.
- **Modelos locales:** `intfloat/multilingual-e5-small` (MIT), `Horizon-Labs/prompt-injection-guard-small` y
  `patronus-studio/wolf-defender-prompt-injection` (Apache-2.0).

## Documentación

- [`CONSTITUTION.md`](CONSTITUTION.md): propósito, alcance, stack, convenciones y flujo.
- [`docs/DECISIONES.md`](docs/DECISIONES.md): decisiones y su justificación.
- [`docs/PLAN.md`](docs/PLAN.md): plan de ejecución por sesiones.
- [`docs/GUIA_PRUEBAS.md`](docs/GUIA_PRUEBAS.md): qué se construyó en cada sesión y cómo probarlo sin costo.
- [`docs/informe/`](docs/informe/): borradores de las secciones del informe.

## Licencia

[MIT](LICENSE) © 2026 William Suaza Losada.
