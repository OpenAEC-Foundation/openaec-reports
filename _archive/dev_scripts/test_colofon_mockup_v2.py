"""Colofon mockup v2: colofon.pdf als achtergrond + alleen dynamische waarden overlay."""
import sys
sys.path.insert(0, r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src")

import fitz
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

OUT_DIR = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\test_output")
COLOFON_PDF = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\paginas\colofon.pdf")
OUTPUT_PDF = OUT_DIR / "colofon_mockup_v2.pdf"

# Fonts
font_dir = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src\bm_reports\assets\fonts")
for name, fn in {"GothamBold": "Gotham-Bold.ttf", "GothamBook": "Gotham-Book.ttf"}.items():
    pdfmetrics.registerFont(TTFont(name, str(font_dir / fn)))

# === Overlay: alleen dynamische waarden ===
buf = io.BytesIO()
w, h = 595.3, 841.9
c = canvas.Canvas(buf, pagesize=(w, h))

PURPLE = HexColor("#401246")
TEAL = HexColor("#38BDAB")

# Titel + subtitel (bovenaan)
c.setFont("GothamBold", 22)
c.setFillColor(PURPLE)
c.drawString(70.9, 784.6, "BBL-toetsingsrapportage")

c.setFont("GothamBook", 14)
c.setFillColor(TEAL)
c.drawString(70.9, 755.1, "Transformatie Data center Spaarneplein Den Haag")

# Tabelwaarden (rechterkolom x=229.1)
c.setFont("GothamBook", 10)
c.setFillColor(PURPLE)

values = [
    # (text, y_pdf) - of (lines[], y_pdf, line_height) voor multiline
    ("2707 - Transformatie Data center Spaarneplein Den Haag", 520.8),
    # Opdrachtgever multiline
    (["Mounir Riffi MSc", "Sping Real Estate", "Lange Voorhout 46,", "2514 EG Den Haag"], 472.8, 12.8),
    ("3BM Cooperatie", 352.8),
    ("J. Kolthof (Jochem)", 340.8),
    ("BBL, NEN 2057, NEN 2580, NEN1087", 316.8),
    ("BBL-toetsing, pg 1-19 (excl. Bijlagen)", 292.8),
    ("05-07-2025", 268.8),
    ("Haalbaarheidsstudie", 244.8),
    ("concept", 220.8),
    ("2707-BBL-01", 196.8),
]

for v in values:
    if isinstance(v[0], list):
        lines, y0, lh = v
        for i, line in enumerate(lines):
            c.drawString(229.1, y0 - (i * lh), line)
    else:
        text, y = v
        c.drawString(229.1, y, text)

# Paginanummer
c.setFont("GothamBold", 8)
c.setFillColor(TEAL)
c.drawString(534.0, 45.6, "2")

c.save()
buf.seek(0)

# === Merge: colofon.pdf + overlay ===
bg = fitz.open(str(COLOFON_PDF))
overlay = fitz.open("pdf", buf.read())
bg[0].show_pdf_page(bg[0].rect, overlay, 0, overlay=True)
bg.save(str(OUTPUT_PDF))
bg.close()
overlay.close()

print(f"DONE: {OUTPUT_PDF}")
