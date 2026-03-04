# TODO — openaec-reports

> Prioriteit: 🔴 Blocker | 🟡 Middel | 🟢 Nice-to-have
> Laatst bijgewerkt: 2026-03-04 (avond)

---

## 🔴 Bugs — Hoog

- [ ] **#14** — Colofon: `revision_history` en `disclaimer` worden niet gerenderd (silent failure)
  - `_build_field_map()` incompleet, template mist posities, schema-implementatie mismatch
  - Bestanden: `renderer_v2.py` (ColofonGenerator), `colofon.yaml`, `report.schema.json`
- [ ] **#6** — Colofon update niet
  - Colofon pagina refresht niet bij data-wijziging

---

## 🔴 Features — Hoog

- [ ] **#13** — MCP-server toevoegen
  - OpenAEC Reports als MCP server beschikbaar maken voor externe tools
- [ ] **#9** — Spreadsheet blok inclusief copy/paste naar LibreOffice Calc
  - Nieuw block type voor spreadsheet-achtige tabellen met clipboard support
- [ ] **#1** — ERPNext integratie
  - Projectinfo ophalen via API keys vanuit ERPNext

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
- [x] T5.8 — BrandExtractWizard (4-stap, paurs) in admin panel
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

## 🟡 GitHub Issues — Middel

- [ ] **#10** — Read/Write to IFC
  - IFC bestandsformaat lezen en schrijven (integratie)
- [ ] **#8** — Bij regenerate blijf op oorspronkelijke pagina
  - UX: na PDF regeneratie terug naar dezelfde pagina in de preview
- [x] **#7** — Adviseur ook aan account koppelen + Authentik SSO
  - User model uitgebreid met phone, job_title, registration_number, company, auth_provider, oidc_subject
  - OIDC token validatie (JWKS/RS256) + auto-provisioning
  - Frontend SSO login flow (PKCE, OidcCallback)
  - Colofon auto-fill vanuit user profiel
  - Docker Compose met Authentik
- [x] **#5** — Organisation / Project Browser
  - ProjectBrowser component (split-panel: projectlijst + rapportenlijst)
  - Server-side rapport opslag (SQLite metadata + JSON op disk)
  - "Projecten" tab in AppShell, server-save via Ctrl+S
  - 11 API endpoints: CRUD projecten + rapporten + verplaatsen
- [x] **#4** — Project → Report (mother-children relatie)
  - `projects` en `reports` tabellen met foreign key relatie
  - Rapport kan in project of standalone bestaan (nullable project_id)
  - Cascade delete: project verwijderen verwijdert ook rapporten
- [x] **#2** — Auteur koppelen aan user
  - Colofon adviseur velden auto-filled vanuit user profiel (display_name, email, phone, etc.)

---

## 🟢 GitHub Issues — Laag

- [ ] **#12** — RUST Library (R&D)
  - Onderzoek naar Rust-implementatie van de report engine
- [ ] **#11** — AI-instructies meegeven voor gebruik in andere tools
  - Documentatie/schema zodat externe AI-tools rapporten kunnen genereren
- [ ] **#3** — Brand visualiser maken
  - Visuele editor voor brand configuratie (kleuren, fonts, layout)

---

## 🟢 Frontend — Geavanceerde Features

- [ ] F1 — Block copy/paste (Ctrl+C/V)
- [ ] F2 — Section templates (standaard secties met pre-filled blocks)
- [x] F3 — Multi-rapport beheer (lijst, dupliceren, verwijderen) — via ProjectBrowser
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
- [ ] H4 — `Inter-Bold.ttf` etc. instructies in fonts.py updaten (verwijst naar oude pad)
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
| `core/fonts.py` | 13 | Inter TTF pad instructies updaten |
| `data/kadaster.py` | 60 | RD↔WGS84 conversie met pyproj/RDNAPTRANS |
| `data/revit_adapter.py` | 42, 64, 69, 89 | Volledige Revit integratie (4 methoden) |
| `reports/building_code.py` | 33 | Bouwbesluit toetsingssecties |
| `reports/daylight.py` | 27 | Daglichtsecties |
| `reports/structural.py` | 28 | Sectie-opbouw vanuit data |

---

## ✅ VOLTOOID

### Self-Registratie + Server-side Opslag + Projectstructuur (4 maart)
- [x] Open registratie: `POST /api/auth/register` met validatie, env var guard (`OPENAEC_REGISTRATION_ENABLED`)
- [x] RegisterPage frontend + authStore `register()` actie
- [x] Server-side rapport opslag: `storage/models.py` (SQLite + bestandssysteem)
- [x] 11 API endpoints: projecten CRUD, rapporten CRUD, verplaatsen, filteren
- [x] ProjectBrowser UI (split-panel), projectStore (Zustand), server-save (Ctrl+S)
- [x] Eigendom-isolatie: users zien alleen eigen projecten/rapporten
- [x] 37 nieuwe tests (registratie + opslag), 1059 bestaande tests ongewijzigd

### API Key Management UI (2 maart)
- [x] Frontend: ApiKeyManagement component + admin tab
- [x] API types + store actions (list, create, revoke, delete)
- [x] Eenmalige plaintext key display + kopieer-knop
- [x] Code review: shared.tsx geextraheerd, usersError gefixt, staleness guard, clipboard error handling

### OpenAEC TemplateEngine Migratie (2 maart)
- [x] OpenAEC templates werkend en gevalideerd

### OpenAEC Rebranding — Volledig (2 maart)
- [x] Package rename, env vars, CLI, frontend, Docker, domain, README, LICENSE, API key prefix

### Deploy + Visuele Validatie (2 maart)
- [x] Docker rebuild op Hetzner VPS
- [x] Customer BIC rapporten visueel gevalideerd — pixel-perfect

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
- [x] BrandExtractWizard (paurs, 4-stap) operationeel

### Tenant Resolution Fix (1 maart)
- [x] `_resolve_tenant_and_template()` helper
- [x] `_resolve_tenants_dir()` robuust met env vars
- [x] 888 tests passed

### TemplateEngine V3 (28 feb)
- [x] 102+ unit tests, 3 E2E tests
- [x] 6-pagina PDF mixed orientation + stationery
- [x] Customer BIC factuur template compleet
