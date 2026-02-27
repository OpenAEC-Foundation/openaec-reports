"""Symitech tenant-specifieke modules."""

from bm_reports.modules import ModuleRegistry

from .bic_table import BicTableModule
from .cost_summary import CostSummaryModule
from .location_detail import LocationDetailModule
from .object_description import ObjectDescriptionModule


def register_symitech_modules() -> None:
    """Registreer alle Symitech modules bij de ModuleRegistry."""
    ModuleRegistry.register_tenant("symitech", "bic_table", BicTableModule)
    ModuleRegistry.register_tenant("symitech", "cost_summary", CostSummaryModule)
    ModuleRegistry.register_tenant(
        "symitech", "location_detail", LocationDetailModule,
    )
    ModuleRegistry.register_tenant(
        "symitech", "object_description", ObjectDescriptionModule,
    )


__all__ = [
    "BicTableModule",
    "CostSummaryModule",
    "LocationDetailModule",
    "ObjectDescriptionModule",
    "register_symitech_modules",
]
