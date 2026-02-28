# TODO — bm-reports

> Prioriteit: 🔴 Hoog | 🟡 Middel | 🟢 Laag
> Laatst bijgewerkt: 2026-02-28 21:30

---

## ✅ T-API — API Endpoint voor TemplateEngine — VOLTOOID

- [x] T-API.1 — Endpoint `/api/generate/template` in `api.py`
- [x] T-API.2 — `data_transform.py` als production module
- [x] T-API.3 — Frontend smart endpoint routing
- [x] T-API.4 — Integratietests (`test_api_template.py`)

## ✅ T1 — Template Engine Fase 1 — VOLTOOID

- [x] T1.1–T1.8 — Compleet (102+ unit tests, 3 E2E tests, 6-pagina PDF)

## ✅ T2 — Stationery + Coördinaten — VOLTOOID

- [x] T2.1–T2.6 — Compleet (referentie-gebaseerde coördinaten)

## ✅ CLEANUP — Deprecated Code Verwijderd

- [x] `modules/customer/` verwijderd (vervangen door TemplateEngine)
- [x] `modules/yaml_module.py` verwijderd (vervangen door TemplateEngine)
- [x] `tenants/customer/modules/` verwijderd (vervangen door page_types/)
- [x] `assets/templates/customer_*.yaml` verwijderd
- [x] Bijbehorende tests opgeruimd
- [x] Prompt bestanden gearchiveerd naar `_archive/prompts/`

---

## 🔴 D-DEPLOY — Deploy Nieuwe Versie

### D-DEPLOY.1 — Docker build testen
- [ ] `docker build -t bm-reports:latest .` — moet slagen
- [ ] Controleer dat `tenants/` correct meekomt in image
- [ ] Test: `docker run --rm -p 8000:8000 bm-reports:latest` + health check

### D-DEPLOY.2 — VPS deployment
- [ ] Push naar GitHub (main branch)
- [ ] SSH naar VPS, pull + rebuild
- [ ] Verifieer `/api/generate/template` endpoint live
- [ ] Test met Customer test JSON via curl

### D-DEPLOY.3 — Frontend rebuild
- [ ] `cd frontend && npm run build`
- [ ] Kopieer `dist/` naar `static/` (of via Docker multi-stage)
- [ ] Verifieer frontend op https://report.open-aec.com

---

## 🟡 V-VALIDATE — Visuele Validatie Customer

- [ ] Genereer PDF via API met `test_336_bic_factuur.json`
- [ ] Open in PDF viewer naast referentie 336.01
- [ ] Controleer per pagina:
  - [ ] Pagina 1: Cover (portrait) — logo, kleur, tekst positie
  - [ ] Pagina 2: Location detail (portrait) — adressen, project info
  - [ ] Pagina 3: BIC tabel (landscape) — kolommen, rijen, totalen
  - [ ] Pagina 4: Detail items (landscape) — tabelopmaak
  - [ ] Pagina 5: Objecten (landscape) — Type kolommen
  - [ ] Pagina 6: Cost summary (portrait) — bedragen, layout

---

## 🟡 T3 — OpenAEC TemplateEngine Migratie

### T3.1 — OpenAEC page_type YAML's
- [ ] `tenants/default/page_types/voorblad.yaml`
- [ ] `tenants/default/page_types/colofon.yaml`
- [ ] `tenants/default/page_types/inhoud.yaml`
- [ ] `tenants/default/page_types/standaard.yaml`
- [ ] `tenants/default/page_types/bijlage_scheidblad.yaml`
- [ ] `tenants/default/page_types/achterblad.yaml`

### T3.2 — OpenAEC template YAML's (TemplateEngine formaat)
- [ ] `tenants/default/templates/rapport_v3.yaml`
- [ ] `tenants/default/templates/berekening_v3.yaml`

### T3.3 — Flow mode engine
- [ ] `_build_flow_content()` integreren met block_registry
- [ ] Regressietest: V2 output vs TemplateEngine output
- [ ] Migratie-pad: `/api/generate/v2` → `/api/generate/template` voor OpenAEC

---

## 🟡 D1 — Server & Infrastructure

- [x] Monorepo deployed op VPS
- [x] SSH key-based auth (thuis + kantoor)
- [x] Cockpit admin panel
- [ ] Caddyfile vereenvoudigen (reverse proxy cleanup)
- [ ] fail2ban installeren
- [ ] Portainer installeren

---

## 🟢 P5 — Toekomstige Features

- [ ] Customer rapport simpel (flow mode, niet alleen BIC)
- [ ] Tweede brand onboarding (BBL Engineering)
- [ ] RevitAdapter: Revit model data → rapport JSON
- [ ] PDF caching op basis van JSON hash
- [ ] Rate limiting per tenant
- [ ] Rich text editing in frontend

---

## 🟢 Housekeeping

- [x] pytest cache cleanup
- [x] Oude PROMPT_*.md bestanden gearchiveerd
- [ ] `lessons_learned.md` aanmaken
- [ ] CLAUDE.md updaten met TemplateEngine documentatie
- [ ] README.md updaten met nieuwe architectuur
