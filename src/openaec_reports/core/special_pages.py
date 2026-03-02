"""Special pages — Cover, colofon en backcover via directe canvas rendering.

Pixel-perfect pagina's gebaseerd op BBL rapport analyse (COVER_SPEC.md).
Alle coördinaten worden proportioneel geschaald ten opzichte van A4
referentie-afmetingen, zodat A3 (en andere formaten) automatisch werken.

Huisstijl referentie:
    - Donkerpaars: #40124A
    - Turquoise:   #38BDA0
    - Tekst:       #45243D
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from reportlab.lib.colors import HexColor, white

from openaec_reports.core.brand import BrandConfig
from openaec_reports.core.document import DocumentConfig
from openaec_reports.core.fonts import get_font_name
from openaec_reports.core.styles import BM_COLORS

logger = logging.getLogger(__name__)

# Assets directory
ASSETS_DIR = Path(__file__).parent.parent / "assets"

# ============================================================
# A4 reference dimensions — all spec coords live in this space
# ============================================================

_REF_W = 595.28  # A4 width in points
_REF_H = 841.89  # A4 height in points

# ============================================================
# Huisstijl kleuren
# ============================================================

_COLOR_WHITE = white


# ============================================================
# Default waarden — backward compatibility als brand YAML geen
# pages.cover of pages.backcover sectie heeft.
# ============================================================

# Clip-path polygon voor cover foto (PDF y-up, A4 reference coords)
_DEFAULT_CLIP_POLYGON: list[list[float]] = [
    [350.809, 159.816],
    [383.673, 192.680],
    [538.583, 347.589],
    [538.583, 519.656],
    [386.850, 519.656],
    [538.583, 674.565],
    [538.583, 723.175],
    [56.693, 723.171],
    [56.693, 192.680],
    [56.697, 159.816],
]

# Default foto rect (x, y, w, h in A4 reference)
_DEFAULT_PHOTO_RECT: list[float] = [55.636, 161.648, 484.002, 560.753]

# Default badge definities (cover page)
_DEFAULT_BADGES: list[dict[str, Any]] = [
    {
        "label": "MEEDENKEN",
        "bg_color": "#f0c385",
        "text_color": BM_COLORS.primary,
        "x_ref": 297.64,
        "y_ref": 298.82,
        "w_ref": 112.05,
        "h_ref": 33.97,
    },
    {
        "label": "PRAKTISCH",
        "bg_color": BM_COLORS.secondary,
        "text_color": BM_COLORS.primary,
        "x_ref": 426.53,
        "y_ref": 298.82,
        "w_ref": 112.05,
        "h_ref": 33.97,
    },
    {
        "label": "BETROUWBAAR",
        "bg_color": "#e1574b",
        "text_color": "#FFFFFF",
        "x_ref": 341.76,
        "y_ref": 253.04,
        "w_ref": 134.70,
        "h_ref": 33.97,
    },
]

# Default backcover polygonen (A4 reference coords, PDF y-up)
_DEFAULT_WHITE_POLYGON: list[list[float]] = [
    [0, 0],
    [0, 698],
    [268, 842],
    [432, 842],
    [432, 698],
    [595, 555],
    [595, 320],
    [436, 320],
    [595, 178],
    [595, 0],
]

_DEFAULT_PURPLE_TRIANGLE: list[list[float]] = [
    [0, 842],
    [0, 539],
    [170, 688],
    [170, 842],
]


# ============================================================
# Proportional scaling utilities
# ============================================================


def _sx(val: float, page_w: float) -> float:
    """Scale horizontal value from A4 reference to actual page width."""
    return val * (page_w / _REF_W)


def _sy(val: float, page_h: float) -> float:
    """Scale vertical value from A4 reference to actual page height."""
    return val * (page_h / _REF_H)


def _sxy(x: float, y: float, pw: float, ph: float) -> tuple[float, float]:
    """Scale (x, y) pair from A4 reference to actual page dimensions."""
    return x * (pw / _REF_W), y * (ph / _REF_H)


def _sf(size: float, page_h: float) -> float:
    """Scale font size proportionally (based on page height ratio)."""
    return size * (page_h / _REF_H)


# ============================================================
# Helper functions
# ============================================================


def _brand_color(brand: BrandConfig, key: str, fallback: str) -> HexColor:
    """Haal een kleur op uit het brand config of gebruik fallback.

    Args:
        brand: Brand configuratie.
        key: Kleur sleutel (bijv. 'primary').
        fallback: Hex fallback kleur.

    Returns:
        HexColor voor gebruik in canvas.
    """
    hex_val = brand.colors.get(key, fallback)
    return HexColor(hex_val)


def _resolve_font(brand: BrandConfig, role: str) -> str:
    """Resolve font naam met Inter-prioriteit en Helvetica fallback.

    Volgorde:
        1. Inter (als geregistreerd via fonts.py)
        2. Brand config (YAML)
        3. Helvetica fallback

    Args:
        brand: Brand configuratie.
        role: Font rol ('heading', 'body', 'medium').

    Returns:
        Geregistreerde font naam bruikbaar in ReportLab.
    """
    optional_fonts = {"heading": "Inter-Bold", "body": "Inter-Regular", "medium": "Inter-Medium"}
    helvetica_fonts = {"heading": "Helvetica-Bold", "body": "Helvetica", "medium": "Helvetica"}

    inter_name = optional_fonts.get(role)
    if inter_name:
        effective = get_font_name(inter_name)
        if effective.startswith("Inter"):
            return effective

    return brand.fonts.get(role, helvetica_fonts.get(role, "Helvetica"))


def _draw_logo(
    canvas,
    logo_path: Path,
    x: float,
    y: float,
    width: float | None = None,
    height: float | None = None,
    *,
    preserve_aspect: bool = True,
) -> bool:
    """Teken een logo (PNG of SVG) op het canvas.

    Args:
        canvas: ReportLab canvas.
        logo_path: Pad naar het logo bestand.
        x: X positie in points.
        y: Y positie in points.
        width: Breedte in points (optioneel).
        height: Hoogte in points (optioneel).
        preserve_aspect: Bewaar aspect ratio als slechts 1 dimensie opgegeven.

    Returns:
        True als succesvol getekend, False bij fout.
    """
    if not logo_path.exists():
        logger.warning("Logo niet gevonden: %s", logo_path)
        return False

    suffix = logo_path.suffix.lower()

    try:
        if suffix == ".svg":
            from reportlab.graphics import renderPDF
            from svglib.svglib import svg2rlg

            drawing = svg2rlg(str(logo_path))
            if drawing is None:
                logger.warning("SVG kon niet worden geladen: %s", logo_path)
                return False

            if width is not None or height is not None:
                orig_w = drawing.width
                orig_h = drawing.height
                if width is not None and height is not None:
                    sx_val = width / orig_w
                    sy_val = height / orig_h
                elif width is not None:
                    sx_val = sy_val = width / orig_w
                else:
                    sx_val = sy_val = height / orig_h  # type: ignore[assignment]
                drawing.width = orig_w * sx_val
                drawing.height = orig_h * sy_val
                drawing.scale(sx_val, sy_val)

            renderPDF.draw(drawing, canvas, x, y)
        else:
            # PNG, JPG, etc.
            kwargs: dict[str, Any] = {"x": x, "y": y, "mask": "auto"}
            if width is not None:
                kwargs["width"] = width
            if height is not None:
                kwargs["height"] = height
            if preserve_aspect and (width is None) != (height is None):
                kwargs["preserveAspectRatio"] = True
            canvas.drawImage(str(logo_path), **kwargs)

        return True

    except (OSError, ValueError):
        logger.exception("Fout bij tekenen logo: %s", logo_path)
        return False


def _resolve_logo_path(brand: BrandConfig, logo_key: str, fallback_name: str) -> Path:
    """Resolve logo pad uit brand config of gebruik fallback.

    Args:
        brand: Brand configuratie.
        logo_key: Sleutel in brand.logos (bijv. 'main').
        fallback_name: Bestandsnaam als fallback (bijv. 'default-wit.png').

    Returns:
        Path naar het logo bestand.
    """
    logo_rel = brand.logos.get(logo_key, f"logos/{fallback_name}")
    return ASSETS_DIR / logo_rel


# ============================================================
# Cover page
# ============================================================


def draw_cover_page(
    canvas,
    doc,
    config: DocumentConfig,
    brand: BrandConfig,
    cover_image: str | Path | None = None,
) -> None:
    """Teken de cover pagina direct op het canvas.

    Alle visuele parameters komen uit brand.pages.cover (met defaults
    voor backward compatibility).

    Layout:
        1. Donkerpaars vlak (~74% van pagina)
        2. Projectfoto met clip-path polygon (optioneel)
        3. Wit OpenAEC logo + "Ontdek ons open-aec.com"
        4. Kernwoord badges (MEEDENKEN, PRAKTISCH, BETROUWBAAR)
        5. Rapporttitel en ondertitel

    Args:
        canvas: ReportLab canvas object.
        doc: ReportLab BaseDocTemplate.
        config: Document configuratie (project, subtitle, etc.).
        brand: Brand configuratie met kleuren en logo paden.
        cover_image: Optioneel pad naar projectfoto voor cover.
    """
    canvas.saveState()

    pw = config.effective_width_pt
    ph = config.effective_height_pt
    spec = brand.pages.get("cover", {})

    color_primary = _brand_color(brand, "primary", BM_COLORS.primary)
    color_secondary = _brand_color(brand, "secondary", BM_COLORS.secondary)

    heading_font = _resolve_font(brand, "heading")
    body_font = _resolve_font(brand, "body")
    medium_font = _resolve_font(brand, "medium")

    # ---- Laag 1: Donkerpaars vlak ----
    purple_y = _sy(spec.get("purple_rect_y_ref", 218.268), ph)
    purple_h = _sy(spec.get("purple_rect_h_ref", 623.622), ph)
    canvas.setFillColor(color_primary)
    canvas.rect(0, purple_y, pw, purple_h, fill=1, stroke=0)

    # ---- Laag 2: Projectfoto met clip-path (optioneel) ----
    if cover_image:
        _draw_clipped_photo(canvas, cover_image, pw, ph, spec)

    # ---- Laag 3: Logo + "Ontdek ons" ----
    logo_key = spec.get("logo_key", "white")
    logo_fallback = spec.get("logo_fallback", "main")
    logo_path = _resolve_logo_path(brand, logo_key, "default-wit.png")
    if not logo_path.exists():
        logo_path = _resolve_logo_path(brand, logo_fallback, "default.png")

    logo_x, logo_y = _sxy(
        spec.get("logo_x_ref", 62),
        spec.get("logo_y_ref", 775),
        pw,
        ph,
    )
    logo_w = _sx(spec.get("logo_w_ref", 100), pw)
    _draw_logo(canvas, logo_path, logo_x, logo_y, width=logo_w)

    # "Ontdek ons " (wit) + URL (turquoise)
    ontdek_text = spec.get("ontdek_text", "Ontdek ons ")
    ontdek_url = spec.get("ontdek_url", "open-aec.com")
    ontdek_size = _sf(spec.get("ontdek_size_ref", 13.0), ph)
    ontdek_y = _sy(spec.get("ontdek_y_ref", 788.7), ph)

    canvas.setFont(medium_font, ontdek_size)
    canvas.setFillColor(_COLOR_WHITE)
    canvas.drawString(_sx(spec.get("ontdek_x_ref", 401.3), pw), ontdek_y, ontdek_text)

    canvas.setFillColor(color_secondary)
    canvas.drawString(_sx(spec.get("ontdek_url_x_ref", 477.9), pw), ontdek_y, ontdek_url)

    # ---- Laag 4: Kernwoord badges ----
    _draw_badges(canvas, pw, ph, medium_font, spec)

    # ---- Laag 5: Titel en ondertitel ----
    title_size = _sf(spec.get("title_size_ref", 28.9), ph)
    canvas.setFont(heading_font, title_size)
    canvas.setFillColor(color_primary)
    canvas.drawString(
        _sx(spec.get("title_x_ref", 54.28), pw),
        _sy(spec.get("title_y_ref", 93.47), ph),
        config.project,
    )

    subtitle = getattr(config, "subtitle", "")
    if subtitle:
        sub_size = _sf(spec.get("subtitle_size_ref", 17.8), ph)
        canvas.setFont(body_font, sub_size)
        canvas.setFillColor(color_secondary)
        canvas.drawString(
            _sx(spec.get("subtitle_x_ref", 55.0), pw),
            _sy(spec.get("subtitle_y_ref", 63.0), ph),
            subtitle,
        )

    canvas.restoreState()


def _draw_clipped_photo(
    canvas,
    image_path: str | Path,
    page_w: float,
    page_h: float,
    spec: dict[str, Any] | None = None,
) -> None:
    """Teken projectfoto met clip-path polygon uit brand YAML.

    Args:
        canvas: ReportLab canvas.
        image_path: Pad naar de projectfoto.
        page_w: Pagina breedte in points.
        page_h: Pagina hoogte in points.
        spec: Cover spec dict uit brand.pages.cover (optioneel).
    """
    path = Path(image_path)
    if not path.exists():
        logger.warning("Cover afbeelding niet gevonden: %s", path)
        return

    spec = spec or {}

    canvas.saveState()

    # Clip-path polygon uit brand YAML of defaults
    clip_points = spec.get("clip_polygon", _DEFAULT_CLIP_POLYGON)
    clip = canvas.beginPath()
    for i, point in enumerate(clip_points):
        x, y = _sxy(point[0], point[1], page_w, page_h)
        if i == 0:
            clip.moveTo(x, y)
        else:
            clip.lineTo(x, y)
    clip.close()
    canvas.clipPath(clip, stroke=0, fill=0)

    # Foto rect uit brand YAML of defaults
    photo = spec.get("photo_rect", _DEFAULT_PHOTO_RECT)
    try:
        canvas.drawImage(
            str(path),
            _sx(photo[0], page_w),
            _sy(photo[1], page_h),
            _sx(photo[2], page_w),
            _sy(photo[3], page_h),
            mask="auto",
            preserveAspectRatio=True,
        )
    except (OSError, ValueError):
        logger.exception("Fout bij tekenen cover afbeelding: %s", path)

    canvas.restoreState()


def _draw_badges(
    canvas,
    page_w: float,
    page_h: float,
    font_name: str,
    spec: dict[str, Any] | None = None,
) -> None:
    """Teken kernwoord badges als rounded rectangles.

    Badge definities komen uit brand.pages.cover.badges (met defaults).

    Args:
        canvas: ReportLab canvas.
        page_w: Pagina breedte in points.
        page_h: Pagina hoogte in points.
        font_name: Font voor badge labels.
        spec: Cover spec dict uit brand.pages.cover (optioneel).
    """
    spec = spec or {}
    font_size = _sf(spec.get("badge_font_size_ref", 10.2), page_h)
    radius = _sy(spec.get("badge_radius_ref", 17), page_h)
    badges = spec.get("badges", _DEFAULT_BADGES)

    for badge in badges:
        label = badge.get("label", "")
        bg_color = HexColor(badge.get("bg_color", "#808080"))
        text_color = HexColor(badge.get("text_color", "#FFFFFF"))

        x = _sx(badge.get("x_ref", 0), page_w)
        y = _sy(badge.get("y_ref", 0), page_h)
        w = _sx(badge.get("w_ref", 100), page_w)
        h = _sy(badge.get("h_ref", 30), page_h)
        r = min(radius, h / 2)

        canvas.setFillColor(bg_color)
        canvas.roundRect(x, y, w, h, r, fill=1, stroke=0)

        # Tekst gecentreerd in badge
        canvas.setFont(font_name, font_size)
        canvas.setFillColor(text_color)
        text_w = canvas.stringWidth(label, font_name, font_size)
        text_x = x + (w - text_w) / 2
        text_y = y + (h - font_size) / 2 + font_size * 0.15  # baseline correctie
        canvas.drawString(text_x, text_y, label)


# ============================================================
# Colofon page
# ============================================================


def draw_colofon_page(
    canvas,
    doc,
    config: DocumentConfig,
    brand: BrandConfig,
    colofon_data: dict[str, Any] | None = None,
) -> None:
    """Teken de colofon pagina direct op het canvas.

    Layout (uit HUISSTIJL_SPEC.md):
        - Rapport type titel + subtitel bovenaan
        - Twee-koloms informatietabel (labels links, waarden rechts)
        - Horizontale scheidingslijnen tussen veldgroepen
        - Eerste twee labels (Project, In opdracht van) in paars, rest turquoise
        - Footer: turquoise blok linksonder + logo + paginanummer

    Alle posities leesbaar uit brand.pages.colofon (met defaults).

    Args:
        canvas: ReportLab canvas object.
        doc: ReportLab BaseDocTemplate.
        config: Document configuratie.
        brand: Brand configuratie.
        colofon_data: Extra colofon gegevens.
    """
    canvas.saveState()

    ph = config.effective_height_pt

    spec = brand.pages.get("colofon", {})
    data = colofon_data or {}

    # ---- Rapport type titel + subtitel bovenaan ----
    rt_font = get_font_name(spec.get("report_type_font", "Inter-Bold"))
    rt_size = spec.get("report_type_size", 22.0)
    rt_color = HexColor(spec.get("report_type_color", BM_COLORS.primary))
    rt_x = spec.get("report_type_x_pt", 70.9)
    rt_y = spec.get("report_type_y_pt", 57.3)

    report_type = config.report_type or data.get("report_type", "")
    if report_type:
        canvas.setFont(rt_font, rt_size)
        canvas.setFillColor(rt_color)
        canvas.drawString(rt_x, ph - rt_y, report_type)

    sub_font = get_font_name(spec.get("subtitle_font", "Inter-Regular"))
    sub_size = spec.get("subtitle_size", 14.0)
    sub_color = HexColor(spec.get("subtitle_color", BM_COLORS.secondary))
    sub_x = spec.get("subtitle_x_pt", 70.9)
    sub_y = spec.get("subtitle_y_pt", 86.8)

    subtitle = getattr(config, "subtitle", "") or data.get("subtitle", "")
    if subtitle:
        canvas.setFont(sub_font, sub_size)
        canvas.setFillColor(sub_color)
        canvas.drawString(sub_x, ph - sub_y, subtitle)

    # ---- Veldwaarden mapping ----
    field_values = {
        "project": config.project,
        "client": config.client,
        "author": config.author,
        "date": data.get("date", ""),
        "norms": data.get("norms", ""),
        "document_description": data.get("document_description", ""),
        "phase": data.get("phase", ""),
        "status": data.get("status", "CONCEPT"),
        "document_code": data.get("document_code", ""),
    }
    # Extra velden uit colofon_data
    for key, val in data.items():
        if key not in field_values and isinstance(val, str):
            field_values[key] = val

    # ---- Posities en stijlen uit spec ----
    label_x = spec.get("label_x_pt", 103)
    value_x = spec.get("value_x_pt", 229)
    first_color = HexColor(spec.get("first_labels_color", BM_COLORS.primary))
    other_color = HexColor(spec.get("other_labels_color", BM_COLORS.secondary))
    value_color = HexColor(spec.get("value_color", BM_COLORS.primary))
    line_x1 = spec.get("line_x1_pt", 102)
    line_x2 = spec.get("line_x2_pt", 420)
    line_stroke = spec.get("line_stroke_pt", 0.25)
    line_color = HexColor(spec.get("line_color", BM_COLORS.primary))

    label_font = get_font_name(spec.get("label_font", "Inter-Bold"))
    label_size = spec.get("label_size", 10.0)
    value_font = get_font_name(spec.get("value_font", "Inter-Regular"))
    value_size = spec.get("value_size", 10.0)

    # ---- Default velden als er geen spec.fields is ----
    default_fields = [
        {"label": "Project", "type": "project", "y_pt": 320.8},
        {"label": "In opdracht van", "type": "client", "y_pt": 368.8},
        {"type": "line", "y_pt": 517},
        {"label": "Adviseur", "type": "author", "y_pt": 488.8},
    ]
    fields = spec.get("fields", default_fields)

    first_n_purple = 2
    field_index = 0

    for field_def in fields:
        y_pt = field_def.get("y_pt", 0)
        y_rl = ph - y_pt  # top-down → bottom-up

        if field_def.get("type") == "line":
            canvas.setStrokeColor(line_color)
            canvas.setLineWidth(line_stroke)
            canvas.line(line_x1, y_rl, line_x2, y_rl)
        else:
            label = field_def.get("label", "")
            value_type = field_def.get("type", "")
            value = field_values.get(value_type, "")

            # Multiline waarden: split op newlines, teken elk op eigen regel
            value_lines = str(value).split("\n") if value else [""]

            # Label kleur: eerste N in paars, rest turquoise
            color = first_color if field_index < first_n_purple else other_color
            canvas.setFont(label_font, label_size)
            canvas.setFillColor(color)
            canvas.drawString(label_x, y_rl, label)

            # Waarde(n)
            canvas.setFont(value_font, value_size)
            canvas.setFillColor(value_color)
            for i, vline in enumerate(value_lines):
                canvas.drawString(value_x, y_rl - i * (value_size * 1.4), vline.strip())

            field_index += 1

    # ---- Footer: turquoise blok + logo + paginanummer ----
    rect_spec = spec.get("footer_rect", [0, 771, 282, 842])
    rect_color = HexColor(spec.get("footer_rect_color", BM_COLORS.secondary))
    # rect_spec = [x, y_top_topdown, width, y_bottom_topdown]
    rx = rect_spec[0]
    ry_bottom = ph - rect_spec[3]  # y_bottom in top-down → y in bottom-up
    rw = rect_spec[2]
    rh = rect_spec[3] - rect_spec[1]
    canvas.setFillColor(rect_color)
    canvas.rect(rx, ry_bottom, rw, rh, fill=1, stroke=0)

    # Logo in het turquoise blok
    logo_path = _resolve_logo_path(brand, "tagline", "default-tagline.png")
    if logo_path.exists():
        _draw_logo(canvas, logo_path, rx + 10, ry_bottom + 5, height=rh - 10)

    # Paginanummer
    pn_x = spec.get("page_num_x_pt", 534)
    pn_y = spec.get("page_num_y_pt", 796.3)
    pn_font = get_font_name(spec.get("page_num_font", "Inter-Regular"))
    pn_size = spec.get("page_num_size", 9.5)
    pn_color = HexColor(spec.get("page_num_color", BM_COLORS.secondary))
    page_num = canvas.getPageNumber()
    canvas.setFont(pn_font, pn_size)
    canvas.setFillColor(pn_color)
    canvas.drawRightString(pn_x, ph - pn_y, str(page_num))

    canvas.restoreState()


def _draw_revision_table(
    canvas,
    revisions: list[dict[str, str]],
    start_y: float,
    left_x: float,
    right_x: float,
    heading_font: str,
    body_font: str,
    header_color,
    page_h: float,
) -> float:
    """Teken een revisiehistorie tabel op het canvas.

    Args:
        canvas: ReportLab canvas.
        revisions: Lijst van revisie dicts met version/date/author/description.
        start_y: Y startpositie (bovenkant tabel).
        left_x: Linker X positie.
        right_x: Rechter X positie.
        heading_font: Font voor headers.
        body_font: Font voor data cellen.
        header_color: Kleur voor header tekst.
        page_h: Pagina hoogte (voor proportionele schaling).

    Returns:
        Y positie na de tabel.
    """
    header_size = _sf(8, page_h)
    cell_size = _sf(8, page_h)
    row_h = _sf(18, page_h)
    y = start_y

    width = right_x - left_x
    col_widths = [width * 0.12, width * 0.18, width * 0.25, width * 0.45]
    headers = ["Versie", "Datum", "Auteur", "Omschrijving"]

    # Header rij
    canvas.setFont(heading_font, header_size)
    canvas.setFillColor(header_color)
    col_x = left_x
    for i, header in enumerate(headers):
        canvas.drawString(col_x, y, header)
        col_x += col_widths[i]

    y -= row_h * 0.6
    canvas.setStrokeColor(header_color)
    canvas.setLineWidth(0.5)
    canvas.line(left_x, y, right_x, y)
    y -= row_h * 0.6

    # Data rijen
    canvas.setFont(body_font, cell_size)
    canvas.setFillColor(HexColor(BM_COLORS.text))
    for rev in revisions:
        col_x = left_x
        cells = [
            rev.get("version", ""),
            rev.get("date", ""),
            rev.get("author", ""),
            rev.get("description", ""),
        ]
        for i, cell in enumerate(cells):
            canvas.drawString(col_x, y, str(cell))
            col_x += col_widths[i]

        y -= row_h
        canvas.setStrokeColor(HexColor(BM_COLORS.separator))
        canvas.setLineWidth(0.2)
        canvas.line(left_x, y + row_h * 0.3, right_x, y + row_h * 0.3)

    return y


# ============================================================
# Appendix divider page
# ============================================================


def draw_appendix_divider_page(
    canvas,
    doc,
    config: DocumentConfig,
    brand: BrandConfig,
    appendix_number: int = 1,
    appendix_title: str = "",
) -> None:
    """Teken een bijlage-scheidingspagina.

    Layout (uit HUISSTIJL_SPEC.md):
        - Volledig turquoise achtergrond
        - Paars blok linksonder (zelfde als colofon footer)
        - "Bijlage N" in Inter-Bold 41.4pt paurs
        - Titel in Inter-Regular 41.4pt wit (kan meerdere regels zijn)
        - Tagline "Projecten die inspireren" rechtsonder in paurs

    Args:
        canvas: ReportLab canvas object.
        doc: ReportLab BaseDocTemplate.
        config: Document configuratie.
        brand: Brand configuratie.
        appendix_number: Bijlage nummer.
        appendix_title: Bijlage titel (kan \\n bevatten voor meerdere regels).
    """
    canvas.saveState()

    pw = config.effective_width_pt
    ph = config.effective_height_pt
    spec = brand.pages.get("appendix_divider", {})

    # Turquoise achtergrond
    bg_color = HexColor(spec.get("bg_color", BM_COLORS.secondary))
    canvas.setFillColor(bg_color)
    canvas.rect(0, 0, pw, ph, fill=1, stroke=0)

    # Paars blok linksonder
    purple_rect = spec.get("purple_rect", [0, 771, 282, 842])
    purple_color = HexColor(spec.get("purple_color", BM_COLORS.primary))
    prx = purple_rect[0]
    pry = ph - purple_rect[3]
    prw = purple_rect[2]
    prh = purple_rect[3] - purple_rect[1]
    canvas.setFillColor(purple_color)
    canvas.rect(prx, pry, prw, prh, fill=1, stroke=0)

    # Bijlage nummer
    num_font = get_font_name(spec.get("number_font", "Inter-Bold"))
    num_size = spec.get("number_size", 41.4)
    num_color = HexColor(spec.get("number_color", BM_COLORS.primary))
    num_x = spec.get("number_x_pt", 103)
    num_y = ph - spec.get("number_y_pt", 193.9)

    canvas.setFont(num_font, num_size)
    canvas.setFillColor(num_color)
    canvas.drawString(num_x, num_y, f"Bijlage {appendix_number}")

    # Titel (kan meerdere regels zijn, split op \n)
    title_font = get_font_name(spec.get("title_font", "Inter-Regular"))
    title_size = spec.get("title_size", 41.4)
    title_color = HexColor(spec.get("title_color", "#FFFFFF"))
    title_x = spec.get("title_x_pt", 136.1)
    title_first_y = ph - spec.get("title_first_y_pt", 262.2)
    title_line_spacing = spec.get("title_line_spacing_pt", 66.4)

    canvas.setFont(title_font, title_size)
    canvas.setFillColor(title_color)
    for i, line in enumerate(appendix_title.split("\n")):
        canvas.drawString(title_x, title_first_y - i * title_line_spacing, line.strip())

    # Tagline
    tagline = spec.get("tagline", "Projecten die inspireren")
    tag_font = get_font_name(spec.get("tagline_font", "Inter-Bold"))
    tag_size = spec.get("tagline_size", 17.9)
    tag_color = HexColor(spec.get("tagline_color", BM_COLORS.primary))
    tag_x = spec.get("tagline_x_pt", 330.5)
    tag_y = ph - spec.get("tagline_y_pt", 785.1)

    canvas.setFont(tag_font, tag_size)
    canvas.setFillColor(tag_color)
    canvas.drawString(tag_x, tag_y, tagline)

    canvas.restoreState()


# ============================================================
# Backcover page
# ============================================================


def draw_backcover_page(
    canvas,
    doc,
    config: DocumentConfig,
    brand: BrandConfig,
) -> None:
    """Teken het achterblad direct op het canvas.

    Alle visuele parameters komen uit brand.pages.backcover (met defaults
    voor backward compatibility).

    Layout:
        - Turquoise vlak als basis (gehele pagina)
        - Wit polygon: geometrisch patroon met schuine lijnen
        - Donkerpaars driehoek linksboven
        - OpenAEC logo groot in het wit vlak
        - Contactgegevens + "Ontdek ons" onderaan

    Args:
        canvas: ReportLab canvas object.
        doc: ReportLab BaseDocTemplate.
        config: Document configuratie.
        brand: Brand configuratie.
    """
    canvas.saveState()

    pw = config.effective_width_pt
    ph = config.effective_height_pt
    spec = brand.pages.get("backcover", {})

    color_primary = _brand_color(brand, "primary", BM_COLORS.primary)
    color_secondary = _brand_color(brand, "secondary", BM_COLORS.secondary)

    heading_font = _resolve_font(brand, "heading")
    body_font = _resolve_font(brand, "body")

    # ---- Turquoise achtergrond (gehele pagina) ----
    canvas.setFillColor(color_secondary)
    canvas.rect(0, 0, pw, ph, fill=1, stroke=0)

    # ---- Wit geometrisch polygon ----
    white_poly = spec.get("white_polygon", _DEFAULT_WHITE_POLYGON)
    canvas.setFillColor(_COLOR_WHITE)
    path = canvas.beginPath()
    for i, point in enumerate(white_poly):
        x, y = _sxy(point[0], point[1], pw, ph)
        if i == 0:
            path.moveTo(x, y)
        else:
            path.lineTo(x, y)
    path.close()
    canvas.drawPath(path, fill=1, stroke=0)

    # ---- Donkerpaars driehoek linksboven ----
    purple_tri = spec.get("purple_triangle", _DEFAULT_PURPLE_TRIANGLE)
    canvas.setFillColor(color_primary)
    tri = canvas.beginPath()
    for i, point in enumerate(purple_tri):
        x, y = _sxy(point[0], point[1], pw, ph)
        if i == 0:
            tri.moveTo(x, y)
        else:
            tri.lineTo(x, y)
    tri.close()
    canvas.drawPath(tri, fill=1, stroke=0)

    # ---- OpenAEC logo groot in het wit vlak ----
    logo_key = spec.get("logo_key", "main")
    logo_path = _resolve_logo_path(brand, logo_key, "default.png")
    logo_w = _sx(spec.get("logo_w_ref", 170), pw)
    logo_x, logo_y = _sxy(
        spec.get("logo_x_ref", 268),
        spec.get("logo_y_ref", 337),
        pw,
        ph,
    )
    _draw_logo(canvas, logo_path, logo_x, logo_y, width=logo_w)

    # ---- Contactgegevens onderaan ----
    contact = brand.contact
    contact_name = contact.get("name", "openaec Foundation U.A.")
    contact_address = contact.get("address", "")
    contact_website = contact.get("website", "open-aec.com")

    contact_x, contact_y = _sxy(
        spec.get("contact_x_ref", 268),
        spec.get("contact_y_ref", 185),
        pw,
        ph,
    )
    line_h = _sf(spec.get("contact_line_h_ref", 20), ph)

    name_size = _sf(spec.get("contact_name_size_ref", 11), ph)
    canvas.setFont(heading_font, name_size)
    canvas.setFillColor(color_primary)
    canvas.drawString(contact_x, contact_y, contact_name)

    detail_size = _sf(spec.get("contact_detail_size_ref", 9), ph)
    canvas.setFont(body_font, detail_size)
    canvas.setFillColor(HexColor(BM_COLORS.text))
    if contact_address:
        canvas.drawString(contact_x, contact_y - line_h, contact_address)

    ontdek_prefix = spec.get("ontdek_prefix", "Ontdek ons  \u2192  ")
    canvas.setFillColor(color_secondary)
    canvas.drawString(
        contact_x,
        contact_y - 2 * line_h,
        f"{ontdek_prefix}{contact_website}",
    )

    canvas.restoreState()
