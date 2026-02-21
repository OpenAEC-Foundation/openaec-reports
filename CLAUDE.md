# OpenAEC Report Generator — `bm-reports`

Modulaire Python library voor het genereren van professionele A4/A3 engineering rapporten in OpenAEC huisstijl.

---

## Quick Start

```bash
# Installeer
pip install -e ".[dev,brand-tools]"

# Tests draaien
python -m pytest tests/ -v

# API starten
bm-report serve --port 8000 --reload

# Rapport genereren
bm-report generate --template structural --data schemas/example_structural.json --output output/test.pdf
```

---

## Doel

Een herbruikbare, configureerbare PDF report generator die:
- Professionele rapporten genereert (constructie, daglicht, bouwbesluit, etc.)
- Integreert met Revit via pyRevit en JSON exchange
- Later inzetbaar is in eigen OpenAEC software
- Modulair opgebouwd is met YAML-configureerbare templates

---

## Platformvisie (3 lagen)

```
Layer 1: LIBRARY (bm-reports)         ← ACTIEF
         Direct import in Python. Voor pyRevit, CLI, scripts.

Layer 2: API SERVER (bm-reports-api)  ← ACTIEF (FastAPI in api.py)
         JSON in → PDF uit. 6 endpoints operationeel.

Layer 3: FRONTEND (bm-reports-ui)     ← APART PROJECT
         Web UI. Template picker, sectie-editor, preview.
```

### Architectuurregels

1. **Alles wat Report() kan, moet ook via JSON kunnen.** De `from_json()` methode moet COMPLEET zijn — niet alleen metadata maar ook secties met alle content block types. Het JSON schema in `schemas/report.schema.json` is het contract.
2. **Assets via pad OF bytes.** ImageBlock en andere afbeelding-componenten moeten werken met bestandspad (library gebruik), URL, EN base64 data (API gebruik). Zie `image_source` in het JSON schema.
3. **Build blijft synchronous.** De API zal `build()` in een worker draaien. Geen async in de library.
4. **Geen hardcoded paden.** Assets/templates altijd relatief aan het package of configureerbaar.

---

## Tech Stack

- **Python 3.10+** (compatibel met pyRevit CPython engine)
- **ReportLab** (BSD) — PDF engine + Platypus layout
- **FastAPI** + **uvicorn** — API server
- **svglib** (BSD) — SVG naar ReportLab conversie
- **PyYAML** — Template configuratie
- **Pillow** — Image processing
- **requests** — PDOK/Kadaster API
- **pdfrw** — Stationery PDF embedding
- **PyMuPDF** (optioneel) — Brand tools (PDF text stripping)

---

## Architectuur

```
src/bm_reports/
├── core/         # Engine, document, page templates, styles, brand, stationery, TOC, tenant
├── components/   # Calculation, check, table, image, map
├── tools/        # Brand analyzer, stationery extractor, brand builder
├── utils/        # Logo prep, fonts
├── data/         # Adapters: JSON, Kadaster
├── api.py        # FastAPI endpoints
├── cli.py        # CLI: analyze-brand, build-brand, serve
└── assets/       # GENERIEKE defaults (blank.yaml, default brand)

tenants/          # Klantspecifieke assets (BUITEN package)
└── default/
    ├── templates/    # Rapport templates (YAML)
    ├── brand.yaml    # Brand configuratie
    ├── stationery/   # PDF/PNG achtergronden
    ├── logos/        # Logo's (SVG, PNG)
    └── fonts/        # Inter fonts (TTF, OTF)

schemas/          # JSON Schema — contract tussen library, API en frontend
```

**Kernprincipe:** Data-interface is altijd JSON. Rendering is verwisselbaar.

### Tenant-scheiding

De library is multi-tenant: klantspecifieke assets (templates, brand, stationery, logo's, fonts) staan BUITEN het package. De engine is generiek, de look & feel per tenant configureerbaar.

```bash
# Eén environment variable bepaalt de tenant:
export BM_TENANT_DIR=tenants/default

# Fallback-chain: tenant → package defaults
# Zonder BM_TENANT_DIR werkt alles met generieke defaults
```

Kernclasses:
- **`TenantConfig`** (`core/tenant.py`): Centraliseert asset-paden met fallback
- **`TemplateLoader`**: Accepteert `templates_dirs` (merged lijst, tenant eerst)
- **`BrandLoader`**: Accepteert `tenant_config` parameter

---

## Status

Zie **`STATUS.md`** voor de volledige module-status en test coverage.
Zie **`TODO.md`** voor openstaande taken en prioriteiten.

**Samenvatting:** Library core compleet, API operationeel, tenant-scheiding geimplementeerd, 589 tests.

---

## JSON Schema (KRITISCH)

Het bestand `schemas/report.schema.json` definieert het volledige datamodel voor een rapport. Dit is het **single source of truth** voor:
- Welke content block types bestaan (paragraph, calculation, check, table, image, map, spacer, page_break)
- Hoe secties gestructureerd zijn
- Hoe afbeeldingen aangeleverd worden (pad, URL, of base64)
- Cover, colofon, TOC, backcover configuratie

**Bij elke nieuwe feature:** check eerst of het JSON schema het ondersteunt. Zo niet, update het schema EERST, bouw dan de implementatie.

### Content Block Types (uit schema)

| Type | Class | Registry | Rendering |
|------|-------|----------|-----------|
| `paragraph` | Paragraph (ReportLab) | ✅ | ✅ Werkend |
| `calculation` | CalculationBlock | ✅ | ✅ Werkend |
| `check` | CheckBlock | ✅ | ✅ Werkend |
| `table` | TableBlock | ✅ | ✅ Werkend |
| `image` | ImageBlock | ✅ | ✅ Werkend |
| `map` | KadasterMap | ✅ | ✅ Werkend (PDOK WMS) |
| `spacer` | Spacer (ReportLab) | ✅ | ✅ Triviaal |
| `page_break` | PageBreak (ReportLab) | ✅ | ✅ Triviaal |
| `raw_flowable` | ReportLab Flowable | ✅ | ✅ Library-only |

### from_json() / from_dict() — COMPLEET

```python
# Publieke API:
report = Report.from_json("rapport.json")           # Bestand → Report
report = Report.from_dict(data, base_dir=Path(...))  # Dict → Report (API use case)

# Block registry (core/block_registry.py):
flowable = create_block({"type": "paragraph", "text": "..."})
path = resolve_image_source(src, base_dir=...)  # pad, base64, of URL
```

**Veldmappings** (schema → component):
- `required_value` → CheckBlock `required`
- `calculated_value` → CheckBlock `calculated`
- `column_widths` → TableBlock `col_widths_mm`
- `alignment` → ImageBlock `align`
- `center.lat/lon` → KadasterMap `latitude/longitude`

---

## Belangrijke Bestanden

| Bestand | Doel |
|---------|------|
| `schemas/report.schema.json` | **JSON Schema — het contract** |
| `schemas/example_structural.json` | Volledig voorbeeld rapport als JSON |
| `src/bm_reports/core/engine.py` | ReportLab wrapper, PDF assembly, from_json(), from_dict() |
| `src/bm_reports/core/block_registry.py` | Block factory registry, create_block(), resolve_image_source() |
| `src/bm_reports/core/document.py` | Document class (A4/A3, margins) |
| `src/bm_reports/core/styles.py` | Huisstijl: fonts, kleuren, spacing |
| `src/bm_reports/core/fonts.py` | Inter font registratie + Helvetica fallback |
| `src/bm_reports/core/toc.py` | Inhoudsopgave generator |
| `src/bm_reports/core/special_pages.py` | Cover, colofon, backcover, appendix divider |
| `src/bm_reports/core/tenant.py` | **TenantConfig — multi-tenant asset-paden** |
| `src/bm_reports/core/brand.py` | Brand systeem (YAML → BrandConfig) |
| `src/bm_reports/core/brand_renderer.py` | Brand rendering (header/footer via stationery) |
| `src/bm_reports/core/stationery.py` | Stationery PDF/PNG embedding |
| `src/bm_reports/core/page_templates.py` | PageTemplate callbacks (stationery-first) |
| `src/bm_reports/api.py` | FastAPI endpoints (/generate, /validate, etc.) |
| `src/bm_reports/assets/brands/` | YAML brand configuraties (default, default) |
| `src/bm_reports/assets/templates/` | YAML rapport definities |
| `src/bm_reports/assets/logos/` | Logo's (PNG, SVG) |
| `huisstijl/` | Bronmateriaal: logo's, referentie-PDF's, analyse |
| `STATUS.md` | Module status + test coverage |
| `TODO.md` | Openstaande taken + prioriteiten |

---

## Conventies

1. **Code:** Python, type hints, docstrings (Google style)
2. **Eenheden:** mm voor afmetingen (ReportLab werkt intern in points, conversie in engine)
3. **Naming:** snake_case voor functies/variabelen, PascalCase voor classes
4. **Templates:** YAML bestanden in `src/bm_reports/assets/templates/`
5. **Assets:** SVG voor vectorgraphics, PNG voor rasterafbeeldingen
6. **Tests:** pytest, een testfile per module
7. **Schema first:** Nieuwe features → update JSON schema → implementeer

---

## Notities

- ReportLab 1 point = 1/72 inch. Conversie: mm x 2.8346 = points
- PDOK WMS is gratis, geen API key nodig
- pyRevit CPython engine = Python 3.8+, geen IronPython beperkingen
- JSON exchange is de primaire data-interface (niet Revit-specifiek)
- ERPNext projectdata via bestaande MCP server (niet in deze library)
- Logo bronbestanden staan in `huisstijl/logo's/RGB/` (SVG, PNG, wit variant)
- Huisstijl referentie-PDF's in `huisstijl/` — gebruik voor kleur/font extractie
- **Inter fonts:** Plaats TTF/OTF bestanden in de tenant fonts/ directory (of `src/bm_reports/assets/fonts/` als fallback) om OpenAEC huisstijl fonts te activeren. Zonder Inter valt de library automatisch terug op Helvetica. Verwachte bestanden: `Inter-Bold.ttf`, `Inter-Regular.ttf`, `Inter-Medium.ttf`, `Inter-Italic.ttf`
- **Multi-tenant:** Zet `BM_TENANT_DIR` om klantspecifieke assets te laden. Zonder env var worden package defaults gebruikt (backward compatible)
- **Brand kleuren:** primary=#40124A (paars), secondary=#38BDA0 (turquoise), text=#45243D. Moeten consistent zijn in `styles.py`, `default.yaml`, en `default.yaml`
