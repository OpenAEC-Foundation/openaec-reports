# STATUS — openaec-reports

> Laatst bijgewerkt: 2026-03-26
> Sessie-historie ouder dan 2 sessies: zie `git log` of `git show <commit>:STATUS.md`

---

## Huidige Staat

- **1230 tests** collected (1180 passed, 50 skipped)
- **BIC Rapport:** 17 pagina's compleet, field groups, PDOK kaarten, flow layout voor tekst overlap
- **Security:** 5 kritieke + 1 hoge items gefixt, 2 hoge + 9 medium open (zie TODO.md)
- **Productie:** `report.open-aec.com` / `report.open-aec.com` — SSO-only, multi-tenant
- **Open:** deploy BIC rapport + field groups naar server, S2 Sanering template

---

## Laatste Sessie — 26 maart

### Flow Layout voor Template Engine Text Zones
- **Probleem:** Tekst overlap op pagina 4-5 van BIC rapporten wanneer waarde-velden wrappen naar meerdere regels
- **Oplossing:** `_apply_flow_layout()` pre-processing in `template_engine.py` — berekent extra ruimte door text wrapping en verschuift onderliggende zones (tekst, lijnen, afbeeldingen) automatisch
- **PageType config:** `flow_layout: bool` + `flow_footer_y_mm: float` velden toegevoegd
- **YAML:** 4 page_types geactiveerd: voorziening_object, bic_rapport_details, herstelwerkzaamheden, locatie
- **Tests:** 13 unit tests in `test_flow_layout.py`

### Openstaand uit vorige sessies
- [ ] Frontend: field groups UI testen na deploy
- [ ] PDOK luchtfoto: 2025_orthoHR layer geconfigureerd (service was down)
- [ ] Deploy naar server (SSH connection issues)

---

## Vorige Sessie — 24 maart

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
| Phase 1 — openaec-layout | ✅ Compleet | 9 |
| Phase 2 — Python ports | MVP (block_renderer) | — |
| Phase 3 — Rendering pipeline | ✅ Compleet | — |
| Phase 4 — Server + CLI | ✅ Compleet (deploy wacht) | — |
| **Totaal** | **62 tests** | **~5.500 LOC** |

---

## Desktop App — Tauri v2

- Scaffold compleet, GitHub Actions 4-platform build, Release v0.2.0-alpha (draft)
- Open: Authentik redirect URI, OA logo, code signing, auto-updater

---

## Frontend Chrome (19-20 maart)

TitleBar, Ribbon, Backstage, StatusBar, Modal, SettingsDialog, FeedbackDialog, ShortcutHelp — allemaal ✅
Theme systeem (~80 CSS vars, light + openaec), i18n (5 namespaces, NL + EN), SSO (Authentik)
