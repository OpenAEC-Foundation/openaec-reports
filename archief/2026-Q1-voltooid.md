# Archief — Q1 2026 (voltooid werk openaec-reports)

> Afgerond werk. Live context staat in `STATUS.md` en `TODO.md`.
> Sessie-logs per maand samengevat. Voor git-history: `git log --since="2026-01-01" --until="2026-03-31"`.

---

## Maart 2026 — samenvatting

### Eind maart — Cloud migratie + Rust server uitbouw

**30 maart — Project container model in cloud.py**
- [x] Python `cloud.py` gemigreerd van `99_overige_documenten/reports/` naar `reports/` met backward compatibility
- [x] Constanten `DIR_REPORTS`, `MANIFEST_FILENAME = "project.wefc"`, fallback-lezen van legacy paden
- [x] `project.wefc` manifest update na PDF upload (read-merge-write, guid + created behouden)
- [x] Rust server: 3 nieuwe cloud routes (`/api/cloud/projects`, `/api/cloud/projects/{project}/reports`, `POST /api/cloud/projects/{project}/upload`)
- [x] Tenant-aware via `OPENAEC_TENANT` + `tenants.json`, volume-mount reads met WebDAV fallback
- [x] Tests: Rust 208 passing, Python 8 cloud tests passing

**28 maart — Rust Server module split + openaec-engine crate**
- [x] `openaec-engine` crate (~2400 LOC, 28 tests) — pure Rust V3 TemplateEngine
  - Modules: engine, pdf_backend, font_engine, text, data_bind, zone_renderer, flow_layout, special_pages
  - Stack: `pdf-writer` + `lopdf` + `ttf-parser` (geen Python/AGPL)
- [x] Server module split: `main.rs` (769 regels) → 14 modulaire bestanden (`routes/`, `db/`, `state.rs`, `error.rs`, `helpers.rs`)
- [x] CORS: `tower-http::CorsLayer` met expliciete origins, `allow_credentials(true)`, env-driven via `CORS_ORIGINS`
- [x] V3 endpoint `POST /api/generate/template` → `openaec_engine::Engine`
- [x] Async-safety via `tokio::task::spawn_blocking()`
- [x] Template loader scant alle tenants (15 templates gevonden)
- [x] Deployed `01cf2f4` naar `report.open-aec.com`

### Midden maart — Security fixes + CR Kritiek

**28 maart sessie 1 — CR-K security fixes (4 van 6 resterende)**
- [x] **CR-K6** Nextcloud credentials lazy loading — `_get_nextcloud_*()` functies i.p.v. module-level constanten (8 tests)
- [x] **CR-K2** JWT default secret enforcement — `enforce_jwt_secret()` in FastAPI `lifespan`, productie → RuntimeError (3 tests)
- [x] **CR-K5** SQL identifier quoting — `quote_identifier()` helper met regex validatie, 4 locaties geupdate (11 tests)
- [x] **CR-K3** Brand session cleanup — `cleanup_stale_sessions(max_age=24h)` bij startup (8 tests)
- [x] **CR-K4** False positive — SVG icons zijn hardcoded constanten, geen XSS-vector, gedowngraded naar CR-L
- [x] **CR-K1** Dockerfile draait niet meer als root (`appuser` + `USER` directive)
- Totaal: 30 nieuwe tests, 1214 passed, 50 skipped

**27 maart — Flow Layout auto page-break**
- [x] `_paginate_flow_zones()` — overflow zones automatisch naar vervolg-pagina's
- [x] Config: `flow_content_start_y_mm` op PageType (default 32mm)
- [x] Footer zones herhaald op elke pagina, correcte paginanummering
- [x] Tests: 26 in `test_flow_layout.py` (13 bestaand + 13 nieuw)
- [x] Deployed `2a413a8` naar `report.open-aec.com`

**26 maart — Flow Layout text zones**
- [x] `_apply_flow_layout()` pre-processing — text wrapping berekent extra ruimte en verschuift onderliggende zones
- [x] PageType config: `flow_layout: bool` + `flow_footer_y_mm: float`
- [x] 4 page_types geactiveerd (voorziening_object, bic_rapport_details, herstelwerkzaamheden, locatie)

**24 maart — BIC Rapport 17 pagina's compleet**
- [x] **S1** BIC Rapport template — 17 pagina's, 5 nieuwe page_types (tekening_overzicht, tekening_detail, tekening_kadaster, vvv_verklaring, schade_fotos)
- [x] Field groups: `_extract_field_groups()` scant page_type YAML's → `FieldGroupForm` component (25 groepen)
- [x] Text wrapping: `TextZone.max_width_mm` + `_wrap_text()`, 87 text_zones
- [x] PDOK kaarten: `/api/pdok/map` + `/api/pdok/services` endpoints, image zones met lat/lon → automatische kaart
- [x] Layout fixes: rechterkolom, tabel origin_y, paginanummers, TOC paginanummers rechts
- [x] Formeel JSON schema: `schemas/bic_rapport.schema.json`
- [x] Voorbeeld JSON met 114/125 velden gevuld

### SEC-K Security fixes (23 maart — alle 5 kritieke items)

- [x] **SEC-K1** `load()` / `_resolve_path()` tenant-isolatie — template_loader + brand respecteren nu `tenant_slug`, geen fallback naar andere tenants (5 tests)
- [x] **SEC-K2** Brand-override in generate endpoints — `_resolve_brand_with_tenant_check()` helper, expliciete brand die niet matcht → 403 (2 tests, toegepast op alle 3 generate endpoints)
- [x] **SEC-K3** Upload endpoint bestandstype + size validatie — allowlist (.jpg/.jpeg/.png/.gif/.webp/.svg/.pdf) + max 10 MB (6 tests)
- [x] **SEC-K4** Path traversal in rapport opslag — `_SAFE_ID` regex `^[a-zA-Z0-9_-]+$` + `is_relative_to()` check in `_report_path()` (5 tests)
- [x] **SEC-K5** Brand sessies user-isolatie — `owner_id` in session metadata, `verify_owner()` op alle 7 session endpoints (3 tests)
- [x] **SEC-H3** OIDC email-linking account takeover — email-fallback koppelt alleen als precies 1 user matcht, tenant niet meer uit OIDC, Authentik `sub_mode = hashed_user_id`

### T-FIX — User-Tenant koppeling (23 maart)

- [x] Tenant wordt NIET meer gesynct vanuit OIDC — admin beheert tenant in DB
- [x] Nieuwe SSO users krijgen `tenant=""`, admin wijst toe via admin panel
- [x] Authentik `sub_mode → hashed_user_id` voor unieke user identificatie

### 14 maart — T5/T6/T8

- [x] **T5** YAML Editor fase 1+2 compleet: ImageZoneSection + ContentFrameSection form editors
- [x] **T5.1–T5.7** API CRUD, frontend browser, upload/download, preview, visuele editor, live preview, kleurenpicker
- [x] **T5.8** BrandExtractWizard (4-stap, paurs) operationeel in admin panel
- [x] **T6** Drie rapporttypen geïmplementeerd met volledige `build_sections()`:
  - StructuralReport (uitgangspunten, belastingen, elementen met Calculation/CheckBlock, UC overzicht)
  - DaylightReport (ruimtes met raamberekening, equivalente daglichtoppervlakte, toetsing NEN 2057)
  - BuildingCodeReport (hoofdstukken met CheckBlocks per artikel, samenvattend overzicht)
- [x] **T8** Kadaster RD↔WGS84 conversie via pyproj (<1mm nauwkeurigheid), `rd_to_wgs84()` reverse
- [x] Tests: 17 voor kadaster + 28 voor rapporttypen (unit + PDF integratie)

### 11 maart — T9 Font Embedding Fix (commit `2de2741`)

- [x] Liberation Sans als embedded fallback voor Helvetica Type1
- [x] 5 Liberation Sans/Mono TTFs gebundeld (Apache 2.0)
- [x] `fonts.py`: `register_liberation_fonts()`, `_HELVETICA_TO_LIBERATION` mapping
- [x] `renderer_v2.py`: FontManager TTF i.p.v. `fitz.Font("helv")`
- [x] Helvetica defaults vervangen in 15 bronbestanden
- [x] 1045 tests passed

### 5 maart — Bug Fixes rendering + Colofon

- [x] **#14** Colofon: `revision_history` + `disclaimer` rendering in V1 en V2
- [x] **#6** Colofon update geverifieerd werkend (frontend chain intact)
- [x] Tabel text-wrap: cellen in `Paragraph` i.p.v. plain strings
- [x] Tabel page-break: `split()` methode op `BMFlowable` + `repeatRows=1`
- [x] Colofon velden: `field_values` mapping uitgebreid
- [x] Cover images: `base_dir` parameter op MCP server `generate_report()`
- [x] **#13** MCP-server wrapper operationeel

### 4 maart — Self-Registratie + Server-side Opslag + Projectstructuur

- [x] Open registratie: `POST /api/auth/register` met validatie, env var guard (`OPENAEC_REGISTRATION_ENABLED`)
- [x] RegisterPage frontend + authStore `register()` actie
- [x] Server-side rapport opslag: `storage/models.py` (SQLite + bestandssysteem)
- [x] 11 API endpoints: projecten CRUD, rapporten CRUD, verplaatsen, filteren
- [x] ProjectBrowser UI (split-panel), projectStore (Zustand), server-save (Ctrl+S)
- [x] Eigendom-isolatie: users zien alleen eigen projecten/rapporten
- [x] 37 nieuwe tests (registratie + opslag)

### 2 maart — API Key Management + OpenAEC Rebranding + Deploy

- [x] API Key Management UI: frontend ApiKeyManagement + admin tab
- [x] API types + store actions (list, create, revoke, delete), eenmalige plaintext display
- [x] `shared.tsx` extracted, `usersError` fix, staleness guard, clipboard error handling
- [x] Docker rebuild op Hetzner VPS
- [x] Customer BIC rapporten visueel gevalideerd — pixel-perfect
- [x] OpenAEC rebranding volledig: package rename (`bm_reports` → `openaec_reports`, 218 bestanden), env vars, CLI, frontend, Docker, domain, README, LICENSE, API key prefix
- [x] 1035 tests passed

### 1 maart — Pixel Precision Fixes + Admin Panel Cleanup + Tenant Resolution

- [x] Arial per-tenant font registratie
- [x] Page numbering "Pagina X van Y"
- [x] Font ascent Y-offset correctie (<0.7pt)
- [x] ImageZone support, achterblad text zones, BIC tabel fontsize 10pt
- [x] Admin Panel: Replace button per asset, oude BrandWizard verwijderd, BrandExtractWizard (paurs, 4-stap) operationeel
- [x] `_resolve_tenant_and_template()` helper, `_resolve_tenants_dir()` robuust met env vars
- [x] 888 tests passed

---

## Februari 2026

### 28 februari — TemplateEngine V3

- [x] 102+ unit tests, 3 E2E tests
- [x] 6-pagina PDF mixed orientation + stationery
- [x] Customer BIC factuur template compleet

---

## Rust Implementatie — volledige historie

### Phase 0 — Setup + Schema Types (maart)
- [x] 40 tests

### Phase 1 — openaec-layout (eigen ReportLab in Rust)
- [x] R1.1 Basis types (Pt, Mm, Size, Rect, Color, A4/A3) + FontRegistry
- [x] R1.2 DrawList (tekst, lijnen, rects, images)
- [x] R1.3 Flowable trait + SplitResult
- [x] R1.4 Spacer + PageBreak
- [x] R1.5 Paragraph (styled text, word-wrap, leading)
- [x] R1.6 Table (kolommen, stijlen, split over pagina's)
- [x] R1.7 Image flowable
- [x] R1.8 Frame (flowable container, overflow detectie)
- [x] R1.9 PageTemplate (PageCallback)
- [x] R1.10 DocTemplate (multi-page PDF assembly)
- [x] R1.11 PDF backend (printpdf crate)
- Tests: 11

### Phase 2 — Python libs porten (169 tests totaal)
- [x] R2.1 Schema sync: Spreadsheet block toegevoegd
- [x] R2.2 `document.rs` page sizes, marges — 260 LOC, 7 tests
- [x] R2.3 `styles.rs` font rollen, kleuren, paragraph styles — 463 LOC, 9 tests
- [x] R2.4 `template_config.rs` PageType, TextZone, ImageZone, flow layout — 460 LOC, 11 tests
- [x] R2.5 `template_loader.rs` YAML discovery, scaffold, multi-dir — 507 LOC, 7 tests
- [x] R2.6 `block_renderer.rs` ContentBlock → Flowable, alle block types
- [x] R2.7 `data_transform.rs` JSON → flat dict, BIC inject helpers — 560 LOC, 13 tests
- [x] R2.8 `stationery.rs` path resolver, format detection, caching — 223 LOC, 7 tests
- [x] R2.9 `toc.rs` TOC builder, styles, page numbers — 224 LOC, 6 tests
- [x] R2.10 `kadaster.rs` RD↔WGS84 polynoom, PDOK WMS URL builder — 354 LOC, 7 tests
- [x] R2.11 `json_adapter.rs` JSON laden, validatie, project/section extractie — 271 LOC, 9 tests
- [x] R2.12 `report_types.rs` structural, daylight, building_code builders — 1020 LOC, 12 tests

### Phase 3 — Rendering pipeline
- [x] R3.1 Block renderers (ContentBlock → Flowable) alle types
- [x] R3.2 Special pages (cover, colofon, TOC, backcover) — RawPage canvas rendering
- [x] R3.3 Engine (ReportData → PDF)

### Phase 4 — Server + CLI
- [x] R4.1 CLI wiring (generate, validate)
- [x] R4.2 Axum API server (health, generate, validate, templates, brands)
- [x] R4.3 Dockerfile (multi-stage, rust:1.85 + debian:bookworm-slim)
- R4.4 — **OPEN** Deploy als `report-rs.open-aec.com` (wacht op subdomein)

### Phase 5 — openaec-engine V3 (28 tests)
- [x] Pure Rust V3 TemplateEngine (~2400 LOC)
- [x] Modules: engine, pdf_backend, font_engine, text, data_bind, zone_renderer, flow_layout, special_pages

### Phase 6 — Server module split + CORS
- [x] main.rs → 14 modulaire bestanden
- [x] tower-http CORS met expliciete origins

**Totaal Rust: 197 tests, ~9.000 LOC**

---

## GitHub Issues — voltooid

- [x] **#2** — Auteur koppelen aan user (colofon auto-fill)
- [x] **#4** — Project → Report mother-children relatie (`projects` + `reports` tabellen, nullable `project_id`, cascade delete)
- [x] **#5** — Organisation / Project Browser (split-panel, server-side opslag, 11 API endpoints)
- [x] **#7** — Adviseur aan account koppelen + Authentik SSO (User model uitgebreid met phone/job_title/registration_number/company/auth_provider/oidc_subject, OIDC JWKS/RS256, auto-provisioning, PKCE OidcCallback, Docker Compose Authentik)
- [x] **#8** — Bij regenerate blijf op oorspronkelijke pagina (`previewPage` state + `#page=N` fragment)
- [x] **#9** — Spreadsheet blok met copy/paste naar LibreOffice Calc (TSV, JSON schema, block_registry)
- [x] **#11** — AI-instructies voor gebruik in andere tools (`docs/ai-instructions.md` Engelstalig)
- [x] **#12** — RUST Library (zie Rust Implementatie sectie)
- [x] **#13** — MCP-server (OpenAEC MCP wrapper, tools list_templates/get_template_scaffold/validate_report/generate_report/generate_report_v2, dedicated venv)

## Housekeeping voltooid

- [x] **H2** Dead code `src/bm_reports/` verwijderd + `docs/TENANT_GUIDE.md`
- [x] **H4** `fonts.py` herschreven met Liberation Sans documentatie
- [x] **H5** STATUS.md en TODO.md actualiseren (20 maart: Tauri + Chrome)
- [x] **CR-H6** `uploads/` directory naar `.gitignore`, bestanden uit tracking
- [x] **CR-H9** Frontend console.log klantdata in productie — gefixt met `import.meta.env.DEV` guard
- [x] **CR-H10** useEffect zonder dependency array in SpreadsheetEditor — gefixt
- [x] **CR-M12 / S3** Spook-templates uit `src/openaec_reports/assets/templates/` verwijderd (customer_bic_factuur.yaml, customer_bic_rapport.yaml, customer_sanering.yaml)

## Frontend multi-rapport / Desktop Tauri

- [x] **F3** Multi-rapport beheer (ProjectBrowser)
- [x] **D1** Tauri v2 scaffold (`src-tauri/`, thin wrapper, cloud API)
- [x] **D2** GitHub Actions release workflow (4-platform matrix build)
- [x] **D3** Release v0.2.0-alpha (draft op GitHub, alle artifacts)

## Infrastructure voltooid

- [x] **I0** Deploy script: `git pull` → `docker build --no-cache` → deploy → health check
- [x] **I4** CI/CD pipeline (GitHub Actions: lint, test, build, deploy + release-desktop)
- [x] **Q8** `OPENAEC_DEFAULT_BRAND` env var configureerbaar

## Inline TODO's opgelost

- [x] `core/fonts.py:13` Inter TTF pad instructies updaten — in T9
- [x] `data/kadaster.py:60` RD↔WGS84 conversie — in T8 (pyproj)
- [x] `reports/building_code.py:33` Bouwbesluit toetsingssecties — in T6
- [x] `reports/daylight.py:27` Daglichtsecties — in T6
- [x] `reports/structural.py:28` Sectie-opbouw vanuit data — in T6

---

## Links

- Live TODO: [`../TODO.md`](../TODO.md) — open items
- Live status: [`../STATUS.md`](../STATUS.md) — huidige state + engines/tenants/Rust tabellen
- Git history: `git log --since="2026-01-01" --until="2026-03-31" --oneline`
