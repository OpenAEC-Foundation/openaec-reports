# Brand Builder — Automatische Huisstijl Extractie uit Referentie-PDF

## Doel

Een tool die een referentie-PDF accepteert, automatisch alle visuele elementen extraheert met exacte coördinaten, pagina-types classificeert, en een concept brand configuratie genereert. Het resultaat is een volledig ingevulde brand YAML + style overrides die direct door de bestaande `BrandRenderer` en `special_pages.py` gebruikt kunnen worden.

**Waarom:** Elke nieuwe huisstijl vereist nu handmatige analyse + prompt. Met deze tool uploadt een gebruiker een referentie-PDF en krijgt binnen seconden een pixel-exacte brand config terug.

---

## Architectuur

```
Referentie PDF
     │
     ▼
┌─────────────────────────┐
│  1. PDF Extractor        │  PyMuPDF: tekst, rects, lijnen, images
│     (per pagina)         │  → RawPageData[]
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  2. Page Classifier      │  Heuristieken: welk pagina-type?
│                          │  cover / colofon / toc / content /
│                          │  appendix_divider / backcover
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  3. Pattern Detector     │  Per pagina-type: zones, marges,
│                          │  kleurenpalet, font-map, spacings
│                          │  → BrandAnalysis
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  4. Config Generator     │  BrandAnalysis → brand YAML +
│                          │  style overrides + page specs
│                          │  → BrandDraft
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  5. API Endpoint         │  POST /api/analyze-brand
│     + Frontend Editor    │  Upload → preview → bewerk → exporteer
└─────────────────────────┘
```

---

## Stap 1: PDF Extractor — `src/openaec_reports/tools/pdf_extractor.py`

### Dependencies

Voeg toe aan `pyproject.toml`:
```toml
[project.optional-dependencies]
brand-tools = ["pymupdf>=1.24"]
```

### Datamodellen

```python
from dataclasses import dataclass, field

@dataclass
class TextElement:
    """Geëxtraheerd tekstelement met exacte positie."""
    text: str
    x: float          # pt, linkerkant
    y_top: float      # pt, bovenkant (PDF origin = linksonder, maar PyMuPDF geeft top-down)
    x2: float         # pt, rechterkant
    y_bottom: float   # pt, onderkant
    font: str         # bv "GothamBold", "Gotham-Book"
    size: float       # pt
    color_hex: str    # "#401246"

@dataclass
class RectElement:
    """Geëxtraheerd rechthoek/lijn element."""
    x: float
    y: float
    width: float
    height: float
    fill_hex: str | None = None     # None = geen fill
    stroke_hex: str | None = None   # None = geen stroke
    stroke_width: float = 0.0
    element_type: str = "rect"      # "rect" | "line"

@dataclass
class ImageElement:
    """Geëxtraheerde afbeelding metadata."""
    x: float
    y: float
    width: float
    height: float
    xref: int           # PyMuPDF cross-reference voor extractie

@dataclass
class RawPageData:
    """Alle geëxtraheerde elementen van één pagina."""
    page_number: int    # 1-based
    width_pt: float
    height_pt: float
    texts: list[TextElement] = field(default_factory=list)
    rects: list[RectElement] = field(default_factory=list)
    images: list[ImageElement] = field(default_factory=list)
    page_image_path: str | None = None   # PNG render pad
```

### Extractie functie

```python
def extract_pdf(pdf_path: Path, output_dir: Path, dpi: int = 150) -> list[RawPageData]:
    """Extracteer alle elementen uit een PDF.

    Args:
        pdf_path: Pad naar de referentie PDF.
        output_dir: Map voor pagina-afbeeldingen (PNG).
        dpi: Render resolutie voor pagina-previews.

    Returns:
        Lijst van RawPageData per pagina.
    """
```

**Implementatiedetails:**

1. Open PDF met `fitz.open()`
2. Per pagina:
   - Render naar PNG (voor visuele preview in frontend)
   - `page.get_text("dict")` → loop door blocks → lines → spans → maak TextElement per span
   - `page.get_drawings()` → classificeer als rect of line gebaseerd op aspect ratio
   - `page.get_images(full=True)` → maak ImageElement (positie via `page.get_image_rects()`)
   - Converteer PyMuPDF kleuren (float tuple) naar hex strings
3. Return lijst van RawPageData

**Belangrijk: coördinatensysteem**
- PyMuPDF gebruikt top-left origin (y=0 is bovenkant)
- ReportLab gebruikt bottom-left origin (y=0 is onderkant)
- Sla op in PyMuPDF coördinaten (top-down), converteer pas in stap 4 naar ReportLab

---

## Stap 2: Page Classifier — `src/openaec_reports/tools/page_classifier.py`

### Pagina-types

```python
from enum import Enum

class PageType(str, Enum):
    COVER = "cover"
    COLOFON = "colofon"
    TOC = "toc"
    CONTENT = "content"
    APPENDIX_DIVIDER = "appendix_divider"
    BACKCOVER = "backcover"
    UNKNOWN = "unknown"
```

### Classificatie heuristieken

```python
def classify_page(page: RawPageData, page_index: int, total_pages: int) -> PageType:
    """Classificeer een pagina op basis van visuele kenmerken.

    Heuristieken (in volgorde van prioriteit):
    1. page_index == 0 → COVER (eerste pagina)
    2. page_index == total_pages - 1 → BACKCOVER (laatste pagina)
    3. Groot gekleurd vlak (>60% pagina) + weinig tekst → COVER of APPENDIX_DIVIDER
    4. Pagina met veel key-value paren (label: waarde) → COLOFON
    5. Pagina met tekst + paginanummers in een kolom → TOC
    6. Anders → CONTENT
    """
```

**Specifieke detectie-signalen:**

| Type | Signalen |
|------|----------|
| **COVER** | Pagina 1, grote afbeelding of gekleurd vlak >50% oppervlak, <10 tekstelementen, grote fontsizes (>20pt) |
| **COLOFON** | Pagina 2-3, key-value layout (twee tekst-kolommen), scheidingslijnen, labels + waarden patroon |
| **TOC** | Woord "Inhoud"/"Inhoudsopgave"/"Contents" in grote font, drie-kolom layout (nummer, titel, pagina), paginanummers rechts uitgelijnd |
| **CONTENT** | Meeste pagina's, lopende tekst, headings + body, consistente marges |
| **APPENDIX_DIVIDER** | Groot gekleurd vlak, weinig maar grote tekst (>30pt), woord "Bijlage"/"Appendix"/"Annex" |
| **BACKCOVER** | Laatste pagina, groot gekleurd vlak, contactgegevens, logo |

**Output:**

```python
@dataclass
class ClassifiedPage:
    page: RawPageData
    page_type: PageType
    confidence: float   # 0.0 - 1.0
```

---

## Stap 3: Pattern Detector — `src/openaec_reports/tools/pattern_detector.py`

Analyseert de geclassificeerde pagina's en detecteert herhalende patronen.

### Kleurenpalet extractie

```python
def extract_color_palette(pages: list[ClassifiedPage]) -> dict[str, str]:
    """Extraheer het kleurenpalet uit alle pagina's.

    Methode:
    1. Verzamel alle unieke kleuren (uit tekst + rects)
    2. Filter wit (#ffffff) en zwart (#000000)
    3. Cluster vergelijkbare kleuren (ΔE < 5 in LAB ruimte)
    4. Sorteer op frequentie
    5. Wijs rollen toe:
       - Meest voorkomende donkere kleur → "primary"
       - Meest voorkomende heldere kleur → "secondary"
       - Body tekst kleur (meest frequent in content pagina's) → "text"
       - Heading kleur in content (anders dan body) → "text_accent"

    Returns:
        Dict van kleurnaam → hex waarde, bv:
        {"primary": "#401246", "secondary": "#38BDAB", "text": "#45243D", ...}
    """
```

### Font-map extractie

```python
def extract_font_map(pages: list[ClassifiedPage]) -> dict[str, str]:
    """Extraheer de font-mapping uit alle pagina's.

    Methode:
    1. Verzamel alle unieke font-namen
    2. Normaliseer varianten (bv "Gotham-Book" en "GothamBook" → zelfde family)
    3. Detecteer rollen:
       - Grootste font op cover → heading font
       - Meest voorkomende font in body tekst → body font
       - Dikgedrukte variant → bold font
       - Cursieve variant → italic font

    Returns:
        {"heading": "GothamBold", "body": "GothamBook", "medium": "GothamMedium", ...}
    """
```

### Marge detectie

```python
def detect_margins(content_pages: list[ClassifiedPage]) -> dict[str, float]:
    """Detecteer content marges uit content pagina's.

    Methode:
    1. Neem alle content pagina's
    2. Per pagina: bepaal min(x) van tekst, max(x2), min(y_top), max(y_bottom)
    3. Neem de mediaan over alle pagina's (robuust tegen uitschieters)
    4. Controleer of er een footer zone is (tekst/elementen in onderste 30mm)

    Returns:
        {"left_mm": 31.7, "right_mm": 18.9, "top_mm": 26.4, "bottom_mm": 13.7}
    """
```

### Header/Footer zone detectie

```python
def detect_zones(content_pages: list[ClassifiedPage]) -> dict:
    """Detecteer header en footer zones uit content pagina's.

    Methode:
    1. Zoek elementen die op ELKE content pagina voorkomen op dezelfde positie
    2. Groepeer deze "vaste" elementen per zone (boven/onder)
    3. Bepaal zone hoogte uit de bounding box van vaste elementen
    4. Classificeer elk vast element (rect, text met variabelen, image)

    Returns:
        {
            "header": {"height_mm": 0, "elements": []},  # of met elementen
            "footer": {"height_mm": 17, "elements": [
                {"type": "text", "content": "{page}", "x": 188, "y": 5, ...}
            ]}
        }
    """
```

**Detectie van variabele tekst:**
- Als een tekstelement op elke pagina voorkomt maar met andere inhoud → het is een variabele
- Vergelijk tekst: als het een getal is dat oploopt → `{page}`
- Als het overeenkomt met bekende velden → `{project}`, `{date}`, etc.

### Style extractie uit content pagina's

```python
def extract_styles(content_pages: list[ClassifiedPage]) -> dict:
    """Extraheer paragraph styles uit content pagina's.

    Methode:
    1. Groepeer tekstelementen per (font, size, color) combinatie
    2. Identificeer rollen:
       - Grootste font → Heading1
       - Middelste font → Heading2
       - Meest voorkomende font/size → Normal (body)
       - Klein font op dezelfde positie als rects → tabel tekst
    3. Meet leading (afstand tussen opeenvolgende regels van zelfde stijl)
    4. Meet spaceBefore/spaceAfter (afstand tussen blokken)

    Returns:
        {
            "Heading1": {"font": "GothamBook", "size": 18.0, "color": "#45243D", "leading": 23.4},
            "Heading2": {"font": "GothamBook", "size": 13.0, "color": "#56B49B", "leading": 16.9},
            "Normal": {"font": "GothamBook", "size": 9.5, "color": "#45243D", "leading": 12.0},
            ...
        }
    """
```

### Tabel stijl detectie

```python
def detect_table_styles(content_pages: list[ClassifiedPage]) -> dict | None:
    """Detecteer tabel styling als er tabellen gevonden worden.

    Signalen voor tabellen:
    - Gekleurde rechthoeken met tekst erin (header rij)
    - Regelmatig grid van tekstelementen
    - Afwisselende rij-kleuren

    Returns:
        {"header_bg": "#45233C", "header_text": "#FFFFFF",
         "footer_bg": "#55B49B", "body_text": "#45243D"} | None
    """
```

### Hoofdresultaat

```python
@dataclass
class BrandAnalysis:
    """Volledig analyse-resultaat van een referentie-PDF."""
    # Basisinfo
    source_pdf: str
    page_count: int
    page_size: tuple[float, float]   # (width_mm, height_mm)

    # Geclassificeerde pagina's
    classified_pages: list[ClassifiedPage]

    # Geëxtraheerde patronen
    colors: dict[str, str]
    fonts: dict[str, str]
    margins: dict[str, float]
    header_zone: dict              # ZoneConfig-achtig
    footer_zone: dict              # ZoneConfig-achtig
    styles: dict[str, dict]        # ParagraphStyle specs

    # Pagina-specifieke specs
    cover_spec: dict | None = None
    colofon_spec: dict | None = None
    toc_spec: dict | None = None
    appendix_divider_spec: dict | None = None
    backcover_spec: dict | None = None

    # Tabel stijl
    table_style: dict | None = None

    # Pagina afbeeldingen (paden naar PNGs)
    page_images: list[str] = field(default_factory=list)
```

---

## Stap 4: Config Generator — `src/openaec_reports/tools/config_generator.py`

Converteert `BrandAnalysis` naar concrete configuratiebestanden.

### Output 1: Brand YAML

```python
def generate_brand_yaml(analysis: BrandAnalysis, brand_name: str, brand_slug: str) -> str:
    """Genereer een brand YAML string uit de analyse.

    Converteert:
    - colors → colors sectie
    - fonts → fonts sectie
    - header_zone → header sectie (met coördinaten omgezet van top-down naar bottom-up mm)
    - footer_zone → footer sectie

    BELANGRIJK: Coördinaat conversie!
    - PyMuPDF y_top (top-down, pt) → ReportLab y (bottom-up, mm, relatief aan zone)
    - Formule: y_reportlab = (page_height_pt - y_bottom_pymupdf) / 2.8346 - zone_origin_mm

    Returns:
        YAML string klaar om op te slaan als .yaml bestand.
    """
```

### Output 2: Style Overrides

```python
def generate_style_overrides(analysis: BrandAnalysis) -> dict:
    """Genereer style overrides die styles.py moet gebruiken.

    Returns:
        Dict die direct kan worden toegepast op de ParagraphStyles:
        {
            "Normal": {"fontSize": 9.5, "leading": 12.0, "textColor": "#45243D"},
            "Heading1": {"fontName": "GothamBook", "fontSize": 18.0, ...},
            ...
        }
    """
```

### Output 3: Pagina specs

```python
def generate_page_specs(analysis: BrandAnalysis) -> dict:
    """Genereer specificaties voor speciale pagina's (colofon, TOC, appendix divider).

    Dit zijn de parameters die special_pages.py nodig heeft om
    deze pagina's correct te tekenen.

    Returns:
        {
            "colofon": {
                "title_font": "GothamBold", "title_size": 22,
                "fields": [...], "separator_lines": [...],
                "footer_rect": {...}
            },
            "toc": {
                "title": "Inhoud", "title_size": 18,
                "level1": {"font": ..., "size": 12, "color": "#56B49B"},
                "level2": {"font": ..., "size": 9.5, "color": "#45243D"},
                "columns": {"number_x": 90, "title_x": 160.9, "page_x": 515.4}
            },
            "appendix_divider": {
                "bg_color": "#37BCAB",
                "title_font": "GothamBold", "title_size": 41.4,
                ...
            }
        }
    """
```

---

## Stap 5: API Endpoint — `src/openaec_reports/api.py` uitbreiding

### POST /api/analyze-brand

```
POST /api/analyze-brand
Content-Type: multipart/form-data

Form fields:
  - pdf: File (de referentie PDF)
  - brand_name: string (optioneel, default uit bestandsnaam)
  - brand_slug: string (optioneel, auto-generated)

Response: 200 OK
{
    "brand_slug": "3bm-cooperatie",
    "analysis": {
        "page_count": 36,
        "page_size": [210.0, 297.0],
        "classified_pages": [
            {"page_number": 1, "type": "cover", "confidence": 0.95},
            {"page_number": 2, "type": "colofon", "confidence": 0.88},
            ...
        ],
        "colors": {"primary": "#401246", "secondary": "#38BDAB", ...},
        "fonts": {"heading": "GothamBold", "body": "GothamBook", ...},
        "margins": {"left_mm": 31.7, ...},
        "styles": {...},
        "header_zone": {...},
        "footer_zone": {...},
        "table_style": {...}
    },
    "generated": {
        "brand_yaml": "brand:\n  name: ...\n...",
        "style_overrides": {...},
        "page_specs": {...}
    },
    "page_images": [
        "/api/brand-analysis/3bm-cooperatie/pages/1.png",
        "/api/brand-analysis/3bm-cooperatie/pages/2.png",
        ...
    ]
}
```

### GET /api/brand-analysis/{slug}/pages/{page_num}.png

Serveert de gerenderde pagina-afbeeldingen voor de frontend preview.

### POST /api/brand-analysis/{slug}/save

Slaat de (evt. handmatig bijgewerkte) brand config op als definitieve YAML.

```
POST /api/brand-analysis/{slug}/save
Content-Type: application/json

{
    "brand_yaml": "...",
    "style_overrides": {...},
    "page_specs": {...}
}

Response: 200 OK
{"saved": true, "path": "assets/brands/3bm-cooperatie.yaml"}
```

---

## Stap 6: Frontend Brand Editor — `src/pages/BrandBuilder.tsx`

### Route

Voeg een nieuwe route toe (of een tab in de AppShell): `/brand-builder`

### Layout

```
┌──────────────────────────────────────────────────────┐
│  Brand Builder                            [Opslaan]  │
├─────────────┬────────────────────────────────────────┤
│             │                                        │
│  PDF Upload │   Pagina Preview                       │
│  ─────────  │   (geselecteerde pagina als image)     │
│             │                                        │
│  Pagina's:  │   Overlay: geëxtraheerde elementen     │
│  □ p1 cover │   met bounding boxes + labels          │
│  □ p2 colof │                                        │
│  □ p3 toc   │                                        │
│  □ p4 cont  │                                        │
│  □ p5 cont  │                                        │
│  ...        │                                        │
│  □ p36 back │                                        │
│             │                                        │
├─────────────┼────────────────────────────────────────┤
│             │                                        │
│  Kleuren:   │   Brand Config Preview (YAML)          │
│  ■ primary  │   ─────────────────────                │
│  ■ seconda  │   brand:                               │
│  ■ text     │     name: "3BM Coöperatie"             │
│             │   colors:                              │
│  Fonts:     │     primary: "#401246"                  │
│  heading:   │     ...                                │
│  body:      │   footer:                              │
│  ...        │     height: 17                         │
│             │     elements:                          │
│  Styles:    │       - type: text ...                 │
│  H1: 18pt   │                                        │
│  H2: 13pt   │                                        │
│  Body: 9.5  │                                        │
│             │                                        │
└─────────────┴────────────────────────────────────────┘
```

### Workflow

1. **Upload**: Gebruiker dropt een PDF → frontend stuurt naar `/api/analyze-brand`
2. **Review**: Pagina's verschijnen links met automatisch gedetecteerd type. Gebruiker kan type corrigeren via dropdown.
3. **Preview**: Klik op een pagina → toont de PNG met transparante overlay van gedetecteerde elementen (rects in blauw, tekst in groen, images in paars)
4. **Configuratie**: Rechts toont het gegenereerde kleurenpalet, fonts, marges, styles. Elk veld is bewerkbaar.
5. **YAML Preview**: Live YAML preview van de brand config
6. **Opslaan**: Klik opslaan → POST naar `/api/brand-analysis/{slug}/save`

### Componenten

| Component | Doel |
|-----------|------|
| `BrandBuilder.tsx` | Hoofd layout + state management |
| `PdfUploader.tsx` | Drag & drop PDF upload |
| `PageList.tsx` | Thumbnail lijst met type labels + correctie dropdown |
| `PagePreview.tsx` | Pagina-afbeelding met element overlay |
| `ColorPalette.tsx` | Kleurenpalet editor (color pickers) |
| `FontMap.tsx` | Font mapping editor |
| `StyleEditor.tsx` | Paragraph style editor per heading level |
| `YamlPreview.tsx` | Live YAML output (read-only of editable) |

---

## Stap 7: Integratie met bestaand systeem

### Brand YAML uitbreiding

De huidige brand YAML ondersteunt `header`, `footer`, `colors`, `fonts`, `logos`, `contact`. Voeg toe:

```yaml
# Nieuw: style overrides
styles:
  Normal:
    fontSize: 9.5
    leading: 12.0
    textColor: "#45243D"
  Heading1:
    fontName: "GothamBook"  # Let op: Book, niet Bold
    fontSize: 18.0
    textColor: "#45243D"
  Heading2:
    fontName: "GothamBook"
    fontSize: 13.0
    textColor: "#56B49B"

# Nieuw: speciale pagina specs
pages:
  colofon:
    title_font: "GothamBold"
    title_size: 22.0
    # ... volledige spec
  toc:
    title: "Inhoud"
    level1_color: "#56B49B"
    level2_color: "#45243D"
    # ...
  appendix_divider:
    bg_color: "#37BCAB"
    # ...
```

### Aanpassing `styles.py`

```python
def create_stylesheet(brand: BrandConfig | None = None) -> StyleSheet1:
    """Maak stylesheet, optioneel met brand-specifieke overrides."""
    styles = StyleSheet1()

    # Defaults
    styles.add(ParagraphStyle(name="Normal", ...))
    styles.add(ParagraphStyle(name="Heading1", ...))
    # etc.

    # Brand overrides toepassen
    if brand and hasattr(brand, 'styles'):
        for style_name, overrides in brand.styles.items():
            if style_name in styles:
                for attr, value in overrides.items():
                    if attr == 'textColor':
                        value = HexColor(value)
                    setattr(styles[style_name], attr, value)

    return styles
```

### Aanpassing `special_pages.py`

```python
def draw_colofon_page(canvas, doc, config, brand, data):
    """Teken colofon — nu configureerbaar via brand.pages.colofon."""
    spec = brand.pages.get('colofon', {}) if hasattr(brand, 'pages') else {}
    # Gebruik spec voor posities, fonts, kleuren
    # Fallback naar hardcoded defaults als spec leeg is
```

---

## Bestandsoverzicht

### Backend (nieuw)

| Bestand | Doel |
|---------|------|
| `src/openaec_reports/tools/__init__.py` | Package init |
| `src/openaec_reports/tools/pdf_extractor.py` | PDF → RawPageData[] |
| `src/openaec_reports/tools/page_classifier.py` | RawPageData → ClassifiedPage |
| `src/openaec_reports/tools/pattern_detector.py` | Kleuren, fonts, marges, zones, styles |
| `src/openaec_reports/tools/config_generator.py` | Analysis → YAML + overrides |
| `tests/test_pdf_extractor.py` | Unit tests |
| `tests/test_page_classifier.py` | Unit tests |
| `tests/test_pattern_detector.py` | Unit tests |
| `tests/test_config_generator.py` | Unit tests |

### Backend (wijzigingen)

| Bestand | Wijziging |
|---------|-----------|
| `src/openaec_reports/api.py` | +3 endpoints (analyze-brand, pages, save) |
| `src/openaec_reports/core/brand.py` | BrandConfig uitbreiden met `styles` en `pages` |
| `src/openaec_reports/core/styles.py` | `create_stylesheet()` accepteert brand overrides |
| `src/openaec_reports/core/special_pages.py` | Gebruik brand.pages specs i.p.v. hardcoded waarden |
| `pyproject.toml` | PyMuPDF dependency |

### Frontend (nieuw)

| Bestand | Doel |
|---------|------|
| `src/pages/BrandBuilder.tsx` | Hoofd pagina |
| `src/components/brand/PdfUploader.tsx` | Upload component |
| `src/components/brand/PageList.tsx` | Pagina thumbnails + type selector |
| `src/components/brand/PagePreview.tsx` | Afbeelding + element overlay |
| `src/components/brand/ColorPalette.tsx` | Kleurenpalet editor |
| `src/components/brand/FontMap.tsx` | Font mapping |
| `src/components/brand/StyleEditor.tsx` | Paragraph styles |
| `src/components/brand/YamlPreview.tsx` | YAML output |
| `src/services/brandApi.ts` | API client voor brand endpoints |
| `src/stores/brandStore.ts` | Zustand store voor brand builder state |

---

## Implementatievolgorde

### Fase A: Backend Extractie (kan standalone draaien)
1. `pdf_extractor.py` + tests
2. `page_classifier.py` + tests
3. `pattern_detector.py` + tests
4. `config_generator.py` + tests
5. CLI command: `openaec-report analyze-brand input.pdf --output brand.yaml`

### Fase B: API Integratie
1. Nieuwe endpoints in `api.py`
2. `BrandConfig` uitbreiden (styles, pages)
3. `styles.py` aanpassen voor brand overrides
4. `special_pages.py` configureerbaar maken

### Fase C: Frontend Brand Editor
1. Store + API client
2. Upload + pagina lijst
3. Preview met overlay
4. Config editors
5. YAML export + opslaan

---

## Niet in scope (later)

- Multi-brand switching in de report editor (template selecteert automatisch brand)
- Logo extractie uit PDF (complexe vector paths → SVG conversie)
- Automatische font installatie (geëxtraheerde fonts → assets/fonts/)
- Versioning van brand configs
- Brand vergelijking (diff tussen twee brands)
