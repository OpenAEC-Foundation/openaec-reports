"""Page templates — ReportLab PageTemplate definities voor cover, content, achterblad."""

from __future__ import annotations

from reportlab.platypus import PageTemplate, Frame
from reportlab.lib.units import mm

from bm_reports.core.document import DocumentConfig, MM_TO_PT
from bm_reports.core.styles import BM_COLORS, BM_FONTS


def _draw_header(canvas, doc, config: DocumentConfig):
    """Teken header op content pagina's."""
    canvas.saveState()

    page_width = config.format.width_pt
    margin_left = config.margins.left_pt
    margin_right = config.margins.right_pt
    header_y = config.format.height_pt - config.margins.top_pt + 5

    # Projectinfo links
    canvas.setFont(BM_FONTS.body, 7.5)
    canvas.setFillColor(config.format.width_pt and BM_COLORS.text_light or BM_COLORS.text_light)
    text = f"{config.project_number} | {config.project}"
    canvas.drawString(margin_left, header_y, text)

    # Horizontale lijn
    line_y = header_y - 3
    canvas.setStrokeColor(BM_COLORS.rule)
    canvas.setLineWidth(0.5)
    canvas.line(margin_left, line_y, page_width - margin_right, line_y)

    canvas.restoreState()


def _draw_footer(canvas, doc, config: DocumentConfig):
    """Teken footer op content pagina's."""
    canvas.saveState()

    page_width = config.format.width_pt
    margin_left = config.margins.left_pt
    margin_right = config.margins.right_pt
    footer_y = config.margins.bottom_pt - 5

    # Horizontale lijn
    line_y = footer_y + 10
    canvas.setStrokeColor(BM_COLORS.rule)
    canvas.setLineWidth(0.5)
    canvas.line(margin_left, line_y, page_width - margin_right, line_y)

    # Bedrijfsnaam links
    canvas.setFont(BM_FONTS.body, 7)
    canvas.setFillColor(BM_COLORS.text_light)
    canvas.drawString(margin_left, footer_y, config.author)

    # Paginanummer rechts
    page_num = canvas.getPageNumber()
    canvas.drawRightString(
        page_width - margin_right,
        footer_y,
        f"Pagina {page_num}",
    )

    canvas.restoreState()


def create_page_templates(config: DocumentConfig) -> list[PageTemplate]:
    """Maak PageTemplates voor het document.

    Returns:
        Lijst met templates: [cover, content, backcover].
    """
    page_w = config.format.width_pt
    page_h = config.format.height_pt
    ml = config.margins.left_pt
    mr = config.margins.right_pt
    mt = config.margins.top_pt
    mb = config.margins.bottom_pt

    # Header en footer ruimte (in points)
    header_h = 15 * MM_TO_PT
    footer_h = 12 * MM_TO_PT

    # Cover: volledig pagina frame, geen header/footer
    cover_frame = Frame(
        ml, mb, page_w - ml - mr, page_h - mt - mb,
        id="cover_frame",
    )
    cover_template = PageTemplate(
        id="cover",
        frames=[cover_frame],
        # Geen onPage callback = geen header/footer
    )

    # Content: frame met ruimte voor header en footer
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
        onPage=lambda canvas, doc: _on_content_page(canvas, doc, config),
    )

    # Achterblad: volledig pagina frame, geen header/footer
    backcover_frame = Frame(
        ml, mb, page_w - ml - mr, page_h - mt - mb,
        id="backcover_frame",
    )
    backcover_template = PageTemplate(
        id="backcover",
        frames=[backcover_frame],
    )

    return [cover_template, content_template, backcover_template]


def _on_content_page(canvas, doc, config: DocumentConfig):
    """Callback voor content pagina's — tekent header en footer."""
    _draw_header(canvas, doc, config)
    _draw_footer(canvas, doc, config)
