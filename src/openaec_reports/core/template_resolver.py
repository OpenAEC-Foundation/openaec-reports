"""Template resolver — laadt template + page_type YAML's uit tenant directory.

Zoekpad:
1. tenants/{tenant}/templates/{name}.yaml  (template)
2. tenants/{tenant}/page_types/{name}.yaml (page types)

Fallback naar package defaults als tenant versie niet bestaat.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from openaec_reports.core.template_config import (
    PageType,
    TemplateConfig,
    parse_page_type,
    parse_template_config,
)

logger = logging.getLogger(__name__)

# Package-level defaults
_PACKAGE_DIR = Path(__file__).parent.parent
_ASSETS_TEMPLATES = _PACKAGE_DIR / "assets" / "templates"

# Tenant root (relatief t.o.v. project root, wordt overschreven door config)
_DEFAULT_TENANTS_DIR = Path(__file__).parent.parent.parent.parent / "tenants"


class TemplateResolver:
    """Laadt templates en page_types uit tenant directories.

    Usage::

        resolver = TemplateResolver(tenants_dir=Path("tenants"))
        template = resolver.load_template("bic_factuur", tenant="symitech")
        page_type = resolver.load_page_type("locatie", tenant="symitech")
    """

    def __init__(self, tenants_dir: Path | None = None):
        self._tenants_dir = tenants_dir or _DEFAULT_TENANTS_DIR
        self._template_cache: dict[str, TemplateConfig] = {}
        self._page_type_cache: dict[str, PageType] = {}

    def load_template(self, name: str, tenant: str) -> TemplateConfig:
        """Laad een template YAML.

        Args:
            name: Template naam (zonder .yaml extensie).
            tenant: Tenant identifier.

        Returns:
            Geparseerde TemplateConfig.

        Raises:
            FileNotFoundError: Als template niet gevonden.
        """
        cache_key = f"{tenant}/{name}"
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]

        # Zoek in tenant dir
        path = self._tenants_dir / tenant / "templates" / f"{name}.yaml"
        if not path.exists():
            # Fallback: package assets
            path = _ASSETS_TEMPLATES / f"{name}.yaml"
        if not path.exists():
            # Fallback: tenant subdir in assets
            path = _ASSETS_TEMPLATES / tenant / f"{name}.yaml"
        if not path.exists():
            raise FileNotFoundError(
                f"Template '{name}' niet gevonden voor tenant '{tenant}'. "
                f"Gezocht in: {self._tenants_dir / tenant / 'templates'}, "
                f"{_ASSETS_TEMPLATES}"
            )

        data = self._load_yaml(path)
        # Ensure tenant is set
        if "tenant" not in data:
            data["tenant"] = tenant

        config = parse_template_config(data)
        self._template_cache[cache_key] = config
        logger.info("Template geladen: %s (%s)", name, path)
        return config

    def load_page_type(self, name: str, tenant: str) -> PageType:
        """Laad een page_type YAML.

        Args:
            name: Page type naam (zonder .yaml extensie).
            tenant: Tenant identifier.

        Returns:
            Geparseerde PageType.

        Raises:
            FileNotFoundError: Als page_type niet gevonden.
        """
        cache_key = f"{tenant}/{name}"
        if cache_key in self._page_type_cache:
            return self._page_type_cache[cache_key]

        path = self._tenants_dir / tenant / "page_types" / f"{name}.yaml"
        if not path.exists():
            raise FileNotFoundError(
                f"Page type '{name}' niet gevonden voor tenant '{tenant}'. "
                f"Gezocht in: {self._tenants_dir / tenant / 'page_types'}"
            )

        data = self._load_yaml(path)
        if "name" not in data:
            data["name"] = name

        page_type = parse_page_type(data)
        self._page_type_cache[cache_key] = page_type
        logger.info("Page type geladen: %s (%s)", name, path)
        return page_type

    def load_all_page_types(self, template: TemplateConfig) -> dict[str, PageType]:
        """Laad alle page_types die een template nodig heeft.

        Args:
            template: De template configuratie.

        Returns:
            Dict van page_type naam → PageType.
        """
        page_types: dict[str, PageType] = {}
        for page_def in template.pages:
            if page_def.page_type not in page_types:
                page_types[page_def.page_type] = self.load_page_type(
                    page_def.page_type, template.tenant,
                )
        return page_types

    @staticmethod
    def _load_yaml(path: Path) -> dict[str, Any]:
        """Laad en parse een YAML bestand."""
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError(f"YAML bestand is geen dict: {path}")
        return data
