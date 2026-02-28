# Backend Status — bm-reports

> Laatst bijgewerkt: 2026-02-28

## Deployment

| Component | URL | Status |
|-----------|-----|--------|
| **API (productie)** | https://report.3bm.co.nl/api/* | ✅ Live |
| **Frontend (productie)** | https://report.3bm.co.nl/ | ✅ Monorepo deployed |
| **Cutlist Optimizer** | https://zaagplan.3bm.co.nl/ | ✅ Live |
| **Cockpit** | https://46.224.215.142:9090 | ✅ User: jochem |

### Infrastructuur
- **Server:** Hetzner CX22 (2 vCPU, 4GB RAM, 75GB SSD) — Ubuntu 24.04
- **IP:** 46.224.215.142
- **SSH:** Key-based only (root), password login disabled
- **Reverse proxy:** Caddy 2 (auto-SSL via Let's Encrypt)
- **Container runtime:** Docker 29.2.1 + Compose v5.0.2
- **Monitoring:** Cockpit (port 9090), CrowdSec
- **Repository:** https://github.com/OpenAEC-Foundation/openaec-reports

## 🔴 Actief: Template-Driven Engine Refactor

### Besluit (2026-02-28)

`renderer_v2.py` brand-aware maken is **vervallen**. Nieuwe aanpak:
**Template-Driven Engine** met declaratieve YAML configuratie.

**Kernprincipe:**
```
TEMPLATE  = documentstructuur (volgorde pagina's)
PAGE_TYPE = stationery + text zones + optioneel tabel
ENGINE    = generiek, nul tenant-specifieke code
```

**Drie pagina-modes:**

| Mode | Gedrag | Gebruik |
|------|--------|---------|
| `special` | Stationery + text zones | Voorblad, colofon, achterblad |
| `fixed` | Stationery + text zones + tabel (auto-paginering) | BIC controles, detail tabellen |
| `flow` | Stationery + ReportLab flowables | 3BM inhoudspagina's, berekeningen |

**Implementatie: Optie C** — alles via ReportLab DocTemplate. Special/fixed als
PageTemplates met onPage callbacks. Flow als standaard flowable content frames.

### Voortgang

| Component | Status | Bestand |
|-----------|--------|---------|
| Architectuurplan | ✅ Goedgekeurd | `docs/ARCHITECTURE_PLAN_TENANT_MODULES.md` |
| Dataclasses + parsers | ✅ Geschreven | `core/template_config.py` |
| Template resolver | ✅ Geschreven | `core/template_resolver.py` |
| Template engine | ✅ Geschreven | `core/template_engine.py` |
| Compilatie + imports | ✅ Gevalideerd | 10/10 runtime checks |
| Symitech page_type YAML's | ✅ 6/6 aangemaakt | `tenants/symitech/page_types/` |
| Symitech template YAML | ✅ Aangemaakt | `tenants/symitech/templates/bic_factuur.yaml` |
| Stationery PDFs per page-type | ⏳ Nog extraheren | `tenants/symitech/stationery/` |
| Unit tests | ✅ 80 tests (4 bestanden) | `tests/test_template_*.py`, `tests/test_data_binding.py` |
| End-to-end test | ✅ 3 tests, 6 pagina PDF | `tests/test_template_e2e.py` |

### Wat wordt verwijderd (na validatie)
- `src/bm_reports/modules/symitech/` — 4 Python modules (redundant met YAML)
- `tenants/symitech/modules/` — 4 YAML module configs
- `yaml_module.py` — 500+ regels (niet nodig voor fixed pages)

### Wat blijft
- `renderer_v2.py` — werkt voor 3BM, wordt niet aangeraakt
- Bestaande flow components (table, calculation, check, etc.)
- Brand systeem (brand.yaml, BrandLoader)
- Stationery renderer
- Auth + tenant systeem

## Architectuur

```
src/bm_reports/
├── core/
│   ├── template_config.py    ✅ NEW — dataclasses voor template YAML's
│   ├── template_resolver.py  ✅ NEW — laadt templates + page_types uit tenant dirs
│   ├── template_engine.py    ✅ NEW — template-driven PDF generator
│   ├── engine.py             ✅ Bestaande v1 engine (flow mode)
│   ├── renderer_v2.py        ✅ Bestaande v2 renderer (3BM only)
│   ├── stationery.py         ✅ Stationery renderer (gedeeld)
│   ├── brand.py              ✅ Brand configuratie + loader
│   ├── tenant_resolver.py    ✅ Per-request tenant resolution
│   ├── page_templates.py     ✅ ReportLab page templates
│   ├── styles.py             ✅ Paragraph/table styles
│   ├── fonts.py              ✅ Font management
│   ├── toc.py                ✅ Table of contents
│   └── document.py           ✅ Document config + constants
├── components/     ✅ Table, Calculation, Check, Image, Map, Spacer
├── modules/
│   ├── __init__.py           ✅ ModuleRegistry
│   ├── yaml_module.py        ⚠️ Te verwijderen na template engine validatie
│   └── symitech/             ⚠️ Te verwijderen na template engine validatie
├── auth/           ✅ JWT + API Key, SQLite store
├── admin/          ✅ User CRUD, tenant/brand beheer
├── tools/          ✅ Brand analyzer, stationery extractor
├── api.py          ✅ Tenant-aware endpoints
├── brand_api.py    ✅ Brand onboarding wizard
└── cli.py          ✅ CLI tools
```

### Tenant Directory Structuur

```
tenants/
├── 3bm_cooperatie/
│   ├── brand.yaml            ✅
│   ├── fonts/                ✅ Gotham
│   ├── logos/                ✅
│   ├── stationery/           ✅ 5 PDFs
│   └── templates/            ⏳ Nog migreren naar nieuwe structuur
│
├── symitech/
│   ├── brand.yaml            ✅ Volledig
│   ├── stationery/           ✅ 5 PDFs (moeten per page-type gesplit)
│   ├── modules/              ⚠️ Te verwijderen
│   ├── templates/            ⏳ Nieuw
│   └── page_types/           ⏳ Nieuw (directory aangemaakt)
```

## Tests

**Totaal:** 916+ tests | **Coverage:** ~75%

## API Endpoints

| Endpoint | Method | Status |
|----------|--------|--------|
| `/api/health` | GET | ✅ |
| `/api/templates` | GET | ✅ Tenant-aware |
| `/api/brands` | GET | ✅ Tenant-aware |
| `/api/generate` | POST | ✅ v1 engine |
| `/api/generate/v2` | POST | ✅ 3BM only (renderer_v2) |
| `/api/brand/*` | CRUD | ✅ |
| `/api/admin/*` | CRUD | ✅ Admin only |

## Recente Wijzigingen (week 9, 2026)

- **Template engine architectuur:** Nieuwe aanpak goedgekeurd — YAML-driven met 3 page modes
- **Nieuwe bestanden:** `template_config.py`, `template_resolver.py`, `template_engine.py`
- **Architectuurplan:** `docs/ARCHITECTURE_PLAN_TENANT_MODULES.md`
- **Ontdekking:** Python modules Symitech 100% redundant met YAML modules — eliminatie gepland
- **T1.7+T1.8:** 92 tests toegevoegd (unit + e2e), bugfix `pageSize` → `pagesize`
