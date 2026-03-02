# TODO — openaec-reports

> Prioriteit: 🔴 Blocker | 🟡 Middel | 🟢 Nice-to-have
> Laatst bijgewerkt: 2026-03-02

---

## 🟡 T5 — YAML Editor in Admin Panel

Self-service YAML beheer per tenant.

**Fase 1 — Upload & beheer (quick win):**
- [ ] T5.1 — API: `/api/admin/tenants/{tenant}/page_types/` CRUD
- [ ] T5.2 — Frontend: YAML file browser per tenant
- [ ] T5.3 — Upload/download YAML's + brand.yaml
- [ ] T5.4 — Preview: upload → render test-PDF → bekijk resultaat

**Fase 2 — Visuele editor:**
- [ ] T5.5 — YAML als formulier: text_zones als bewerkbare rijen
- [ ] T5.6 — Live preview bij wijziging
- [ ] T5.7 — Kleurenpicker uit brand.yaml

**Fase 3 — Brand onboarding wizard (deels klaar):**
- [x] T5.8 — BrandExtractWizard (4-stap, paars) in admin panel
- [ ] T5.9 — Upload referentie PDF → coordinaten-extractie naar YAML
- [ ] T5.10 — Stationery PDF generator vanuit guidelines

---

## 🟡 T6 — Report Type Stubs Implementeren

Stub-modules met alleen `# TODO` comments. Moeten gevuld worden:

- [ ] T6.1 — `reports/structural.py` — Constructief rapport sectie-opbouw
- [ ] T6.2 — `reports/daylight.py` — Daglichtsecties
- [ ] T6.3 — `reports/building_code.py` — Bouwbesluit toetsingssecties

---

## 🟡 T7 — Revit Adapter

`data/revit_adapter.py` is een stub. Alle methoden zijn `# TODO`.

- [ ] T7.1 — `get_project_info()` — ProjectInfo uitlezing via pyRevit
- [ ] T7.2 — `get_elements()` — FilteredElementCollector
- [ ] T7.3 — `get_rooms()` — Room ophaling
- [ ] T7.4 — `build_report_data()` — Element data mapping naar report JSON
- [ ] T7.5 — WebSocket bridge voor live Revit → frontend push

---

## 🟡 T8 — Kadaster/PDOK Verbetering

- [ ] T8.1 — `data/kadaster.py` RD ↔ WGS84 conversie verbeteren (pyproj of RDNAPTRANS i.p.v. huidige benadering)

---

## 🟢 Frontend — Geavanceerde Features

- [ ] F1 — Block copy/paste (Ctrl+C/V)
- [ ] F2 — Section templates (standaard secties met pre-filled blocks)
- [ ] F3 — Multi-rapport beheer (lijst, dupliceren, verwijderen)
- [ ] F4 — Visuele template editor (drag & drop sectie volgorde)
- [ ] F5 — Revit bridge: WebSocket listener + auto-fill berekening blocks

---

## 🟢 Admin Panel — Verbeteringen

- [ ] A1 — Shared sub-components verder consolideren (TenantManagement, TemplateManagement, BrandManagement gebruiken nog eigen spinners)
- [ ] A2 — API key expiry datumpicker in create form
- [ ] A3 — Bulk operaties (meerdere keys tegelijk intrekken)

---

## 🟢 Housekeeping

- [ ] H1 — `_temp_analyze.py` verwijderen uit project root
- [ ] H2 — CLAUDE.md updaten (nog verwijzingen naar `src/bm_reports` in architectuur sectie)
- [ ] H3 — `lessons_learned.md` aanmaken
- [ ] H4 — `Gotham-Bold.ttf` etc. instructies in fonts.py updaten (verwijst naar oude pad)
- [ ] H5 — STATUS.md en frontend/STATUS.md actualiseren

---

## 🟢 Infrastructure

- [ ] I1 — Caddyfile vereenvoudigen
- [ ] I2 — fail2ban installeren
- [ ] I3 — Portainer installeren
- [ ] I4 — CI/CD pipeline (GitHub Actions: lint, test, build, deploy)

---

## 🟢 Code Quality

- [ ] Q1 — `usersError` was dead state — nu gefixt, maar review alle store slices voor vergelijkbare patronen
- [ ] Q2 — Stringly-typed user roles → `UserRole` union type
- [ ] Q3 — `formatDate` verplaatsen naar `frontend/src/utils/` als gedeelde utility

---

## Inline TODO's in Code

| Bestand | Regel | TODO |
|---------|-------|------|
| `core/fonts.py` | 13 | Gotham TTF pad instructies updaten |
| `data/kadaster.py` | 60 | RD↔WGS84 conversie met pyproj/RDNAPTRANS |
| `data/revit_adapter.py` | 42, 64, 69, 89 | Volledige Revit integratie (4 methoden) |
| `reports/building_code.py` | 33 | Bouwbesluit toetsingssecties |
| `reports/daylight.py` | 27 | Daglichtsecties |
| `reports/structural.py` | 28 | Sectie-opbouw vanuit data |

---

## ✅ VOLTOOID

### API Key Management UI (2 maart)
- [x] Frontend: ApiKeyManagement component + admin tab
- [x] API types + store actions (list, create, revoke, delete)
- [x] Eenmalige plaintext key display + kopieer-knop
- [x] Code review: shared.tsx geextraheerd, usersError gefixt, staleness guard, clipboard error handling

### 3BM TemplateEngine Migratie (2 maart)
- [x] 3BM templates werkend en gevalideerd

### OpenAEC Rebranding — Volledig (2 maart)
- [x] Package rename, env vars, CLI, frontend, Docker, domain, README, LICENSE, API key prefix

### Deploy + Visuele Validatie (2 maart)
- [x] Docker rebuild op Hetzner VPS
- [x] Symitech BIC rapporten visueel gevalideerd — pixel-perfect

### OpenAEC Rebranding — Package Rename (2 maart)
- [x] `git mv src/bm_reports src/openaec_reports`
- [x] 218 bestanden: imports, env vars, CLI, Dockerfile, docs
- [x] 1035 tests passed

### Pixel Precision Fixes (1 maart)
- [x] Arial per-tenant font registratie
- [x] Page numbering "Pagina X van Y"
- [x] Font ascent Y-offset correctie (<0.7pt)
- [x] ImageZone support
- [x] Achterblad text zones
- [x] BIC tabel fontsize 10pt

### Admin Panel Cleanup (1 maart)
- [x] Replace button per asset
- [x] BrandWizard (blauw, 3-stap) verwijderd
- [x] BrandExtractWizard (paars, 4-stap) operationeel

### Tenant Resolution Fix (1 maart)
- [x] `_resolve_tenant_and_template()` helper
- [x] `_resolve_tenants_dir()` robuust met env vars
- [x] 888 tests passed


### TemplateEngine V3 (28 feb)
- [x] 102+ unit tests, 3 E2E tests
- [x] 6-pagina PDF mixed orientation + stationery
- [x] Symitech BIC factuur template compleet
