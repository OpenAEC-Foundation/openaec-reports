"""Mockup: render pagina 7 content dynamisch op standaard.pdf met content_styles.yaml."""
import fitz
import yaml
from pathlib import Path

OUT_DIR = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\test_output")
STANDAARD_PDF = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\paginas\standaard.pdf")
FONT_DIR = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src\bm_reports\assets\fonts")
OUTPUT_PDF = OUT_DIR / "content_mockup_p7_v2.pdf"

# Laad styles
with open(OUT_DIR / "content_styles.yaml", "r", encoding="utf-8") as f:
    styles = yaml.safe_load(f)

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))

class ContentRenderer:
    """Rendert dynamische content blocks op een PDF pagina."""
    
    def __init__(self, template_pdf, font_dir, styles):
        self.template_pdf = template_pdf
        self.font_dir = font_dir
        self.styles = styles
        self.blocks = styles["blocks"]
        self.doc = None
        self.page = None
        self.y = 0  # huidige y positie (top-down)
        self.page_count = 0
        self.y_max = 780.0  # onderkant content area
        
    def start(self):
        self.doc = fitz.open()
        # Laad echte font voor breedte-meting
        self.gotham_book = fitz.Font(fontfile=str(self.font_dir / "Gotham-Book.ttf"))
        self.gotham_bold = fitz.Font(fontfile=str(self.font_dir / "Gotham-Bold.ttf"))
        self._new_page()
        
    def _new_page(self):
        """Voeg nieuwe pagina toe met standaard achtergrond."""
        src = fitz.open(str(self.template_pdf))
        self.doc.insert_pdf(src)
        src.close()
        self.page_count += 1
        self.page = self.doc[-1]
        self.page.insert_font(fontname="GothamBook", fontfile=str(self.font_dir / "Gotham-Book.ttf"))
        self.page.insert_font(fontname="GothamBold", fontfile=str(self.font_dir / "Gotham-Bold.ttf"))
        self.y = 74.9  # bovenkant content area
        
    def _check_overflow(self, needed_height):
        """Check of er ruimte is, zo niet: nieuwe pagina."""
        if self.y + needed_height > self.y_max:
            self._add_page_number()
            self._new_page()
            return True
        return False
        
    def _add_page_number(self):
        pn = self.styles["page_number"]
        self.page.insert_text(
            (pn["x"], pn["y_td"] + pn["size"] * 0.8),
            str(self.page_count),
            fontname="GothamBook", fontsize=pn["size"],
            color=hex_to_rgb(pn["color"])
        )
        
    def _text(self, x, y_td, text, fontname, size, color_hex):
        """Tekst plaatsen op positie."""
        baseline = y_td + size * 0.8
        self.page.insert_text(
            (x, baseline), text,
            fontname=fontname, fontsize=size,
            color=hex_to_rgb(color_hex)
        )
    
    def heading_1(self, number, title):
        """H1: Hoofdstuk titel."""
        s = self.blocks["heading_1"]
        self._check_overflow(s["number"]["size"] + s["spacing_after"])
        
        self._text(s["number"]["x"], self.y, number,
                    s["number"]["font"], s["number"]["size"], s["number"]["color"])
        self._text(s["title"]["x"], self.y, title,
                    s["title"]["font"], s["title"]["size"], s["title"]["color"])
        self.y += s["number"]["size"] + s["spacing_after"]
    
    def heading_2(self, number, title):
        """H2: Paragraaf titel."""
        s = self.blocks["heading_2"]
        self.y += s["spacing_before"]
        self._check_overflow(s["title"]["size"] + s["spacing_after"])
        
        self._text(s["number"]["x"], self.y, number,
                    s["number"]["font"], s["number"]["size"], s["number"]["color"])
        # H2 title zit iets hoger dan nummer (13pt vs 10pt)
        y_title = self.y - (s["title"]["size"] - s["number"]["size"]) * 0.3
        self._text(s["title"]["x"], y_title, title,
                    s["title"]["font"], s["title"]["size"], s["title"]["color"])
        self.y += s["title"]["size"] + s["spacing_after"]
    
    def _wrap_text(self, text, fontsize, max_width):
        """Word-wrap met echte Gotham font breedte-meting."""
        words = text.split()
        lines = []
        current = ""
        for w in words:
            test = f"{current} {w}".strip()
            tw = self.gotham_book.text_length(test, fontsize=fontsize)
            if tw > max_width and current:
                lines.append(current)
                current = w
            else:
                current = test
        if current:
            lines.append(current)
        return lines
    
    def paragraph(self, text):
        """Body text met automatische regelafbraak."""
        s = self.blocks["paragraph"]
        self.y += s["spacing_before"]
        
        lines = self._wrap_text(text, s["size"], s["max_width"])
        
        needed = len(lines) * s["line_height"]
        self._check_overflow(needed)
        
        for line in lines:
            self._text(s["x"], self.y, line, s["font"], s["size"], s["color"])
            self.y += s["line_height"]
        
        self.y += s["spacing_after"]
    
    def bullet_list(self, items):
        """Bullet list met marker + ingesprongen tekst."""
        sb = self.blocks["bullet_list"]
        
        for item in items:
            lines = self._wrap_text(item, sb["text"]["size"], sb["text"]["max_width"])
            
            needed = len(lines) * sb["text"]["line_height"] + sb["spacing_between"]
            self._check_overflow(needed)
            
            # Bullet marker (•)
            self.page.insert_text(
                (sb["marker"]["x"], self.y + sb["marker"]["size"] * 0.8),
                "\u2022",  # bullet character
                fontname="GothamBook", fontsize=sb["marker"]["size"],
                color=hex_to_rgb(sb["marker"]["color"])
            )
            
            # Tekst regels
            for line in lines:
                self._text(sb["text"]["x"], self.y, line,
                           sb["text"]["font"], sb["text"]["size"], sb["text"]["color"])
                self.y += sb["text"]["line_height"]
            
            self.y += sb["spacing_between"]
    
    def finish(self, output_path):
        self._add_page_number()
        self.doc.save(str(output_path))
        self.doc.close()
        print(f"DONE: {output_path}")
        print(f"Pagina's: {self.page_count}")


# ============================================================
# Render pagina 7 van BBL rapport als test
# ============================================================
r = ContentRenderer(STANDAARD_PDF, FONT_DIR, styles)
r.start()

r.heading_1("3", "Samenvatting")

r.paragraph("De belangrijkste constateringen zijn:")

r.heading_2("3.1", "Bruikbaarheid:")

r.bullet_list([
    "Woning type B is met het huidige ontwerp niet te realiseren in de oksel. Op andere plekken in het gebouw kan dit type wel worden gemaakt.",
    "De woningtype A en B zijn herontworpen naar een studio zodat elke ruimte voldoet aan de minimale eis van 0,5 m² daglicht. Elke verblijfsruimte moet ook doorspuibaar zijn er is dus minimaal 1 te openen deel aanwezig per ruimte.",
    "Verblijfsgebieden voor gebruiksfunctie woonfunctie voldoen voor woning type B niet aan de eis 55% van gebruiks-oppervlakte conform NEN 2580.",
    "het hoofdtrappenhuis is te smal 1200mm is de minimale breedte voor het hoofdtrappenhuis",
    "Ruimten binnen de woning waardoor gevlucht wordt dienen voorzien te worden van een niet-ioniserende rookmelder.",
    "Toiletruimten en badkamers worden voorzien van vloertegelwerk en wandtegelwerk.",
    "Alle woningen dienen een berging te hebben van minimaal 5m2.",
    "Alle woningen dienen te beschikken over buitenruimten, voor woningen kleiner dan 50m2 mag dit een gemeenschappelijke ruimte zijn.",
])

r.heading_2("3.2", "Ventilatie:")

r.bullet_list([
    "Bij alle woningen wordt de ventilatie gerealiseerd met centraal gestuurd mechanische toe- en afvoer (gebalanceerde ventilatie). In de woningen wordt een WTW unit opgenomen en op het dak zal een LBK unit moeten komen.",
])

r.heading_2("3.3", "Brandveiligheid en vluchten:")

r.bullet_list([
    "In het huidige ontwerp zijn de corridors te lang, de maximale vlucht lengte oningedeeld is 20m. In dit rapport is een voorstel gedaan voor een mogelijke indeling.",
])

r.heading_2("3.4", "Parkeren")

r.paragraph("Op dit moment zijn er 44 parkeerplekken in het VO ingetekend. Echter deze plekken voldoen niet aan de NEN 2443. Dit is geen harde eis, maar bij verhuur of exploitatie kan dit wel een eis worden. Gezien de huidige kolommen structuur en breedte is er geen efficiënte garage in te maken die voldoet aan de NEN2443. Er zijn meerdere opstelling probeert er kunnen maximaal zo'n 25 plekken in die voldoen aan de norm.")

r.finish(OUTPUT_PDF)
