# CotIA en un solo contenedor (D81, D116): frontend SvelteKit compilado + API FastAPI + agente.
#   docker build -t cotia .
#   docker run --rm -p 8000:8000 -e COTIA_BD_URL=postgresql+psycopg://... cotia

# --- Frontend: SvelteKit 3 exige Node >= 22.17 ---------------------------------------------------
FROM node:22-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# --- Dependencias de Python con uv (proyecto editable: el código ubica el corpus desde /app) ------
FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_NO_DEV=1 UV_PYTHON_DOWNLOADS=0
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project
COPY . .
RUN uv sync --locked

# --- Imagen final ---------------------------------------------------------------------------------
FROM python:3.13-slim-trixie
ENV PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/opt/hf \
    HF_HUB_DISABLE_TELEMETRY=1 \
    PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright \
    CRAWL4AI_NO_CLOUD_NOTICE=1 \
    PORT=8000
WORKDIR /app
COPY --from=builder /app /app
COPY --from=web /web/build /app/web/build

# Chromium para crawl4ai, modelos locales (embeddings y los dos clasificadores de C2) y corpus
# regenerado desde lo versionado: tiendas A1-A3 desde los hechos y variantes atacadas de B (D95).
RUN python -m playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/* \
    && python -c "from sentence_transformers import SentenceTransformer as S; \
    from transformers import AutoModelForSequenceClassification as M, AutoTokenizer as T; \
    from comercio_agentico.agente.defensa import CLASIFICADORES; \
    from comercio_agentico.emparejamiento import MODELO_EMBEDDINGS; \
    S(MODELO_EMBEDDINGS); [(T.from_pretrained(c), M.from_pretrained(c)) for c in CLASIFICADORES]" \
    && python -m comercio_agentico.corpus_a.construir \
    && python -m comercio_agentico.ataques.plantar \
    && useradd --create-home --uid 1000 cotia \
    && chown -R cotia /app/corpus /app/resultados

USER cotia
ENV HF_HUB_OFFLINE=1
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn comercio_agentico.api.app:crear_app --factory --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
