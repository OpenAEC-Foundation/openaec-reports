"""Colofon mockup: standaard.pdf achtergrond + colofon content overlay."""
import sys
sys.path.insert(0, r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src")

import fitz  # PyMuPDF
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io, yaml

OUT_DIR = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\test_output")
STANDAARD_PDF = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\paginas\standaard.pdf")
YAML_PATH = OUT_DIR / "colofon_template.yaml"
OUTPUT_PDF = OUT_DIR / "colofon_mockup.pdf"

# Font registratie
font_dir = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src\bm_reports\assets\fonts")
for name, filename in {"GothamBold": "Gotham-Bold.ttf", "GothamBook": "Gotham-Book.ttf", "GothamMedium": "Gotham-Medium.ttf", "GothamBookItalic": "Gotham-BookItalic.ttf"}.items():
    fp = font_dir / filename
    if fp.exists():
        pdfmetrics.registerFont(TTFont(name, str(fp)))
        print(f"  Font: {name}")

# Laad template
with open(YAML_PATH) as f:
    template = yaml.safe_load(f)

# === Stap 1: Maak ReportLab overlay PDF in memory ===
print("\nGenerating overlay...")
buf = io.BytesIO()
w, h = 595.3, 841.9
c = canvas.Canvas(buf, pagesize=(w, h))

# --- Colofon labels (linkerkolom, statisch) ---
# Deze staan NIET in standaard.pdf, dus we tekenen ze
TEAL = "#38BDAB"
PURPLE = "#401246"
LINE_COLOR = HexColor("#40124E")

labels = [
    # (label, x, y_pdf, color)
    ("Project", 103.0, 521.1, PURPLE),
    ("In opdracht van", 103.0, 473.1, PURPLE),
    ("Adviseur", 103.0, 353.1, TEAL),
    ("Toegepaste Normen", 103.0, 317.1, TEAL),
    ("Documentgegevens", 103.0, 293.1, TEAL),
    ("Datum rapport", 103.0, 269.1, TEAL),
    ("Fase in bouwproces", 103.0, 245.1, TEAL),
    ("Rapportstatus", 103.0, 221.1, TEAL),
    ("Documentkenmerk", 103.0, 197.1, TEAL),
]

for label_text, x, y, color in labels:
    c.setFont("GothamBold", 10)
    c.setFillColor(HexColor(color))
    c.drawString(x, y, label_text)

# --- Scheidingslijnen ---
lines_y = [324.3, 298.9, 275.7, 251.7, 227.0, 203.0]
c.setStrokeColor(LINE_COLOR)
c.setLineWidth(0.5)
for ly in lines_y:
    c.line(103.0, ly, 419.8, ly)

# --- Dynamische waarden (rechterkolom) ---
fields = template["text_fields"]
for field_name, field in fields.items():
    text = field["example"]
    x = field["x"]
    y = field["y"]
    font = field["font"]
    size = field["size"]
    color = HexColor(field["color"])
    
    # Map font namen
    font_rl = font
    if font == "GothamBook":
        font_rl = "GothamBook"
    elif font == "GothamBold":
        font_rl = "GothamBold"
    
    try:
        c.setFont(font_rl, size)
    except:
        c.setFont("Helvetica", size)
    
    c.setFillColor(color)
    
    # Multiline support
    if "\n" in text:
        line_h = field.get("line_height", size * 1.28)
        for i, line in enumerate(text.split("\n")):
            c.drawString(x, y - (i * line_h), line)
    else:
        c.drawString(x, y, text)

# --- Annotaties: rode kaders om dynamische zones ---
c.setStrokeColor(HexColor("#FF0000"))
c.setLineWidth(0.5)
c.setDash(2, 2)
for field_name, field in fields.items():
    x = field["x"]
    y = field["y"] - 3
    mw = field.get("max_width", 200)
    fh = field["size"] + 6
    if "\n" in field["example"]:
        n_lines = len(field["example"].split("\n"))
        fh = n_lines * field.get("line_height", field["size"] * 1.28) + 6
        y = y - (n_lines - 1) * field.get("line_height", field["size"] * 1.28)
    c.rect(x, y, mw, fh, fill=0, stroke=1)
    c.setFont("Helvetica", 5)
    c.setFillColor(HexColor("#FF0000"))
    c.drawString(x, y + fh + 1, f"YAML: {field_name}")

c.save()
buf.seek(0)

# === Stap 2: Merge overlay op standaard.pdf ===
print("Merging with standaard.pdf...")
bg = fitz.open(str(STANDAARD_PDF))
overlay = fitz.open("pdf", buf.read())

page = bg[0]
page.show_pdf_page(page.rect, overlay, 0, overlay=True)

bg.save(str(OUTPUT_PDF))
bg.close()
overlay.close()

print(f"\nDONE: {OUTPUT_PDF}")
