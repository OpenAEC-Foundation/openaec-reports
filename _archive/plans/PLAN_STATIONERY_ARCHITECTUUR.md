# Plan: Achtergrond-template architectuur voor pixel-perfecte PDF's

## Probleemstelling

De huidige aanpak tekent alle visuele elementen (vlakken, driehoeken, polygonen, badges) 
programmatisch via ReportLab canvas operaties. Dit leidt tot:

1. **Geometrische afwijkingen** — Vereenvoudigde polygonen (bijv. backcover "driehoek" is eigenlijk 
   een complex polygon met schuine snijlijnen)
2. **Kleur-/font mismatch** — Hardcoded waarden die subtiel afwijken van het referentiedocument
3. **Onmogelijk te matchen details** — Schaduweffecten, antialiasing, subtiele gradiënten die 
   alleen in de originele PDF zitten
4. **Maintenance nachtmerrie** — Elk nieuw bureau vereist weken programmeerwerk om geometrie 
   na te bouwen

## Kernidee: Stationery Layer

Elk paginatype krijgt optioneel een **"stationery"** — een achtergrond-template (PDF of PNG) 
met alle STATISCHE visuele elementen. Dynamische tekst en afbeeldingen worden er overheen getekend.

```
┌─────────────────────────────────────────┐
│  Laag 3: Dynamische tekst              │  ← ReportLab (titels, content, paginanr)
│  Laag 2: Dynamische afbeeldingen        │  ← ReportLab (projectfoto op cover)
│  Laag 1: Stationery achtergrond         │  ← PDF/PNG template (alle statische geometrie)
└─────────────────────────────────────────┘
```

## Analyse per paginatype

### Cover (pagina 1)
```
STATISCH:                           DYNAMISCH:
├─ Paars vlak (bovenste 74%)        ├─ Projectfoto (in clip-polygon)
├─ Clip-path contour                ├─ Rapporttitel (GothamBold 28.9pt)
├─ Wit logo linksboven              └─ Ondertitel (GothamBook 17.8pt)
├─ "Ontdek ons 3bm.co.nl"
├─ 3 badges (goud/turq/koraal)
└─ Witte vlakken / geometrie
```

**Probleem:** De badges overlappen met het foto-gebied. De foto moet ACHTER de badges 
maar VOOR het paarse vlak. Dit vereist een specifieke laagvolgorde:

1. Stationery = paars vlak (zonder badges, logo, tekst)
2. Projectfoto (clip-path)  
3. Overlay = badges + logo + "Ontdek ons" (als tweede stationery-laag, of programmatisch)
4. Titel + ondertitel

**Aanpak:** Twee opties:
- **A) Twee-laags stationery:** Eén achtergrond-PDF (paars vlak) + één overlay-PDF (badges/logo)
- **B) Hybride:** Stationery voor paurs vlak, programmatisch voor badges/logo/foto (zoals nu, maar met correcte kleuren/fonts)

**Aanbeveling: Optie B.** De cover-geometrie (paurs vlak + clip-path) is relatief simpel en 
werkt al in de huidige code. De badges zijn rounded rectangles — triviaal in code. 
Het probleem is alleen fonts/kleuren, niet de geometrie.

### Colofon (pagina 2)
```
STATISCH:                           DYNAMISCH:
├─ Turquoise footer blok            ├─ Rapport type titel
├─ 3BM logo in footer               ├─ Subtitel
└─ (verder leeg)                    ├─ Alle label-waarde paren
                                    ├─ Scheidingslijnen
                                    └─ Paginanummer
```

**Aanpak:** Eenvoudige geometrie (1 rechthoek + 1 logo). Programmatisch is prima. 
Fix alleen fonts/kleuren.

### Inhoudsopgave (pagina 3)
```
STATISCH: niets                     DYNAMISCH: alles
```

**Aanpak:** Puur programmatisch. Fix fonts/kleuren.

### Content pagina's (pagina 4-20)
```
STATISCH: niets                     DYNAMISCH: alles + paginanummer
```

**Aanpak:** Puur programmatisch. Fix fonts/kleuren + content marges.

### Bijlage-scheidingspagina (pagina 21)
```
STATISCH:                           DYNAMISCH:
├─ Turquoise achtergrond            ├─ "Bijlage N" (nummer)
├─ Paars blok linksonder            └─ Bijlagetitel (1-2 regels)
└─ "Projecten die inspireren"
```

**Aanpak:** Simpele geometrie (2 rechthoeken + 1 tekstregel). Programmatisch is prima.
Maar stationery-optie is ook makkelijk (1 pagina extraheren, tekst strippen).

### Backcover (pagina 36) ⚡ HIER GAAT HET MIS
```
STATISCH:                           DYNAMISCH:
├─ Turquoise achtergrond            └─ NIETS
├─ Complex wit polygon met          
│   schuine snijlijnen              
├─ Paars "driehoekig" vlak         
│   (eigenlijk trapezium)           
├─ 3BM logo (groot, midden)        
├─ Bedrijfsnaam + adres            
└─ "Ontdek ons 3bm.co.nl"         
```

**Dit is de pagina waar het écht misgaat.** Het witte vlak is geen simpel polygon — 
het heeft meerdere schuine snijlijnen die exact moeten matchen met het referentiedocument. 
De huidige code gebruikt een vereenvoudigd polygon dat er "roughly" uitziet maar niet klopt.

**Aanpak: 100% stationery.** Extraheer pagina 36 uit de referentie-PDF als achtergrond. 
Geen dynamische content nodig → gewoon de hele pagina gebruiken.

---

## Uitvoeringsplan

### Fase 1: Font/kleur fixes (Quick Win — 1 sessie)

Alle bugs die géén architectuurwijziging vereisen:

| Fix | Bestand | Impact |
|-----|---------|--------|
| Brand YAML: fonts → Gotham | `brands/3bm_cooperatie.yaml` | Alle pagina's |
| Colors dataclass defaults | `core/styles.py` | Alle componenten |
| Hardcoded kleuren in special_pages | `core/special_pages.py` | Cover, colofon, backcover |
| FontConfig defaults (9.0→9.5, 16→18) | `core/styles.py` | Content body + headings |
| H1 fontName: Bold→Book | `core/styles.py` | Alle H1 headings |
| H2 textColor: primary→#56B49B | `core/styles.py` | Alle H2 headings |
| Brand-aware stylesheet in engine | `core/engine.py` | Hele pipeline |

**Na deze fase:** Content pagina's, colofon, TOC zien er al veel beter uit.

### Fase 2: Stationery systeem (architectuur — 1 sessie)

#### 2a. Brand YAML uitbreiding

Voeg `stationery` sectie toe aan `3bm_cooperatie.yaml`:

```yaml
stationery:
  # Per paginatype: optioneel een achtergrond-template
  backcover:
    type: "pdf"                           # "pdf" of "png"
    source: "graphics/3bm-backcover.pdf"  # relatief t.o.v. assets/
    # Geen text_zones nodig — 100% statisch
  
  # Optioneel, voor toekomstige pagina's:
  # appendix_divider:
  #   type: "pdf"
  #   source: "graphics/3bm-appendix-divider.pdf"
  #   text_zones:
  #     - {role: "number", x: 103, y: 193.9, w: 300, h: 50}
  #     - {role: "title", x: 136.1, y: 262.2, w: 400, h: 150}
```

#### 2b. BrandConfig uitbreiden

```python
@dataclass
class StationeryConfig:
    """Achtergrond-template configuratie per paginatype."""
    type: str = "pdf"        # "pdf" of "png"
    source: str = ""         # Pad relatief t.o.v. assets/
    text_zones: list[dict] = field(default_factory=list)  # Optioneel: dynamische zones

@dataclass
class BrandConfig:
    # ... bestaande velden ...
    stationery: dict[str, StationeryConfig] = field(default_factory=dict)
```

#### 2c. StationeryRenderer (nieuw bestand)

`src/openaec_reports/core/stationery.py`:

```python
"""Stationery renderer — Tekent achtergrond-templates op de ReportLab canvas."""

class StationeryRenderer:
    """Tekent stationery (achtergrond PDF/PNG) als eerste laag op een pagina."""
    
    def __init__(self, brand: BrandConfig, assets_dir: Path):
        self._brand = brand
        self._assets_dir = assets_dir
        self._cache: dict[str, Any] = {}  # Cache geladen templates
    
    def has_stationery(self, page_type: str) -> bool:
        """Check of er een stationery template is voor dit paginatype."""
        return page_type in self._brand.stationery
    
    def draw(self, canvas, page_type: str, page_w: float, page_h: float) -> bool:
        """Teken de stationery achtergrond op het canvas.
        
        Returns True als getekend, False als geen stationery beschikbaar.
        """
        config = self._brand.stationery.get(page_type)
        if not config:
            return False
        
        source_path = self._assets_dir / config.source
        if not source_path.exists():
            logger.warning("Stationery niet gevonden: %s", source_path)
            return False
        
        if config.type == "pdf":
            self._draw_pdf_background(canvas, source_path, page_w, page_h)
        elif config.type == "png":
            self._draw_png_background(canvas, source_path, page_w, page_h)
        
        return True
    
    def _draw_pdf_background(self, canvas, pdf_path, page_w, page_h):
        """Render een PDF pagina als achtergrond (vector kwaliteit behouden)."""
        from pdfrw import PdfReader
        from pdfrw.buildxobj import pagexobj
        from reportlab.lib.utils import ImageReader
        
        # Laad PDF pagina als XObject
        if str(pdf_path) not in self._cache:
            reader = PdfReader(str(pdf_path))
            page = reader.pages[0]
            self._cache[str(pdf_path)] = pagexobj(page)
        
        xobj = self._cache[str(pdf_path)]
        
        # Teken op canvas met juiste schaling
        canvas.saveState()
        # Schaal naar pagina afmetingen
        sx = page_w / float(xobj.BBox[2])
        sy = page_h / float(xobj.BBox[3])
        canvas.transform(sx, 0, 0, sy, 0, 0)
        canvas.doForm(makerl(canvas, xobj))
        canvas.restoreState()
    
    def _draw_png_background(self, canvas, png_path, page_w, page_h):
        """Render een PNG als full-page achtergrond."""
        canvas.drawImage(
            str(png_path), 0, 0, page_w, page_h,
            preserveAspectRatio=False, mask='auto',
        )
```

#### 2d. Integratie in special_pages.py

Wijzig `draw_backcover_page()`:

```python
def draw_backcover_page(canvas, doc, config, brand, stationery=None):
    """Teken het achterblad.
    
    Als stationery beschikbaar is: gebruik achtergrond-template.
    Anders: fallback naar programmatische rendering.
    """
    if stationery and stationery.has_stationery("backcover"):
        # Pixel-perfect: gebruik de template
        stationery.draw(canvas, "backcover", 
                        config.effective_width_pt, config.effective_height_pt)
        return
    
    # Fallback: programmatische rendering (huidige code)
    _draw_backcover_programmatic(canvas, doc, config, brand)
```

### Fase 3: Template extractie (1 sessie)

#### 3a. Extract backcover uit referentie-PDF

Script: `tools/extract_stationery.py`

```python
"""Extraheer stationery-pagina's uit een referentie-PDF.

Gebruikt PyMuPDF om specifieke pagina's te extraheren als:
- Losse PDF (vector kwaliteit) 
- Hoge-resolutie PNG (300 DPI, als fallback)
"""

import fitz  # PyMuPDF

def extract_page_as_pdf(source_pdf, page_num, output_pdf):
    """Extraheer één pagina als nieuwe PDF (behoudt vectoren)."""
    src = fitz.open(source_pdf)
    dst = fitz.open()
    dst.insert_pdf(src, from_page=page_num, to_page=page_num)
    dst.save(output_pdf)

def extract_page_as_png(source_pdf, page_num, output_png, dpi=300):
    """Extraheer één pagina als PNG."""
    doc = fitz.open(source_pdf)
    page = doc[page_num]
    mat = fitz.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat)
    pix.save(output_png)

def strip_text_from_page(source_pdf, page_num, output_pdf):
    """Extraheer pagina zonder tekst (alleen grafische elementen).
    
    Handig voor pagina's waar je de geometrie wilt behouden
    maar eigen tekst wilt plaatsen.
    """
    doc = fitz.open(source_pdf)
    page = doc[page_num]
    
    # Verwijder alle tekstblokken
    blocks = page.get_text("dict")["blocks"]
    for block in blocks:
        if block["type"] == 0:  # Text block
            rect = fitz.Rect(block["bbox"])
            # Redact (wis) het tekstgebied
            page.add_redact_annot(rect)
    page.apply_redactions()
    
    # Sla op als nieuwe PDF
    dst = fitz.open()
    dst.insert_pdf(doc, from_page=page_num, to_page=page_num)
    dst.save(output_pdf)
```

#### 3b. Genereer stationery bestanden

```bash
# Backcover: pagina 36 (index 35) — 100% statisch, geen tekst strippen nodig
python tools/extract_stationery.py \
  --source huisstijl/2707_BBLrapportage_v01.pdf \
  --page 35 \
  --output src/openaec_reports/assets/graphics/3bm-backcover.pdf \
  --mode full

# Appendix divider: pagina 21 (index 20) — strip dynamische tekst
python tools/extract_stationery.py \
  --source huisstijl/2707_BBLrapportage_v01.pdf \
  --page 20 \
  --output src/openaec_reports/assets/graphics/3bm-appendix-divider.pdf \
  --mode strip-text

# Optioneel: Cover pagina zonder foto en titels (voor referentie)
python tools/extract_stationery.py \
  --source huisstijl/2707_BBLrapportage_v01.pdf \
  --page 0 \
  --output src/openaec_reports/assets/graphics/3bm-cover-reference.png \
  --mode png --dpi 300
```

### Fase 4: Visuele verificatie

1. Genereer test-PDF met alle paginatypes
2. Vergelijk side-by-side met referentiedocument
3. Fine-tune tekstposities waar nodig
4. Documenteer afwijkingen die acceptabel zijn vs. must-fix

---

## Dependency overzicht

| Package | Doel | Status |
|---------|------|--------|
| `pdfrw` | PDF-als-achtergrond in ReportLab | **Toevoegen** aan dependencies |
| `pymupdf` | PDF pagina extractie (stationery tool) | Al in `[brand-tools]` |
| `reportlab` | PDF generatie + canvas rendering | ✅ Aanwezig |
| `Pillow` | PNG verwerking | ✅ Aanwezig |

Voeg toe aan `pyproject.toml`:
```toml
dependencies = [
    # ... bestaande ...
    "pdfrw>=0.4",
]
```

---

## Samenvatting: wat verandert er per paginatype

| Pagina | Huidige aanpak | Nieuwe aanpak |
|--------|---------------|---------------|
| **Cover** | Programmatisch (vlak+clip+badges) | **Zelfde**, maar fix fonts/kleuren |
| **Colofon** | Programmatisch (tekst+lijnen+footer) | **Zelfde**, maar fix fonts/kleuren |
| **TOC** | Programmatisch | **Zelfde**, fix fonts/kleuren |
| **Content** | Programmatisch | **Zelfde**, fix fonts/kleuren/marges |
| **Bijlage divider** | Programmatisch | **Optioneel** stationery, of fix code |
| **Backcover** | Programmatisch (fout polygon) | **Stationery PDF** uit referentie ⚡ |

## Prioriteit

1. **Fase 1** (font/kleur fixes) → grootste visuele impact, kleinste effort
2. **Fase 3** (backcover stationery extractie) → lost het hardste probleem op
3. **Fase 2** (stationery architectuur) → maakt het generiek/herbruikbaar
4. **Fase 4** (verificatie) → kwaliteitsborging

## Toekomstig voordeel

Als een nieuw bureau (bijv. "3BM Constructie") een andere huisstijl heeft:
1. Designer levert referentie-PDF aan
2. `extract_stationery.py` haalt achtergrondtemplates eruit
3. Brand YAML wordt aangemaakt met kleuren, fonts, stationery paden
4. Dynamische tekst posities worden ingesteld in de YAML
5. **Geen code wijzigingen nodig** — alleen YAML + stationery bestanden

Dit is het verschil tussen "weken programmeren" en "een uurtje configureren" per nieuw bureau.
