# Fase A: Brand Analyzer — Backend PDF Extractie Pipeline

## Context

Je werkt in het `openaec-reports` project: een modulaire PDF report generator voor 3BM Bouwkunde.
Project root: huidige directory (bevat `pyproject.toml`, `src/openaec_reports/`, `tests/`).

Het bestaande brand systeem (`src/openaec_reports/core/brand.py`) laadt YAML configs met kleuren, fonts, header/footer zones. Wat ontbreekt is **automatische extractie** van deze config uit een referentie-PDF. Dat bouwen we nu.

## Referentiebestanden

- **Ground truth specificatie:** `huisstijl/HUISSTIJL_SPEC.md` — handmatig geëxtraheerde layout specs uit de referentie-PDF. Gebruik dit als validatie-target voor je extractie.
- **Referentie PDF:** `huisstijl/2707_BBLrapportage_v01.pdf` — 36 pagina's, A4 portrait (595.3×841.9 pt). Pagina's 1-21 en 36 zijn A4, pagina's 22-35 zijn US Letter bijlagen.
- **Bestaande brand YAML:** `src/openaec_reports/assets/brands/3bm_cooperatie.yaml` — huidige (deels incorrecte) config.
- **Bestaande brand code:** `src/openaec_reports/core/brand.py` — `BrandConfig`, `ZoneConfig`, `ElementConfig` dataclasses + `BrandLoader`.
- **Bestaande styles:** `src/openaec_reports/core/styles.py`
- **Bestaande CLI:** `src/openaec_reports/cli.py` — heeft al generate/templates/validate/serve commands.

## Opdracht

Bouw een `src/openaec_reports/tools/` package met 4 modules die samen een referentie-PDF analyseren en een brand config genereren. Plus een CLI command en tests.

---

## Module 1: `src/openaec_reports/tools/pdf_extractor.py`

Extraheert alle visuele elementen uit een PDF met PyMuPDF.

### Datamodellen

```python
@dataclass
class TextElement:
    text: str
    x: float           # pt, linkerkant
    y_top: float        # pt, bovenkant (PyMuPDF top-down)
    x2: float           # pt, rechterkant
    y_bottom: float     # pt, onderkant
    font: str           # bv "GothamBold", "Gotham-Book"
    size: float         # pt
    color_hex: str      # "#401246"

@dataclass
class RectElement:
    x: float            # pt
    y: float            # pt (top-down)
    width: float        # pt
    height: float       # pt
    fill_hex: str | None = None
    stroke_hex: str | None = None
    stroke_width: float = 0.0
    element_type: str = "rect"   # "rect" | "line"

@dataclass
class ImageElement:
    x: float
    y: float
    width: float
    height: float
    xref: int

@dataclass
class RawPageData:
    page_number: int        # 1-based
    width_pt: float
    height_pt: float
    texts: list[TextElement]
    rects: list[RectElement]
    images: list[ImageElement]
    page_image_path: str | None = None   # PNG pad voor preview
```

### Functie

```python
def extract_pdf(pdf_path: Path, output_dir: Path | None = None, dpi: int = 150) -> list[RawPageData]:
```

- Open PDF met `fitz.open()`
- Per pagina:
  - Als `output_dir` opgegeven: render naar PNG (`page.get_pixmap(dpi=dpi)`)
  - `page.get_text("dict")` → loop blocks → lines → spans → `TextElement` per span (skip lege tekst)
  - `page.get_drawings()` → classificeer: als breedte of hoogte < 2pt → `element_type="line"`, anders `"rect"`
  - Converteer kleuren: float tuple `(r, g, b)` → hex `"#RRGGBB"`. `None` fill/color → `None`.
  - `page.get_images(full=True)` → `ImageElement` (gebruik `page.get_image_rects(xref)` voor positie)
- Filter rects: skip rects die de hele pagina vullen (breedte > 90% pagina EN hoogte > 90%) tenzij ze een niet-witte kleur hebben
- Return `list[RawPageData]`

---

## Module 2: `src/openaec_reports/tools/page_classifier.py`

Classificeert pagina's op type.

### Enum en resultaat

```python
class PageType(str, Enum):
    COVER = "cover"
    COLOFON = "colofon"
    TOC = "toc"
    CONTENT = "content"
    APPENDIX_DIVIDER = "appendix_divider"
    BACKCOVER = "backcover"
    UNKNOWN = "unknown"

@dataclass
class ClassifiedPage:
    page: RawPageData
    page_type: PageType
    confidence: float       # 0.0 - 1.0
```

### Functie

```python
def classify_pages(pages: list[RawPageData]) -> list[ClassifiedPage]:
```

Heuristieken (in volgorde):

1. **Pagina 1** → `COVER` (confidence 0.95). Bevestig: groot gekleurd vlak (>40% pagina), weinig tekst (<15 elementen), grote fonts (>20pt).
2. **Laatste pagina** → `BACKCOVER` (confidence 0.90). Bevestig: gekleurd vlak, contactgegevens (zoek "T.", telefoonnummer patroon, website URL).
3. **Appendix divider** → Zoek pagina's met: groot gekleurd vlak (>80% oppervlak), weinig tekst (<8 elementen), grote fonts (>30pt), woorden "Bijlage"/"Appendix"/"Annex" (case-insensitive).
4. **Colofon** → Zoek in pagina's 2-4: veel scheidingslijnen (>4 horizontale lijnen), key-value layout (twee clusters van tekst-x-posities), labels in bold font.
5. **TOC** → Zoek woord "Inhoud"/"Inhoudsopgave"/"Contents" in font >14pt. Bevestig: drie-kolom layout (nummer links, titel midden, paginanummer rechts uitgelijnd).
6. **Rest** → `CONTENT`.

---

## Module 3: `src/openaec_reports/tools/pattern_detector.py`

Detecteert herhalende patronen over geclassificeerde pagina's.

### Resultaat

```python
@dataclass
class BrandAnalysis:
    source_pdf: str
    page_count: int
    page_size_mm: tuple[float, float]     # (width, height) in mm
    classified_pages: list[ClassifiedPage]
    colors: dict[str, str]                # {"primary": "#401246", ...}
    fonts: dict[str, str]                 # {"heading": "GothamBold", ...}
    margins_mm: dict[str, float]          # {"left": 31.7, "right": 18.9, ...}
    header_zone: dict                     # {"height_mm": 0, "elements": []}
    footer_zone: dict                     # {"height_mm": 17, "elements": [...]}
    styles: dict[str, dict]               # {"Heading1": {"font": ..., "size": ...}, ...}
    table_style: dict | None
    cover_spec: dict | None
    colofon_spec: dict | None
    toc_spec: dict | None
    appendix_divider_spec: dict | None
    backcover_spec: dict | None
    page_images: list[str]
```

### Sub-functies

**extract_color_palette(pages) → dict[str, str]**
1. Verzamel alle unieke kleuren uit tekst + rect fills (filter #ffffff, #000000)
2. Cluster vergelijkbare kleuren (verschil < 10 in elke RGB component → zelfde kleur, neem de meest voorkomende)
3. Tel frequentie per kleur, gescheiden voor "donkere" (sum RGB < 384) en "lichte" (sum RGB >= 384) kleuren
4. Wijs toe: meest voorkomende donkere → `primary`, meest voorkomende lichte → `secondary`
5. Body tekst kleur (meest frequent in content pagina's, font size < 12) → `text`
6. Als er een turquoise/groen-achtige kleur is die verschilt van secondary → `text_accent`

**extract_font_map(pages) → dict[str, str]**
1. Verzamel alle unieke font-namen over alle pagina's
2. Normaliseer: strip varianten (bv "Gotham-Book" → family "Gotham", weight "Book")
3. Font op cover met grootste size → `heading` (neem de bold variant als die bestaat)
4. Meest voorkomende font in content body tekst (size < 12pt) → `body`
5. Als er een "Medium" variant bestaat → `medium`

**detect_margins(content_pages) → dict[str, float]**
1. Per content pagina: min(x) van alle tekst, max(x2), min(y_top), max(y_bottom)
2. Neem mediaan over alle content pagina's
3. Converteer pt → mm (deel door 2.8346)
4. Return `{"left": ..., "right": ..., "top": ..., "bottom": ...}`

**detect_footer_zone(content_pages) → dict**
1. Zoek tekstelementen die op >70% van content pagina's voorkomen in de onderste 50pt
2. Als ze bestaan: bepaal zone hoogte (= pagina_hoogte - min_y_top van vaste elementen, in mm)
3. Classificeer elk vast element:
   - Als tekst een oplopend getal is → `{"type": "text", "content": "{page}", ...}`
   - Als tekst constant is → `{"type": "text", "content": "<de tekst>", ...}`
4. Zoek ook rects die op >70% van content pagina's op dezelfde positie staan → voeg toe als rect elementen
5. Converteer alle posities naar mm, relatief aan de zone onderkant (ReportLab conventie)
6. Als niets gevonden → `{"height_mm": 0, "elements": []}`

**detect_header_zone(content_pages) → dict**
- Zelfde logica als footer maar dan voor de bovenste 60pt van de pagina
- In de referentie-PDF is er geen header op content pagina's, dus dit zou `height_mm: 0` moeten opleveren

**extract_styles(content_pages) → dict[str, dict]**
1. Groepeer alle tekstelementen in content pagina's per (font, size, color_hex) tuple
2. Sorteer groepen op frequentie (hoe vaak komt deze combinatie voor)
3. Grootste font size (>= 16pt) → `Heading1`
4. Middelste font size (12-16pt) → `Heading2`
5. Meest voorkomende font/size combinatie (< 12pt) → `Normal`
6. Als er een size tussen Normal en Heading2 zit → `Heading3`
7. Meet leading: zoek opeenvolgende regels met dezelfde stijl, bereken y_top verschil. Neem mediaan.
8. Per stijl return: `{"font": "...", "size": 9.5, "color": "#45243D", "leading": 12.0}`

**detect_table_styles(content_pages) → dict | None**
1. Zoek gekleurde rects (niet wit, niet pagina-groot) met tekst erin (tekst bbox overlapt rect bbox)
2. Als gevonden: header rect kleur → `header_bg`, tekst kleur op die rect → `header_text`
3. Zoek een 2e rect kleur (totaalrij) → `footer_bg`
4. Return dict of None als geen tabellen gevonden

**Hoofdfunctie:**

```python
def analyze_brand(pages: list[ClassifiedPage], source_pdf: str, page_images: list[str] | None = None) -> BrandAnalysis:
```

Roept alle sub-functies aan, vult BrandAnalysis in. De `*_spec` velden (cover_spec, colofon_spec etc.) zijn voor nu `None` — die vullen we in een latere fase.

---

## Module 4: `src/openaec_reports/tools/config_generator.py`

Converteert BrandAnalysis naar concrete output.

### Functies

**generate_brand_yaml(analysis, brand_name, brand_slug) → str**

Genereert een YAML string die direct als `.yaml` bestand opgeslagen kan worden. Structuur:

```yaml
brand:
  name: "<brand_name>"
  slug: "<brand_slug>"

colors:
  primary: "<analysis.colors['primary']>"
  secondary: "<analysis.colors['secondary']>"
  text: "<analysis.colors['text']>"
  # etc.

fonts:
  heading: "<analysis.fonts['heading']>"
  body: "<analysis.fonts['body']>"
  # etc.

logos:
  main: "logos/<slug>.png"
  tagline: "logos/<slug>-tagline.png"

header:
  height: <analysis.header_zone['height_mm']>
  elements: <geconverteerde elementen>

footer:
  height: <analysis.footer_zone['height_mm']>
  elements: <geconverteerde elementen>

styles:
  Normal:
    fontSize: <...>
    leading: <...>
    textColor: "<...>"
  Heading1:
    fontName: "<...>"
    fontSize: <...>
    textColor: "<...>"
  # etc.
```

Gebruik `yaml.dump()` met `default_flow_style=False`.

**generate_style_overrides(analysis) → dict**

Return de `analysis.styles` dict, klaar voor toepassing op ReportLab ParagraphStyles.

**generate_analysis_report(analysis) → str**

Return een leesbare markdown string met:
- Pagina-classificatie overzicht (tabel)
- Gedetecteerd kleurenpalet (met hex codes)
- Font mapping
- Marges
- Header/footer zone beschrijving
- Style specificaties
- Eventuele tabel stijl

Dit is handig voor debugging en review.

---

## Module 5: `src/openaec_reports/tools/__init__.py`

```python
"""Brand analysis tools — extracteer huisstijl uit referentie-PDF's."""

from .pdf_extractor import extract_pdf, RawPageData, TextElement, RectElement, ImageElement
from .page_classifier import classify_pages, ClassifiedPage, PageType
from .pattern_detector import analyze_brand, BrandAnalysis
from .config_generator import generate_brand_yaml, generate_style_overrides, generate_analysis_report
```

---

## CLI Command: `openaec-report analyze-brand`

Voeg toe aan `src/openaec_reports/cli.py`:

```
openaec-report analyze-brand input.pdf [--output-dir ./output] [--brand-name "3BM Coöperatie"] [--brand-slug "3bm-cooperatie"] [--dpi 150]
```

Stappen:
1. `extract_pdf(input_pdf, output_dir / "pages", dpi)`
2. `classify_pages(pages)`
3. `analyze_brand(classified, source_pdf, page_images)`
4. `generate_brand_yaml(analysis, brand_name, brand_slug)` → schrijf naar `output_dir / f"{slug}.yaml"`
5. `generate_analysis_report(analysis)` → schrijf naar `output_dir / "analysis_report.md"`
6. Print samenvatting naar stdout

---

## Dependency

Voeg `pymupdf` toe aan `pyproject.toml`:

```toml
[project.optional-dependencies]
brand-tools = ["pymupdf>=1.24"]
```

In de code: importeer PyMuPDF met graceful fallback:
```python
try:
    import fitz
except ImportError:
    fitz = None

def extract_pdf(...):
    if fitz is None:
        raise ImportError("PyMuPDF is vereist voor brand analyse. Installeer met: pip install openaec-reports[brand-tools]")
```

---

## Tests: `tests/test_brand_analyzer.py`

Eén testbestand met alle tests. Gebruik de referentie-PDF als fixture (skip als niet aanwezig).

```python
import pytest
from pathlib import Path

REFERENCE_PDF = Path(__file__).parent.parent / "huisstijl" / "2707_BBLrapportage_v01.pdf"
SKIP_NO_PDF = pytest.mark.skipif(not REFERENCE_PDF.exists(), reason="Referentie PDF niet aanwezig")
```

### Test klassen

**TestPdfExtractor**
- `test_extract_page_count`: assert 36 pagina's
- `test_extract_page_dimensions`: pagina 1 = 595.3×841.9 pt (±1pt)
- `test_extract_cover_text`: pagina 1 bevat "BBL-toetsingsrapportage" in font "GothamBold" met size ~29pt
- `test_extract_cover_rects`: pagina 1 heeft een groot paars rect (#401146)
- `test_extract_colofon_text`: pagina 2 bevat labels "Project", "In opdracht van", "Adviseur"
- `test_extract_colofon_lines`: pagina 2 heeft >5 scheidingslijnen
- `test_extract_content_text`: pagina 5 bevat body tekst in Gotham-Book 9.5pt
- `test_extract_page_images`: pagina 1 heeft minimaal 1 image
- `test_extract_without_images_dir`: extract zonder output_dir geeft page_image_path=None

**TestPageClassifier**
- `test_classify_cover`: pagina 1 → COVER
- `test_classify_backcover`: pagina 36 → BACKCOVER
- `test_classify_colofon`: pagina 2 → COLOFON
- `test_classify_toc`: pagina 3 → TOC
- `test_classify_appendix_divider`: pagina 21 → APPENDIX_DIVIDER
- `test_classify_content`: pagina's 4-20 → CONTENT (test een paar)
- `test_all_pages_classified`: elke pagina heeft een type != UNKNOWN

**TestPatternDetector**
- `test_color_palette_primary`: primary begint met "#40" (paars)
- `test_color_palette_secondary`: secondary is een turquoise/groen kleur
- `test_color_palette_text`: text kleur is donkerpaurs (#45243D of dichtbij)
- `test_font_map_heading`: heading font bevat "Gotham" en "Bold"
- `test_font_map_body`: body font bevat "Gotham" en "Book"
- `test_margins_left`: linkermarge ~31-33mm
- `test_margins_right`: rechtermarge ~17-20mm
- `test_header_zone_empty`: header height == 0 (geen header op content pagina's)
- `test_footer_zone_page_number`: footer bevat een element met content "{page}"
- `test_footer_zone_height`: footer height < 20mm (alleen paginanummer, geen groot blok)
- `test_style_heading1_size`: Heading1 size ~18pt
- `test_style_heading2_size`: Heading2 size ~13pt
- `test_style_normal_size`: Normal size ~9.5pt
- `test_style_heading1_not_bold`: Heading1 font is NIET bold (dit is een specifieke vereiste uit de referentie)
- `test_table_style_detected`: table_style is niet None, header_bg is een donkere kleur

**TestConfigGenerator**
- `test_generate_yaml_parseable`: output is geldige YAML (yaml.safe_load succeeds)
- `test_generate_yaml_has_brand_section`: bevat brand.name en brand.slug
- `test_generate_yaml_has_colors`: bevat colors.primary
- `test_generate_yaml_has_footer`: bevat footer.height en footer.elements
- `test_generate_yaml_has_styles`: bevat styles.Normal en styles.Heading1
- `test_generate_report_is_markdown`: output bevat "# " (markdown heading)
- `test_generate_report_contains_colors`: output bevat het woord "primary" en een hex kleur

**TestCLI** (optioneel, alleen als je tijd hebt)
- `test_cli_analyze_brand_creates_files`: run CLI command → output_dir bevat .yaml en .md

---

## Verwachte output bij analyse van de referentie-PDF

Als alles correct werkt, moet de analyse deze resultaten opleveren (gebruik HUISSTIJL_SPEC.md als bron):

```
Pagina-classificatie:
  p1  → COVER
  p2  → COLOFON
  p3  → TOC
  p4-20 → CONTENT
  p21 → APPENDIX_DIVIDER
  p22-35 → CONTENT (US Letter bijlagen)
  p36 → BACKCOVER

Kleuren:
  primary:    #401246 (donkerpaars)
  secondary:  #38BDAB (turquoise cover/colofon)
  text:       #45243D (donkerpaurs body tekst)
  text_accent: #56B49B (licht turquoise headings)

Fonts:
  heading: GothamBold
  body:    Gotham-Book / GothamBook
  medium:  GothamMedium (als gedetecteerd)

Marges (content):
  left:   ~31.7mm (90pt)
  right:  ~18.9mm
  top:    ~26.4mm
  bottom: ~13.7mm

Footer (content pagina's):
  height: ~17mm
  elements: alleen paginanummer (Gotham-Book 9.5pt #45243D, rechts uitgelijnd)
  GEEN turquoise blok, GEEN logo

Styles:
  Heading1: Gotham-Book 18pt #45243D (NOT bold!)
  Heading2: Gotham-Book 13pt #56B49B
  Normal:   Gotham-Book 9.5pt #45243D, leading ~12pt
```

---

## Belangrijk

- **Coördinatensysteem:** PyMuPDF is top-down (y=0 = bovenkant). ReportLab is bottom-up. Sla intern alles top-down op. Converteer alleen in `config_generator.py` bij het genereren van de YAML (footer/header elementen moeten bottom-up mm zijn relatief aan zone).
- **Robuustheid:** Niet elke PDF heeft dezelfde structuur. Gebruik toleranties (±5pt voor posities, ±2pt voor sizes) bij patroonherkenning.
- **Performance:** De referentie-PDF is 36 pagina's / 3.5MB. Extractie moet < 10 seconden duren.
- **Geen hardcoded waarden:** De analyzer mag NIET specifiek voor 3BM gecodeerd zijn. Hij moet werken voor elke willekeurige referentie-PDF.
