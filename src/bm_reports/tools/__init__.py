"""Brand analysis tools — extracteer huisstijl uit referentie-PDF's."""

from .pdf_extractor import (
    extract_pdf, RawPageData, TextElement, RectElement, ImageElement, PathElement,
)
from .page_classifier import classify_pages, ClassifiedPage, PageType
from .pattern_detector import analyze_brand, BrandAnalysis
from .config_generator import (
    generate_brand_yaml, generate_style_overrides, generate_analysis_report,
    generate_pages_yaml,
)
from .layout_extractor import (
    extract_page_layouts, PageLayout, TextZone, StaticElement, BadgeSpec,
)
from .stationery_extractor import StationeryExtractor
from .brand_builder import BrandBuilder

__all__ = [
    "extract_pdf", "RawPageData", "TextElement", "RectElement", "ImageElement", "PathElement",
    "classify_pages", "ClassifiedPage", "PageType",
    "analyze_brand", "BrandAnalysis",
    "generate_brand_yaml", "generate_style_overrides", "generate_analysis_report",
    "generate_pages_yaml",
    "extract_page_layouts", "PageLayout", "TextZone", "StaticElement", "BadgeSpec",
    "StationeryExtractor",
    "BrandBuilder",
]
