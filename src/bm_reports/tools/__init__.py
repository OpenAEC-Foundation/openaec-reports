"""Brand analysis tools — extracteer huisstijl uit referentie-PDF's."""

from .brand_builder import BrandBuilder
from .config_generator import (
    generate_analysis_report,
    generate_brand_yaml,
    generate_pages_yaml,
    generate_style_overrides,
)
from .layout_extractor import (
    BadgeSpec,
    PageLayout,
    StaticElement,
    TextZone,
    extract_page_layouts,
)
from .page_classifier import ClassifiedPage, PageType, classify_pages
from .pattern_detector import BrandAnalysis, analyze_brand
from .pdf_extractor import (
    ImageElement,
    PathElement,
    RawPageData,
    RectElement,
    TextElement,
    extract_pdf,
)
from .stationery_extractor import StationeryExtractor

__all__ = [
    "extract_pdf",
    "RawPageData",
    "TextElement",
    "RectElement",
    "ImageElement",
    "PathElement",
    "classify_pages",
    "ClassifiedPage",
    "PageType",
    "analyze_brand",
    "BrandAnalysis",
    "generate_brand_yaml",
    "generate_style_overrides",
    "generate_analysis_report",
    "generate_pages_yaml",
    "extract_page_layouts",
    "PageLayout",
    "TextZone",
    "StaticElement",
    "BadgeSpec",
    "StationeryExtractor",
    "BrandBuilder",
]
