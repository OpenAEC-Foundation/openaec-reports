"""Tenant configuratie — centraliseert alle asset-paden.

Multi-tenant deployment: elke klant heeft eigen templates, brand, stationery,
logo's en fonts. De engine is generiek, de look & feel per tenant configureerbaar.

Eén environment variable BM_TENANT_DIR bepaalt waar klantspecifieke assets staan.
De library bevat alleen generieke defaults. Fallback-chain: tenant → package defaults.
"""

from __future__ import annotations

import os
from pathlib import Path

# Package defaults
_PACKAGE_ASSETS = Path(__file__).parent.parent / "assets"


class TenantConfig:
    """Beheert asset-paden met fallback naar package defaults.

    Volgorde: tenant_dir → package assets.

    Usage:
        config = TenantConfig()  # leest BM_TENANT_DIR
        config = TenantConfig("/data/tenants/3bm_cooperatie")

        config.templates_dirs   # → tenant templates + package templates
        config.brand_path       # → tenant brand.yaml of package default.yaml
        config.stationery_dir   # → tenant stationery/
        config.logos_dir        # → tenant logos/
        config.fonts_dir        # → tenant fonts/
    """

    def __init__(self, tenant_dir: str | Path | None = None):
        env_dir = os.environ.get("BM_TENANT_DIR")
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
        # Fallback naar package stationery (voor backward compat)
        pkg = _PACKAGE_ASSETS / "stationery"
        if pkg.exists() and any(pkg.iterdir()):
            # Zoek eerste subdirectory met stationery bestanden
            for sub in pkg.iterdir():
                if sub.is_dir() and (sub / "standaard.pdf").exists():
                    return sub
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
