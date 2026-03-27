# ---- Stage 1: Frontend build ----
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python runtime ----
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libffi-dev libcairo2 libcairo2-dev pkg-config \
    libpango-1.0-0 libpangocairo-1.0-0 curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY schemas/ ./schemas/
COPY tenants/ ./tenants/
COPY docs/ ./docs/
RUN pip install --no-cache-dir .

# Frontend dist van stage 1
COPY --from=frontend-build /app/frontend/dist /app/static

# Non-root user voor security
RUN adduser --disabled-password --gecos '' appuser
RUN mkdir -p /app/uploads /app/data && chown -R appuser:appuser /app

# Multi-tenant: alle tenant directories beschikbaar voor brand resolution
ENV OPENAEC_TENANTS_ROOT=/app/tenants
ENV OPENAEC_TENANT_DIR=/app/tenants/default

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "openaec_reports.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
