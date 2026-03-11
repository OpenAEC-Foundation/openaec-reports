# STATUS — openaec-reports

> Laatst bijgewerkt: 2026-03-11 (sessie: T9 font embedding fix)

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
