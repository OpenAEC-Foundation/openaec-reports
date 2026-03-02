# Huisstijl Vertaling — Probleemanalyse & Aanpak

## Het probleem

De gegenereerde PDF's wijken sterk af van het referentiedocument. Op de cover alleen al:
- Logo op verkeerde positie
- Titel/subtitel ontbreekt of staat verkeerd
- Geen projectafbeelding
- Badges niet in kleur
- Turquoise lijn onderaan die er niet hoort
- Op pagina 2 staat tekst die er niet hoort

**Oorzaak:** De huidige workflow probeert een complex visueel ontwerp te *reconstrueren* vanuit code met handmatig geschatte coördinaten. Dit is inherent foutgevoelig omdat:

1. **Coördinaat-systemen conflicteren** — PDF gebruikt bottom-up (y=0 onderaan), de YAML mix top-down en bottom-up referenties
2. **Geen visuele verificatie** — er is geen manier om gegenereerde output te vergelijken met het origineel
3. **Complexe geometrieën** — clip-paths, polygonen, badge-posities zijn handmatig overgetypt
4. **Geen feedback loop** — als iets niet klopt, is er geen systematische manier om het te debuggen

---

## De opties

### Optie A: Coördinaten repareren (huidige aanpak verbeteren)

**Wat:** Elke coördinaat in de YAML handmatig nalopen, vergelijken met het referentie-PDF, corrigeren.

| + | - |
|---|---|
| Geen architectuurwijziging | Extreem tijdrovend |
| | Foutgevoelig (zelfde probleem opnieuw) |
| | Moet herhaald worden voor elk nieuw bureau |
| | Complexe polygonen/clip-paths blijven fragiel |

**Verdict:** ❌ Symptoombestrijding, geen oplossing.

---

### Optie B: Stationery-first (PDF als achtergrond)

**Wat:** Gebruik de originele PDF-pagina's als *achtergrond* (stationery). Leg alleen dynamische tekst er overheen. Net zoals briefpapier bij een printer.

**Hoe:**
1. Extraheer elke pagina-type (cover, colofon, content, bijlage, backcover) als losse PDF
2. Strip de variabele tekst (projectnaam, datum, etc.) uit de stationery
3. Definieer "tekst-zones" in YAML: rechthoeken waar dynamische tekst komt
4. Renderer laadt stationery PDF als achtergrond, plaatst tekst in de zones

```yaml
pages:
  cover:
    stationery: "stationery/cover.pdf"
    text_zones:
      - name: "title"
        x: 54
        y: 94
        width: 480
        font: "$heading"
        size: 28.9
        color: "$primary"
      - name: "subtitle"
        x: 55
        y: 63
        width: 480
        font: "$body"
        size: 17.8
        color: "$secondary"
      - name: "project_image"
        type: "image"
        clip_from_stationery: true  # foto-zone al in stationery
```

| + | - |
|---|---|
| **Pixel-perfect by design** | Stationery is statisch (badges altijd zelfde) |
| Geen coördinaat-problemen voor visuele elementen | Elke format-wijziging vereist nieuwe stationery |
| Snel op te zetten voor nieuw bureau | A3/landscape vereist aparte stationery |
| Eenvoudige YAML (alleen tekst-zones) | Cover-foto vereist extra logica |

**Verdict:** ✅ Beste optie voor snelle, betrouwbare resultaten.

---

### Optie C: Visuele diff + iteratieve correctie

**Wat:** Bouw een tool die:
1. Genereert een PDF pagina
2. Legt het over het referentie-origineel
3. Toont pixel-voor-pixel verschil
4. Ontwikkelaar past YAML aan → herhaal

**Hoe:** Python script met pdf2image + PIL/OpenCV:
```python
def visual_diff(generated: Path, reference: Path, page: int) -> float:
    """Vergelijk twee PDF pagina's, return similarity score 0-1."""
    gen_img = pdf_to_image(generated, page)
    ref_img = pdf_to_image(reference, page)
    diff = ImageChops.difference(gen_img, ref_img)
    # Bereken similarity percentage
    return 1.0 - (sum(diff.getdata()) / (255 * pixels))
```

| + | - |
|---|---|
| Objectieve verificatie | Vereist nog steeds handmatig corrigeren |
| Kan in CI/CD pipeline | Traag iteratief proces |
| Werkt voor elke pagina type | Geen automatische fix |

**Verdict:** ⚠️ Waardevol als verificatie-tool, maar geen oplossing op zich.

---

### Optie D: Hybride — Stationery + coded dynamic zones + visuele diff

**Wat:** Combineer B en C:
- **Statische pagina's** (cover, backcover, bijlage-divider): Stationery PDF
- **Semi-dynamische pagina's** (colofon): Stationery + tekst-zones
- **Dynamische pagina's** (content): Coded met header/footer templates
- **Verificatie**: Visuele diff tool voor quality assurance

Dit is de architectuur die professionele publishing systemen (InDesign Server, Prince XML) ook gebruiken.

| + | - |
|---|---|
| Pixel-perfect voor statische pagina's | Meer werk upfront |
| Flexibel voor dynamische content | Stationery extractie moet goed werken |
| Verifieerbaar via diff tool | |
| Schaalt naar nieuwe bureaus | |

**Verdict:** ✅✅ Beste langetermijn-oplossing.

---

## Aanbevolen aanpak: Optie D (Hybride)

### Fase 1: Stationery extractie repareren (1-2 uur)

De `StationeryExtractor` bestaat al maar wordt niet goed gebruikt. Fix:

1. **Extraheer cover als complete PDF-pagina** (zonder tekst-stripping)
   - Verwijder alleen: projecttitel, subtitel (dynamische velden)
   - Behoud: logo, paars vlak, badges, "Ontdek ons", geometrische vormen
   
2. **Extraheer colofon als stationery** (strip alle veldwaarden)
   - Behoud: layout-structuur, turquoise footer-blok, logo, lijnen
   - Verwijder: alle veldwaarden (project, datum, etc.)

3. **Extraheer backcover als complete pagina** (geen dynamische content)

4. **Extraheer bijlage-divider** (strip nummer + titel)

5. **Content pagina**: geen stationery nodig (alleen footer met paginanummer)

### Fase 2: Renderer refactoren naar stationery-first (2-3 uur)

Wijzig `special_pages.py` zodat het stationery PDFs als achtergrond gebruikt:

```python
def draw_cover_page(canvas, doc, config, brand, cover_image=None):
    # 1. Teken stationery als achtergrond
    stationery_path = brand.resolve_stationery("cover")
    if stationery_path:
        canvas.drawImage(str(stationery_path), 0, 0, pw, ph)
    
    # 2. Leg dynamische tekst er overheen
    for zone in brand.pages["cover"]["text_zones"]:
        draw_text_zone(canvas, zone, config)
    
    # 3. Optioneel: projectfoto in clip-zone
    if cover_image:
        draw_clipped_photo(canvas, cover_image, brand)
```

### Fase 3: YAML herstructureren (1 uur)

Vereenvoudig de YAML van 200+ regels geometrie-definities naar:

```yaml
pages:
  cover:
    stationery: "stationery/cover.pdf"
    text_zones:
      - name: "title"
        x_pt: 54.28
        y_pt: 93.47      # top-down referentie
        max_width_pt: 480
        font: "$heading"
        size: 28.9
        color: "$primary"
      - name: "subtitle"
        x_pt: 55.0
        y_pt: 63.0
        max_width_pt: 480
        font: "$body"
        size: 17.8
        color: "$secondary"
    photo_zone:
        clip_polygon: [...]  # alleen nodig als cover foto gewenst
        rect: [55.6, 161.6, 484.0, 560.8]
```

**Alle polygonen, badges, logo-posities, geometrische vormen VERDWIJNEN uit de YAML** — ze zitten in de stationery PDF.

### Fase 4: Visuele diff tool (1 uur)

Script `tools/visual_diff.py`:

```python
def compare_pages(generated: Path, reference: Path) -> list[PageDiff]:
    """Vergelijk alle pagina's, rapporteer similarity scores."""
    results = []
    for page_num in range(num_pages):
        gen = render_page(generated, page_num)
        ref = render_page(reference, page_num)
        score = structural_similarity(gen, ref)
        diff_image = create_diff_overlay(gen, ref)
        results.append(PageDiff(page_num, score, diff_image))
    return results
```

Output: per pagina een similarity score + verschil-overlay afbeelding.

### Fase 5: Workflow voor nieuw bureau documenteren (30 min)

```
NIEUW BUREAU TOEVOEGEN:
1. Verzamel referentie-rapport + logo's + fonts
2. Run: python -m openaec_reports.tools extract-stationery rapport.pdf --output brands/nieuw-bureau/
3. Definieer tekst-zones in YAML (alleen dynamische velden)
4. Run: python -m openaec_reports.tools visual-diff --reference rapport.pdf --generated test.pdf
5. Itereer tot similarity > 95% per pagina
```

---

## Tijdsinschatting

| Fase | Uur | Prioriteit |
|------|-----|-----------|
| 1: Stationery extractie fix | 1-2 | 🔴 Hoog |
| 2: Renderer refactor | 2-3 | 🔴 Hoog |
| 3: YAML herstructureren | 1 | 🔴 Hoog |
| 4: Visuele diff tool | 1 | 🟡 Middel |
| 5: Documentatie | 0.5 | 🟢 Laag |
| **Totaal** | **5.5-7.5** | |

---

## Wat dit oplevert

**Nu:** 200+ regels coördinaat-spaghetti in YAML → visueel incorrect resultaat
**Straks:** ~30 regels tekst-zones in YAML + stationery PDF → pixel-perfect resultaat

**Nu:** Nieuw bureau = weken handmatig coördinaten meten
**Straks:** Nieuw bureau = stationery extraheren + 10 tekst-zones definiëren = 1 uur

**Nu:** Geen verificatie mogelijk
**Straks:** Visuele diff tool geeft objectieve score per pagina
