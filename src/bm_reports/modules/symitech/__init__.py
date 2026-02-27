"""Symitech tenant-specifieke modules.

Registreert zowel de originele Python modules als YAML-driven modules.
Python modules hebben prioriteit (expliciet geregistreerd).
YAML modules worden als fallback geladen voor types zonder Python module.
"""

from __future__ import annotations

import logging
from pathlib import Path

from bm_reports.modules import ModuleRegistry

from .bic_table import BicTableModule
from .cost_summary import CostSummaryModule
from .location_detail import LocationDetailModule
from .object_description import ObjectDescriptionModule

logger = logging.getLogger(__name__)

# Directory met YAML module definities
_YAML_DEFS_DIR = Path(__file__).parent / "yaml_defs"


def register_symitech_modules() -> None:
    """Registreer alle Symitech modules bij de ModuleRegistry.

    Registreert eerst de Python modules (prioriteit), daarna eventuele
    YAML modules die nog niet bestaan.
    """
    ModuleRegistry.register_tenant("symitech", "bic_table", BicTableModule)
    ModuleRegistry.register_tenant("symitech", "cost_summary", CostSummaryModule)
    ModuleRegistry.register_tenant(
        "symitech", "location_detail", LocationDetailModule,
    )
    ModuleRegistry.register_tenant(
        "symitech", "object_description", ObjectDescriptionModule,
    )

    # Load YAML modules (only registers types not already registered)
    _register_yaml_modules()


def _register_yaml_modules() -> None:
    """Laad YAML module definities en registreer nieuwe types."""
    try:
        from bm_reports.modules.yaml_module import load_yaml_modules_from_dir
    except ImportError:
        logger.debug("yaml_module niet beschikbaar, YAML modules overgeslagen")
        return

    yaml_modules = load_yaml_modules_from_dir(_YAML_DEFS_DIR, tenant="symitech")

    # Bestaande Python module namen
    existing = {"bic_table", "cost_summary", "location_detail", "object_description"}

    for name, module_class in yaml_modules.items():
        if name not in existing:
            ModuleRegistry.register_tenant("symitech", name, module_class)
            logger.info("YAML module geregistreerd: symitech/%s", name)
        else:
            logger.debug(
                "YAML module %s overgeslagen (Python module heeft prioriteit)",
                name,
            )


def register_symitech_yaml_modules() -> None:
    """Registreer ALLEEN de YAML-versies van alle Symitech modules.

    Nuttig voor testen of wanneer YAML modules de voorkeur hebben boven
    Python modules. Overschrijft eventuele eerder geregistreerde modules.
    """
    try:
        from bm_reports.modules.yaml_module import load_yaml_modules_from_dir
    except ImportError:
        logger.warning("yaml_module niet beschikbaar")
        return

    yaml_modules = load_yaml_modules_from_dir(_YAML_DEFS_DIR, tenant="symitech")

    for name, module_class in yaml_modules.items():
        ModuleRegistry.register_tenant("symitech", name, module_class)
        logger.info("YAML module geregistreerd (override): symitech/%s", name)


__all__ = [
    "BicTableModule",
    "CostSummaryModule",
    "LocationDetailModule",
    "ObjectDescriptionModule",
    "register_symitech_modules",
    "register_symitech_yaml_modules",
]
