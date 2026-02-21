# ---- Stage 1: Frontend build ----
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
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
RUN pip install --no-cache-dir hatchling && \
    pip install --no-cache-dir reportlab>=4.0 svglib>=0.9 PyYAML>=6.0 \
    Pillow>=10.0 requests>=2.31 fastapi>=0.115.0 "uvicorn[standard]>=0.30.0" \
    python-multipart>=0.0.9 jsonschema>=4.20.0 pymupdf>=1.24 pydantic>=2.0

COPY src/ ./src/
COPY schemas/ ./schemas/
RUN pip install --no-cache-dir .

# Frontend dist van stage 1
COPY --from=frontend-build /app/frontend/dist /app/static

RUN mkdir -p /app/uploads

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "bm_reports.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
