# STATUS — openaec-reports

> Laatst bijgewerkt: 2026-03-28 (sessie 2)
> Sessie-historie ouder dan 2 sessies: zie `git log` of `git show <commit>:STATUS.md`

---

## Huidige Staat

- **1264 tests** collected (1214 passed, 50 skipped)
- **BIC Rapport:** 17 pagina's compleet, field groups, PDOK kaarten, flow layout met auto page-break
- **Security:** Alle 6 kritieke items gefixt (K1-K6), 1 hoge + 8 medium open (zie TODO.md)
- **Productie:** `report.open-aec.com` / `report.open-aec.com` — SSO-only, multi-tenant
- **Open:** S2 Sanering template

---

## Laatste Sessie — 28 maart (sessie 2)

### Rust Server Uitbouw + openaec-engine crate
- **openaec-engine crate:** V3 TemplateEngine in pure Rust (~2400 LOC), coordinate-based PDF rendering, 28 tests
  - Modules: engine, pdf_backend, font_engine, text, data_bind, zone_renderer, flow_layout, special_pages
  - Pure Rust stack: `pdf-writer` + `lopdf` + `ttf-parser` (geen Python/AGPL)
- **Server module split:** `main.rs` (769 regels) → 14 bestanden in modulaire structuur
  - `routes/`: health, templates, brands, stationery, generate, validate, admin, auth
  - `db/`: projects CRUD, reports CRUD
  - `state.rs`, `error.rs` (AppError enum), `helpers.rs`
- **CORS middleware:** `tower-http::CorsLayer` met expliciete origins, `allow_credentials(true)`, configureerbaar via `CORS_ORIGINS` env var
- **V3 Engine endpoint:** `POST /api/generate/template` → `openaec_engine::Engine` (apart van legacy V1/V2)
- **Async-safety:** Alle PDF generatie in `tokio::task::spawn_blocking()`
- **Template loader:** Scant alle tenants in `OPENAEC_TENANTS_ROOT` (15 templates gevonden)
- **BIC Schema docs:** `docs/CUSTOMER_BIC_SCHEMA.md` (598 regels), `test_bic_rapport.py`
- **Deployed:** `01cf2f4` naar `report.open-aec.com`

---

## Sessie — 28 maart (sessie 1)

### CR-K Security Fixes (4 van 6 resterende kritieke items)
- **CR-K6:** Nextcloud credentials lazy loading — `_get_nextcloud_*()` functies i.p.v. module-level constanten (8 tests)
- **CR-K2:** JWT default secret enforcement — `enforce_jwt_secret()` in FastAPI `lifespan` startup, productie → RuntimeError (3 tests)
- **CR-K5:** SQL identifier quoting — `quote_identifier()` helper met regex validatie, 4 locaties geupdate (11 tests)
- **CR-K3:** Brand session cleanup — `cleanup_stale_sessions()` verwijdert sessies >24u bij startup (8 tests)
- **CR-K4:** False positive — SVG icons zijn hardcoded constanten, geen XSS-vector
- **Totaal:** 30 nieuwe tests, 1214 passed, 50 skipped, 0 failures

---

## Sessie — 27 maart

### Flow Layout Auto Page-Break bij Overflow
- **Probleem:** Dynamische velden die veel wrappen duwden content zones voorbij de footer grens (260mm), tekst viel over voettekst heen
- **Oplossing:** `_paginate_flow_zones()` — splitst overflow zones automatisch naar vervolg-pagina's
- **Mechanisme:** Zones die na shifting y >= `flow_footer_y_mm` hebben → nieuwe pagina, herpositionering vanaf `flow_content_start_y_mm` (default 32mm), footer zones herhaald op elke pagina
- **Config:** `flow_content_start_y_mm: float` veld toegevoegd aan PageType
- **Engine:** Flow layout pagina's worden als chunks behandeld (zelfde patroon als tabel-paginering), inclusief correcte paginanummering
- **Tests:** 26 tests in `test_flow_layout.py` (13 bestaand + 13 nieuw)
- **Deployed:** `2a413a8` naar `report.open-aec.com`

### Openstaand uit vorige sessies
- [ ] Frontend: field groups UI testen na deploy
- [ ] PDOK luchtfoto: 2025_orthoHR layer geconfigureerd (service was down)

---

## Vorige Sessie — 26 maart

### Flow Layout voor Template Engine Text Zones
- `_apply_flow_layout()` pre-processing — berekent extra ruimte door text wrapping en verschuift onderliggende zones automatisch
- PageType config: `flow_layout: bool` + `flow_footer_y_mm: float`
- 4 page_types geactiveerd: voorziening_object, bic_rapport_details, herstelwerkzaamheden, locatie

---

## Sessie — 24 maart

### BIC Rapport: Field Groups, Layout, PDOK Kaarten
- **Field groups:** `_extract_field_groups()` scant page_type YAML's → `FieldGroupForm` component in sidebar (25 groepen)
- **BIC Template:** 17 pagina's compleet (5 nieuwe page_types), formeel schema `schemas/bic_rapport.schema.json`, voorbeeld JSON (114/125 velden)
- **Text wrapping:** `TextZone.max_width_mm` + `_wrap_text()`, 87 text_zones voorzien
- **PDOK kaarten:** `/api/pdok/map` + `/api/pdok/services` endpoints, image zones met lat/lon → automatisch kaart
- **Layout fixes:** rechterkolom verschoven, tabel origin_y gecorrigeerd, paginanummers consistent, TOC paginanummers rechts

---

## Deployment

| Omgeving | URL | Status |
|----------|-----|--------|
| Productie | https://report.open-aec.com | ✅ Online |
| API Health | https://report.open-aec.com/api/health | ✅ OK (v0.1.0) |
| Deploy script | `deploy.sh` | ✅ Git pull → docker build → deploy → health check |

---

## Engines

| Engine | Endpoint | Status | Gebruik |
|--------|----------|--------|---------|
| V1 — `Report.from_dict()` | `/api/generate` | ✅ Productie | Legacy, OpenAEC content-block rapporten |
| V2 — `ReportGeneratorV2` | `/api/generate/v2` | ✅ Productie | OpenAEC rapporten (renderer_v2) |
| V3 — `TemplateEngine` | `/api/generate/template` | ✅ Lokaal | Customer BIC (YAML page_types) |

---

## Tenants

| Tenant | Templates | Engine | Status |
|--------|-----------|--------|--------|
| `default` | structural, daylight, building_code | V1/V2 | ✅ Productie |
| `openaec_v2` | (kopie cooperatie in V3 formaat) | V3 | ⏳ Experimenteel |
| `customer` | bic_factuur, bic_rapport | V3 | ✅ Lokaal, deploy nodig |
| `openaec_foundation` | (V3 formaat) | V3 | ⏳ Experimenteel |

---

## Rust Implementatie

| Phase | Status | Tests |
|-------|--------|-------|
| Phase 0 — Schema Types | ✅ Compleet | 40 |
| Phase 1 — openaec-layout | ✅ Compleet | 11 |
| Phase 2 — Python ports | ✅ Compleet | 102 |
| Phase 3 — Rendering pipeline | ✅ Compleet | incl. in P2 |
| Phase 4 — Server + CLI | ✅ Compleet (deploy wacht) | 2 |
| Phase 5 — openaec-engine (V3) | ✅ Compleet | 28 |
| Phase 6 — Server module split + CORS | ✅ Compleet | 0 (integration) |
| **Totaal** | **197 tests** | **~9.000 LOC** |

---

## Desktop App — Tauri v2

- Scaffold compleet, GitHub Actions 4-platform build, Release v0.2.0-alpha (draft)
- Open: Authentik redirect URI, OA logo, code signing, auto-updater

---

## Frontend Chrome (19-20 maart)

TitleBar, Ribbon, Backstage, StatusBar, Modal, SettingsDialog, FeedbackDialog, ShortcutHelp — allemaal ✅
Theme systeem (~80 CSS vars, light + openaec), i18n (5 namespaces, NL + EN), SSO (Authentik)
