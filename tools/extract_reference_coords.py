"""Analyseer symitech_bic_test.pdf en extraheer tekst-coordinaten per pagina.

Output: JSON met per pagina alle tekstelementen + hun exacte positie.
Doel: coordinaten meten voor page_type YAML's.

Usage:
    python tools/extract_reference_coords.py
"""

from __future__ import annotations

import json
from pathlib import Path

import fitz

# Conversie: 1 pt = 0.3528 mm  (mm = pt / 2.8346)
PT_TO_MM = 1.0 / 2.8346

# Pagina-mapping uit de prompt
PAGE_MAP = {
    0: "voorblad_bic",
    1: "locatie",
    2: "bic_controles",
    3: "detail_weergave",
    4: "objecten",
    5: "achterblad",
}

# Bekende dynamische data patronen — text die per rapport verschilt
DYNAMIC_PATTERNS = [
    # Locatie/client data
    "Schoolweg", "1234 AB", "Meppel", "VVE Schoolweg", "LOC-001",
    "brandblus", "hoofdgebouw",
    # Getallen/bedragen
    "€", ",00", ".00",
    # Datums
    "2024", "2025", "2026",
    # BIC codes
    "BIC-", "INT-",
    # Generiek
    "Ja", "Nee", "Conform", "Afwijkend",
]

# Bekende statische labels
STATIC_PATTERNS = [
    "Opdrachtgever", "Locatie", "LOCATIE", "OPDRACHTGEVER",
    "Naam", "Adres", "Plaats", "Locatiecode", "Voorziening", "Object",
    "Conform opdracht", "Werkelijke kosten",
    "Detail weergave", "Voorziening en objecten",
    "BIC Controle nummer", "Type", "Datum", "BIC controle",
    "Int. inspectie", "Reiniging", "Additioneel",
    "Status", "Beschrijving", "Gebouw",
    "Locatie van uitvoer",
]


def classify_text(text: str) -> str:
    """Classify text as static or dynamic."""
    stripped = text.strip()
    if not stripped:
        return "empty"

    # Check static patterns first (headers, labels)
    for pattern in STATIC_PATTERNS:
        if pattern.lower() in stripped.lower():
            return "static"

    # Check dynamic patterns
    for pattern in DYNAMIC_PATTERNS:
        if pattern in stripped:
            return "dynamic"

    # Heuristic: short uppercase text is likely a header/label
    if stripped.isupper() and len(stripped) < 30:
        return "static"

    # Numbers with decimals are likely data
    if any(c.isdigit() for c in stripped):
        return "dynamic"

    return "unknown"


def color_to_hex(color_value: int | float | tuple) -> str:
    """Convert PyMuPDF color to hex string."""
    if isinstance(color_value, (int, float)):
        # Grayscale
        v = int(color_value * 255)
        return f"#{v:02X}{v:02X}{v:02X}"
    if isinstance(color_value, (list, tuple)):
        if len(color_value) == 3:
            r, g, b = [int(c * 255) if isinstance(c, float) and c <= 1.0
                        else int(c) for c in color_value]
            return f"#{r:02X}{g:02X}{b:02X}"
    return "#000000"


def extract_page_text_elements(page: fitz.Page, page_num: int) -> list[dict]:
    """Extract all text elements from a page with position info."""
    elements = []
    text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

    for block in text_dict.get("blocks", []):
        if block.get("type") != 0:  # Skip image blocks
            continue

        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not text:
                    continue

                x_pt = span["origin"][0]
                y_pt = span["origin"][1]
                bbox = span["bbox"]
                font = span.get("font", "")
                size = round(span.get("size", 0), 1)
                color_int = span.get("color", 0)

                # Convert color int to hex
                r = (color_int >> 16) & 0xFF
                g = (color_int >> 8) & 0xFF
                b = color_int & 0xFF
                color_hex = f"#{r:02X}{g:02X}{b:02X}"

                elements.append({
                    "text": text,
                    "x_pt": round(x_pt, 2),
                    "y_pt": round(y_pt, 2),
                    "x_mm": round(x_pt * PT_TO_MM, 1),
                    "y_mm": round(y_pt * PT_TO_MM, 1),
                    "bbox_pt": [round(v, 2) for v in bbox],
                    "bbox_mm": [round(v * PT_TO_MM, 1) for v in bbox],
                    "font": font,
                    "size": size,
                    "color": color_hex,
                    "classification": classify_text(text),
                })

    return elements


def main() -> None:
    """Main entry point."""
    project_root = Path(__file__).resolve().parent.parent
    source_pdf = project_root / "output" / "symitech_bic_test.pdf"
    output_file = project_root / "output" / "reference_coords.json"

    if not source_pdf.exists():
        print(f"ERROR: Referentie-PDF niet gevonden: {source_pdf}")
        return

    doc = fitz.open(str(source_pdf))
    result = {
        "source": str(source_pdf.name),
        "page_count": doc.page_count,
        "pages": [],
    }

    for page_num in range(doc.page_count):
        page = doc[page_num]
        rect = page.rect
        page_type = PAGE_MAP.get(page_num, f"unknown_page_{page_num}")

        elements = extract_page_text_elements(page, page_num)

        page_data = {
            "page_num": page_num,
            "page_type": page_type,
            "width_pt": round(rect.width, 2),
            "height_pt": round(rect.height, 2),
            "width_mm": round(rect.width * PT_TO_MM, 1),
            "height_mm": round(rect.height * PT_TO_MM, 1),
            "orientation": "landscape" if rect.width > rect.height else "portrait",
            "element_count": len(elements),
            "elements": elements,
        }

        result["pages"].append(page_data)

        # Print summary
        print(f"\n=== Pagina {page_num}: {page_type} ({page_data['orientation']}) ===")
        print(f"    Formaat: {page_data['width_mm']}x{page_data['height_mm']} mm")
        print(f"    Elementen: {len(elements)}")

        for elem in elements:
            cls = elem["classification"]
            marker = "S" if cls == "static" else "D" if cls == "dynamic" else "?"
            print(f"    [{marker}] x={elem['x_mm']:6.1f} y={elem['y_mm']:6.1f} "
                  f"size={elem['size']:4.1f} color={elem['color']} "
                  f"font={elem['font'][:20]:20s} | {elem['text'][:60]}")

    doc.close()

    # Save JSON
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n\nOutput opgeslagen: {output_file}")
    print(f"Totaal pagina's: {result['page_count']}")


if __name__ == "__main__":
    main()
