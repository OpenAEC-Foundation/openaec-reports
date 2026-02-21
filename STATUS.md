# Backend Status — bm-reports

> Laatst bijgewerkt: 2026-02-21

## Deployment

| Component | URL | Status |
|-----------|-----|--------|
| **API (productie)** | https://report.3bm.co.nl/api/* | ✅ Live |
| **Frontend (productie)** | https://report.3bm.co.nl/ | ⏳ Monorepo klaar, deploy pending |
| **Cutlist Optimizer** | https://zaagplan.3bm.co.nl/ | ✅ Live |
| **CrowdSec IPS** | — | ✅ Monitoring |

### Infrastructuur
- **Server:** Hetzner CX22 (2 vCPU, 4GB RAM, 75GB SSD) — Ubuntu 24.04
- **IP:** 46.224.215.142
- **Reverse proxy:** Caddy 2 (auto-SSL via Let's Encrypt)
- **Container runtime:** Docker 29.2.1 + Compose v5.0.2
- **Security:** CrowdSec (Caddy log monitoring, community threat intel)
- **Repository:** https://github.com/OpenAEC-Foundation/openaec-reports

### Docker Stack (`/opt/3bm/docker-compose.yml`)
```
caddy           → Ports 80, 443 (reverse proxy + SSL)
crowdsec        → Log analysis + IP blocking
bm-reports-api  → Multi-stage: node:20-alpine (frontend build) + python:3.12-slim (runtime)
                  Frontend served as static files via FastAPI, uvicorn, 2 workers
cutlist-frontend → nginx
cutlist-backend  → Python
```

### Monorepo Structuur

```
openaec-reports/
├── frontend/       # React/TypeScript UI (Vite, Tailwind, Zustand)
├── src/bm_reports/ # Python library + FastAPI API
├── schemas/        # JSON Schema (single source of truth)
├── tenants/        # Klantspecifieke assets (buiten package)
└── Dockerfile      # Multi-stage: frontend build + python runtime
```

## Architectuur

```
src/bm_reports/
├── core/           # Engine, document, styles, brand, stationery, page templates
├── components/     # Calculation, check, table, image, map, spacer
├── tools/          # Brand analyzer, stationery extractor, brand builder
├── utils/          # Logo prep, fonts
├── assets/         # Templates (YAML), brands (YAML), logos, fonts, graphics
├── api.py          # FastAPI endpoints + StaticFiles mount (SPA serving)
├── cli.py          # CLI: analyze-brand, build-brand, serve
└── schemas/        # JSON Schema + example
```

## Modules — Status

| Module | Status | Tests | Coverage |
|--------|--------|-------|----------|
| **core/engine.py** | ✅ Compleet | ✅ test_engine.py | 94% |
| **core/document.py** | ✅ Compleet | ✅ test_core.py | 99% |
| **core/styles.py** | ✅ Compleet | ✅ test_styles.py | 100% |
| **core/brand.py** | ✅ Compleet | ✅ test_brand.py | 95% |
| **core/brand_renderer.py** | ✅ Compleet | ✅ test_brand.py | 71% |
| **core/page_templates.py** | ✅ Compleet | ✅ test_page_templates_integration.py | 89% |
| **core/stationery.py** | ✅ Compleet | ✅ test_stationery.py | 89% |
| **core/special_pages.py** | ✅ Compleet | ✅ test_special_pages.py (56 tests) | 80% |
| **core/block_registry.py** | ✅ Compleet | ✅ test_block_registry.py | 90% |
| **core/template_loader.py** | ✅ Compleet | ✅ test_templates.py + test_template_scaffold.py | 94% |
| **core/toc.py** | ✅ Compleet | ✅ via integratietests | 100% |
| **core/fonts.py** | ✅ Compleet | — | 66% |
| **core/renderer_v2.py** | ✅ Compleet | ✅ test_renderer_v2.py (52 tests) | — |
| **components/calculation.py** | ✅ Compleet | ✅ test_engine.py | 100% |
| **components/check_block.py** | ✅ Compleet | ✅ test_block_registry.py | 100% |
| **components/table_block.py** | ✅ Compleet | ✅ test_block_registry.py | 97% |
| **components/image_block.py** | ✅ Compleet | ✅ test_image_block.py (20 tests) | 79% |
| **components/map_block.py** | ✅ Compleet | ✅ test_map_block.py | 96% |
| **api.py** | ✅ Compleet | ✅ test_api.py | 88% |
| **cli.py** | ✅ Compleet | ✅ test_cli.py (14 tests) | 61% |
| **data/json_adapter.py** | ✅ Compleet | ✅ test_json_adapter.py (14 tests) | 88% |
| **data/kadaster.py** | ✅ Compleet | ✅ test_data_adapters.py | 100% |
| **data/revit_adapter.py** | ⚠️ Stub | ✅ test_data_adapters.py | 87% |
| **tools/brand_analyzer** | ✅ Compleet | ✅ test_brand_analyzer.py | 93-99% |
| **tools/stationery_extractor.py** | ✅ Compleet | ✅ test_stationery_extractor.py | 96% |
| **tools/brand_builder.py** | ✅ Compleet | ✅ test_brand_builder.py | 68% |
| **utils/logo_prep.py** | ✅ Compleet | ✅ test_logo_prep.py | 100% |
| **reports/** | ⚠️ Toekomstige stubs | — | 0% (fase 6) |

## Test Suite

```
tests/
├── test_api.py                    ✅ 18 tests
├── test_block_registry.py         ✅ 23 tests
├── test_brand.py                  ✅ 31 tests
├── test_brand_analyzer.py         ✅ 24 tests
├── test_brand_builder.py          ✅  8 tests
├── test_cli.py                    ✅ 14 tests
├── test_core.py                   ✅ 14 tests
├── test_data_adapters.py          ✅ 13 tests
├── test_engine.py                 ✅ 12 tests
├── test_from_json.py              ✅ 13 tests
├── test_image_block.py            ✅ 20 tests
├── test_json_adapter.py           ✅ 14 tests
├── test_landscape.py              ✅ 10 tests
├── test_logo_prep.py              ✅ 22 tests
├── test_map_block.py              ✅ 19 tests
├── test_page_templates_integration ✅ 18 tests
├── test_special_pages.py          ✅ 56 tests
├── test_stationery.py             ✅ 14 tests
├── test_stationery_extractor.py   ✅  8 tests
├── test_styles.py                 ✅  7 tests
├── test_template_scaffold.py      ✅ 16 tests
└── test_templates.py              ✅ 10 tests
```

**Totaal:** 577 tests (575 pass, 2 fail: pdfrw niet geïnstalleerd) | **Coverage:** 75%

## API Endpoints

| Endpoint | Method | Status | Productie |
|----------|--------|--------|-----------|
| `/api/health` | GET | ✅ | ✅ Live |
| `/api/templates` | GET | ✅ | ✅ Live |
| `/api/brands` | GET | ✅ | ✅ Live |
| `/api/templates/{name}/scaffold` | GET | ✅ | ✅ Live |
| `/api/validate` | POST | ✅ | ✅ Live |
| `/api/generate/v2` | POST | ✅ | ✅ Live |
| `/api/upload` | POST | ✅ | ✅ Live |

## Dependencies

```toml
# Core
reportlab>=4.0, svglib, PyYAML, Pillow, requests
fastapi, uvicorn, python-multipart, jsonschema, pymupdf, pydantic

# Optional
owslib   # kadaster (PDOK WMS)

# Dev
pytest, pytest-cov, ruff, mypy, httpx
```
