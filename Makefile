# =============================================================================
# Comercio agéntico — automatización de tareas
# =============================================================================

SHELL := /bin/bash

.DEFAULT_GOAL := help
.PHONY: help install dev pre-commit-install pre-commit lint format format-check typecheck test check build clean ping corpus-b corpus-b-servir corpus-b-catalogo corpus-a-recolectar corpus-a corpus-a-servir corpus-a-correr humo candidatos app arnes-simulado calibracion e3 e3-frontera e2-ataques e2-ataques-simulado e2-utilidad e2 jev e1 e1-lecturas metricas

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

corpus-a-recolectar: ## Lee de nuevo las fichas reales (red; robot identificable; ~6 min; US$0)
	uv run python -m comercio_agentico.corpus_a.recolectar

corpus-a: ## Reconstruye catálogo, verdad, tiendas y tareas del corpus A desde los hechos (US$0)
	uv run python -m comercio_agentico.corpus_a.construir
	uv run python -m comercio_agentico.corpus_a.tareas

corpus-a-servir: ## Sirve las tiendas reconstruidas A1-A3 en :8802; Ctrl+C para detener (US$0)
	uv run python -m comercio_agentico.corpus_a.servir

corpus-a-correr: ## Corrida del agente sobre el corpus A: 20 tareas con Flash (~US$0,3; requiere corpus-a-servir)
	uv run python -m comercio_agentico.arnes.correr --config configs/corpus_a_flash.yaml --repeticiones 1 --metricas

humo: ## Prueba de humo del agente: 5 tareas con DeepSeek Flash (~US$0,05; requiere corpus-b-servir)
	uv run python -m comercio_agentico.preguntar --tareas B001,B013,B025,B037,B054 --tope 0.10

app: ## Interfaz Streamlit (modo simulado US$0; consulta libre ~US$0,02 y requiere corpus-b-servir)
	uv run streamlit run src/comercio_agentico/app.py

arnes-simulado: ## Arnés completo con el agente simulado: 60 tareas × 3 repeticiones + métricas (US$0, sin red)
	rm -f resultados/corridas/*_calibracion_flash_simulado.jsonl
	uv run python -m comercio_agentico.arnes.correr --config configs/calibracion_flash.yaml --simulado --repeticiones 3 --metricas

calibracion: ## Corrida de calibración: 60 tareas con DeepSeek Flash + métricas (~US$1; requiere corpus-b-servir)
	uv run python -m comercio_agentico.arnes.correr --config configs/calibracion_flash.yaml --repeticiones 1 --metricas

e3: ## E3, un modelo en el subconjunto 30 × 3: make e3 MODELO=flash|haiku|deepseek-pro|kimi|sonnet (Flash ~US$1,5; requiere corpus-b-servir)
	uv run python -m comercio_agentico.arnes.correr --config configs/e3_$(MODELO).yaml --tareas tareas/subconjunto_e3.jsonl --repeticiones 3 --metricas

e3-frontera: ## E3: tabla, regla de parada D77 y frontera costo-desempeño con las corridas hechas (US$0)
	uv run python -m comercio_agentico.arnes.e3

e2-ataques: ## E2: 20 cargas × C0–C3 × 3 repeticiones con Flash (~US$3,7; requiere corpus-b-servir)
	uv run python -m comercio_agentico.ataques.correr --repeticiones 3 --tope-total 3.8 --concurrencia 4

e2-ataques-simulado: ## E2: la matriz completa con el agente simulado (US$0, sin red)
	uv run python -m comercio_agentico.ataques.correr --simulado --salida /tmp/e2_simulado.jsonl

e2-utilidad: ## E2: utilidad benigna, subconjunto E3 × C0–C3 × 1 (~US$1,8; requiere corpus-b-servir)
	for c in c0 c1 c2 c3; do uv run python -m comercio_agentico.arnes.correr --config configs/e2_$$c.yaml --tareas tareas/subconjunto_e3.jsonl --repeticiones 1 --metricas; done

e2: ## E2: curva seguridad-utilidad, Pareto, codo y control limpio con las corridas hechas (US$0)
	uv run python -m comercio_agentico.arnes.e2

jev: ## Compara el clasificador de C2 con Jev (TypeSafe) en 68 fragmentos (< US$0,01; requiere TYPESAFE_API_KEY)
	uv run python -m comercio_agentico.ataques.comparar_jev

e1: ## E1: N3 por reproducción pareada con las lecturas guardadas (US$0; requiere corpus-b-servir y corpus-a-servir)
	uv run python -m comercio_agentico.arnes.e1 --solo-analisis

e1-lecturas: ## E1: segunda lectura de los fragmentos que falten con Haiku (~US$0,02; requiere corpus B y A servidos)
	uv run python -m comercio_agentico.arnes.e1

metricas: ## Recalcula métricas de una corrida: make metricas CORRIDA=resultados/corridas/<archivo>.jsonl (US$0)
	uv run python -m comercio_agentico.arnes.metricas $(CORRIDA)

test: ## Ejecuta las pruebas
	uv run pytest

check: lint format-check test ## Verificación completa (lint + formato + pruebas)

build: ## Construye el paquete (sdist + wheel)
	uv build

clean: ## Limpia cachés y artefactos
	rm -rf .pytest_cache .ruff_cache .mypy_cache dist build htmlcov .coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
