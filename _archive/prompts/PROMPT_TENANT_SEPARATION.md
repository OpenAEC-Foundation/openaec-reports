# Opdracht: Tenant-scheiding — Assets uit de library halen

## Context

De library bundelt nu alle klantspecifieke assets (templates, brands, stationery, logo's, fonts) in `src/openaec_reports/assets/`. Dit is een probleem voor multi-tenant deployment: elke klant ziet elkaars templates en huisstijl. De engine moet generiek zijn, de look & feel moet per tenant configureerbaar zijn.

## Doel

Eén environment variable `OPENAEC_TENANT_DIR` bepaalt waar klantspecifieke assets staan. De library bevat alleen generieke defaults. Fallback-chain: tenant → package defaults.

## Gewenste structuur

```
# LIBRARY (package) — alleen generieke defaults
src/openaec_reports/assets/
├── templates/
│   └── blank.yaml              ← enige ingebouwde template
├── brands/
│   └── default.yaml            ← generieke fallback brand
├── fonts/                      ← LEEG (fonts zijn altijd tenant-specifiek)
├── logos/                      ← LEEG
└── stationery/                 ← LEEG

# TENANT (extern, via OPENAEC_TENANT_DIR)
# Voorbeeld: /data/tenants/3bm_cooperatie/
├── templates/
│   ├── structural_report.yaml
│   ├── daylight.yaml
│   └── building_code.yaml
├── brand.yaml                  ← was: brands/3bm_cooperatie.yaml
├── stationery/
│   ├── colofon.pdf
│   ├── standaard.pdf
│   ├── bijlagen.pdf
│   └── achterblad.pdf
├── logos/
│   ├── logo.svg
│   ├── logo-wit.svg
│   └── logo.png
└── fonts/
    ├── Gotham-Bold.ttf
    ├── Gotham-Book.ttf
    ├── Gotham-Medium.ttf
    └── Gotham-BookItalic.ttf
```

## Stappen

### Stap 1: TenantConfig class

Maak `src/openaec_reports/core/tenant.py`:

```python
"""Tenant configuratie — centraliseert alle asset-paden."""

from __future__ import annotations
import os
from pathlib import Path

# Package defaults
_PACKAGE_ASSETS = Path(__file__).parent.parent / "assets"


class TenantConfig:
    """Beheert asset-paden met fallback naar package defaults.
    
    Volgorde: tenant_dir → package assets.
    
    Usage:
        config = TenantConfig()  # leest OPENAEC_TENANT_DIR
        config = TenantConfig("/data/tenants/3bm_cooperatie")
        
        config.templates_dir   # → tenant templates + package templates
        config.brand_path      # → tenant brand.yaml of package default.yaml
        config.stationery_dir  # → tenant stationery/
        config.logos_dir       # → tenant logos/
        config.fonts_dir       # → tenant fonts/
    """
    
    def __init__(self, tenant_dir: str | Path | None = None):
        env_dir = os.environ.get("OPENAEC_TENANT_DIR")
        if tenant_dir:
            self._tenant_dir = Path(tenant_dir)
        elif env_dir:
            self._tenant_dir = Path(env_dir)
        else:
            self._tenant_dir = None
    
    @property
    def tenant_dir(self) -> Path | None:
        return self._tenant_dir
    
    @property
    def templates_dirs(self) -> list[Path]:
        """Tenant templates eerst, dan package defaults."""
        dirs = []
        if self._tenant_dir and (self._tenant_dir / "templates").exists():
            dirs.append(self._tenant_dir / "templates")
        dirs.append(_PACKAGE_ASSETS / "templates")
        return dirs
    
    @property
    def brand_path(self) -> Path:
        """Tenant brand.yaml, fallback naar package default.yaml."""
        if self._tenant_dir:
            tenant_brand = self._tenant_dir / "brand.yaml"
            if tenant_brand.exists():
                return tenant_brand
        return _PACKAGE_ASSETS / "brands" / "default.yaml"
    
    @property
    def stationery_dir(self) -> Path | None:
        if self._tenant_dir:
            d = self._tenant_dir / "stationery"
            if d.exists():
                return d
        return None
    
    @property
    def logos_dir(self) -> Path | None:
        if self._tenant_dir:
            d = self._tenant_dir / "logos"
            if d.exists():
                return d
        # Fallback naar package logos (als die er zijn)
        pkg = _PACKAGE_ASSETS / "logos"
        return pkg if pkg.exists() and any(pkg.iterdir()) else None
    
    @property
    def fonts_dir(self) -> Path | None:
        if self._tenant_dir:
            d = self._tenant_dir / "fonts"
            if d.exists():
                return d
        pkg = _PACKAGE_ASSETS / "fonts"
        return pkg if pkg.exists() and any(pkg.iterdir()) else None
```

### Stap 2: TemplateLoader aanpassen

Wijzig `template_loader.py`:
- `list_templates()` → merged lijst uit ALLE `templates_dirs` (tenant eerst, dedup op naam)
- `load(name)` → zoekt eerst in tenant dir, dan package
- `to_scaffold(name)` → ongewijzigd (gebruikt `load()`)

### Stap 3: BrandLoader aanpassen

Wijzig `brand.py`:
- `BrandLoader` accepteert `TenantConfig` als parameter
- `load()` leest `tenant_config.brand_path`
- `list_brands()` toont alleen de actieve tenant brand + "default"

### Stap 4: API aanpassen

Wijzig `api.py`:
- Maak één `TenantConfig()` instantie bij startup
- Alle endpoints gebruiken deze config
- `STATIONERY_DIR` → `tenant_config.stationery_dir`
- `/api/templates` → `TemplateLoader(tenant_config.templates_dirs)`
- `/api/brands` → alleen actieve brand + default
- `/api/stationery` → alleen tenant stationery

### Stap 5: Fonts registratie aanpassen

Wijzig `fonts.py`:
- `register_fonts()` accepteert optioneel `fonts_dir` parameter
- Zoekt eerst in meegegeven dir, dan package assets/fonts/

### Stap 6: Assets verplaatsen

1. Maak `tenants/3bm_cooperatie/` in de PROJECT ROOT (niet in package)
2. Verplaats (COPY, niet move — zodat tests blijven werken):
   - `assets/templates/structural_report.yaml` → `tenants/3bm_cooperatie/templates/`
   - `assets/templates/daylight.yaml` → idem
   - `assets/templates/building_code.yaml` → idem
   - `assets/brands/3bm_cooperatie.yaml` → `tenants/3bm_cooperatie/brand.yaml`
   - `assets/stationery/3bm_cooperatie/*` → `tenants/3bm_cooperatie/stationery/`
   - `assets/logos/*` → `tenants/3bm_cooperatie/logos/`
   - `assets/fonts/Gotham-*` → `tenants/3bm_cooperatie/fonts/`
3. Laat `blank.yaml` en `default.yaml` in package assets staan
4. Verwijder de klantspecifieke kopieën uit `assets/` NA stap 7

### Stap 7: Tests aanpassen

- Bestaande tests moeten blijven slagen
- Tests die specifiek 3BM assets gebruiken → set `OPENAEC_TENANT_DIR` in fixture
- Voeg test toe: `test_tenant.py` met:
  - TenantConfig zonder env var → package defaults
  - TenantConfig met dir → tenant assets
  - Fallback chain: tenant template bestaat niet → package default
  - TemplateLoader met tenant → merged lijst
  - BrandLoader met tenant → tenant brand

### Stap 8: Documentatie

- Update `CLAUDE.md` met tenant architectuur
- Update `DEPLOYMENT_GUIDE.md` met `OPENAEC_TENANT_DIR` instructie
- Update `STATUS.md`

## Regels

- GEEN breaking changes in de publieke API (Report.from_dict(), from_json())
- Zonder OPENAEC_TENANT_DIR moet alles werken zoals nu (backward compatible)
- Tests: alle 559 bestaande tests moeten blijven slagen
- Nieuwe tests voor tenant logic

## Verificatie

Na afloop:
1. `python -m pytest tests/ -v` → 0 failures
2. `OPENAEC_TENANT_DIR=tenants/3bm_cooperatie python -m pytest tests/ -v` → 0 failures
3. API starten met `OPENAEC_TENANT_DIR` → `/api/templates` toont alleen tenant + default templates
4. API starten ZONDER `OPENAEC_TENANT_DIR` → `/api/templates` toont alleen default (blank)
