# STATUS — openaec-reports

> Laatst bijgewerkt: 2026-03-24 (sessie: BIC rapport field groups + layout fine-tuning)

---

## Sessie 24 maart — BIC Rapport: Field Groups, Layout, PDOK Kaarten

### Architectuur: Page-type-driven field groups
- **Backend:** `_extract_field_groups()` scant page_type YAML's, extraheert data_bind velden, groepeert per prefix, bepaalt input_type heuristisch
- **Frontend:** `FieldGroupForm` component rendert formuliervelden + tabeleditors. Sidebar toont "Formulier" sectie met 25 groepen
- **Conversie:** `toEditorReport()` extraheert flat_data uit onbekende top-level keys. `toReportDefinition()` schrijft flat_data + field_groups terug
- **Auto-fetch:** Als field_groups ontbreken bij JSON import, worden ze automatisch opgehaald van scaffold API

### BIC Template: 17 pagina's compleet
- 5 nieuwe page_types: tekening_overzicht, tekening_detail, tekening_kadaster, vvv_verklaring, schade_fotos
- Template matcht exact de originele 17-pagina Customer structuur
- Formeel JSON schema: `schemas/bic_rapport.schema.json`
- Voorbeeld JSON met realistische sample data (114/125 velden gevuld)

### Text wrapping + layout fixes
- `TextZone.max_width_mm` + `_wrap_text()` in template engine
- 87 text_zones voorzien van max_width_mm
- Rechterkolom 20mm naar links (132→112mm) op pagina 3-6
- Tabel origin_y gecorrigeerd op pagina 10-13
- Tabel body_color: secondary (oranje) op alle tabelpagina's
- Paginanummers consistent uitgelijnd op alle pagina's
- TOC: aparte rechts-uitgelijnde paginanummers

### PDOK kaarten
- `/api/pdok/map` endpoint: luchtfoto, kadaster, BAG via lat/lon
- `/api/pdok/services` endpoint: beschikbare services
- Template engine: image zones accepteren dict met lat/lon → PDOK kaart automatisch ophalen
- Combinatie-modus: coördinaten + image override

### Openstaand
- [ ] Pagina 4-5: tekst overlap bij lange content (spacing fine-tuning)
- [ ] Frontend: field groups tonen in UI (browser cache + auto-fetch fix gedeployed, nog testen)
- [ ] PDOK luchtfoto service was tijdelijk down — 2025_orthoHR layer geconfigureerd
- [ ] Deploy naar server (SSH connection issues)

---

## Sessie 24 maart (2) — Migratie-instructies verbeterd

`migratie-instructies.md` in het `OpenAEC_stijlbook` repo herschreven op basis van lessons learned uit de openaec-reports frontend (de referentie-implementatie).

### Nieuwe/verbeterde secties:
- **Referentie-implementatie** — directe links naar werkende bestanden in openaec-reports
- **CSS architectuur: twee lagen** — `--brand-*` (vast) vs `--theme-*` (per thema)
- **Boot sequence** — exacte volgorde `injectBrandStyles() → applyTheme() → render`
- **Chrome directory structuur** — complete bestandsboom met colocated CSS patroon
- **`brand.ts` + `injectBrandStyles.ts`** — volledig uitgewerkt met hexToRgb uitleg
- **Tailwind bridge** — concrete `tailwind.config.js` met `brand.*` en `chrome.*`
- **`useKeyboardShortcuts` hook** — centraal keyboard shortcut patroon
- **Zustand multi-store** — template met undo/redo patroon
- **i18n setup** — complete `config.ts` met namespace imports
- **Veelgemaakte fouten** — uitgebreid van 14 naar 28 items, gegroepeerd per categorie
- **Validatie-checklist** — uitgebreid van ~30 naar ~50 items

### Bestand gewijzigd:
- `C:\Users\Joche\Documents\GitHub\OpenAEC_stijlbook\migratie-instructies.md`

---

## Sessie 24 maart (1) — BIC Lijnen Fix

Blauwe lijnen op pagina 5 (bic_rapport_details) en pagina 6 (herstelwerkzaamheden) 2.55mm naar beneden verplaatst. Alle `line_zones` y_mm waarden aangepast. Gedeployd naar productie.

---

## Sessie 23 maart — Security Fixes + OIDC Tenant Fix

### 5 kritieke security items gefixt (SEC-K1 t/m K5)

| ID | Fix | Bestand(en) | Tests |
|----|-----|-------------|-------|
| SEC-K1 | `_resolve_path()` respecteert `tenant_slug` | `template_loader.py`, `brand.py` | 5 |
| SEC-K2 | `_resolve_brand_with_tenant_check()` helper | `api.py` | 2 |
| SEC-K3 | Upload allowlist + 10 MB size limit | `api.py` | 6 |
| SEC-K4 | `_SAFE_ID` regex + `is_relative_to()` | `storage/models.py` | 5 |
| SEC-K5 | `owner_id` in session metadata + `verify_owner()` | `brand_api.py` | 3 |

- 21 nieuwe security tests in `tests/test_security_fixes.py`
- 239 tests passed, 0 regressies

### OIDC tenant koppeling gefixt (SEC-H3 + T-FIX)

Root cause: Authentik `sub_mode=user_email` → meerdere users met zelfde email kregen zelfde `sub` claim → SSO login als Customer werd gekoppeld aan admin account.

3 fixes doorgevoerd:
1. **Authentik sub_mode** → `hashed_user_id` (unieke `sub` per user)
2. **OIDC email-fallback** weigert koppeling als >1 user met zelfde email (`get_all_by_email()`)
3. **Tenant sync gestopt** — tenant wordt niet meer overschreven door OIDC claims, admin beheert

DB state gecorrigeerd: `customer` user gekoppeld aan Authentik Customer account via `oidc_subject`.

### Geverifieerd op productie
- [x] Customer user ziet alleen eigen templates (bic_factuur, bic_rapport)
- [x] Customer user ziet geen admin panel (role=user)
- [x] OpenAEC admin accounts werken correct met default tenant

---

## Sessie 22 maart (3) — Deploy + Verificatie

### Gedeployed (commits `fac8545`, `beea126`)
- [x] Tenant isolatie fixes (templates, brands, stationery)
- [x] localStorage `serverReportId` fix
- [x] `VITE_API_URL` leeggemaakt (was hardcoded `https://report.open-aec.com`)

### SSO werkt weer na deploy
- `report.open-aec.com` → redirect naar `report.open-aec.com` verloor het pad
- Oorzaak: frontend had `VITE_API_URL=https://report.open-aec.com` gebaked in productie JS
- Fix: `.env.production` → `VITE_API_URL=` (leeg = relatieve URLs, domein-onafhankelijk)
- Server is GEEN git repo (`/opt/openaec/`) — deploy via eigen deploy script

### Productie verificatie (23 maart)

- [x] **Templates** — Customer user ziet alleen eigen templates ✅
- [x] **Admin panel** — Customer user (role=user) ziet geen admin panel ✅
- [x] **OIDC login** — Customer en OpenAEC accounts resolven naar juiste DB users ✅
- [ ] **Rapport opslag** — Meerdere rapporten opslaan zonder overschrijven (nog testen)
- [ ] **Organisaties tab** — Moet verwijderd zijn uit admin panel

### Security items
- **SEC-K1 t/m SEC-K5 (kritiek):** GEFIXT in sessie 23 maart
- **SEC-H1 t/m SEC-H4 (hoog) + SEC-M1 t/m SEC-M9 (medium):** Zie TODO.md, nog open

---

## Sessie 22 maart (2) — Deploy + Admin Cleanup

- [x] **Deploy naar productie** — SSO-only login + BIC Rapport template live
  - Server: `/opt/openaec/`, SSH alias `hetzner`, user `jochem`
  - `docker compose build --no-cache` nodig (met cache pakt Docker oude frontend layers)
- [x] **Organisaties tab verwijderd** uit admin panel
  - `OrganisationManagement.tsx` verwijderd
  - Tab, store state, en API client functies opgeruimd
  - Backend endpoints blijven beschikbaar (API keys)
  - Commit `eabd643`, gedeployed

---

## Sessie 22 maart (1) — Security Audit + Tenant Isolatie Fixes

### Volledige code review uitgevoerd

Alle bestanden geaudit op bugs, inconsistenties, security issues en code quality.
Resultaat: **5 kritieke, 4 hoge, 9 medium** bevindingen. Zie `TODO.md` sectie `SEC`.

### Bugs gefixt (deze sessie)

**BUG-1: `serverReportId` niet bewaard in localStorage (GEFIXT)**
- Symptoom: Na page refresh overschrijft elke save een willekeurig rapport; altijd maar 1 rapport in projecten
- Oorzaak: localStorage auto-save bewaarde `serverReportId` en `serverProjectId` niet
- Fix: 3 wijzigingen in `reportStore.ts` (auto-save + subscribe) en `App.tsx` (restore)

**BUG-2: Templates van andere tenants zichtbaar (GEFIXT)**
- Symptoom: Customer user ziet OpenAEC templates en vice versa
- Oorzaak: `list_templates()` scande altijd package-wide `assets/templates/` als fallback
- Fix: `template_loader.py` + `tenant_resolver.py` — met `tenant_slug` wordt alleen eigen tenant-directory gescand

**BUG-3: Brands van alle tenants zichtbaar (GEFIXT)**
- Symptoom: `/api/brands` toonde brands van alle tenants
- Oorzaak: `list_brands()` scande alle tenant directories in `tenants_root`
- Fix: `brand.py` + `tenant_resolver.py` — met `tenant_slug` alleen eigen brand tonen

**BUG-4: Cross-tenant template generatie mogelijk (GEFIXT)**
- Symptoom: User kon `customer_bic_factuur` template gebruiken vanuit OpenAEC tenant
- Oorzaak: `_resolve_tenant_and_template()` scande alle tenant directories
- Fix: `api.py` — tenant wordt nu altijd afgeleid uit `user.tenant`, geen cross-tenant scan

**BUG-5: Stationery van alle brands zichtbaar (GEFIXT)**
- Symptoom: `/api/stationery` toonde stationery van alle tenants in package
- Oorzaak: Package-wide `assets/stationery/` werd volledig gescand
- Fix: `api.py` — alleen eigen tenant stationery, fallback naar package stationery voor eigen tenant

### Openstaande security bevindingen (TODO)

| ID | Ernst | Omschrijving | Status |
|----|-------|-------------|--------|
| SEC-K1 | Kritiek | `load()` / `_resolve_path()` bypass tenant-isolatie | ✅ GEFIXT |
| SEC-K2 | Kritiek | Brand-override in generate endpoints | ✅ GEFIXT |
| SEC-K3 | Kritiek | Upload endpoint geen bestandstype validatie | ✅ GEFIXT |
| SEC-K4 | Kritiek | Path traversal in rapport opslag | ✅ GEFIXT |
| SEC-K5 | Kritiek | Brand API sessies geen user isolatie | ✅ GEFIXT |
| SEC-H1 | Hoog | IDOR op `list_reports` (project_id) | TODO |
| SEC-H2 | Hoog | Admin endpoints missen tenant-check | TODO |
| SEC-H3 | Hoog | OIDC email-linking account takeover | ✅ GEFIXT |
| SEC-H4 | Hoog | `_resolve_brand_from_template()` geen tenant check | TODO |
| SEC-M1–M9 | Medium | CORS, rate limiting, JWT, 401 interceptor, etc. | TODO |

### Gewijzigde bestanden

| Bestand | Wijziging |
|---------|-----------|
| `frontend/src/stores/reportStore.ts` | `serverReportId` + `serverProjectId` in localStorage auto-save + subscribe |
| `frontend/src/App.tsx` | Restore `serverReportId` + `serverProjectId` uit localStorage |
| `src/openaec_reports/core/template_loader.py` | `tenant_slug` parameter, `list_templates()` strikt per tenant |
| `src/openaec_reports/core/brand.py` | `tenant_slug` parameter, `list_brands()` alleen eigen tenant |
| `src/openaec_reports/core/tenant_resolver.py` | `tenant_slug` doorgeven aan TemplateLoader + BrandLoader |
| `src/openaec_reports/api.py` | `_resolve_tenant_and_template()` geen cross-tenant scan, `/api/stationery` tenant-only |

---

## Sessie 21 maart (3) — BIC Rapport Template + User Fixes

- [x] **BIC Rapport template aangemaakt** — 8 nieuwe page_types + 1 template YAML
  - `bic_rapport.yaml` template met 14 pagina's (portrait + landscape mix)
  - Nieuwe page_types: inhoudsopgave, voorziening_object, bic_rapport_details, herstelwerkzaamheden, tekening_pagina, controlelijst_bic, onderhouds_inspecties, historie_bic, historie_herstel, foto_bijlage
  - Hergebruikt: voorblad_bic, locatie, achterblad
  - Coördinaten pixel-exact gemeten uit `336.01-BIC Rapportage.pdf`
- [x] **Voorbeeld JSON** — `schemas/example_bic_rapport.json` met realistische BIC data
- [x] **Test-PDF gegenereerd** — 14 pagina's, lokaal succesvol
- [x] **User fixes op productie** (via admin API):
  - OpenAEC user: tenant hersteld naar `default`
  - jochem user: tenant gezet op `default`
  - Nieuwe `customer` user aangemaakt (local, tenant=customer)
- [x] **Gepusht naar GitHub** — commit `982461e`
- [ ] **Deploy nog nodig** — `bic_rapport` template nog niet live op server
  - Run `deploy.sh` op server, of: `cd /opt/openaec/bm-reports-api && git pull && cd /opt/openaec && docker compose build --no-cache bm-reports-api && docker compose up -d bm-reports-api`

---

## Sessie 21 maart (2) — Tenant Resolution Debug

- **Probleem:** `Template 'bic_rapport' niet gevonden voor tenant 'default'` op productie
- **Oorzaak:** User heeft `tenant: "default"` (of leeg) in profiel, maar roept template `bic_rapport` aan dat bij tenant `customer` hoort
- **Overwogen en afgewezen:** Cross-tenant template fallback scan — templates zijn user-specifiek en mogen niet tenant-grenzen overschrijden
- **Juiste fix (TODO):** De user moet de correcte tenant-toewijzing krijgen via:
  1. Authentik OIDC token: `tenant` claim toevoegen aan de user's scope
  2. Of handmatig in de database: `UPDATE users SET tenant='customer' WHERE ...`
  3. Of de request moet `brand: "customer"` meesturen
- **Code ongewijzigd** — geen cross-tenant leaking geïntroduceerd

---

## Sessie 21 maart (1) — SSO-only Auth + Fixes

- [x] **Auth: SSO-only** — Lokale username/password login uitgeschakeld
  - Backend: `/login` en `/register` endpoints afgesloten achter `OPENAEC_LOCAL_AUTH_ENABLED` (default `false`)
  - Frontend: LoginPage vereenvoudigd naar alleen SSO-knop, registratiepagina verwijderd
  - 3 nieuwe tests (`TestSsoOnly`), alle 22 auth tests passed
  - Noodluk: `OPENAEC_LOCAL_AUTH_ENABLED=true` om lokale login tijdelijk weer aan te zetten
- [x] **Fix: SSO-links in TitleBar** — `checkOidcEnabled()` toegevoegd aan App.tsx startup
  - `getAuthentikUserUrl()` gaf `null` terug na page refresh omdat OIDC config alleen vanuit LoginPage werd opgehaald
- [x] **TODO: F6** — Undo in tekstvelden genoteerd (Ctrl+Z/Y in `alwaysActive` blokkeert browser-native undo in inputs)
- [x] **Deploy** — Gedeployed naar `report.open-aec.com` (redirect van `report.open-aec.com`)

---

## Desktop App — Tauri v2 (20 maart)

| Component | Status |
|-----------|--------|
| **Scaffold** (`src-tauri/`) | ✅ Compleet |
| — `tauri.conf.json` (v2, 1280×800, CSP, NSIS bundle) | ✅ |
| — Rust wrapper (`lib.rs`, `main.rs`, `build.rs`) | ✅ |
| — Shell plugin (externe links, SSO) | ✅ |
| — Capabilities (`core:default`, `shell:allow-open`) | ✅ |
| **Root Cargo.toml** (workspace, excludeert `rust/`) | ✅ |
| **App icons** (PNG 32/128/256/1024, ICO) | ✅ Placeholder |
| **GitHub Actions** (`release-desktop.yml`) | ✅ 4-platform builds |
| — Windows (NSIS `.exe`) | ✅ Gebouwd |
| — macOS ARM (`.dmg`) | ✅ Gebouwd |
| — macOS Intel (`.dmg`, cross-compile via macos-14) | ✅ Gebouwd |
| — Linux (`.deb`, `.AppImage`, `.rpm`) | ✅ Gebouwd |
| **Release v0.2.0-alpha** | ✅ Draft op GitHub |
| **Authentik redirect URI** (`http://tauri.localhost`) | ⏳ Handmatige actie |
| **Code signing** | ⏳ Gepland voor v0.3+ |

### Architectuur
- Thin wrapper: frontend identiek aan web, PDF generatie via cloud API (`report.open-aec.com`)
- `VITE_API_URL=https://report.open-aec.com` in productie build
- OIDC redirect werkt automatisch (`window.location.origin` = `http://tauri.localhost` in Tauri)

---

## Frontend — Office-style Chrome (19-20 maart)

| Component | Status |
|-----------|--------|
| **TitleBar** (logo, tabs, user dropdown, admin knop) | ✅ |
| **Ribbon** (Home, Insert, View tabs met tool groups) | ✅ |
| **Backstage** (full-screen overlay, New/Open/Save/Export/Admin) | ✅ |
| **StatusBar** (zoom, preview toggle, validation count) | ✅ |
| **Modal** (generieke modal component) | ✅ |
| **SettingsDialog** (taal, theme, sneltoetsen) | ✅ |
| **FeedbackDialog** (issue/bug rapportage) | ✅ |
| **ShortcutHelp** (sneltoetsen overlay) | ✅ |
| **Theme systeem** (~80 CSS custom properties, light + openaec) | ✅ |
| **i18n** (5 namespaces, NL + EN) | ✅ |
| **SSO** (Authentik, user dropdown met profiel link) | ✅ |

---

## Rust Implementatie — Phase 1-4 (15 maart)

| Component | Status | Tests | Lines |
|-----------|--------|-------|-------|
| **openaec-layout** (eigen ReportLab) | ✅ Compleet | 9 | ~1,200 |
| — types.rs (Pt, Mm, Size, Rect, Color, A4/A3) | ✅ | 5 | 200 |
| — fonts.rs (FontRegistry, TTF metrics, text width) | ✅ | 1 | 160 |
| — draw.rs (DrawOp, DrawList) | ✅ | — | 130 |
| — flowable.rs (Flowable trait, SplitResult) | ✅ | — | 55 |
| — spacer.rs (Spacer, PageBreak) | ✅ | — | 70 |
| — paragraph.rs (word wrap, ParagraphStyle) | ✅ | 1 | 230 |
| — table.rs (grid, header, zebra-striping, split) | ✅ | 2 | 250 |
| — image_flowable.rs (ImageData, aspect ratio) | ✅ | — | 120 |
| — frame.rs (flowable container, overflow) | ✅ | — | 100 |
| — page_template.rs (PageCallback) | ✅ | — | 50 |
| — doc_template.rs (multi-page PDF assembly via printpdf) | ✅ | — | 360 |
| **openaec-core** (data+rendering) | ✅ | 52 | ~3,300 |
| — schema.rs (alle block types + Spreadsheet) | ✅ | 30 | 1,150 |
| — brand.rs (YAML loading, color/font resolution) | ✅ | 8 | 600 |
| — tenant.rs (multi-tenant asset paden) | ✅ | 5 | 256 |
| — font_manager.rs (Inter discovery + fallback) | ✅ | 9 | 316 |
| — block_renderer.rs (ContentBlock → Flowable) | ✅ | 9 | 420 |
| — engine.rs (ReportData → PDF, font setup) | ✅ | 3 | 260 |
| **openaec-cli** | ✅ | — | 115 |
| — generate (JSON → PDF) | ✅ | — | — |
| — validate (JSON schema check) | ✅ | — | — |
| — serve (placeholder) | ⏳ | — | — |
| **openaec-server** (Axum API) | ✅ | — | 95 |
| — GET /api/health | ✅ | — | — |
| — GET /api/templates | ✅ | — | — |
| — GET /api/brands | ✅ | — | — |
| — POST /api/validate | ✅ | — | — |
| — POST /api/generate | ✅ | — | — |
| **openaec-ffi** (C ABI wrapper) | ⏳ Stubs | — | 39 |
| **Totaal** | **62 tests, 0 failures** | **62** | **~5,500** |

### E2E Verificatie

```
$ cargo run -p openaec-cli -- generate --data tests/fixtures/example_structural.json --output output/test_rust_structural.pdf
Registering font: LiberationSans-Regular, LiberationSans-Bold, Inter-Bold, Inter-Book, ...
Generated: output/test_rust_structural.pdf (3,022,534 bytes)

$ python -c "import fitz; doc=fitz.open('output/test_rust_structural.pdf'); print(f'Pages: {len(doc)}')"
Pages: 2
```

- 2 pagina's, 6 secties, 13 fonts embedded (Liberation Sans + Inter)
- Alle content block types renderen (paragraph, calculation, check, table, bullet_list, heading_2, spacer, page_break, spreadsheet)
- Image en Map blocks zijn gestubbed (placeholder)
- Special pages: cover (paarse achtergrond + titel), colofon (2-kolom metadata), TOC (sectie-index), backcover (turquoise + contact)
- Dockerfile: `rust/Dockerfile` multi-stage build (rust:1.85 → debian:bookworm-slim), healthcheck, OPENAEC_FONTS_DIR
- Deploy: `docker build -f rust/Dockerfile .` vanuit monorepo root

---

## Deployment

| Omgeving | URL | Status |
|----------|-----|--------|
| Productie | https://report.open-aec.com | ✅ Online |
| API Health | https://report.open-aec.com/api/health | ✅ OK (v0.1.0) |
| `/api/generate/v2` | POST | ✅ Werkt (OpenAEC rapporten) |
| `/api/generate/template` | POST | ✅ Werkt (Customer BIC) |
| Deploy script | `deploy.sh` | ✅ Git pull → docker build → deploy → health check |

---

## Engines

| Engine | Endpoint | Lokaal | Productie | Gebruik |
|--------|----------|--------|-----------|---------|
| V1 — `Report.from_dict()` | `/api/generate` | ✅ | ✅ | Legacy |
| V2 — `ReportGeneratorV2` | `/api/generate/v2` | ✅ | ✅ | OpenAEC rapporten |
| V3 — `TemplateEngine` | `/api/generate/template` | ✅ | ⏳ Wacht op deploy | Customer BIC |

### TemplateEngine (V3) — Lokale Tests

| Component | Status | Tests |
|-----------|--------|-------|
| `template_config.py` — dataclasses + parsers + ImageZone | ✅ | 40+ |
| `template_resolver.py` — template discovery | ✅ | 20+ |
| `template_engine.py` — PDF assembly + font ascent + page numbering | ✅ | 42+ |
| `data_transform.py` — JSON → flat dict | ✅ | via E2E |
| E2E: 6-pagina PDF mixed orientation + stationery | ✅ | 3 tests |

**Lokale E2E output (`output/test_template_e2e.pdf`):**
- 6 pagina's, correct P-P-P-L-L-P orientatie
- 5 XObjects per pagina (stationery embedded)
- Tekst correct ingevuld op alle pagina's (Arial fonts, Y-offset <0.7pt afwijking)
- Paginanummering "Pagina X van Y" (cover excluded)
- Achterblad met tekst "Deze pagina is [met opzet] leeg gelaten"
- Image zones support (locatie pagina)

### Customer Tenant Assets

| Asset | Status | Pad |
|-------|--------|-----|
| `brand.yaml` (Arial fonts, font_files) | ✅ | `tenants/customer/brand.yaml` |
| Stationery PDFs (5) | ✅ | `tenants/customer/stationery/` |
| Page type YAMLs (6) | ✅ | `tenants/customer/page_types/` |
| Template YAML | ✅ | `tenants/customer/templates/bic_factuur.yaml` |
| Arial font files (4 TTF) | ✅ | `tenants/customer/fonts/` |
| Placeholder aerial photo | ✅ | `tenants/customer/assets/placeholder_aerial.png` |
| Test data | ✅ | `schemas/test_336_bic_factuur.json` |

---

## Frontend

| Feature | Lokaal | Productie |
|---------|--------|-----------|
| Block editors (paragraph, table, image, calc, check, map, spreadsheet) | ✅ | ⏳ Wacht op deploy |
| Template selector + scaffold loader | ✅ | ✅ |
| Split view + live preview | ✅ | ✅ |
| JSON import/export | ✅ | ✅ |
| Smart endpoint routing (V2 vs TemplateEngine) | ✅ | ✅ |
| Admin: Asset replace button | ✅ | ✅ |
| Admin: Organisatie beheer (CRUD) | ✅ | ⏳ Wacht op deploy |
| Profiel pagina (self-service) | ✅ | ⏳ Wacht op deploy |
| Admin: BrandExtractWizard (4-stap, paars) | ✅ | ✅ |

---

## API Endpoints

| Endpoint | Method | Auth | Status |
|----------|--------|------|--------|
| `/api/health` | GET | ❌ | ✅ |
| `/api/templates` | GET | ✅ | ✅ |
| `/api/brands` | GET | ✅ | ✅ |
| `/api/validate` | POST | ✅ | ✅ |
| `/api/generate` | POST | ✅ | ✅ |
| `/api/generate/v2` | POST | ✅ | ✅ |
| `/api/generate/template` | POST | ✅ | ⏳ Wacht op deploy |
| `/api/upload` | POST | ✅ | ✅ |
| `/api/auth/profile` | GET | ✅ | ✅ |
| `/api/auth/profile` | PATCH | ✅ | ✅ |
| `/api/admin/organisations` | GET | ✅ Admin | ✅ |
| `/api/admin/organisations` | POST | ✅ Admin | ✅ |
| `/api/admin/organisations/{id}` | GET | ✅ Admin | ✅ |
| `/api/admin/organisations/{id}` | PATCH | ✅ Admin | ✅ |
| `/api/admin/organisations/{id}` | DELETE | ✅ Admin | ✅ |

---

## Cleanup Status (28 feb)

- [x] Deprecated `modules/customer/` verwijderd
- [x] Deprecated `modules/yaml_module.py` verwijderd
- [x] Deprecated `tenants/customer/modules/` verwijderd
- [x] Prompt bestanden gearchiveerd naar `_archive/prompts/`
- [x] pytest cache opgeruimd

---

## Sessie 14 maart — T5/T6/T8 Implementatie

- [x] **T8** — Kadaster RD↔WGS84 conversie: pyproj Transformer vervangt polynoom-benadering
  - `pyproj>=3.6` toegevoegd aan dependencies
  - `wgs84_to_rd()` herschreven met `Transformer.from_crs("EPSG:4326", "EPSG:28992")`
  - `rd_to_wgs84()` reverse methode toegevoegd
  - 17 tests: referentiepunten + roundtrip nauwkeurigheid <0.0001°
- [x] **T6** — Drie rapporttypen volledig geïmplementeerd:
  - `StructuralReport`: uitgangspunten, belastingen (subsecties), elementen met CalculationBlock/CheckBlock, UC overzicht tabel, conclusie
  - `DaylightReport`: uitgangspunten, situatie, daglichtberekening per ruimte (ramen tabel, A_eq berekening, Bouwbesluit check), toetsingsoverzicht, conclusie
  - `BuildingCodeReport`: projectgegevens, toetsingen per hoofdstuk met CheckBlocks, samenvattend overzicht, conclusie
  - 28 tests (unit + PDF integratie per rapporttype)
- [x] **T5** — YAML Editor fase 2 compleet:
  - `ImageZoneSection.tsx`: bind, x/y, width/height, fallback
  - `ContentFrameSection.tsx`: x/y, width/height met toggle
  - Geïntegreerd in `YamlFormEditor.tsx`, geëxporteerd via `index.ts`
  - TypeScript type check clean
- [x] 1121 tests passed (45 nieuw), 0 regressies

---

## Sessie 11 maart (2) — T9 Font Embedding Fix (2de2741)

- [x] **T9** — Font Embedding Fix: Liberation Sans als embedded fallback
  - 5 Liberation Sans/Mono TTFs gebundeld in `assets/fonts/` (Apache 2.0)
  - `fonts.py`: `register_liberation_fonts()`, `_HELVETICA_TO_LIBERATION` mapping, `get_font_name()` onderschept Helvetica
  - `styles.py`: `@functools.cache` vervangen door manual flag
  - `renderer_v2.py`: FontManager laadt Liberation Sans TTF i.p.v. `fitz.Font("helv")`
  - Alle Helvetica defaults vervangen in 15 bronbestanden + 2 testbestanden
  - `default.yaml` brand fonts → LiberationSans
  - PDF verificatie: alle content fonts zijn TrueType (embedded), geen Type1
  - 1045 tests passed, 0 regressies

---

## Sessie 11 maart (1) — Issues #5/#7/#9/#11 + Organisaties + Deploy

- [x] **#9** — SpreadsheetBlock: grid-tabel met headers, zebra-striping, rijnummers, voetnoot
  - `components/spreadsheet_block.py` + `create_spreadsheet()` in block_registry
  - Frontend: `SpreadsheetEditor.tsx` met TSV copy/paste support
  - JSON schema uitgebreid met `block_spreadsheet` definitie
- [x] **#11** — AI-instructies document (`docs/ai-instructions.md`)
  - Engelstalig document voor externe AI-tools: API, auth, block types, MCP server, voorbeeld JSON
- [x] **#5** — Organisation model + admin CRUD
  - `Organisation` dataclass + `OrganisationDB` in `auth/models.py`
  - 5 admin endpoints: GET/POST/GET/PATCH/DELETE `/api/admin/organisations`
  - Frontend: `OrganisationManagement.tsx` in admin panel
  - User model uitgebreid met `organisation_id`
- [x] **#7** — Adviseur koppeling via profiel + organisatie
  - `GET/PATCH /api/auth/profile` endpoints (self-service)
  - Auto-fill `adviseur_naam` en `adviseur_bedrijf` in generate endpoints
  - Organisatie genest in profiel response
- [x] Deploy script (`deploy.sh`): git pull → docker build --no-cache → deploy → health check
- [x] Dead code cleanup: `src/bm_reports/` directory + `docs/TENANT_GUIDE.md` verwijderd
- [x] 764 tests passed

---

## Fixes (1 maart)

### Pixel precision fixes — 6 issues (f3b8228)
- **Issue 1 — Arial fonts:** Per-tenant font registratie via `font_files` mapping in brand.yaml. Nieuwe `register_tenant_fonts()` in `fonts.py`. Customer brand gewijzigd van Helvetica → Arial.
- **Issue 2 — Page numbering:** "Pagina X van Y" format. Cover page excluded van content count. `_BuildContext` uitgebreid met `content_page_count` en `page_number_offset`.
- **Issue 3 — Y-offset correction:** Font ascent correctie in `_draw_text_zones()`. PyMuPDF bbox-top (referentie) vs ReportLab baseline offset = `pdfmetrics.getAscent()`. Delta gereduceerd van ~11pt naar <0.7pt.
- **Issue 4 — Image zones:** Nieuwe `ImageZone` dataclass in `template_config.py`. `_draw_image_zones()` in template engine. Locatie pagina configuratie met placeholder aerial photo.
- **Issue 5 — Achterblad text:** Text zones toegevoegd in `achterblad.yaml`: "Deze pagina is [met opzet] leeg gelaten", footer, paginanummer.
- **Issue 6 — BIC controles fontsize:** Table body fontsize → 10pt in `bic_controles.yaml`.

### Admin panel cleanup (ab93b13)
- **Replace button:** "Vervangen" knop per asset bestand in BrandManagement. Upload met filename rename via `new File([file], replaceTarget)`.
- **BrandWizard verwijderd:** Standalone BrandWizard (blauw, 3-stap) volledig verwijderd — 8 bestanden. BrandExtractWizard (paars, 4-stap) blijft als enige brand creation flow.
- **AdminTab type:** `"brand-wizard"` verwijderd uit union type.

### T10 Planning — User Reports + Profiel (3 maart)
- Uitvoerplan geschreven: `PLAN-user-reports.md`
- TODO.md bijgewerkt met T10.1–T10.16 (16 subtaken, 5 fasen)
- 8 nieuwe bestanden, 7 te wijzigen bestanden, 4 test bestanden
- Features: auto-save PDFs, user profiel, rapporten-lijst, wachtwoord wijzigen

### Tenant resolution in `/api/generate/template` — GEFIXT (cfaa808)
- **FIX-1:** Nieuwe `_resolve_tenant_and_template()` helper leidt tenant af uit template naam prefix (bijv. `customer_bic_factuur` → tenant=`customer`). Scant bestaande tenant directories, sorted by name length (langste eerst) om ambiguïteit te voorkomen. Fallback: `data["brand"]` → `user.tenant` → `"customer"`.
- **FIX-2:** `_resolve_tenants_dir()` herschreven: checkt `OPENAEC_TENANTS_ROOT` env var eerst, dan parent van `OPENAEC_TENANT_DIR` (met brand.yaml verificatie), dan source tree, dan package-relatief. Dockerfile had `OPENAEC_TENANTS_ROOT=/app/tenants` al.
- **FIX-3:** Frontend smart routing code was al correct in broncode. Probleem was Docker cache → vereist `docker build --no-cache` bij volgende deploy.
- **Tests:** 888 passed, 0 failures. E2E PDF generatie OK.
