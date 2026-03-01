# STATUS — bm-reports

> Laatst bijgewerkt: 2026-03-01 (sessie: pixel fixes + admin cleanup)

---

## Deployment

| Omgeving | URL | Status |
|----------|-----|--------|
| Productie | https://report.3bm.co.nl | ⚠️ Online, wacht op rebuild (`docker build --no-cache`) |
| API Health | https://report.3bm.co.nl/api/health | ✅ OK (v0.1.0) |
| `/api/generate/v2` | POST | ✅ Werkt (3BM rapporten) |
| `/api/generate/template` | POST | ✅ Code gefixt, wacht op deploy |

---

## Engines

| Engine | Endpoint | Lokaal | Productie | Gebruik |
|--------|----------|--------|-----------|---------|
| V1 — `Report.from_dict()` | `/api/generate` | ✅ | ✅ | Legacy |
| V2 — `ReportGeneratorV2` | `/api/generate/v2` | ✅ | ✅ | 3BM rapporten |
| V3 — `TemplateEngine` | `/api/generate/template` | ✅ | ⏳ Wacht op deploy | Symitech BIC |

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

### Symitech Tenant Assets

| Asset | Status | Pad |
|-------|--------|-----|
| `brand.yaml` (Arial fonts, font_files) | ✅ | `tenants/symitech/brand.yaml` |
| Stationery PDFs (5) | ✅ | `tenants/symitech/stationery/` |
| Page type YAMLs (6) | ✅ | `tenants/symitech/page_types/` |
| Template YAML | ✅ | `tenants/symitech/templates/bic_factuur.yaml` |
| Arial font files (4 TTF) | ✅ | `tenants/symitech/fonts/` |
| Placeholder aerial photo | ✅ | `tenants/symitech/assets/placeholder_aerial.png` |
| Test data | ✅ | `schemas/test_336_bic_factuur.json` |

---

## Frontend

| Feature | Lokaal | Productie |
|---------|--------|-----------|
| Block editors (paragraph, table, image, calc, check, map) | ✅ | ✅ |
| Template selector + scaffold loader | ✅ | ✅ |
| Split view + live preview | ✅ | ✅ |
| JSON import/export | ✅ | ✅ |
| Smart endpoint routing (V2 vs TemplateEngine) | ✅ | ⏳ Wacht op `--no-cache` rebuild |
| Admin: Asset replace button | ✅ | ⏳ Wacht op deploy |
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

---

## Cleanup Status (28 feb)

- [x] Deprecated `modules/symitech/` verwijderd
- [x] Deprecated `modules/yaml_module.py` verwijderd
- [x] Deprecated `tenants/symitech/modules/` verwijderd
- [x] Prompt bestanden gearchiveerd naar `_archive/prompts/`
- [x] pytest cache opgeruimd

---

## Fixes (1 maart)

### Pixel precision fixes — 6 issues (f3b8228)
- **Issue 1 — Arial fonts:** Per-tenant font registratie via `font_files` mapping in brand.yaml. Nieuwe `register_tenant_fonts()` in `fonts.py`. Symitech brand gewijzigd van Helvetica → Arial.
- **Issue 2 — Page numbering:** "Pagina X van Y" format. Cover page excluded van content count. `_BuildContext` uitgebreid met `content_page_count` en `page_number_offset`.
- **Issue 3 — Y-offset correction:** Font ascent correctie in `_draw_text_zones()`. PyMuPDF bbox-top (referentie) vs ReportLab baseline offset = `pdfmetrics.getAscent()`. Delta gereduceerd van ~11pt naar <0.7pt.
- **Issue 4 — Image zones:** Nieuwe `ImageZone` dataclass in `template_config.py`. `_draw_image_zones()` in template engine. Locatie pagina configuratie met placeholder aerial photo.
- **Issue 5 — Achterblad text:** Text zones toegevoegd in `achterblad.yaml`: "Deze pagina is [met opzet] leeg gelaten", footer, paginanummer.
- **Issue 6 — BIC controles fontsize:** Table body fontsize → 10pt in `bic_controles.yaml`.

### Admin panel cleanup (ab93b13)
- **Replace button:** "Vervangen" knop per asset bestand in BrandManagement. Upload met filename rename via `new File([file], replaceTarget)`.
- **BrandWizard verwijderd:** Standalone BrandWizard (blauw, 3-stap) volledig verwijderd — 8 bestanden. BrandExtractWizard (paars, 4-stap) blijft als enige brand creation flow.
- **AdminTab type:** `"brand-wizard"` verwijderd uit union type.

### Tenant resolution in `/api/generate/template` — GEFIXT (cfaa808)
- **FIX-1:** Nieuwe `_resolve_tenant_and_template()` helper leidt tenant af uit template naam prefix (bijv. `symitech_bic_factuur` → tenant=`symitech`). Scant bestaande tenant directories, sorted by name length (langste eerst) om ambiguïteit te voorkomen. Fallback: `data["brand"]` → `user.tenant` → `"symitech"`.
- **FIX-2:** `_resolve_tenants_dir()` herschreven: checkt `BM_TENANTS_ROOT` env var eerst, dan parent van `BM_TENANT_DIR` (met brand.yaml verificatie), dan source tree, dan package-relatief. Dockerfile had `BM_TENANTS_ROOT=/app/tenants` al.
- **FIX-3:** Frontend smart routing code was al correct in broncode. Probleem was Docker cache → vereist `docker build --no-cache` bij volgende deploy.
- **Tests:** 888 passed, 0 failures. E2E PDF generatie OK.
