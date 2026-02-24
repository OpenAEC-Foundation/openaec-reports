# TODO — bm-reports

> Prioriteit: 🔴 Hoog | 🟡 Middel | 🟢 Laag
> Laatst bijgewerkt: 2026-02-24

---

## 🟡 Code Quality Audit (7 fasen)

### Fase 1 — Kritieke fixes (schema & security) ✅

- [x] 1.1 MapLayer type mismatch: frontend TypeScript aligned met schema/Python (`percelen`, `bebouwing`, etc.)
- [x] 1.2 `bullet_list` en `heading_2` block types toegevoegd aan JSON schema (backend ondersteunde ze al)
- [x] 1.3 `tempfile.mktemp()` → `NamedTemporaryFile(delete=False)` in `block_registry.py`
- [x] 1.4 Colofon schema uitgebreid met renderer_v2 velden (`opdrachtgever_naam`, `adviseur_bedrijf`, etc.)

### Fase 2 — PEP8 & consistentie ✅

- [x] 2.1 Bare `except Exception:` vervangen door specifieke types in 7 bestanden
- [x] 2.2 Duplicate `Colors.hex()` → alias van `as_hex`
- [x] 2.3 Foutafhandelingsstrategie gedocumenteerd (components raise, registry graceful, API catch)
- [x] 2.4 Lange regels opgesplitst in `api.py`
- [x] 2.5 Whitespace fixes in `special_pages.py`
- [x] 2.6 Volledige autoformat met `ruff format` (28 bestanden)
- [x] 2.7 Import ordering met `ruff check --select I --fix` (14 fixes)

### Fase 3 — Code duplication reduceren ✅

- [x] 3.1 `BLOCK_PADDING = 6` constante in `styles.py`, gebruikt in 3 componenten
- [x] 3.2 `_generate_and_respond()` helper in `api.py` (dedupliceert generate endpoints)
- [x] 3.3 `BMFlowable` base class met standaard `wrap()`/`draw()` (4 componenten, map_block uitgezonderd)
- [x] 3.4 Gedeelde style factories in `styles.py` voor calculation/check_block (~30 regels minder)
- [x] 3.5 Dead code verwijderd: ongebruikte `_brand_primary`/`_brand_secondary`/`_brand_text` uit special_pages

### Fase 4 — Performance & efficiëntie ✅

- [x] 4.1 Image size caching in `ImageBlock._get_natural_size()`
- [x] 4.2 Cached `_template_loader` en `_brand_loader` in `api.py` (module-level)
- [x] 4.3 Map cache LRU eviction (`_CACHE_MAX_FILES = 200`) in `KadasterMap`
- [x] 4.4 Lazy font initialization via `@functools.cache` in `_ensure_fonts_registered()`

### Fase 5 — Type hints ✅

- [x] 5.1 `wrap()` return type hints op alle Flowable componenten
- [x] 5.2 `TableBlock.wrap()` zet `self.width`/`self.height` consistent
- [x] 5.3 `**_kwargs` verwijderd uit block_registry factories (niet nodig, `create_block()` geeft selectief door)
- [x] 5.4 PEP 604 union syntax — al consistent (`from __future__ import annotations` + `str | Path` overal)

### Fase 6 — Configuratie & build ✅

- [x] 6.1 Dockerfile vereenvoudigd: `pip install .` ipv hardcoded deps
- [x] 6.2 CORS origins configureerbaar via `CORS_ORIGINS` env var
- [x] 6.3 Brand kleuren geünificeerd: `#40124A` (primary), `#38BDA0` (secondary) in 15+ bestanden
- [x] 6.4 Schema sync validatie script: `python scripts/check_schema_sync.py`

### Fase 7 — Dead code & cleanup ✅

- [x] 7.1 STATUS.md bijgewerkt (datum, test count, deps)
- [x] 7.2 Test assertions bijgewerkt voor nieuwe kleurwaarden
- [x] 7.3 `TOCBuilder._entries` lijst → vervangen door `_entry_count` counter (alleen len() werd gebruikt)
- [x] 7.4 `special_pages._build_colofon_rows()` verwijderd (dead code, 45 regels + 7 tests)
- [x] 7.5 STATUS.md verrijkt: recente features, correcte test counts (603+), nieuwe modules

### Fase 8 — Hardcoded data eliminatie ✅

- [x] 8.1 `special_pages.py`: 15+ hardcoded hex fallbacks vervangen door `BM_COLORS.*` constanten
- [x] 8.2 `page_templates.py`: `"GothamBook"` → `BM_FONTS.body`, `"#45243D"` → `BM_COLORS.text`
- [x] 8.3 `page_templates.py`: Return type hints toegevoegd aan 7 functies
- [x] 8.4 `brand_renderer.py`: `"#000000"` fallbacks → `BM_COLORS.text`
- [x] 8.5 `map_block.py`: Magic DPI `150` → `_MAP_DPI` constante, `"#F0F0F0"` → `BM_COLORS.background_alt`
- [x] 8.6 `check_block.py`: Magic `bar_h = 8` → `_UC_BAR_HEIGHT` constante
- [x] 8.7 `api.py`: `"3bm_cooperatie"` → `_DEFAULT_BRAND` constante

---

## 🟡 D1 — Monorepo Deploy op VPS

**Status:** Code gepusht, server deploy pending

- [x] `git push` naar GitHub
- [ ] Op server: `git pull` + `docker compose build --no-cache bm-reports-api`
- [ ] `docker compose up -d bm-reports-api`
- [ ] Verifiëren: https://report.3bm.co.nl/ laadt frontend (via StaticFiles)
- [ ] Verifiëren: https://report.3bm.co.nl/api/health werkt
- [ ] End-to-end test: template laden → rapport genereren → PDF download
- [ ] Caddyfile vereenvoudigen: enkele `reverse_proxy` naar API container
- [ ] Verwijder `bm-reports-ui/dist` volume mount uit docker-compose.yml

---

## ✅ D3 — CI/CD Pipeline

- [x] GitHub Actions workflow: build + push Docker image (multi-stage)
- [x] Lint (ruff) + test (pytest) in CI pipeline
- [x] Frontend + backend in één pipeline (multi-stage Dockerfile)

---

## 🟡 D4 — CrowdSec Bouncer

- [ ] Caddy bouncer installeren voor actieve IP blocking
- [ ] Testen met `cscli decisions list`

---

## 🟡 P1 — Stationery Extractie

**Prompt:** `PROMPT_P1_STATIONERY_EXTRACTIE.md`

- [ ] `build-brand` draaien tegen referentie-PDF
- [ ] Visueel verifiëren: tekst gestript, graphics intact
- [ ] `source:` paden + `text_zones:` invullen in `3bm_cooperatie.yaml`

---

## 🟢 P5 — Toekomstige Features

### Multi-bureau support
- [ ] Tweede brand toevoegen (bijv. BBL Engineering)
- [ ] Brand selector via API
- [ ] Stamkaart parser: PMS/CMYK kleurcodes

### Rapport types
- [ ] `reports/structural.py` — Constructief rapport
- [ ] `reports/daylight.py` — Daglichttoetreding
- [ ] `reports/building_code.py` — BBL-toetsing

### Revit integratie
- [ ] RevitAdapter: Revit model data → rapport JSON
- [ ] pyRevit commands: Generate rapport vanuit Revit UI

### SaaS / Deployment
- [ ] Frontend brand setup wizard (roept B5 tools aan)
- [ ] Multi-tenant brand management
- [ ] PDF caching op basis van JSON hash
- [x] User authentication (JWT via httpOnly cookies, SQLite user store)
- [x] API Key authenticatie (X-API-Key header, SHA-256, expiry, admin CRUD)
- [x] Bearer token authenticatie (Authorization header voor scripts/pyRevit)
- [x] Admin panel (user CRUD, tenant/template/brand/asset beheer)
- [ ] Rate limiting per tenant

---

## 🟡 Housekeeping (uit Lessons Learned audit 2026-02-24)

- [ ] **pytest cache cleanup:** 28+ `pytest-cache-files-*` directories verwijderen
- [ ] `pytest-cache-files-*` toevoegen aan `.gitignore`
- [ ] Overweeg `--basetemp=/tmp/pytest-bm` in `pyproject.toml` om cache te centraliseren
- [ ] `lessons_learned.md` aanmaken op basis van template (zie `../lessons_learned_template.md`)
- [ ] Vastleggen: "Schema-first" als architectuurregel heeft veel rework voorkomen — opnemen in lessons learned
- [ ] Vastleggen: Fase 8 (hardcoded eliminatie) had vermeden kunnen worden door vanaf dag 1 constanten te definiëren
- [ ] Vastleggen: Multi-tenant fallback-chain patroon documenteren als herbruikbaar pattern voor andere projecten
- [ ] D1 (VPS deploy) afronden — handmatig deployen is foutgevoelig en niet herhaalbaar

---

## Afgerond ✅

| Item | Wanneer |
|------|---------|
| Fase A: Brand Analyzer (PDF → YAML pipeline) | Week 7 |
| B1: KadasterMap + PDOK WMS | Week 8 |
| B2: FastAPI API (6 endpoints) | Week 8 |
| B3: Scaffold + Landscape oriëntatie | Week 8 |
| Font/kleur fixes (6 bugs) | Week 8 |
| Stationery systeem (code) | Week 8 |
| Brand Builder pipeline (code) | Week 8 |
| Page templates met stationery-first | Week 8 |
| CLI: analyze-brand, build-brand, serve | Week 8 |
| Test suite: 397 tests, 70% coverage | Week 8 |
| P2: Cleanup + archivering | Week 8 |
| P3: Special pages → brand YAML aansluiting | Week 8 |
| P4: Coverage gaps dichten (70% → 75%) | Week 8 |
| B5: Huisstijl extractie tool (6 modules, 50 tests) | Week 8 |
| **VPS opgezet: Hetzner CX22, Caddy, CrowdSec** | **Week 8** |
| **Docker image gebuild + API live** | **Week 8** |
| **GitHub repo: OpenAEC-Foundation/openaec-reports** | **Week 8** |
| **Cutlist Optimizer gemigreerd naar Caddy stack** | **Week 8** |
| **SSL auto-provisioned (Let's Encrypt)** | **Week 8** |
| **Dockerfile + pyproject.toml fixes (pycairo, README, force-include)** | **Week 8** |
| **D2: Tenant Separation (TenantConfig, loaders, tests)** | **Week 8** |
| **Monorepo merge: frontend + backend in één repo** | **Week 8** |
| **Multi-stage Dockerfile (node build + python runtime)** | **Week 8** |
| **StaticFiles mount in FastAPI (SPA serving)** | **Week 8** |
| **Vite dev proxy voor lokale ontwikkeling** | **Week 8** |
| **JSON alignment fixes (6 fixes, 22 tests)** | **Week 8** |
| **P2: Opschonen — dead code, docs archiveren, CLAUDE.md** | **Week 8** |
| **Code Quality Audit Fase 1-6 (schema fixes, PEP8, DRY, perf, types, config)** | **Week 8** |
| **Brand kleur unificatie (#40124A, #38BDA0) in 15+ bestanden** | **Week 8** |
| **bullet_list + heading_2 block types in JSON schema** | **Week 8** |
| **Fase 8: Hardcoded data eliminatie (BM_COLORS, constanten, type hints)** | **Week 8** |
| **D3: CI/CD Pipeline (GitHub Actions: lint, test, Docker build+push GHCR)** | **Week 8** |
| **Auth: Bearer token + API Key authenticatie** | **Week 9** |
| **Admin panel: user CRUD, tenant/asset beheer, API key management** | **Week 9** |
