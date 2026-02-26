# Backend Opdracht — Bugs fixen + Ontbrekende onderdelen

## Situatieschets

De core components (CalculationBlock, CheckBlock, ImageBlock, TableBlock) zijn werkend.
De JSON pipeline (from_json/from_dict, block_registry) is compleet.
Het brand systeem (YAML-driven header/footer) werkt.

Maar er zitten meerdere bugs en architectuurproblemen in die eerst opgelost moeten worden
voordat we aan nieuwe features beginnen (cover/colofon/backcover).

---

## BUG 1 — KRITISCH: Kleuren mismatch tussen styles.py en brand systeem

### Probleem
`core/styles.py` definieert `BM_COLORS` met GENERIEKE kleuren:
- primary = "#1B3A5C" (marineblauw)
- secondary = "#4A90A4" (middenblauw)

Maar de 3BM huisstijl kleuren staan in `assets/brands/3bm_cooperatie.yaml`:
- primary = "#40124A" (donkerpaars)
- secondary = "#38BDA0" (turquoise)

ALLE componenten (CalculationBlock, CheckBlock, TableBlock) importeren `BM_COLORS` uit styles.py.
Dus ze renderen in marineblauw in plaats van 3BM paars/turquoise.

Het brand systeem voedt alleen de BrandRenderer (header/footer), NIET de componenten.

### Oplossing
De kleuren in `styles.py` moeten overeenkomen met de 3BM huisstijl.
Update BM_COLORS naar de correcte 3BM kleuren:

```python
@dataclass(frozen=True)
class Colors:
    primary: str = "#40124A"       # Donkerpaars (3BM huisstijl)
    secondary: str = "#38BDA0"     # Turquoise (3BM huisstijl)
    accent: str = "#2ECC71"        # Groen (voldoet)
    warning: str = "#E74C3C"       # Rood (voldoet niet)
    text: str = "#45243D"          # Donkerpaars tekst
    text_light: str = "#7F8C8D"    # Lichtgrijs
    background: str = "#FFFFFF"    # Wit
    background_alt: str = "#F8F9FA"  # Lichtgrijs achtergrond
    rule: str = "#BDC3C7"          # Lijn kleur
```

Tegelijk: update de heading/TOC kleuren in de stylesheet.
De TOC koppen in het referentie-PDF gebruiken turquoise (#56b49b / #38BDA0) voor hoofdstuk-titels.

Na deze wijziging: regenereer `output/component_showcase.pdf` en verifieer dat de kleuren
nu paars/turquoise zijn in plaats van blauw.

---

## BUG 2 — Engine convenience methods zijn dode code

### Probleem
In `core/engine.py` zijn deze methods leeg (alleen `return self`):
- `add_calculation()`
- `add_check()`
- `add_table()`
- `add_image()`

Ze voegen NIETS toe aan het rapport. Iemand die de Python API gebruikt (niet via JSON)
krijgt een leeg rapport.

### Oplossing
Implementeer elke method zodat ze de bijbehorende component instantiëren en toevoegen
aan de huidige sectie (of een nieuwe sectie als er geen is).

Voorbeeld voor add_calculation:
```python
def add_calculation(self, title, formula="", substitution="", result="", unit="", reference="", **kwargs):
    from bm_reports.components.calculation import CalculationBlock
    block = CalculationBlock(
        title=title, formula=formula, substitution=substitution,
        result=result, unit=unit, reference=reference,
    )
    # Voeg toe aan laatste sectie, of maak een impliciete sectie
    if self._sections:
        self._sections[-1]["content"].append(block)
    else:
        self.document.add_element(block)
    return self
```

Doe hetzelfde voor add_check, add_table, add_image.

Schrijf een test die verifieert dat `report.add_calculation(...)` daadwerkelijk
een CalculationBlock in de output genereert.

---

## BUG 3 — TitleBlock.draw() is leeg

### Probleem
`components/title_block.py` heeft een lege `draw()` methode.
De engine gebruikt TitleBlock niet eens — het maakt een kale Paragraph.

### Oplossing
Op dit moment: NIET implementeren. TitleBlock wordt vervangen door een canvas-functie
voor de cover page (zie taak "Special Pages" hieronder). 
Markeer de class als deprecated met een TODO of verwijder hem.

---

## TAAK 1 — CLAUDE.md updaten

Update de statustabel in CLAUDE.md. De huidige status is FOUT.
Correcte status:

| Type | Class | Registry | Rendering |
|------|-------|----------|-----------|
| paragraph | Paragraph (ReportLab) | ✅ | ✅ Werkend |
| calculation | CalculationBlock | ✅ | ✅ Werkend |
| check | CheckBlock | ✅ | ✅ Werkend |
| table | TableBlock | ✅ | ✅ Werkend |
| image | ImageBlock | ✅ | ✅ Werkend |
| map | KadasterMap | ✅ | 🔲 Stub (PDOK) |
| spacer | Spacer (ReportLab) | ✅ | ✅ Triviaal |
| page_break | PageBreak (ReportLab) | ✅ | ✅ Triviaal |
| raw_flowable | ReportLab Flowable | ✅ | ✅ Library-only |

Markeer Fase 3 als: [x] Fase 3: Components — AFGEROND

---

## TAAK 2 — Gotham fonts registreren (VOORBEREIDING)

De 3BM huisstijl gebruikt de Gotham fontfamilie:
- GothamBold (koppen, labels)
- GothamBook (broodtekst)
- GothamMedium (accenten)
- Gotham-BookItalic (cursief)

Check of de Gotham font-bestanden (.ttf of .otf) beschikbaar zijn in het project
of op het systeem. Als ze er zijn, registreer ze in ReportLab:

```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont('GothamBold', 'pad/naar/Gotham-Bold.ttf'))
pdfmetrics.registerFont(TTFont('GothamBook', 'pad/naar/Gotham-Book.ttf'))
# etc.
```

Maak een `core/fonts.py` module die:
1. Zoekt naar font bestanden in `assets/fonts/`
2. Registreert ze als ze bestaan
3. Graceful fallback naar Helvetica als ze ontbreken
4. Wordt aangeroepen bij module import (in __init__.py)

Update daarna FontConfig in styles.py:
```python
@dataclass(frozen=True)
class FontConfig:
    heading: str = "GothamBold"      # fallback: "Helvetica-Bold"
    body: str = "GothamBook"         # fallback: "Helvetica"
    mono: str = "Courier"
    # ...
```

ALS de font bestanden NIET beschikbaar zijn: laat dit als TODO staan,
maak wel de fonts.py infrastructuur klaar, en documenteer in CLAUDE.md
dat de Gotham TTF/OTF bestanden in `assets/fonts/` geplaatst moeten worden.

---

## TAAK 3 — Special Pages (cover, colofon, backcover)

Dit is de grootste taak. De cover, colofon en backcover zijn visueel complexe pagina's
die NIET als flowables geïmplementeerd kunnen worden. Ze moeten direct op het canvas
getekend worden.

### Huisstijl referentie (uit BBL rapport analyse)

**Kleuren:**
- Donkerpaars: rgb(0.25, 0.07, 0.28) = #40124A
- Turquoise: rgb(0.22, 0.74, 0.67) = #38BDA0 / #38BDAB
- Wit: #FFFFFF
- Tekst donker: #45243D / #401246

**Cover page (pagina 1):**
- Donkerpaars vlak bovenaan: rect(0, 0, 595×624 pt) — ~74% van pagina
- Projectfoto erboven (gemaskeerd)
- 3BM logo linksboven (als vector, maar wij gebruiken SVG/PNG)
- "Ontdek ons 3bm.co.nl" rechtsboven
- Kernwoorden: "BETROUWBAAR", "PRAKTISCH", "MEEDENKEN" — zwevend op de pagina
- Titel onderaan: GothamBold 28.9pt, kleur #401246
- Ondertitel: GothamBook 17.8pt, kleur #38BDAB

**Colofon (pagina 2):**
- Titel + ondertitel herhaald bovenaan (GothamBold 22pt + GothamBook 14pt)
- Twee-koloms info tabel:
  - Links (GothamBold 10pt, paars/turquoise): Project, In opdracht van, Adviseur, etc.
  - Rechts (GothamBook 10pt, paars): waarden
- Horizontale scheidingslijnen in paars
- Turquoise geometrische driehoek/parallelogram linksonder
- 3BM logo rechtsonder

**Backcover (pagina 36):**
- Turquoise vlak als basis (bijna hele pagina)
- Wit polygon eroverheen: zigzag/geometrisch patroon met schuine lijnen
  Polygon: (0,0→0,698→0,842→268,842→432,698→595,555→595,320→436,320→595,178→595,0→0,0)
- Donkerpaars driehoek linksboven: (0,0→0,303→170,154→170,0)
- 3BM logo groot in het midden (vector)
- Contactgegevens + "Ontdek ons" onderaan
- "3bm Coöperatie U.A.", "Wattstraat 17 | 3335 LV Zwijndrecht | T. 078 7400 250"

### Implementatie aanpak

Maak een nieuw bestand: `src/bm_reports/core/special_pages.py`

Met drie functies:
1. `draw_cover_page(canvas, doc, config: DocumentConfig, brand: BrandConfig)`
2. `draw_colofon_page(canvas, doc, config: DocumentConfig, brand: BrandConfig, colofon_data: dict)`
3. `draw_backcover_page(canvas, doc, config: DocumentConfig, brand: BrandConfig)`

Deze functies tekenen DIRECT op het canvas met:
- canvas.setFillColor(), canvas.rect(), canvas.line()
- canvas.drawString(), canvas.setFont()
- canvas.drawImage() voor logo's
- Polygonen via canvas.beginPath(), canvas.moveTo(), canvas.lineTo(), canvas.fill()

**Integratie in engine.py:**
De `_build_elements()` methode moet gewijzigd worden:
- Cover: gebruik NextPageTemplate("cover") + een lege/minimale flowable,
  en koppel draw_cover_page aan de cover PageTemplate's onPage callback.
- Colofon: idem met een colofon PageTemplate
- Backcover: idem

OF: voeg een extra PageTemplate toe per special page en gebruik onPage callbacks.

**BELANGRIJK:** Begin simpel. Maak eerst een werkende cover met:
- Paars vlak bovenaan (2/3 van pagina)
- Logo (uit assets/logos/3bm-cooperatie-wit.png) in het paarse vlak
- Projecttitel groot onderaan
- Ondertitel in turquoise

Pas daarna de geometrische elementen, kernwoorden, en fotomask toe.

---

## Volgorde van uitvoering

1. **BUG 1** — Fix kleuren in styles.py (5 min)
2. **TAAK 1** — Update CLAUDE.md (5 min)
3. **BUG 2** — Fix engine convenience methods (15 min)
4. Regenereer component_showcase.pdf en verifieer kleuren (5 min)
5. **TAAK 2** — Fonts infrastructuur (20 min)
6. **TAAK 3** — Special pages — cover first, dan colofon, dan backcover (groot)

Na elke stap: commit met beschrijvend bericht.
