# Deployment Guide — bm-reports

> Laatst bijgewerkt: 2026-02-20

## Server Info

| Item | Waarde |
|------|--------|
| Provider | Hetzner (CX22) |
| IP | 46.224.215.142 |
| OS | Ubuntu 24.04.4 LTS |
| Specs | 2 vCPU, 4GB RAM, 75GB SSD |
| Docker | 29.2.1 + Compose v5.0.2 |

## Domeinen

| Domein | Service |
|--------|---------|
| `report.open-aec.com` | bm-reports (API + frontend) |
| `zaagplan.open-aec.com` | cutlist-optimizer |

DNS: A-records wijzen naar 46.224.215.142

## Directorystructuur

```
/opt/openaec/
├── docker-compose.yml          # Alle services
├── caddy/
│   ├── Caddyfile               # Reverse proxy + SSL config
│   └── logs/access.log         # Caddy access log (CrowdSec input)
├── crowdsec/
│   └── acquis.yaml             # Log bronnen config
├── bm-reports-api/             # Git clone van openaec-reports
│   ├── Dockerfile
│   ├── src/bm_reports/
│   └── ...
└── bm-reports-ui/
    └── dist/                   # Vite production build (static files)
        ├── index.html
        └── assets/
```

## Services

### Caddy (reverse proxy + auto-SSL)
- Poorten: 80, 443, 443/udp
- SSL: automatisch via Let's Encrypt
- `report.open-aec.com/api/*` → `bm-reports-api:8000`
- `report.open-aec.com/*` → static files uit `/srv/reports`
- `zaagplan.open-aec.com/api/*` → `cutlist-backend:8000`
- `zaagplan.open-aec.com/*` → `cutlist-frontend:80`

### bm-reports-api
- Image: gebuild vanuit `/opt/openaec/bm-reports-api/Dockerfile`
- Python 3.12-slim, uvicorn, 2 workers
- Port: 8000 (intern)
- Healthcheck: `GET /api/health`
- Env: `BM_TENANT_DIR=/app/tenants/default`
- Volume: `reports_uploads:/app/uploads`

### CrowdSec
- Monitort Caddy access log
- Collections: caddy, http-cve, base-http-scenarios
- TODO: bouncer installeren voor actieve IP blocking

## Beheer Commands

```bash
# Status
cd /opt/openaec && docker compose ps

# Logs
docker logs bm-reports-api --tail 50
docker logs caddy --tail 50

# Restart
docker compose restart bm-reports-api

# Update API (na git push)
cd /opt/openaec/bm-reports-api && git pull
cd /opt/openaec && docker compose build bm-reports-api
docker compose up -d bm-reports-api

# Update frontend
# Upload nieuwe dist/ bestanden naar /opt/openaec/bm-reports-ui/dist/
# Caddy serveert automatisch (geen restart nodig)

# CrowdSec
docker exec crowdsec cscli metrics
docker exec crowdsec cscli alerts list
docker exec crowdsec cscli decisions list
```

## GitHub Repository

- **URL:** https://github.com/OpenAEC-Foundation/openaec-reports
- **Branch:** main
- **Auth:** Personal Access Token (Settings → Developer settings → Tokens)

## Frontend Deploy Procedure

1. Lokaal:
   ```
   cd Report_generator_frontend
   # .env.production bevat: VITE_API_URL=https://report.open-aec.com
   npm run build
   ```
2. Upload `dist/` naar server (scp of rsync):
   ```
   scp -r dist/* root@46.224.215.142:/opt/openaec/bm-reports-ui/dist/
   ```
3. Geen restart nodig — Caddy serveert direct

## Bekende Issues

- PowerShell/npm wrapper geeft `$LASTEXITCODE` warnings (onschuldig)
- Git push vereist PAT via terminal (geen TTY in PowerShell wrapper)
- cutlist-frontend nginx verwacht upstream "backend" — opgelost via network alias
