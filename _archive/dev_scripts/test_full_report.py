"""
=============================================================
VOLLEDIG RAPPORT GENERATOR - Proof of Concept
=============================================================
Genereert een compleet 3BM rapport met YAML-gestuurde templates:
  1. Voorblad (cover) - ReportLab 3-lagen
  2. Colofon - PyMuPDF op colofon.pdf
  3. Inhoudsopgave (TOC) - Dynamisch blok
  4. Content pagina's - H1, H2, paragrafen, bullets
  5. Bijlage divider
  6. Bijlage content
  7. Achterblad - statisch
=============================================================
"""
import fitz
import yaml
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

# === PADEN ===
BASE = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator")
OUT_DIR = BASE / "test_output"
HUISSTIJL = BASE / "huisstijl" / "paginas"
FONT_DIR = BASE / "src" / "bm_reports" / "assets" / "fonts"
STATIONERY_PNG = HUISSTIJL / "2707_BBLrapportage_v01_1.png"
COLOFON_PDF = HUISSTIJL / "colofon.pdf"
STANDAARD_PDF = HUISSTIJL / "standaard.pdf"
BIJLAGEN_PDF = HUISSTIJL / "bijlagen.pdf"
ACHTERBLAD_PDF = HUISSTIJL / "achterblad.pdf"

OUTPUT_PDF = OUT_DIR / "volledig_rapport_v3.pdf"

# === STYLES ===
with open(OUT_DIR / "content_styles.yaml", "r", encoding="utf-8") as f:
    STYLES = yaml.safe_load(f)

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))

COLOR_PURPLE = (0.251, 0.071, 0.275)
COLOR_TEAL = (0.220, 0.741, 0.671)

# === FAKE PROJECT DATA ===
PROJECT = {
    "rapport_type": "Constructief adviesrapport",
    "project_naam": "Nieuwbouw Wooncomplex De Horizon - Scheveningen",
    "project_nummer": "2801",
    "opdrachtgever_naam": "Van der Berg Ontwikkeling B.V.",
    "opdrachtgever_contact": "Dhr. P. van der Berg",
    "opdrachtgever_adres": "Koninginnegracht 12,\n2514 AA Den Haag",
    "adviseur_bedrijf": "3BM Coöperatie",
    "adviseur_naam": "Ir. S. de Vries",
    "normen": "Eurocode, NEN-EN 1990, NEN-EN 1992",
    "documentgegevens": "Constructief advies, pg 1-14",
    "datum": "20-02-2026",
    "fase": "Definitief Ontwerp",
    "status": "Concept",
    "kenmerk": "2801-CA-01",
    "cover_photo": None,  # placeholder
}

# Chaptered content
CHAPTERS = [
    {
        "number": "1", "title": "Inleiding",
        "blocks": [
            ("paragraph", "In opdracht van Van der Berg Ontwikkeling B.V. is door 3BM Coöperatie een constructief adviesrapport opgesteld voor het project Nieuwbouw Wooncomplex De Horizon te Scheveningen. Het betreft een woongebouw met 48 appartementen, een ondergrondse parkeergarage en commerciële ruimten op de begane grond."),
            ("paragraph", "Het doel van dit rapport is het vastleggen van de constructieve uitgangspunten en het geven van een advies over de draagconstructie. De volgende aspecten worden behandeld:"),
            ("bullets", [
                "Constructieve opzet en materialisatie van de hoofddraagconstructie",
                "Stabiliteitsvoorzieningen en windbelasting conform Eurocode",
                "Funderingsadvies op basis van beschikbare sonderingsgegevens",
                "Toelichting op de gekozen vloerconstructie en overspanningen",
                "Aandachtspunten voor de verdere uitwerking in de volgende ontwerpfase",
            ]),
        ],
    },
    {
        "number": "2", "title": "Uitgangspunten",
        "blocks": [
            ("paragraph", "Het constructief ontwerp is gebaseerd op de volgende uitgangspunten en randvoorwaarden. De belastingen zijn bepaald conform NEN-EN 1991 en de constructieve toetsing is uitgevoerd conform NEN-EN 1992 (beton) en NEN-EN 1993 (staal)."),
            ("h2", "2.1", "Gebouwgeometrie"),
            ("paragraph", "Het gebouw bestaat uit een kelder, begane grond en 6 verdiepingen. De totale bouwhoogte bedraagt circa 24 meter boven maaiveld. De ondergrondse parkeergarage heeft een vrije hoogte van 2.600 mm en biedt ruimte aan 36 parkeerplaatsen conform NEN 2443."),
            ("h2", "2.2", "Belastingen"),
            ("bullets", [
                "Permanente belasting: eigengewicht constructie + afbouw (1,5 kN/m²)",
                "Veranderlijke belasting woonfunctie: 1,75 kN/m² conform tabel NB.1 NEN-EN 1991-1-1",
                "Veranderlijke belasting parkeergarage: 2,5 kN/m² (categorie F)",
                "Windbelasting: conform NEN-EN 1991-1-4, windgebied II, kustlocatie",
                "Sneeuwbelasting: 0,56 kN/m² conform NEN-EN 1991-1-3",
            ]),
            ("h2", "2.3", "Materialen"),
            ("paragraph", "De hoofddraagconstructie wordt uitgevoerd in gewapend beton sterkteklasse C30/37 met betonstaal B500B. De staalconstructie voor de commerciële ruimten op de begane grond wordt uitgevoerd in staal S355. Alle materialen voldoen aan de eisen gesteld in de relevante Eurocodes."),
        ],
    },
    {
        "number": "3", "title": "Constructief ontwerp",
        "blocks": [
            ("paragraph", "Het constructief concept is gebaseerd op een combinatie van dragende wanden en kolommen. De stabiliteit wordt verzorgd door betonnen schijfwanden in beide richtingen. Hieronder worden de belangrijkste onderdelen van de constructie toegelicht."),
            ("h2", "3.1", "Hoofddraagconstructie"),
            ("paragraph", "De verticale krachtsafdracht vindt plaats via betonnen draagwanden met een dikte van 200 mm en kolommen 400x400 mm. De vloeren zijn uitgevoerd als breedplaatvloeren met een totale dikte van 260 mm. De overspanningen variëren van 5.400 tot 7.200 mm."),
            ("bullets", [
                "Draagwanden: gewapend beton C30/37, dikte 200 mm, wapening volgens berekening",
                "Kolommen begane grond: 400x400 mm, C30/37, belasting tot 2.800 kN per kolom",
                "Breedplaatvloeren: totale dikte 260 mm, maximale overspanning 7.200 mm",
                "Balkons: uitkragende betonvloer 1.500 mm met thermische onderbreking",
            ]),
            ("h2", "3.2", "Stabiliteit"),
            ("paragraph", "De horizontale stabiliteit wordt verzorgd door vier betonnen schijfwanden rondom de trappen- en liftkernen. De windbelasting op de gevel wordt via de stijve vloerschijven naar de stabiliteitskernen geleid. Uit de voorlopige berekening blijkt dat de horizontale verplaatsing op dakn ruimschoots voldoet aan de eis van h/500."),
            ("h2", "3.3", "Fundering"),
            ("paragraph", "Op basis van de beschikbare sondering (S01, uitgevoerd door Fugro d.d. 15-01-2026) wordt een paalfundering geadviseerd. De eerste zandlaag is aangetroffen op NAP -14,0 m. Geadviseerd wordt om te heien met prefab betonpalen 320x320 mm tot een diepte van circa NAP -16,0 m. Het geschatte draagvermogen bedraagt 900 kN per paal."),
        ],
    },
    {
        "number": "4", "title": "Aandachtspunten en aanbevelingen",
        "blocks": [
            ("paragraph", "Op basis van het uitgevoerde constructief advies worden de volgende aandachtspunten en aanbevelingen meegegeven voor de verdere uitwerking:"),
            ("bullets", [
                "De definitieve wapeningsberekening dient te worden uitgevoerd in de volgende fase op basis van het uitgewerkte DO",
                "Voor de parkeergarage wordt aanbevolen een trillingsanalyse uit te voeren i.v.m. de bovengelegen woonfunctie",
                "De thermische onderbrekingen bij de balkons dienen vroegtijdig te worden gespecificeerd om de detaillering hierop af te stemmen",
                "Bij de verdere uitwerking van de fundering dient rekening te worden gehouden met negatieve kleef ter plaatse van de slappe bodemlagen",
                "De stabiliteitsberekening dient in de volgende fase te worden geverifieerd met een eindig-elementenmodel",
                "Aanbevolen wordt om in overleg met de architect de mogelijkheid van een staalconstructie voor de begane grondverdieping nader te onderzoeken",
            ]),
        ],
    },
]

BIJLAGEN = [
    {
        "nummer": "Bijlage 1",
        "titel": "Sonderingsgegevens en\nfunderingsadvies",
    },
]


# ================================================================
# STAP 1: COVER PAGE (ReportLab)
# ================================================================
def generate_cover(output_path):
    """Genereer cover pagina met 3-lagen aanpak."""
    print("  [1/7] Cover pagina...")
    w, h = A4
    
    # Register fonts
    for name, filename in [("GothamBold", "Gotham-Bold.ttf"), ("GothamBook", "Gotham-Book.ttf")]:
        try:
            pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / filename)))
        except:
            pass
    
    c = rl_canvas.Canvas(str(output_path), pagesize=A4)
    
    # Laag 1: Placeholder projectfoto (teal gradient)
    c.setFillColor(HexColor("#38BDAB"))
    c.rect(55.6, 161.7, 484.0, 560.8, fill=1, stroke=0)
    # Donkerder bovenlaag voor diepte
    c.setFillColor(Color(0.15, 0.35, 0.35, alpha=0.4))
    c.rect(55.6, 161.7, 484.0, 280, fill=1, stroke=0)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica", 16)
    c.drawCentredString(w / 2, 440, "[ PROJECTFOTO ]")
    c.setFont("Helvetica", 10)
    c.drawCentredString(w / 2, 420, "De Horizon - Scheveningen")
    
    # Laag 2: Stationery PNG overlay (met alpha)
    if STATIONERY_PNG.exists():
        img = ImageReader(str(STATIONERY_PNG))
        c.drawImage(img, 0, 0, width=w, height=h, mask='auto', preserveAspectRatio=False)
    
    # Laag 3: Dynamische tekst
    c.setFont("GothamBold", 28.9)
    c.setFillColor(HexColor("#401246"))
    c.drawString(54.3, 120.5, PROJECT["rapport_type"])
    
    c.setFont("GothamBook", 17.8)
    c.setFillColor(HexColor("#38BDAB"))
    c.drawString(55.0, 78.6, PROJECT["project_naam"])
    
    c.save()
    return output_path

# ================================================================
# STAP 2: COLOFON (PyMuPDF)
# ================================================================
def generate_colofon(output_path):
    """Genereer colofon pagina."""
    print("  [2/7] Colofon...")
    doc = fitz.open(str(COLOFON_PDF))
    page = doc[0]
    page.insert_font(fontname="GothamBold", fontfile=str(FONT_DIR / "Gotham-Bold.ttf"))
    page.insert_font(fontname="GothamBook", fontfile=str(FONT_DIR / "Gotham-Book.ttf"))
    
    # Titel + subtitel
    page.insert_text((70.9, 57.3 + 22 * 0.8), PROJECT["rapport_type"],
                      fontname="GothamBold", fontsize=22, color=COLOR_PURPLE)
    page.insert_text((70.9, 86.8 + 14 * 0.8), PROJECT["project_naam"],
                      fontname="GothamBook", fontsize=14, color=COLOR_TEAL)
    
    # Tabelwaarden
    values = [
        (f"{PROJECT['project_nummer']} - {PROJECT['project_naam']}", 321.1),
        (PROJECT["opdrachtgever_contact"], 369.1),
        (PROJECT["opdrachtgever_naam"], 381.8),
        ("Koninginnegracht 12,", 394.6),
        ("2514 AA Den Haag", 407.2),
        (PROJECT["adviseur_bedrijf"], 489.1),
        (PROJECT["adviseur_naam"], 501.1),
        (PROJECT["normen"], 525.1),
        (PROJECT["documentgegevens"], 549.1),
        (PROJECT["datum"], 573.1),
        (PROJECT["fase"], 597.1),
        (PROJECT["status"], 621.1),
        (PROJECT["kenmerk"], 645.1),
    ]
    for text, y_td in values:
        page.insert_text((229.1, y_td + 10 * 0.8), text,
                          fontname="GothamBook", fontsize=10, color=COLOR_PURPLE)
    
    # Paginanummer
    page.insert_text((534.0, 796.3 + 8 * 0.8), "2",
                      fontname="GothamBold", fontsize=8, color=COLOR_TEAL)
    
    doc.save(str(output_path))
    doc.close()
    return output_path

# ================================================================
# STAP 3-6: CONTENT RENDERER (PyMuPDF)
# ================================================================
class ReportRenderer:
    """Rendert dynamische content blocks op standaard.pdf pagina's."""
    
    def __init__(self):
        self.doc = fitz.open()
        self.gotham_book = fitz.Font(fontfile=str(FONT_DIR / "Gotham-Book.ttf"))
        self.gotham_bold = fitz.Font(fontfile=str(FONT_DIR / "Gotham-Bold.ttf"))
        self.blocks = STYLES["blocks"]
        self.page = None
        self.y = 0
        self.page_count = 0
        self.y_max = 780.0
        self.total_page_nr = 3  # begint na cover (1) + colofon (2)
    
    def _new_page(self, template_pdf=None):
        if template_pdf is None:
            template_pdf = STANDAARD_PDF
        src = fitz.open(str(template_pdf))
        self.doc.insert_pdf(src)
        src.close()
        self.page_count += 1
        self.page = self.doc[-1]
        self.page.insert_font(fontname="GothamBook", fontfile=str(FONT_DIR / "Gotham-Book.ttf"))
        self.page.insert_font(fontname="GothamBold", fontfile=str(FONT_DIR / "Gotham-Bold.ttf"))
        self.y = 74.9
    
    def _check_overflow(self, needed):
        if self.y + needed > self.y_max:
            self._add_page_number()
            self._new_page()
            return True
        return False
    
    def _add_page_number(self):
        pn = STYLES["page_number"]
        self.page.insert_text(
            (pn["x"], pn["y_td"] + pn["size"] * 0.8),
            str(self.total_page_nr),
            fontname="GothamBook", fontsize=pn["size"],
            color=hex_to_rgb(pn["color"])
        )
        self.total_page_nr += 1
    
    def _text(self, x, y_td, text, fontname, size, color_hex):
        self.page.insert_text(
            (x, y_td + size * 0.8), text,
            fontname=fontname, fontsize=size,
            color=hex_to_rgb(color_hex)
        )
    
    def _wrap(self, text, fontsize, max_width):
        words = text.split()
        lines, current = [], ""
        for w in words:
            test = f"{current} {w}".strip()
            if self.gotham_book.text_length(test, fontsize=fontsize) > max_width and current:
                lines.append(current)
                current = w
            else:
                current = test
        if current:
            lines.append(current)
        return lines
    
    # --- TOC ---
    def render_toc(self, entries):
        """Render inhoudsopgave. entries = [(level, number, title, page), ...]"""
        print("  [3/7] Inhoudsopgave...")
        self._new_page()
        # Titel
        self._text(90.0, 74.9, "Inhoud", "GothamBook", 18.0, "#401246")
        self.y = 127.2
        
        for level, number, title, pg in entries:
            if level == 1:
                self.y += 17.0
                self._check_overflow(20)
                self._text(90.0, self.y, number, "GothamBook", 12.0, "#56B49B")
                self._text(160.9, self.y, title, "GothamBook", 12.0, "#56B49B")
                self._text(515.4, self.y, str(pg), "GothamBook", 12.0, "#56B49B")
                self.y += 20.0
            else:
                self._check_overflow(17.3)
                self._text(90.0, self.y, number, "GothamBook", 9.5, "#401246")
                self._text(160.9, self.y, title, "GothamBook", 9.5, "#401246")
                self._text(515.4, self.y, str(pg), "GothamBook", 9.5, "#401246")
                self.y += 17.3
        
        self._add_page_number()
    
    # --- Content blocks ---
    def heading_1(self, number, title):
        s = self.blocks["heading_1"]
        self._check_overflow(s["number"]["size"] + s["spacing_after"])
        self._text(s["number"]["x"], self.y, number, s["number"]["font"], s["number"]["size"], s["number"]["color"])
        self._text(s["title"]["x"], self.y, title, s["title"]["font"], s["title"]["size"], s["title"]["color"])
        self.y += s["number"]["size"] + s["spacing_after"]
    
    def heading_2(self, number, title):
        s = self.blocks["heading_2"]
        self.y += s["spacing_before"]
        self._check_overflow(s["title"]["size"] + s["spacing_after"])
        self._text(s["number"]["x"], self.y, number, s["number"]["font"], s["number"]["size"], s["number"]["color"])
        y_title = self.y - (s["title"]["size"] - s["number"]["size"]) * 0.3
        self._text(s["title"]["x"], y_title, title, s["title"]["font"], s["title"]["size"], s["title"]["color"])
        self.y += s["title"]["size"] + s["spacing_after"]
    
    def paragraph(self, text):
        s = self.blocks["paragraph"]
        self.y += s["spacing_before"]
        lines = self._wrap(text, s["size"], s["max_width"])
        self._check_overflow(len(lines) * s["line_height"])
        for line in lines:
            self._text(s["x"], self.y, line, s["font"], s["size"], s["color"])
            self.y += s["line_height"]
        self.y += s["spacing_after"]
    
    def bullet_list(self, items):
        sb = self.blocks["bullet_list"]
        for item in items:
            lines = self._wrap(item, sb["text"]["size"], sb["text"]["max_width"])
            needed = len(lines) * sb["text"]["line_height"] + sb["spacing_between"]
            self._check_overflow(needed)
            self.page.insert_text(
                (sb["marker"]["x"], self.y + sb["marker"]["size"] * 0.8),
                "\u2022", fontname="GothamBook", fontsize=sb["marker"]["size"],
                color=hex_to_rgb(sb["marker"]["color"])
            )
            for line in lines:
                self._text(sb["text"]["x"], self.y, line, sb["text"]["font"], sb["text"]["size"], sb["text"]["color"])
                self.y += sb["text"]["line_height"]
            self.y += sb["spacing_between"]
    
    # --- Chapters ---
    def render_chapters(self, chapters):
        """Render alle hoofdstukken."""
        print("  [4/7] Content pagina's...")
        for ch in chapters:
            self._new_page()
            self.heading_1(ch["number"], ch["title"])
            
            for block in ch["blocks"]:
                if block[0] == "paragraph":
                    self.paragraph(block[1])
                elif block[0] == "bullets":
                    self.bullet_list(block[1])
                elif block[0] == "h2":
                    self.heading_2(block[1], block[2])
            
            self._add_page_number()
    
    # --- Bijlage divider ---
    def render_bijlage_divider(self, nummer, titel):
        """Render bijlage scheidingsblad met auto-fit titel."""
        print("  [5/7] Bijlage divider...")
        self._new_page(BIJLAGEN_PDF)
        # Nummer: altijd 41.4pt (kort genoeg)
        self._text(103.0, 193.9, nummer, "GothamBold", 41.4, "#401246")
        
        # Titel: vast 20pt
        max_width = 595.3 - 136.1 - 20
        lines = titel.split("\n")
        fontsize = 20.0
        line_height = fontsize * 1.6
        for i, line in enumerate(lines):
            y_td = 262.2 + i * line_height
            self._text(136.1, y_td, line, "GothamBook", fontsize, "#FFFFFF")
        # Geen paginanummer op divider
        self.total_page_nr += 1
    
    # --- Bijlage content ---
    def render_bijlage_content(self):
        """Render dummy bijlage content."""
        print("  [6/7] Bijlage content...")
        self._new_page()
        self.heading_1("B1", "Sonderingsgegevens")
        self.paragraph("Onderstaand zijn de sonderingsresultaten weergegeven van sondering S01, uitgevoerd door Fugro Geoservices B.V. op 15 januari 2026. De sondering is uitgevoerd conform NEN-EN-ISO 22476-1.")
        self.paragraph("Uit de sondering blijkt dat de eerste draagkrachtige zandlaag wordt aangetroffen op een diepte van NAP -14,0 m. De conusweerstand in deze laag bedraagt gemiddeld 18 MPa over een traject van 3 meter. Op basis van de beschikbare gegevens wordt een funderingsdiepte van NAP -16,0 m geadviseerd.")
        self.bullet_list([
            "Maaiveld: NAP +1,2 m",
            "Eerste zandlaag: NAP -14,0 m (qc = 15-22 MPa)",
            "Geadviseerde paallengte: circa 17 meter onder maaiveld",
            "Geschat draagvermogen: 900 kN per paal (prefab beton 320x320 mm)",
            "Negatieve kleef: rekening houden met 80 kN per paal",
        ])
        self.paragraph("Voor de definitieve funderingsberekening dient een aanvullende sondering te worden uitgevoerd ter plaatse van de zwaarst belaste kolommen. Tevens wordt aanbevolen een grondonderzoek uit te voeren voor het bepalen van de grondwaterstand en doorlatendheid.")
        self._add_page_number()
    
    # --- Achterblad ---
    def render_achterblad(self):
        """Voeg statisch achterblad toe."""
        print("  [7/7] Achterblad...")
        src = fitz.open(str(ACHTERBLAD_PDF))
        self.doc.insert_pdf(src)
        src.close()
    
    def save(self, output_path):
        self.doc.save(str(output_path))
        self.doc.close()


# ================================================================
# MAIN: Bouw het rapport
# ================================================================
print("=" * 60)
print("3BM RAPPORT GENERATOR - Proof of Concept")
print("=" * 60)
print(f"Project: {PROJECT['project_naam']}")
print(f"Output:  {OUTPUT_PDF}")
print()

# Stap 1: Cover (ReportLab → tijdelijk bestand)
cover_tmp = OUT_DIR / "_tmp_cover.pdf"
generate_cover(cover_tmp)

# Stap 2: Colofon (PyMuPDF → tijdelijk bestand)
colofon_tmp = OUT_DIR / "_tmp_colofon.pdf"
generate_colofon(colofon_tmp)

# Stap 3-7: Rest van het rapport (PyMuPDF)
renderer = ReportRenderer()

# TOC entries (page nummers zijn schattingen)
toc_entries = [
    (1, "1", "Inleiding", 4),
    (1, "2", "Uitgangspunten", 5),
    (2, "2.1", "Gebouwgeometrie", 5),
    (2, "2.2", "Belastingen", 5),
    (2, "2.3", "Materialen", 6),
    (1, "3", "Constructief ontwerp", 7),
    (2, "3.1", "Hoofddraagconstructie", 7),
    (2, "3.2", "Stabiliteit", 8),
    (2, "3.3", "Fundering", 8),
    (1, "4", "Aandachtspunten en aanbevelingen", 9),
]
renderer.render_toc(toc_entries)
renderer.render_chapters(CHAPTERS)

# Bijlagen
for bijl in BIJLAGEN:
    renderer.render_bijlage_divider(bijl["nummer"], bijl["titel"])
renderer.render_bijlage_content()

# Achterblad
renderer.render_achterblad()

# Sla tussenresultaat op
content_tmp = OUT_DIR / "_tmp_content.pdf"
renderer.save(str(content_tmp))

# === MERGE: Cover + Colofon + Content → Eindresultaat ===
print()
print("  Merging PDF...")
final = fitz.open()

# 1. Cover
cover_doc = fitz.open(str(cover_tmp))
final.insert_pdf(cover_doc)
cover_doc.close()

# 2. Colofon
colofon_doc = fitz.open(str(colofon_tmp))
final.insert_pdf(colofon_doc)
colofon_doc.close()

# 3. Content (TOC + chapters + bijlagen + achterblad)
content_doc = fitz.open(str(content_tmp))
final.insert_pdf(content_doc)
content_doc.close()

final.save(str(OUTPUT_PDF))
final.close()

# Cleanup
cover_tmp.unlink(missing_ok=True)
colofon_tmp.unlink(missing_ok=True)
content_tmp.unlink(missing_ok=True)

# Resultaat
result_doc = fitz.open(str(OUTPUT_PDF))
print()
print("=" * 60)
print(f"RAPPORT GEREED: {OUTPUT_PDF}")
print(f"Totaal pagina's: {result_doc.page_count}")
print("=" * 60)
result_doc.close()
