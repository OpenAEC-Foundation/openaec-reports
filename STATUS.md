# STATUS — bm-reports

> Laatst bijgewerkt: 2026-02-28 21:30

---

## Deployment

| Omgeving | URL | Status |
|----------|-----|--------|
| Productie | https://report.3bm.co.nl | ✅ Online |
| API Health | https://report.3bm.co.nl/api/health | ✅ OK |

---

## Engines

| Engine | Endpoint | Status | Gebruik |
|--------|----------|--------|---------|
| V1 — `Report.from_dict()` | `/api/generate` | ✅ Werkend | 3BM standaard rapporten |
| V2 — `ReportGeneratorV2` | `/api/generate/v2` | ✅ Werkend | 3BM pixel-perfect rapporten |
| V3 — `TemplateEngine` | `/api/generate/template` | ✅ Werkend | Symitech BIC + multi-tenant YAML |

### TemplateEngine (V3) — Detail

| Component | Status | Tests |
|-----------|--------|-------|
| `template_config.py` — dataclasses + parsers | ✅ | 40+ |
| `template_resolver.py` — template discovery | ✅ | 20+ |
| `template_engine.py` — PDF assembly | ✅ | 42+ |
| `data_transform.py` — JSON → flat dict | ✅ | via E2E |
| API endpoint `/api/generate/template` | ✅ | 3 tests |
| E2E: 6-pagina PDF mixed orientation | ✅ | 3 tests |

### Symitech Tenant

| Asset | Status | Pad |
|-------|--------|-----|
| `brand.yaml` | ✅ | `tenants/symitech/brand.yaml` |
| Stationery PDFs (5) | ✅ | `tenants/symitech/stationery/` |
| Page type YAMLs (6) | ✅ | `tenants/symitech/page_types/` |
| Template YAML | ✅ | `tenants/symitech/templates/bic_factuur.yaml` |
| Test data | ✅ | `schemas/test_336_bic_factuur.json` |

---

## Frontend

| Feature | Status |
|---------|--------|
| Block editors (paragraph, table, image, calc, check, map) | ✅ |
| Template selector + scaffold loader | ✅ |
| Split view + live preview | ✅ |
| JSON import/export | ✅ |
| Undo/redo | ✅ |
| Auto-save | ✅ |
| Smart endpoint routing (V2 vs TemplateEngine) | ✅ |
| Brand wizard (admin) | ✅ |
| User/tenant management (admin) | ✅ |

---

## API Endpoints

| Endpoint | Method | Auth | Doel |
|----------|--------|------|------|
| `/api/health` | GET | ❌ | Health check |
| `/api/templates` | GET | ✅ | Lijst templates |
| `/api/templates/{name}/scaffold` | GET | ✅ | Leeg rapport scaffold |
| `/api/brands` | GET | ✅ | Lijst brands |
| `/api/validate` | POST | ✅ | JSON validatie |
| `/api/generate` | POST | ✅ | V1 PDF generatie |
| `/api/generate/v2` | POST | ✅ | V2 pixel-perfect PDF |
| `/api/generate/template` | POST | ✅ | TemplateEngine PDF |
| `/api/upload` | POST | ✅ | Afbeelding upload |
| `/api/stationery` | GET | ✅ | Stationery status |
| `/api/admin/*` | * | ✅ Admin | User/tenant beheer |

---

## Cleanup Status

| Item | Status |
|------|--------|
| Deprecated `modules/symitech/` verwijderd | ✅ |
| Deprecated `modules/yaml_module.py` verwijderd | ✅ |
| Deprecated `tenants/symitech/modules/` verwijderd | ✅ |
| Deprecated `assets/templates/symitech_*.yaml` verwijderd | ✅ |
| Oude PROMPT_*.md bestanden gearchiveerd | ✅ |
| pytest cache opgeruimd | ✅ |

---

## Volgende Stappen

Zie `TODO.md` voor gedetailleerde taken.

Korte termijn:
1. 🟡 Deploy nieuwe versie naar VPS (met TemplateEngine endpoint)
2. 🟡 Visuele validatie Symitech PDF vs referentie 336.01
3. 🟡 3BM page_type YAML's voor TemplateEngine migratie

Lange termijn:
4. 🟢 Tweede brand onboarding (BBL Engineering)
5. 🟢 RevitAdapter voor automatische rapport data
