"""Special pages — Cover, colofon en backcover via directe canvas rendering.

Pixel-perfect pagina's gebaseerd op brand configuratie (YAML).
Alle coördinaten worden proportioneel geschaald ten opzichte van A4
referentie-afmetingen, zodat A3 (en andere formaten) automatisch werken.

Elke tenant kan alle visuele elementen configureren via brand.pages;
defaults zijn bewust neutraal (Helvetica, donkergrijs) zodat er geen
brand-specifieke kleuren of fonts verschijnen als er geen override is.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from reportlab.lib.colors import HexColor, white

from openaec_reports.core.brand import BrandConfig
from openaec_reports.core.document import DocumentConfig
from openaec_reports.core.fonts import get_font_name

logger = logging.getLogger(__name__)

# Assets directory
ASSETS_DIR = Path(__file__).parent.parent / "assets"

# ============================================================
# A4 reference dimensions — all spec coords live in this space
# ============================================================

_REF_W = 595.28  # A4 width in points
_REF_H = 841.89  # A4 height in points

# ============================================================
# Neutral fallback colours (geen brand-specifieke kleuren)
# ============================================================

_FALLBACK_PRIMARY = "#333333"
_FALLBACK_SECONDARY = "#666666"
_FALLBACK_TEXT = "#333333"
_FALLBACK_SEPARATOR = "#E0E0E0"

_COLOR_WHITE = white

# ============================================================
# Default waarden — neutraal, lege lijsten = skip
# ============================================================

# Default foto rect (x, y, w, h in A4 reference)
_DEFAULT_PHOTO_RECT: list[float] = [55.636, 161.648, 484.002, 560.753]


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
    """Resolve font naam via brand config met Helvetica fallback.

    Args:
        brand: Brand configuratie.
        role: Font rol ('heading', 'body', 'medium').

    Returns:
        Geregistreerde font naam bruikbaar in ReportLab.
    """
    helvetica_fonts = {
        "heading": "Helvetica-Bold",
        "body": "Helvetica",
        "medium": "Helvetica",
    }
    brand_font = brand.fonts.get(role, helvetica_fonts.get(role, "Helvetica"))
    return get_font_name(brand_font)


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

    Zoekt eerst in brand_dir (tenant), dan in package ASSETS_DIR.

    Args:
        brand: Brand configuratie.
        logo_key: Sleutel in brand.logos (bijv. 'main').
        fallback_name: Bestandsnaam als fallback (bijv. 'logo.png').

    Returns:
        Path naar het logo bestand.
    """
    logo_rel = brand.logos.get(logo_key, f"logos/{fallback_name}")
    # Zoek eerst in tenant/brand directory
    if brand.brand_dir:
        tenant_path = brand.brand_dir / logo_rel
        if tenant_path.exists():
            return tenant_path
    # Fallback naar package assets
    return ASSETS_DIR / logo_rel


# ============================================================
# Cover page
# ============================================================


def _draw_cover_dynamic_text(
    canvas,
    config: DocumentConfig,
    spec: dict[str, Any],
    pw: float,
    ph: float,
    heading_font: str,
    body_font: str,
    brand: BrandConfig,
) -> None:
    """Teken alleen de dynamische titel en ondertitel op de cover.

    Gebruikt wanneer stationery de statische visuals (achtergrond, logo,
    badges, etc.) afhandelt.

    Args:
        canvas: ReportLab canvas.
        config: Document configuratie.
        spec: Cover spec dict uit brand.pages.cover.
        pw: Pagina breedte in points.
        ph: Pagina hoogte in points.
        heading_font: Font voor de titel.
        body_font: Font voor de ondertitel.
        brand: Brand configuratie.
    """
    # Titel
    title_size = _sf(spec.get("title_size_ref", 28.9), ph)
    title_color = HexColor(
        spec.get(
            "title_color", brand.colors.get("primary", _FALLBACK_PRIMARY)
        )
    )
    canvas.setFont(heading_font, title_size)
    canvas.setFillColor(title_color)
    canvas.drawString(
        _sx(spec.get("title_x_ref", 54.28), pw),
        _sy(spec.get("title_y_ref", 93.47), ph),
        config.project,
    )

    # Ondertitel
    subtitle = getattr(config, "subtitle", "")
    if subtitle:
        sub_size = _sf(spec.get("subtitle_size_ref", 17.8), ph)
        sub_color = HexColor(
            spec.get(
                "subtitle_color",
                brand.colors.get("secondary", _FALLBACK_SECONDARY),
            )
        )
        canvas.setFont(body_font, sub_size)
        canvas.setFillColor(sub_color)
        canvas.drawString(
            _sx(spec.get("subtitle_x_ref", 55.0), pw),
            _sy(spec.get("subtitle_y_ref", 63.0), ph),
            subtitle,
        )


def draw_cover_page(
    canvas,
    doc,
    config: DocumentConfig,
    brand: BrandConfig,
    cover_image: str | Path | None = None,
) -> None:
    """Teken de cover pagina direct op het canvas.

    Alle visuele parameters komen uit brand.pages.cover (met neutrale
    defaults als er geen brand YAML override is).

    Layout:
        1. Achtergrondvlak (kleur uit brand of spec)
        2. Optioneel: illustratie overlay
        3. Projectfoto met clip-path polygon (optioneel)
        4. Logo + tagline (of legacy "Ontdek ons")
        5. Kernwoord badges (optioneel)
        6. Rapporttitel en ondertitel

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

    heading_font = _resolve_font(brand, "heading")
    body_font = _resolve_font(brand, "body")
    medium_font = _resolve_font(brand, "medium")

    # ---- Stationery-only modus: skip alle statische visuals ----
    # Als stationery de achtergrond, logo, badges, etc. levert,
    # renderen we alleen de dynamische titel en ondertitel.
    if spec.get("stationery_only", False):
        _draw_cover_dynamic_text(
            canvas, config, spec, pw, ph, heading_font, body_font, brand
        )
        canvas.restoreState()
        return

    # ---- Laag 1: Achtergrondvlak ----
    bg_y_ref = spec.get(
        "bg_rect_y_ref", spec.get("purple_rect_y_ref", 218.268)
    )
    bg_h_ref = spec.get(
        "bg_rect_h_ref", spec.get("purple_rect_h_ref", 623.622)
    )
    bg_y = _sy(bg_y_ref, ph)
    bg_h = _sy(bg_h_ref, ph)
    bg_color = HexColor(
        spec.get("bg_color", brand.colors.get("primary", _FALLBACK_PRIMARY))
    )
    canvas.setFillColor(bg_color)
    canvas.rect(0, bg_y, pw, bg_h, fill=1, stroke=0)

    # ---- Laag 1b: Illustratie overlay (optioneel) ----
    illustration_src = spec.get("illustration", "")
    if illustration_src and brand.brand_dir:
        ill_path = brand.brand_dir / illustration_src
        if ill_path.exists():
            canvas.saveState()
            try:
                opacity = spec.get("illustration_opacity", 1.0)
                canvas.setFillAlpha(opacity)
            except AttributeError:
                pass  # Oudere ReportLab zonder alpha support
            try:
                canvas.drawImage(
                    str(ill_path),
                    0,
                    bg_y,
                    pw,
                    bg_h,
                    mask="auto",
                    preserveAspectRatio=False,
                )
            except (OSError, ValueError):
                logger.warning(
                    "Kon illustration niet tekenen: %s", ill_path
                )
            canvas.restoreState()

    # ---- Laag 2: Projectfoto met clip-path (optioneel) ----
    if cover_image:
        _draw_clipped_photo(canvas, cover_image, pw, ph, spec)

    # ---- Laag 3: Logo ----
    logo_key = spec.get("logo_key", "white")
    logo_fallback = spec.get("logo_fallback", "main")
    logo_path = _resolve_logo_path(brand, logo_key, "logo-white.png")
    if not logo_path.exists():
        logo_path = _resolve_logo_path(brand, logo_fallback, "logo.png")

    logo_x, logo_y = _sxy(
        spec.get("logo_x_ref", 62),
        spec.get("logo_y_ref", 775),
        pw,
        ph,
    )
    logo_w = _sx(spec.get("logo_w_ref", 100), pw)
    _draw_logo(canvas, logo_path, logo_x, logo_y, width=logo_w)

    # ---- Laag 3b: Tagline (vervangt legacy "Ontdek ons") ----
    tagline = spec.get("tagline", "")
    if tagline:
        tag_font = get_font_name(
            spec.get("tagline_font", brand.fonts.get("medium", "Helvetica"))
        )
        tag_size = _sf(spec.get("tagline_size", 10.0), ph)
        tag_color = HexColor(
            spec.get("tagline_color", _FALLBACK_SECONDARY)
        )
        tag_x = _sx(spec.get("tagline_x_ref", 62), pw)
        tag_y = _sy(spec.get("tagline_y_ref", 755), ph)
        canvas.setFont(tag_font, tag_size)
        canvas.setFillColor(tag_color)
        canvas.drawString(tag_x, tag_y, tagline)

    # ---- Laag 3c: "Ontdek ons" (legacy — alleen als expliciet geconfigureerd) ----
    ontdek_text = spec.get("ontdek_text", "")
    if ontdek_text:
        color_secondary = _brand_color(
            brand, "secondary", _FALLBACK_SECONDARY
        )
        ontdek_url = spec.get("ontdek_url", "")
        ontdek_size = _sf(spec.get("ontdek_size_ref", 13.0), ph)
        ontdek_y = _sy(spec.get("ontdek_y_ref", 788.7), ph)

        canvas.setFont(medium_font, ontdek_size)
        canvas.setFillColor(_COLOR_WHITE)
        canvas.drawString(
            _sx(spec.get("ontdek_x_ref", 401.3), pw),
            ontdek_y,
            ontdek_text,
        )

        if ontdek_url:
            canvas.setFillColor(color_secondary)
            canvas.drawString(
                _sx(spec.get("ontdek_url_x_ref", 477.9), pw),
                ontdek_y,
                ontdek_url,
            )

    # ---- Laag 4: Kernwoord badges (optioneel) ----
    _draw_badges(canvas, pw, ph, medium_font, spec)

    # ---- Laag 5: Titel en ondertitel ----
    title_size = _sf(spec.get("title_size_ref", 28.9), ph)
    title_color = HexColor(
        spec.get(
            "title_color", brand.colors.get("primary", _FALLBACK_PRIMARY)
        )
    )
    canvas.setFont(heading_font, title_size)
    canvas.setFillColor(title_color)
    canvas.drawString(
        _sx(spec.get("title_x_ref", 54.28), pw),
        _sy(spec.get("title_y_ref", 93.47), ph),
        config.project,
    )

    subtitle = getattr(config, "subtitle", "")
    if subtitle:
        sub_size = _sf(spec.get("subtitle_size_ref", 17.8), ph)
        sub_color = HexColor(
            spec.get(
                "subtitle_color",
                brand.colors.get("secondary", _FALLBACK_SECONDARY),
            )
        )
        canvas.setFont(body_font, sub_size)
        canvas.setFillColor(sub_color)
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
    """Teken projectfoto met optioneel clip-path polygon uit brand YAML.

    Als geen clip_polygon geconfigureerd is, wordt de foto als simpele
    rechthoek getekend (zonder clipping).

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

    # Clip-path polygon uit brand YAML (leeg = geen clipping)
    clip_points = spec.get("clip_polygon", [])
    if clip_points:
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

    Badge definities komen uit brand.pages.cover.badges.
    Als geen badges geconfigureerd zijn, wordt er niets getekend.

    Args:
        canvas: ReportLab canvas.
        page_w: Pagina breedte in points.
        page_h: Pagina hoogte in points.
        font_name: Font voor badge labels.
        spec: Cover spec dict uit brand.pages.cover (optioneel).
    """
    spec = spec or {}
    badges = spec.get("badges", [])
    if not badges:
        return

    font_size = _sf(spec.get("badge_font_size_ref", 10.2), page_h)
    radius = _sy(spec.get("badge_radius_ref", 17), page_h)

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

    Layout:
        - Rapport type titel + subtitel bovenaan
        - Twee-koloms informatietabel (labels links, waarden rechts)
        - Horizontale scheidingslijnen tussen veldgroepen
        - Eerste twee labels in primaire kleur, rest in secundaire kleur
        - Footer: accent blok linksonder + logo + paginanummer

    Alle posities leesbaar uit brand.pages.colofon (met neutrale defaults).

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
    rt_font = get_font_name(
        spec.get("report_type_font", "Helvetica-Bold")
    )
    rt_size = spec.get("report_type_size", 22.0)
    rt_color = HexColor(
        spec.get(
            "report_type_color",
            brand.colors.get("primary", _FALLBACK_PRIMARY),
        )
    )
    rt_x = spec.get("report_type_x_pt", 70.9)
    rt_y = spec.get("report_type_y_pt", 57.3)

    report_type = config.report_type or data.get("report_type", "")
    if report_type:
        canvas.setFont(rt_font, rt_size)
        canvas.setFillColor(rt_color)
        canvas.drawString(rt_x, ph - rt_y, report_type)

    sub_font = get_font_name(spec.get("subtitle_font", "Helvetica"))
    sub_size = spec.get("subtitle_size", 14.0)
    sub_color = HexColor(
        spec.get(
            "subtitle_color",
            brand.colors.get("secondary", _FALLBACK_SECONDARY),
        )
    )
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
    first_color = HexColor(
        spec.get(
            "first_labels_color",
            brand.colors.get("primary", _FALLBACK_PRIMARY),
        )
    )
    other_color = HexColor(
        spec.get(
            "other_labels_color",
            brand.colors.get("secondary", _FALLBACK_SECONDARY),
        )
    )
    value_color = HexColor(
        spec.get(
            "value_color",
            brand.colors.get("primary", _FALLBACK_PRIMARY),
        )
    )
    line_x1 = spec.get("line_x1_pt", 102)
    line_x2 = spec.get("line_x2_pt", 420)
    line_stroke = spec.get("line_stroke_pt", 0.25)
    line_color = HexColor(
        spec.get(
            "line_color",
            brand.colors.get("primary", _FALLBACK_PRIMARY),
        )
    )

    label_font = get_font_name(spec.get("label_font", "Helvetica-Bold"))
    label_size = spec.get("label_size", 10.0)
    value_font = get_font_name(spec.get("value_font", "Helvetica"))
    value_size = spec.get("value_size", 10.0)

    # ---- Default velden (neutraal, Engelstalig) ----
    default_fields = [
        {"label": "Project", "type": "project", "y_pt": 320.8},
        {"label": "Client", "type": "client", "y_pt": 368.8},
        {"type": "line", "y_pt": 517},
        {"label": "Author", "type": "author", "y_pt": 488.8},
    ]
    fields = spec.get("fields", default_fields)

    first_n_colored = 2
    field_index = 0

    for field_def in fields:
        y_pt = field_def.get("y_pt", 0)
        y_rl = ph - y_pt  # top-down -> bottom-up

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

            # Label kleur: eerste N in primaire kleur, rest secundair
            color = first_color if field_index < first_n_colored else other_color
            canvas.setFont(label_font, label_size)
            canvas.setFillColor(color)
            canvas.drawString(label_x, y_rl, label)

            # Waarde(n)
            canvas.setFont(value_font, value_size)
            canvas.setFillColor(value_color)
            for i, vline in enumerate(value_lines):
                canvas.drawString(
                    value_x, y_rl - i * (value_size * 1.4), vline.strip()
                )

            field_index += 1

    # ---- Footer: accent blok + logo + paginanummer ----
    rect_spec = spec.get("footer_rect", [0, 771, 282, 842])
    rect_color = HexColor(
        spec.get(
            "footer_rect_color",
            brand.colors.get("secondary", _FALLBACK_SECONDARY),
        )
    )
    # rect_spec = [x, y_top_topdown, width, y_bottom_topdown]
    rx = rect_spec[0]
    ry_bottom = ph - rect_spec[3]  # y_bottom in top-down -> y in bottom-up
    rw = rect_spec[2]
    rh = rect_spec[3] - rect_spec[1]
    canvas.setFillColor(rect_color)
    canvas.rect(rx, ry_bottom, rw, rh, fill=1, stroke=0)

    # Logo in het accent blok
    logo_path = _resolve_logo_path(brand, "tagline", "logo-tagline.png")
    if logo_path.exists():
        _draw_logo(canvas, logo_path, rx + 10, ry_bottom + 5, height=rh - 10)

    # Paginanummer
    pn_x = spec.get("page_num_x_pt", 534)
    pn_y = spec.get("page_num_y_pt", 796.3)
    pn_font = get_font_name(spec.get("page_num_font", "Helvetica"))
    pn_size = spec.get("page_num_size", 9.5)
    pn_color = HexColor(
        spec.get(
            "page_num_color",
            brand.colors.get("secondary", _FALLBACK_SECONDARY),
        )
    )
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
    *,
    text_color: str = _FALLBACK_TEXT,
    separator_color: str = _FALLBACK_SEPARATOR,
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
        text_color: Hex kleur voor data cellen.
        separator_color: Hex kleur voor scheidingslijnen.

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
    canvas.setFillColor(HexColor(text_color))
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
        canvas.setStrokeColor(HexColor(separator_color))
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

    Layout:
        - Achtergrondkleur (gehele pagina)
        - Accent blok linksonder
        - "Bijlage N" in heading font
        - Titel (kan meerdere regels zijn)
        - Tagline rechtsonder (optioneel — skip als leeg)

    Alle parameters uit brand.pages.appendix_divider (met neutrale defaults).

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

    # Achtergrond
    bg_color = HexColor(
        spec.get(
            "bg_color",
            brand.colors.get("secondary", _FALLBACK_SECONDARY),
        )
    )
    canvas.setFillColor(bg_color)
    canvas.rect(0, 0, pw, ph, fill=1, stroke=0)

    # Accent blok linksonder (ondersteunt zowel accent_rect als purple_rect)
    accent_rect = spec.get(
        "accent_rect", spec.get("purple_rect", [0, 771, 282, 842])
    )
    accent_color = HexColor(
        spec.get(
            "accent_color",
            spec.get(
                "purple_color",
                brand.colors.get("primary", _FALLBACK_PRIMARY),
            ),
        )
    )
    prx = accent_rect[0]
    pry = ph - accent_rect[3]
    prw = accent_rect[2]
    prh = accent_rect[3] - accent_rect[1]
    canvas.setFillColor(accent_color)
    canvas.rect(prx, pry, prw, prh, fill=1, stroke=0)

    # Bijlage nummer
    num_font = get_font_name(
        spec.get("number_font", "Helvetica-Bold")
    )
    num_size = spec.get("number_size", 41.4)
    num_color = HexColor(
        spec.get(
            "number_color",
            brand.colors.get("primary", _FALLBACK_PRIMARY),
        )
    )
    num_x = spec.get("number_x_pt", 103)
    num_y = ph - spec.get("number_y_pt", 193.9)

    canvas.setFont(num_font, num_size)
    canvas.setFillColor(num_color)
    canvas.drawString(num_x, num_y, f"Bijlage {appendix_number}")

    # Titel (kan meerdere regels zijn, split op \n)
    title_font = get_font_name(spec.get("title_font", "Helvetica"))
    title_size = spec.get("title_size", 41.4)
    title_color = HexColor(spec.get("title_color", "#FFFFFF"))
    title_x = spec.get("title_x_pt", 136.1)
    title_first_y = ph - spec.get("title_first_y_pt", 262.2)
    title_line_spacing = spec.get("title_line_spacing_pt", 66.4)

    canvas.setFont(title_font, title_size)
    canvas.setFillColor(title_color)
    for i, line in enumerate(appendix_title.split("\n")):
        canvas.drawString(
            title_x, title_first_y - i * title_line_spacing, line.strip()
        )

    # Tagline (optioneel — skip als leeg)
    tagline = spec.get("tagline", "")
    if tagline:
        tag_font = get_font_name(
            spec.get("tagline_font", "Helvetica-Bold")
        )
        tag_size = spec.get("tagline_size", 17.9)
        tag_color = HexColor(
            spec.get(
                "tagline_color",
                brand.colors.get("primary", _FALLBACK_PRIMARY),
            )
        )
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

    Alle visuele parameters komen uit brand.pages.backcover (met neutrale
    defaults). Polygonen en decoraties worden alleen getekend als ze in de
    brand YAML gedefinieerd zijn.

    Layout:
        - Achtergrond (kleur uit spec of brand secondary)
        - Optioneel: wit polygon, driehoek, of accent rect
        - Logo
        - Optioneel: tagline
        - Contactgegevens + optioneel "Ontdek ons" prefix

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

    heading_font = _resolve_font(brand, "heading")
    body_font = _resolve_font(brand, "body")

    # ---- Achtergrond ----
    bg_color_hex = spec.get(
        "bg_color", brand.colors.get("secondary", _FALLBACK_SECONDARY)
    )
    canvas.setFillColor(HexColor(bg_color_hex))
    canvas.rect(0, 0, pw, ph, fill=1, stroke=0)

    # ---- Wit geometrisch polygon (optioneel — skip als leeg) ----
    white_poly = spec.get("white_polygon", [])
    if white_poly:
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

    # ---- Driehoek/accent polygon (optioneel — skip als leeg) ----
    purple_tri = spec.get("purple_triangle", [])
    if purple_tri:
        color_primary = _brand_color(brand, "primary", _FALLBACK_PRIMARY)
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

    # ---- Accent rect (optioneel — alternatief voor polygon decoraties) ----
    accent_rect = spec.get("accent_rect", [])
    if accent_rect:
        accent_color = HexColor(
            spec.get("accent_color", _FALLBACK_PRIMARY)
        )
        canvas.setFillColor(accent_color)
        apath = canvas.beginPath()
        for i, point in enumerate(accent_rect):
            x, y = _sxy(point[0], point[1], pw, ph)
            if i == 0:
                apath.moveTo(x, y)
            else:
                apath.lineTo(x, y)
        apath.close()
        canvas.drawPath(apath, fill=1, stroke=0)

    # ---- Logo ----
    logo_key = spec.get("logo_key", "main")
    logo_path = _resolve_logo_path(brand, logo_key, "logo.png")
    logo_w = _sx(spec.get("logo_w_ref", 170), pw)
    logo_x, logo_y = _sxy(
        spec.get("logo_x_ref", 268),
        spec.get("logo_y_ref", 337),
        pw,
        ph,
    )
    _draw_logo(canvas, logo_path, logo_x, logo_y, width=logo_w)

    # ---- Tagline (optioneel) ----
    tagline = spec.get("tagline", "")
    if tagline:
        tag_font = get_font_name(
            spec.get(
                "tagline_font",
                brand.fonts.get("heading", "Helvetica-Bold"),
            )
        )
        tag_size = _sf(spec.get("tagline_size", 14.0), ph)
        tag_color = HexColor(
            spec.get(
                "tagline_color",
                brand.colors.get("primary", _FALLBACK_PRIMARY),
            )
        )
        tag_x = _sx(spec.get("tagline_x_ref", 298), pw)
        tag_y = _sy(spec.get("tagline_y_ref", 380), ph)
        tag_align = spec.get("tagline_align", "left")

        canvas.setFont(tag_font, tag_size)
        canvas.setFillColor(tag_color)
        if tag_align == "center":
            canvas.drawCentredString(tag_x, tag_y, tagline)
        elif tag_align == "right":
            canvas.drawRightString(tag_x, tag_y, tagline)
        else:
            canvas.drawString(tag_x, tag_y, tagline)

    # ---- Contactgegevens onderaan ----
    contact = brand.contact
    contact_name = contact.get("name", "")
    contact_address = contact.get("address", "")
    contact_website = contact.get("website", "")

    if contact_name or contact_address or contact_website:
        contact_x, contact_y = _sxy(
            spec.get("contact_x_ref", 268),
            spec.get("contact_y_ref", 185),
            pw,
            ph,
        )
        line_h = _sf(spec.get("contact_line_h_ref", 20), ph)
        line_offset = 1

        name_size = _sf(spec.get("contact_name_size_ref", 11), ph)
        color_primary = _brand_color(brand, "primary", _FALLBACK_PRIMARY)
        if contact_name:
            canvas.setFont(heading_font, name_size)
            canvas.setFillColor(color_primary)
            canvas.drawString(contact_x, contact_y, contact_name)

        detail_size = _sf(spec.get("contact_detail_size_ref", 9), ph)
        text_color = _brand_color(brand, "text", _FALLBACK_TEXT)
        if contact_address:
            canvas.setFont(body_font, detail_size)
            canvas.setFillColor(text_color)
            canvas.drawString(contact_x, contact_y - line_h, contact_address)
            line_offset = 2

        # "Ontdek ons" prefix (legacy — alleen als expliciet geconfigureerd)
        ontdek_prefix = spec.get("ontdek_prefix", "")
        if ontdek_prefix and contact_website:
            color_secondary = _brand_color(
                brand, "secondary", _FALLBACK_SECONDARY
            )
            canvas.setFillColor(color_secondary)
            canvas.drawString(
                contact_x,
                contact_y - line_offset * line_h,
                f"{ontdek_prefix}{contact_website}",
            )
        elif contact_website:
            canvas.setFont(body_font, detail_size)
            canvas.setFillColor(text_color)
            canvas.drawString(
                contact_x,
                contact_y - line_offset * line_h,
                contact_website,
            )

    canvas.restoreState()
