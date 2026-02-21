"""Layout extractor — extraheer per-pagina layout specificaties uit geëxtraheerde data."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from .pdf_extractor import RawPageData, TextElement, RectElement, ImageElement, PathElement
from .page_classifier import ClassifiedPage, PageType

logger = logging.getLogger(__name__)


@dataclass
class TextZone:
    """Dynamisch tekstveld op een pagina."""

    name: str  # "title", "subtitle", "project", etc.
    x_pt: float
    y_pt: float  # Top-down referentie (vanuit bovenkant pagina)
    font: str
    size: float
    color: str
    align: str = "left"
    max_width_pt: float | None = None
    is_dynamic: bool = True


@dataclass
class StaticElement:
    """Statisch visueel element (rect, path, image)."""

    element_type: str  # "rect" | "polygon" | "image" | "rounded_rect" | "line"
    x_pt: float = 0
    y_pt: float = 0  # Top-down referentie
    width_pt: float = 0
    height_pt: float = 0
    fill_color: str | None = None
    stroke_color: str | None = None
    stroke_width: float = 0
    corner_radius: float = 0
    points: list[tuple[float, float]] | None = None
    image_role: str | None = None  # "logo" | "photo" | "decorative"


@dataclass
class BadgeSpec:
    """Badge/pill element (rounded rect met tekst)."""

    label: str
    bg_color: str
    text_color: str
    x_pt: float
    y_pt: float
    width_pt: float
    height_pt: float
    corner_radius: float
    font_size: float


@dataclass
class PageLayout:
    """Volledige layout specificatie voor één pagina-type."""

    page_type: PageType
    page_number: int
    width_pt: float
    height_pt: float
    static_elements: list[StaticElement] = field(default_factory=list)
    text_zones: list[TextZone] = field(default_factory=list)
    badges: list[BadgeSpec] = field(default_factory=list)
    clip_polygon: list[tuple[float, float]] | None = None
    photo_rect: tuple[float, float, float, float] | None = None


def extract_page_layouts(
    classified_pages: list[ClassifiedPage],
) -> dict[PageType, PageLayout]:
    """Extraheer layout voor alle speciale pagina-types.

    Args:
        classified_pages: Lijst van geclassificeerde pagina's.

    Returns:
        Dict van PageType naar PageLayout.
    """
    layouts: dict[PageType, PageLayout] = {}

    for cp in classified_pages:
        if cp.page_type == PageType.CONTENT:
            continue
        layout = _extract_single_page_layout(cp)
        layouts[cp.page_type] = layout

    return layouts


def _extract_single_page_layout(cp: ClassifiedPage) -> PageLayout:
    """Extraheer layout voor één pagina."""
    page = cp.page
    ph = page.height_pt

    layout = PageLayout(
        page_type=cp.page_type,
        page_number=page.page_number,
        width_pt=page.width_pt,
        height_pt=page.height_pt,
    )

    # 1. Converteer alle rects naar StaticElements (y -> top-down)
    for r in page.rects:
        el_type = r.element_type
        if r.corner_radius > 0 and el_type == "rect":
            el_type = "rounded_rect"
        layout.static_elements.append(StaticElement(
            element_type=el_type,
            x_pt=round(r.x, 1),
            y_pt=round(ph - r.y - r.height, 1),
            width_pt=round(r.width, 1),
            height_pt=round(r.height, 1),
            fill_color=r.fill_hex,
            stroke_color=r.stroke_hex,
            stroke_width=r.stroke_width,
            corner_radius=r.corner_radius,
        ))

    # 2. Converteer alle paths naar StaticElements
    for p in page.paths:
        td_points = [(round(x, 1), round(ph - y, 1)) for x, y in p.points]
        layout.static_elements.append(StaticElement(
            element_type="polygon",
            x_pt=round(p.bbox_x, 1),
            y_pt=round(ph - p.bbox_y - p.bbox_height, 1),
            width_pt=round(p.bbox_width, 1),
            height_pt=round(p.bbox_height, 1),
            fill_color=p.fill_hex,
            stroke_color=p.stroke_hex,
            points=td_points,
        ))

    # 3. Converteer images
    for img in page.images:
        role = _classify_image_role(img, page)
        layout.static_elements.append(StaticElement(
            element_type="image",
            x_pt=round(img.x, 1),
            y_pt=round(ph - img.y - img.height, 1),
            width_pt=round(img.width, 1),
            height_pt=round(img.height, 1),
            image_role=role,
        ))

    # 4. Classificeer tekstelementen
    for t in page.texts:
        y_td = round(ph - t.y_top, 1)
        is_dynamic = _is_dynamic_text(t, cp.page_type)
        layout.text_zones.append(TextZone(
            name=_guess_text_role(t, cp.page_type),
            x_pt=round(t.x, 1),
            y_pt=y_td,
            font=t.font,
            size=t.size,
            color=t.color_hex,
            is_dynamic=is_dynamic,
        ))

    # 5. Detecteer badges (rounded rects met tekst erin)
    layout.badges = _detect_badges(page)

    # 6. Detecteer clip-path voor cover foto
    if cp.page_type == PageType.COVER:
        layout.clip_polygon = _find_clip_polygon(page)
        layout.photo_rect = _find_photo_rect(page)

    return layout


def _classify_image_role(img: ImageElement, page: RawPageData) -> str:
    """Classificeer een image als logo, foto of decoratief."""
    page_area = page.width_pt * page.height_pt
    img_area = img.width * img.height

    if img_area < page_area * 0.05 and (img.x < 150 or img.y < 150):
        return "logo"

    if img_area > page_area * 0.15:
        return "photo"

    return "decorative"


def _is_dynamic_text(text: TextElement, page_type: PageType) -> bool:
    """Bepaal of tekst dynamisch is (ingevuld bij generatie) of statisch."""
    static_texts = {
        "ontdek ons", "3bm.co.nl", "meedenken", "praktisch", "betrouwbaar",
        "projecten die inspireren", "coöperatie", "bijlage",
        "betrouwbaar | praktisch | meedenken",
    }

    text_lower = text.text.strip().lower()

    for st in static_texts:
        if st in text_lower:
            return False

    if page_type == PageType.COVER and text.size > 20:
        return True

    if page_type == PageType.COLOFON:
        colofon_labels = {
            "project", "in opdracht van", "adviseur", "datum",
            "fase", "status", "normen", "documentgegevens", "documentkenmerk",
        }
        if text_lower in colofon_labels:
            return False
        return True

    return False


def _guess_text_role(text: TextElement, page_type: PageType) -> str:
    """Geef een semantische naam aan een tekstelement."""
    if page_type == PageType.COVER:
        if text.size > 25:
            return "title"
        if text.size > 15:
            return "subtitle"
        if "ontdek" in text.text.lower():
            return "ontdek_text"

    if page_type == PageType.COLOFON:
        if text.size > 18:
            return "report_type"
        if text.size > 12:
            return "colofon_subtitle"

    if page_type == PageType.APPENDIX_DIVIDER:
        if text.size > 30 and "bijlage" in text.text.lower():
            return "appendix_number"
        if text.size > 30:
            return "appendix_title"

    return f"text_{round(text.y_top)}"


def _detect_badges(page: RawPageData) -> list[BadgeSpec]:
    """Detecteer badges: rounded rects met gecentreerde tekst."""
    badges: list[BadgeSpec] = []
    ph = page.height_pt

    for r in page.rects:
        if r.corner_radius <= 0:
            continue
        if r.width < 50 or r.height < 15 or r.height > 50:
            continue

        for t in page.texts:
            if (t.x >= r.x - 2 and t.x2 <= r.x + r.width + 2
                    and t.y_top >= r.y - 2 and t.y_bottom <= r.y + r.height + 2):
                badges.append(BadgeSpec(
                    label=t.text.strip(),
                    bg_color=r.fill_hex or "#808080",
                    text_color=t.color_hex,
                    x_pt=round(r.x, 1),
                    y_pt=round(ph - r.y - r.height, 1),
                    width_pt=round(r.width, 1),
                    height_pt=round(r.height, 1),
                    corner_radius=r.corner_radius,
                    font_size=t.size,
                ))
                break

    return badges


def _find_clip_polygon(
    page: RawPageData,
) -> list[tuple[float, float]] | None:
    """Zoek het clip-path polygon voor de cover foto."""
    best = None
    best_area = 0.0

    for p in page.paths:
        if len(p.points) < 5:
            continue
        area = p.bbox_width * p.bbox_height
        if area > best_area:
            best_area = area
            best = p

    if best and best_area > page.width_pt * page.height_pt * 0.1:
        return best.points

    return None


def _find_photo_rect(
    page: RawPageData,
) -> tuple[float, float, float, float] | None:
    """Zoek de foto-rechthoek op de cover."""
    for img in page.images:
        img_area = img.width * img.height
        if img_area > page.width_pt * page.height_pt * 0.15:
            return (round(img.x, 1), round(img.y, 1),
                    round(img.width, 1), round(img.height, 1))
    return None
