# P1: Stationery Extractie — Brand Achtergronden Genereren

## Context

De openaec-reports backend is feature-complete. De `StationeryExtractor`, `BrandBuilder`, en `page_templates.py` (stationery-first callbacks) werken. Maar de **data ontbreekt**: in `3bm_cooperatie.yaml` staan alle `source:` velden leeg en alle `text_zones:` zijn `[]`.

Zonder stationery PDFs valt het systeem terug op programmatische rendering (`special_pages.py`). Die werkt, maar is niet pixel-perfect gelijk aan de originele huisstijl. Het doel van deze prompt is de stationery PDFs te extraheren, in te pluggen, en de text zones te mappen.

## Referentie-bestanden

- **Referentie-rapport:** `huisstijl/2707_BBLrapportage_v01.pdf` — het originele BBL rapport
- **Brand YAML:** `src/openaec_reports/assets/brands/3bm_cooperatie.yaml`
- **Stationery tools:** `src/openaec_reports/tools/stationery_extractor.py` en `tools/brand_builder.py`
- **Page templates:** `src/openaec_reports/core/page_templates.py`
- **Cover spec:** `COVER_SPEC.md`

## Stap 0: Oriëntatie

Lees deze bestanden voordat je begint:
- `src/openaec_reports/tools/stationery_extractor.py` — de 4 extractie-modi
- `src/openaec_reports/tools/brand_builder.py` — de build pipeline
- `src/openaec_reports/core/page_templates.py` — hoe stationery wordt gerenderd
- `src/openaec_reports/assets/brands/3bm_cooperatie.yaml` — wat ingevuld moet worden
- `COVER_SPEC.md` — pixel-precieze cover layout

## Stap 1: Analyseer het referentie-rapport

Gebruik PyMuPDF om het referentie-rapport te inspecteren. Bepaal welke pagina's welk type zijn:

```python
import fitz

doc = fitz.open("huisstijl/2707_BBLrapportage_v01.pdf")
for i in range(len(doc)):
    page = doc[i]
    text = page.get_text()[:200]
    print(f"Pagina {i+1}: {text[:80]}...")
    # Check ook afmetingen en kleuren
    print(f"  Size: {page.rect.width:.1f} x {page.rect.height:.1f}")
doc.close()
```

**Verwacht:** Pagina 1 = cover, pagina 2 = colofon, pagina 3+ = content, ergens een appendix divider, en de laatste pagina = backcover.

Noteer de exacte paginanummers (0-based) voor elk type.

## Stap 2: Extraheer stationery PDFs

Maak de output directory en extraheer per paginatype:

```python
from pathlib import Path
from openaec_reports.tools.stationery_extractor import StationeryExtractor

source = Path("huisstijl/2707_BBLrapportage_v01.pdf")
out_dir = Path("src/openaec_reports/assets/brands/3bm-cooperatie/stationery")
out_dir.mkdir(parents=True, exist_ok=True)

extractor = StationeryExtractor(source)

# Cover (pagina 0): strip de titel en subtitel, behoud graphics + logo
# Bepaal strip zones op basis van de tekst posities
```

### Per paginatype:

#### Cover
- **Methode:** `extract_stripped_page()` met strip zones voor titel en subtitel
- **Strip zones:** Vind de titel-tekst en subtitel-tekst posities via `page.get_text("dict")`, maak rectangles die de tekst omvatten met 5pt marge
- **Output:** `stationery/cover.pdf`
- **Verificatie:** Open de output PDF, controleer dat het paarse vlak, de badges, het logo, en "Ontdek ons 3bm.co.nl" intact zijn, maar de projectnaam en subtitel weg zijn

#### Colofon
- **Methode:** `extract_stripped_page()` met strip zones voor alle dynamische labels en waarden
- **Strip zones:** Alle tekst in het formuliergebied (y ≈ 300-660 in PDF coords). Het rapport type en subtitel bovenaan. De pagina-nummer. Behoud het turquoise blok en logo linksonder
- **Output:** `stationery/colofon.pdf`
- **Verificatie:** Turquoise blok + logo intact, alle veldtekst weg

#### Content
- **Methode:** `extract_stripped_page()` op een typische content pagina
- **Strip zones:** Alle body tekst, headings, paginanummer. Behoud header/footer grafische elementen als die er zijn
- **Output:** `stationery/content.pdf`
- **Opmerking:** Als de content pagina's geen grafische achtergrond hebben (alleen tekst + header/footer), dan is `source: ""` correct en wordt de programmatische BrandRenderer gebruikt. In dat geval: **sla deze extractie over** en laat `source: ""` staan.

#### Appendix Divider
- **Methode:** `extract_stripped_page()` met strip zones voor "Bijlage N" en de titel
- **Strip zones:** Tekst > 20pt fontsize
- **Output:** `stationery/appendix_divider.pdf`
- **Verificatie:** Turquoise achtergrond + paurs blok intact, bijlage tekst weg

#### Backcover
- **Methode:** `extract_full_page()` — de backcover is 100% statisch
- **Output:** `stationery/backcover.pdf`
- **Verificatie:** Alles intact, geen tekst verwijderd

## Stap 3: Visuele verificatie

Open elke geëxtraheerde PDF en vergelijk met de originele pagina in het referentie-rapport:

```python
import fitz

for name in ["cover", "colofon", "appendix_divider", "backcover"]:
    path = f"src/openaec_reports/assets/brands/3bm-cooperatie/stationery/{name}.pdf"
    doc = fitz.open(path)
    page = doc[0]
    # Render naar PNG voor visuele inspectie
    pix = page.get_pixmap(dpi=150)
    pix.save(f"output/_review/stationery_{name}.png")
    doc.close()
    print(f"Review: output/_review/stationery_{name}.png")
```

**Check per bestand:**
- ✅ Grafische elementen (vlakken, polygonen, logo's) intact
- ✅ Dynamische tekst (titel, subtitel, veldwaarden) verwijderd
- ❌ Logo's of grafisch design beschadigd → pas strip zones aan

## Stap 4: Text Zones Mappen

Nu de stationery PDFs staan, moeten de `text_zones` gedefinieerd worden. Dit zijn de posities waar `page_templates.py` dynamische tekst tekent bovenop de stationery achtergrond.

### Cover text zones

Haal de exacte posities uit de originele pagina:

```python
doc = fitz.open("huisstijl/2707_BBLrapportage_v01.pdf")
page = doc[0]  # cover
text_dict = page.get_text("dict")
for block in text_dict["blocks"]:
    if block["type"] == 0:  # tekst
        for line in block["lines"]:
            for span in line["spans"]:
                if span["size"] > 14:  # alleen grote tekst = titel/subtitel
                    print(f"  Text: '{span['text'][:50]}' size={span['size']:.1f} "
                          f"x={span['origin'][0]:.1f} y={span['origin'][1]:.1f} "
                          f"font={span['font']}")
doc.close()
```

Gebruik de gevonden posities om text zones te definiëren. Map de y-coördinaten van PyMuPDF (top-down) naar `y_pt` in de YAML (ook top-down, conversie naar ReportLab bottom-up gebeurt in `_draw_text_zones()`).

**Cover text zones (voorbeeld, pas aan op werkelijke posities):**
```yaml
text_zones:
  - type: text
    bind: project
    font: "$fonts.heading"
    color: "$colors.primary"
    size: 28.9
    x_pt: 54.28
    y_pt: 748.4    # ph - 93.47 in A4 = ~748.4 top-down
    align: left
  - type: text
    bind: subtitle
    font: "$fonts.body"
    color: "$colors.secondary"
    size: 17.8
    x_pt: 55.0
    y_pt: 778.9    # ph - 63.0 = ~778.9 top-down
    align: left
```

### Colofon text zones

Map alle velden uit `pages.colofon.fields` naar text zones. De y_pt waarden staan al in de YAML. Kopieer ze naar de stationery text_zones:

```yaml
text_zones:
  - type: text
    bind: report_type
    font: "$fonts.heading"
    color: "$colors.primary"
    size: 22.0
    x_pt: 70.9
    y_pt: 57.3
    align: left
  - type: text
    bind: subtitle
    font: "$fonts.body"
    color: "$colors.secondary"
    size: 14.0
    x_pt: 70.9
    y_pt: 86.8
    align: left
  # ... alle velden uit pages.colofon.fields mappen
```

### Appendix divider text zones

```yaml
text_zones:
  - type: text
    bind: appendix_number
    font: "$fonts.heading"
    color: "$colors.primary"
    size: 41.4
    x_pt: 103
    y_pt: 193.9
    align: left
  - type: text
    bind: appendix_title
    font: "$fonts.body"
    color: "#FFFFFF"
    size: 41.4
    x_pt: 136.1
    y_pt: 262.2
    align: left
```

### Backcover text zones

Backcover is 100% statisch (alle tekst bakt mee in de stationery PDF), dus `text_zones: []` is correct.

## Stap 5: Update 3bm_cooperatie.yaml

Vul de `stationery:` sectie in met de correcte `source:` paden (relatief aan de brand directory) en de gemapte `text_zones:`. 

De `source:` paden moeten relatief zijn aan `assets/brands/`:
```yaml
stationery:
  cover:
    source: "3bm-cooperatie/stationery/cover.pdf"
    text_zones:
      - type: text
        bind: project
        # ... etc
```

## Stap 6: End-to-End Test

Genereer een test-rapport met de stationery achtergronden:

```python
from openaec_reports.core.engine import Report

report = Report.from_json("schemas/example_structural.json", brand="3bm_cooperatie")
output = report.build("output/test_met_stationery.pdf")
print(f"Output: {output}")
```

Open `output/test_met_stationery.pdf` en verifieer:
- ✅ Cover: stationery achtergrond met dynamische titel bovenop
- ✅ Colofon: stationery achtergrond met ingevulde velden
- ✅ Content pagina's: header/footer correct, body tekst in het content frame
- ✅ Appendix divider: turquoise achtergrond met dynamisch nummer/titel
- ✅ Backcover: exact zoals origineel

Render de eerste 5 pagina's naar PNG voor visuele review:

```python
import fitz
doc = fitz.open("output/test_met_stationery.pdf")
for i in range(min(5, len(doc))):
    pix = doc[i].get_pixmap(dpi=150)
    pix.save(f"output/_review/result_page_{i+1}.png")
doc.close()
```

## Stap 7: Fix Issues

Als text zones niet op de juiste plek staan:
1. Vergelijk de originele referentie-pagina (PNG) naast de gegenereerde pagina (PNG)
2. Meet het verschil in pixels, converteer naar points (1 pixel @ 150 DPI ≈ 0.48 pt)
3. Pas `x_pt` en `y_pt` aan in de YAML
4. Regenereer en verifieer opnieuw

**Let op:** De `_draw_text_zones()` functie converteert `y_pt` (top-down) naar ReportLab (bottom-up) met `rl_y = ph - y_pt`. Zorg dat de y_pt waarden in de YAML in **top-down** notatie staan (0 = bovenkant pagina).

## Regels

1. **Geen productie code wijzigen** — alleen YAML config en stationery PDF bestanden
2. **Visueel verifiëren** na elke stap — open de PNG output
3. **Relatieve paden** in YAML — `3bm-cooperatie/stationery/cover.pdf`, niet absoluut
4. **Fallback behouden** — als stationery niet werkt, moet de programmatische rendering (`special_pages.py`) nog steeds functioneren. Test dit door tijdelijk `source: ""` te zetten
5. **Geen externe afhankelijkheden** — alle tools zitten al in de codebase

## Verwachte output

Na afloop moeten bestaan:
- `src/openaec_reports/assets/brands/3bm-cooperatie/stationery/cover.pdf`
- `src/openaec_reports/assets/brands/3bm-cooperatie/stationery/colofon.pdf` (indien relevant)
- `src/openaec_reports/assets/brands/3bm-cooperatie/stationery/appendix_divider.pdf`
- `src/openaec_reports/assets/brands/3bm-cooperatie/stationery/backcover.pdf`
- `src/openaec_reports/assets/brands/3bm_cooperatie.yaml` — bijgewerkt met `source:` en `text_zones:`
- `output/test_met_stationery.pdf` — werkend test-rapport
- `output/_review/stationery_*.png` — visuele review van geëxtraheerde stationery
- `output/_review/result_page_*.png` — visuele review van gegenereerd rapport

## Update na afloop

Werk `SESSION_STATUS.md` en `STATUS.md` bij:
- Stationery PDFs: ✅ Geëxtraheerd
- Text zones: ✅ Gemapped
- End-to-end met stationery: ✅ Werkend
