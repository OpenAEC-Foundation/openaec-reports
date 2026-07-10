# STATUS — openaec-reports

**Laatste update:** 2026-07-10 | **Productie:** [`report.open-aec.com`](https://report.open-aec.com)
**Archief:** [`archief/2026-Q1-voltooid.md`](archief/2026-Q1-voltooid.md) | **Git history:** `git log --oneline -30`

---

## Huidige staat

- **Tests:** 1358 collected (1256 passed, 92 skipped, 10 pre-existing failures — zie git-history) — Python backend
- **Rust tests:** 197 totaal (9 phases compleet, deploy van Rust server wacht op subdomein `report-rs.open-aec.com`)
- **Productie:** multi-tenant via bind-mount `/opt/openaec/reports-tenants/`, SSO-only via Authentik
- **Engines live:** V1 (`/api/generate`), V2 (`/api/generate/v2`), V3 (`/api/generate/template`)
- **Security:** alle 6 CR-K + alle 5 SEC-K + T-FIX gefixt (Q1) — 3 SEC-H open, 8 SEC-M open, zie `TODO.md`
- **Cloud integratie:** project container model (`project.wefc`) live in Python `cloud.py` en Rust server (3 routes)

---

## 🎯 Actieve sporen

| Spoor | Status | Volgende stap |
|---|---|---|
| **S2 Sanering template** | spec open | Referentie-PDF voor pixel-exacte coördinaten |
| **T7 Revit Adapter** | stub (4 methoden) | `get_project_info` via pyRevit |
| **Phase 2 Auth (Rust)** | niet begonnen | User struct, JWT, bcrypt, api_keys |
| **Phase 3 Rust endpoints** | niet begonnen | `/api/upload` + PDOK proxy |
| **Rust renderer feature parity** | parity gap vs Python `renderer_v2.py` | Heading-nummering + TOC counter state |
| **Authentik Unified SSO migratie** | plan klaar, blokkeert op auth-fix | Fase 5 Reports migratie (dependencies.py refactor, JWT exit) |
| **Desktop Tauri v2** | v0.2.0-alpha draft | D4 Authentik redirect URI, D5 OA logo, D6-D9 signing/updater/dialogs |
| **Renderer brand-substitutie** | Fase 1-3 klaar | RV-3 (SegoeUI-Semibold.ttf), RV-5 (covervarianten b/c/d), RV-6 (KBA-tenant deploy naar server) — zie `TODO.md` |

---

## 🎨 Renderer-refactor (`renderer_v2.py`) — brand-lekkage

**Probleem:** tenant-templates bevatten hardcoded 3BM-huisstijlkleuren; een tenant die van 3BM gekopieerd wordt rendert daardoor zonder fout in 3BM-paars/turquoise. `$colors`/`$fonts`-substitutie bestond alleen in het engine.Report-pad (`brand_renderer`/`page_templates`), niet in `ReportGeneratorV2` dat het live v2-endpoint bedient.

- **Fase 1 (klaar):** `tenants/kba/brand.yaml` wordt afgeleid uit de canonieke `kba-brand.json` via `scripts/build_tenant_brand.py` (`--check` als CI-guard tegen handmatige bewerking).
- **Fase 2 (klaar):** resolver in `src/openaec_reports/core/refs.py`, toegepast bij het laden van de template-YAML in `TemplateSet`. Onbekende sleutel faalt luid (tenant + bestand + sleutel in de melding), geen stille fallback. Regressie-vangrail: `scripts/render_baseline.py` + `scripts/diff_baseline.py` — 3BM 8/8 pagina's pixel-identiek vastgelegd (tolerance=0 px), `tests/baseline/manifest.json` + PNG's in git.
- **Fase 3 (klaar):** `src/openaec_reports/core/static_elements.py` — generieke primitive-renderer (`rect`/`rounded_rect`/`line`/`polygon`/`image`/`text`) die `pages.<type>.static_elements` uit tenant-config tekent. Kleuren via `_style_color()`: template-waarde, dan semantische `brand.colors`, anders `ValueError` — geen stille 3BM-fallback meer (RV-1 opgelost). KBA-cover (variant a) is hiermee volledig data-gedreven: duotone-fotoband, accentstreep, metagrid, footerbalk, kicker met `char_space`-letterspacing én (2026-07-10) `transform: upper` — report-data blijft leesbare spreektaal ("Constructief advies"), de opmaakregel staat in `tenants/kba/brand.base.yaml`. `tests/test_brand_leakage.py` borgt dat de 3BM-lekkage niet terugkomt (RV-2 opgelost).
- **Restpunten (RV-3, RV-5, RV-6):** `SegoeUI-Semibold.ttf` ontbreekt in `tenants/kba/fonts/` (font-weight 600 valt terug op Bold/Regular) — user moet aanleveren. Covervarianten b (full-bleed)/c (venster)/d (45°-snede) zijn nog niet uitgewerkt — de generieke primitieven maken ze mogelijk. `tenants/kba/` (nieuwe brand.yaml/brand.base.yaml) is nog niet gedeployed naar `/opt/openaec/reports-tenants/kba/` op productie.
- **Bekende bug (buiten scope fase 1-3):** `openaec_foundation`-tenant crasht op content-secties — `KeyError: 'x'` in `heading_1()` (`renderer_v2.py:1317`), content-secties gebruiken een afwijkend `content_styles`-schema. Vastgelegd in `tests/baseline/FAILURES.md`.
- **Nieuw in de canonieke bron:** `rood: #A6342B` toegevoegd aan `kba-brand.json` als fail-kleur voor unity-checks (user-besluit, 2026-07-10).

---

## 📐 Engines

| Engine | Endpoint | Gebruik |
|---|---|---|
| V1 `Report.from_dict()` | `/api/generate` | Legacy flow-based content-block rapporten |
| V2 `ReportGeneratorV2` | `/api/generate/v2` | Pixel-perfect via `renderer_v2` (Python) |
| V3 `TemplateEngine` | `/api/generate/template` | YAML page_types, fixed-page layouts |
| V3-Rust `openaec_engine::Engine` | (zelfde endpoint, alternatieve deploy) | Pure Rust V3 — 28 tests, wacht op `report-rs.open-aec.com` |

---

## 🏢 Tenants

Public repo bevat alleen `tenants/default/` placeholder. Private tenant-directories (brand, templates, stationery, fonts) via host bind-mount op productie, niet in git.

| Tenant | Locatie | Engines | Status |
|---|---|---|---|
| `default` | `tenants/default/` (public) | V1/V2/V3 | Repo MVP, OFL fonts |
| Private tenants | bind-mount op Hetzner | V1/V2/V3 | Productie |

Tenant-model: user.tenant wordt **admin-managed** (niet uit OIDC). SSO-users krijgen initieel `tenant=""` en admin wijst toe via admin panel. Authentik gebruikt `sub_mode=hashed_user_id` voor unieke user-identificatie. Brand-override in generate endpoints wordt gevalideerd tegen `user.tenant`.

---

## 🔧 Deployment

| Omgeving | URL | Status |
|---|---|---|
| Productie Python | [`report.open-aec.com`](https://report.open-aec.com) | ✅ Online |
| API Health | `/api/health` | ✅ OK |
| Productie Rust | `report-rs.open-aec.com` | ⏳ Wacht op subdomein (R4.4) |

**Deploy pipeline:** `deploy.sh` — `git pull` → `docker build --no-cache` → deploy → health check. GitHub Actions voor lint/test/build/deploy + release-desktop (4-platform matrix).

---

## 🦀 Rust implementatie — samenvatting

| Phase | Status | Tests |
|---|---|---|
| 0 Setup + Schema Types | ✅ | 40 |
| 1 openaec-layout (eigen ReportLab) | ✅ | 11 |
| 2 Python libs porten | ✅ | 102 |
| 3 Rendering pipeline | ✅ | incl. P2 |
| 4 Server + CLI | ✅ | 2 (deploy open) |
| 5 openaec-engine V3 | ✅ | 28 |
| 6 Server module split + CORS | ✅ | integration |
| **Totaal** | | **197 tests / ~9.000 LOC** |

Phase-detail in [`archief/2026-Q1-voltooid.md`](archief/2026-Q1-voltooid.md) §"Rust implementatie".

---

## 🖥️ Frontend + Desktop

**Frontend Chrome (19-20 maart):** TitleBar, Ribbon, Backstage, StatusBar, Modal, SettingsDialog, FeedbackDialog, ShortcutHelp ✅. Theme systeem (~80 CSS vars, light + openaec), i18n (5 namespaces NL+EN), SSO Authentik.

**Desktop Tauri v2:** scaffold + GitHub Actions 4-platform build + Release v0.2.0-alpha (draft) ✅. Open: Authentik redirect URI (`http://tauri.localhost/auth/callback`), OA logo vervangen, code signing, auto-updater, native file dialogs.

---

## 🔗 Integraties

- **warmteverlies → reports:** JSON resultaten als rapportinput (via `/api/generate/v2` met water-voetnoot hook sinds 10 apr)
- **pyrevit-gis2bim → reports:** Revit-knop triggert rapportgeneratie met `X-API-Key` header, key `pyrevit-rc` op user `jochem`
- **openaec-cloud crate:** reports-rs gebruikt het voor Nextcloud WebDAV opslag van gegenereerde rapporten
- **reports (Rust) → reports (Python):** delen JSON schema als contract; Rust is drop-in vervanging

---

## 📚 Archief

- [`archief/2026-Q1-voltooid.md`](archief/2026-Q1-voltooid.md) — Q1 2026 (februari + maart): Rust Phase 0-6, CR-K/SEC-K security fixes, BIC Rapport 17 pagina's, OpenAEC rebranding, T5/T6/T8, cloud migratie, Tauri v0.2.0-alpha
