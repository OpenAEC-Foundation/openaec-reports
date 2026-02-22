"""PDF extractor — haal visuele elementen uit een PDF met PyMuPDF."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import fitz
except ImportError:
    fitz = None


@dataclass
class TextElement:
    """Tekstelement uit een PDF pagina."""

    text: str
    x: float
    y_top: float
    x2: float
    y_bottom: float
    font: str
    size: float
    color_hex: str


@dataclass
class RectElement:
    """Rechthoek of lijn uit een PDF pagina."""

    x: float
    y: float
    width: float
    height: float
    fill_hex: str | None = None
    stroke_hex: str | None = None
    stroke_width: float = 0.0
    element_type: str = "rect"  # "rect" | "line"
    corner_radius: float = 0.0


@dataclass
class ImageElement:
    """Afbeelding uit een PDF pagina."""

    x: float
    y: float
    width: float
    height: float
    xref: int


@dataclass
class PathElement:
    """Vector path uit een PDF pagina (polygon, clip-path, bezier)."""

    path_type: str  # "polygon" | "bezier" | "clip_path"
    points: list[tuple[float, float]]
    fill_hex: str | None = None
    stroke_hex: str | None = None
    stroke_width: float = 0.0
    is_closed: bool = True
    bbox_x: float = 0.0
    bbox_y: float = 0.0
    bbox_width: float = 0.0
    bbox_height: float = 0.0


@dataclass
class RawPageData:
    """Alle geëxtraheerde elementen van één PDF pagina."""

    page_number: int  # 1-based
    width_pt: float
    height_pt: float
    texts: list[TextElement] = field(default_factory=list)
    rects: list[RectElement] = field(default_factory=list)
    images: list[ImageElement] = field(default_factory=list)
    paths: list[PathElement] = field(default_factory=list)
    page_image_path: str | None = None


def _color_to_hex(color: tuple | list | None) -> str | None:
    """Converteer float RGB tuple (0-1) naar hex string.

    Args:
        color: Tuple van (r, g, b) floats, of None.

    Returns:
        Hex string "#RRGGBB" of None.
    """
    if color is None:
        return None
    if len(color) < 3:
        return None
    r, g, b = color[:3]
    return f"#{int(r * 255):02X}{int(g * 255):02X}{int(b * 255):02X}"


def extract_pdf(
    pdf_path: Path,
    output_dir: Path | None = None,
    dpi: int = 150,
) -> list[RawPageData]:
    """Extraheer alle visuele elementen uit een PDF.

    Args:
        pdf_path: Pad naar het PDF bestand.
        output_dir: Optionele map voor pagina PNG renders.
        dpi: DPI voor pagina renders.

    Returns:
        Lijst van RawPageData, één per pagina.

    Raises:
        ImportError: Als PyMuPDF niet geïnstalleerd is.
        FileNotFoundError: Als het PDF bestand niet bestaat.
    """
    if fitz is None:
        raise ImportError(
            "PyMuPDF is vereist voor brand analyse. "
            "Installeer met: pip install bm-reports[brand-tools]"
        )

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF niet gevonden: {pdf_path}")

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    pages: list[RawPageData] = []

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        page_num = page_idx + 1
        pw = page.rect.width
        ph = page.rect.height

        # Render pagina naar PNG
        page_image_path = None
        if output_dir:
            pix = page.get_pixmap(dpi=dpi)
            img_path = output_dir / f"page_{page_num:03d}.png"
            pix.save(str(img_path))
            page_image_path = str(img_path)

        # Tekst extractie
        texts = _extract_texts(page)

        # Rechthoeken en lijnen
        rects = _extract_rects(page, pw, ph)

        # Vector paths (polygonen, clip-paths)
        paths = _extract_paths(page)

        # Afbeeldingen
        images = _extract_images(page)

        pages.append(
            RawPageData(
                page_number=page_num,
                width_pt=pw,
                height_pt=ph,
                texts=texts,
                rects=rects,
                images=images,
                paths=paths,
                page_image_path=page_image_path,
            )
        )

    doc.close()
    return pages


def _extract_texts(page) -> list[TextElement]:
    """Extraheer tekstelementen uit een pagina."""
    texts: list[TextElement] = []
    text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

    for block in text_dict.get("blocks", []):
        if block.get("type") != 0:  # 0 = tekst blok
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not text:
                    continue

                bbox = span.get("bbox", (0, 0, 0, 0))
                color_int = span.get("color", 0)
                r = (color_int >> 16) & 0xFF
                g = (color_int >> 8) & 0xFF
                b = color_int & 0xFF
                color_hex = f"#{r:02X}{g:02X}{b:02X}"

                texts.append(
                    TextElement(
                        text=text,
                        x=bbox[0],
                        y_top=bbox[1],
                        x2=bbox[2],
                        y_bottom=bbox[3],
                        font=span.get("font", ""),
                        size=round(span.get("size", 0), 1),
                        color_hex=color_hex,
                    )
                )

    return texts


def _extract_rects(page, page_width: float, page_height: float) -> list[RectElement]:
    """Extraheer rechthoeken en lijnen uit een pagina."""
    rects: list[RectElement] = []

    for drawing in page.get_drawings():
        items = drawing.get("items", [])
        fill = drawing.get("fill")
        stroke_color = drawing.get("color")
        stroke_width = drawing.get("width", 0)

        fill_hex = _color_to_hex(fill)
        stroke_hex = _color_to_hex(stroke_color)

        rect = drawing.get("rect")
        if rect is None:
            continue

        x = rect.x0
        y = rect.y0
        w = rect.x1 - rect.x0
        h = rect.y1 - rect.y0

        if w <= 0 and h <= 0:
            continue

        # Classificeer: lijn of rect
        element_type = "line" if (abs(w) < 2 or abs(h) < 2) else "rect"

        # Detecteer rounded rect: "re" items met aangrenzende "c" (curve) items
        corner_radius = _detect_corner_radius(items)

        # Filter pagina-vullende witte rects
        is_page_filling = abs(w) > 0.9 * page_width and abs(h) > 0.9 * page_height
        if is_page_filling:
            # Skip tenzij niet-witte kleur
            if fill_hex is None or fill_hex.upper() in ("#FFFFFF", "#FEFEFE", "#FDFDFD"):
                continue

        rects.append(
            RectElement(
                x=x,
                y=y,
                width=abs(w),
                height=abs(h),
                fill_hex=fill_hex,
                stroke_hex=stroke_hex,
                stroke_width=stroke_width,
                element_type=element_type,
                corner_radius=corner_radius,
            )
        )

    return rects


def _detect_corner_radius(items: list) -> float:
    """Detecteer corner radius uit drawing items.

    Rounded rects bestaan uit afwisselende "l" (line) en "c" (curve) items.
    De radius wordt berekend uit de afstand tussen curve start en eindpunt.
    """
    curve_count = sum(1 for item in items if item[0] == "c")
    if curve_count < 4:
        return 0.0

    # Bereken radius uit eerste curve
    for item in items:
        if item[0] == "c":
            # Cubic bezier: item = ("c", p1, c1, c2, p2)
            try:
                p1 = item[1]
                p2 = item[4]
                dx = abs(p2.x - p1.x)
                dy = abs(p2.y - p1.y)
                radius = max(dx, dy)
                if radius > 0.5:
                    return round(radius, 1)
            except (IndexError, AttributeError):
                pass
    return 0.0


def _extract_paths(page) -> list[PathElement]:
    """Extraheer vector paths (polygonen, clip-paths) uit een pagina."""
    paths: list[PathElement] = []

    for drawing in page.get_drawings():
        items = drawing.get("items", [])
        if not items:
            continue

        # Verzamel alle punten uit de path items
        points: list[tuple[float, float]] = []
        has_curves = False
        has_rect_only = True

        for item in items:
            item_type = item[0]
            if item_type == "l":  # line to
                points.append((item[1].x, item[1].y))
                points.append((item[2].x, item[2].y))
                has_rect_only = False
            elif item_type == "c":  # cubic bezier
                points.append((item[1].x, item[1].y))
                points.append((item[4].x, item[4].y))
                has_curves = True
                has_rect_only = False
            elif item_type == "re":  # rectangle — skip, al in rects
                continue
            elif item_type == "qu":  # quad
                for qi in range(1, 5):
                    q = item[qi]
                    points.append((q.x, q.y))
                has_rect_only = False

        if has_rect_only or len(points) < 3:
            continue

        # Deduplicate opeenvolgende identieke punten
        deduped = [points[0]]
        for p in points[1:]:
            if abs(p[0] - deduped[-1][0]) > 0.1 or abs(p[1] - deduped[-1][1]) > 0.1:
                deduped.append(p)

        if len(deduped) < 3:
            continue

        fill = drawing.get("fill")
        stroke = drawing.get("color")

        # Bereken bounding box
        xs = [p[0] for p in deduped]
        ys = [p[1] for p in deduped]

        path_type = "bezier" if has_curves else "polygon"

        paths.append(
            PathElement(
                path_type=path_type,
                points=[(round(p[0], 1), round(p[1], 1)) for p in deduped],
                fill_hex=_color_to_hex(fill),
                stroke_hex=_color_to_hex(stroke),
                stroke_width=drawing.get("width", 0),
                is_closed=drawing.get("closePath", False),
                bbox_x=min(xs),
                bbox_y=min(ys),
                bbox_width=max(xs) - min(xs),
                bbox_height=max(ys) - min(ys),
            )
        )

    return paths


def _extract_images(page) -> list[ImageElement]:
    """Extraheer afbeeldingen uit een pagina."""
    images: list[ImageElement] = []

    for img_info in page.get_images(full=True):
        xref = img_info[0]
        try:
            img_rects = page.get_image_rects(xref)
            if img_rects:
                r = img_rects[0]
                images.append(
                    ImageElement(
                        x=r.x0,
                        y=r.y0,
                        width=r.width,
                        height=r.height,
                        xref=xref,
                    )
                )
        except Exception:
            # Sommige images hebben geen positie-info
            pass

    return images
