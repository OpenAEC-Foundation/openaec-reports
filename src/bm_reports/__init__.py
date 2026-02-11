"""3BM Report Generator — Modulaire PDF rapportage library."""

__version__ = "0.1.0"

from bm_reports.core.document import A4, A3, Document
from bm_reports.core.engine import Report

__all__ = ["A4", "A3", "Document", "Report", "__version__"]
