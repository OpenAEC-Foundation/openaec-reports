# TODO — bm-reports

> Prioriteit: 🔴 Hoog | 🟡 Middel | 🟢 Laag
> Laatst bijgewerkt: 2026-02-20

---

## 🔴 D1 — Frontend Deploy op VPS

**Status:** Build klaar, deploy pending

- [ ] `npm run build` met `VITE_API_URL=https://report.3bm.co.nl`
- [ ] Dist bestanden uploaden naar server: `/opt/3bm/bm-reports-ui/dist/`
- [ ] Verifiëren: https://report.3bm.co.nl laadt frontend
- [ ] End-to-end test: template laden → rapport genereren → PDF download

---

## 🔴 D2 — Tenant Separation

**Prompt:** `PROMPT_TENANT_SEPARATION.md`

Architectureel kritiek voor multi-tenant SaaS. Huidige situatie: alle client-specifieke assets (templates, brands, fonts, stationery) zitten gebundeld in het Python package. Andere bedrijven zouden 3BM's templates zien.

- [ ] Stap 1: TenantConfig class + BM_TENANT_DIR environment variable
- [ ] Stap 2: Loader refactors (brand, template, stationery, fonts)
- [ ] Stap 3: API endpoints updaten (tenant-aware)
- [ ] Stap 4: Font registratie per tenant
- [ ] Stap 5: Assets migreren naar `tenants/3bm_cooperatie/`
- [ ] Stap 6: Fallback chain: tenant → package defaults
- [ ] Stap 7: Tests aanpassen
- [ ] Stap 8: Documentatie

---

## 🔴 D3 — CI/CD Pipeline

- [ ] GitHub Actions workflow: build + push Docker image
- [ ] Auto-deploy op VPS bij push naar main
- [ ] Frontend build als apart CI step

---

## 🟡 D4 — CrowdSec Bouncer

- [ ] Caddy bouncer installeren voor actieve IP blocking
- [ ] Testen met `cscli decisions list`

---

## 🟡 P1 — Stationery Extractie

**Prompt:** `PROMPT_P1_STATIONERY_EXTRACTIE.md`

- [ ] `build-brand` draaien tegen referentie-PDF
- [ ] Visueel verifiëren: tekst gestript, graphics intact
- [ ] `source:` paden + `text_zones:` invullen in `3bm_cooperatie.yaml`

---

## 🟡 P2 — Opschonen

**Prompt:** `PROMPT_P2_CLEANUP.md`

- [ ] ~50 `pytest-cache-files-*` mappen verwijderen
- [ ] Afgeronde PROMPT bestanden archiveren naar `_archive/`
- [ ] `CLAUDE.md` actualiseren (beide repos)
- [ ] Dead code verwijderen: `template_renderer.py`, `template_schema.py`

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
