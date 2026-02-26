# Pagina-architectuur — 3BM Rapport Generator

## Universeel principe

Elke pagina bestaat uit **drie lagen**, altijd in deze volgorde:

```
┌─────────────────────────────────────────┐
│  Laag 3: Modules / tekst               │  ← Dynamische content
│  Laag 2: Kop- en voettekst             │  ← Semi-statisch (logo + paginanr)
│  Laag 1: Achtergrondafbeelding         │  ← Statisch per paginatype
└─────────────────────────────────────────┘
```

**Laag 1** = stationery PDF/PNG — alle gekleurde vlakken, geometrie, decoratie.
**Laag 2** = kop/voettekst — logo, paginanummer, eventueel projectnaam. Wordt OVER de achtergrond getekend.
**Laag 3** = dynamische content — tekst, tabellen, afbeeldingen, berekeningen. Per paginatype anders.

Alle teksten in ALLE lagen krijgen het juiste **font, grootte en kleur** uit de brand config.
Alle modules krijgen de juiste **padding, marges, kleuren** uit de brand config.

---

## Paginatypes

### 1. Voorpagina (Cover)

```
┌─────────────────────────────────────┐
│  ACHTERGROND                        │  Laag 1: Stationery PDF
│  ├─ Paars vlak (bovenste ~74%)      │         (alle statische geometrie)
│  ├─ Witte geometrische vormen       │
│  └─ (eventueel decoratieve lijnen)  │
│                                     │
│  VOORGROND ELEMENTEN                │  Laag 3: Dynamisch
│  ├─ Logo (wit, linksboven)          │         positie uit brand config
│  ├─ "Ontdek ons 3bm.co.nl"         │         (statische tekst, brand-specifiek)
│  ├─ Projectfoto (met clip-path)     │         AANPASBAAR door gebruiker
│  ├─ Badges (MEEDENKEN etc.)        │         (statisch per brand)
│  ├─ Rapporttitel                    │         AANPASBAAR door gebruiker
│  └─ Ondertitel                      │         AANPASBAAR door gebruiker
│                                     │
│  GEEN kop/voettekst                 │  Laag 2: n.v.t.
└─────────────────────────────────────┘
```

**Aanpasbare elementen:**
- Rapporttitel (tekst, font/grootte/kleur uit brand)
- Ondertitel (tekst, font/grootte/kleur uit brand)
- Projectfoto (afbeelding, clip-path uit brand)

**Statische elementen (uit stationery + brand config):**
- Achtergrond geometrie
- Logo positie + bestand
- Website tekst
- Badges (tekst, kleuren, posities)

---

### 2. Colofon

```
┌─────────────────────────────────────┐
│  ACHTERGROND                        │  Laag 1: Stationery PDF
│  └─ (leeg wit, of subtiele          │
│      decoratie als die er is)       │
│                                     │
│  KOP- EN VOETTEKST                  │  Laag 2:
│  ├─ Voettekst: turquoise blok      │    Logo in turquoise blok
│  ├─          + 3BM logo             │    Paginanummer rechtsonder
│  └─ Paginanummer rechtsonder        │
│                                     │
│  TEKST MODULES                      │  Laag 3: Dynamisch
│  ├─ Rapport type titel              │    font/grootte/kleur uit brand
│  ├─ Project subtitel                │    
│  ├─ Label-waarde tabel:             │    Twee-kolom layout
│  │   ├─ Project          waarde     │    Labels: font/kleur per groep
│  │   ├─ In opdracht van  waarde     │    Waarden: font/kleur
│  │   ├─ ── scheidslijn ────────     │    Lijnkleur uit brand
│  │   ├─ Adviseur         waarde     │    
│  │   ├─ Normen           waarde     │    
│  │   └─ ... etc                     │    
│  └─ (optioneel: revisietabel)       │
└─────────────────────────────────────┘
```

**Aanpasbare elementen:**
- Rapport type titel
- Subtitel
- Alle label-waarde paren (projectinfo, metadata)
- Revisiehistorie

**Kop/voettekst:**
- Turquoise blok + logo (specifiek voor colofon — NIET op content pagina's)
- Paginanummer

---

### 3. Inhoudsopgave (TOC)

```
┌─────────────────────────────────────┐
│  ACHTERGROND                        │  Laag 1: Stationery PDF
│  └─ (decoratief element /           │    (als er een watermark of
│      watermerk als die er is)       │     decoratie is, anders blanco)
│                                     │
│  KOP- EN VOETTEKST                  │  Laag 2:
│  └─ Paginanummer rechtsonder        │    Alleen paginanummer
│     (GEEN turquoise blok/logo)      │    Font/grootte/kleur uit brand
│                                     │
│  TOC MODULE                         │  Laag 3: Dynamisch
│  ├─ Titel "Inhoud"                  │    font/grootte/kleur uit brand
│  ├─ Hoofdstukken (level 1):         │    nummer | titel | pagina
│  │   font/grootte/kleur per level   │    
│  └─ Sub-items (level 2):            │    
│      font/grootte/kleur per level   │    
└─────────────────────────────────────┘
```

**Kop/voettekst:**
- ALLEEN paginanummer (zelfde als content pagina's)
- GEEN turquoise blok, GEEN logo

---

### 4. Gewone pagina (Content)

```
┌─────────────────────────────────────┐
│  ACHTERGROND                        │  Laag 1: Stationery PDF
│  └─ (briefpapier achtergrond        │    Kan blanco zijn als er geen
│      als die er is, anders blanco)  │    header/footer decoratie is
│                                     │
│  KOP- EN VOETTEKST                  │  Laag 2:
│  ├─ Koptekst: (geen bij 3BM)       │    Brand-specifiek
│  └─ Voettekst: paginanummer        │    Font/grootte/kleur uit brand
│     rechtsonder                     │    
│                                     │
│  CONTENT FRAME                      │  Laag 3: Dynamisch
│  (marges uit brand config)          │    Alle modules binnen dit frame
│  ├─ Heading 1 (sectietitel)         │    font/grootte/kleur uit brand
│  ├─ Heading 2 (subsectie)          │    font/grootte/kleur uit brand
│  ├─ Paragraaf tekst                 │    font/grootte/kleur uit brand
│  ├─ Bullet points                   │    
│  ├─ Tabel module                    │    header bg/tekst, body, footer
│  │   ├─ padding per cel             │    uit brand config
│  │   ├─ header achtergrondkleur     │    
│  │   └─ footer achtergrondkleur     │    
│  ├─ Berekening module               │    formule/substitutie/resultaat
│  │   └─ padding, kleuren, fonts     │    uit brand config
│  ├─ Toets (unity check) module      │    VOLDOET/VOLDOET NIET kleuren
│  │   └─ padding, kleuren, fonts     │    uit brand config
│  ├─ Afbeelding module               │    caption font/kleur
│  ├─ Kaart module (PDOK)             │    caption font/kleur
│  └─ Witruimte / pagina-einde        │    
└─────────────────────────────────────┘
```

**Module styling (ALLEMAAL uit brand config):**

| Module | Wat moet kloppen |
|--------|-----------------|
| Heading 1 | font, grootte, kleur, spacing boven/onder |
| Heading 2 | font, grootte, kleur, spacing boven/onder |
| Heading 3 | font, grootte, kleur, spacing boven/onder |
| Paragraaf | font, grootte, kleur, leading, inspringing |
| Bullet points | bullet karakter, inspringing, font/kleur |
| Tabel | header bg + tekst kleur, body font/kleur, footer bg, cel padding, lijnkleur |
| Berekening | titel font, formule font, resultaat font, accent lijn kleur, achtergrond |
| Toets | beschrijving font, VOLDOET kleur (groen), VOLDOET NIET kleur (rood), kader |
| Afbeelding | caption font/grootte/kleur |
| Kaart | caption font/grootte/kleur, kader |

---

### 5. Bijlage-scheidingspagina (Appendix Divider)

```
┌─────────────────────────────────────┐
│  ACHTERGROND                        │  Laag 1: Stationery PDF
│  ├─ Turquoise volledige pagina      │    (alle geometrie)
│  ├─ Paurs blok linksonder           │    
│  └─ "Projecten die inspireren"      │    (statische tekst in stationery)
│                                     │
│  GEEN kop/voettekst                 │  Laag 2: n.v.t.
│                                     │
│  TEKST MODULES                      │  Laag 3: Dynamisch
│  ├─ "Bijlage N" (nummer)            │    font/grootte/kleur uit brand
│  └─ Bijlagetitel (1-2 regels)       │    font/grootte/kleur uit brand
└─────────────────────────────────────┘
```

---

### 6. Achterblad (Backcover)

```
┌─────────────────────────────────────┐
│  ACHTERGROND                        │  Laag 1: Stationery PDF
│  ├─ Turquoise achtergrond           │    Alle complexe geometrie
│  ├─ Wit polygon met schuine lijnen  │    (onmogelijk programmatisch)
│  ├─ Paurs driehoekig vlak           │    
│  └─ (alle decoratieve vormen)       │    
│                                     │
│  GEEN kop/voettekst                 │  Laag 2: n.v.t.
│                                     │
│  TEKST MODULES                      │  Laag 3: 
│  ├─ 3BM logo (groot, midden)        │    Statisch per brand
│  ├─ Bedrijfsnaam                     │    AANPASBAAR (uit brand config)
│  ├─ Adresgegevens                    │    AANPASBAAR (uit brand config)
│  └─ "Ontdek ons 3bm.co.nl"          │    Statisch per brand
└─────────────────────────────────────┘
```

**Opmerking:** Bij 3BM is het achterblad grotendeels statisch, maar de contactgegevens 
en bedrijfsnaam MOETEN aanpasbaar zijn (andere bureaus binnen de coöperatie kunnen 
andere adressen hebben).

---

## Brand Config: wat moet er per brand gedefinieerd worden

### Kleuren (uit stamkaart)
```yaml
colors:
  primary: "#401246"        # Hoofdkleur (paars)
  secondary: "#38BDAB"      # Accent (turquoise)
  text: "#45243D"           # Body tekst
  text_accent: "#56B49B"    # H2 headings, TOC level 1
  accent_green: "#2ECC71"   # VOLDOET (toets module)
  accent_red: "#E74C3C"     # VOLDOET NIET (toets module)
  table_header_bg: "#45233C"   # Tabel header achtergrond
  table_header_text: "#FFFFFF" # Tabel header tekst
  table_footer_bg: "#55B49B"   # Tabel footer/totaal rij
  separator: "#E0D0E8"        # Scheidingslijnen
  background_alt: "#F8F9FA"   # Afwisselende rij achtergrond
```

### Fonts (uit stamkaart + referentie-rapport)
```yaml
fonts:
  heading: "GothamBold"
  body: "GothamBook"
  medium: "GothamMedium"
  italic: "GothamBookItalic"
  mono: "Courier"
  
  # Font bestanden (relatief t.o.v. brand directory)
  files:
    GothamBold: "fonts/Gotham-Bold.ttf"
    GothamBook: "fonts/Gotham-Book.ttf"
    GothamMedium: "fonts/Gotham-Medium.ttf"
    GothamBookItalic: "fonts/Gotham-BookItalic.ttf"
```

### Styles (uit referentie-rapport — per tekststijl)
```yaml
styles:
  Normal:
    fontName: "GothamBook"
    fontSize: 9.5
    leading: 12.0
    textColor: "$colors.text"
    spaceAfter: 4
  Heading1:
    fontName: "GothamBook"     # LET OP: NIET Bold!
    fontSize: 18.0
    leading: 23.4
    textColor: "$colors.text"
    spaceBefore: 12
    spaceAfter: 6
  Heading2:
    fontName: "GothamBook"
    fontSize: 13.0
    leading: 16.9
    textColor: "$colors.text_accent"
    spaceBefore: 10
    spaceAfter: 4
  Heading3:
    fontName: "GothamBook"
    fontSize: 11.0
    leading: 14.3
    textColor: "$colors.text_accent"
    spaceBefore: 8
    spaceAfter: 3
  Caption:
    fontName: "GothamBook"
    fontSize: 8.0
    textColor: "$colors.text"
  BulletItem:
    fontName: "GothamBook"
    fontSize: 9.5
    leading: 12.0
    textColor: "$colors.text"
    bulletIndent: 0
    leftIndent: 18
```

### Module styling
```yaml
modules:
  table:
    header_bg: "$colors.table_header_bg"
    header_font: "GothamBook"
    header_size: 12.0
    header_text_color: "#FFFFFF"
    body_font: "GothamBook"
    body_size: 9.0
    body_text_color: "$colors.text"
    footer_bg: "$colors.table_footer_bg"
    cell_padding: [4, 6, 4, 6]   # top, right, bottom, left (pt)
    grid_color: "$colors.separator"
    grid_width: 0.5
    alt_row_bg: "$colors.background_alt"
    
  calculation:
    title_font: "$fonts.heading"
    title_size: 10.0
    title_color: "$colors.primary"
    formula_font: "$fonts.body"
    formula_size: 9.5
    result_font: "$fonts.heading"
    result_color: "$colors.primary"
    accent_line_color: "$colors.secondary"
    accent_line_width: 2.5
    background: "$colors.background_alt"
    padding: [8, 10, 8, 10]
    
  check:
    description_font: "$fonts.body"
    pass_color: "$colors.accent_green"
    fail_color: "$colors.accent_red"
    border_color: "$colors.separator"
    border_width: 0.5
    padding: [6, 8, 6, 8]

  image:
    caption_font: "$fonts.body"
    caption_size: 8.0
    caption_color: "$colors.text"
    
  map:
    caption_font: "$fonts.body"
    caption_size: 8.0
    caption_color: "$colors.text"
    border_color: "$colors.separator"
```

### Stationery (achtergrondafbeeldingen per paginatype)
```yaml
stationery:
  cover:
    source: "stationery/cover.pdf"
    text_zones:
      - role: title
        x_pt: 54.28
        y_pt: 93.47
        font: "$fonts.heading"
        size: 28.9
        color: "$colors.primary"
        max_width_pt: 490
      - role: subtitle
        x_pt: 55.0
        y_pt: 63.0
        font: "$fonts.body"
        size: 17.8
        color: "$colors.secondary"
      - role: hero_image
        type: clipped_image
        image_rect: [55.6, 161.6, 484.0, 560.8]
        clip_polygon: [[350.8, 159.8], ...]
  
  colofon:
    source: "stationery/colofon.pdf"
    header_footer: "colofon"    # Specifieke kop/voettekst variant
    text_zones: [...]
  
  content:
    source: "stationery/content.pdf"  # Kan null/blanco zijn
    header_footer: "content"
    content_frame:
      x_pt: 90.0
      y_pt: 48.0
      width_pt: 451.6
      height_pt: 746.0
  
  toc:
    source: "stationery/toc.pdf"
    header_footer: "content"    # Zelfde als content pagina's
    text_zones: [...]
  
  appendix_divider:
    source: "stationery/appendix_divider.pdf"
    header_footer: null         # GEEN kop/voettekst
    text_zones:
      - role: number
        x_pt: 103.0
        y_pt: 193.9
        font: "$fonts.heading"
        size: 41.4
        color: "$colors.primary"
      - role: title
        x_pt: 136.1
        y_pt: 262.2
        font: "$fonts.body"
        size: 41.4
        color: "#FFFFFF"
        line_spacing_pt: 66.4
  
  backcover:
    source: "stationery/backcover.pdf"
    header_footer: null         # GEEN kop/voettekst
    text_zones:
      - role: company_name
        x_pt: 268
        y_pt: 185
        font: "$fonts.heading"
        size: 11.0
        color: "$colors.primary"
        bind: "contact.name"
      - role: address
        x_pt: 268
        y_pt: 165
        font: "$fonts.body"
        size: 9.0
        color: "$colors.text"
        bind: "contact.address"
```

### Kop- en voettekst varianten
```yaml
header_footer:
  content:
    header:
      height_mm: 0              # Geen header bij 3BM
    footer:
      height_mm: 17
      elements:
        - type: page_number
          x_pt: 541.6
          y_pt: 35.7
          font: "$fonts.body"
          size: 9.5
          color: "$colors.text"
          align: right
  
  colofon:
    header:
      height_mm: 0
    footer:
      height_mm: 25
      elements:
        - type: rect
          x_pt: 0
          y_pt: 0
          width_pt: 282
          height_pt: 71
          fill: "$colors.secondary"
        - type: image
          source: "$logos.tagline"
          x_pt: 10
          y_pt: 5
          height_pt: 61
        - type: page_number
          x_pt: 534
          y_pt: 45.6
          font: "$fonts.body"
          size: 9.5
          color: "$colors.secondary"
          align: right
```

---

## Samenvatting: rendering pipeline per pagina

```python
def render_page(canvas, page_type, brand, config, content=None):
    """Universele pagina renderer."""
    
    stationery = brand.stationery.get(page_type)
    
    # LAAG 1: Achtergrondafbeelding
    if stationery and stationery.source:
        draw_stationery_background(canvas, stationery.source)
    
    # LAAG 2: Kop- en voettekst
    hf_variant = stationery.header_footer if stationery else None
    if hf_variant:
        hf_config = brand.header_footer[hf_variant]
        draw_header(canvas, hf_config.header, brand, config)
        draw_footer(canvas, hf_config.footer, brand, config)
    
    # LAAG 3: Dynamische content
    if stationery and stationery.text_zones:
        for zone in stationery.text_zones:
            draw_text_zone(canvas, zone, brand, config)
    
    if content:  # ReportLab flowables (voor content pagina's)
        # Worden getekend in het content_frame door ReportLab's platypus
        pass
```
