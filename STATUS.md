# Backend Status — bm-reports

> Laatst bijgewerkt: 2026-02-27

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
├── modules/        # ContentModule base + tenant-specifieke modules (ModuleRegistry)
│   └── symitech/   # BIC table, cost summary, location detail, object description
├── auth/           # JWT + API Key authenticatie, user model, SQLite store
├── admin/          # Admin API: user CRUD, tenant/brand/asset/API key beheer
├── tools/          # Brand analyzer, stationery extractor, brand builder
├── utils/          # Logo prep, fonts
├── assets/         # Templates (YAML), brands (YAML), logos, fonts, graphics
│   └── brands/symitech/  # Symitech brand.yaml, stationery, logos
├── api.py          # FastAPI endpoints + StaticFiles mount (SPA serving)
├── cli.py          # CLI: analyze-brand, build-brand, serve, create-user
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
| **core/special_pages.py** | ✅ Compleet | ✅ test_special_pages.py (49 tests) | 80% |
| **core/block_registry.py** | ✅ Compleet | ✅ test_block_registry.py | 90% |
| **core/template_loader.py** | ✅ Compleet | ✅ test_templates.py + test_template_scaffold.py | 94% |
| **core/toc.py** | ✅ Compleet | ✅ via integratietests | 100% |
| **core/fonts.py** | ✅ Compleet | — | 66% |
| **core/renderer_v2.py** | ✅ Compleet | ✅ test_renderer_v2.py (53 tests) | — |
| **core/tenant.py** | ✅ Compleet | ✅ test_tenant.py (23 tests) | — |
| **components/base.py** | ✅ Compleet | — (via subclass tests) | — |
| **components/calculation.py** | ✅ Compleet | ✅ test_engine.py | 100% |
| **components/check_block.py** | ✅ Compleet | ✅ test_block_registry.py | 100% |
| **components/table_block.py** | ✅ Compleet | ✅ test_block_registry.py | 97% |
| **components/image_block.py** | ✅ Compleet | ✅ test_image_block.py (20 tests) | 79% |
| **components/map_block.py** | ✅ Compleet | ✅ test_map_block.py | 96% |
| **auth/** | ✅ Compleet | ✅ test_auth.py (19) + test_api_keys.py (36) | — |
| **admin/** | ✅ Compleet | ✅ test_admin.py (41 tests) | — |
| **api.py** | ✅ Compleet | ✅ test_api.py | 88% |
| **cli.py** | ✅ Compleet | ✅ test_cli.py (14 tests) | 61% |
| **data/json_adapter.py** | ✅ Compleet | ✅ test_json_adapter.py (14 tests) | 88% |
| **data/kadaster.py** | ✅ Compleet | ✅ test_data_adapters.py | 100% |
| **data/revit_adapter.py** | ⚠️ Stub | ✅ test_data_adapters.py | 87% |
| **modules/base.py** | ✅ Compleet | ✅ test_modules_foundation.py | — |
| **modules/__init__.py** | ✅ Compleet | ✅ test_modules_foundation.py | — |
| **modules/symitech/** | ✅ Compleet | ✅ test_symitech_modules.py (32 tests) | — |
| **tools/brand_analyzer** | ✅ Compleet | ✅ test_brand_analyzer.py | 93-99% |
| **tools/stationery_extractor.py** | ✅ Compleet | ✅ test_stationery_extractor.py | 96% |
| **tools/brand_builder.py** | ✅ Compleet | ✅ test_brand_builder.py | 68% |
| **utils/logo_prep.py** | ✅ Compleet | ✅ test_logo_prep.py | 100% |
| **reports/** | ⚠️ Toekomstige stubs | — | 0% (fase 6) |

## Test Suite

```
tests/
├── test_api_keys.py                ✅ 36 tests
├── test_admin.py                   ✅ 41 tests
├── test_auth.py                    ✅ 19 tests
├── test_api.py                     ✅ 26 tests
├── test_api_v2.py                  ✅  8 tests
├── test_block_registry.py          ✅ 34 tests
├── test_brand.py                   ✅ 42 tests
├── test_brand_analyzer.py          ✅ 39 tests
├── test_brand_builder.py           ✅  9 tests
├── test_cli.py                     ✅ 17 tests
├── test_core.py                    ✅ 19 tests
├── test_data_adapters.py           ✅ 13 tests
├── test_engine.py                  ✅ 15 tests
├── test_from_json.py               ✅ 19 tests
├── test_image_block.py             ✅ 20 tests
├── test_json_adapter.py            ✅ 14 tests
├── test_landscape.py               ✅ 12 tests
├── test_layout_extractor.py        ✅ 50 tests
├── test_logo_prep.py               ✅ 31 tests
├── test_map_block.py               ✅ 24 tests
├── test_page_templates_integration ✅ 18 tests
├── test_renderer_v2.py             ✅ 53 tests
├── test_special_pages.py           ✅ 49 tests
├── test_stationery.py              ✅ 14 tests
├── test_stationery_extractor.py    ✅  9 tests
├── test_styles.py                  ✅  7 tests
├── test_template_scaffold.py       ✅ 21 tests
├── test_templates.py               ✅ 12 tests
├── test_tenant.py                  ✅ 30 tests
├── test_modules_foundation.py     ✅ 22 tests
├── test_symitech_modules.py       ✅ 32 tests
├── test_symitech_brand.py         ✅ 16 tests
├── test_symitech_integration.py   ✅ 14 tests
└── test_symitech_templates.py     ✅ 21 tests
```

**Totaal:** 824 tests | **Coverage:** ~75%

## Recente Features

- **API Key authenticatie:** X-API-Key header voor machine-to-machine integratie (pyRevit, MCP, CI/CD). SHA-256 hashing, expiry, soft/hard delete
- **Bearer token auth:** Authorization: Bearer header support naast httpOnly cookies
- **Admin panel:** User CRUD, tenant/template/brand/asset beheer, API key management
- **Asset upload:** Stationery (.pdf/.png), logos (.svg/.png), fonts (.ttf/.otf) per tenant
- **Cadastral lookup:** POI marker op kaartcentrum + kadastrale perceelinfo in PDF via BAG/BRK API
- **BRT WMTS tiles:** Frontend map preview via BRT standaard tilestitching (WMS endpoint niet beschikbaar)
- **Multi-tenant:** `TenantConfig` met `BM_TENANT_DIR` env var, fallback-chain tenant → package defaults
- **Schema-aligned block types:** `bullet_list` en `heading_2` toegevoegd aan JSON schema (backend + frontend)
- **Code quality audit:** 7 fasen — schema fixes, PEP8, DRY refactoring, caching, type hints, config, dead code cleanup
- **BMFlowable base class:** Gedeelde `wrap()`/`draw()` voor 4 componenten
- **Shared style factories:** `block_style_heading()`, `_reference()`, `_body()`, `_mono()`, `_result()` in `styles.py`
- **Font embedding fix:** Gotham fonts embedded als subset via `fitz.TextWriter` in `renderer_v2.py` — PDF's nu leesbaar zonder lokaal geïnstalleerde fonts
- **Tenant management:** Tenants tab in admin panel — overzicht met asset counts, nieuwe tenant aanmaken (POST), verwijderen (DELETE), directe navigatie naar Brand tab
- **ModuleRegistry:** Content module systeem met core/tenant scheiding. `register_core()` voor universele blocks, `register_tenant()` voor klantspecifiek
- **Symitech tenant:** 4 modules (bic_table, cost_summary, location_detail, object_description), brand.yaml, 2 rapport templates
- **create_block() tenant support:** Block registry fallback naar ModuleRegistry voor tenant-specifieke block types

## API Endpoints

| Endpoint | Method | Status | Auth |
|----------|--------|--------|------|
| `/api/health` | GET | ✅ | Open |
| `/api/auth/login` | POST | ✅ | Open |
| `/api/auth/logout` | POST | ✅ | Open |
| `/api/auth/me` | GET | ✅ | User |
| `/api/templates` | GET | ✅ | User |
| `/api/brands` | GET | ✅ | User |
| `/api/templates/{name}/scaffold` | GET | ✅ | User |
| `/api/validate` | POST | ✅ | User |
| `/api/generate` | POST | ✅ | User |
| `/api/generate/v2` | POST | ✅ | User |
| `/api/upload` | POST | ✅ | User |
| `/api/stationery` | GET | ✅ | User |
| `/api/admin/users` | CRUD | ✅ | Admin |
| `/api/admin/tenants` | GET/POST | ✅ | Admin |
| `/api/admin/tenants/{t}` | DELETE | ✅ | Admin |
| `/api/admin/tenants/{t}/templates` | CRUD | ✅ | Admin |
| `/api/admin/tenants/{t}/brand` | GET/POST | ✅ | Admin |
| `/api/admin/tenants/{t}/assets/{c}` | CRUD | ✅ | Admin |
| `/api/admin/api-keys` | CRUD | ✅ | Admin |

## Dependencies

```toml
# Core
reportlab>=4.0, svglib, PyYAML, Pillow, requests
fastapi, uvicorn, python-multipart, jsonschema, pymupdf

# Optional
owslib   # kadaster (PDOK WMS)

# Dev
pytest, pytest-cov, ruff, mypy, httpx
```
