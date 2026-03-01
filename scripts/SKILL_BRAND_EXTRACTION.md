# SKILL: Brand Extractie uit Huisstijl PDF

## Doel
Extraheer een pixel-precieze brand.yaml uit een huisstijl-referentie PDF voor het bm-reports systeem.

## Workflow

### Stap 1: Draai het extractie-script
```bash
python scripts/brand_extractor.py <pdf_path> --render-pages output/_brand_analysis --dpi 200
```

Dit produceert:
- Een JSON bestand met alle visuele elementen per pagina
- PNG renders van elke pagina in `output/_brand_analysis/`

### Stap 2: Lees de JSON output
De JSON bevat per pagina:
- **texts**: elk tekst-span met font, size, color (hex), bbox (x0/y0/x1/y1 in pt)
- **rects**: rechthoeken/lijnen met fill/stroke, corner_radius
- **paths**: polygonen en beziers met alle punten
- **images**: positie en afmetingen
- **fonts_summary**: overzicht van alle font-stijl combinaties met sample teksten
- **colors_summary**: alle gebruikte kleuren met context

### Stap 3: Bekijk de PNG renders
Gebruik de page renders om visueel te verifiëren wat elk element is. De JSON geeft de data, de afbeelding geeft de context.

### Stap 4: Classificeer pagina's
Identificeer welke pagina welk type is:
- **cover** (voorblad): grote foto, badges, titel, logo
- **colofon**: projectgegevens, label-value paren, scheidingslijnen
- **toc** (inhoudsopgave): "Inhoud" titel, genummerde items
- **content** (standaard): header/footer zone, tekst content area
- **appendix_divider** (bijlage-scheidingspagina): gekleurde achtergrond, bijlagenummer
- **backcover** (achterblad): logo, contactgegevens, decoratieve vormen

### Stap 5: Genereer brand.yaml

Gebruik het volgende schema. **Alle coördinaten in pt (punten). Alle kleuren als hex.**

```yaml
brand:
  name: "<Bedrijfsnaam>"
  slug: "<slug>"  # lowercase, hyphens

colors:
  # Haal uit colors_summary — match met visuele context
  primary: "#..."        # Hoofdkleur (meest prominent in headers, grote vlakken)
  secondary: "#..."      # Accentkleur (tweede prominente kleur)
  text: "#..."           # Body tekst kleur
  text_accent: "#..."    # Heading 2/3 kleur (vaak = secondary)
  accent: "#..."         # Positief/groen accent
  warning: "#..."        # Negatief/rood accent
  text_light: "#..."     # Subtekst, captions
  table_header_bg: "#..."
  table_header_text: "#FFFFFF"  # Meestal wit
  table_footer_bg: "#..."
  separator: "#..."      # Scheidingslijnen kleur

fonts:
  # Haal uit fonts_summary — match font names
  heading: "<FontBold>"       # Bold variant
  body: "<FontRegular>"       # Regular/Book variant
  medium: "<FontMedium>"      # Medium variant (optioneel)
  italic: "<FontItalic>"      # Italic variant (optioneel)

logos:
  main: "logos/<slug>.png"
  tagline: "logos/<slug>-tagline.png"     # Indien aanwezig
  white: "logos/<slug>-wit.png"           # Wit/negatief versie

contact:
  name: "<Bedrijfsnaam>"
  address: "<adres | postcode | telefoon>"
  website: "<website>"

# === HEADER/FOOTER (content pagina's) ===
header:
  height: <hoogte in pt, 0 als geen header>
  elements: []  # Indien header elementen aanwezig

footer:
  height: <hoogte in pt>
  elements:
    - type: text
      content: "{page}"
      x: <x_pt>
      y: <y_pt>
      font: "$body"
      size: <size>
      color: "$text"
      align: right

# === TEKSTSTIJLEN ===
# Haal uit fonts_summary — groepeer op semantische rol
styles:
  Normal:
    fontName: "<body font>"
    fontSize: <meest voorkomende body size>
    leading: <fontSize * 1.26>
    textColor: "<text color>"
  Heading1:
    fontName: "<heading of body font>"  # Check of H1 bold is!
    fontSize: <groot, ~18pt>
    leading: <fontSize * 1.3>
    textColor: "<text color>"
  Heading2:
    fontName: "<font>"
    fontSize: <~13pt>
    leading: <fontSize * 1.3>
    textColor: "<text_accent color>"
  Heading3:
    fontName: "<font>"
    fontSize: <~11pt>
    leading: <fontSize * 1.3>
    textColor: "<text_accent color>"

# === PAGINA CONFIGURATIES ===
pages:
  cover:
    # Gebruik bbox data van de cover pagina
    # Paars/gekleurd vlak
    purple_rect_y_ref: <y van het grote gekleurde vlak>
    purple_rect_h_ref: <hoogte>

    # Clip-path polygon (voor foto masking)
    clip_polygon:
      - [<x>, <y>]  # Alle punten uit het grootste path op de cover
      # ... meer punten

    photo_rect: [<x>, <y>, <width>, <height>]  # Positie van de hoofdfoto

    # Logo
    logo_key: "white"  # of "main"
    logo_x_ref: <x>
    logo_y_ref: <y>
    logo_w_ref: <width>

    # Badges (rounded rects met tekst)
    badges:
      - label: "<tekst>"
        bg_color: "<fill kleur>"
        text_color: "<tekst kleur>"
        x_ref: <x>
        y_ref: <y>
        w_ref: <width>
        h_ref: <height>
    badge_radius_ref: <corner_radius>
    badge_font_size_ref: <font size>

    # Titel en subtitel
    title_size_ref: <size van grootste tekst>
    title_x_ref: <x>
    title_y_ref: <y>
    subtitle_size_ref: <size>
    subtitle_x_ref: <x>
    subtitle_y_ref: <y>

  colofon:
    # Header zone
    report_type_font: "<font>"
    report_type_size: <size>
    report_type_color: "<color>"
    report_type_x_pt: <x>
    report_type_y_pt: <y>

    subtitle_font: "<font>"
    subtitle_size: <size>
    subtitle_color: "<color>"
    subtitle_x_pt: <x>
    subtitle_y_pt: <y>

    # Label-value layout
    label_x_pt: <x van labels>
    value_x_pt: <x van waarden>
    label_font: "<font>"
    label_size: <size>
    value_font: "<font>"
    value_size: <size>

    # Scheidingslijnen
    line_x1_pt: <start x>
    line_x2_pt: <eind x>
    line_stroke_pt: <lijndikte>
    line_color: "<color>"

    # Velden met y_pt posities — haal uit de tekst bboxen
    fields:
      - {label: "<label>", type: "<type>", y_pt: <y>}
      # ... meer velden

  toc:
    title: "<titel tekst>"
    title_font: "<font>"
    title_size: <size>
    title_color: "<color>"
    title_x_pt: <x>
    title_y_pt: <y>

    # Level styling
    level1_font: "<font>"
    level1_size: <size>
    level1_color: "<color>"
    level2_font: "<font>"
    level2_size: <size>
    level2_color: "<color>"

    # Kolom posities
    number_x_pt: <x>
    text_x_pt: <x>
    page_x_pt: <x>

    # Spacing (bereken uit verschil in y-posities van opeenvolgende items)
    chapter_spacing_pt: <verschil y tussen hoofdstukken>
    item_spacing_pt: <verschil y tussen sub-items>

  appendix_divider:
    bg_color: "<achtergrond kleur>"
    purple_rect: [<x>, <y>, <x2>, <y2>]
    purple_color: "<kleur>"

    number_font: "<font>"
    number_size: <size>
    number_color: "<color>"
    number_x_pt: <x>
    number_y_pt: <y>

    title_font: "<font>"
    title_size: <size>
    title_color: "<color>"
    title_x_pt: <x>
    title_first_y_pt: <y van eerste regel>
    title_line_spacing_pt: <verschil y tussen regels>

  backcover:
    # Decoratieve polygonen
    white_polygon:
      - [<x>, <y>]  # Alle punten
    purple_triangle:
      - [<x>, <y>]

    # Logo
    logo_key: "main"
    logo_x_ref: <x>
    logo_y_ref: <y>
    logo_w_ref: <width>

    # Contactgegevens
    contact_x_ref: <x>
    contact_y_ref: <y>

# === STATIONERY ===
stationery:
  cover:
    source: ""  # Wordt later gevuld met pad naar stationery PDF
  colofon:
    source: ""
    header_footer: "colofon"
  content:
    source: ""
    header_footer: "content"
    content_frame:
      x_pt: <linker marge van tekst area>
      y_pt: <onder marge>
      width_pt: <breedte tekst area>
      height_pt: <hoogte tekst area>
  toc:
    source: ""
    header_footer: "content"
  appendix_divider:
    source: ""
  backcover:
    source: ""

# === MODULE STYLING ===
modules:
  table:
    header_bg: "$colors.table_header_bg"
    header_text_color: "#FFFFFF"
    body_font: "<body font>"
    body_size: <size>
    footer_bg: "$colors.table_footer_bg"
    grid_color: "$colors.separator"
  calculation:
    title_color: "$colors.primary"
    accent_line_color: "$colors.secondary"
  check:
    pass_color: "$colors.accent"
    fail_color: "$colors.warning"
```

## Belangrijke regels

### Coördinaten
- De extractor levert coördinaten in **PDF-native formaat** (origin linksonder, y omhoog)
- De brand.yaml gebruikt **top-down referentie** voor `y_pt` velden (origin linksboven)
- Conversie: `y_topdown = page_height_pt - y_pdf`
- Let op: text bbox `y0` in de JSON is al top-down (PyMuPDF text dict is top-down)
- Rects en paths zijn PDF-native — die moeten geconverteerd worden

### Kleuren
- Gebruik **exact** de hex waarden uit de extractie, rond niet af
- Match kleuren met hun semantische rol door context te bekijken (waar worden ze gebruikt)

### Fonts
- Gebruik de **exacte font naam** uit de extractie (bijv. "GothamHTF-Bold" niet "Gotham Bold")
- Check of de font bestanden beschikbaar zijn in `tenants/<slug>/fonts/`
- Definieer korte aliassen in de fonts sectie die matchen met de bestandsnamen

### Content frame
- Het content frame bepaalt waar tekst geplaatst mag worden op standaard pagina's
- Meet dit door de buitenste tekst-bboxen op een content pagina te vinden
- `x_pt` = kleinste x0 van body tekst
- `width_pt` = grootste x1 - kleinste x0
- `y_pt` = ruimte onder de tekst (footer zone)
- `height_pt` = beschikbare hoogte tussen header en footer

### Validatie
- Vergelijk de gegenereerde YAML visueel met de PNG renders
- Genereer een test-rapport en leg het naast het origineel
- Check specifiek: titel posities, badge posities, colofon layout, footer paginanummer

## Referentie
- Bestaande brand.yaml: `tenants/3bm_cooperatie/brand.yaml`
- Report schema: `schemas/report.schema.json`
- Renderer code: `src/bm_reports/core/`
