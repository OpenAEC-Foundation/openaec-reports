"""Template-driven report configuratie.

Dataclasses voor het laden van template YAML's en page_type YAML's.
Templates definiëren documentstructuur (volgorde pagina's).
Page types definiëren wat er op elke pagina komt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class TextZone:
    """Tekstveld op een vaste positie op de pagina."""

    bind: str                          # dot-notatie pad in data: "client.name"
    x_mm: float = 0.0
    y_mm: float = 0.0                  # top-down (mm vanaf bovenkant)
    font: str = "body"                 # "heading", "body", of font naam
    size: float = 10.0
    color: str = "text"                # "primary", "secondary", "text", of hex
    align: Literal["left", "right", "center"] = "left"
    max_width_mm: float | None = None  # Maximale breedte — tekst wraps bij overschrijding
    line_height_mm: float = 4.2        # Regelafstand voor multi-line tekst


@dataclass
class ImageZone:
    """Afbeelding op een vaste positie op de pagina."""

    bind: str                          # dot-notatie pad naar afbeelding (pad of base64)
    x_mm: float = 0.0
    y_mm: float = 0.0                  # top-down (mm vanaf bovenkant)
    width_mm: float = 100.0
    height_mm: float = 70.0
    fallback: str = ""                 # fallback bestandsnaam in assets/


@dataclass
class LineZone:
    """Decoratieve lijn op een vaste positie op de pagina."""

    x0_mm: float = 0.0                # startpunt x (mm)
    y_mm: float = 0.0                  # y positie (top-down mm)
    x1_mm: float = 100.0              # eindpunt x (mm)
    width_pt: float = 1.0             # lijndikte in points
    color: str = "primary"            # kleur referentie of hex


@dataclass
class TableColumn:
    """Kolomdefinitie voor een fixed-page tabel."""

    field: str                         # key in data dict
    width_mm: float = 40.0
    align: Literal["left", "right", "center"] = "left"
    format: str | None = None          # "currency_nl", None = plain text
    font: str = "body"
    size: float = 9.0
    color: str = "text"
    header: str | None = None          # display naam voor kolomkop (fallback: field)


@dataclass
class TableConfig:
    """Tabelconfiguratie voor fixed pages."""

    data_bind: str                     # dot-notatie pad naar list in data
    columns: list[TableColumn] = field(default_factory=list)
    origin_x_mm: float = 20.0
    origin_y_mm: float = 60.0          # top-down
    row_height_mm: float = 5.6
    max_y_mm: float = 260.0            # ondergrens (top-down), daarna nieuwe pagina
    header_font: str = "heading"
    header_size: float = 9.0
    header_color: str = "text"
    show_header: bool = False          # kolomkoppen al in stationery
    header_bg: str | None = None       # achtergrondkleur kolomkoppen
    body_font: str | None = None       # override font voor data rijen
    body_size: float | None = None     # override size voor data rijen
    body_color: str | None = None      # override kleur voor data rijen
    alt_row_bg: str | None = None      # alternerende rij achtergrond
    grid_color: str | None = None      # tabel rasterlijnen


@dataclass
class ContentFrame:
    """Frame definitie voor flow-mode pagina's."""

    x_mm: float = 20.0
    y_mm: float = 25.0                 # top-down
    width_mm: float = 175.0
    height_mm: float = 247.0


@dataclass
class PageType:
    """Definitie van wat er op een pagina-type komt."""

    name: str
    stationery: str | None = None      # bestandsnaam in tenant stationery dir
    text_zones: list[TextZone] = field(default_factory=list)
    image_zones: list[ImageZone] = field(default_factory=list)
    line_zones: list[LineZone] = field(default_factory=list)
    table: TableConfig | None = None
    content_frame: ContentFrame | None = None  # voor flow mode
    flow_layout: bool = False                  # text zones verschuiven bij wrapping
    flow_footer_y_mm: float = 260.0            # zones >= deze y zijn footer (vast)


@dataclass
class PageDef:
    """Pagina in een template — verwijst naar een page_type."""

    type: Literal["special", "fixed", "flow", "toc"]
    page_type: str                     # naam → resolves naar PageType
    orientation: Literal["portrait", "landscape"] = "portrait"
    repeat: Literal["auto", "none"] = "none"  # auto = pagineer tabeldata


@dataclass
class TemplateConfig:
    """Documentstructuur — volgorde van pagina's."""

    name: str
    tenant: str
    pages: list[PageDef] = field(default_factory=list)


# ============================================================
# Parsing helpers
# ============================================================


def parse_text_zone(data: dict[str, Any]) -> TextZone:
    """Parse een text zone dict naar TextZone dataclass."""
    max_w = data.get("max_width_mm")
    return TextZone(
        bind=data["bind"],
        x_mm=float(data.get("x_mm", 0)),
        y_mm=float(data.get("y_mm", 0)),
        font=data.get("font", "body"),
        size=float(data.get("size", 10)),
        color=data.get("color", "text"),
        align=data.get("align", "left"),
        max_width_mm=float(max_w) if max_w is not None else None,
        line_height_mm=float(data.get("line_height_mm", 4.2)),
    )


def parse_image_zone(data: dict[str, Any]) -> ImageZone:
    """Parse een image zone dict naar ImageZone dataclass."""
    return ImageZone(
        bind=data["bind"],
        x_mm=float(data.get("x_mm", 0)),
        y_mm=float(data.get("y_mm", 0)),
        width_mm=float(data.get("width_mm", 100)),
        height_mm=float(data.get("height_mm", 70)),
        fallback=data.get("fallback", ""),
    )


def parse_line_zone(data: dict[str, Any]) -> LineZone:
    """Parse een line zone dict naar LineZone dataclass."""
    return LineZone(
        x0_mm=float(data.get("x0_mm", 0)),
        y_mm=float(data.get("y_mm", 0)),
        x1_mm=float(data.get("x1_mm", 100)),
        width_pt=float(data.get("width_pt", 1.0)),
        color=data.get("color", "primary"),
    )


def parse_table_column(data: dict[str, Any]) -> TableColumn:
    """Parse een tabel kolom dict naar TableColumn dataclass."""
    return TableColumn(
        field=data["field"],
        width_mm=float(data.get("width_mm", 40)),
        align=data.get("align", "left"),
        format=data.get("format"),
        font=data.get("font", "body"),
        size=float(data.get("size", 9)),
        color=data.get("color", "text"),
        header=data.get("header"),
    )


def parse_table_config(data: dict[str, Any]) -> TableConfig:
    """Parse een tabel config dict naar TableConfig dataclass."""
    origin = data.get("origin", {})
    body_size_raw = data.get("body_size")
    return TableConfig(
        data_bind=data["data_bind"],
        columns=[parse_table_column(c) for c in data.get("columns", [])],
        origin_x_mm=float(origin.get("x_mm", 20)),
        origin_y_mm=float(origin.get("y_mm", 60)),
        row_height_mm=float(data.get("row_height_mm", 5.6)),
        max_y_mm=float(data.get("max_y_mm", 260)),
        header_font=data.get("header_font", "heading"),
        header_size=float(data.get("header_size", 9)),
        header_color=data.get("header_color", "text"),
        show_header=data.get("show_header", False),
        header_bg=data.get("header_bg"),
        body_font=data.get("body_font"),
        body_size=float(body_size_raw) if body_size_raw is not None else None,
        body_color=data.get("body_color"),
        alt_row_bg=data.get("alt_row_bg"),
        grid_color=data.get("grid_color"),
    )


def parse_content_frame(data: dict[str, Any]) -> ContentFrame:
    """Parse een content frame dict naar ContentFrame dataclass."""
    return ContentFrame(
        x_mm=float(data.get("x_mm", 20)),
        y_mm=float(data.get("y_mm", 25)),
        width_mm=float(data.get("width_mm", 175)),
        height_mm=float(data.get("height_mm", 247)),
    )


def parse_page_type(data: dict[str, Any]) -> PageType:
    """Parse een page_type YAML dict naar PageType dataclass."""
    pt = PageType(
        name=data.get("name", "unknown"),
        stationery=data.get("stationery"),
    )

    if "text_zones" in data:
        pt.text_zones = [parse_text_zone(z) for z in data["text_zones"]]

    if "image_zones" in data:
        pt.image_zones = [parse_image_zone(z) for z in data["image_zones"]]

    if "line_zones" in data:
        pt.line_zones = [parse_line_zone(z) for z in data["line_zones"]]

    if "table" in data:
        pt.table = parse_table_config(data["table"])

    if "content_frame" in data:
        pt.content_frame = parse_content_frame(data["content_frame"])

    if "flow_layout" in data:
        pt.flow_layout = bool(data["flow_layout"])
    if "flow_footer_y_mm" in data:
        pt.flow_footer_y_mm = float(data["flow_footer_y_mm"])

    return pt


def parse_page_def(data: dict[str, Any]) -> PageDef:
    """Parse een page definitie uit template YAML."""
    return PageDef(
        type=data["type"],
        page_type=data["page_type"],
        orientation=data.get("orientation", "portrait"),
        repeat=data.get("repeat", "none"),
    )


def parse_template_config(data: dict[str, Any]) -> TemplateConfig:
    """Parse een volledige template YAML naar TemplateConfig."""
    return TemplateConfig(
        name=data.get("name", "unknown"),
        tenant=data.get("tenant", ""),
        pages=[parse_page_def(p) for p in data.get("pages", [])],
    )
