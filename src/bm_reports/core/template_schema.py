"""Template schema — Dataclasses voor pixel-perfect pagina templates.

Definieert de structuur van template YAML bestanden:
    - TemplateConfig: Root met metadata, kleuren, fonts, pagina-types
    - PageConfig: Enkel pagina-type met geordende layers
    - Layer subclasses: RectLayer, TextLayer, ClippedImageLayer, etc.

Elke layer beschrijft een visueel element in PDF y-up coördinaten (origin = linksonder).
Dynamische velden worden aangeduid met `bind` (verwijzing naar rapport JSON data).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class LayerType(str, Enum):
    """Ondersteunde layer types voor de template renderer."""
    RECT = "rect"
    POLYGON = "polygon"
    CLIPPED_IMAGE = "clipped_image"
    IMAGE = "image"
    TEXT = "text"
    TEXT_BLOCK = "text_block"
    BADGE_GROUP = "badge_group"
    LINE = "line"
    TABLE = "table"
    PAGE_NUMBER = "page_number"


@dataclass
class LayerBase:
    """Basis voor alle layer types.

    Attrs:
        type: Layer type string.
        role: Semantische rol (bijv. 'background', 'title', 'logo').
        static: True = huisstijl element, False = dynamisch per rapport.
        bind: JSON pad voor dynamische waarde (bijv. 'cover.image').
        condition: Optionele conditie — layer wordt overgeslagen als bind-waarde leeg is.
    """
    type: str = ""
    role: str = ""
    static: bool = True
    bind: str = ""
    condition: str = ""


@dataclass
class RectLayer(LayerBase):
    """Gevulde rechthoek.

    Coördinaten in PDF y-up systeem (origin = linksonder pagina).
    """
    x: float = 0.0
    y: float = 0.0
    w: float = 0.0
    h: float = 0.0
    fill: str = ""          # Hex kleur of $colors.primary referentie
    stroke: str = ""
    stroke_width: float = 0.0
    radius: float = 0.0     # Hoekradius voor afgeronde hoeken


@dataclass
class PolygonLayer(LayerBase):
    """Gevuld polygon."""
    points: list[list[float]] = field(default_factory=list)  # [[x,y], [x,y], ...]
    fill: str = ""
    stroke: str = ""


@dataclass
class ImageLayer(LayerBase):
    """Statische afbeelding (logo, icoon)."""
    source: str = ""         # Pad relatief t.o.v. assets/
    x: float = 0.0
    y: float = 0.0
    w: float = 0.0
    h: float = 0.0
    mask: str = "auto"


@dataclass
class ClippedImageLayer(LayerBase):
    """Afbeelding met clip-path polygon (voor cover hero foto's)."""
    image_rect: dict = field(default_factory=dict)     # {x, y, w, h}
    clip_polygon: list[list[float]] = field(default_factory=list)  # [[x,y], ...]


@dataclass
class TextLayer(LayerBase):
    """Enkele tekstregel."""
    content: str = ""        # Statische tekst of "" als bind is gezet
    font: str = ""           # $fonts.heading of directe font naam
    size: float = 10.0
    color: str = ""          # Hex of $colors.primary
    x: float = 0.0
    y: float = 0.0           # PDF y-up baseline positie
    align: str = "left"      # left, center, right
    max_width: float = 0.0   # Max breedte voor auto-wrapping (0 = geen limiet)


@dataclass
class TextBlockLayer(LayerBase):
    """Meerdere tekst-spans op dezelfde regel (bijv. 'Ontdek ons ' + '3bm.co.nl')."""
    spans: list[dict] = field(default_factory=list)  # [{content, font, size, color, x, y}]


@dataclass
class BadgeConfig:
    """Enkel badge element."""
    text: str = ""
    fill: str = ""
    text_color: str = ""
    rect: list[float] = field(default_factory=list)  # [x, y, w, h]
    radius: float = 17.0
    font: str = ""
    font_size: float = 10.2
    icon: str = ""           # Optioneel icoon type


@dataclass
class BadgeGroupLayer(LayerBase):
    """Groep van rounded-rect badges met tekst."""
    badges: list[BadgeConfig] = field(default_factory=list)


@dataclass
class LineLayer(LayerBase):
    """Lijn of scheidingsstreep."""
    x1: float = 0.0
    y1: float = 0.0
    x2: float = 0.0
    y2: float = 0.0
    color: str = ""
    width: float = 0.5
    dash: list[float] = field(default_factory=list)


@dataclass
class PageNumberLayer(LayerBase):
    """Paginanummer element."""
    x: float = 0.0
    y: float = 0.0
    font: str = ""
    size: float = 8.0
    color: str = ""
    align: str = "right"


@dataclass
class TableLayer(LayerBase):
    """Twee-koloms metadata tabel (voor colofon)."""
    x: float = 0.0
    y_start: float = 0.0    # Startpositie eerste rij (y-down from top)
    col1_x: float = 0.0     # Label kolom x
    col2_x: float = 0.0     # Waarde kolom x
    row_height: float = 24.0 # Rijhoogte in pt
    label_font: str = ""
    label_size: float = 10.0
    label_color: str = ""
    value_font: str = ""
    value_size: float = 10.0
    value_color: str = ""
    separator_color: str = ""
    separator_width: float = 0.3
    separator_x_end: float = 0.0
    rows: list[dict] = field(default_factory=list)  # [{label, bind/value}]


# ============================================================
# Page and Template config
# ============================================================

@dataclass
class ContentFrameConfig:
    """Content frame definitie voor flowable content pagina's."""
    x: float = 0.0
    y: float = 0.0
    w: float = 0.0
    h: float = 0.0


@dataclass
class PageConfig:
    """Configuratie voor één pagina-type.

    Attrs:
        source_page: Pagina-index in referentie-PDF (voor documentatie).
        layers: Geordende lijst van layers (tekenvolgorde).
        content_frame: Optioneel frame voor flowable content (alleen bij content pages).
    """
    source_page: int = 0
    layers: list[Any] = field(default_factory=list)
    content_frame: ContentFrameConfig | None = None


@dataclass
class TemplateConfig:
    """Root configuratie voor een compleet template.

    Attrs:
        name: Weergavenaam (bijv. '3BM Coöperatie').
        version: Template versie.
        source_pdf: Referentie-PDF bestandsnaam.
        brand: Gekoppelde brand slug.
        colors: Kleurenpalet (naam → hex).
        fonts: Font mapping (naam → font naam).
        pages: Pagina-type configuraties.
    """
    name: str = ""
    version: str = "1.0"
    source_pdf: str = ""
    brand: str = ""
    colors: dict[str, str] = field(default_factory=dict)
    fonts: dict[str, str] = field(default_factory=dict)
    pages: dict[str, PageConfig] = field(default_factory=dict)


# ============================================================
# YAML Parser
# ============================================================

_LAYER_PARSERS = {
    "rect": RectLayer,
    "polygon": PolygonLayer,
    "image": ImageLayer,
    "clipped_image": ClippedImageLayer,
    "text": TextLayer,
    "text_block": TextBlockLayer,
    "badge_group": BadgeGroupLayer,
    "line": LineLayer,
    "page_number": PageNumberLayer,
    "table": TableLayer,
}


def _parse_badge(data: dict) -> BadgeConfig:
    """Parseer een badge dict naar BadgeConfig."""
    return BadgeConfig(
        text=data.get("text", ""),
        fill=data.get("fill", ""),
        text_color=data.get("text_color", ""),
        rect=data.get("rect", []),
        radius=float(data.get("radius", 17.0)),
        font=data.get("font", ""),
        font_size=float(data.get("font_size", 10.2)),
        icon=data.get("icon", ""),
    )


def _parse_layer(data: dict) -> LayerBase | None:
    """Parseer een layer dict naar het juiste Layer dataclass.

    Returns None als het type onbekend is.
    """
    layer_type = data.get("type", "")
    cls = _LAYER_PARSERS.get(layer_type)

    if cls is None:
        logger.warning("Onbekend layer type: %s", layer_type)
        return None

    # Base velden
    base = {
        "type": layer_type,
        "role": data.get("role", ""),
        "static": data.get("static", True),
        "bind": data.get("bind", ""),
        "condition": data.get("condition", ""),
    }

    if layer_type == "rect":
        return RectLayer(
            **base,
            x=float(data.get("x", 0)),
            y=float(data.get("y", 0)),
            w=float(data.get("w", 0)),
            h=float(data.get("h", 0)),
            fill=data.get("fill", ""),
            stroke=data.get("stroke", ""),
            stroke_width=float(data.get("stroke_width", 0)),
            radius=float(data.get("radius", 0)),
        )
    elif layer_type == "polygon":
        return PolygonLayer(
            **base,
            points=data.get("points", []),
            fill=data.get("fill", ""),
            stroke=data.get("stroke", ""),
        )
    elif layer_type == "image":
        return ImageLayer(
            **base,
            source=data.get("source", ""),
            x=float(data.get("x", 0)),
            y=float(data.get("y", 0)),
            w=float(data.get("w", 0)),
            h=float(data.get("h", 0)),
            mask=data.get("mask", "auto"),
        )
    elif layer_type == "clipped_image":
        return ClippedImageLayer(
            **base,
            image_rect=data.get("image_rect", {}),
            clip_polygon=data.get("clip_polygon", []),
        )
    elif layer_type == "text":
        return TextLayer(
            **base,
            content=data.get("content", ""),
            font=data.get("font", ""),
            size=float(data.get("size", 10)),
            color=data.get("color", ""),
            x=float(data.get("x", 0)),
            y=float(data.get("y", 0)),
            align=data.get("align", "left"),
            max_width=float(data.get("max_width", 0)),
        )
    elif layer_type == "text_block":
        return TextBlockLayer(
            **base,
            spans=data.get("spans", []),
        )
    elif layer_type == "badge_group":
        badges = [_parse_badge(b) for b in data.get("badges", [])]
        return BadgeGroupLayer(**base, badges=badges)
    elif layer_type == "line":
        return LineLayer(
            **base,
            x1=float(data.get("x1", 0)),
            y1=float(data.get("y1", 0)),
            x2=float(data.get("x2", 0)),
            y2=float(data.get("y2", 0)),
            color=data.get("color", ""),
            width=float(data.get("width", 0.5)),
            dash=data.get("dash", []),
        )
    elif layer_type == "page_number":
        return PageNumberLayer(
            **base,
            x=float(data.get("x", 0)),
            y=float(data.get("y", 0)),
            font=data.get("font", ""),
            size=float(data.get("size", 8)),
            color=data.get("color", ""),
            align=data.get("align", "right"),
        )
    elif layer_type == "table":
        return TableLayer(
            **base,
            x=float(data.get("x", 0)),
            y_start=float(data.get("y_start", 0)),
            col1_x=float(data.get("col1_x", 0)),
            col2_x=float(data.get("col2_x", 0)),
            row_height=float(data.get("row_height", 24)),
            label_font=data.get("label_font", ""),
            label_size=float(data.get("label_size", 10)),
            label_color=data.get("label_color", ""),
            value_font=data.get("value_font", ""),
            value_size=float(data.get("value_size", 10)),
            value_color=data.get("value_color", ""),
            separator_color=data.get("separator_color", ""),
            separator_width=float(data.get("separator_width", 0.3)),
            separator_x_end=float(data.get("separator_x_end", 0)),
            rows=data.get("rows", []),
        )

    return None


def _parse_page(data: dict) -> PageConfig:
    """Parseer een page dict naar PageConfig."""
    layers = []
    for layer_data in data.get("layers", []):
        layer = _parse_layer(layer_data)
        if layer is not None:
            layers.append(layer)

    content_frame = None
    cf_data = data.get("content_frame")
    if cf_data:
        content_frame = ContentFrameConfig(
            x=float(cf_data.get("x", 0)),
            y=float(cf_data.get("y", 0)),
            w=float(cf_data.get("w", 0)),
            h=float(cf_data.get("h", 0)),
        )

    return PageConfig(
        source_page=int(data.get("source_page", 0)),
        layers=layers,
        content_frame=content_frame,
    )


def load_template(path: Path) -> TemplateConfig:
    """Laad een template YAML bestand en parseer naar TemplateConfig.

    Args:
        path: Pad naar het YAML bestand.

    Returns:
        Volledig geparseerde TemplateConfig.

    Raises:
        FileNotFoundError: Als het bestand niet bestaat.
        yaml.YAMLError: Bij ongeldige YAML syntax.
    """
    if not path.exists():
        raise FileNotFoundError(f"Template niet gevonden: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        return TemplateConfig()

    tmpl_info = data.get("template", {})
    colors = data.get("colors", {})
    fonts = data.get("fonts", {})

    pages = {}
    for page_key, page_data in data.get("pages", {}).items():
        pages[page_key] = _parse_page(page_data)

    return TemplateConfig(
        name=tmpl_info.get("name", ""),
        version=tmpl_info.get("version", "1.0"),
        source_pdf=tmpl_info.get("source_pdf", ""),
        brand=tmpl_info.get("brand", ""),
        colors=colors,
        fonts=fonts,
        pages=pages,
    )


# ============================================================
# Template directory management
# ============================================================

TEMPLATES_DIR = Path(__file__).parent.parent / "assets" / "templates"


def list_templates(templates_dir: Path | None = None) -> list[dict[str, str]]:
    """Lijst alle beschikbare templates.

    Returns:
        Lijst van dicts met 'name', 'slug', 'path' per template.
    """
    d = templates_dir or TEMPLATES_DIR
    templates = []
    if not d.exists():
        return templates

    for path in sorted(d.glob("*.yaml")):
        try:
            with path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            tmpl_info = data.get("template", {}) if data else {}
            templates.append({
                "name": tmpl_info.get("name", path.stem),
                "slug": path.stem,
                "path": str(path),
            })
        except yaml.YAMLError:
            templates.append({
                "name": path.stem,
                "slug": path.stem,
                "path": str(path),
            })

    return templates
