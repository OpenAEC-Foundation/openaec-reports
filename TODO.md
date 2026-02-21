# TODO — bm-reports

> Prioriteit: 🔴 Hoog | 🟡 Middel | 🟢 Laag
> Laatst bijgewerkt: 2026-02-21

---

## 🔴 D1 — Monorepo Deploy op VPS

**Status:** Monorepo merge klaar, deploy pending

- [ ] `git push` naar GitHub
- [ ] Op server: `git pull` + `docker compose build --no-cache bm-reports-api`
- [ ] `docker compose up -d bm-reports-api`
- [ ] Verifiëren: https://report.open-aec.com/ laadt frontend (via StaticFiles)
- [ ] Verifiëren: https://report.open-aec.com/api/health werkt
- [ ] End-to-end test: template laden → rapport genereren → PDF download
- [ ] Caddyfile vereenvoudigen: enkele `reverse_proxy` naar API container
- [ ] Verwijder `bm-reports-ui/dist` volume mount uit docker-compose.yml

---

## 🔴 D3 — CI/CD Pipeline

- [ ] GitHub Actions workflow: build + push Docker image (multi-stage)
- [ ] Auto-deploy op VPS bij push naar main
- [ ] Frontend + backend in één pipeline

---

## 🟡 D4 — CrowdSec Bouncer

- [ ] Caddy bouncer installeren voor actieve IP blocking
- [ ] Testen met `cscli decisions list`

---

## 🟡 P1 — Stationery Extractie

**Prompt:** `PROMPT_P1_STATIONERY_EXTRACTIE.md`

- [ ] `build-brand` draaien tegen referentie-PDF
- [ ] Visueel verifiëren: tekst gestript, graphics intact
- [ ] `source:` paden + `text_zones:` invullen in `default.yaml`

---

## 🟢 P5 — Toekomstige Features

### Multi-bureau support
- [ ] Tweede brand toevoegen (bijv. BBL Engineering)
- [ ] Brand selector via API
- [ ] Stamkaart parser: PMS/CMYK kleurcodes

### Rapport types
- [ ] `reports/structural.py` — Constructief rapport
- [ ] `reports/daylight.py` — Daglichttoetreding
- [ ] `reports/building_code.py` — BBL-toetsing

### Revit integratie
- [ ] RevitAdapter: Revit model data → rapport JSON
- [ ] pyRevit commands: Generate rapport vanuit Revit UI

### SaaS / Deployment
- [ ] Frontend brand setup wizard (roept B5 tools aan)
- [ ] Multi-tenant brand management
- [ ] PDF caching op basis van JSON hash
- [ ] User authentication (API keys of OAuth)
- [ ] Rate limiting per tenant

---

## Afgerond ✅

| Item | Wanneer |
|------|---------|
| Fase A: Brand Analyzer (PDF → YAML pipeline) | Week 7 |
| B1: KadasterMap + PDOK WMS | Week 8 |
| B2: FastAPI API (6 endpoints) | Week 8 |
| B3: Scaffold + Landscape oriëntatie | Week 8 |
| Font/kleur fixes (6 bugs) | Week 8 |
| Stationery systeem (code) | Week 8 |
| Brand Builder pipeline (code) | Week 8 |
| Page templates met stationery-first | Week 8 |
| CLI: analyze-brand, build-brand, serve | Week 8 |
| Test suite: 397 tests, 70% coverage | Week 8 |
| P2: Cleanup + archivering | Week 8 |
| P3: Special pages → brand YAML aansluiting | Week 8 |
| P4: Coverage gaps dichten (70% → 75%) | Week 8 |
| B5: Huisstijl extractie tool (6 modules, 50 tests) | Week 8 |
| **VPS opgezet: Hetzner CX22, Caddy, CrowdSec** | **Week 8** |
| **Docker image gebuild + API live** | **Week 8** |
| **GitHub repo: OpenAEC-Foundation/openaec-reports** | **Week 8** |
| **Cutlist Optimizer gemigreerd naar Caddy stack** | **Week 8** |
| **SSL auto-provisioned (Let's Encrypt)** | **Week 8** |
| **Dockerfile + pyproject.toml fixes (pycairo, README, force-include)** | **Week 8** |
| **D2: Tenant Separation (TenantConfig, loaders, tests)** | **Week 8** |
| **Monorepo merge: frontend + backend in één repo** | **Week 8** |
| **Multi-stage Dockerfile (node build + python runtime)** | **Week 8** |
| **StaticFiles mount in FastAPI (SPA serving)** | **Week 8** |
| **Vite dev proxy voor lokale ontwikkeling** | **Week 8** |
| **JSON alignment fixes (6 fixes, 22 tests)** | **Week 8** |
| **P2: Opschonen — dead code, docs archiveren, CLAUDE.md** | **Week 8** |
