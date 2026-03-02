"""Tenant configuratie — centraliseert alle asset-paden.

Multi-tenant deployment: elke klant heeft eigen templates, brand, stationery,
logo's en fonts. De engine is generiek, de look & feel per tenant configureerbaar.

Environment variables:
    OPENAEC_TENANT_DIR: Pad naar de primaire tenant directory (default brand).
    OPENAEC_TENANTS_ROOT: Pad naar parent directory met alle tenants.
        Als niet gezet, afgeleid van parent van OPENAEC_TENANT_DIR.

Fallback-chain: tenant → tenants_root/<name> → package defaults.
"""

from __future__ import annotations

import os
from pathlib import Path

# Package defaults
_PACKAGE_ASSETS = Path(__file__).parent.parent / "assets"


def detect_tenants_root() -> Path | None:
    """Detecteer de tenants root directory.

    Zoekt in volgorde:
    1. ``OPENAEC_TENANTS_ROOT`` environment variable
    2. Parent van ``OPENAEC_TENANT_DIR`` (afgeleid)

    Returns:
        Path naar tenants root, of None als niet gevonden.
    """
    env_root = os.environ.get("OPENAEC_TENANTS_ROOT")
    if env_root:
        root = Path(env_root)
        if root.exists():
            return root
    env_dir = os.environ.get("OPENAEC_TENANT_DIR")
    if env_dir:
        parent = Path(env_dir).parent
        if parent.exists() and parent != Path(env_dir):
            return parent
    return None


class TenantConfig:
    """Beheert asset-paden met fallback naar package defaults.

    Volgorde: tenant_dir → package assets.

    Usage:
        config = TenantConfig()  # leest OPENAEC_TENANT_DIR
        config = TenantConfig("/data/tenants/default")

        config.templates_dirs   # → tenant templates + package templates
        config.brand_path       # → tenant brand.yaml of package default.yaml
        config.stationery_dir   # → tenant stationery/
        config.logos_dir        # → tenant logos/
        config.fonts_dir        # → tenant fonts/
        config.tenants_root     # → parent met alle tenant directories
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
    def tenants_root(self) -> Path | None:
        """Parent directory met alle tenant directories.

        Afgeleid van ``OPENAEC_TENANTS_ROOT`` env var, of parent van
        ``OPENAEC_TENANT_DIR``. Bruikbaar voor multi-tenant brand resolution.
        """
        env_root = os.environ.get("OPENAEC_TENANTS_ROOT")
        if env_root:
            root = Path(env_root)
            if root.exists():
                return root
        if self._tenant_dir and self._tenant_dir.parent.exists():
            parent = self._tenant_dir.parent
            if parent != self._tenant_dir:
                return parent
        return None

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

    @property
    def modules_dir(self) -> Path | None:
        """Tenant YAML module definities directory."""
        if self._tenant_dir:
            d = self._tenant_dir / "modules"
            if d.exists():
                return d
        return None
