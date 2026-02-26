"""Colofon mockup v3: tekst direct op colofon.pdf met PyMuPDF insert_text."""
import fitz
from pathlib import Path

OUT_DIR = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\test_output")
COLOFON_PDF = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\paginas\colofon.pdf")
FONT_DIR = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src\bm_reports\assets\fonts")
OUTPUT_PDF = OUT_DIR / "colofon_mockup_v3.pdf"

COLOR_PURPLE = (0.251, 0.071, 0.275)
COLOR_TEAL = (0.220, 0.741, 0.671)

doc = fitz.open(str(COLOFON_PDF))
page = doc[0]

# Registreer fonts in PDF
font_bold_name = page.insert_font(fontname="GothamBold", fontfile=str(FONT_DIR / "Gotham-Bold.ttf"))
font_book_name = page.insert_font(fontname="GothamBook", fontfile=str(FONT_DIR / "Gotham-Book.ttf"))

# insert_text: point = (x, y) waar y = baseline in top-down coords
# Onze y_td extractie-waarden zijn bbox-top, baseline ~= y_td + fontsize * 0.8

# === Titel + subtitel ===
page.insert_text((70.9, 57.3 + 22 * 0.8), "BBL-toetsingsrapportage",
                  fontname="GothamBold", fontsize=22, color=COLOR_PURPLE)
page.insert_text((70.9, 86.8 + 14 * 0.8), "Transformatie Data center Spaarneplein Den Haag",
                  fontname="GothamBook", fontsize=14, color=COLOR_TEAL)

# === Tabelwaarden (rechterkolom x=229.1) ===
# y_td = bbox top, baseline offset = fontsize * 0.8
values = [
    ("2707 - Transformatie Data center Spaarneplein Den Haag", 321.1),
    ("Mounir Riffi MSc", 369.1),
    ("Sping Real Estate", 381.8),
    ("Lange Voorhout 46,", 394.6),
    ("2514 EG Den Haag", 407.2),
    ("3BM Cooperatie", 489.1),
    ("J. Kolthof (Jochem)", 501.1),
    ("BBL, NEN 2057, NEN 2580, NEN1087", 525.1),
    ("BBL-toetsing, pg 1-19 (excl. Bijlagen)", 549.1),
    ("05-07-2025", 573.1),
    ("Haalbaarheidsstudie", 597.1),
    ("concept", 621.1),
    ("2707-BBL-01", 645.1),
]

for text, y_td in values:
    page.insert_text((229.1, y_td + 10 * 0.8), text,
                      fontname="GothamBook", fontsize=10, color=COLOR_PURPLE)

# Paginanummer
page.insert_text((534.0, 796.3 + 8 * 0.8), "2",
                  fontname="GothamBold", fontsize=8, color=COLOR_TEAL)

doc.save(str(OUTPUT_PDF))
doc.close()
print(f"DONE: {OUTPUT_PDF}")
