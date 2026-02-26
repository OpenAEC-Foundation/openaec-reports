# PROMPT: Huisstijl Studio — Stationery-architectuur + Brand Builder

## Context

Dit is de report generator backend voor 3BM Coöperatie (Python/ReportLab).
Het doel: pixel-perfecte PDF rapporten die 1-op-1 overeenkomen met de referentie-PDF.

**Kernprobleem:** De huidige code tekent alle visuele elementen programmatisch (polygonen, 
rechthoeken, clip-paths). Dit levert nooit pixel-perfecte output op. Complexe geometrie 
(backcover, cover decoratie) wijkt zichtbaar af van het origineel.

**Oplossing:** Stationery-architectuur. Elke pagina bestaat uit 3 lagen:
1. **Achtergrondafbeelding** (stationery PDF) — alle statische geometrie, kleuren, decoratie
2. **Kop/voettekst** — logo, paginanummer (semi-statisch, per paginatype anders)
3. **Dynamische content** — tekst, tabellen, afbeeldingen (modules)

Alle teksten krijgen het juiste font, grootte en kleur uit de brand config.
Alle modules krijgen de juiste padding, fonts, kleuren uit de brand config.

## Referentiedocumenten

Lees deze bestanden voor de volledige specificatie:

- `SPEC_PAGINA_ARCHITECTUUR.md` — Laag-model per paginatype, brand config structuur
- `HUISSTIJL_SPEC.md` (in `huisstijl/`) — Exacte fonts, kleuren, posities per element
- `PLAN_HUISSTIJL_STUDIO.md` — Brand Builder tool architectuur
- `PLAN_STATIONERY_ARCHITECTUUR.md` — Stationery extractie concept
- `PROMPT_FASE_B_FIX_HUISSTIJL.md` — Concrete font/kleur bugs

## Bronbestanden

```
huisstijl/
├── 2707_BBLrapportage_v01.pdf       # Hoofd-referentie BBL rapport (36 pagina's)
├── 3BM-250206-Constructierapport.pdf # Constructie variant  
├── 3BM-Briefpapier-Digitaal.pdf     # Briefpapier (direct bruikbaar als stationery)
├── 3BM-Stamkaart.pdf                # Kleurenpalet, fonts, beeldmerk specificatie
├── 3BM Brief Template.pdf           # Brief template
├── logo's/RGB/SVG/                  # Logo bestanden (SVG)
└── pages/page_01.png ... page_36.png # 150 DPI renders van referentie
```

## Bestaande code

```
src/bm_reports/
├── core/
│   ├── engine.py           # Report class — build pipeline
│   ├── page_templates.py   # PageTemplate registratie + onPage callbacks
│   ├── special_pages.py    # draw_cover_page, draw_colofon_page, draw_backcover_page, etc.
│   ├── brand.py            # BrandConfig + BrandLoader (YAML)
│   ├── brand_renderer.py   # BrandRenderer — tekent header/footer elementen
│   ├── styles.py           # Colors, FontConfig, create_stylesheet, BM_STYLES, BM_COLORS
│   ├── fonts.py            # Gotham font registratie + Helvetica fallback
│   ├── document.py         # DocumentConfig, Margins, PageFormat
│   ├── toc.py              # TOCBuilder
│   └── block_registry.py   # create_block factory
├── components/
│   ├── calculation.py      # CalculationBlock (berekeningsmodule)
│   ├── check_block.py      # CheckBlock (toetsingsmodule)
│   ├── table_block.py      # TableBlock
│   ├── image_block.py      # ImageBlock
│   └── map_block.py        # KadasterMapBlock
├── tools/                  # Brand analyse tools (Fase A — bestaand)
│   ├── pdf_extractor.py    # PyMuPDF extractie (tekst, rects, images)
│   ├── page_classifier.py  # Classificeer pagina's op type
│   ├── pattern_detector.py # Detecteer kleuren, fonts, marges, zones
│   └── config_generator.py # Genereer brand YAML
├── assets/
│   ├── brands/3bm_cooperatie.yaml  # Huidige brand config
│   ├── templates/3bm_cooperatie.yaml # Huidige template config
│   ├── fonts/Gotham-*.ttf          # Gotham fonts (4 varianten)
│   ├── logos/*.png + *.svg         # Logo bestanden
│   └── graphics/                   # LEEG — hier komen stationery bestanden
└── cli.py                  # CLI met analyze-brand command
```

Dependencies: `reportlab>=4.0, PyYAML, Pillow, svglib, pymupdf (optional brand-tools)`
Toevoegen: `pdfrw>=0.4` (voor PDF-als-achtergrond in ReportLab)

---

## FASE 1: Font/kleur fixes (direct, geen architectuurwijziging)

### 1.1 Colors dataclass — `core/styles.py`

```python
# FOUT:
primary: str = "#40124A"    # MOET: "#401246"
secondary: str = "#38BDA0"  # MOET: "#38BDAB"

# TOEVOEGEN:
text_accent: str = "#56B49B"   # H2/H3 headings, TOC level 1
table_header_bg: str = "#45233C"
table_footer_bg: str = "#55B49B"
separator: str = "#E0D0E8"
```

### 1.2 FontConfig defaults — `core/styles.py`

```python
# FOUT:
body_size: float = 9.0      # MOET: 9.5
heading1_size: float = 16.0  # MOET: 18.0
```

### 1.3 Stylesheet — `core/styles.py` → `create_stylesheet()`

Heading1: `fontName=BM_FONTS.body` (GothamBook, NIET Bold!), `textColor="#45243D"`
Heading2: `fontName=BM_FONTS.body`, `textColor="#56B49B"` 
Heading3: `fontName=BM_FONTS.body`, `textColor="#56B49B"`

Zie `HUISSTIJL_SPEC.md` §4.4-4.6 voor exacte waarden.

### 1.4 Brand YAML fonts — `assets/brands/3bm_cooperatie.yaml`

```yaml
# FOUT: verwijst naar Helvetica fallbacks
fonts:
  heading: "Helvetica-Bold"
  body: "Helvetica"

# MOET:
fonts:
  heading: "GothamBold"
  body: "GothamBook"
  medium: "GothamMedium"
  italic: "GothamBookItalic"
```

### 1.5 Hardcoded kleuren — `core/special_pages.py`

Corrigeer bovenaan:
```python
_COLOR_PRIMARY = HexColor("#401246")    # Was: #40124A
_COLOR_SECONDARY = HexColor("#38BDAB")  # Was: #38BDA0
```

Geef `brand` parameter mee aan `_draw_badges()` en andere helpers.
Vervang directe `_COLOR_*` referenties met `_brand_color(brand, ...)` calls.

### 1.6 Module styling doorvoeren

Alle componenten (`calculation.py`, `check_block.py`, `table_block.py`, etc.) gebruiken 
`BM_COLORS` en `BM_STYLES` direct. Na de Colors fix (1.1) kloppen de hex waarden automatisch.
Verifieer dat `create_stylesheet(brand)` wordt gebruikt in `engine.py` (niet `BM_STYLES`).

---

## FASE 2: Stationery extractie systeem

### 2.1 Nieuw bestand: `tools/stationery_extractor.py`

Vereist: `pymupdf` (al in `[brand-tools]` optional dependency)

```python
"""Stationery extractor — extraheer achtergrondtemplates uit referentie-PDF's."""

class StationeryExtractor:
    """Extraheer stationery-pagina's uit een referentie-PDF met PyMuPDF.
    
    Drie extractiemodi:
    1. full     — hele pagina als PDF (voor 100% statische pagina's zoals backcover)
    2. stripped — pagina met tekst in opgegeven zones verwijderd (wit gemaakt)
    3. graphics — pagina met ALLE tekst verwijderd (alleen grafische elementen)
    """
    
    def __init__(self, source_pdf: Path):
        """Open de bron-PDF."""
    
    def extract_full_page(self, page_num: int, output_path: Path) -> Path:
        """Extraheer hele pagina als nieuwe PDF (vectoren behouden).
        
        Gebruik voor: backcover (100% statisch, geen dynamische tekst).
        """
    
    def extract_stripped_page(
        self, page_num: int, output_path: Path,
        strip_zones: list[tuple[float, float, float, float]],
    ) -> Path:
        """Extraheer pagina met specifieke zones leeggemaakt.
        
        strip_zones: lijst van (x0, y0, x1, y1) in PDF coords.
        Tekst in deze zones wordt verwijderd, grafische elementen blijven.
        
        Gebruik voor: cover (strip titel/subtitel zone), colofon (strip labels),
        appendix divider (strip nummer/titel).
        """
    
    def extract_graphics_only(self, page_num: int, output_path: Path) -> Path:
        """Extraheer pagina met ALLE tekst verwijderd.
        
        Behoudt: kleurvlakken, lijnen, afbeeldingen, geometrie.
        Verwijdert: alle tekst inclusief logo-tekst.
        
        Gebruik voor: generieke stationery waar alle tekst dynamisch is.
        Let op: logo's die uit tekst bestaan worden ook verwijderd!
        """
    
    def extract_as_png(self, page_num: int, output_path: Path, dpi: int = 300) -> Path:
        """Extraheer pagina als hoge-resolutie PNG (fallback).
        
        Gebruik als PDF-extractie problemen geeft (corrupte vectoren, etc.).
        Nadeel: rasterisatie, grotere bestandsgrootte.
        """
    
    def copy_external_pdf(self, source_pdf: Path, output_path: Path) -> Path:
        """Kopieer een externe PDF als stationery (bijv. briefpapier).
        
        Valideert dat het een geldige single-page PDF is.
        """
```

**Implementatiedetails:**

Tekst strippen met PyMuPDF:
```python
import fitz

def _strip_text_in_zones(page, zones):
    """Verwijder tekst in specifieke zones via redaction."""
    for (x0, y0, x1, y1) in zones:
        rect = fitz.Rect(x0, y0, x1, y1)
        # Vind tekst in deze zone
        text_dict = page.get_text("dict", clip=rect)
        for block in text_dict["blocks"]:
            if block["type"] == 0:  # tekst blok
                block_rect = fitz.Rect(block["bbox"])
                # Redact met witte vulling
                page.add_redact_annot(block_rect, fill=(1, 1, 1))
    page.apply_redactions()
```

Pagina als PDF extraheren:
```python
def _extract_page_to_pdf(source_doc, page_num, output_path):
    """Extraheer één pagina als nieuwe PDF."""
    new_doc = fitz.open()
    new_doc.insert_pdf(source_doc, from_page=page_num, to_page=page_num)
    new_doc.save(str(output_path))
    new_doc.close()
```

### 2.2 Text zone detectie — `tools/text_zone_mapper.py`

Nieuw bestand dat per paginatype de dynamische tekst-zones bepaalt:

```python
"""Text zone mapper — bepaal waar dynamische tekst komt op stationery pagina's."""

class TextZoneMapper:
    """Bepaal text zones per paginatype op basis van geëxtraheerde tekst."""
    
    def map_cover_zones(self, cover_page: RawPageData) -> list[TextZone]:
        """Bepaal text zones voor de cover pagina.
        
        Zoekt:
        - Grootste tekst (font size) = titel zone
        - Op-één-na-grootste = subtitel zone
        - Foto/image rect = hero_image zone
        """
    
    def map_colofon_zones(self, colofon_page: RawPageData) -> list[TextZone]:
        """Bepaal text zones voor de colofon pagina.
        
        Zoekt:
        - Titel (bovenaan, groot font)
        - Subtitel (onder titel, accent kleur)
        - Label-waarde tabel (twee kolommen met scheidingslijnen)
        """
    
    def map_appendix_divider_zones(self, divider_page: RawPageData) -> list[TextZone]:
        """Bepaal text zones voor de bijlage-scheidingspagina.
        
        Zoekt:
        - "Bijlage N" tekst (groot, donkere kleur)
        - Titel tekst (groot, lichte kleur / wit)
        """
    
    def map_content_zones(self, content_pages: list[RawPageData]) -> ContentFrameSpec:
        """Bepaal content frame en header/footer zones voor content pagina's.
        
        Analyseert meerdere content pagina's om herhalende elementen te vinden.
        Returns content_frame (marges) + header/footer elementen.
        """
    
    def map_backcover_zones(self, backcover_page: RawPageData) -> list[TextZone]:
        """Bepaal aanpasbare text zones op de backcover.
        
        Zoekt contactgegevens (bedrijfsnaam, adres, website).
        """

@dataclass
class TextZone:
    """Definitie van een dynamische tekst-zone op een stationery pagina."""
    role: str              # "title", "subtitle", "number", "company_name", etc.
    x_pt: float            # X positie (PDF coords)
    y_pt: float            # Y positie (top-down vanuit pagina top)
    font: str              # Font referentie ("$fonts.heading")
    size: float            # Font grootte in pt
    color: str             # Kleur referentie ("$colors.primary" of "#401246")
    max_width_pt: float | None = None  # Max breedte voor text wrapping
    align: str = "left"    # "left", "center", "right"
    bind: str | None = None  # Data binding ("project", "contact.name", etc.)
    type: str = "text"     # "text", "clipped_image", "key_value_table"
    # Extra velden voor specifieke types:
    line_spacing_pt: float | None = None   # Voor multi-line titels
    clip_polygon: list | None = None        # Voor clipped_image
    image_rect: list | None = None          # Voor clipped_image
    fields: list | None = None              # Voor key_value_table

@dataclass
class ContentFrameSpec:
    """Content frame specificatie voor content pagina's."""
    x_pt: float
    y_pt: float
    width_pt: float
    height_pt: float
    header_footer_zones: list[TextZone]
```

### 2.3 Stamkaart parser — `tools/stamkaart_parser.py`

Nieuw bestand voor extractie van exacte kleuren uit de stamkaart:

```python
"""Stamkaart parser — extraheer exacte kleuren uit huisstijl stamkaart PDF."""

def extract_colors_from_stamkaart(pages: list[RawPageData]) -> dict[str, str]:
    """Extraheer kleurenpalet uit stamkaart PDF.
    
    Zoekt naar patronen in tekst:
    - "R123 G45 B67" of "123 / 45 / 67" → RGB
    - "#401246" → direct hex
    - "C76 M100 Y36 K43" → CMYK → RGB conversie
    - "PMS 5195" → opzoeken in PMS tabel (best effort)
    
    Matcht kleurtekst aan het dichtstbijzijnde kleurvlak op dezelfde pagina.
    
    Prioriteit: Stamkaart kleuren > rapport pixel-sampling.
    """

def _find_color_text_patterns(texts: list[TextElement]) -> list[ColorMatch]:
    """Zoek RGB/CMYK/Hex patronen in tekstelementen."""

def _match_colors_to_rects(
    color_matches: list[ColorMatch], 
    rects: list[RectElement],
) -> dict[str, str]:
    """Koppel gevonden kleurtekst aan dichtstbijzijnde kleurvlak."""

def _cmyk_to_rgb(c: float, m: float, y: float, k: float) -> str:
    """Converteer CMYK (0-100) naar hex RGB."""
```

---

## FASE 3: Stationery renderer

### 3.1 Nieuw bestand: `core/stationery.py`

```python
"""Stationery renderer — tekent PDF/PNG achtergrondtemplates op ReportLab canvas."""

class StationeryRenderer:
    """Tekent stationery (achtergrond PDF/PNG) als eerste laag op een pagina.
    
    Gebruikt pdfrw om PDF pagina's als XObject te embedden in ReportLab.
    Dit behoudt vector-kwaliteit (geen rasterisatie).
    Fallback naar Pillow voor PNG achtergronden.
    """
    
    def __init__(self, brand_dir: Path):
        """brand_dir = pad naar brand directory (bijv. assets/brands/3bm-cooperatie/)."""
        self._brand_dir = brand_dir
        self._cache: dict[str, Any] = {}
    
    def has_stationery(self, page_type: str, brand: BrandConfig) -> bool:
        """Check of er een stationery template is voor dit paginatype."""
    
    def draw_background(
        self, canvas, page_type: str, page_w: float, page_h: float, brand: BrandConfig,
    ) -> bool:
        """Teken stationery achtergrond op het canvas.
        
        Returns True als getekend, False als geen stationery beschikbaar.
        """
    
    def _draw_pdf_stationery(self, canvas, pdf_path: Path, page_w: float, page_h: float):
        """Render PDF als achtergrond via pdfrw XObject embedding."""
        from pdfrw import PdfReader
        from pdfrw.buildxobj import pagexobj
        from pdfrw.toreportlab import makerl
        
        if str(pdf_path) not in self._cache:
            reader = PdfReader(str(pdf_path))
            self._cache[str(pdf_path)] = pagexobj(reader.pages[0])
        
        xobj = self._cache[str(pdf_path)]
        canvas.saveState()
        # Schaal naar pagina afmetingen
        xobj_w = float(xobj.BBox[2])
        xobj_h = float(xobj.BBox[3])
        sx = page_w / xobj_w
        sy = page_h / xobj_h
        canvas.transform(sx, 0, 0, sy, 0, 0)
        canvas.doForm(makerl(canvas, xobj))
        canvas.restoreState()
    
    def _draw_png_stationery(self, canvas, png_path: Path, page_w: float, page_h: float):
        """Render PNG als full-page achtergrond (fallback)."""
        canvas.drawImage(str(png_path), 0, 0, page_w, page_h, 
                         preserveAspectRatio=False, mask='auto')
```

### 3.2 Integratie in rendering pipeline

**`core/page_templates.py`** — Wijzig `create_page_templates()`:

Per paginatype wordt de `onPage` callback nu:
1. Stationery achtergrond tekenen (als beschikbaar)
2. Kop/voettekst tekenen (als gedefinieerd voor dit type)
3. Text zones tekenen (dynamische tekst op stationery)
4. Fallback naar programmatische rendering (als geen stationery)

```python
def _make_page_callback(page_type, config, brand, stationery_renderer, extra_data=None):
    """Maak een onPage callback die stationery-first werkt."""
    
    def callback(canvas, doc):
        pw = config.effective_width_pt
        ph = config.effective_height_pt
        
        # LAAG 1: Achtergrond
        has_bg = stationery_renderer.draw_background(canvas, page_type, pw, ph, brand)
        
        if has_bg:
            # LAAG 2: Kop/voettekst (als gedefinieerd)
            hf_config = _get_header_footer_config(page_type, brand)
            if hf_config:
                _draw_header_footer(canvas, hf_config, config, brand)
            
            # LAAG 3: Text zones
            text_zones = _get_text_zones(page_type, brand)
            for zone in text_zones:
                _draw_text_zone(canvas, zone, config, brand, extra_data)
        else:
            # FALLBACK: bestaande programmatische rendering
            _FALLBACK_RENDERERS[page_type](canvas, doc, config, brand, **(extra_data or {}))
    
    return callback
```

**`core/special_pages.py`** — Bestaande functies worden fallback renderers:

```python
# Bestaande functies hernoemd als fallback
_FALLBACK_RENDERERS = {
    "cover": draw_cover_page,          # Behoud als fallback
    "colofon": draw_colofon_page,      # Behoud als fallback
    "backcover": draw_backcover_page,  # Behoud als fallback
    "appendix_divider": draw_appendix_divider_page,
    "content": lambda c, d, cfg, b: None,  # Content heeft geen speciale rendering
}
```

### 3.3 Text zone rendering — `core/text_zone_renderer.py`

Nieuw bestand voor het tekenen van dynamische tekst in text zones:

```python
"""Text zone renderer — tekent dynamische tekst op stationery pagina's."""

def draw_text_zone(canvas, zone: dict, config: DocumentConfig, brand: BrandConfig, data: dict):
    """Teken één text zone op het canvas.
    
    Ondersteunde zone types:
    - "text": Enkele tekstregel of multi-line
    - "clipped_image": Afbeelding met clip-path polygon
    - "key_value_table": Twee-kolom label-waarde tabel
    """

def _resolve_zone_font(zone: dict, brand: BrandConfig) -> str:
    """Resolve font referentie ($fonts.heading) naar effectieve font naam."""

def _resolve_zone_color(zone: dict, brand: BrandConfig) -> str:
    """Resolve kleur referentie ($colors.primary) naar hex waarde."""

def _resolve_zone_value(zone: dict, config: DocumentConfig, data: dict) -> str:
    """Resolve data binding (bijv. "project" → config.project)."""

def _draw_text(canvas, zone, text, font, size, color, page_h):
    """Teken tekst op de juiste positie (top-down → bottom-up conversie)."""

def _draw_clipped_image(canvas, zone, image_path, page_w, page_h):
    """Teken afbeelding met clip-path polygon (cover projectfoto)."""

def _draw_key_value_table(canvas, zone, data, brand, page_h):
    """Teken twee-kolom label-waarde tabel (colofon)."""
```

---

## FASE 4: Brand YAML v2

### 4.1 Nieuwe brand directory structuur

Migreer van single YAML file naar directory:

```
assets/brands/3bm-cooperatie/
├── brand.yaml               # Hoofdconfiguratie
├── stationery/
│   ├── cover.pdf            # Cover achtergrond (geëxtraheerd)
│   ├── colofon.pdf          # Colofon achtergrond
│   ├── appendix_divider.pdf # Bijlage divider achtergrond
│   ├── backcover.pdf        # Backcover (100% statisch)
│   └── briefpapier.pdf      # Briefpapier stationery
├── fonts/
│   ├── Gotham-Bold.ttf
│   ├── Gotham-Book.ttf
│   ├── Gotham-Medium.ttf
│   └── Gotham-BookItalic.ttf
└── logos/
    ├── main.svg
    ├── wit.svg
    └── tagline.png
```

### 4.2 Brand YAML v2 schema

Genereer een nieuw `brand.yaml` dat de complete structuur bevat uit `SPEC_PAGINA_ARCHITECTUUR.md`:
- `colors:` met alle kleurvarianten
- `fonts:` met font namen + bestanden
- `styles:` met Heading1-3, Normal, Caption, BulletItem
- `modules:` met table, calculation, check, image, map styling
- `stationery:` met source + text_zones per paginatype
- `header_footer:` met varianten (content, colofon)
- `contact:` bedrijfsgegevens

Zie `SPEC_PAGINA_ARCHITECTUUR.md` voor het volledige schema.

### 4.3 BrandConfig v2 — `core/brand.py`

Breid `BrandConfig` uit met:

```python
@dataclass
class TextZoneConfig:
    role: str
    x_pt: float
    y_pt: float
    font: str = ""
    size: float = 10.0
    color: str = ""
    align: str = "left"
    bind: str = ""
    type: str = "text"
    max_width_pt: float | None = None
    line_spacing_pt: float | None = None
    clip_polygon: list | None = None
    fields: list | None = None

@dataclass
class StationeryPageConfig:
    source: str = ""                   # Pad naar stationery bestand
    header_footer: str | None = None   # Kop/voettekst variant naam
    text_zones: list[TextZoneConfig] = field(default_factory=list)
    content_frame: dict | None = None  # Voor content pagina's

@dataclass
class HeaderFooterVariant:
    header: ZoneConfig = field(default_factory=ZoneConfig)
    footer: ZoneConfig = field(default_factory=ZoneConfig)

@dataclass
class BrandConfig:
    # Bestaande velden (backward compatible)
    name: str = "Default"
    slug: str = "default"
    colors: dict[str, str] = field(default_factory=dict)
    fonts: dict[str, str] = field(default_factory=dict)
    header: ZoneConfig = field(default_factory=ZoneConfig)  # LEGACY
    footer: ZoneConfig = field(default_factory=ZoneConfig)  # LEGACY
    logos: dict[str, str] = field(default_factory=dict)
    contact: dict[str, str] = field(default_factory=dict)
    styles: dict[str, dict] = field(default_factory=dict)
    pages: dict[str, dict] = field(default_factory=dict)
    
    # NIEUW
    stationery: dict[str, StationeryPageConfig] = field(default_factory=dict)
    header_footer_variants: dict[str, HeaderFooterVariant] = field(default_factory=dict)
    modules: dict[str, dict] = field(default_factory=dict)
    brand_dir: Path | None = None  # Pad naar brand directory
```

**BrandLoader** moet zowel single-file YAML als directory structuur laden:
- Als `brands/3bm-cooperatie.yaml` bestaat → laad single file (legacy)
- Als `brands/3bm-cooperatie/brand.yaml` bestaat → laad directory (v2)

---

## FASE 5: Brand Builder CLI tool

### 5.1 Nieuw bestand: `tools/brand_builder.py`

```python
"""Brand Builder — genereer complete brand configuratie uit huisstijl-documenten."""

class BrandBuilder:
    """Orchestreert de volledige brand-extractie pipeline.
    
    Input: set huisstijl-documenten (stamkaart, referentie-rapport, briefpapier, logo's)
    Output: complete brand directory (YAML + stationery + fonts + logo's)
    """
    
    def __init__(self, output_dir: Path, brand_name: str, brand_slug: str):
        self.output_dir = output_dir
        self.brand_name = brand_name
        self.brand_slug = brand_slug
    
    def build(
        self,
        referentie_rapport: Path,
        stamkaart: Path | None = None,
        briefpapier: Path | None = None,
        logo_dir: Path | None = None,
        font_dir: Path | None = None,
        base_brand: Path | None = None,
    ) -> Path:
        """Voer de volledige pipeline uit.
        
        Stappen:
        1. Analyseer referentie-rapport (pagina classificatie + patronen)
        2. Verrijk kleuren uit stamkaart (als aangeleverd)
        3. Extraheer stationery per paginatype
        4. Kopieer briefpapier als stationery (als aangeleverd)
        5. Map text zones per stationery pagina
        6. Kopieer logo's en fonts
        7. Genereer brand.yaml
        8. Genereer analyserapport
        
        base_brand: Optioneel pad naar bestaande brand directory.
        Als opgegeven: overerf kleuren, fonts, logo's en genereer alleen 
        nieuwe stationery + text zones uit het referentie-rapport.
        Handig voor varianten (BBL vs constructie vs brandveiligheid).
        
        Returns: pad naar gegenereerde brand directory.
        """
    
    def _determine_strip_zones(
        self, page_type: str, page_data: RawPageData
    ) -> list[tuple[float, float, float, float]]:
        """Bepaal welke tekst-zones verwijderd moeten worden per paginatype.
        
        Cover: strip titel + subtitel (grootste tekst, onderste deel)
        Colofon: strip rapport-titel, subtitel, alle label-waarde paren
        Appendix divider: strip "Bijlage N" + titel
        Backcover: strip NIETS (100% statisch)
        Content/TOC: geen stationery extractie (programmatisch)
        """
```

### 5.2 CLI command — `cli.py`

Voeg `build-brand` command toe:

```bash
bm-report build-brand \
  --rapport huisstijl/2707_BBLrapportage_v01.pdf \
  --stamkaart huisstijl/3BM-Stamkaart.pdf \
  --briefpapier huisstijl/3BM-Briefpapier-Digitaal.pdf \
  --logos "huisstijl/logo's/RGB/SVG/" \
  --fonts src/bm_reports/assets/fonts/ \
  --name "3BM Coöperatie" \
  --slug "3bm-cooperatie" \
  --output src/bm_reports/assets/brands/3bm-cooperatie/

# Variant met overerving
bm-report build-brand \
  --rapport huisstijl/3BM-250206-Constructierapport.pdf \
  --base-brand src/bm_reports/assets/brands/3bm-cooperatie/ \
  --name "3BM Constructie" \
  --slug "3bm-constructie" \
  --output src/bm_reports/assets/brands/3bm-constructie/
```

---

## FASE 6: Content frame + marges uit brand config

### 6.1 Marges per paginatype

De huidige `DocumentConfig.margins` is globaal. Maar content pagina's bij 3BM BBL hebben:
- Links: 90.0 pt (31.7mm) — veel meer dan standaard 20mm
- Rechts: 53.7 pt (18.9mm)
- Boven: ~74.9 pt (26.4mm)
- Onder: ~38.9 pt (13.7mm)

Dit moet uit de brand config komen, niet uit de globale DocumentConfig.

**Oplossing:** `content_frame` in de stationery config:

```yaml
stationery:
  content:
    content_frame:
      x_pt: 90.0
      y_pt: 48.0       # = page_height - top_margin
      width_pt: 451.6   # = 541.6 - 90.0
      height_pt: 746.0
```

**In `page_templates.py`:** Lees content_frame uit brand.stationery["content"] 
en gebruik het voor het Frame object i.p.v. DocumentConfig.margins.

---

## Uitvoeringsvolgorde

```
FASE 1  →  FASE 3.1  →  FASE 2.1  →  FASE 3.2  →  FASE 4  →  FASE 5  →  FASE 6
fonts/     stationery   extractor    integratie    YAML v2    CLI tool    marges
kleuren    renderer     tool                       brand dir
```

**Fase 1** is de quick win — fix fonts en kleuren, direct visueel resultaat.
**Fase 2.1 + 3.1** samen: extraheer backcover als stationery + render het → pixel-perfect.
**Fase 3.2** integreert stationery in de bestaande rendering pipeline.
**Fase 4** herstructureert de brand config naar directory-based.
**Fase 5** automatiseert alles met de Brand Builder CLI.
**Fase 6** zorgt dat content marges uit de brand config komen.

## Verificatie na elke fase

Na elke fase: genereer een test-PDF en vergelijk met `huisstijl/pages/page_XX.png`:

- [ ] Fase 1: Fonts zijn Gotham (niet Helvetica), kleuren kloppen exact
- [ ] Fase 2+3: Backcover is pixel-perfect identiek aan referentie
- [ ] Fase 4: brand.yaml v2 laadt correct, backward compatible met v1
- [ ] Fase 5: `bm-report build-brand` genereert werkende brand directory
- [ ] Fase 6: Content pagina marges matchen referentie (links=90pt)

## Dependencies toevoegen

In `pyproject.toml`:
```toml
dependencies = [
    # bestaande...
    "pdfrw>=0.4",          # PDF-als-achtergrond in ReportLab
]
```

`pymupdf` blijft optioneel in `[brand-tools]` (alleen nodig voor extractie, niet voor rendering).
