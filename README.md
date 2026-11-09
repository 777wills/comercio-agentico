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
- [Stack](#stack)
- [Primeros pasos](#primeros-pasos)
- [Estructura](#estructura)
- [Documentación](#documentación)
- [Licencia](#licencia)

## Qué hace

Recibe una necesidad de compra en lenguaje natural, consulta proveedores con distintos niveles de madurez digital
(servidor MCP, web con schema.org, web plana, PDF y mensajería), extrae ofertas a un esquema canónico con
procedencia obligatoria y entrega una propuesta comparativa trazable, o se abstiene. No ejecuta pagos.

## Stack

Python 3.13 · uv · LangGraph / LangChain · Anthropic y OpenRouter · crawl4ai · Pydantic · FastMCP · Streamlit ·
Ruff · pytest · GitHub Actions.

## Primeros pasos

```bash
make dev                      # uv sync + hooks de pre-commit
cp .env.example .env          # y completar las claves
make check                    # lint + formato + pruebas (sin red)
make ping                     # una llamada con herramientas a cada uno de los seis modelos
```

## Estructura

```text
src/comercio_agentico/   esquema canónico, fábrica de modelos y agente
perfiles/                perfiles de categoría declarativos (YAML)
tests/                   pruebas
docs/                    plan, decisiones, estado e informe
```

## Documentación

- [`CONSTITUTION.md`](CONSTITUTION.md): propósito, alcance, stack, convenciones y flujo.
- [`docs/DECISIONES.md`](docs/DECISIONES.md): decisiones y su justificación.
- [`docs/PLAN.md`](docs/PLAN.md): plan de ejecución por sesiones.

## Licencia

[MIT](LICENSE) © 2026 William Suaza Losada.
