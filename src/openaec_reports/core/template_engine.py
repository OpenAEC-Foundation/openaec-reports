"""Template-driven report engine (v2).

Bouwt PDF rapporten op basis van template YAML configuratie.
Drie pagina-modes:
- special: stationery + text zones (voorblad, achterblad)
- fixed:   stationery + text zones + tabel op vaste positie (BIC controles)
- flow:    stationery + ReportLab flowables (OpenAEC inhoudspagina's)

Gebruikt Optie C: alles via ReportLab DocTemplate.
Special/fixed pagina's zijn PageTemplates met onPage callbacks.
Flow pagina's gebruiken standaard ReportLab flowable paginering.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
)

from openaec_reports.core.document import A4, MM_TO_PT
from openaec_reports.core.fonts import get_font_name, register_tenant_fonts
from openaec_reports.core.stationery import StationeryRenderer
from openaec_reports.core.template_config import (
    ContentFrame,
    ImageZone,
    LineZone,
    PageDef,
    PageType,
    TableConfig,
    TemplateConfig,
    TextZone,
)
from openaec_reports.core.template_resolver import TemplateResolver

logger = logging.getLogger(__name__)

# A4 afmetingen in points
A4_W = A4.width_pt
A4_H = A4.height_pt


# ============================================================
# Data binding
# ============================================================


def resolve_bind(data: dict[str, Any], path: str) -> Any:
    """Resolve dot-notatie pad naar waarde in data dict.

    Special prefixes:
    - ``_static.<label>``: returns the label text literally (not from data).
    - ``_page_number``: returns None here; handled by _draw_text_zones.
    """
    if not path:
        return None
    # _static.* → literal label text
    if path.startswith("_static."):
        return path[8:]
    parts = path.split(".")
    current: Any = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def format_value(value: Any, fmt: str | None = None) -> str:
    """Format een waarde voor display."""
    if value is None:
        return ""
    if fmt == "currency_nl":
        try:
            v = float(value)
            formatted = (
                f"{v:,.2f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )
            return f"\u20ac {formatted}"
        except (ValueError, TypeError):
            return str(value)
    return str(value)


# ============================================================
# Rendering helpers (module-level, geen forward refs)
# ============================================================


def _get_pagesize(orientation: str) -> tuple[float, float]:
    """Geef A4 pagesize in points voor gegeven orientatie."""
    if orientation == "landscape":
        return (A4_H, A4_W)
    return (A4_W, A4_H)


def _resolve_font(font_ref: str, brand) -> str:
    """Resolve font referentie naar ReportLab font naam.

    Lookup order:
    1. Direct match in brand.fonts dict (heading, body, heading_bold, etc.)
    2. Fallback heuristics for heading_bold / body_bold
    3. Treat font_ref as literal ReportLab font name
    """
    if font_ref in brand.fonts:
        font_name = brand.fonts[font_ref]
    elif font_ref == "heading_bold":
        font_name = brand.fonts.get("heading", "Helvetica-Bold")
    elif font_ref == "body_bold":
        base = brand.fonts.get("body", "Helvetica")
        font_name = base + "-Bold" if not base.endswith("Bold") else base
    else:
        font_name = font_ref
    try:
        return get_font_name(font_name)
    except Exception:
        return font_name


def _resolve_color(color_ref: str, brand) -> HexColor:
    """Resolve kleur referentie naar HexColor."""
    if color_ref in ("primary", "secondary", "text", "white", "accent"):
        hex_val = brand.colors.get(color_ref, "#000000")
    elif color_ref.startswith("#"):
        hex_val = color_ref
    else:
        hex_val = brand.colors.get(color_ref, "#000000")
    return HexColor(hex_val)


def _draw_text_zones(
    canvas,
    text_zones: list[TextZone],
    data: dict[str, Any],
    brand,
    page_height: float,
    ctx: _BuildContext | None = None,
) -> None:
    """Vul text zones in op het canvas (top-down mm → bottom-up pt).

    YAML y_mm is gemeten als bbox-top (PyMuPDF top-down).
    ReportLab drawString tekent op de baseline.
    Correctie: rl_y = page_height - y_td - ascent.
    """
    from reportlab.pdfbase import pdfmetrics

    for zone in text_zones:
        if zone.bind == "_page_number":
            if ctx:
                abs_page = canvas.getPageNumber()
                content_n = abs_page - ctx.page_number_offset
                total = ctx.content_page_count
                value = f"Pagina {content_n} van {total}"
            else:
                value = str(canvas.getPageNumber())
        else:
            value = resolve_bind(data, zone.bind)
        if not value:
            continue

        text = str(value)
        font_name = _resolve_font(zone.font, brand)
        color = _resolve_color(zone.color, brand)

        x = zone.x_mm * MM_TO_PT
        y_td = zone.y_mm * MM_TO_PT  # top-down: bbox top

        # Corrigeer voor font ascent (bbox top → baseline)
        try:
            ascent = pdfmetrics.getAscent(font_name, zone.size)
        except Exception:
            ascent = zone.size * 0.77  # safe fallback
        rl_y = page_height - y_td - ascent

        canvas.saveState()
        canvas.setFont(font_name, zone.size)
        canvas.setFillColor(color)

        if zone.align == "right":
            canvas.drawRightString(x, rl_y, text)
        elif zone.align == "center":
            canvas.drawCentredString(x, rl_y, text)
        else:
            canvas.drawString(x, rl_y, text)

        canvas.restoreState()


def _draw_image_zones(
    canvas,
    image_zones: list[ImageZone],
    data: dict[str, Any],
    page_height: float,
    assets_dir: Path | None = None,
) -> None:
    """Teken afbeeldingen op vaste posities op het canvas."""
    for zone in image_zones:
        img_src = resolve_bind(data, zone.bind)
        if not img_src and zone.fallback and assets_dir:
            fallback_path = assets_dir / zone.fallback
            if fallback_path.exists():
                img_src = str(fallback_path)
        if not img_src:
            continue

        img_path = Path(str(img_src))
        if not img_path.exists():
            logger.warning("Image zone niet gevonden: %s", img_src)
            continue

        x = zone.x_mm * MM_TO_PT
        w = zone.width_mm * MM_TO_PT
        h = zone.height_mm * MM_TO_PT
        y = page_height - (zone.y_mm * MM_TO_PT) - h  # ReportLab y = bottom-left

        try:
            canvas.drawImage(
                str(img_path), x, y, width=w, height=h,
                preserveAspectRatio=True, anchor="nw", mask="auto",
            )
        except Exception:
            logger.exception("Image zone render fout: %s", img_src)


def _draw_line_zones(
    canvas,
    line_zones: list[LineZone],
    brand,
    page_height: float,
) -> None:
    """Teken decoratieve lijnen op het canvas.

    Horizontale lijnen op vaste posities — gebruikt voor sectie-scheiding
    en subtotaal-lijnen in Customer BIC facturen.

    YAML y_mm is top-down. ReportLab y is bottom-up.
    """
    for zone in line_zones:
        x0 = zone.x0_mm * MM_TO_PT
        x1 = zone.x1_mm * MM_TO_PT
        rl_y = page_height - (zone.y_mm * MM_TO_PT)

        color = _resolve_color(zone.color, brand)

        canvas.saveState()
        canvas.setStrokeColor(color)
        canvas.setLineWidth(zone.width_pt)
        canvas.line(x0, rl_y, x1, rl_y)
        canvas.restoreState()


def _truncate_text(canvas, text: str, max_width: float, font_name: str, size: float, padding: float = 2.0) -> str:
    """Truncate tekst met ellipsis als deze breder is dan max_width.

    Args:
        canvas: ReportLab canvas (voor stringWidth berekening).
        text: Originele tekst.
        max_width: Maximale breedte in points.
        font_name: Font naam.
        size: Font grootte.
        padding: Extra marge in points om overlap te voorkomen.

    Returns:
        Originele tekst of afgebroken tekst met "…".
    """
    from reportlab.pdfbase.pdfmetrics import stringWidth

    usable = max_width - padding
    if usable <= 0:
        return ""
    if stringWidth(text, font_name, size) <= usable:
        return text

    ellipsis = "…"
    ew = stringWidth(ellipsis, font_name, size)
    for i in range(len(text), 0, -1):
        if stringWidth(text[:i], font_name, size) + ew <= usable:
            return text[:i] + ellipsis
    return ellipsis


def _draw_table(
    canvas,
    table_config: TableConfig,
    rows: list[dict[str, Any]],
    brand,
    page_height: float,
) -> None:
    """Teken een transparante tabel met vaste kolommen op canvas."""
    x_origin = table_config.origin_x_mm * MM_TO_PT
    row_h = table_config.row_height_mm * MM_TO_PT
    total_w = sum(c.width_mm for c in table_config.columns) * MM_TO_PT

    y_td = table_config.origin_y_mm * MM_TO_PT  # top-down in pt

    # Optionele kolomkoppen
    if table_config.show_header:
        rl_y = page_height - y_td

        # Header achtergrondkleur
        if table_config.header_bg:
            canvas.saveState()
            canvas.setFillColor(_resolve_color(table_config.header_bg, brand))
            canvas.rect(x_origin, rl_y - row_h * 0.3, total_w, row_h, fill=1, stroke=0)
            canvas.restoreState()

        canvas.saveState()
        header_font = _resolve_font(table_config.header_font, brand)
        header_color = _resolve_color(table_config.header_color, brand)
        canvas.setFont(header_font, table_config.header_size)
        canvas.setFillColor(header_color)

        x = x_origin
        for col in table_config.columns:
            col_w = col.width_mm * MM_TO_PT
            header_text = col.header or col.field

            if col.align == "right":
                canvas.drawRightString(x + col_w, rl_y, header_text)
            elif col.align == "center":
                canvas.drawCentredString(x + col_w / 2, rl_y, header_text)
            else:
                canvas.drawString(x, rl_y, header_text)
            x += col_w

        canvas.restoreState()
        y_td += row_h

    # Data rijen
    for row_idx, row in enumerate(rows):
        rl_y = page_height - y_td
        x = x_origin

        # Alternerende rijkleur
        if table_config.alt_row_bg and row_idx % 2 == 1:
            canvas.saveState()
            canvas.setFillColor(_resolve_color(table_config.alt_row_bg, brand))
            canvas.rect(x_origin, rl_y - row_h * 0.3, total_w, row_h, fill=1, stroke=0)
            canvas.restoreState()

        for col in table_config.columns:
            col_w = col.width_mm * MM_TO_PT
            raw_value = row.get(col.field, "")
            text = format_value(raw_value, col.format)

            if text:
                canvas.saveState()
                # Body overrides op TableConfig niveau
                font_ref = table_config.body_font or col.font
                color_ref = table_config.body_color or col.color
                size = table_config.body_size or col.size

                font_name = _resolve_font(font_ref, brand)
                color = _resolve_color(color_ref, brand)
                canvas.setFont(font_name, size)
                canvas.setFillColor(color)

                # Truncate tekst als deze breder is dan de kolom
                text = _truncate_text(canvas, text, col_w, font_name, size)

                if col.align == "right":
                    canvas.drawRightString(x + col_w, rl_y, text)
                elif col.align == "center":
                    canvas.drawCentredString(x + col_w / 2, rl_y, text)
                else:
                    canvas.drawString(x, rl_y, text)

                canvas.restoreState()
            x += col_w

        # Grid lijnen
        if table_config.grid_color:
            canvas.saveState()
            canvas.setStrokeColor(_resolve_color(table_config.grid_color, brand))
            canvas.setLineWidth(0.25)
            canvas.line(x_origin, rl_y - row_h * 0.3, x_origin + total_w, rl_y - row_h * 0.3)
            canvas.restoreState()

        y_td += row_h


def _paginate_table_data(
    rows: list[dict[str, Any]],
    table_config: TableConfig,
) -> list[list[dict[str, Any]]]:
    """Verdeel tabelrijen over pagina's op basis van max_y."""
    if not rows:
        return []

    available_height_mm = table_config.max_y_mm - table_config.origin_y_mm
    rows_per_page = max(1, int(available_height_mm / table_config.row_height_mm))

    chunks = []
    for i in range(0, len(rows), rows_per_page):
        chunks.append(rows[i:i + rows_per_page])
    return chunks


# ============================================================
# Build context (vóór engine class)
# ============================================================


class _BuildContext:
    """Interne context voor de build operatie."""

    __slots__ = (
        "template", "page_types", "data", "brand",
        "stationery", "stationery_dir",
        "content_page_count", "page_number_offset",
    )

    def __init__(
        self,
        template: TemplateConfig,
        page_types: dict[str, PageType],
        data: dict[str, Any],
        brand,
        stationery: StationeryRenderer,
        stationery_dir: Path,
    ):
        self.template = template
        self.page_types = page_types
        self.data = data
        self.brand = brand
        self.stationery = stationery
        self.stationery_dir = stationery_dir
        self.content_page_count: int = 0
        self.page_number_offset: int = 0


# ============================================================
# Template Engine
# ============================================================


class TemplateEngine:
    """Template-driven report generator.

    Usage::

        engine = TemplateEngine(tenants_dir=Path("tenants"))
        engine.build(
            template_name="bic_factuur",
            tenant="customer",
            data=json_data,
            output_path="output/factuur.pdf",
        )
    """

    def __init__(self, tenants_dir: Path | None = None):
        self._resolver = TemplateResolver(tenants_dir=tenants_dir)
        self._tenants_dir = tenants_dir or self._resolver._tenants_dir

    def build(
        self,
        template_name: str,
        tenant: str,
        data: dict[str, Any],
        output_path: str | Path,
        brand=None,
    ) -> Path:
        """Genereer een PDF rapport op basis van template + data.

        Args:
            template_name: Naam van de template YAML.
            tenant: Tenant identifier.
            data: JSON data dict.
            output_path: Pad voor output PDF.
            brand: Optioneel BrandConfig of brand naam (str).

        Returns:
            Path naar gegenereerd PDF bestand.
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        # Laad configuratie
        template = self._resolver.load_template(template_name, tenant)
        page_types = self._resolver.load_all_page_types(template)

        # Brand laden
        from openaec_reports.core.brand import BrandConfig, BrandLoader

        if isinstance(brand, BrandConfig):
            brand_config = brand
        elif isinstance(brand, str):
            brand_config = BrandLoader(tenants_root=self._tenants_dir).load(brand)
        else:
            brand_config = self._load_tenant_brand(tenant)

        # Registreer tenant-specifieke fonts (vóór eerste pagina)
        font_files = getattr(brand_config, "font_files", None)
        if font_files and isinstance(font_files, dict):
            fonts_dir = self._tenants_dir / tenant
            register_tenant_fonts(font_files, fonts_dir)

        # Stationery renderer met tenant stationery dir
        stationery_dir = self._tenants_dir / tenant / "stationery"
        stationery = StationeryRenderer(brand_dir=stationery_dir)

        ctx = _BuildContext(
            template=template,
            page_types=page_types,
            data=data,
            brand=brand_config,
            stationery=stationery,
            stationery_dir=stationery_dir,
        )

        # Bereken content paginanummering (excl cover)
        cover_pages = 0
        content_pages = 0
        for page_def in template.pages:
            pt = page_types[page_def.page_type]
            if page_def.type == "special" and cover_pages == 0:
                # Eerste special page = cover (telt niet mee)
                cover_pages = 1
            elif page_def.type == "fixed" and page_def.repeat == "auto" and pt.table:
                table_data = resolve_bind(data, pt.table.data_bind) or []
                chunks = _paginate_table_data(table_data, pt.table)
                content_pages += max(1, len(chunks))
            else:
                content_pages += 1
        ctx.content_page_count = content_pages
        ctx.page_number_offset = cover_pages

        self._build_pdf(ctx, output)

        logger.info("PDF gegenereerd: %s", output)
        return output

    def _load_tenant_brand(self, tenant: str):
        """Laad brand.yaml uit tenant directory."""
        from openaec_reports.core.brand import BrandLoader
        brand_path = self._tenants_dir / tenant / "brand.yaml"
        if brand_path.exists():
            loader = BrandLoader(tenants_root=self._tenants_dir)
            return loader.load(tenant)
        return BrandLoader(tenants_root=self._tenants_dir).load_default()

    def _build_pdf(self, ctx: _BuildContext, output: Path) -> None:
        """Bouw PDF via ReportLab DocTemplate (Optie C).

        Elke pagina-definitie wordt een PageTemplate.
        Special/fixed: onPage callback tekent alles, Spacer als trigger.
        Flow: flowables in content frame.
        """
        self._pending_chunk_templates: list[PageTemplate] = []

        first_page = ctx.template.pages[0] if ctx.template.pages else None
        initial_pagesize = _get_pagesize(
            first_page.orientation if first_page else "portrait",
        )

        doc = BaseDocTemplate(
            filename=str(output),
            pagesize=initial_pagesize,
            topMargin=0,
            bottomMargin=0,
            leftMargin=0,
            rightMargin=0,
        )

        # Registreer basis PageTemplates + bouw elements
        base_templates = []
        template_info = []

        for i, page_def in enumerate(ctx.template.pages):
            page_type = ctx.page_types[page_def.page_type]
            template_id = f"page_{i}_{page_def.page_type}"
            pagesize = _get_pagesize(page_def.orientation)

            if page_def.type == "fixed" and page_def.repeat == "auto":
                # Chunk templates worden in _build_elements aangemaakt
                template_info.append((template_id, None, page_def, page_type))
            elif page_def.type in ("special", "fixed"):
                pt = self._make_special_fixed_pt(
                    template_id, page_def, page_type, pagesize, ctx,
                )
                base_templates.append(pt)
                template_info.append((template_id, pt, page_def, page_type))
            elif page_def.type in ("flow", "toc"):
                pt = self._make_flow_pt(
                    template_id, page_def, page_type, pagesize, ctx,
                )
                base_templates.append(pt)
                template_info.append((template_id, pt, page_def, page_type))

        # Bouw elements (chunk templates worden bijgemaakt)
        elements = self._build_elements(template_info, ctx)

        # Alle templates combineren
        all_templates = base_templates + self._pending_chunk_templates
        if not all_templates:
            logger.warning("Geen page templates — leeg document")
            return

        doc.addPageTemplates(all_templates)
        doc.build(elements)

    # ----------------------------------------------------------
    # PageTemplate factory methods
    # ----------------------------------------------------------

    def _make_special_fixed_pt(
        self,
        template_id: str,
        page_def: PageDef,
        page_type: PageType,
        pagesize: tuple[float, float],
        ctx: _BuildContext,
    ) -> PageTemplate:
        """PageTemplate voor special/fixed (geen repeat)."""
        pw, ph = pagesize
        frame = Frame(0, 0, pw, ph, id=f"f_{template_id}",
                       leftPadding=0, rightPadding=0,
                       topPadding=0, bottomPadding=0)

        def on_page(canvas, doc, _pd=page_def, _pt=page_type, _pw=pw, _ph=ph, _ctx=ctx):
            canvas.setPageSize((_pw, _ph))
            if _pt.stationery:
                _ctx.stationery.draw(canvas, _pt.stationery, _pw, _ph)
            if _pt.line_zones:
                _draw_line_zones(canvas, _pt.line_zones, _ctx.brand, _ph)
            _draw_text_zones(canvas, _pt.text_zones, _ctx.data, _ctx.brand, _ph, _ctx)
            if _pt.image_zones:
                assets_dir = _ctx.stationery_dir.parent / "assets"
                _draw_image_zones(canvas, _pt.image_zones, _ctx.data, _ph, assets_dir)
            # Fixed zonder repeat: tabel direct tekenen
            if _pd.type == "fixed" and _pt.table:
                rows = resolve_bind(_ctx.data, _pt.table.data_bind)
                if rows:
                    _draw_table(canvas, _pt.table, rows, _ctx.brand, _ph)

        return PageTemplate(
            id=template_id, frames=[frame], pagesize=pagesize, onPage=on_page,
        )

    def _make_flow_pt(
        self,
        template_id: str,
        page_def: PageDef,
        page_type: PageType,
        pagesize: tuple[float, float],
        ctx: _BuildContext,
    ) -> PageTemplate:
        """PageTemplate voor flow pagina's."""
        pw, ph = pagesize
        cf = page_type.content_frame or ContentFrame()

        frame = Frame(
            cf.x_mm * MM_TO_PT,
            ph - (cf.y_mm + cf.height_mm) * MM_TO_PT,
            cf.width_mm * MM_TO_PT,
            cf.height_mm * MM_TO_PT,
            id=f"f_{template_id}",
        )

        def on_page(canvas, doc, _pt=page_type, _pw=pw, _ph=ph, _ctx=ctx):
            canvas.setPageSize((_pw, _ph))
            if _pt.stationery:
                _ctx.stationery.draw(canvas, _pt.stationery, _pw, _ph)

        return PageTemplate(
            id=template_id, frames=[frame], pagesize=pagesize, onPage=on_page,
        )

    def _make_fixed_chunk_pt(
        self,
        template_id: str,
        page_def: PageDef,
        page_type: PageType,
        pagesize: tuple[float, float],
        ctx: _BuildContext,
        chunk: list[dict],
    ) -> PageTemplate:
        """PageTemplate voor een chunk van tabeldata (fixed + repeat:auto)."""
        pw, ph = pagesize
        frame = Frame(0, 0, pw, ph, id=f"f_{template_id}",
                       leftPadding=0, rightPadding=0,
                       topPadding=0, bottomPadding=0)

        def on_page(canvas, doc, _pt=page_type, _pw=pw, _ph=ph,
                     _chunk=chunk, _ctx=ctx):
            canvas.setPageSize((_pw, _ph))
            if _pt.stationery:
                _ctx.stationery.draw(canvas, _pt.stationery, _pw, _ph)
            if _pt.line_zones:
                _draw_line_zones(canvas, _pt.line_zones, _ctx.brand, _ph)
            _draw_text_zones(canvas, _pt.text_zones, _ctx.data, _ctx.brand, _ph, _ctx)
            if _pt.image_zones:
                assets_dir = _ctx.stationery_dir.parent / "assets"
                _draw_image_zones(canvas, _pt.image_zones, _ctx.data, _ph, assets_dir)
            if _pt.table and _chunk:
                _draw_table(canvas, _pt.table, _chunk, _ctx.brand, _ph)

        return PageTemplate(
            id=template_id, frames=[frame], pagesize=pagesize, onPage=on_page,
        )

    # ----------------------------------------------------------
    # Elements builder
    # ----------------------------------------------------------

    def _build_elements(
        self,
        template_info: list[tuple[str, PageTemplate | None, PageDef, PageType]],
        ctx: _BuildContext,
    ) -> list:
        """Bouw de volledige elements list voor ReportLab."""
        elements: list = []
        first = True

        for template_id, pt, page_def, page_type in template_info:

            if page_def.type == "special":
                elements.append(NextPageTemplate(template_id))
                if not first:
                    elements.append(PageBreak())
                elements.append(Spacer(1, 1))
                first = False

            elif page_def.type == "fixed":
                if page_def.repeat == "auto" and page_type.table:
                    table_data = resolve_bind(ctx.data, page_type.table.data_bind) or []
                    chunks = _paginate_table_data(table_data, page_type.table)
                    if not chunks:
                        chunks = [[]]

                    pagesize = _get_pagesize(page_def.orientation)

                    for ci, chunk in enumerate(chunks):
                        chunk_id = f"{template_id}_c{ci}"
                        chunk_pt = self._make_fixed_chunk_pt(
                            chunk_id, page_def, page_type, pagesize, ctx, chunk,
                        )
                        self._pending_chunk_templates.append(chunk_pt)

                        elements.append(NextPageTemplate(chunk_id))
                        if not first:
                            elements.append(PageBreak())
                        elements.append(Spacer(1, 1))
                        first = False
                else:
                    elements.append(NextPageTemplate(template_id))
                    if not first:
                        elements.append(PageBreak())
                    elements.append(Spacer(1, 1))
                    first = False

            elif page_def.type == "flow":
                elements.append(NextPageTemplate(template_id))
                if not first:
                    elements.append(PageBreak())
                first = False

                flow = self._build_flow_content(ctx)
                if flow:
                    elements.extend(flow)
                else:
                    elements.append(Spacer(1, 1))

            elif page_def.type == "toc":
                elements.append(NextPageTemplate(template_id))
                if not first:
                    elements.append(PageBreak())
                first = False
                elements.append(Spacer(1, 20))  # placeholder

        return elements

    def _build_flow_content(self, ctx: _BuildContext) -> list:
        """Bouw flowable content uit data["sections"]."""
        elements: list = []

        sections = ctx.data.get("sections", [])
        if not sections:
            return elements

        try:
            from openaec_reports.core.styles import create_stylesheet
            styles = create_stylesheet(brand=ctx.brand)
        except Exception:
            from reportlab.lib.styles import getSampleStyleSheet
            styles = getSampleStyleSheet()

        for section_data in sections:
            title = section_data.get("title", "")
            level = section_data.get("level", 1)

            if title:
                style_name = f"Heading{level}"
                style = styles.get(style_name, styles.get("Heading1", styles["Normal"]))
                elements.append(Paragraph(title, style))

            for block_data in section_data.get("content", []):
                text = block_data.get("text", "")
                if text:
                    elements.append(Paragraph(text, styles.get("Normal", styles["Normal"])))

            elements.append(Spacer(1, 6))

        return elements
