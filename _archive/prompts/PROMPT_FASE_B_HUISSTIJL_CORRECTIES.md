# Fase B: Huisstijl Correcties + Brand Integratie

## Context

Je werkt in het `bm-reports` project (root = huidige directory met `pyproject.toml`).
De Brand Analyzer (Fase A) is compleet: `src/bm_reports/tools/` bevat pdf_extractor, page_classifier, pattern_detector en config_generator.

Nu moeten we:
1. De analyzer draaien op de referentie-PDF om de automatische output te verifiëren
2. De bestaande brand YAML, styles en special_pages corrigeren op basis van de handmatige specificatie
3. Het brand systeem uitbreiden zodat styles en pagina-specs vanuit de YAML configureerbaar zijn
4. De bijlage-divider pagina toevoegen

## Referentiebestanden

Lees deze bestanden **eerst** voordat je begint:

- **`huisstijl/HUISSTIJL_SPEC.md`** — De ground truth. Alle pixel-exacte metingen uit de referentie-PDF. Dit is de bron voor alle correcties.
- **`src/bm_reports/assets/brands/3bm_cooperatie.yaml`** — Huidige (incorrecte) brand YAML
- **`src/bm_reports/core/styles.py`** — Huidige styles met verkeerde waarden
- **`src/bm_reports/core/special_pages.py`** — Cover (OK), colofon (moet herschreven), backcover (OK)
- **`src/bm_reports/core/brand.py`** — BrandConfig dataclass (moet uitgebreid)
- **`src/bm_reports/core/brand_renderer.py`** — Footer/header renderer (werkt al generiek)
- **`src/bm_reports/core/page_templates.py`** — PageTemplate registratie (moet appendix_divider krijgen)
- **`src/bm_reports/core/engine.py`** — Report class (moet appendix ondersteunen)

---

## Stap 1: Draai de analyzer (verifieer Fase A)

Run de analyzer op de referentie-PDF en bewaar de output:

```bash
cd <project_root>
pip install pymupdf --break-system-packages 2>/dev/null || pip install pymupdf
python -m bm_reports.cli analyze-brand huisstijl/2707_BBLrapportage_v01.pdf \
    --output-dir huisstijl/brand_analysis \
    --brand-name "3BM Coöperatie" \
    --brand-slug "3bm-cooperatie" \
    --dpi 72
```

Controleer de output in `huisstijl/brand_analysis/analysis_report.md` en vergelijk met `huisstijl/HUISSTIJL_SPEC.md`. De automatische extractie hoeft niet 100% overeen te komen — de HUISSTIJL_SPEC.md is de ground truth.

---

## Stap 2: BrandConfig uitbreiden met `styles` en `pages`

### `src/bm_reports/core/brand.py`

Voeg twee nieuwe velden toe aan `BrandConfig`:

```python
@dataclass
class BrandConfig:
    name: str = "Default"
    slug: str = "default"
    colors: dict[str, str] = field(default_factory=dict)
    fonts: dict[str, str] = field(default_factory=dict)
    header: ZoneConfig = field(default_factory=ZoneConfig)
    footer: ZoneConfig = field(default_factory=ZoneConfig)
    logos: dict[str, str] = field(default_factory=dict)
    contact: dict[str, str] = field(default_factory=dict)
    # NIEUW:
    styles: dict[str, dict] = field(default_factory=dict)   # Style overrides per paragraph style
    pages: dict[str, dict] = field(default_factory=dict)     # Speciale pagina specs
```

Update `BrandLoader.load()` om de nieuwe secties te parsen:

```python
return BrandConfig(
    # ... bestaande velden ...
    styles=data.get("styles", {}),
    pages=data.get("pages", {}),
)
```

---

## Stap 3: Update `3bm_cooperatie.yaml`

Herschrijf de volledige brand YAML op basis van HUISSTIJL_SPEC.md. De kritieke correcties:

### Footer: ALLEEN paginanummer

De huidige footer heeft een turquoise blok + logo + paginanummer. De referentie toont op content pagina's ALLEEN een kaal paginanummer rechtsonder.

```yaml
footer:
  height: 17          # was 25
  elements:
    - type: text
      content: "{page}"
      x: 188           # ~533pt = rechts uitgelijnd, in mm ≈ 188mm
      y: 5             # ~14pt boven onderkant
      font: "$body"    # Gotham-Book, NIET bold
      size: 9.5        # was 8
      color: "$text"   # #45243D
      align: right
```

### Styles sectie (NIEUW)

Voeg toe op basis van HUISSTIJL_SPEC.md:

```yaml
styles:
  Normal:
    fontName: "GothamBook"
    fontSize: 9.5       # was 9.0
    leading: 12.0
    textColor: "#45243D"
  Heading1:
    fontName: "GothamBook"   # NIET GothamBold! Dit is een cruciale correctie.
    fontSize: 18.0           # was 16.0
    leading: 23.4
    textColor: "#45243D"     # was #40124A
  Heading2:
    fontName: "GothamBook"   # NIET GothamBold!
    fontSize: 13.0
    leading: 16.9
    textColor: "#56B49B"     # was #38BDA0 — let op: ander turquoise
  Heading3:
    fontName: "GothamBook"
    fontSize: 11.0
    leading: 14.3
    textColor: "#56B49B"
```

### Colors: voeg text_accent toe

```yaml
colors:
  primary: "#401246"       # was #40124A — corrigeer (check HUISSTIJL_SPEC)
  secondary: "#38BDAB"     # Cover/colofon turquoise
  text: "#45243D"
  text_accent: "#56B49B"   # Content headings turquoise (lichter dan secondary)
  accent: "#2ECC71"
  warning: "#E74C3C"
  text_light: "#7F8C8D"
```

### Pages sectie (NIEUW)

Voeg pagina-specifieke specs toe voor colofon en TOC:

```yaml
pages:
  colofon:
    # Label kolom
    label_x_pt: 103
    value_x_pt: 229
    # Kleuren
    first_labels_color: "#401246"    # "Project" en "In opdracht van" zijn paars
    other_labels_color: "#38BDAB"    # Rest is turquoise
    value_color: "#401246"
    # Fonts
    label_font: "GothamBook"
    label_size: 10.0
    value_font: "GothamBook"
    value_size: 10.0
    # Scheidingslijnen
    line_x1_pt: 102
    line_x2_pt: 420
    line_stroke_pt: 0.25
    line_color: "#401146"
    # Footer (turquoise blok + logo, alleen op colofon)
    footer_rect: [0, 771, 282, 842]    # [x, y_bottom, width, y_top] in pt
    footer_rect_color: "#38BDAB"
    # Veld volgorde
    fields:
      - {label: "Project", type: "project"}
      - {label: "In opdracht van", type: "client"}
      - {type: "line"}
      - {label: "Adviseur", type: "author"}
      - {label: "Toegepaste Normen", type: "norms"}
      - {type: "line"}
      - {label: "Documentgegevens", type: "document_description"}
      - {type: "line"}
      - {label: "Datum rapport", type: "date"}
      - {type: "line"}
      - {label: "Fase in bouwproces", type: "phase"}
      - {type: "line"}
      - {label: "Rapportstatus", type: "status"}
      - {type: "line"}
      - {label: "Documentkenmerk", type: "document_code"}

  toc:
    title: "Inhoud"
    title_font: "GothamBook"
    title_size: 18.0
    title_color: "#45243D"
    title_x_pt: 90
    title_y_pt: 74.9
    # Level 1 (hoofdstukken)
    level1_font: "GothamBook"
    level1_size: 12.0
    level1_color: "#56B49B"
    # Level 2 (subsecties)
    level2_font: "GothamBook"
    level2_size: 9.5
    level2_color: "#45243D"
    # Kolommen
    number_x_pt: 90
    title_x_pt: 160.9
    page_x_pt: 515.4
    # Spacing
    chapter_spacing_pt: 39
    item_spacing_pt: 17

  appendix_divider:
    bg_color: "#37BCAB"
    # Paars blok linksonder
    purple_rect: [0, 771, 282, 842]
    purple_color: "#401246"
    # Bijlage nummer
    number_font: "GothamBold"
    number_size: 41.4
    number_color: "#401246"
    number_x_pt: 103
    number_y_pt: 193.9
    # Titel regels
    title_font: "GothamBook"
    title_size: 41.4
    title_color: "#FFFFFF"
    title_x_pt: 136.1
    # Tagline
    tagline: "Projecten die inspireren"
    tagline_font: "GothamBold"
    tagline_size: 17.9
    tagline_color: "#401246"
    tagline_x_pt: 330.5
    tagline_y_pt: 785.1
```

---

## Stap 4: Update `styles.py` — Brand overrides toepassen

De `create_stylesheet()` functie moet een optioneel `brand` parameter accepteren en style overrides toepassen:

```python
def create_stylesheet(brand: BrandConfig | None = None) -> StyleSheet1:
    """Maak de 3BM stylesheet, optioneel met brand-specifieke overrides."""
    styles = StyleSheet1()
    
    # Defaults (huidige waarden als fallback)
    styles.add(ParagraphStyle(name="Normal", ...))
    styles.add(ParagraphStyle(name="Heading1", ...))
    # etc. (behoudt bestaande code)
    
    # Brand style overrides toepassen
    if brand and brand.styles:
        for style_name, overrides in brand.styles.items():
            if style_name in styles.byName:
                style = styles[style_name]
                for attr, value in overrides.items():
                    if attr == "textColor":
                        value = HexColor(value)
                    elif attr == "fontName":
                        value = get_font_name(value)  # Gotham fallback
                    setattr(style, attr, value)
    
    return styles
```

**Belangrijk:** De globale `BM_STYLES` wordt nu lazy of met default brand geladen. De `Report` class moet bij `build()` de stylesheet opnieuw aanmaken met de juiste brand:

In `engine.py`, in `_build_elements()` of `build()`:
```python
# Maak brand-aware stylesheet
styles = create_stylesheet(brand=self._brand)
```

En gebruik deze `styles` in plaats van de globale `BM_STYLES` bij het aanmaken van flowables.

**Concreet:**
- Voeg een `self._styles` attribuut toe aan `Report.__init__()` dat `create_stylesheet(brand=self._brand)` aanroept
- Gebruik `self._styles` in `_build_elements()` i.p.v. `BM_STYLES`
- In `block_registry.py`: pas `create_paragraph()` aan zodat het een `styles` parameter accepteert (of geef de stylesheet mee via kwargs)

Dit is een wat invasievere wijziging. De eenvoudigste aanpak:
1. Voeg een optionele `styles` parameter toe aan `create_block()` in block_registry.py
2. Geef de stylesheet door van `Report._build_elements()` naar `create_block()`
3. `create_paragraph()` gebruikt de meegegeven stylesheet i.p.v. de globale

---

## Stap 5: Herschrijf `draw_colofon_page()` in special_pages.py

De huidige colofon is een generieke twee-kolom layout. De referentie heeft een specifiek patroon:
- Twee kolommen (labels links, waarden rechts) 
- Horizontale scheidingslijnen tussen veldgroepen
- Eerste twee labels (Project, In opdracht van) in paars, rest in turquoise
- Footer: turquoise blok linksonder + 3BM logo + paginanummer

De nieuwe implementatie moet de specs uit `brand.pages.colofon` lezen (met fallback naar defaults).

```python
def draw_colofon_page(canvas, doc, config, brand, colofon_data=None):
    """Teken colofon — configureerbaar via brand.pages.colofon."""
    canvas.saveState()
    
    pw = config.effective_width_pt
    ph = config.effective_height_pt
    spec = brand.pages.get("colofon", {})
    data = colofon_data or {}
    
    # Lees posities uit spec (met defaults)
    label_x = spec.get("label_x_pt", 103)
    value_x = spec.get("value_x_pt", 229)
    first_color = HexColor(spec.get("first_labels_color", "#401246"))
    other_color = HexColor(spec.get("other_labels_color", "#38BDAB"))
    value_color = HexColor(spec.get("value_color", "#401246"))
    line_x1 = spec.get("line_x1_pt", 102)
    line_x2 = spec.get("line_x2_pt", 420)
    line_stroke = spec.get("line_stroke_pt", 0.25)
    line_color = HexColor(spec.get("line_color", "#401146"))
    
    label_font = get_font_name(spec.get("label_font", "GothamBook"))
    label_size = spec.get("label_size", 10.0)
    value_font = get_font_name(spec.get("value_font", "GothamBook"))
    value_size = spec.get("value_size", 10.0)
    
    # Veld mapping: type → waarde
    field_values = {
        "project": config.project,
        "client": config.client,
        "author": config.author,
        "date": data.get("date", ""),
        "norms": data.get("norms", ""),
        "document_description": data.get("document_description", ""),
        "phase": data.get("phase", ""),
        "status": data.get("status", "CONCEPT"),
        "document_code": data.get("document_code", ""),
    }
    
    # Teken velden
    fields = spec.get("fields", _DEFAULT_COLOFON_FIELDS)
    y_cursor = 120  # startpositie (y in pt, top-down → converteer naar bottom-up)
    first_n_purple = 2  # eerste N labels in paars
    field_index = 0
    
    for field_def in fields:
        if field_def.get("type") == "line":
            # Scheidingslijn
            y_rl = ph - y_cursor
            canvas.setStrokeColor(line_color)
            canvas.setLineWidth(line_stroke)
            canvas.line(line_x1, y_rl, line_x2, y_rl)
            y_cursor += 20
        else:
            label = field_def.get("label", "")
            value_type = field_def.get("type", "")
            value = field_values.get(value_type, data.get(value_type, ""))
            
            y_rl = ph - y_cursor
            
            # Label kleur: eerste N in paars, rest turquoise
            color = first_color if field_index < first_n_purple else other_color
            canvas.setFont(label_font, label_size)
            canvas.setFillColor(color)
            canvas.drawString(label_x, y_rl, label)
            
            # Waarde
            canvas.setFont(value_font, value_size)
            canvas.setFillColor(value_color)
            canvas.drawString(value_x, y_rl, str(value))
            
            field_index += 1
            y_cursor += 22
    
    # Footer: turquoise blok + logo + paginanummer
    rect_spec = spec.get("footer_rect", [0, 771, 282, 842])
    rect_color = HexColor(spec.get("footer_rect_color", "#38BDAB"))
    # rect_spec = [x, y_bottom_topdown, width, y_top_topdown]
    # Converteer naar ReportLab bottom-up
    rx = rect_spec[0]
    ry_bottom = ph - rect_spec[3]  # y_top in top-down → y_bottom in bottom-up
    rw = rect_spec[2]
    rh = rect_spec[3] - rect_spec[1]
    canvas.setFillColor(rect_color)
    canvas.rect(rx, ry_bottom, rw, rh, fill=1, stroke=0)
    
    # Logo in/naast het turquoise blok
    logo_path = ASSETS_DIR / brand.logos.get("tagline", "logos/3bm-cooperatie-tagline.png")
    if logo_path.exists():
        _draw_logo(canvas, logo_path, rx + 10, ry_bottom + 5, height=rh - 10)
    
    # Paginanummer
    canvas.setFont(get_font_name("GothamBook"), 9.5)
    canvas.setFillColor(HexColor("#45243D"))
    page_num = canvas.getPageNumber()
    canvas.drawRightString(533, ry_bottom + 20, str(page_num))
    
    canvas.restoreState()
```

**Belangrijk:** De exacte y-posities en spacing moeten getuned worden door het resultaat visueel te vergelijken met de referentie-PDF. De bovenstaande code is een startpunt — gebruik `HUISSTIJL_SPEC.md` voor de exacte coördinaten.

---

## Stap 6: Voeg `draw_appendix_divider_page()` toe aan special_pages.py

Nieuwe functie gebaseerd op `HUISSTIJL_SPEC.md` sectie "Bijlage Divider":

```python
def draw_appendix_divider_page(
    canvas, doc, config, brand,
    appendix_number: int = 1,
    appendix_title: str = "",
):
    """Teken een bijlage-scheidingspagina.
    
    Layout:
    - Volledig turquoise achtergrond
    - Paars blok linksonder (zelfde als colofon footer)  
    - "Bijlage N" in GothamBold 41.4pt paars
    - Titel in GothamBook 41.4pt wit (kan meerdere regels zijn)
    - Tagline "Projecten die inspireren" rechtsonder in paars
    """
    canvas.saveState()
    
    pw = config.effective_width_pt
    ph = config.effective_height_pt
    spec = brand.pages.get("appendix_divider", {})
    
    # Turquoise achtergrond
    bg_color = HexColor(spec.get("bg_color", "#37BCAB"))
    canvas.setFillColor(bg_color)
    canvas.rect(0, 0, pw, ph, fill=1, stroke=0)
    
    # Paars blok linksonder
    purple_rect = spec.get("purple_rect", [0, 771, 282, 842])
    purple_color = HexColor(spec.get("purple_color", "#401246"))
    prx = purple_rect[0]
    pry = ph - purple_rect[3]
    prw = purple_rect[2]
    prh = purple_rect[3] - purple_rect[1]
    canvas.setFillColor(purple_color)
    canvas.rect(prx, pry, prw, prh, fill=1, stroke=0)
    
    # Bijlage nummer
    num_font = get_font_name(spec.get("number_font", "GothamBold"))
    num_size = spec.get("number_size", 41.4)
    num_color = HexColor(spec.get("number_color", "#401246"))
    num_x = spec.get("number_x_pt", 103)
    num_y = ph - spec.get("number_y_pt", 193.9)  # top-down → bottom-up
    
    canvas.setFont(num_font, num_size)
    canvas.setFillColor(num_color)
    canvas.drawString(num_x, num_y, f"Bijlage {appendix_number}")
    
    # Titel (kan meerdere regels zijn, split op \n)
    title_font = get_font_name(spec.get("title_font", "GothamBook"))
    title_size = spec.get("title_size", 41.4)
    title_color = HexColor(spec.get("title_color", "#FFFFFF"))
    title_x = spec.get("title_x_pt", 136.1)
    title_y_start = num_y - title_size * 1.3
    
    canvas.setFont(title_font, title_size)
    canvas.setFillColor(title_color)
    for i, line in enumerate(appendix_title.split("\n")):
        canvas.drawString(title_x, title_y_start - i * title_size * 1.2, line.strip())
    
    # Tagline
    tagline = spec.get("tagline", "Projecten die inspireren")
    tag_font = get_font_name(spec.get("tagline_font", "GothamBold"))
    tag_size = spec.get("tagline_size", 17.9)
    tag_color = HexColor(spec.get("tagline_color", "#401246"))
    tag_x = spec.get("tagline_x_pt", 330.5)
    tag_y = ph - spec.get("tagline_y_pt", 785.1)
    
    canvas.setFont(tag_font, tag_size)
    canvas.setFillColor(tag_color)
    canvas.drawString(tag_x, tag_y, tagline)
    
    canvas.restoreState()
```

---

## Stap 7: Registreer appendix_divider in page_templates.py

Voeg een nieuw PageTemplate toe voor de bijlage-divider:

In `create_page_templates()`:

```python
# Bijlage divider template (herbruikbaar via engine)
appendix_frame = Frame(ml, mb, page_w - ml - mr, page_h - mt - mb, id="appendix_frame")
# Default: bijlage 1 zonder titel. Wordt override per gebruik.
appendix_template = PageTemplate(
    id="appendix_divider",
    frames=[appendix_frame],
    onPage=lambda canvas, doc: draw_appendix_divider_page(
        canvas, doc, config, brand
    ),
)
```

Voeg `draw_appendix_divider_page` toe aan de import.

Return de template in de lijst: `[cover, colofon, content, appendix_divider, backcover]`.

---

## Stap 8: Voeg `add_appendix()` toe aan `engine.py`

```python
def add_appendix(
    self,
    title: str,
    number: int | None = None,
    content: list[Any] | None = None,
) -> Report:
    """Voeg een bijlage toe met scheidingspagina.
    
    Args:
        title: Bijlage titel (getoond op divider).
        number: Bijlage nummer (auto-increment als None).
        content: Optionele content na de divider.
    """
    if number is None:
        number = self._next_appendix_number()
    
    self._appendices.append({
        "title": title,
        "number": number,
        "content": content or [],
    })
    return self
```

In `_build_elements()`, na de secties en vóór de backcover:

```python
# Bijlagen
for appendix in self._appendices:
    # Wissel naar appendix divider template
    elements.append(NextPageTemplate("appendix_divider"))
    elements.append(PageBreak())
    # De divider page template tekent de turquoise achtergrond
    elements.append(Spacer(1, 1))
    
    # Wissel terug naar content voor eventuele bijlage-inhoud
    if appendix["content"]:
        elements.append(NextPageTemplate("content"))
        elements.append(PageBreak())
        for item in appendix["content"]:
            if isinstance(item, str):
                elements.append(Paragraph(item, styles["Normal"]))
            else:
                elements.append(item)
```

**Let op:** De appendix divider template moet dynamisch de titel en nummer meekrijgen. Dit vereist een closure of state op de Report class. Mogelijke aanpak:

```python
# In page_templates.py — maak een factory functie
def _make_appendix_callback(config, brand, number, title):
    def callback(canvas, doc):
        draw_appendix_divider_page(canvas, doc, config, brand, number, title)
    return callback
```

En in `_build_elements()` registreer je een nieuw PageTemplate per bijlage met de juiste callback. Of gebruik een simpeler patroon: sla de huidige bijlage-info op de Report class op en lees die in de callback.

---

## Stap 9: Test het resultaat

Genereer het voorbeeld rapport opnieuw met de gecorrigeerde brand:

```python
# Test script: huisstijl/generate_example.py
import sys
sys.path.insert(0, "src")

from pathlib import Path
from bm_reports.core.engine import Report

json_path = Path("huisstijl/voorbeeld_rapport.json")
output_path = Path("huisstijl/voorbeeld_rapport_v2.pdf")

report = Report.from_json(json_path, brand="3bm_cooperatie")
result = report.build(output_path)
print(f"OK: {result} ({result.stat().st_size / 1024:.0f} KB)")
```

**Visuele check:** Open de gegenereerde PDF en vergelijk met de referentie (`huisstijl/2707_BBLrapportage_v01.pdf`):

- [ ] Content pagina's: ALLEEN paginanummer rechtsonder, GEEN turquoise blok
- [ ] H1: GothamBook (niet Bold) 18pt, kleur #45243D
- [ ] H2: GothamBook 13pt, kleur #56B49B (licht turquoise)
- [ ] Body: 9.5pt (niet 9.0pt)
- [ ] Colofon: twee-kolom layout met scheidingslijnen, turquoise blok alleen op colofon
- [ ] TOC: (als er een custom TOC renderer is) turquoise chapter titels

---

## Stap 10: Update tests

### `tests/test_brand.py`

Voeg tests toe voor de nieuwe BrandConfig velden:

```python
def test_brand_config_styles():
    config = BrandConfig(styles={"Normal": {"fontSize": 9.5}})
    assert config.styles["Normal"]["fontSize"] == 9.5

def test_brand_config_pages():
    config = BrandConfig(pages={"colofon": {"label_x_pt": 103}})
    assert config.pages["colofon"]["label_x_pt"] == 103

def test_load_3bm_styles():
    loader = BrandLoader()
    brand = loader.load("3bm_cooperatie")
    assert "Normal" in brand.styles
    assert brand.styles["Heading1"]["fontName"] == "GothamBook"

def test_load_3bm_footer_corrected():
    loader = BrandLoader()
    brand = loader.load("3bm_cooperatie")
    assert brand.footer.height == 17  # was 25
    assert len(brand.footer.elements) == 1  # alleen paginanummer
    assert brand.footer.elements[0].content == "{page}"
```

### `tests/test_styles.py` (nieuw)

```python
def test_create_stylesheet_default():
    styles = create_stylesheet()
    assert "Normal" in styles
    assert styles["Normal"].fontSize == 9.0  # default zonder brand

def test_create_stylesheet_with_brand():
    brand = BrandConfig(styles={
        "Normal": {"fontSize": 9.5, "textColor": "#45243D"},
        "Heading1": {"fontName": "GothamBook", "fontSize": 18.0},
    })
    styles = create_stylesheet(brand=brand)
    assert styles["Normal"].fontSize == 9.5
    assert styles["Heading1"].fontSize == 18.0
```

### `tests/test_special_pages.py`

Update bestaande tests voor de nieuwe colofon layout en voeg tests toe voor de appendix divider.

---

## Samenvatting wijzigingen

| Bestand | Wijziging |
|---------|-----------|
| `src/bm_reports/core/brand.py` | +`styles` en `pages` velden op BrandConfig + parsing in BrandLoader |
| `src/bm_reports/assets/brands/3bm_cooperatie.yaml` | Volledig herschreven: footer, styles, pages, colors correctie |
| `src/bm_reports/core/styles.py` | `create_stylesheet(brand=None)` met override logica |
| `src/bm_reports/core/special_pages.py` | Colofon herschreven + nieuwe `draw_appendix_divider_page()` |
| `src/bm_reports/core/page_templates.py` | +appendix_divider template |
| `src/bm_reports/core/engine.py` | +`add_appendix()`, brand-aware stylesheet, appendix in elements |
| `src/bm_reports/core/block_registry.py` | `create_block()` accepteert optionele `styles` parameter |
| `tests/test_brand.py` | +tests voor styles/pages velden |
| `tests/test_styles.py` | Nieuw: stylesheet override tests |
| `tests/test_special_pages.py` | Update colofon + appendix divider tests |

## Niet wijzigen

- `src/bm_reports/core/brand_renderer.py` — werkt al correct generiek
- `src/bm_reports/tools/*` — Fase A is compleet
- `src/bm_reports/core/document.py` — geen wijzigingen nodig
- Cover en backcover in `special_pages.py` — deze zijn al correct

## Prioriteit

Als je tijd tekort komt, focus dan op deze volgorde:
1. **Footer correctie** (meest zichtbare fout)
2. **Style overrides** (H1/H2/body sizes en fonts)
3. **Colofon herschrijven**
4. **Appendix divider** (nice to have)
