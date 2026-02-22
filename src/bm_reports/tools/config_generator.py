"""Config generator — converteer BrandAnalysis naar concrete output."""

from __future__ import annotations

import yaml

from .pattern_detector import BrandAnalysis


def generate_brand_yaml(
    analysis: BrandAnalysis,
    brand_name: str,
    brand_slug: str,
    page_layouts: dict | None = None,
) -> str:
    """Genereer een YAML brand configuratie string.

    Args:
        analysis: De brand analyse resultaten.
        brand_name: Weergavenaam van het merk.
        brand_slug: Machine-leesbare identifier.
        page_layouts: Optionele page layouts uit layout_extractor.

    Returns:
        YAML string klaar om op te slaan als .yaml bestand.
    """
    # Bouw de YAML structuur
    data: dict = {
        "brand": {
            "name": brand_name,
            "slug": brand_slug,
        },
        "colors": analysis.colors,
        "fonts": analysis.fonts,
        "logos": {
            "main": f"logos/{brand_slug}.png",
            "tagline": f"logos/{brand_slug}-tagline.png",
        },
        "header": _zone_to_dict(analysis.header_zone),
        "footer": _zone_to_dict(analysis.footer_zone),
    }

    # Styles → converteer naar YAML-compatibel formaat
    if analysis.styles:
        styles_section = {}
        for name, style in analysis.styles.items():
            style_entry: dict = {}
            if "font" in style:
                style_entry["fontName"] = style["font"]
            if "size" in style:
                style_entry["fontSize"] = style["size"]
            if "leading" in style:
                style_entry["leading"] = style["leading"]
            if "color" in style:
                style_entry["textColor"] = style["color"]
            styles_section[name] = style_entry
        data["styles"] = styles_section

    # Tabelstijl
    if analysis.table_style:
        data["table_style"] = analysis.table_style

    # Pages sectie uit layout extractie
    if page_layouts:
        data["pages"] = generate_pages_yaml(page_layouts)

    return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)


def generate_pages_yaml(layouts: dict) -> dict:
    """Genereer de pages-sectie van de brand YAML.

    Args:
        layouts: Dict van PageType -> PageLayout uit layout_extractor.

    Returns:
        Dict klaar voor YAML serialisatie.
    """
    pages: dict = {}

    for page_type, layout in layouts.items():
        key = page_type.value
        page_data: dict = {}

        # Static elements gegroepeerd op type
        rects = [e for e in layout.static_elements if e.element_type == "rect"]
        polygons = [e for e in layout.static_elements if e.element_type == "polygon"]
        images = [e for e in layout.static_elements if e.element_type == "image"]

        # Grootste rect = achtergrond vlak
        if rects:
            biggest = max(rects, key=lambda r: r.width_pt * r.height_pt)
            if biggest.fill_color:
                page_data["bg_rect"] = {
                    "x": biggest.x_pt,
                    "y_ref": biggest.y_pt,
                    "width": biggest.width_pt,
                    "height": biggest.height_pt,
                    "color": biggest.fill_color,
                }

        # Clip polygon (cover)
        if layout.clip_polygon:
            page_data["clip_polygon"] = [list(p) for p in layout.clip_polygon]

        # Photo rect (cover)
        if layout.photo_rect:
            page_data["photo_rect"] = list(layout.photo_rect)

        # Badges
        if layout.badges:
            page_data["badges"] = [
                {
                    "label": b.label,
                    "bg_color": b.bg_color,
                    "text_color": b.text_color,
                    "x_ref": b.x_pt,
                    "y_ref": b.y_pt,
                    "w_ref": b.width_pt,
                    "h_ref": b.height_pt,
                }
                for b in layout.badges
            ]
            page_data["badge_radius_ref"] = layout.badges[0].corner_radius
            page_data["badge_font_size_ref"] = layout.badges[0].font_size

        # Text zones: dynamisch en statisch
        dynamic_zones = [z for z in layout.text_zones if z.is_dynamic]

        for zone in dynamic_zones:
            key_name = zone.name
            page_data[f"{key_name}_x_ref"] = zone.x_pt
            page_data[f"{key_name}_y_ref"] = zone.y_pt
            page_data[f"{key_name}_size_ref"] = zone.size

        # Logo's
        logos = [e for e in images if e.image_role == "logo"]
        if logos:
            logo = logos[0]
            page_data["logo_x_ref"] = logo.x_pt
            page_data["logo_y_ref"] = logo.y_pt
            page_data["logo_w_ref"] = logo.width_pt

        # Polygonen
        for i, poly in enumerate(polygons):
            if poly.points:
                name = _guess_polygon_name(poly, layout)
                page_data[name] = [list(p) for p in poly.points]

        pages[key] = page_data

    return pages


def _guess_polygon_name(poly, layout) -> str:
    """Geef een semantische naam aan een polygon element."""
    # Witte polygonen zijn typisch masker/overlay
    if poly.fill_color and poly.fill_color.upper() in ("#FFFFFF", "#FEFEFE"):
        return "white_polygon"

    # Donkere polygonen (driehoek op backcover)
    if poly.fill_color:
        try:
            r = int(poly.fill_color[1:3], 16)
            g = int(poly.fill_color[3:5], 16)
            b = int(poly.fill_color[5:7], 16)
            brightness = (r + g + b) / 3
            if brightness < 100:
                return "dark_polygon"
        except (ValueError, IndexError):
            pass

    return "polygon"


def _zone_to_dict(zone: dict) -> dict:
    """Converteer zone dict naar YAML-compatibel formaat."""
    result = {"height": zone.get("height_mm", 0)}
    elements = zone.get("elements", [])
    if elements:
        result["elements"] = elements
    else:
        result["elements"] = []
    return result


def generate_style_overrides(analysis: BrandAnalysis) -> dict:
    """Return de styles dict, klaar voor toepassing op ReportLab ParagraphStyles.

    Args:
        analysis: De brand analyse resultaten.

    Returns:
        Dict van stijlnaam → stijl properties.
    """
    return dict(analysis.styles)


def generate_analysis_report(analysis: BrandAnalysis) -> str:
    """Genereer een leesbaar markdown rapport van de analyse.

    Args:
        analysis: De brand analyse resultaten.

    Returns:
        Markdown string met alle analyse resultaten.
    """
    lines: list[str] = []

    lines.append(f"# Brand Analyse — {analysis.source_pdf}")
    lines.append("")
    lines.append(f"**Pagina's:** {analysis.page_count}")
    lines.append(f"**Formaat:** {analysis.page_size_mm[0]} x {analysis.page_size_mm[1]} mm")
    lines.append("")

    # Pagina-classificatie
    lines.append("## Pagina-classificatie")
    lines.append("")
    lines.append("| Pagina | Type | Confidence |")
    lines.append("|--------|------|------------|")
    for cp in analysis.classified_pages:
        lines.append(f"| {cp.page.page_number} | {cp.page_type.value} | {cp.confidence:.2f} |")
    lines.append("")

    # Kleuren
    lines.append("## Kleurenpalet")
    lines.append("")
    if analysis.colors:
        for name, hex_val in analysis.colors.items():
            lines.append(f"- **{name}:** `{hex_val}`")
    else:
        lines.append("Geen kleuren gedetecteerd.")
    lines.append("")

    # Fonts
    lines.append("## Font mapping")
    lines.append("")
    if analysis.fonts:
        for role, font_name in analysis.fonts.items():
            lines.append(f"- **{role}:** {font_name}")
    else:
        lines.append("Geen fonts gedetecteerd.")
    lines.append("")

    # Marges
    lines.append("## Marges")
    lines.append("")
    if analysis.margins_mm:
        for side, mm in analysis.margins_mm.items():
            lines.append(f"- **{side}:** {mm} mm")
    lines.append("")

    # Header zone
    lines.append("## Header zone")
    lines.append("")
    lines.append(f"**Hoogte:** {analysis.header_zone.get('height_mm', 0)} mm")
    h_elements = analysis.header_zone.get("elements", [])
    if h_elements:
        for elem in h_elements:
            lines.append(f"- {elem}")
    else:
        lines.append("Geen header elementen gedetecteerd.")
    lines.append("")

    # Footer zone
    lines.append("## Footer zone")
    lines.append("")
    lines.append(f"**Hoogte:** {analysis.footer_zone.get('height_mm', 0)} mm")
    f_elements = analysis.footer_zone.get("elements", [])
    if f_elements:
        for elem in f_elements:
            lines.append(f"- {elem}")
    else:
        lines.append("Geen footer elementen gedetecteerd.")
    lines.append("")

    # Stijlen
    lines.append("## Stijlen")
    lines.append("")
    if analysis.styles:
        lines.append("| Stijl | Font | Size | Color | Leading |")
        lines.append("|-------|------|------|-------|---------|")
        for name, style in analysis.styles.items():
            lines.append(
                f"| {name} | {style.get('font', '-')} | "
                f"{style.get('size', '-')}pt | "
                f"`{style.get('color', '-')}` | "
                f"{style.get('leading', '-')}pt |"
            )
    else:
        lines.append("Geen stijlen gedetecteerd.")
    lines.append("")

    # Tabelstijl
    lines.append("## Tabelstijl")
    lines.append("")
    if analysis.table_style:
        for key, val in analysis.table_style.items():
            lines.append(f"- **{key}:** `{val}`")
    else:
        lines.append("Geen tabelstijl gedetecteerd.")
    lines.append("")

    return "\n".join(lines)
