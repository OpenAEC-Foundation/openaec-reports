# Cover Page — Pixel-Perfect Specificatie

> Geëxtraheerd uit `2707_BBLrapportage_v01.pdf` pagina 1 via PyMuPDF content stream analyse.
> Alle coördinaten in **PDF points** (1pt = 1/72 inch = 0.353mm).
> PDF coördinatensysteem: **y=0 is onderkant pagina** (ReportLab convention).

## Pagina

| Eigenschap | Waarde |
|---|---|
| Formaat | A4 Portrait |
| Afmeting | 595.28 × 841.89 pt (210 × 297 mm) |

## Laag 1 — Paarse achtergrond (vast)

```
canvas.setFillColorCMYK(0.76, 1.0, 0.36, 0.43)  # Exact CMYK uit PDF
# OF: canvas.setFillColor(HexColor("#401146"))
canvas.rect(0, 218.268, 595.275, 623.622, fill=1, stroke=0)
```

| Eigenschap | Waarde |
|---|---|
| PDF operatie | `0 218.268 595.275 623.622 re f` |
| Positie (y-up) | x=0, y=218.27, w=595.28, h=623.62 |
| Bovenkant (y-down) | y=0 tot y=623.62 (74.1% van pagina) |
| Kleur (CMYK) | C=0.76 M=1.0 Y=0.36 K=0.43 |
| Kleur (RGB approx) | `#401146` |

## Laag 2 — Projectfoto met clipping path (DYNAMISCH)

### Image transform
```
484.0020752 0 0 560.753235 55.636658 161.648239 cm
/Im0 Do
```

| Eigenschap | Waarde |
|---|---|
| Positie (y-up) | x=55.64, y=161.65 |
| Afmeting | 484.00 × 560.75 pt (170.8 × 197.8 mm) |
| Bron resolutie | 927 × 1074 px, RGB, PNG |

### Clipping polygon (PDF y-up coördinaten)

**CRITICAL: Dit is de exacte clip-path uit de PDF. Gebruik `canvas.clipPath()` in ReportLab.**

```python
# Exacte polygon punten (PDF y-up coördinaten — direct bruikbaar in ReportLab)
COVER_CLIP_POINTS = [
    (350.809, 159.816),   # punt 1  — rechtsonder start
    (383.673, 192.680),   # punt 2  — diagonaal naar rechtsboven
    (538.583, 347.589),   # punt 3  — rechterrand, middenboven
    (538.583, 519.656),   # punt 4  — rechterrand, hoger
    (386.850, 519.656),   # punt 5  — terug naar midden (inkeping)
    (538.583, 674.565),   # punt 6  — diagonaal naar rechtsboven
    (538.583, 723.175),   # punt 7  — rechterrand, bovenkant
    ( 56.693, 723.171),   # punt 8  — linkerrand, bovenkant
    ( 56.693, 192.680),   # punt 9  — linkerrand, onderkant
    ( 56.697, 159.816),   # punt 10 — linkerrand, start
]
```

### Drie uitsnedes (waar paars doorheen schijnt)

1. **Rechtsonder (groot)**: Driehoek tussen punten 10→1→2→3 en de rechteronderkant. Diagonale lijn van (56.70, 159.82) via (350.81, 159.82) naar (538.58, 347.59).
2. **Rechtsmidden (klein)**: "Inkeping" tussen punten 3→4→5→6. Het pad gaat van rechterrand (538.58) naar links (386.85) en terug, waardoor een driehoekige notch ontstaat.
3. **Linksonder (klein)**: Driehoek tussen punten 9→10 en de linkeronderkant. Verticale sprong van y=192.68 naar y=159.82 (klein verschil van ~32.86pt).

### ReportLab implementatie

```python
def _draw_clipped_photo(canvas, photo_path, page_w, page_h):
    """Teken projectfoto met exacte clip-path uit BBL template."""
    canvas.saveState()
    
    # Clipping polygon definiëren
    clip = canvas.beginPath()
    clip.moveTo(350.809, 159.816)
    clip.lineTo(383.673, 192.680)
    clip.lineTo(538.583, 347.589)
    clip.lineTo(538.583, 519.656)
    clip.lineTo(386.850, 519.656)
    clip.lineTo(538.583, 674.565)
    clip.lineTo(538.583, 723.175)
    clip.lineTo( 56.693, 723.171)
    clip.lineTo( 56.693, 192.680)
    clip.lineTo( 56.697, 159.816)
    clip.close()
    
    # Clip toepassen
    canvas.clipPath(clip, stroke=0, fill=0)
    
    # Foto tekenen (wordt automatisch geclipt)
    canvas.drawImage(
        str(photo_path),
        55.636658, 161.648239,  # x, y positie
        484.002075, 560.753235,  # breedte, hoogte
        mask='auto',
        preserveAspectRatio=True,
    )
    
    canvas.restoreState()
```

## Laag 3 — Logo + "Ontdek ons" (vast)

### 3BM Logo (wit variant)
- Positie: linksboven in paars vlak
- Type: vectorpaden (wit, #FFFFFF)
- Fallback: PNG `assets/logos/3bm-cooperatie-wit.png`
- Geschatte bbox (y-down): x=62, y=30, ~100×60pt

### "Ontdek ons 3bm.co.nl"

| Element | Font | Size | Kleur | Positie (y-down bbox) |
|---|---|---|---|---|
| "Ontdek ons " | GothamMedium | 13.0pt | #FFFFFF (wit) | (401.3, 53.2) |
| "3bm.co.nl" | GothamMedium | 13.0pt | #38bdab (turquoise) | (477.9, 53.2) |

```python
# In PDF y-up coords: baseline y = 841.89 - 53.2 - ~14 (cap height) ≈ 774.69
# Maar het eenvoudigst: gebruik y-down bbox en converteer
# "Ontdek ons" baseline in y-up: 841.89 - 67.4 + (67.4-53.2)*0.7 ≈ 784.43
canvas.setFont("GothamMedium", 13)
canvas.setFillColor(white)
canvas.drawString(401.3, 784.4, "Ontdek ons ")
canvas.setFillColor(HexColor("#38bdab"))
canvas.drawString(477.9, 784.4, "3bm.co.nl")
```

## Laag 4 — Kernwoord badges (vast)

Alle badges zijn **rounded rectangles** met radius ~17pt.

### MEEDENKEN (goud)

| Eigenschap | Waarde |
|---|---|
| Rect (y-down) | (297.64, 509.10) → (409.69, 543.07) |
| Afmeting | 112.05 × 33.97 pt |
| Achtergrond | `#f0c385` (goud) |
| Font | GothamMedium 10.2pt |
| Tekst kleur | `#401246` (donkerpaars) |
| Icoon | Ster, `#2d0435`, 13.8×13.8pt |

### PRAKTISCH (turquoise)

| Eigenschap | Waarde |
|---|---|
| Rect (y-down) | (426.53, 509.10) → (538.58, 543.07) |
| Afmeting | 112.05 × 33.97 pt |
| Achtergrond | `#37bcab` (turquoise) |
| Font | GothamMedium 10.2pt |
| Tekst kleur | `#401246` (donkerpaars) |
| Icoon | Zon, `#2d0435`, 15.3×15.3pt |

### BETROUWBAAR (koraalrood)

| Eigenschap | Waarde |
|---|---|
| Rect (y-down) | (341.76, 554.88) → (476.46, 588.85) |
| Afmeting | 134.70 × 33.97 pt |
| Achtergrond | `#e1574b` (koraalrood) |
| Font | GothamMedium 10.2pt |
| Tekst kleur | `#FFFFFF` (wit) |
| Icoon | Vinkje, `#FFFFFF`, 12.3×12.3pt |

**Positie-patroon**: MEEDENKEN en PRAKTISCH staan op dezelfde hoogte (y=509.10), BETROUWBAAR eronder (y=554.88). Badges overlappen gedeeltelijk met de foto-clip zone.

## Laag 5 — Titel & ondertitel (DYNAMISCH)

| Element | Font | Size | Kleur | PDF y-up baseline |
|---|---|---|---|---|
| Rapporttitel | GothamBold | 28.9pt | #401246 | y=93.47, x=54.28 |
| Ondertitel | GothamBook | 17.8pt | #38bdab | y=~63 (afgeleid), x=55.0 |

```python
# Titel
canvas.setFont("GothamBold", 28.9)  # fallback: Helvetica-Bold
canvas.setFillColor(HexColor("#401246"))
canvas.drawString(54.28, 93.47, config.project)  # PDF y-up coords!

# Ondertitel  
canvas.setFont("GothamBook", 17.8)  # fallback: Helvetica
canvas.setFillColor(HexColor("#38bdab"))
canvas.drawString(55.0, 63.0, cover_subtitle)
```

## Tekenvolgorde (draw order)

1. `setFillColorCMYK(0.76, 1.0, 0.36, 0.43)` → `rect(0, 218.27, 595.28, 623.62)` — Paarse achtergrond
2. `saveState()` → `clipPath(polygon)` → `drawImage(foto)` → `restoreState()` — Geclipt foto
3. Logo tekenen (wit PNG/SVG)
4. "Ontdek ons 3bm.co.nl" tekst
5. Drie keyword badges (rounded rects + tekst + iconen)
6. Rapporttitel (GothamBold 28.9pt, paars)
7. Ondertitel (GothamBook 17.8pt, turquoise)

## Samenvatting instelbare velden

| Veld | JSON pad | Beschrijving |
|---|---|---|
| Projectfoto | `cover.image` | Pad naar afbeelding of base64 |
| Rapporttitel | `project` | Hoofd titel (groot, paars) |
| Ondertitel | `cover.subtitle` | Subtitel (kleiner, turquoise) |

Alle overige elementen (paars vlak, clip-polygon, logo, "Ontdek ons", badges) zijn **vast** en worden niet per rapport aangepast.
