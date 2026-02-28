"""Template-driven report engine (v2).

Bouwt PDF rapporten op basis van template YAML configuratie.
Drie pagina-modes:
- special: stationery + text zones (voorblad, achterblad)
- fixed:   stationery + text zones + tabel op vaste positie (BIC controles)
- flow:    stationery + ReportLab flowables (3BM inhoudspagina's)

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

from bm_reports.core.document import A4, MM_TO_PT
from bm_reports.core.stationery import StationeryRenderer
from bm_reports.core.template_config import (
    ContentFrame,
    PageDef,
    PageType,
    TableConfig,
    TemplateConfig,
    TextZone,
)
from bm_reports.core.template_resolver import TemplateResolver

logger = logging.getLogger(__name__)

# A4 afmetingen in points
A4_W = A4.width_pt
A4_H = A4.height_pt


# ============================================================
# Data binding
# ============================================================


def resolve_bind(data: dict[str, Any], path: str) -> Any:
    """Resolve dot-notatie pad naar waarde in data dict."""
    if not path:
        return None
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
    """Resolve font referentie naar ReportLab font naam."""
    if font_ref in ("heading", "body"):
        font_name = brand.fonts.get(font_ref, "Helvetica")
    else:
        font_name = font_ref
    try:
        from bm_reports.core.fonts import get_font_name
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
) -> None:
    """Vul text zones in op het canvas (top-down mm → bottom-up pt)."""
    for zone in text_zones:
        value = resolve_bind(data, zone.bind)
        if not value:
            continue

        text = str(value)
        font_name = _resolve_font(zone.font, brand)
        color = _resolve_color(zone.color, brand)

        x = zone.x_mm * MM_TO_PT
        rl_y = page_height - (zone.y_mm * MM_TO_PT)

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

    y_td = table_config.origin_y_mm * MM_TO_PT  # top-down in pt

    # Optionele kolomkoppen
    if table_config.show_header:
        canvas.saveState()
        header_font = _resolve_font(table_config.header_font, brand)
        header_color = _resolve_color(table_config.header_color, brand)
        canvas.setFont(header_font, table_config.header_size)
        canvas.setFillColor(header_color)

        x = x_origin
        for col in table_config.columns:
            col_w = col.width_mm * MM_TO_PT
            rl_y = page_height - y_td

            if col.align == "right":
                canvas.drawRightString(x + col_w, rl_y, col.field)
            elif col.align == "center":
                canvas.drawCentredString(x + col_w / 2, rl_y, col.field)
            else:
                canvas.drawString(x, rl_y, col.field)
            x += col_w

        canvas.restoreState()
        y_td += row_h

    # Data rijen
    for row in rows:
        rl_y = page_height - y_td
        x = x_origin
        for col in table_config.columns:
            col_w = col.width_mm * MM_TO_PT
            raw_value = row.get(col.field, "")
            text = format_value(raw_value, col.format)

            if text:
                canvas.saveState()
                font_name = _resolve_font(col.font, brand)
                color = _resolve_color(col.color, brand)
                canvas.setFont(font_name, col.size)
                canvas.setFillColor(color)

                if col.align == "right":
                    canvas.drawRightString(x + col_w, rl_y, text)
                elif col.align == "center":
                    canvas.drawCentredString(x + col_w / 2, rl_y, text)
                else:
                    canvas.drawString(x, rl_y, text)

                canvas.restoreState()
            x += col_w
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


# ============================================================
# Template Engine
# ============================================================


class TemplateEngine:
    """Template-driven report generator.

    Usage::

        engine = TemplateEngine(tenants_dir=Path("tenants"))
        engine.build(
            template_name="bic_factuur",
            tenant="symitech",
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
        from bm_reports.core.brand import BrandConfig, BrandLoader

        if isinstance(brand, BrandConfig):
            brand_config = brand
        elif isinstance(brand, str):
            brand_config = BrandLoader(tenants_root=self._tenants_dir).load(brand)
        else:
            brand_config = self._load_tenant_brand(tenant)

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

        self._build_pdf(ctx, output)

        logger.info("PDF gegenereerd: %s", output)
        return output

    def _load_tenant_brand(self, tenant: str):
        """Laad brand.yaml uit tenant directory."""
        from bm_reports.core.brand import BrandLoader
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
            _draw_text_zones(canvas, _pt.text_zones, _ctx.data, _ctx.brand, _ph)
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
            _draw_text_zones(canvas, _pt.text_zones, _ctx.data, _ctx.brand, _ph)
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
                if not first:
                    elements.append(PageBreak())
                elements.append(NextPageTemplate(template_id))
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

                        if not first:
                            elements.append(PageBreak())
                        elements.append(NextPageTemplate(chunk_id))
                        elements.append(Spacer(1, 1))
                        first = False
                else:
                    if not first:
                        elements.append(PageBreak())
                    elements.append(NextPageTemplate(template_id))
                    elements.append(Spacer(1, 1))
                    first = False

            elif page_def.type == "flow":
                if not first:
                    elements.append(PageBreak())
                elements.append(NextPageTemplate(template_id))
                first = False

                flow = self._build_flow_content(ctx)
                if flow:
                    elements.extend(flow)
                else:
                    elements.append(Spacer(1, 1))

            elif page_def.type == "toc":
                if not first:
                    elements.append(PageBreak())
                elements.append(NextPageTemplate(template_id))
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
            from bm_reports.core.styles import create_stylesheet
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
