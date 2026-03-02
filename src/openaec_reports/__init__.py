"""OpenAEC Report Generator — Modulaire PDF rapportage library."""

__version__ = "0.1.0"

from openaec_reports.core.brand import BrandConfig, BrandLoader
from openaec_reports.core.document import A3, A4, Document
from openaec_reports.core.engine import Report
from openaec_reports.core.renderer_v2 import ReportGeneratorV2
from openaec_reports.core.tenant import TenantConfig

__all__ = [
    "A4",
    "A3",
    "BrandConfig",
    "BrandLoader",
    "Document",
    "Report",
    "ReportGeneratorV2",
    "TenantConfig",
    "__version__",
]
