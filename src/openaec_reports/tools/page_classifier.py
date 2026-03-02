"""Page classifier — classificeer PDF pagina's op type."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from .pdf_extractor import RawPageData


class PageType(str, Enum):
    """Paginatype classificatie."""

    COVER = "cover"
    COLOFON = "colofon"
    TOC = "toc"
    CONTENT = "content"
    APPENDIX_DIVIDER = "appendix_divider"
    BACKCOVER = "backcover"
    UNKNOWN = "unknown"


@dataclass
class ClassifiedPage:
    """Pagina met classificatie en betrouwbaarheid."""

    page: RawPageData
    page_type: PageType
    confidence: float  # 0.0 - 1.0


def classify_pages(pages: list[RawPageData]) -> list[ClassifiedPage]:
    """Classificeer alle pagina's op type.

    Heuristieken worden in volgorde toegepast. Eerder toegewezen pagina's
    worden niet opnieuw geclassificeerd.

    Args:
        pages: Lijst van geëxtraheerde pagina's.

    Returns:
        Lijst van ClassifiedPage met type en confidence.
    """
    if not pages:
        return []

    results: dict[int, ClassifiedPage] = {}

    # 1. Cover = pagina 1
    if len(pages) >= 1:
        p = pages[0]
        conf = 0.95
        has_large_rect = _has_large_colored_rect(p, min_area_frac=0.40)
        has_few_texts = len(p.texts) < 15
        has_large_font = any(t.size > 20 for t in p.texts)
        if has_large_rect and has_few_texts and has_large_font:
            conf = 0.98
        elif has_large_rect or has_large_font:
            conf = 0.90
        results[0] = ClassifiedPage(page=p, page_type=PageType.COVER, confidence=conf)

    # 2. Backcover = laatste pagina
    if len(pages) >= 2:
        p = pages[-1]
        idx = len(pages) - 1
        conf = 0.90
        has_rect = _has_large_colored_rect(p, min_area_frac=0.30)
        has_contact = _has_contact_info(p)
        if has_rect and has_contact:
            conf = 0.95
        elif has_rect or has_contact:
            conf = 0.85
        results[idx] = ClassifiedPage(page=p, page_type=PageType.BACKCOVER, confidence=conf)

    # 3. Appendix dividers
    for i, p in enumerate(pages):
        if i in results:
            continue
        if _is_appendix_divider(p):
            results[i] = ClassifiedPage(
                page=p, page_type=PageType.APPENDIX_DIVIDER, confidence=0.90
            )

    # 4. Colofon (pagina's 2-4)
    for i in range(1, min(4, len(pages))):
        if i in results:
            continue
        if _is_colofon(pages[i]):
            results[i] = ClassifiedPage(page=pages[i], page_type=PageType.COLOFON, confidence=0.85)
            break  # max 1 colofon

    # 5. TOC (zoek in eerste 6 pagina's)
    for i in range(min(6, len(pages))):
        if i in results:
            continue
        if _is_toc(pages[i]):
            results[i] = ClassifiedPage(page=pages[i], page_type=PageType.TOC, confidence=0.85)
            break

    # 6. Rest → CONTENT
    classified: list[ClassifiedPage] = []
    for i, p in enumerate(pages):
        if i in results:
            classified.append(results[i])
        else:
            classified.append(ClassifiedPage(page=p, page_type=PageType.CONTENT, confidence=0.70))

    return classified


def _has_large_colored_rect(page: RawPageData, min_area_frac: float = 0.40) -> bool:
    """Check of pagina een groot gekleurd vlak heeft."""
    page_area = page.width_pt * page.height_pt
    for r in page.rects:
        if r.fill_hex is None:
            continue
        if r.fill_hex.upper() in ("#FFFFFF", "#FEFEFE", "#FDFDFD", "#000000"):
            continue
        rect_area = r.width * r.height
        if rect_area > min_area_frac * page_area:
            return True
    return False


def _has_contact_info(page: RawPageData) -> bool:
    """Check of pagina contactgegevens bevat."""
    combined = " ".join(t.text for t in page.texts).lower()
    patterns = [
        r"t\.\s*\+?\d",  # T. +31...
        r"\d{2}[\s-]\d{7}",  # telefoonnummer
        r"www\.",  # website
        r"\.nl\b",  # .nl domein
        r"@",  # email
    ]
    return sum(1 for p in patterns if re.search(p, combined)) >= 2


def _is_appendix_divider(page: RawPageData) -> bool:
    """Check of pagina een bijlage-scheidingspagina is."""
    has_large_rect = _has_large_colored_rect(page, min_area_frac=0.80)
    few_texts = len(page.texts) < 8
    has_large_font = any(t.size > 30 for t in page.texts)

    combined = " ".join(t.text for t in page.texts).lower()
    has_keyword = any(w in combined for w in ("bijlage", "appendix", "annex", "bijlagen"))

    return has_large_rect and few_texts and (has_large_font or has_keyword)


def _is_colofon(page: RawPageData) -> bool:
    """Check of pagina een colofon is."""
    # Tel horizontale lijnen
    h_lines = sum(
        1 for r in page.rects if r.element_type == "line" and r.width > 50 and r.height < 5
    )
    if h_lines < 4:
        return False

    # Zoek naar key-value labels
    bold_count = sum(
        1 for t in page.texts if "bold" in t.font.lower() or "medium" in t.font.lower()
    )
    # Zoek typische colofon-labels
    combined = " ".join(t.text for t in page.texts).lower()
    label_hits = sum(
        1
        for label in ("project", "opdracht", "adviseur", "datum", "versie", "status")
        if label in combined
    )

    return label_hits >= 2 or bold_count >= 4


def _is_toc(page: RawPageData) -> bool:
    """Check of pagina een inhoudsopgave is."""
    for t in page.texts:
        if t.size >= 14:
            lower = t.text.strip().lower()
            if lower in ("inhoud", "inhoudsopgave", "contents", "table of contents"):
                return True
    return False
