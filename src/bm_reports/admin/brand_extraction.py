"""Brand extraction — pipeline logica voor de brand extraction wizard.

Wrapt de bestaande tools/ modules en biedt API-vriendelijke functies
die structured JSON retourneren in plaats van direct bestanden te schrijven.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# Maximale upload grootte voor referentie-PDF's (25 MB)
MAX_PDF_SIZE_BYTES = 25 * 1024 * 1024

# DPI voor pagina-renders
DEFAULT_RENDER_DPI = 150

# Pagina-types die we renderen voor de prompt package
_KEY_PAGE_TYPES = {"cover", "colofon", "toc", "appendix_divider", "backcover"}


def run_extraction(
    pdf_path: Path,
    tenant_dir: Path,
    brand_name: str,
    brand_slug: str,
    stamkaart_path: Path | None = None,
    dpi: int = DEFAULT_RENDER_DPI,
) -> dict:
    """Draai de volledige brand extraction pipeline.

    Gebruikt de bestaande tools (pdf_extractor, page_classifier,
    pattern_detector, layout_extractor) en retourneert structured JSON.

    Args:
        pdf_path: Pad naar het referentie-rapport PDF.
        tenant_dir: Tenant directory (voor opslag van analyse-output).
        brand_name: Weergavenaam van het merk.
        brand_slug: Machine-leesbare identifier.
        stamkaart_path: Optioneel pad naar stamkaart PDF.
        dpi: DPI voor pagina renders.

    Returns:
        Dict met extraction data, page images, en draft YAML.

    Raises:
        ImportError: Als PyMuPDF niet beschikbaar is.
        FileNotFoundError: Als de PDF niet gevonden wordt.
    """
    from bm_reports.tools.config_generator import generate_brand_yaml
    from bm_reports.tools.layout_extractor import extract_page_layouts
    from bm_reports.tools.page_classifier import PageType, classify_pages
    from bm_reports.tools.pattern_detector import analyze_brand
    from bm_reports.tools.pdf_extractor import extract_pdf

    # Maak analyse-directories
    analysis_dir = tenant_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    pages_dir = analysis_dir / "pages"
    pages_dir.mkdir(exist_ok=True)

    # --- Stap 1: Extraheer PDF ---
    logger.info("Brand extraction stap 1: PDF extractie (%s)", pdf_path.name)
    raw_pages = extract_pdf(pdf_path, pages_dir, dpi=dpi)

    # --- Stap 2: Classificeer pagina's ---
    logger.info("Brand extraction stap 2: pagina classificatie")
    classified = classify_pages(raw_pages)

    page_images = [p.page_image_path for p in raw_pages if p.page_image_path]

    # --- Stap 3: Analyseer brand patronen ---
    logger.info("Brand extraction stap 3: pattern detectie")
    analysis = analyze_brand(classified, str(pdf_path), page_images)

    # --- Stap 4: Verrijk kleuren uit stamkaart ---
    if stamkaart_path and stamkaart_path.exists():
        logger.info("Brand extraction stap 4: stamkaart verrijking")
        from bm_reports.tools.brand_builder import BrandBuilder

        builder = BrandBuilder(tenant_dir, brand_name, brand_slug)
        stamkaart_pages = extract_pdf(stamkaart_path)
        stamkaart_colors = builder._extract_stamkaart_colors(stamkaart_pages)
        if stamkaart_colors:
            analysis.colors.update(stamkaart_colors)

    # --- Stap 5: Layout extractie ---
    logger.info("Brand extraction stap 5: layout extractie")
    page_layouts = {}
    try:
        page_layouts = extract_page_layouts(classified)
    except Exception as exc:
        logger.warning("Layout extractie gefaald: %s", exc)

    # --- Stap 6: Genereer draft brand.yaml ---
    logger.info("Brand extraction stap 6: draft YAML generatie")
    draft_yaml = generate_brand_yaml(
        analysis, brand_name, brand_slug, page_layouts=page_layouts
    )

    # --- Bouw response ---
    page_classifications = []
    page_image_map = {}

    for cp in classified:
        page_num = cp.page.page_number
        page_type = cp.page_type.value
        page_classifications.append({
            "page_number": page_num,
            "type": page_type,
            "confidence": round(cp.confidence, 2),
        })

        # Bewaar key pages voor de prompt
        if page_type in _KEY_PAGE_TYPES and page_type not in page_image_map:
            img_filename = f"page_{page_num:03d}.png"
            page_image_map[page_type] = img_filename

    # Als er geen specifieke content page in de map zit, voeg er een toe
    if "content" not in page_image_map:
        for cp in classified:
            if cp.page_type == PageType.CONTENT:
                page_num = cp.page.page_number
                page_image_map["content"] = f"page_{page_num:03d}.png"
                break

    # Converteer styles naar API-formaat
    styles_out = {}
    for name, style in analysis.styles.items():
        styles_out[name] = {
            "fontName": style.get("font", ""),
            "fontSize": style.get("size", 10),
            "leading": style.get("leading", 12),
            "textColor": style.get("color", "#000000"),
        }

    # Serialiseer page_layouts voor JSON response
    layouts_serialized = _serialize_layouts(page_layouts)

    return {
        "extraction": {
            "brand": {"name": brand_name, "slug": brand_slug},
            "colors": analysis.colors,
            "fonts": analysis.fonts,
            "margins_mm": analysis.margins_mm,
            "header": {
                "height": analysis.header_zone.get("height_mm", 0),
                "elements": analysis.header_zone.get("elements", []),
            },
            "footer": {
                "height": analysis.footer_zone.get("height_mm", 0),
                "elements": analysis.footer_zone.get("elements", []),
            },
            "styles": styles_out,
            "table_style": analysis.table_style or {},
            "page_classifications": page_classifications,
            "page_layouts": layouts_serialized,
        },
        "page_images": page_image_map,
        "draft_yaml": draft_yaml,
    }


def generate_prompt_package(
    extraction: dict,
    page_image_map: dict[str, str],
    brand_name: str,
    brand_slug: str,
    reference_pages_yaml: str | None = None,
) -> str:
    """Genereer een markdown prompt package voor Claude Desktop.

    De prompt bevat alle extractie-data en instructies om de `pages:`
    sectie van brand.yaml te genereren op basis van visuele inspectie.

    Args:
        extraction: De extraction dict uit run_extraction().
        page_image_map: Dict van page_type → image bestandsnaam.
        brand_name: Merk weergavenaam.
        brand_slug: Machine-leesbare identifier.
        reference_pages_yaml: Optioneel: bestaande pages-sectie als referentie.

    Returns:
        Markdown string klaar om in Claude Desktop te plakken.
    """
    lines: list[str] = []

    lines.append(f"# Brand Extraction — {brand_name}")
    lines.append("")
    lines.append("## Opdracht")
    lines.append("")
    lines.append(
        "Genereer de `pages:` sectie van een brand.yaml configuratiebestand. "
        "Ik geef je: (1) geautomatiseerde extractie-data uit PyMuPDF, "
        "(2) gerenderde pagina-afbeeldingen."
    )
    lines.append(
        "Jouw taak: bekijk de pagina-afbeeldingen visueel en produceer "
        "precieze coordinaten en styling voor elk pagina-type."
    )
    lines.append("")

    # --- Referentiedata ---
    lines.append("## Referentiedata (Geautomatiseerde Extractie)")
    lines.append("")

    # Kleuren
    lines.append("### Kleuren")
    lines.append("")
    colors = extraction.get("colors", {})
    for name, hex_val in colors.items():
        lines.append(f"- **{name}:** `{hex_val}`")
    lines.append("")

    # Fonts
    lines.append("### Fonts (zoals gedetecteerd in PDF)")
    lines.append("")
    fonts = extraction.get("fonts", {})
    for role, font_name in fonts.items():
        lines.append(f"- **{role}:** {font_name}")
    lines.append("")

    # Styles
    lines.append("### Stijlen")
    lines.append("")
    lines.append("| Stijl | Font | Size | Color | Leading |")
    lines.append("|-------|------|------|-------|---------|")
    styles = extraction.get("styles", {})
    for name, style in styles.items():
        lines.append(
            f"| {name} | {style.get('fontName', '-')} | "
            f"{style.get('fontSize', '-')}pt | "
            f"`{style.get('textColor', '-')}` | "
            f"{style.get('leading', '-')}pt |"
        )
    lines.append("")

    # Pagina classificaties
    lines.append("### Pagina-classificatie")
    lines.append("")
    lines.append("| Pagina | Type | Confidence |")
    lines.append("|--------|------|------------|")
    for pc in extraction.get("page_classifications", []):
        lines.append(
            f"| {pc['page_number']} | {pc['type']} | {pc['confidence']:.0%} |"
        )
    lines.append("")

    # Layout data (raw)
    layouts = extraction.get("page_layouts", {})
    if layouts:
        lines.append("### Gedetecteerde Layout Elementen (Raw)")
        lines.append("")
        lines.append(
            "Onderstaande data is automatisch geextraheerd. "
            "Gebruik dit als startpunt, maar verifieer visueel."
        )
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(layouts, indent=2, ensure_ascii=False))
        lines.append("```")
        lines.append("")

    # --- Pagina afbeeldingen ---
    lines.append("## Pagina-afbeeldingen")
    lines.append("")
    lines.append("De volgende afbeeldingen zijn bijgevoegd:")
    lines.append("")
    for i, (page_type, filename) in enumerate(sorted(page_image_map.items()), 1):
        lines.append(f"{i}. **{filename}** — {page_type.upper()}")
    lines.append("")

    # --- Output formaat ---
    lines.append("## Gewenst Output Formaat")
    lines.append("")
    lines.append(
        "Genereer YAML voor de `pages:` sectie. "
        "Geef het resultaat als een YAML code block."
    )
    lines.append("")
    lines.append("De structuur moet de volgende pagina-types bevatten:")
    lines.append("")
    lines.append("- **cover**: paars vlak, clip polygon voor foto, badges, "
                  "logo positie, titel/subtitel coordinaten")
    lines.append("- **colofon**: rapport-type header, veldvolgorde met y_pt "
                  "posities, footer turquoise blok")
    lines.append("- **toc**: titel positie, level1/level2 kolommen en spacing")
    lines.append("- **appendix_divider**: achtergrondkleur, paars blok, "
                  "nummer/titel posities, tagline")
    lines.append("- **backcover**: wit polygon masker, paars driehoek, "
                  "logo en contact posities")
    lines.append("")

    # --- Coordinatensysteem ---
    lines.append("## Coordinatensysteem")
    lines.append("")
    lines.append("- Alle coordinaten in PDF points (1 point = 1/72 inch)")
    lines.append("- `_ref` suffix: referentie-coordinaten voor A4 "
                  "(595.28 x 841.89 pt), PDF y-up")
    lines.append("- `_pt` suffix: absolute point waarden, top-down")
    lines.append("- Polygonen: PDF y-up conventie (origin linksonder)")
    lines.append("")

    # --- Referentie voorbeeld ---
    if reference_pages_yaml:
        lines.append("## Referentie Voorbeeld")
        lines.append("")
        lines.append(
            "Hieronder staat een complete `pages:` sectie van een bestaande "
            "brand (3BM Cooperatie) als template. Match deze structuur exact, "
            "maar pas alle waarden aan op basis van wat je in de afbeeldingen ziet."
        )
        lines.append("")
        lines.append("```yaml")
        lines.append(reference_pages_yaml)
        lines.append("```")
        lines.append("")

    # --- Belangrijke opmerkingen ---
    lines.append("## Belangrijke Opmerkingen")
    lines.append("")
    lines.append("- Kijk goed naar visuele verhoudingen en spacing")
    lines.append("- Badges zijn afgeronde rechthoeken met tekst — "
                  "noteer hun exacte positie relatief aan de foto")
    lines.append("- Het clip polygon definieert de vorm van de foto-uitsnede "
                  "op de cover")
    lines.append("- Colofon velden hebben specifieke y_pt posities — "
                  "meet vanaf de bovenkant van de pagina")
    lines.append("- De backcover heeft een wit polygon masker en een "
                  "paars driehoek")
    lines.append("- Gebruik de font-namen uit de extractie-data, "
                  "niet de ruwe PDF font-namen")
    lines.append("")

    return "\n".join(lines)


def merge_brand_yaml(
    edited_extraction: dict,
    pages_yaml_str: str | None,
    brand_name: str,
    brand_slug: str,
) -> str:
    """Merge alle onderdelen tot een complete brand.yaml.

    Combineert:
    1. User-gecorrigeerde extractie data (kleuren, fonts, styles, header, footer)
    2. Claude Desktop artifact (pages: sectie)
    3. Auto-gegenereerde secties (stationery, modules)

    Args:
        edited_extraction: Gecorrigeerde extractie data uit de UI.
        pages_yaml_str: YAML string van de pages-sectie (Claude Desktop artifact).
        brand_name: Merk weergavenaam.
        brand_slug: Machine-leesbare identifier.

    Returns:
        Complete brand.yaml als string.
    """
    brand_config: dict = {
        "brand": {"name": brand_name, "slug": brand_slug},
        "colors": edited_extraction.get("colors", {}),
        "fonts": edited_extraction.get("fonts", {}),
        "logos": edited_extraction.get("logos", {
            "main": f"logos/{brand_slug}.png",
            "tagline": f"logos/{brand_slug}-tagline.png",
            "white": f"logos/{brand_slug}-wit.png",
        }),
        "contact": edited_extraction.get("contact", {}),
        "header": edited_extraction.get("header", {"height": 0, "elements": []}),
        "footer": edited_extraction.get("footer", {"height": 17, "elements": []}),
        "styles": edited_extraction.get("styles", {}),
    }

    # Pages sectie: parse Claude Desktop artifact
    if pages_yaml_str:
        try:
            pages_data = yaml.safe_load(pages_yaml_str)
            # Ondersteun zowel {pages: {...}} als direct de pages dict
            if isinstance(pages_data, dict):
                if "pages" in pages_data:
                    brand_config["pages"] = pages_data["pages"]
                else:
                    brand_config["pages"] = pages_data
        except yaml.YAMLError as exc:
            logger.warning("Kon pages YAML niet parsen: %s", exc)
            raise ValueError(f"Ongeldige pages YAML: {exc}") from exc

    # Stationery sectie (auto-generated scaffold)
    brand_config["stationery"] = _generate_stationery_scaffold()

    # Modules sectie (auto-generated met $colors.* references)
    brand_config["modules"] = _generate_modules_scaffold()

    return yaml.dump(
        brand_config,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )


def get_reference_pages_yaml(tenants_base: Path) -> str | None:
    """Lees de pages-sectie uit de 3bm_cooperatie brand.yaml als referentie.

    Args:
        tenants_base: Basis pad naar tenants directory.

    Returns:
        YAML string van de pages-sectie, of None.
    """
    ref_path = tenants_base / "3bm_cooperatie" / "brand.yaml"
    if not ref_path.exists():
        return None

    try:
        data = yaml.safe_load(ref_path.read_text(encoding="utf-8"))
        pages = data.get("pages")
        if pages:
            return yaml.dump(
                {"pages": pages},
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
    except (yaml.YAMLError, OSError) as exc:
        logger.warning("Kon referentie pages YAML niet laden: %s", exc)

    return None


def _serialize_layouts(page_layouts: dict) -> dict:
    """Serialiseer PageLayout objecten naar JSON-compatibele dicts.

    Args:
        page_layouts: Dict van PageType → PageLayout.

    Returns:
        Dict van page_type string → geserialiseerde layout.
    """
    result: dict = {}
    for page_type, layout in page_layouts.items():
        key = page_type.value
        layout_dict: dict = {
            "page_number": layout.page_number,
            "width_pt": layout.width_pt,
            "height_pt": layout.height_pt,
        }

        if layout.static_elements:
            layout_dict["static_elements"] = [
                _serialize_static_element(el) for el in layout.static_elements
            ]

        if layout.text_zones:
            layout_dict["text_zones"] = [
                _serialize_text_zone(tz) for tz in layout.text_zones
            ]

        if layout.badges:
            layout_dict["badges"] = [
                _serialize_badge(b) for b in layout.badges
            ]

        if layout.clip_polygon:
            layout_dict["clip_polygon"] = [
                list(p) for p in layout.clip_polygon
            ]

        if layout.photo_rect:
            layout_dict["photo_rect"] = list(layout.photo_rect)

        result[key] = layout_dict

    return result


def _serialize_static_element(el) -> dict:
    """Serialiseer een StaticElement naar dict."""
    d: dict = {
        "type": el.element_type,
        "x_pt": el.x_pt,
        "y_pt": el.y_pt,
    }
    if el.width_pt:
        d["width_pt"] = el.width_pt
    if el.height_pt:
        d["height_pt"] = el.height_pt
    if el.fill_color:
        d["fill_color"] = el.fill_color
    if el.stroke_color:
        d["stroke_color"] = el.stroke_color
    if el.corner_radius:
        d["corner_radius"] = el.corner_radius
    if el.points:
        d["points"] = [list(p) for p in el.points]
    if el.image_role:
        d["image_role"] = el.image_role
    return d


def _serialize_text_zone(tz) -> dict:
    """Serialiseer een TextZone naar dict."""
    return {
        "name": tz.name,
        "x_pt": tz.x_pt,
        "y_pt": tz.y_pt,
        "font": tz.font,
        "size": tz.size,
        "color": tz.color,
        "is_dynamic": tz.is_dynamic,
    }


def _serialize_badge(badge) -> dict:
    """Serialiseer een BadgeSpec naar dict."""
    return {
        "label": badge.label,
        "bg_color": badge.bg_color,
        "text_color": badge.text_color,
        "x_pt": badge.x_pt,
        "y_pt": badge.y_pt,
        "width_pt": badge.width_pt,
        "height_pt": badge.height_pt,
        "corner_radius": badge.corner_radius,
        "font_size": badge.font_size,
    }


def _generate_stationery_scaffold() -> dict:
    """Genereer een lege stationery-sectie als scaffold.

    Returns:
        Dict met page-type entries en lege bronpaden.
    """
    return {
        "cover": {
            "source": "",
            "text_zones": [],
        },
        "colofon": {
            "source": "",
            "header_footer": "colofon",
            "text_zones": [],
        },
        "content": {
            "source": "",
            "header_footer": "content",
            "content_frame": {
                "x_pt": 90.0,
                "y_pt": 38.9,
                "width_pt": 451.6,
                "height_pt": 746.0,
            },
        },
        "toc": {
            "source": "",
            "header_footer": "content",
        },
        "appendix_divider": {
            "source": "",
            "header_footer": None,
            "text_zones": [],
        },
        "backcover": {
            "source": "",
            "header_footer": None,
            "text_zones": [],
        },
    }


def _generate_modules_scaffold() -> dict:
    """Genereer een modules-sectie met $colors.* references.

    Returns:
        Dict met module-specifieke styling.
    """
    return {
        "table": {
            "header_bg": "$colors.table_header_bg",
            "header_text_color": "#FFFFFF",
            "body_font": "$body",
            "body_size": 9.0,
            "footer_bg": "$colors.table_footer_bg",
            "grid_color": "$colors.separator",
        },
        "calculation": {
            "title_color": "$colors.primary",
            "accent_line_color": "$colors.secondary",
        },
        "check": {
            "pass_color": "$colors.accent",
            "fail_color": "$colors.warning",
        },
    }
