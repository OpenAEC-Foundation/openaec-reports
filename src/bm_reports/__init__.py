"""3BM Report Generator — Modulaire PDF rapportage library."""

__version__ = "0.1.0"

from bm_reports.core.brand import BrandConfig, BrandLoader
from bm_reports.core.document import A3, A4, Document
from bm_reports.core.engine import Report
from bm_reports.core.renderer_v2 import ReportGeneratorV2

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
