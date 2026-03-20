# OpenAEC Report Generator — `openaec-reports`

Modulaire Python library voor het genereren van professionele A4/A3 engineering rapporten.

---

## Quick Start

```bash
# Installeer
pip install -e ".[dev,brand-tools]"

# Tests draaien
python -m pytest tests/ -v

# API starten
openaec-report serve --port 8000 --reload

# Rapport genereren
openaec-report generate --template structural --data schemas/example_structural.json --output output/test.pdf
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
Layer 1: LIBRARY (openaec-reports)         ← ACTIEF
         Direct import in Python. Voor pyRevit, CLI, scripts.

Layer 2: API SERVER (openaec-reports-api)  ← ACTIEF (FastAPI in api.py)
         JSON in → PDF uit. 6 endpoints operationeel.

Layer 3: FRONTEND (openaec-reports-ui)     ← MONOREPO (frontend/)
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
openaec-reports/            # Monorepo
├── frontend/               # React/TypeScript UI (Vite, Tailwind, Zustand)
│   ├── src/components/     # Block editors, forms, layout
│   ├── src/stores/         # Zustand state management
│   └── src/services/       # API client
├── src/openaec_reports/         # Python library
│   ├── core/               # Engine, document, styles, brand, stationery, TOC, tenant, renderer_v2
│   ├── components/         # Calculation, check, table, image, map
│   ├── tools/              # Brand analyzer, stationery extractor, brand builder
│   ├── utils/              # Logo prep, fonts
│   ├── data/               # Adapters: JSON, Kadaster
│   ├── api.py              # FastAPI endpoints + StaticFiles (SPA serving)
│   ├── cli.py              # CLI: analyze-brand, build-brand, serve
│   └── assets/             # GENERIEKE defaults (blank.yaml, default brand)
├── tenants/                # Klantspecifieke assets (BUITEN package)
│   └── default/
│       ├── templates/      # Rapport templates (YAML)
│       ├── brand.yaml      # Brand configuratie
│       ├── stationery/     # PDF/PNG achtergronden
│       ├── logos/          # Logo's (SVG, PNG)
│       └── fonts/          # Inter fonts (TTF, OTF)
├── rust/                   # Rust implementatie (parallel aan Python)
│   ├── Cargo.toml          # Workspace: 4 crates
│   └── crates/
│       ├── openaec-core/   # Kernlibrary (schema, brand, tenant, fonts, renderer)
│       ├── openaec-server/  # Axum API server (drop-in voor FastAPI)
│       ├── openaec-cli/    # CLI tool
│       └── openaec-ffi/    # C ABI wrapper → DLL/so/dylib
├── schemas/                # JSON Schema — contract tussen library, API en frontend
└── Dockerfile              # Multi-stage: node build + python runtime
```

**Kernprincipe:** Data-interface is altijd JSON. Rendering is verwisselbaar.

### Tenant-scheiding

De library is multi-tenant: klantspecifieke assets (templates, brand, stationery, logo's, fonts) staan BUITEN het package. De engine is generiek, de look & feel per tenant configureerbaar.

```bash
# Eén environment variable bepaalt de tenant:
export OPENAEC_TENANT_DIR=tenants/default

# Fallback-chain: tenant → package defaults
# Zonder OPENAEC_TENANT_DIR werkt alles met generieke defaults
```

Kernclasses:
- **`TenantConfig`** (`core/tenant.py`): Centraliseert asset-paden met fallback
- **`TemplateLoader`**: Accepteert `templates_dirs` (merged lijst, tenant eerst)
- **`BrandLoader`**: Accepteert `tenant_config` parameter

---

## Status

Zie **`STATUS.md`** voor de volledige module-status en test coverage.
Zie **`TODO.md`** voor openstaande taken en prioriteiten.

**Samenvatting:** Monorepo (frontend + backend), library core compleet, API operationeel, tenant-scheiding geïmplementeerd, 575+ tests.

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
| `bullet_list` | renderer_v2 bullet list | ✅ | ✅ Werkend |
| `heading_2` | renderer_v2 subkop | ✅ | ✅ Werkend |
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
| `src/openaec_reports/core/engine.py` | ReportLab wrapper, PDF assembly, from_json(), from_dict() |
| `src/openaec_reports/core/renderer_v2.py` | **PyMuPDF renderer — pixel-perfect PDF met YAML templates** |
| `src/openaec_reports/core/block_registry.py` | Block factory registry, create_block(), resolve_image_source() |
| `src/openaec_reports/core/document.py` | Document class (A4/A3, margins) |
| `src/openaec_reports/core/styles.py` | Huisstijl: fonts, kleuren, spacing |
| `src/openaec_reports/core/fonts.py` | Inter font registratie + Helvetica fallback |
| `src/openaec_reports/core/toc.py` | Inhoudsopgave generator |
| `src/openaec_reports/core/special_pages.py` | Cover, colofon, backcover, appendix divider |
| `src/openaec_reports/core/tenant.py` | **TenantConfig — multi-tenant asset-paden** |
| `src/openaec_reports/core/brand.py` | Brand systeem (YAML → BrandConfig) |
| `src/openaec_reports/core/brand_renderer.py` | Brand rendering (header/footer via stationery) |
| `src/openaec_reports/core/stationery.py` | Stationery PDF/PNG embedding |
| `src/openaec_reports/core/page_templates.py` | PageTemplate callbacks (stationery-first) |
| `src/openaec_reports/api.py` | FastAPI endpoints + StaticFiles mount (SPA serving) |
| `frontend/src/` | React/TypeScript UI (editor, blocks, forms) |
| `frontend/src/stores/reportStore.ts` | Zustand rapport state management |
| `frontend/src/utils/conversion.ts` | Store → API JSON conversie |
| `Dockerfile` | Multi-stage build (node + python) |
| `STATUS.md` | Module status + test coverage |
| `TODO.md` | Openstaande taken + prioriteiten |

---

## Conventies

1. **Code:** Python, type hints, docstrings (Google style)
2. **Eenheden:** mm voor afmetingen (ReportLab werkt intern in points, conversie in engine)
3. **Naming:** snake_case voor functies/variabelen, PascalCase voor classes
4. **Templates:** YAML bestanden in `src/openaec_reports/assets/templates/`
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
- **Inter fonts:** Plaats TTF/OTF bestanden in de tenant fonts/ directory (of `src/openaec_reports/assets/fonts/` als fallback) om OpenAEC huisstijl fonts te activeren. Zonder Inter valt de library automatisch terug op Helvetica. Verwachte bestanden: `Inter-Bold.ttf`, `Inter-Regular.ttf`, `Inter-Medium.ttf`, `Inter-Italic.ttf`
- **Multi-tenant:** Zet `OPENAEC_TENANT_DIR` om klantspecifieke assets te laden. Zonder env var worden package defaults gebruikt (backward compatible)
- **Brand kleuren:** primary=#40124A (paars), secondary=#38BDA0 (turquoise), text=#45243D. Moeten consistent zijn in `styles.py`, `default.yaml`, en `default.yaml`

---

## Orchestrator

Bij sessie START → lees:
- `X:\10_OpenAEC_bouwkunde\50_Claude-Code-Projects\lessons_learned_global.md`
- `C:\Users\JochemK\.claude\orchestrator\sessions\report-generator_latest.md` (indien aanwezig)

Bij sessie EINDE → schrijf update naar:
`C:\Users\JochemK\.claude\orchestrator\sessions\report-generator_latest.md`

**Context:** `C:\Users\JochemK\.claude\orchestrator\context\report.md`
**Registry:** `C:\Users\JochemK\.claude\orchestrator\project-registry.json`
