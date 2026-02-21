"""Bijlage divider mockup: bijlagen.pdf + nummer + titel."""
import fitz
from pathlib import Path

OUT_DIR = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\test_output")
BIJLAGEN_PDF = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\paginas\bijlagen.pdf")
FONT_DIR = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src\bm_reports\assets\fonts")
OUTPUT_PDF = OUT_DIR / "bijlage_mockup.pdf"

COLOR_PURPLE = (0.251, 0.071, 0.275)  # #401246
COLOR_WHITE = (1.0, 1.0, 1.0)

doc = fitz.open(str(BIJLAGEN_PDF))
page = doc[0]
page.insert_font(fontname="GothamBold", fontfile=str(FONT_DIR / "Gotham-Bold.ttf"))
page.insert_font(fontname="GothamBook", fontfile=str(FONT_DIR / "Gotham-Book.ttf"))

# Bijlage nummer
page.insert_text((103.0, 193.9 + 41.4 * 0.8), "Bijlage 1",
                  fontname="GothamBold", fontsize=41.4, color=COLOR_PURPLE)

# Bijlage titel (multiline)
lines = ["Bouwbesluittoets en", "daglichttoetsing"]
for i, line in enumerate(lines):
    y_td = 262.2 + i * 66.4  # 66.4pt regelhoogte uit extractie (328.6 - 262.2)
    page.insert_text((136.1, y_td + 41.4 * 0.8), line,
                      fontname="GothamBook", fontsize=41.4, color=COLOR_WHITE)

doc.save(str(OUTPUT_PDF))
doc.close()
print(f"DONE: {OUTPUT_PDF}")
