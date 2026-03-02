#!/usr/bin/env python3
"""
Brand Extractor — Pixel-precieze extractie van huisstijl-elementen uit PDF.

Standalone script, geen openaec_reports dependencies.
Vereist: pip install PyMuPDF

Gebruik:
    python brand_extractor.py <pdf_path> [--output <json_path>] [--render-pages <output_dir>] [--dpi 150]

Output: JSON met per pagina alle visuele elementen:
    - texts: font, size, color, exacte bbox (pt)
    - rects: positie, fill/stroke kleur, corner radius
    - paths: polygonen, beziers met alle punten
    - images: positie, afmetingen, xref
    - page_meta: breedte, hoogte in pt en mm

Coordinaten: PDF-native (origin linksonder, y omhoog).
De SKILL.md beschrijft hoe Claude deze data interpreteert naar brand.yaml.
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: PyMuPDF is vereist. Installeer met: pip install PyMuPDF", file=sys.stderr)
    sys.exit(1)


# =============================================================================
# EXTRACTIE FUNCTIES
# =============================================================================

def color_int_to_hex(color_int: int) -> str:
    """Converteer PyMuPDF integer kleur naar hex string."""
    r = (color_int >> 16) & 0xFF
    g = (color_int >> 8) & 0xFF
    b = color_int & 0xFF
    return f"#{r:02X}{g:02X}{b:02X}"


def color_tuple_to_hex(color: tuple | list | None) -> str | None:
    """Converteer float RGB tuple (0-1) naar hex string."""
    if color is None or len(color) < 3:
        return None
    r, g, b = color[:3]
    return f"#{int(r * 255):02X}{int(g * 255):02X}{int(b * 255):02X}"


def extract_texts(page) -> list[dict]:
    """Extraheer alle tekst spans met exacte posities en styling."""
    texts = []
    text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

    for block in text_dict.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not text:
                    continue

                bbox = span.get("bbox", (0, 0, 0, 0))
                texts.append({
                    "text": text,
                    "font": span.get("font", ""),
                    "size": round(span.get("size", 0), 2),
                    "color": color_int_to_hex(span.get("color", 0)),
                    "bold": bool(span.get("flags", 0) & 2**4),  # bit 4 = bold
                    "italic": bool(span.get("flags", 0) & 2**1),  # bit 1 = italic
                    "bbox": {
                        "x0": round(bbox[0], 2),
                        "y0": round(bbox[1], 2),  # top (PDF coords)
                        "x1": round(bbox[2], 2),
                        "y1": round(bbox[3], 2),  # bottom (PDF coords)
                    },
                    "width": round(bbox[2] - bbox[0], 2),
                    "height": round(bbox[3] - bbox[1], 2),
                })

    return texts


def extract_rects(page, page_width: float, page_height: float) -> list[dict]:
    """Extraheer rechthoeken en lijnen."""
    rects = []

    for drawing in page.get_drawings():
        items = drawing.get("items", [])
        rect = drawing.get("rect")
        if rect is None:
            continue

        x0, y0 = rect.x0, rect.y0
        w = rect.x1 - rect.x0
        h = rect.y1 - rect.y0

        if w <= 0 and h <= 0:
            continue

        fill_hex = color_tuple_to_hex(drawing.get("fill"))
        stroke_hex = color_tuple_to_hex(drawing.get("color"))
        stroke_width = drawing.get("width", 0)

        # Classificeer
        element_type = "line" if (abs(w) < 2 or abs(h) < 2) else "rect"

        # Detecteer corner radius
        corner_radius = detect_corner_radius(items)

        # Skip pagina-vullende witte rects
        is_page_filling = abs(w) > 0.9 * page_width and abs(h) > 0.9 * page_height
        if is_page_filling and (fill_hex is None or fill_hex.upper() in ("#FFFFFF", "#FEFEFE", "#FDFDFD")):
            continue

        rects.append({
            "type": element_type,
            "x": round(x0, 2),
            "y": round(y0, 2),
            "width": round(abs(w), 2),
            "height": round(abs(h), 2),
            "fill": fill_hex,
            "stroke": stroke_hex,
            "stroke_width": round(stroke_width, 2),
            "corner_radius": round(corner_radius, 1),
        })

    return rects


def detect_corner_radius(items: list) -> float:
    """Detecteer corner radius uit drawing items."""
    curve_count = sum(1 for item in items if item[0] == "c")
    if curve_count < 4:
        return 0.0

    for item in items:
        if item[0] == "c":
            try:
                p1 = item[1]
                p2 = item[4]
                dx = abs(p2.x - p1.x)
                dy = abs(p2.y - p1.y)
                radius = max(dx, dy)
                if radius > 0.5:
                    return round(radius, 1)
            except (IndexError, AttributeError):
                pass
    return 0.0


def extract_paths(page) -> list[dict]:
    """Extraheer vector paths (polygonen, beziers)."""
    paths = []

    for drawing in page.get_drawings():
        items = drawing.get("items", [])
        if not items:
            continue

        points = []
        has_curves = False
        has_rect_only = True

        for item in items:
            item_type = item[0]
            if item_type == "l":  # line to
                points.append((round(item[1].x, 2), round(item[1].y, 2)))
                points.append((round(item[2].x, 2), round(item[2].y, 2)))
                has_rect_only = False
            elif item_type == "c":  # cubic bezier
                points.append((round(item[1].x, 2), round(item[1].y, 2)))
                # control points
                points.append((round(item[2].x, 2), round(item[2].y, 2)))
                points.append((round(item[3].x, 2), round(item[3].y, 2)))
                points.append((round(item[4].x, 2), round(item[4].y, 2)))
                has_curves = True
                has_rect_only = False
            elif item_type == "re":
                continue
            elif item_type == "qu":  # quad
                for qi in range(1, 5):
                    q = item[qi]
                    points.append((round(q.x, 2), round(q.y, 2)))
                has_rect_only = False

        if has_rect_only or len(points) < 3:
            continue

        # Dedup opeenvolgende identieke punten
        deduped = [points[0]]
        for p in points[1:]:
            if abs(p[0] - deduped[-1][0]) > 0.1 or abs(p[1] - deduped[-1][1]) > 0.1:
                deduped.append(p)

        if len(deduped) < 3:
            continue

        fill_hex = color_tuple_to_hex(drawing.get("fill"))
        stroke_hex = color_tuple_to_hex(drawing.get("color"))

        xs = [p[0] for p in deduped]
        ys = [p[1] for p in deduped]

        paths.append({
            "path_type": "bezier" if has_curves else "polygon",
            "points": deduped,
            "fill": fill_hex,
            "stroke": stroke_hex,
            "stroke_width": round(drawing.get("width", 0), 2),
            "is_closed": drawing.get("closePath", False),
            "bbox": {
                "x": round(min(xs), 2),
                "y": round(min(ys), 2),
                "width": round(max(xs) - min(xs), 2),
                "height": round(max(ys) - min(ys), 2),
            },
        })

    return paths


def extract_images(page) -> list[dict]:
    """Extraheer afbeeldingen met posities."""
    images = []

    for img_info in page.get_images(full=True):
        xref = img_info[0]
        try:
            img_rects = page.get_image_rects(xref)
            if img_rects:
                r = img_rects[0]
                images.append({
                    "xref": xref,
                    "x": round(r.x0, 2),
                    "y": round(r.y0, 2),
                    "width": round(r.width, 2),
                    "height": round(r.height, 2),
                    "native_width": img_info[2],
                    "native_height": img_info[3],
                })
        except Exception:
            pass

    return images


def extract_fonts_summary(pages_data: list[dict]) -> dict:
    """Maak een samenvatting van alle gebruikte fonts met hun contexten."""
    font_usage = {}

    for page_data in pages_data:
        for text in page_data["texts"]:
            font = text["font"]
            size = text["size"]
            color = text["color"]
            key = f"{font}_{size}_{color}"

            if key not in font_usage:
                font_usage[key] = {
                    "font": font,
                    "size": size,
                    "color": color,
                    "bold": text["bold"],
                    "italic": text["italic"],
                    "count": 0,
                    "sample_texts": [],
                    "pages": set(),
                }

            font_usage[key]["count"] += 1
            font_usage[key]["pages"].add(page_data["page_number"])
            if len(font_usage[key]["sample_texts"]) < 3:
                sample = text["text"][:60]
                if sample not in font_usage[key]["sample_texts"]:
                    font_usage[key]["sample_texts"].append(sample)

    # Converteer sets naar lists voor JSON
    result = []
    for key, data in sorted(font_usage.items(), key=lambda x: -x[1]["count"]):
        data["pages"] = sorted(data["pages"])
        result.append(data)

    return result


def extract_colors_summary(pages_data: list[dict]) -> dict:
    """Maak een samenvatting van alle gebruikte kleuren."""
    colors = {}

    # Tekst kleuren
    for page_data in pages_data:
        for text in page_data["texts"]:
            c = text["color"]
            if c not in colors:
                colors[c] = {"hex": c, "used_in": [], "count": 0}
            colors[c]["count"] += 1
            if "text" not in colors[c]["used_in"]:
                colors[c]["used_in"].append("text")

        # Rect fills
        for rect in page_data["rects"]:
            if rect["fill"]:
                c = rect["fill"]
                if c not in colors:
                    colors[c] = {"hex": c, "used_in": [], "count": 0}
                colors[c]["count"] += 1
                ctx = f"rect_fill_{rect['type']}"
                if ctx not in colors[c]["used_in"]:
                    colors[c]["used_in"].append(ctx)

        # Path fills
        for path in page_data["paths"]:
            if path["fill"]:
                c = path["fill"]
                if c not in colors:
                    colors[c] = {"hex": c, "used_in": [], "count": 0}
                colors[c]["count"] += 1
                if "path_fill" not in colors[c]["used_in"]:
                    colors[c]["used_in"].append("path_fill")

    return sorted(colors.values(), key=lambda x: -x["count"])


# =============================================================================
# HOOFD EXTRACTIE
# =============================================================================

def extract_brand_data(pdf_path: str, render_dir: str | None = None, dpi: int = 150) -> dict:
    """Extraheer alle brand-relevante data uit een PDF.

    Args:
        pdf_path: Pad naar het huisstijl PDF bestand.
        render_dir: Optionele map voor pagina PNG renders.
        dpi: DPI voor pagina renders.

    Returns:
        Dict met volledige extractie data.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF niet gevonden: {pdf_path}")

    if render_dir:
        render_dir = Path(render_dir)
        render_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    pages_data = []

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        pw = page.rect.width
        ph = page.rect.height

        # Render pagina
        page_image_path = None
        if render_dir:
            pix = page.get_pixmap(dpi=dpi)
            img_path = render_dir / f"page_{page_idx + 1:03d}.png"
            pix.save(str(img_path))
            page_image_path = str(img_path)

        page_data = {
            "page_number": page_idx + 1,
            "meta": {
                "width_pt": round(pw, 2),
                "height_pt": round(ph, 2),
                "width_mm": round(pw / 2.8346, 1),
                "height_mm": round(ph / 2.8346, 1),
            },
            "texts": extract_texts(page),
            "rects": extract_rects(page, pw, ph),
            "paths": extract_paths(page),
            "images": extract_images(page),
        }

        if page_image_path:
            page_data["render"] = page_image_path

        pages_data.append(page_data)

    doc.close()

    # Samenvattingen
    result = {
        "source": str(pdf_path),
        "total_pages": len(pages_data),
        "document_format": {
            "width_pt": pages_data[0]["meta"]["width_pt"] if pages_data else 0,
            "height_pt": pages_data[0]["meta"]["height_pt"] if pages_data else 0,
            "width_mm": pages_data[0]["meta"]["width_mm"] if pages_data else 0,
            "height_mm": pages_data[0]["meta"]["height_mm"] if pages_data else 0,
        },
        "fonts_summary": extract_fonts_summary(pages_data),
        "colors_summary": extract_colors_summary(pages_data),
        "pages": pages_data,
    }

    return result


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Brand Extractor — Pixel-precieze huisstijl extractie uit PDF"
    )
    parser.add_argument("pdf_path", help="Pad naar het PDF bestand")
    parser.add_argument("--output", "-o", help="Output JSON pad (default: <pdf_naam>_brand_extract.json)")
    parser.add_argument("--render-pages", "-r", help="Map voor pagina PNG renders")
    parser.add_argument("--dpi", type=int, default=150, help="DPI voor pagina renders (default: 150)")
    parser.add_argument("--pretty", action="store_true", default=True, help="Pretty-print JSON (default: True)")
    parser.add_argument("--compact", action="store_true", help="Compact JSON output")
    parser.add_argument("--pages", help="Specifieke pagina's (bijv: 1,2,3,36)")

    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"ERROR: Bestand niet gevonden: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    # Output pad
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = pdf_path.parent / f"{pdf_path.stem}_brand_extract.json"

    print(f"Extracting brand data from: {pdf_path}")
    print(f"Output: {output_path}")

    if args.render_pages:
        print(f"Rendering pages to: {args.render_pages} @ {args.dpi} DPI")

    # Extractie
    data = extract_brand_data(str(pdf_path), args.render_pages, args.dpi)

    # Filter specifieke pagina's indien opgegeven
    if args.pages:
        page_nums = [int(p.strip()) for p in args.pages.split(",")]
        data["pages"] = [p for p in data["pages"] if p["page_number"] in page_nums]
        data["filtered_pages"] = page_nums
        # Herbereken summaries
        data["fonts_summary"] = extract_fonts_summary(data["pages"])
        data["colors_summary"] = extract_colors_summary(data["pages"])

    # Schrijf JSON
    indent = None if args.compact else 2
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)

    # Rapportage
    print(f"\nDone! {data['total_pages']} pagina's geanalyseerd")
    print(f"  Unieke font-stijlen: {len(data['fonts_summary'])}")
    print(f"  Unieke kleuren: {len(data['colors_summary'])}")

    total_texts = sum(len(p["texts"]) for p in data["pages"])
    total_rects = sum(len(p["rects"]) for p in data["pages"])
    total_paths = sum(len(p["paths"]) for p in data["pages"])
    total_images = sum(len(p["images"]) for p in data["pages"])
    print(f"  Totaal: {total_texts} teksten, {total_rects} rects, {total_paths} paths, {total_images} images")


if __name__ == "__main__":
    main()
