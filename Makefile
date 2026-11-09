# =============================================================================
# Comercio agéntico — automatización de tareas
# =============================================================================

SHELL := /bin/bash

.DEFAULT_GOAL := help
.PHONY: help install dev pre-commit-install pre-commit lint format format-check typecheck test check build clean ping corpus-b corpus-b-servir corpus-b-catalogo humo candidatos

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Sincroniza el entorno virtual e instala dependencias
	uv sync

dev: install pre-commit-install ## Prepara el entorno de desarrollo (sync + hooks)

pre-commit-install: ## Instala los hooks de pre-commit en el repositorio local
	uv run pre-commit install

pre-commit: ## Ejecuta todos los hooks de pre-commit sobre el repositorio
	uv run pre-commit run --all-files

lint: ## Ejecuta Ruff (lint)
	uv run ruff check .

format: ## Formatea el código con Ruff
	uv run ruff format .

format-check: ## Verifica el formato sin modificarlo
	uv run ruff format --check .

ping: ## Llama con herramientas a los seis modelos (gasta centavos; requiere .env)
	uv run python -m comercio_agentico.ping

corpus-b: ## Regenera proveedores, verdad y tareas del corpus B (US$0, sin red)
	uv run python -m comercio_agentico.corpus_b.generar
	uv run python -m comercio_agentico.corpus_b.tareas

corpus-b-servir: ## Sirve P2-P5 en :8800 y P1 (MCP) en :8801; Ctrl+C para detener (US$0)
	uv run python -m comercio_agentico.corpus_b.servir

corpus-b-catalogo: ## Regenera el catálogo con DeepSeek Flash (~US$0,03; requiere .env)
	uv run python -m comercio_agentico.corpus_b.catalogo

candidatos: ## Embeddings: candidatos del catálogo para nombres informales (US$0, sin LLM)
	uv run python -m comercio_agentico.emparejamiento

humo: ## Prueba de humo del agente: 5 tareas con DeepSeek Flash (~US$0,05; requiere corpus-b-servir)
	uv run python -m comercio_agentico.preguntar --tareas B001,B013,B025,B037,B054 --tope 0.10

test: ## Ejecuta las pruebas
	uv run pytest

check: lint format-check test ## Verificación completa (lint + formato + pruebas)

build: ## Construye el paquete (sdist + wheel)
	uv build

clean: ## Limpia cachés y artefactos
	rm -rf .pytest_cache .ruff_cache .mypy_cache dist build htmlcov .coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
