"""Page templates — ReportLab PageTemplate definities voor cover, content, achterblad."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.platypus import Frame, PageTemplate

from openaec_reports.core.brand import BrandConfig, BrandLoader
from openaec_reports.core.brand_renderer import BrandRenderer
from openaec_reports.core.document import MM_TO_PT, DocumentConfig
from openaec_reports.core.fonts import get_font_name
from openaec_reports.core.special_pages import (
    draw_appendix_divider_page,
    draw_backcover_page,
    draw_colofon_page,
    draw_cover_page,
)
from openaec_reports.core.stationery import StationeryRenderer
from openaec_reports.core.styles import BM_COLORS, BM_FONTS

# Assets directory voor afbeeldingen in brand elementen
ASSETS_DIR = Path(__file__).parent.parent / "assets"


def create_page_templates(
    config: DocumentConfig,
    brand: BrandConfig | None = None,
    colofon_data: dict | None = None,
    cover_image: str | Path | None = None,
) -> list[PageTemplate]:
    """Maak PageTemplates voor het document.

    Elke pagina volgt het 3-lagenmodel:
    1. Stationery achtergrond (optioneel PDF/PNG)
    2. Header/footer
    3. Dynamische content

    Args:
        config: Document configuratie.
        brand: Optionele brand configuratie. Laadt default als None.
        colofon_data: Extra gegevens voor de colofon pagina.
        cover_image: Optioneel pad naar projectfoto voor cover.

    Returns:
        Lijst met templates: [cover, colofon, content, appendix_divider, backcover].
    """
    if brand is None:
        brand = BrandLoader().load_default()

    renderer = BrandRenderer(brand, assets_dir=ASSETS_DIR)
    stationery = StationeryRenderer(brand_dir=brand.brand_dir)

    page_w = config.effective_width_pt
    page_h = config.effective_height_pt
    ml = config.margins.left_pt
    mr = config.margins.right_pt
    mt = config.margins.top_pt
    mb = config.margins.bottom_pt

    # Header en footer ruimte uit brand config (in points)
    header_h = brand.header.height * MM_TO_PT
    footer_h = brand.footer.height * MM_TO_PT

    # Cover: volledig pagina frame
    cover_frame = Frame(
        ml,
        mb,
        page_w - ml - mr,
        page_h - mt - mb,
        id="cover_frame",
    )
    cover_template = PageTemplate(
        id="cover",
        frames=[cover_frame],
        onPage=lambda c, d: _on_page_cover(c, d, config, brand, stationery, cover_image),
    )

    # Colofon: volledig pagina frame
    colofon_frame = Frame(
        ml,
        mb,
        page_w - ml - mr,
        page_h - mt - mb,
        id="colofon_frame",
    )
    colofon_template = PageTemplate(
        id="colofon",
        frames=[colofon_frame],
        onPage=lambda c, d: _on_page_colofon(c, d, config, brand, stationery, colofon_data),
    )

    # Content: frame met ruimte voor header en footer
    # Gebruik brand stationery content_frame als beschikbaar
    content_spec = brand.stationery.get("content")
    if content_spec and content_spec.content_frame:
        cf = content_spec.content_frame
        content_frame = Frame(
            cf["x_pt"],
            cf.get("y_pt", mb),
            cf["width_pt"],
            cf["height_pt"],
            id="content_frame",
        )
    else:
        content_frame = Frame(
            ml,
            mb + footer_h,
            page_w - ml - mr,
            page_h - mt - mb - header_h - footer_h,
            id="content_frame",
        )
    content_template = PageTemplate(
        id="content",
        frames=[content_frame],
        onPage=lambda c, d: _on_page_content(c, d, config, brand, renderer, stationery),
    )

    # Bijlage divider: volledig pagina frame
    appendix_frame = Frame(
        ml,
        mb,
        page_w - ml - mr,
        page_h - mt - mb,
        id="appendix_frame",
    )
    appendix_template = PageTemplate(
        id="appendix_divider",
        frames=[appendix_frame],
        onPage=lambda c, d: _on_page_appendix(c, d, config, brand, stationery),
    )

    # Achterblad: volledig pagina frame
    backcover_frame = Frame(
        ml,
        mb,
        page_w - ml - mr,
        page_h - mt - mb,
        id="backcover_frame",
    )
    backcover_template = PageTemplate(
        id="backcover",
        frames=[backcover_frame],
        onPage=lambda c, d: _on_page_backcover(c, d, config, brand, stationery),
    )

    return [
        cover_template,
        colofon_template,
        content_template,
        appendix_template,
        backcover_template,
    ]


# ============================================================
# Stationery-first page callbacks
# ============================================================


def _on_page_cover(canvas, doc, config, brand, stationery, cover_image) -> None:
    """Cover: stationery-first, fallback naar programmatisch."""
    pw = config.effective_width_pt
    ph = config.effective_height_pt

    spec = brand.stationery.get("cover")
    if spec and spec.source and stationery.draw(canvas, spec.source, pw, ph):
        _draw_text_zones(canvas, spec.text_zones, config, brand, pw, ph)
    else:
        draw_cover_page(canvas, doc, config, brand, cover_image)


def _on_page_colofon(canvas, doc, config, brand, stationery, colofon_data) -> None:
    """Colofon: stationery-first, fallback naar programmatisch."""
    pw = config.effective_width_pt
    ph = config.effective_height_pt

    spec = brand.stationery.get("colofon")
    if spec and spec.source and stationery.draw(canvas, spec.source, pw, ph):
        _draw_text_zones(canvas, spec.text_zones, config, brand, pw, ph)
    else:
        draw_colofon_page(canvas, doc, config, brand, colofon_data)


def _on_page_content(canvas, doc, config, brand, renderer, stationery) -> None:
    """Content: stationery achtergrond (optioneel) + header/footer."""
    pw = config.effective_width_pt
    ph = config.effective_height_pt

    spec = brand.stationery.get("content")
    if spec and spec.source:
        stationery.draw(canvas, spec.source, pw, ph)

    # Header/footer altijd tekenen (via BrandRenderer)
    renderer.draw_page(canvas, doc, config)


def _on_page_appendix(canvas, doc, config, brand, stationery) -> None:
    """Appendix divider: stationery-first, fallback naar programmatisch."""
    pw = config.effective_width_pt
    ph = config.effective_height_pt

    spec = brand.stationery.get("appendix_divider")
    if spec and spec.source and stationery.draw(canvas, spec.source, pw, ph):
        _draw_text_zones(canvas, spec.text_zones, config, brand, pw, ph)
    else:
        draw_appendix_divider_page(canvas, doc, config, brand)


def _on_page_backcover(canvas, doc, config, brand, stationery) -> None:
    """Backcover: stationery-first, fallback naar programmatisch."""
    pw = config.effective_width_pt
    ph = config.effective_height_pt

    spec = brand.stationery.get("backcover")
    if spec and spec.source and stationery.draw(canvas, spec.source, pw, ph):
        _draw_text_zones(canvas, spec.text_zones, config, brand, pw, ph)
    else:
        draw_backcover_page(canvas, doc, config, brand)


# ============================================================
# Text zone rendering
# ============================================================


def _draw_text_zones(canvas, text_zones, config, brand, pw, ph) -> None:
    """Teken dynamische tekst in text zones op de stationery.

    Text zones zijn gedefinieerd met y_pt in top-down coördinaten.
    ReportLab canvas gebruikt bottom-up. Converteer: rl_y = ph - y_pt
    """
    for zone in text_zones:
        zone_type = zone.get("type", "text")

        if zone_type != "text":
            continue  # clipped_image en key_value_table later implementeren

        # Resolve font
        font_ref = zone.get("font", "$fonts.body")
        if font_ref.startswith("$fonts."):
            font_key = font_ref.replace("$fonts.", "")
            font_name = brand.fonts.get(font_key, BM_FONTS.body)
        else:
            font_name = font_ref
        font_name = get_font_name(font_name)

        # Resolve kleur
        color_ref = zone.get("color", "$colors.text")
        if color_ref.startswith("$colors."):
            color_key = color_ref.replace("$colors.", "")
            color_hex = brand.colors.get(color_key, BM_COLORS.text)
        else:
            color_hex = color_ref

        # Resolve tekst via data binding
        bind = zone.get("bind", zone.get("role", ""))
        text = _resolve_binding(bind, config, brand)
        if not text:
            continue

        size = zone.get("size", 10.0)
        x_pt = zone.get("x_pt", 0)
        y_pt = zone.get("y_pt", 0)
        align = zone.get("align", "left")

        # Converteer top-down y naar bottom-up
        rl_y = ph - y_pt

        canvas.saveState()
        canvas.setFont(font_name, size)
        canvas.setFillColor(HexColor(color_hex))

        if align == "right":
            canvas.drawRightString(x_pt, rl_y, text)
        elif align == "center":
            canvas.drawCentredString(x_pt, rl_y, text)
        else:
            canvas.drawString(x_pt, rl_y, text)

        canvas.restoreState()


def _resolve_binding(bind, config, brand) -> str:
    """Resolve data binding naar tekst waarde."""
    bindings = {
        "project": config.project,
        "project_number": config.project_number,
        "client": config.client,
        "author": config.author,
        "report_type": config.report_type,
        "subtitle": getattr(config, "subtitle", ""),
    }
    # Contact velden
    if bind.startswith("contact."):
        key = bind.replace("contact.", "")
        return brand.contact.get(key, "")

    return bindings.get(bind, "")
