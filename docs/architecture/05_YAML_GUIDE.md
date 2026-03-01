# YAML Configuratie Guide

## Hiërarchie

```
brand.yaml                    ── Huisstijl (kleuren, fonts, styles)
  └── templates/
      └── bic_factuur.yaml    ── Document structuur (paginavolgorde)
          └── page_types/
              ├── voorblad.yaml    ── Pagina layout (tekst + lijnen posities)
              ├── locatie.yaml
              └── bic_controles.yaml
```

## 1. brand.yaml — Huisstijl Definitie

```yaml
brand:
  name: "Customer"
  slug: "customer"

colors:
  primary: "#006FAB"       # Blauw — koppen, sectie-lijnen
  secondary: "#94571E"     # Bruin — subtitels, subtotaal-lijnen
  text: "#000000"          # Zwart — body tekst
  text_light: "#666666"    # Grijs — secundaire tekst
  white: "#FFFFFF"         # Wit — footer tekst op gekleurde balk

font_files:                # Pad relatief aan tenant directory
  Arial: "fonts/arial.ttf"
  Arial-Bold: "fonts/arialbd.ttf"

fonts:                     # Logische namen → font_files keys
  heading: "Arial-Bold"    # Gebruikt bij font: heading in text_zones
  body: "Arial"            # Gebruikt bij font: body in text_zones
```

**Regel:** `font:` in text_zones verwijst naar `fonts:` in brand.yaml,
die verwijst naar `font_files:` die het .ttf bestand bepaalt.

## 2. Template YAML — Paginavolgorde

```yaml
# templates/bic_factuur.yaml
name: customer_bic_factuur     # Moet matchen met JSON "template" veld
tenant: customer

pages:
  - type: special              # Cover, achterblad
    page_type: voorblad_bic    # → page_types/voorblad_bic.yaml
    orientation: portrait

  - type: fixed                # Vaste layout, geen herhaling
    page_type: locatie
    orientation: portrait

  - type: fixed
    page_type: bic_controles
    orientation: portrait
    repeat: none               # Exact 1 pagina

  - type: fixed
    page_type: detail_weergave
    orientation: landscape
    repeat: auto               # Pagineert automatisch als data overflowt

  - type: fixed
    page_type: objecten
    orientation: landscape
    repeat: auto

  - type: special
    page_type: achterblad
    orientation: portrait
```

### Page Types

| Type | `repeat` | Gebruik |
|---|---|---|
| `special` | n.v.t. | Cover, achterblad (stationery-heavy) |
| `fixed` | `none` | Vaste layout, exact 1 pagina |
| `fixed` | `auto` | Tabel data, auto-paginering |
| `flow` | n.v.t. | Lopende tekst (ReportLab flowables) |

## 3. Page Type YAML — Pagina Layout

### Structuur

```yaml
name: bic_controles
stationery: content_portrait_stationery.pdf    # Achtergrond PDF

# Optioneel: decoratieve lijnen
line_zones:
  - x0_mm: 17.5       # Start x (mm van linkerkant)
    y_mm: 44.3         # Y positie (mm van bovenkant)
    x1_mm: 80.1        # Eind x
    width_pt: 3.0       # Lijndikte in punten
    color: "primary"    # Verwijst naar brand.yaml colors

# Tekst posities
text_zones:
  - bind: location.name          # Data binding (dot-notatie)
    x_mm: 190.6                   # X positie in mm
    y_mm: 31.7                    # Y positie in mm (van bovenkant!)
    align: right                  # left (default) | right | center
    font: heading                 # → brand.yaml fonts.heading
    size: 10                      # Font grootte in pt
    color: "primary"              # → brand.yaml colors.primary

# Optioneel: tabel configuratie (voor repeat: auto pagina's)
table:
  data_key: detail_items          # Welke array uit de flat data
  origin_x_mm: 21.9              # Tabel linkerbovenhoek
  origin_y_mm: 36.7
  row_height_mm: 5.6
  header_height_mm: 5.6
  font: body
  font_size: 7.0
  header_font: heading
  header_font_size: 7.0
  header_bg_color: "table_header_bg"
  header_text_color: "table_header_text"
  columns:
    - key: "BIC Controle nummer"
      width_mm: 40.0
      align: left
    - key: "Type"
      width_mm: 35.0
      align: left
```

### Bind Types

| Bind | Voorbeeld | Bron |
|---|---|---|
| `location.name` | "Strandbaak Kijkduin" | Uit data_transform output |
| `bic.aantal_conform` | "6" | Uit data_transform output |
| `_static.Tekst hier` | "Tekst hier" | Letterlijke tekst (hardcoded label) |
| `_page_number` | "3" | Automatisch paginanummer |
| `client.name` | "Haagwonen" | Uit data_transform output |

### Color References

| In YAML | Verwijst naar | brand.yaml |
|---|---|---|
| `"primary"` | `colors.primary` | "#006FAB" |
| `"secondary"` | `colors.secondary` | "#94571E" |
| `"text"` | `colors.text` | "#000000" |
| `"white"` | `colors.white` | "#FFFFFF" |
| `"#FF0000"` | Direct hex | (geen lookup) |

### Coördinaten Systeem

```
(0,0) ─────────────────────────── (210,0)    ← mm van linksboven
  │                                   │
  │   x_mm = afstand van links        │
  │   y_mm = afstand van boven        │
  │                                   │
  │   ⚠️ DIT IS TOP-DOWN!            │
  │   (PDF intern is bottom-up,       │
  │    maar YAML is top-down)         │
  │                                   │
(0,297) ──────────────────────── (210,297)

Portrait:  210 × 297 mm
Landscape: 297 × 210 mm
```

## 4. Hoe Voeg je een Nieuwe Pagina Toe

### Stap 1: Referentie PDF analyseren
```
Claude extraheert met PyMuPDF:
  - Tekstposities (x, y in pt)
  - Font namen en groottes
  - Kleuren (hex)
  - Lijn posities en diktes
```

### Stap 2: Converteer pt → mm
```
mm = pt × 0.352778
Voorbeeld: x=55.2pt → 19.5mm
```

### Stap 3: Schrijf YAML
```yaml
name: nieuwe_pagina
stationery: content_portrait_stationery.pdf

text_zones:
  - bind: data.veld
    x_mm: 19.5    # ← 55.2pt × 0.352778
    y_mm: 52.2
    font: body
    size: 10
    color: "text"
```

### Stap 4: Voeg toe aan template
```yaml
# templates/bic_factuur.yaml
pages:
  # ... bestaande pagina's ...
  - type: fixed
    page_type: nieuwe_pagina    # ← zelfde naam als YAML
    orientation: portrait
    repeat: none
```

### Stap 5: Update data_transform (indien nodig)
Als de JSON nieuwe velden bevat die nog niet getransformeerd worden,
update `data_transform.py` zodat de bind-paths beschikbaar zijn.
