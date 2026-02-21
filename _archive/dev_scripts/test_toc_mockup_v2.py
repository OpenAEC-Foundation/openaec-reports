"""TOC mockup v2: dynamisch block - entries worden berekend, niet hardcoded."""
import fitz
import yaml
from pathlib import Path

OUT_DIR = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\test_output")
STANDAARD_PDF = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\paginas\standaard.pdf")
FONT_DIR = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src\bm_reports\assets\fonts")
YAML_PATH = OUT_DIR / "toc_template.yaml"
OUTPUT_PDF = OUT_DIR / "toc_mockup_v3.pdf"

with open(YAML_PATH) as f:
    tpl = yaml.safe_load(f)

# ===================================================================
# SIMULATIE: rapport structuur (dit komt straks uit de frontend JSON)
# ===================================================================
toc_entries = [
    {"level": 1, "number": "",    "title": "Bijbehorende tekeningen en bijlagen:", "page": 4},
    {"level": 2, "number": "1.1", "title": "Toegepaste documenten:", "page": 4},
    {"level": 2, "number": "1.2", "title": "Wetten, besluiten en regelingen:", "page": 4},
    {"level": 2, "number": "1.3", "title": "NEN normen. Direct aangestuurde normbladen (1e Lijns)", "page": 4},
    {"level": 1, "number": "2",   "title": "Inleiding", "page": 5},
    {"level": 1, "number": "3",   "title": "Samenvatting", "page": 7},
    {"level": 2, "number": "3.1", "title": "Bruikbaarheid:", "page": 7},
    {"level": 2, "number": "3.2", "title": "Ventilatie:", "page": 7},
    {"level": 2, "number": "3.3", "title": "Brandveiligheid en vluchten:", "page": 7},
    {"level": 2, "number": "3.4", "title": "Parkeren", "page": 7},
    {"level": 1, "number": "4",   "title": "Oppervlakte toets en daglichtberekening", "page": 8},
    {"level": 2, "number": "4.1", "title": "conclusie", "page": 8},
    {"level": 1, "number": "5",   "title": "Brandveiligheid", "page": 9},
    {"level": 2, "number": "5.1", "title": "Indeling in brandcompartimenten", "page": 9},
    {"level": 2, "number": "5.2", "title": "Indeling in subbrandcompartimenten", "page": 11},
    {"level": 2, "number": "5.3", "title": "WRD eisen", "page": 11},
    {"level": 2, "number": "5.4", "title": "Wbdbo en brandwerendheid.", "page": 12},
    {"level": 1, "number": "6",   "title": "Veilig Vluchten", "page": 16},
    {"level": 2, "number": "6.1", "title": "Vluchtroute", "page": 16},
    {"level": 2, "number": "6.2", "title": "inrichting en afmetingen vluchtroutes", "page": 16},
    {"level": 1, "number": "7",   "title": "Parkeren.", "page": 20},
    {"level": 1, "number": "8",   "title": "bouwbesluit toets en daglichttoetsing", "page": 21},
]

# ===================================================================
# DYNAMISCHE TOC RENDERER
# ===================================================================
COLOR_MAP = {}
for lvl_key, lvl_cfg in tpl["levels"].items():
    hex_color = lvl_cfg["color"]
    r = int(hex_color[1:3], 16) / 255
    g = int(hex_color[3:5], 16) / 255
    b = int(hex_color[5:7], 16) / 255
    COLOR_MAP[int(lvl_key)] = (r, g, b)

title_color_hex = tpl["title"]["color"]
TITLE_COLOR = tuple(int(title_color_hex[i:i+2], 16) / 255 for i in (1, 3, 5))
pn_color_hex = tpl["page_number"]["color"]
PN_COLOR = tuple(int(pn_color_hex[i:i+2], 16) / 255 for i in (1, 3, 5))

cols = tpl["columns"]
content = tpl["content_area"]

class TOCRenderer:
    def __init__(self, tpl):
        self.tpl = tpl
        self.pages = []       # lijst van fitz.Document pages
        self.current_page = None
        self.cursor_y = 0     # huidige y_td positie
        self.page_num = 3     # TOC begint op pagina 3
        
    def new_page(self):
        """Maak nieuwe pagina aan vanuit standaard.pdf."""
        doc = fitz.open(str(STANDAARD_PDF))
        page = doc[0]
        page.insert_font(fontname="GothamBook", fontfile=str(FONT_DIR / "Gotham-Book.ttf"))
        self.pages.append((doc, page))
        self.current_page = page
        
        if len(self.pages) == 1:
            # Eerste pagina: titel "Inhoud"
            t = self.tpl["title"]
            self._text(t["x"], t["y_td"], t["text"], t["size"], TITLE_COLOR)
            self.cursor_y = content["y_td_start"]
        else:
            # Vervolgpagina: start bovenaan content area
            self.cursor_y = content["y_td_start"]
    
    def _text(self, x, y_td, txt, size, color):
        self.current_page.insert_text(
            (x, y_td + size * 0.8), txt,
            fontname="GothamBook", fontsize=size, color=color
        )
    
    def add_entry(self, entry):
        """Voeg TOC entry toe, met automatische overflow."""
        level = entry["level"]
        lvl_cfg = self.tpl["levels"][level]
        size = lvl_cfg["size"]
        color = COLOR_MAP[level]
        spacing = lvl_cfg["spacing_before"]
        line_h = lvl_cfg["line_height"]
        indent = lvl_cfg.get("indent", 0)
        
        # Check overflow
        needed_y = self.cursor_y + spacing + line_h
        if needed_y > content["y_td_end"] or self.current_page is None:
            self.new_page()
        
        # Spacing voor entry
        self.cursor_y += spacing
        
        # Render: nummer | titel | pagina
        num_x = cols["number"]["x"]
        title_x = cols["title"]["x"] + indent
        page_x = cols["page_number"]["x"]
        
        if entry["number"]:
            self._text(num_x, self.cursor_y, entry["number"], size, color)
        self._text(title_x, self.cursor_y, entry["title"], size, color)
        self._text(page_x, self.cursor_y, str(entry["page"]), size, color)
        
        self.cursor_y += line_h
    
    def finalize(self):
        """Voeg paginanummers toe en merge alles."""
        pn = self.tpl["page_number"]
        for i, (doc, page) in enumerate(self.pages):
            num = self.page_num + i
            self._finalize_page(page, str(num), pn)
        
    def _finalize_page(self, page, num_str, pn_cfg):
        page.insert_text(
            (pn_cfg["x"], pn_cfg["y_td"] + pn_cfg["size"] * 0.8), num_str,
            fontname="GothamBook", fontsize=pn_cfg["size"], color=PN_COLOR
        )
    
    def save(self, output_path):
        """Sla alle pagina's op als één PDF."""
        self.finalize()
        if len(self.pages) == 1:
            self.pages[0][0].save(str(output_path))
        else:
            # Merge alle pagina's
            result = fitz.open()
            for doc, page in self.pages:
                result.insert_pdf(doc)
            result.save(str(output_path))
            result.close()
        
        for doc, page in self.pages:
            doc.close()

# === Render ===
renderer = TOCRenderer(tpl)
renderer.new_page()

for entry in toc_entries:
    renderer.add_entry(entry)

renderer.save(OUTPUT_PDF)
print(f"DONE: {OUTPUT_PDF}")
print(f"Pagina's: {len(renderer.pages)}")
