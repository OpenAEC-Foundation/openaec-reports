"""Pattern detector — detecteer herhalende visuele patronen in geclassificeerde pagina's."""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from statistics import median

from .page_classifier import ClassifiedPage, PageType

logger = logging.getLogger(__name__)

PT_TO_MM = 1 / 2.8346


@dataclass
class BrandAnalysis:
    """Resultaat van de volledige brand analyse."""

    source_pdf: str
    page_count: int
    page_size_mm: tuple[float, float]
    classified_pages: list[ClassifiedPage]
    colors: dict[str, str]
    fonts: dict[str, str]
    margins_mm: dict[str, float]
    header_zone: dict
    footer_zone: dict
    styles: dict[str, dict]
    table_style: dict | None
    cover_spec: dict | None = None
    colofon_spec: dict | None = None
    toc_spec: dict | None = None
    appendix_divider_spec: dict | None = None
    backcover_spec: dict | None = None
    page_images: list[str] = field(default_factory=list)


def analyze_brand(
    pages: list[ClassifiedPage],
    source_pdf: str,
    page_images: list[str] | None = None,
) -> BrandAnalysis:
    """Analyseer brand patronen over geclassificeerde pagina's.

    Args:
        pages: Geclassificeerde pagina's.
        source_pdf: Bronbestand naam.
        page_images: Optionele lijst van pagina PNG paden.

    Returns:
        BrandAnalysis met gedetecteerde patronen.
    """
    if not pages:
        return BrandAnalysis(
            source_pdf=source_pdf,
            page_count=0,
            page_size_mm=(0, 0),
            classified_pages=pages,
            colors={},
            fonts={},
            margins_mm={},
            header_zone={"height_mm": 0, "elements": []},
            footer_zone={"height_mm": 0, "elements": []},
            styles={},
            table_style=None,
            page_images=page_images or [],
        )

    first = pages[0].page
    page_size_mm = (
        round(first.width_pt * PT_TO_MM, 1),
        round(first.height_pt * PT_TO_MM, 1),
    )

    content_pages = [p for p in pages if p.page_type == PageType.CONTENT]

    # Filter op hoofdformaat (A4) — appendix pages hebben vaak afwijkende fonts/sizes
    main_page_height = first.height_pt
    main_content = [
        p for p in content_pages
        if abs(p.page.height_pt - main_page_height) < 10
    ]
    if not main_content:
        main_content = content_pages

    colors = extract_color_palette(pages)
    fonts = extract_font_map(pages, main_content)
    margins = detect_margins(main_content)
    header = detect_header_zone(main_content)
    footer = detect_footer_zone(main_content)
    styles = extract_styles(main_content)
    table_style = detect_table_styles(main_content)

    return BrandAnalysis(
        source_pdf=source_pdf,
        page_count=len(pages),
        page_size_mm=page_size_mm,
        classified_pages=pages,
        colors=colors,
        fonts=fonts,
        margins_mm=margins,
        header_zone=header,
        footer_zone=footer,
        styles=styles,
        table_style=table_style,
        page_images=page_images or [],
    )


# ============================================================
# Kleurenpalet
# ============================================================

def _cluster_color(hex_color: str, existing: list[str], threshold: int = 10) -> str | None:
    """Vind een bestaande kleur die dichtbij genoeg is."""
    r1, g1, b1 = _hex_to_rgb(hex_color)
    for existing_hex in existing:
        r2, g2, b2 = _hex_to_rgb(existing_hex)
        if abs(r1 - r2) < threshold and abs(g1 - g2) < threshold and abs(b1 - b2) < threshold:
            return existing_hex
    return None


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Converteer hex kleur naar RGB tuple."""
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _is_near_white(hex_color: str, threshold: int = 240) -> bool:
    r, g, b = _hex_to_rgb(hex_color)
    return r > threshold and g > threshold and b > threshold


def _is_near_black(hex_color: str, threshold: int = 15) -> bool:
    r, g, b = _hex_to_rgb(hex_color)
    return r < threshold and g < threshold and b < threshold


def extract_color_palette(pages: list[ClassifiedPage]) -> dict[str, str]:
    """Extraheer kleurenpalet uit alle pagina's.

    Primary wordt bepaald uit rect fills (grote gekleurde vlakken),
    niet uit body tekst. Secondary is de meest voorkomende lichte kleur.

    Returns:
        Dict met primary, secondary, text, en optioneel text_accent.
    """
    clustered: list[str] = []

    # Aparte counters voor rect fills vs tekst kleuren
    rect_counter: Counter = Counter()
    text_counter_all: Counter = Counter()

    for cp in pages:
        p = cp.page
        for t in p.texts:
            _count_color(t.color_hex, text_counter_all, clustered)
        for r in p.rects:
            if r.fill_hex and r.element_type == "rect":
                # Weeg grotere rects zwaarder (area-based)
                area = r.width * r.height
                weight = max(1, int(area / 1000))
                hex_c = r.fill_hex
                existing = _cluster_color(hex_c, clustered)
                if existing:
                    rect_counter[existing] += weight
                else:
                    clustered.append(hex_c)
                    rect_counter[hex_c] += weight

    # Combineer voor licht/donker split — rects wegen zwaarder voor primary
    dark_rects: Counter = Counter()
    light_rects: Counter = Counter()

    for color, count in rect_counter.items():
        if _is_near_white(color) or _is_near_black(color):
            continue
        r, g, b = _hex_to_rgb(color)
        if r + g + b < 384:
            dark_rects[color] = count
        else:
            light_rects[color] = count

    # Voeg ook lichte tekst kleuren toe (voor secondary detectie)
    for color, count in text_counter_all.items():
        if _is_near_white(color) or _is_near_black(color):
            continue
        r, g, b = _hex_to_rgb(color)
        if r + g + b >= 384:
            light_rects[color] += count

    result: dict[str, str] = {}

    # Primary = meest voorkomende donkere kleur in rects
    if dark_rects:
        result["primary"] = dark_rects.most_common(1)[0][0]

    # Secondary = meest voorkomende lichte kleur
    if light_rects:
        result["secondary"] = light_rects.most_common(1)[0][0]

    # Text = meest voorkomende kleur in content body tekst (size < 12)
    content_pages = [p for p in pages if p.page_type == PageType.CONTENT]
    text_counter: Counter = Counter()
    for cp in content_pages:
        for t in cp.page.texts:
            if t.size < 12:
                _count_color(t.color_hex, text_counter, clustered)

    for color, _ in text_counter.most_common():
        if not _is_near_white(color) and not _is_near_black(color):
            result["text"] = color
            break

    # text_accent = turquoise/groenachtige kleur die verschilt van secondary
    for color, count in light_rects.most_common():
        r, g, b = _hex_to_rgb(color)
        is_turquoise = g > r and g > 100 and b > 80
        if is_turquoise and color != result.get("secondary"):
            result["text_accent"] = color
            break

    return result


def _count_color(
    hex_color: str, counter: Counter, clustered: list[str]
) -> None:
    """Tel een kleur, cluster met bestaande kleuren."""
    if not hex_color or hex_color == "None":
        return
    existing = _cluster_color(hex_color, clustered)
    if existing:
        counter[existing] += 1
    else:
        clustered.append(hex_color)
        counter[hex_color] += 1


# ============================================================
# Font mapping
# ============================================================

def extract_font_map(
    pages: list[ClassifiedPage],
    main_content: list[ClassifiedPage] | None = None,
) -> dict[str, str]:
    """Extraheer font mapping uit alle pagina's.

    Args:
        pages: Alle geclassificeerde pagina's.
        main_content: Optioneel gefilterde main content pages (A4).

    Returns:
        Dict met heading, body, en optioneel medium.
    """
    result: dict[str, str] = {}

    # Heading: font op cover met grootste size
    cover_pages = [p for p in pages if p.page_type == PageType.COVER]
    if cover_pages:
        cover = cover_pages[0].page
        max_size = 0
        heading_font = ""
        for t in cover.texts:
            if t.size > max_size:
                max_size = t.size
                heading_font = t.font
        if heading_font:
            # Zoek bold variant
            all_fonts = set()
            for cp in pages:
                for t in cp.page.texts:
                    all_fonts.add(t.font)

            family = _font_family(heading_font)
            bold_variant = None
            for f in all_fonts:
                if family.lower() in f.lower() and "bold" in f.lower():
                    bold_variant = f
                    break
            result["heading"] = bold_variant or heading_font

    # Body: meest voorkomende font in main content (size < 12)
    # Filter CIDFont+ namen (embedded fonts zonder leesbare naam)
    content_for_body = main_content or [
        p for p in pages if p.page_type == PageType.CONTENT
    ]
    font_counter: Counter = Counter()
    all_fonts_set: set[str] = set()
    for cp in content_for_body:
        for t in cp.page.texts:
            all_fonts_set.add(t.font)
            if t.size < 12 and not t.font.startswith("CIDFont"):
                font_counter[t.font] += 1

    if font_counter:
        result["body"] = font_counter.most_common(1)[0][0]

    # Medium: zoek een "Medium" variant
    for f in all_fonts_set:
        if "medium" in f.lower() and "bold" not in f.lower():
            result["medium"] = f
            break

    return result


def _font_family(font_name: str) -> str:
    """Extraheer font family uit volledige naam."""
    for sep in ("-", " "):
        if sep in font_name:
            return font_name.split(sep)[0]
    # Probeer CamelCase te splitsen
    import re
    parts = re.findall(r"[A-Z][a-z]+", font_name)
    return parts[0] if parts else font_name


# ============================================================
# Marges
# ============================================================

def detect_margins(content_pages: list[ClassifiedPage]) -> dict[str, float]:
    """Detecteer marges uit content pagina's.

    Returns:
        Dict met left, right, top, bottom in mm.
    """
    if not content_pages:
        return {"left": 25, "right": 20, "top": 25, "bottom": 15}

    lefts, rights, tops, bottoms = [], [], [], []

    for cp in content_pages:
        p = cp.page
        if not p.texts:
            continue
        min_x = min(t.x for t in p.texts)
        max_x2 = max(t.x2 for t in p.texts)
        min_y = min(t.y_top for t in p.texts)
        max_y = max(t.y_bottom for t in p.texts)

        lefts.append(min_x)
        rights.append(p.width_pt - max_x2)
        tops.append(min_y)
        bottoms.append(p.height_pt - max_y)

    return {
        "left": round(median(lefts) * PT_TO_MM, 1) if lefts else 25,
        "right": round(median(rights) * PT_TO_MM, 1) if rights else 20,
        "top": round(median(tops) * PT_TO_MM, 1) if tops else 25,
        "bottom": round(median(bottoms) * PT_TO_MM, 1) if bottoms else 15,
    }


# ============================================================
# Header / footer zones
# ============================================================

def detect_header_zone(content_pages: list[ClassifiedPage]) -> dict:
    """Detecteer herhalend header patroon.

    Returns:
        Dict met height_mm en elements.
    """
    return _detect_zone(content_pages, zone="header")


def detect_footer_zone(content_pages: list[ClassifiedPage]) -> dict:
    """Detecteer herhalend footer patroon.

    Returns:
        Dict met height_mm en elements.
    """
    return _detect_zone(content_pages, zone="footer")


def _detect_zone(
    content_pages: list[ClassifiedPage], zone: str
) -> dict:
    """Detecteer herhalende elementen in header of footer zone.

    Args:
        content_pages: Lijst van content pagina's.
        zone: "header" of "footer".

    Returns:
        Dict met height_mm en elements.
    """
    if not content_pages:
        return {"height_mm": 0, "elements": []}

    n_pages = len(content_pages)
    threshold = 0.5  # element moet op >50% pagina's voorkomen

    # Zoek vaste teksten en rects
    if zone == "footer":
        y_min_pt = content_pages[0].page.height_pt - 70
        y_max_pt = content_pages[0].page.height_pt
    else:
        y_min_pt = 0
        y_max_pt = 60

    # Verzamel teksten per ronde positie
    text_positions: dict[tuple[int, int], list[str]] = {}
    for cp in content_pages:
        p = cp.page
        for t in p.texts:
            if zone == "footer":
                if t.y_top < y_min_pt:
                    continue
            else:
                if t.y_bottom > y_max_pt:
                    continue
            key = (round(t.x / 5) * 5, round(t.y_top / 5) * 5)
            text_positions.setdefault(key, []).append(t.text)

    # Zoek rects in de zone
    rect_positions: dict[tuple[int, int, int, int], int] = {}
    for cp in content_pages:
        p = cp.page
        for r in p.rects:
            if zone == "footer":
                if r.y < y_min_pt:
                    continue
            else:
                if r.y + r.height > y_max_pt:
                    continue
            key = (
                round(r.x / 5) * 5,
                round(r.y / 5) * 5,
                round(r.width / 5) * 5,
                round(r.height / 5) * 5,
            )
            rect_positions[key] = rect_positions.get(key, 0) + 1

    # Filter op threshold
    elements: list[dict] = []
    zone_y_min_pt = None  # bovenkant van zone-elementen

    for pos, texts in text_positions.items():
        if len(texts) < threshold * n_pages:
            continue

        x_pt, y_pt = pos
        # Bepaal of het een paginanummer is (oplopende getallen)
        is_page_number = _is_page_number_sequence(texts)

        if zone_y_min_pt is None or y_pt < zone_y_min_pt:
            zone_y_min_pt = y_pt

        page_h = content_pages[0].page.height_pt
        page_w = content_pages[0].page.width_pt

        # Bepaal alignment
        align = "left"
        if x_pt > page_w * 0.6:
            align = "right"
        elif x_pt > page_w * 0.35:
            align = "center"

        if is_page_number:
            content = "{page}"
        else:
            # Gebruik meest voorkomende tekst
            content = Counter(texts).most_common(1)[0][0]

        # Positie: mm relatief aan zone-onderkant
        if zone == "footer":
            y_mm = round((page_h - y_pt) * PT_TO_MM, 1)
        else:
            y_mm = round(y_pt * PT_TO_MM, 1)

        # Zoek font/size van dit element
        sample_font = ""
        sample_size = 0.0
        sample_color = ""
        for cp in content_pages:
            for t in cp.page.texts:
                t_key = (round(t.x / 5) * 5, round(t.y_top / 5) * 5)
                if t_key == pos:
                    sample_font = t.font
                    sample_size = t.size
                    sample_color = t.color_hex
                    break
            if sample_font:
                break

        elements.append({
            "type": "text",
            "content": content,
            "x": round(x_pt * PT_TO_MM, 1),
            "y": y_mm,
            "font": sample_font,
            "size": sample_size,
            "color": sample_color,
            "align": align,
        })

    # Voeg rects toe
    for (x_pt, y_pt, w_pt, h_pt), count in rect_positions.items():
        if count < threshold * n_pages:
            continue

        page_h = content_pages[0].page.height_pt
        if zone == "footer":
            y_mm = round((page_h - y_pt) * PT_TO_MM, 1)
        else:
            y_mm = round(y_pt * PT_TO_MM, 1)

        if zone_y_min_pt is None or y_pt < zone_y_min_pt:
            zone_y_min_pt = y_pt

        elements.append({
            "type": "rect",
            "x": round(x_pt * PT_TO_MM, 1),
            "y": y_mm,
            "width": round(w_pt * PT_TO_MM, 1),
            "height": round(h_pt * PT_TO_MM, 1),
        })

    # Bereken zone hoogte
    if zone_y_min_pt is not None:
        page_h = content_pages[0].page.height_pt
        if zone == "footer":
            height_mm = round((page_h - zone_y_min_pt) * PT_TO_MM, 1)
        else:
            height_mm = round(zone_y_min_pt * PT_TO_MM, 1)
    else:
        height_mm = 0

    return {"height_mm": height_mm, "elements": elements}


def _is_page_number_sequence(texts: list[str]) -> bool:
    """Check of een lijst teksten een oplopende getalreeks is."""
    numbers = []
    for t in texts:
        t = t.strip()
        try:
            numbers.append(int(t))
        except ValueError:
            return False
    if len(numbers) < 2:
        return False
    return all(numbers[i] <= numbers[i + 1] for i in range(len(numbers) - 1))


# ============================================================
# Stijlen
# ============================================================

def extract_styles(content_pages: list[ClassifiedPage]) -> dict[str, dict]:
    """Extraheer tekststijlen uit content pagina's.

    Returns:
        Dict met Heading1, Heading2, Heading3, Normal stijlen.
    """
    if not content_pages:
        return {}

    # Groepeer per (font, afgeronde size, color)
    style_groups: Counter = Counter()
    for cp in content_pages:
        for t in cp.page.texts:
            key = (t.font, round(t.size, 1), t.color_hex)
            style_groups[key] += 1

    # Meet leading per stijl
    leadings: dict[tuple, list[float]] = {}
    for cp in content_pages:
        texts = sorted(cp.page.texts, key=lambda t: (t.x, t.y_top))
        for i in range(len(texts) - 1):
            t1 = texts[i]
            t2 = texts[i + 1]
            key1 = (t1.font, round(t1.size, 1), t1.color_hex)
            key2 = (t2.font, round(t2.size, 1), t2.color_hex)
            if key1 == key2 and abs(t1.x - t2.x) < 5:
                diff = t2.y_top - t1.y_top
                if 1 < diff < 50:  # redelijke leading
                    leadings.setdefault(key1, []).append(diff)

    # Sorteer groepen op size
    all_styles = sorted(style_groups.keys(), key=lambda k: k[1], reverse=True)

    # Filter stijlen met minimaal 3 voorkomens
    all_styles = [s for s in all_styles if style_groups[s] >= 3]

    result: dict[str, dict] = {}

    # Heading1: grootste font (>= 16pt)
    for s in all_styles:
        if s[1] >= 16:
            result["Heading1"] = _style_dict(s, leadings)
            break

    # Heading2: 12-16pt
    for s in all_styles:
        if 12 <= s[1] < 16 and s != _key_for("Heading1", result):
            result["Heading2"] = _style_dict(s, leadings)
            break

    # Normal: meest voorkomende < 12pt
    normal_styles = [(s, style_groups[s]) for s in all_styles if s[1] < 12]
    normal_styles.sort(key=lambda x: x[1], reverse=True)
    if normal_styles:
        result["Normal"] = _style_dict(normal_styles[0][0], leadings)

    # Heading3: tussen Normal en Heading2
    normal_size = result.get("Normal", {}).get("size", 10)
    h2_size = result.get("Heading2", {}).get("size", 14)
    for s in all_styles:
        if normal_size < s[1] < h2_size and s not in [
            _key_for(n, result) for n in result
        ]:
            result["Heading3"] = _style_dict(s, leadings)
            break

    return result


def _style_dict(key: tuple, leadings: dict) -> dict:
    """Maak een stijl dict van een (font, size, color) tuple."""
    font, size, color = key
    leading_values = leadings.get(key, [])
    leading = round(median(leading_values), 1) if leading_values else round(size * 1.2, 1)
    return {
        "font": font,
        "size": size,
        "color": color,
        "leading": leading,
    }


def _key_for(name: str, result: dict) -> tuple | None:
    """Haal de originele key tuple op voor een stijlnaam."""
    style = result.get(name)
    if style:
        return (style["font"], style["size"], style["color"])
    return None


# ============================================================
# Tabelstijlen
# ============================================================

def detect_table_styles(content_pages: list[ClassifiedPage]) -> dict | None:
    """Detecteer tabelstijlen uit content pagina's.

    Returns:
        Dict met header_bg, header_text, footer_bg of None.
    """
    if not content_pages:
        return None

    # Zoek gekleurde rects met tekst erin
    header_colors: Counter = Counter()
    header_text_colors: Counter = Counter()
    footer_colors: Counter = Counter()

    for cp in content_pages:
        p = cp.page
        for r in p.rects:
            if r.fill_hex is None or r.element_type != "rect":
                continue
            if _is_near_white(r.fill_hex) or _is_near_black(r.fill_hex):
                continue
            if r.width < 50 or r.height < 8 or r.height > 50:
                continue

            # Zoek tekst die overlapt
            overlapping_texts = [
                t for t in p.texts
                if t.x >= r.x - 5
                and t.x2 <= r.x + r.width + 5
                and t.y_top >= r.y - 5
                and t.y_bottom <= r.y + r.height + 5
            ]
            if overlapping_texts:
                rgb = _hex_to_rgb(r.fill_hex)
                brightness = sum(rgb)
                if brightness < 384:
                    header_colors[r.fill_hex] += 1
                    for t in overlapping_texts:
                        header_text_colors[t.color_hex] += 1
                else:
                    footer_colors[r.fill_hex] += 1

    if not header_colors:
        return None

    result: dict[str, str] = {
        "header_bg": header_colors.most_common(1)[0][0],
    }
    if header_text_colors:
        result["header_text"] = header_text_colors.most_common(1)[0][0]
    if footer_colors:
        result["footer_bg"] = footer_colors.most_common(1)[0][0]

    return result
