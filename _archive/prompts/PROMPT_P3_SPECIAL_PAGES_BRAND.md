# P3: Special Pages — Brand YAML Aansluiting

## Context

`special_pages.py` rendert cover, colofon, appendix divider en backcover programmatisch. Dit is de fallback wanneer er geen stationery PDFs beschikbaar zijn. Momenteel haalt de code deels waardes uit `brand.pages.*` (colofon, appendix_divider) maar er zijn nog hardcoded coördinaten, polygonen en kleuren die niet configureerbaar zijn via de brand YAML.

Het doel: **alle visuele parameters uit de brand YAML halen**, zodat een nieuwe brand (bijv. BBL Engineering) alleen een YAML hoeft aan te passen zonder code te wijzigen.

## Scope

Focus op drie gebieden:
1. **Cover** — clip-path polygonen, badge posities/kleuren/labels, logo posities
2. **Backcover** — polygon coördinaten, contactgegevens layout
3. **TOC** — styling parameters al grotendeels in YAML, maar verify completeness

Colofon en appendix divider zijn al goed aangesloten op `brand.pages.*`.

## Stap 0: Oriëntatie

Lees voordat je begint:
- `src/bm_reports/core/special_pages.py` — alle render functies
- `src/bm_reports/assets/brands/3bm_cooperatie.yaml` — huidige `pages:` en `stationery:` secties
- `src/bm_reports/core/toc.py` — TOC rendering
- `tests/test_special_pages.py` — bestaande tests (28 tests)

## Stap 1: Inventariseer Hardcoded Waarden

Scan `special_pages.py` en maak een lijst van alle waarden die nu hardcoded zijn maar configureerbaar moeten zijn:

### Cover (`draw_cover_page`)
- `_COVER_CLIP_POINTS` — polygon voor projectfoto clip-path
- Badge definities: labels ("MEEDENKEN", "PRAKTISCH", "BETROUWBAAR"), kleuren (`_BADGE_GOLD`, `_BADGE_TURQUOISE`, `_BADGE_CORAL`), posities, afmetingen
- Logo positie en grootte (`logo_x=62, logo_y=775, logo_w=100`)
- "Ontdek ons" tekst positie en grootte
- Titel positie (`x=54.28, y=93.47`) en grootte (`28.9pt`)
- Subtitel positie en grootte
- Paars vlak hoogte/positie (`y=218.268, h=623.622`)

### Backcover (`draw_backcover_page`)
- `_WHITE_POLY` — wit geometrisch polygon
- `_PURPLE_TRI` — paurs driehoek
- Logo positie (`268, 337`) en grootte (`170`)
- Contactgegevens positie (`268, 185`) — **al deels uit brand.contact**

### TOC
- Check of `toc.py` alle styling uit `brand.pages.toc` haalt

## Stap 2: Extend Brand YAML Schema

Voeg de ontbrekende parameters toe aan `3bm_cooperatie.yaml` onder `pages:`.

### Cover sectie uitbreiden

```yaml
pages:
  cover:
    # Paurs vlak
    purple_rect_y_pt: 218.268
    purple_rect_h_pt: 623.622
    
    # Clip-path polygon voor projectfoto (A4 reference coords, PDF y-up)
    clip_polygon:
      - [350.809, 159.816]
      - [383.673, 192.680]
      - [538.583, 347.589]
      - [538.583, 519.656]
      - [386.850, 519.656]
      - [538.583, 674.565]
      - [538.583, 723.175]
      - [56.693, 723.171]
      - [56.693, 192.680]
      - [56.697, 159.816]
    
    # Foto rect (x, y, w, h in A4 reference)
    photo_rect: [55.636, 161.648, 484.002, 560.753]
    
    # Logo
    logo_key: "white"
    logo_fallback: "main"
    logo_x_ref: 62
    logo_y_ref: 775
    logo_w_ref: 100
    
    # "Ontdek ons" tekst
    ontdek_text: "Ontdek ons "
    ontdek_url: "3bm.co.nl"
    ontdek_size: 13.0
    ontdek_y_ref: 788.7
    ontdek_x_ref: 401.3
    ontdek_url_x_ref: 477.9
    
    # Badges
    badges:
      - label: "MEEDENKEN"
        bg_color: "#f0c385"
        text_color: "#401246"
        x_ref: 297.64
        y_ref: 298.82
        w_ref: 112.05
        h_ref: 33.97
      - label: "PRAKTISCH"
        bg_color: "#37bcab"
        text_color: "#401246"
        x_ref: 426.53
        y_ref: 298.82
        w_ref: 112.05
        h_ref: 33.97
      - label: "BETROUWBAAR"
        bg_color: "#e1574b"
        text_color: "#FFFFFF"
        x_ref: 341.76
        y_ref: 253.04
        w_ref: 134.70
        h_ref: 33.97
    badge_radius_ref: 17
    badge_font_size_ref: 10.2
    
    # Titel
    title_font: "$fonts.heading"
    title_size: 28.9
    title_color: "$colors.primary"
    title_x_ref: 54.28
    title_y_ref: 93.47
    
    # Subtitel
    subtitle_font: "$fonts.body"
    subtitle_size: 17.8
    subtitle_color: "$colors.secondary"
    subtitle_x_ref: 55.0
    subtitle_y_ref: 63.0
```

### Backcover sectie toevoegen

```yaml
  backcover:
    # Wit polygon (A4 reference coords, PDF y-up)
    white_polygon:
      - [0, 0]
      - [0, 698]
      - [268, 842]
      - [432, 842]
      - [432, 698]
      - [595, 555]
      - [595, 320]
      - [436, 320]
      - [595, 178]
      - [595, 0]
    
    # Paurs driehoek
    purple_triangle:
      - [0, 842]
      - [0, 539]
      - [170, 688]
      - [170, 842]
    
    # Logo
    logo_key: "main"
    logo_x_ref: 268
    logo_y_ref: 337
    logo_w_ref: 170
    
    # Contactgegevens
    contact_x_ref: 268
    contact_y_ref: 185
    contact_line_h_ref: 20
    contact_name_size: 11
    contact_detail_size: 9
    ontdek_prefix: "Ontdek ons  →  "
```

## Stap 3: Refactor special_pages.py

Pas de render functies aan om alle waarden uit de brand config te lezen in plaats van hardcoded constanten.

### Patroon

Voor elke hardcoded waarde:
```python
# VOOR (hardcoded):
canvas.drawString(_sx(54.28, pw), _sy(93.47, ph), config.project)

# NA (uit brand YAML):
spec = brand.pages.get("cover", {})
title_x = spec.get("title_x_ref", 54.28)
title_y = spec.get("title_y_ref", 93.47)
canvas.drawString(_sx(title_x, pw), _sy(title_y, ph), config.project)
```

### Volgorde van wijzigingen

1. `draw_cover_page()` — vervang alle hardcoded constanten door `spec.get()` lookups
2. `_draw_clipped_photo()` — haal clip polygon uit `spec.get("clip_polygon", _COVER_CLIP_POINTS)`
3. `_draw_badges()` — haal badge definities uit `spec.get("badges", DEFAULT_BADGES)`
4. `draw_backcover_page()` — haal polygonen en posities uit `spec.get("backcover", {})`

### Bewaar defaults

Elke `spec.get()` moet een default waarde hebben die gelijk is aan de huidige hardcoded waarde. Dit garandeert backward compatibility — een brand YAML zonder deze nieuwe velden werkt identiek aan voorheen.

```python
def draw_cover_page(canvas, doc, config, brand, cover_image=None):
    canvas.saveState()
    pw = config.effective_width_pt
    ph = config.effective_height_pt
    spec = brand.pages.get("cover", {})
    
    # Paurs vlak — uit spec met defaults
    purple_y = _sy(spec.get("purple_rect_y_pt", 218.268), ph)
    purple_h = _sy(spec.get("purple_rect_h_pt", 623.622), ph)
    # ... etc
```

## Stap 4: Update BrandConfig model

Check of `core/brand.py` het `pages` dict doorlaat als een generiek dict. Als het Pydantic velden heeft die de nieuwe keys blokkeren, pas het model aan zodat `pages` een `Dict[str, Any]` blijft (of een model met `extra = "allow"`).

## Stap 5: Tests bijwerken

### Bestaande tests
Draai `tests/test_special_pages.py` — alle 28 tests moeten nog slagen (backward compatibility door defaults).

### Nieuwe tests
Voeg tests toe die verifiëren dat brand YAML waarden correct worden opgepikt:

```python
class TestCoverFromBrandConfig:
    def test_cover_uses_brand_title_position(self):
        """Cover titel positie komt uit brand.pages.cover."""
        brand = BrandConfig()
        brand.pages["cover"] = {
            "title_x_ref": 100.0,
            "title_y_ref": 200.0,
            "title_size": 30.0,
        }
        canvas = MagicMock()
        config = _make_config(project="Test")
        draw_cover_page(canvas, None, config, brand)
        # Verifieer dat drawString is aangeroepen (titel wordt getekend)
        assert canvas.drawString.called

    def test_cover_uses_brand_badges(self):
        """Cover badges komen uit brand.pages.cover.badges."""
        brand = BrandConfig()
        brand.pages["cover"] = {
            "badges": [
                {"label": "CUSTOM", "bg_color": "#FF0000", "text_color": "#000000",
                 "x_ref": 100, "y_ref": 100, "w_ref": 80, "h_ref": 30},
            ],
        }
        canvas = MagicMock()
        config = _make_config(project="Test")
        draw_cover_page(canvas, None, config, brand)
        # roundRect moet aangeroepen zijn (badge)
        assert canvas.roundRect.called

    def test_backcover_uses_brand_polygons(self):
        """Backcover polygonen komen uit brand.pages.backcover."""
        brand = BrandConfig()
        brand.pages["backcover"] = {
            "white_polygon": [[0, 0], [100, 0], [100, 100], [0, 100]],
        }
        canvas = MagicMock()
        config = _make_config()
        draw_backcover_page(canvas, None, config, brand)
        assert canvas.drawPath.called

    def test_cover_defaults_without_spec(self):
        """Cover werkt zonder pages.cover in brand YAML."""
        brand = BrandConfig()
        canvas = MagicMock()
        config = _make_config(project="Fallback Test")
        # Moet niet crashen
        draw_cover_page(canvas, None, config, brand)
        assert canvas.drawString.called
```

## Stap 6: Draai volledige suite

```bash
python -m pytest tests/ -v --tb=short
```

**Verwacht:** 0 failures. Bestaande tests slagen door defaults, nieuwe tests valideren de brand YAML aansluiting.

## Regels

1. **Backward compatible** — elke `spec.get()` heeft een default die identiek is aan de huidige hardcoded waarde
2. **Geen regressie** — alle 28 bestaande tests moeten groen blijven
3. **Brand YAML is single source of truth** — geen hardcoded waarden meer in de code, alles via `spec.get()` met defaults
4. **A4 reference coords** — alle `_ref` waarden in de YAML zijn in het A4 referentie-coördinatenstelsel (595.28 × 841.89 pt). Schaling naar andere formaten gaat via `_sx()` en `_sy()`
5. **Module constanten als defaults** — de huidige module-level constanten (`_COVER_CLIP_POINTS`, `_WHITE_POLY`, etc.) blijven bestaan als default waarden, maar worden niet meer direct aangesproken in de render functies

## Verwachte output

- `src/bm_reports/core/special_pages.py` — refactored, alle waarden uit brand spec
- `src/bm_reports/assets/brands/3bm_cooperatie.yaml` — uitgebreid met `pages.cover` en `pages.backcover`
- `tests/test_special_pages.py` — uitgebreid met brand YAML tests
- Alle tests groen

## Update na afloop

Werk `SESSION_STATUS.md` en `STATUS.md` bij:
- Special pages brand YAML aansluiting: ✅ Compleet
