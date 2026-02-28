# TODO — bm-reports

> Prioriteit: 🔴 Hoog | 🟡 Middel | 🟢 Laag
> Laatst bijgewerkt: 2026-02-28

---

## Architectuur-besluit (2026-02-28)

**renderer_v2 brand-aware refactor is VERVALLEN.**  
Nieuwe aanpak: **Template-Driven Engine (Optie C)** — declaratieve YAML templates die
documentstructuur definiëren. Drie pagina-modes: `special`, `fixed`, `flow`.

Zie: `docs/ARCHITECTURE_PLAN_TENANT_MODULES.md`

Kern: stationery-first. Alle visuele elementen (lijnen, headers, kleur) zitten in de
stationery PDF. Engine vult alleen text zones + transparante tabellen.

---

## 🔴 T1 — Template Engine Fase 1: Fixed + Special mode

Nieuwe engine: `src/bm_reports/core/template_engine.py`

### ✅ T1.1 — Dataclasses + Parsers
- [x] `template_config.py` — TemplateConfig, PageDef, PageType, TableConfig, TextZone, ContentFrame
- [x] Parse helpers voor YAML → dataclass conversie

### ✅ T1.2 — Template Resolver
- [x] `template_resolver.py` — laadt template + page_type YAML's uit tenant dirs
- [x] Caching, fallback naar package assets

### ✅ T1.3 — Template Engine (v2 naast bestaand)
- [x] `template_engine.py` — TemplateEngine met DocTemplate (Optie C)
- [x] `_render_special()` — stationery + text zones via onPage callback
- [x] `_render_fixed()` — stationery + text zones + tabel met auto-paginering
- [x] `_render_flow()` — stationery + flowables in content frame
- [x] `resolve_bind()` — dot-notatie data binding
- [x] `format_value()` — currency_nl formatter
- [x] `_draw_text_zones()` — text zones op canvas (top-down → bottom-up)
- [x] `_draw_table()` — transparante tabel met vaste kolommen
- [x] `_paginate_table_data()` — verdeel rijen over pagina's

### ✅ T1.4 — Compilatie + imports fixen (2026-02-28)
- [x] Forward reference `_BuildContext` → al opgelost (_BuildContext staat vóór TemplateEngine)
- [x] Import paden: `brand.py` `load_from_path()` niet nodig → engine gebruikt `BrandLoader.load(name)`
- [x] `document.py`: A4.width_pt=595.3, A4.height_pt=841.9, MM_TO_PT=2.8346 ✅
- [x] `block_registry.py`: `create_block()` niet gebruikt — flow mode gebruikt directe Paragraph()
- [x] `fonts.py`: `get_font_name()` ✅ (fallback Helvetica als Gotham niet registered)
- [x] Import test: `from bm_reports.core.template_engine import TemplateEngine` ✅
- [x] Runtime verificatie: 10/10 integratiepunten gevalideerd (dataclasses, parsers, helpers, pagination, BrandLoader, StationeryRenderer)

### ✅ T1.5 — Symitech page_type YAML's (2026-02-28)
- [x] `tenants/symitech/page_types/voorblad_bic.yaml` — text zones
- [x] `tenants/symitech/page_types/locatie.yaml` — text zones
- [x] `tenants/symitech/page_types/bic_controles.yaml` — text zones + tabel
- [x] `tenants/symitech/page_types/detail_weergave.yaml` — tabel (landscape)
- [x] `tenants/symitech/page_types/objecten.yaml` — tabel (landscape)
- [x] `tenants/symitech/page_types/achterblad.yaml` — leeg (stationery only)

### ✅ T1.6 — Symitech template YAML (2026-02-28)
- [x] `tenants/symitech/templates/bic_factuur.yaml` — documentstructuur

### ✅ T1.7 — Unit tests (2026-02-28)
- [x] `test_template_config.py` — 23 tests: alle dataclasses + parse helpers
- [x] `test_template_resolver.py` — 12 tests: loading, caching, fallback, edge cases
- [x] `test_template_engine.py` — 17 tests: resolve_bind, format_value, _get_pagesize, _paginate_table_data, _BuildContext
- [x] `test_data_binding.py` — 28 tests: diep nested, arrays, mixed types, currency edge cases
- [x] Bugfix: `pageSize` → `pagesize` in template_engine.py (ReportLab API)

### ✅ T1.8 — End-to-end test Symitech BIC factuur (2026-02-28)
- [x] `test_template_e2e.py` — 3 tests: PDF generatie, page count (6 pagina's), data transformatie
- [x] Test JSON fixture → engine data transformatie
- [x] `TemplateEngine.build("bic_factuur", "symitech", data, "output/test_template_e2e.pdf")` ✅
- [x] PDF output: 6 pagina's (voorblad, locatie, bic_controles, detail, objecten, achterblad)

---

## 🔴 T2 — Stationery PDFs per page-type

Huidige Symitech stationery PDFs (5 stuks) dekken het hele document.
Nodig: **per page-type een stationery** met alle visuele elementen erop.

### T2.1 — Stationery extraheren/maken
- [ ] Referentie-PDF analyseren: welke elementen zijn vast per pagina
- [ ] Per page-type stationery PDF maken:
  - `voorblad_bic.pdf` (bestaand: cover_stationery.pdf ≈ hernoemen)
  - `locatie.pdf` (extract uit referentie, zonder dynamische tekst)
  - `bic_controles.pdf` (extract: blauwe lijnen, kolomkoppen, sectielijnen)
  - `detail_landscape.pdf` (extract: kolomkoppen, tabelstructuur)
  - `objecten_landscape.pdf` (extract: kolomkoppen, tabelstructuur)
  - `achterblad.pdf` (bestaand: backcover_stationery.pdf ≈ hernoemen)
- [ ] Optie A: split referentie-PDF, verwijder data → InDesign/Illustrator
- [ ] Optie B: vanuit bron opnieuw exporteren zonder data

### T2.2 — Text zone coördinaten extraheren
- [ ] Per page-type: exact x,y van elke text zone meten uit referentie-PDF
- [ ] Vastleggen in page_type YAML's (T1.5)

---

## 🟡 T3 — Flow mode integratie (3BM rapporten)

### T3.1 — 3BM page_type YAML's
- [ ] `tenants/3bm_cooperatie/page_types/voorblad.yaml`
- [ ] `tenants/3bm_cooperatie/page_types/colofon.yaml`
- [ ] `tenants/3bm_cooperatie/page_types/inhoud.yaml` (content_frame)
- [ ] `tenants/3bm_cooperatie/page_types/achterblad.yaml`

### T3.2 — 3BM template YAML's
- [ ] `tenants/3bm_cooperatie/templates/rapport.yaml`
- [ ] `tenants/3bm_cooperatie/templates/berekening.yaml`
- [ ] `tenants/3bm_cooperatie/templates/offerte.yaml`

### T3.3 — Flow mode engine
- [ ] `_build_flow_content()` integreren met bestaande block_registry
- [ ] Bestaande 3BM rapporten werken ongewijzigd via nieuwe engine
- [ ] Regressietest: output v1 engine vs template engine

---

## 🟡 T4 — Cleanup na validatie

- [ ] Verwijder `src/bm_reports/modules/symitech/` (4 Python modules)
- [ ] Verwijder `tenants/symitech/modules/` (4 YAML modules)  
- [ ] Verwijder `yaml_module.py` (500+ regels) — niet meer nodig voor fixed pages
- [ ] Verwijder `src/bm_reports/assets/templates/symitech_*.yaml` (verplaatst)
- [ ] API endpoint `/api/generate/v2` omschakelen naar TemplateEngine
- [ ] CLI `generate` command omschakelen naar TemplateEngine

---

## 🟡 D1 — Deploy & Infrastructure

- [x] Monorepo deployed op VPS
- [x] SSH key-based auth (thuis + kantoor)
- [x] Cockpit admin panel
- [ ] Caddyfile vereenvoudigen: enkele reverse_proxy
- [ ] fail2ban installeren
- [ ] Portainer installeren

---

## 🟢 P5 — Toekomstige Features

- [ ] Symitech rapport simpel (flow mode — zelfde als 3BM)
- [ ] Tweede brand (BBL Engineering)
- [ ] `reports/structural.py` — Constructief rapport
- [ ] RevitAdapter: Revit model data → rapport JSON
- [ ] PDF caching op basis van JSON hash
- [ ] Rate limiting per tenant

---

## 🟢 Housekeeping

- [ ] **pytest cache cleanup:** 38+ `pytest-cache-files-*` dirs verwijderen
- [ ] `lessons_learned.md` aanmaken
- [ ] Oude PROMPT_*.md bestanden archiveren
