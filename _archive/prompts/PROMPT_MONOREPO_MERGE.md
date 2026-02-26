# PROMPT: Monorepo Merge — Frontend + Backend

> Uitvoeren in de backend repo root met Claude Code
> Doel: Frontend samenvoegen in openaec-reports monorepo met multi-stage Docker build
> Auth/tenant separation komt later — dit is puur de code-merge + unified deploy

## Context

- Backend repo: huidige directory (openaec-reports op GitHub)
- Frontend staat in: `../Report_generator_frontend/`
- Server: report.3bm.co.nl draait al de backend API via Docker
- GitHub: https://github.com/OpenAEC-Foundation/openaec-reports

## Instructies

### Stap 1: Kopieer frontend naar `frontend/` map

Kopieer ALLES uit `../Report_generator_frontend/` naar `frontend/` BEHALVE:
- `node_modules/`
- `dist/`
- `.git/`

De volgende bestanden moeten er minimaal zijn:
- `frontend/package.json`
- `frontend/package-lock.json` (als bestaat)
- `frontend/vite.config.ts`
- `frontend/tsconfig.json` + `tsconfig.app.json` + `tsconfig.node.json` (als bestaan)
- `frontend/tailwind.config.js` of `.ts`
- `frontend/postcss.config.js` of `.mjs`
- `frontend/index.html`
- `frontend/src/` (hele map)
- `frontend/public/` (als bestaat)

### Stap 2: Maak `frontend/.env.production`

```
VITE_API_URL=
```

Leeg = relative URLs. Werkt zowel lokaal via proxy als in productie op hetzelfde domein.

### Stap 3: Update `frontend/vite.config.ts`

Voeg `server.proxy` toe zodat `npm run dev` API calls doorstuurt naar de lokale backend:

```ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
},
```

### Stap 4: Vervang de `Dockerfile` met multi-stage build

```dockerfile
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
```

### Stap 5: Voeg static file serving toe aan `src/bm_reports/api.py`

Voeg ONDERAAN het bestand toe, NA alle API route definities:

```python
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# Static frontend (moet ONDERAAN staan, na alle API routes)
_static_dir = Path(__file__).parent.parent.parent / "static"
if _static_dir.exists():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")
```

De `html=True` parameter zorgt voor SPA fallback: onbekende routes serveren `index.html`.

### Stap 6: Update `.dockerignore`

Voeg toe:
```
frontend/node_modules
frontend/dist
frontend/.env.local
```

### Stap 7: Update `.gitignore`

Voeg toe:
```
frontend/node_modules/
frontend/dist/
```

### Stap 8: Commit

```bash
git add -A
git commit -m "Monorepo: merge frontend into openaec-reports

- Multi-stage Dockerfile (node build + python runtime)
- Frontend served as static files via FastAPI
- Vite dev proxy for local development
- One deploy pipeline for everything"
```

## Verificatie

Na uitvoering, controleer:
- [ ] `frontend/package.json` bestaat
- [ ] `frontend/src/` bevat React componenten
- [ ] `Dockerfile` heeft twee FROM stages
- [ ] `src/bm_reports/api.py` heeft StaticFiles mount onderaan
- [ ] `.gitignore` bevat `frontend/node_modules/`
- [ ] Geen `frontend/node_modules/` of `frontend/dist/` in git

## Na merge (handmatig)

```bash
git push

# Op server:
cd /opt/3bm/bm-reports-api && git pull
cd /opt/3bm && docker compose build --no-cache bm-reports-api
docker compose up -d bm-reports-api

# Test:
curl https://report.3bm.co.nl/api/health
curl -s https://report.3bm.co.nl/ | head -5   # moet index.html tonen
```

## Caddyfile vereenvoudigen (op server)

Na succesvolle deploy kan de Caddyfile vereenvoudigd worden. Nu serveert Caddy static files apart — straks gaat alles via de API container:

```
report.3bm.co.nl {
    reverse_proxy bm-reports-api:8000

    header {
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
        Referrer-Policy strict-origin-when-cross-origin
    }

    log {
        output file /var/log/caddy/access.log
        format json
    }
}
```

En verwijder de `bm-reports-ui/dist` volume mount uit docker-compose.yml.

## Wat NIET verandert

- Backend Python code (alleen StaticFiles mount erbij)
- Frontend React code (alleen .env.production en vite proxy)
- API contract / endpoints
- Tests (beide kanten)
- pyproject.toml
