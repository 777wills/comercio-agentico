# CONSTITUTION — Comercio agéntico

Fuente única de verdad sobre **qué es** el proyecto y **cómo se trabaja** en él. El detalle vive en documentos
especializados a los que esta constitución remite; no se duplica aquí.

| Tema | Documento |
|---|---|
| Decisiones y su porqué (historial) | [`docs/DECISIONES.md`](docs/DECISIONES.md) |
| Plan por sesiones, entregables y criterios de terminado | [`docs/PLAN.md`](docs/PLAN.md) |
| Estado actual, gasto y siguiente paso | [`docs/ESTADO.md`](docs/ESTADO.md) |
| Instrucciones para agentes de código | [`CLAUDE.md`](CLAUDE.md) |
| Borradores del informe | [`docs/informe/`](docs/informe/) |

## 0. Identidad

| Campo | Valor |
|---|---|
| Nombre | Comercio agéntico: del comprador al proveedor |
| Repositorio | [`777wills/comercio-agentico`](https://github.com/777wills/comercio-agentico) (público) |
| Autor | William Suaza Losada |
| Contexto | Proyecto III de Innovación Tecnológica en IA — Maestría en IA Aplicada, Universidad Icesi (2026-2) |
| Licencia | MIT |

## 1. Propósito y no-propósito

**Propósito.** Prototipo de agente de compras verificable sobre proveedores heterogéneos (MCP, web con schema.org,
web plana, PDF y mensajería), que entrega una propuesta de compra trazable hasta el fragmento de origen de cada
cifra y mide su defensa frente a la inyección indirecta de instrucciones.

**No-propósito.** No ejecuta pagos ni compras, no es un comparador de precios en producción y no rastrea sitios
reales más allá del corpus A pequeño, fechado y no publicado.

## 2. Alcance

Cuatro capas (D10, D11): **N2** agente navegador, **N4** defensa, **N3** verificación y **N1** consumo
determinista (al final o propuesto). Experimentos **E3** (modelos), **E2** (seguridad-utilidad) y **E1**
(verificación); **E4** (transferencia de dominio) queda propuesto (D40). El alcance por sesión está en el plan.

## 3. Stack técnico

| Categoría | Tecnología |
|---|---|
| Lenguaje y entorno | Python 3.13, [`uv`](https://docs.astral.sh/uv/) (`uv.lock` versionado; sin `pip` ni `requirements.txt`) |
| Agente | LangGraph / LangChain 1.x |
| Modelos | Anthropic directo; modelos de pesos abiertos por OpenRouter con proveedor fijado (D30–D33) |
| Contenido web | crawl4ai (Playwright → Markdown) |
| Esquema y validación | Pydantic 2 |
| Proveedor sintético por MCP | FastMCP |
| Interfaz | Streamlit |
| Calidad | Ruff, pre-commit, pytest; CI en GitHub Actions |

## 4. Estructura

```text
src/comercio_agentico/   código del paquete (src-layout)
  esquema.py             Oferta, Procedencia, PerfilCategoria, PropuestaCompra
  modelos.py             fábrica de los seis modelos y registro de tokens y costo
  ping.py                prueba de humo de los modelos
perfiles/                perfiles de categoría declarativos (YAML)
corpus/                  b_sintetico (versionado) y a_real (solo manifiesto)
tareas/, ataques/        tareas con verdad conocida y suite adversarial
arnes/, resultados/      ejecutor de corridas, métricas y corridas versionadas
app/                     interfaz Streamlit
tests/                   pruebas (pytest)
docs/                    plan, estado, decisiones, guía de pruebas e informe por partes
privado/                 fuera de git: material del curso, entregables y contexto (D55)
```

## 5. Convenciones

- **Idioma:** nombres del dominio, comentarios, documentación y commits en español (D18); identificadores
  técnicos de librerías, en su forma original.
- **Estilo:** Ruff (`line-length = 100`, comillas dobles); anotaciones de tipo en las firmas públicas.
- **Invariantes del dominio:**
  - Toda oferta lleva `Procedencia`, y la procedencia la escribe el código, nunca el modelo.
  - El contenido de terceros entra al modelo solo por las herramientas de extracción; el planificador ve
    instrucciones del usuario y datos ya extraídos (N4, separación de planos).
  - Cada llamada a un LLM registra tokens, costo y proveedor; ninguna tarea supera el tope de gasto.
  - Una propuesta recomienda una oferta o se abstiene con motivo explícito.
- **Pruebas:** sin red ni claves; patrón preparar · actuar · verificar.

## 6. Calidad y automatización

`make check` (lint, formato y pruebas) debe pasar antes de cada commit; los hooks de pre-commit lo refuerzan
(incluida la detección de llaves privadas) y la CI corre lo mismo en cada push. `make help` lista los comandos.

## 7. Git y repositorio

- Rama `main`; un commit por sesión de trabajo como mínimo, con [Conventional Commits](https://www.conventionalcommits.org/)
  (`feat:`, `fix:`, `docs:`, `test:`, `chore:`…) y descripción en imperativo.
- El repositorio es público: nunca se versionan `.env`, material del curso, documentos personales ni copias de
  sitios reales (D51). Se revisa `git status` antes de cada commit.

## 8. Flujo de trabajo

Cada sesión arranca leyendo `docs/ESTADO.md` y la sección del plan que corresponde, y cierra actualizando estado,
plan, decisiones y el borrador del informe, con su commit.

## 9. Historial de decisiones

El historial completo, con fecha y motivo, está en [`docs/DECISIONES.md`](docs/DECISIONES.md). Todo cambio
arquitectónico, tecnológico o de proceso se registra allí en el mismo commit que lo introduce.

## 10. Configuración local (no se versiona)

Claves en `.env` (plantilla en [`.env.example`](.env.example)): `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY` y el tope
`COSTO_MAXIMO_POR_TAREA_USD`.
