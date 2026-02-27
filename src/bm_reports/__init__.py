"""3BM Report Generator — Modulaire PDF rapportage library."""

__version__ = "0.1.0"

from bm_reports.core.brand import BrandConfig, BrandLoader
from bm_reports.core.document import A3, A4, Document
from bm_reports.core.engine import Report
from bm_reports.core.renderer_v2 import ReportGeneratorV2
from bm_reports.core.tenant import TenantConfig
from bm_reports.modules.symitech import register_symitech_modules

# Registreer tenant-specifieke modules bij import.
# TenantConfig detecteert automatisch de modules_dir via BM_TENANT_DIR
# of BM_TENANTS_ROOT. De Python modules worden altijd geregistreerd,
# YAML modules alleen als de tenant directory beschikbaar is.
_tenant = TenantConfig()
_symitech_modules_dir = None
if _tenant.tenants_root:
    _candidate = _tenant.tenants_root / "symitech" / "modules"
    if _candidate.exists():
        _symitech_modules_dir = _candidate
elif _tenant.modules_dir:
    _symitech_modules_dir = _tenant.modules_dir

register_symitech_modules(modules_dir=_symitech_modules_dir)

__all__ = [
    "A4",
    "A3",
    "BrandConfig",
    "BrandLoader",
    "Document",
    "Report",
    "ReportGeneratorV2",
    "__version__",
]
