"""Standaard pagina mockup: standaard.pdf + paginanummer."""
import fitz
from pathlib import Path

OUT_DIR = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\test_output")
STANDAARD_PDF = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\paginas\standaard.pdf")
FONT_DIR = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src\bm_reports\assets\fonts")
OUTPUT_PDF = OUT_DIR / "standaard_mockup.pdf"

# Check paginanummer positie uit BBL rapport (pagina 3 = eerste content)
bbl = fitz.open(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\2707_BBLrapportage_v01.pdf")
for pg_idx in [2, 3, 4]:  # pagina 3,4,5
    p = bbl[pg_idx]
    for block in p.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                t = span["text"].strip()
                if t.isdigit() and span["bbox"][1] > 780:  # paginanummer = onderaan
                    bbox = span["bbox"]
                    c = span["color"]
                    r = (c >> 16) & 0xFF; g = (c >> 8) & 0xFF; b = c & 0xFF
                    print(f"Pagina {pg_idx+1}: \"{t}\" @ x={bbox[0]:.1f} y_td={bbox[1]:.1f} font={span['font']} size={span['size']:.1f} color=#{r:02X}{g:02X}{b:02X}")
bbl.close()

# === Mockup genereren ===
doc = fitz.open(str(STANDAARD_PDF))
page = doc[0]
page.insert_font(fontname="GothamBook", fontfile=str(FONT_DIR / "Gotham-Book.ttf"))

# Paginanummer: Gotham-Book 9.5pt #45243D @ x=533, y_td=793.5
COLOR_DARK = (0.271, 0.141, 0.239)  # #45243D
page.insert_text((533.0, 793.5 + 9.5 * 0.8), "5",
                  fontname="GothamBook", fontsize=9.5, color=COLOR_DARK)

doc.save(str(OUTPUT_PDF))
doc.close()
print(f"DONE: {OUTPUT_PDF}")
