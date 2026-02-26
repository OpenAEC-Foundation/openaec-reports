"""TOC mockup: standaard.pdf + "Inhoud" titel + TOC entries."""
import fitz
from pathlib import Path

OUT_DIR = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\test_output")
STANDAARD_PDF = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\paginas\standaard.pdf")
FONT_DIR = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src\bm_reports\assets\fonts")
OUTPUT_PDF = OUT_DIR / "toc_mockup.pdf"

COLOR_DARK = (0.271, 0.141, 0.239)    # #45243D
COLOR_TEAL = (0.337, 0.706, 0.608)    # #56B49B

doc = fitz.open(str(STANDAARD_PDF))
page = doc[0]
page.insert_font(fontname="GothamBook", fontfile=str(FONT_DIR / "Gotham-Book.ttf"))

# Helper
def text(x, y_td, txt, size, color):
    page.insert_text((x, y_td + size * 0.8), txt, fontname="GothamBook", fontsize=size, color=color)

# Titel
text(90.0, 74.9, "Inhoud", 18.0, COLOR_DARK)

# Voorbeeld TOC entries (chapter = teal 12pt, section = dark 9.5pt)
entries = [
    # (level, number, title, page, y_td)
    (1, "", "Bijbehorende tekeningen en bijlagen:", "4", 127.2),
    (2, "1.1", "Toegepaste documenten:", "4", 147.4),
    (2, "1.2", "Wetten, besluiten en regelingen:", "4", 164.8),
    (2, "1.3", "NEN normen. Direct aangestuurde normbladen (1e Lijns)", "4", 182.0),
    (1, "2", "Inleiding", "5", 218.7),
    (1, "3", "Samenvatting", "7", 258.2),
    (2, "3.1", "Bruikbaarheid:", "7", 278.4),
    (2, "3.2", "Ventilatie:", "7", 295.7),
    (2, "3.3", "Brandveiligheid en vluchten:", "7", 313.0),
    (2, "3.4", "Parkeren", "7", 330.4),
    (1, "4", "Oppervlakte toets en daglichtberekening", "8", 367.0),
    (2, "4.1", "conclusie", "8", 387.1),
    (1, "5", "Brandveiligheid", "9", 423.8),
    (2, "5.1", "Indeling in brandcompartimenten", "9", 444.0),
    (2, "5.2", "Indeling in subbrandcompartimenten", "11", 461.3),
    (2, "5.3", "WRD eisen", "11", 478.6),
    (2, "5.4", "Wbdbo en brandwerendheid.", "12", 495.9),
    (1, "6", "Veilig Vluchten", "16", 532.6),
    (2, "6.1", "Vluchtroute", "16", 552.8),
    (2, "6.2", "inrichting en afmetingen vluchtroutes", "16", 570.1),
    (1, "7", "Parkeren.", "20", 606.8),
    (1, "8", "bouwbesluit toets en daglichttoetsing", "21", 646.3),
]

for level, num, title, pg, y_td in entries:
    if level == 1:
        color, size = COLOR_TEAL, 12.0
    else:
        color, size = COLOR_DARK, 9.5
    
    if num:
        text(90.0, y_td, num, size, color)
    text(160.9, y_td, title, size, color)
    text(515.4, y_td, pg, size, color)

# Paginanummer
text(533.0, 793.5, "3", 9.5, COLOR_DARK)

doc.save(str(OUTPUT_PDF))
doc.close()
print(f"DONE: {OUTPUT_PDF}")
