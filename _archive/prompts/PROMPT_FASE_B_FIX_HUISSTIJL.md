# Fase B-fix: Pixel-perfect Huisstijl Correcties

## Probleemanalyse

Er zijn **6 concrete bugs** die samen verklaren waarom de PDF output niet overeenkomt met het referentiedocument (`2707_BBLrapportage_v01.pdf`). Ze zijn geordend op impact.

---

## Bug 1: Brand YAML gebruikt Helvetica i.p.v. Gotham fonts [KRITIEK]

**Bestand:** `src/openaec_reports/assets/brands/3bm_cooperatie.yaml`

**Probleem:** De `fonts:` sectie verwijst naar Helvetica-fallbacks, terwijl Gotham fonts WEL beschikbaar zijn in `assets/fonts/`.

**Huidig (FOUT):**
```yaml
fonts:
  heading: "Helvetica-Bold"
  body: "Helvetica"
```

**Moet worden:**
```yaml
fonts:
  heading: "GothamBold"
  body: "GothamBook"
  medium: "GothamMedium"
  italic: "GothamBookItalic"
```

**Waarom dit ertoe doet:** De `BrandRenderer._resolve_font("$body")` lookup retourneert `brand.fonts["body"]` → `"Helvetica"`. Hierdoor wordt ALLE tekst in header/footer met Helvetica getekend in plaats van Gotham. De `special_pages.py` `_resolve_font()` probeert WEL eerst Gotham via `get_font_name()`, maar die flow wordt niet consistent gevolgd overal.

---

## Bug 2: Stylesheet defaults matchen niet met huisstijl [KRITIEK]

**Bestand:** `src/openaec_reports/core/styles.py`

**Probleem:** `FontConfig` en de `create_stylesheet()` gebruiken verkeerde font sizes en font names.

### 2a. FontConfig defaults

**Huidig (FOUT):**
```python
body_size: float = 9.0        # Moet 9.5
heading1_size: float = 16.0   # Moet 18.0
```

**Fix:**
```python
body_size: float = 9.5
heading1_size: float = 18.0
```

### 2b. Heading1 font

**Huidig (FOUT):** Heading1 gebruikt `BM_FONTS.heading` → **GothamBold**  
**Moet:** Heading1 gebruikt `BM_FONTS.body` → **GothamBook** (NOT Bold!)

Zie HUISSTIJL_SPEC.md §4.4: "Font: Gotham-Book (NIET Bold!)"

**Fix in `create_stylesheet()`:**
```python
styles.add(ParagraphStyle(
    name="Heading1",
    parent=styles["Normal"],
    fontName=BM_FONTS.body,        # Was: BM_FONTS.heading — FOUT!
    fontSize=BM_FONTS.heading1_size,
    leading=BM_FONTS.heading1_size * 1.3,
    textColor=HexColor(BM_COLORS.text),  # Was: BM_COLORS.primary — subtiel verschil
    spaceBefore=12,
    spaceAfter=6,
))
```

### 2c. Heading2 kleur

**Huidig (FOUT):** `textColor=HexColor(BM_COLORS.primary)` → #40124A  
**Moet:** `textColor=HexColor("#56B49B")` (licht turquoise, NIET #38BDA0)

Zie HUISSTIJL_SPEC.md §4.5: "Kleur: #56B49B"

**Fix:**
```python
styles.add(ParagraphStyle(
    name="Heading2",
    parent=styles["Normal"],
    fontName=BM_FONTS.body,        # Was: BM_FONTS.heading — FOUT!
    fontSize=BM_FONTS.heading2_size,
    leading=BM_FONTS.heading2_size * 1.3,
    textColor=HexColor("#56B49B"),  # Was: BM_COLORS.primary
    spaceBefore=10,
    spaceAfter=4,
))
```

### 2d. Heading3 font

Zelfde patroon: Heading3 moet ook `BM_FONTS.body` gebruiken, niet `BM_FONTS.heading`.

---

## Bug 3: Brand style overrides worden nooit toegepast [KRITIEK]

**Bestand:** `src/openaec_reports/core/styles.py`

**Probleem:** De globale `BM_STYLES` wordt aangemaakt zonder brand:
```python
BM_STYLES = create_stylesheet()  # brand=None, dus overrides worden geskipt
```

De `create_stylesheet(brand)` functie ondersteunt WEL brand overrides, maar die wordt nergens aangeroepen met een actual brand.

**Twee opties:**

### Optie A (minimaal): Fix de defaults zodat ze matchen
Als de FontConfig en create_stylesheet defaults al correct zijn (na Bug 2 fixes), dan zijn brand overrides minder urgent. De `brand.styles` sectie in de YAML dient dan als documentatie/override voor toekomstige andere brands.

### Optie B (robuust): Report class gebruikt brand-aware stylesheet
In de `Report` class (of waar de stylesheet wordt geconsumeerd), vervang:
```python
# Huidig
from openaec_reports.core.styles import BM_STYLES
stylesheet = BM_STYLES

# Nieuw
from openaec_reports.core.styles import create_stylesheet
stylesheet = create_stylesheet(brand=self.brand)
```

**Aanbeveling:** Doe BEIDE — fix de defaults (Bug 2) EN gebruik brand-aware stylesheet (Bug 3 optie B). Zoek in de codebase naar alle plekken waar `BM_STYLES` wordt gebruikt en vervang met `create_stylesheet(brand)`.

---

## Bug 4: Hardcoded kleuren in special_pages.py wijken af van YAML [MEDIUM]

**Bestand:** `src/openaec_reports/core/special_pages.py`

**Probleem:** Bovenaan staan hardcoded kleuren die NIET overeenkomen met de brand YAML:

```python
_COLOR_PRIMARY = HexColor("#40124A")    # YAML: #401246  (verschil!)
_COLOR_SECONDARY = HexColor("#38BDA0")  # YAML: #38BDAB  (verschil!)
```

Dit zijn subtiele maar zichtbare kleurverschillen (de 'A' vs '6' en '0' vs 'B' aan het eind).

**Fix — twee stappen:**

### 4a. Corrigeer de hardcoded waarden als fallback
```python
_COLOR_PRIMARY = HexColor("#401246")
_COLOR_SECONDARY = HexColor("#38BDAB")
```

### 4b. Gebruik altijd brand kleuren
De `draw_cover_page()` doet dit al deels met `_brand_color(brand, "primary", "#401246")`, maar sommige plekken gebruiken nog de hardcoded `_COLOR_PRIMARY` / `_COLOR_TEXT` etc.

**Zoek en vervang alle directe referenties naar `_COLOR_PRIMARY`, `_COLOR_SECONDARY`, `_COLOR_TEXT` in:**
- `_draw_badges()` → gebruikt `_BADGE_TEXT_DARK` = `_COLOR_PRIMARY` (fout)
- `_draw_revision_table()` → gebruikt `_COLOR_TEXT` direct
- `draw_backcover_page()` → gebruikt `_COLOR_WHITE` + `_COLOR_TEXT` direct

**Strategie:** Geef `brand` als parameter mee aan alle helper functies en resolve kleuren via `_brand_color()`.

---

## Bug 5: Cover logo positie en grootte [MEDIUM]

**Bestand:** `src/openaec_reports/core/special_pages.py` → `draw_cover_page()`

**Probleem:** De logo rendering gebruikt alleen `width` maar niet `height`. ReportLab's `preserveAspectRatio` is impliciet True maar het anker (x,y) is de linkeronderhoek. Als het logo te groot/klein is of verkeerd gepositioneerd, ligt het aan:

1. **Logo bestand kwaliteit** — Is `3bm-cooperatie-wit.png` het juiste bestand? Check of het transparante achtergrond heeft.
2. **Positionering** — `x=62, y=775` in A4 reference coords, geschaald via `_sxy()`. Dit plaatst het logo linksboven in het paarse vlak. Verifieer visueel.
3. **Logo width** — `w=100` pt (≈35mm). Als het logo er te klein/groot uitziet, pas deze waarde aan.

**Verificatie stap:** Genereer een test PDF en vergelijk de logo positie + grootte met pagina 1 van het referentiedocument. Eventueel fine-tunen op 5-10pt.

---

## Bug 6: Backcover geometrie wijkt af [LOW]

**Bestand:** `src/openaec_reports/core/special_pages.py` → `draw_backcover_page()`

**Probleem:** De backcover gebruikt een vereenvoudigd wit polygon en paars driehoek. Het referentiedocument heeft een complexer geometrisch patroon met schuine lijnen. 

De huidige polygonen:
```python
_WHITE_POLY = [(0,0), (0,698), (268,842), (432,842), ...]  # Vereenvoudigd
_PURPLE_TRI = [(0,842), (0,539), (170,688), (170,842)]     # Rechthoek, geen driehoek
```

Dit is een visueel verschil maar minder kritiek dan fonts/kleuren. Kan later geoptimaliseerd worden door de exacte coördinaten uit de referentie PDF te extraheren.

---

## Uitvoeringsplan

### Stap 1: Brand YAML fonts fixen (Bug 1)
Wijzig `src/openaec_reports/assets/brands/3bm_cooperatie.yaml`:
- `fonts.heading` → `"GothamBold"`
- `fonts.body` → `"GothamBook"`
- Voeg `medium: "GothamMedium"` en `italic: "GothamBookItalic"` toe

### Stap 2: styles.py defaults fixen (Bug 2)
Wijzig `src/openaec_reports/core/styles.py`:
- `body_size` → 9.5
- `heading1_size` → 18.0
- Heading1: `fontName=BM_FONTS.body`, `textColor=HexColor(BM_COLORS.text)`
- Heading2: `fontName=BM_FONTS.body`, `textColor=HexColor("#56B49B")`
- Heading3: `fontName=BM_FONTS.body`

### Stap 3: Brand-aware stylesheet (Bug 3)
- Zoek alle `from openaec_reports.core.styles import BM_STYLES` usages
- Vervang met `create_stylesheet(brand=...)` waar brand beschikbaar is
- Houd `BM_STYLES` als fallback voor code zonder brand context

### Stap 4: Hardcoded kleuren fixen (Bug 4)
Wijzig `src/openaec_reports/core/special_pages.py`:
- Corrigeer `_COLOR_PRIMARY` → `#401246`
- Corrigeer `_COLOR_SECONDARY` → `#38BDAB`
- Geef `brand` parameter mee aan `_draw_badges()` en andere helpers
- Vervang directe kleur-referenties met `_brand_color()` calls

### Stap 5: Visuele verificatie
1. Genereer `voorbeeld_rapport_v2.pdf` via `huisstijl/generate_example.py`
2. Open naast `2707_BBLrapportage_v01.pdf` en vergelijk:
   - [ ] Cover: fonts (Gotham, niet Helvetica)
   - [ ] Cover: logo positie en grootte
   - [ ] Cover: titel font size (28.9pt GothamBold)
   - [ ] Cover: subtitle kleur (#38BDAB turquoise)
   - [ ] Content: H1 = GothamBook 18pt, kleur #45243D
   - [ ] Content: H2 = GothamBook 13pt, kleur #56B49B
   - [ ] Content: body = GothamBook 9.5pt, kleur #45243D
   - [ ] Content footer: ALLEEN paginanummer rechtsonder (geen turquoise blok)
   - [ ] Colofon: labels + waarden in juiste fonts/kleuren
   - [ ] Badge kleuren op cover
3. Fine-tune afmetingen indien nodig

### Stap 6: BM_COLORS bijwerken (optioneel)
De `Colors` dataclass in styles.py heeft ook afwijkende defaults:
```python
primary: str = "#40124A"   # Moet: #401246
secondary: str = "#38BDA0" # Moet: #38BDAB
```

---

## Referentie: Correcte huisstijl waarden

### Kleuren
| Naam | Hex | Gebruik |
|------|-----|---------|
| primary | #401246 | Cover paars vlak, titels, labels |
| secondary | #38BDAB | Cover subtitle, colofon labels/footer |
| text | #45243D | Body tekst, H1 heading, paginanummers |
| text_accent | #56B49B | H2 heading, TOC chapters |
| badge_gold | #F0C385 | MEEDENKEN badge |
| badge_turquoise | #37BCAB | PRAKTISCH badge, bijlage achtergrond |
| badge_coral | #E1574B | BETROUWBAAR badge |

### Fonts
| Context | Font | Size |
|---------|------|------|
| Body tekst | GothamBook | 9.5pt |
| Heading 1 | GothamBook (NIET Bold!) | 18pt |
| Heading 2 | GothamBook | 13pt |
| Cover titel | GothamBold | 28.9pt |
| Cover subtitle | GothamBook | 17.8pt |
| Colofon labels | GothamBold | 10pt |
| Colofon waarden | GothamBook | 10pt |
| Paginanummer | GothamBook | 9.5pt |

### Content marges (in pt)
| Marge | Waarde |
|-------|--------|
| Links | 90.0 |
| Rechts | 53.7 (= 595.3 - 541.6) |
| Boven | ~74.9 |
| Onder | ~38.9 |

---

## Appendix: Bestanden die BM_STYLES en BM_COLORS gebruiken

### BM_STYLES referenties (23 hits — moeten brand-aware worden)
| Bestand | Gebruik |
|---------|---------|
| `components/calculation.py` | `BM_STYLES["Normal"]` als parent voor lokale styles |
| `components/check_block.py` | `BM_STYLES["Normal"]` als parent |
| `components/image_block.py` | `BM_STYLES["Caption"]` |
| `components/map_block.py` | `BM_STYLES["Caption"]`, `BM_STYLES["Normal"]` |
| `core/block_registry.py` | `ss = styles or BM_STYLES` — hier wordt de stylesheet doorgegeven |
| `core/engine.py` | Importeert `BM_STYLES` + `create_stylesheet` |

**Strategie:** De `block_registry.py` is de sleutel — die accepteert al een `styles` parameter. De `engine.py` moet `create_stylesheet(brand)` aanroepen en doorgeven.

### BM_COLORS referenties (38 hits — hex waarden moeten kloppen)
| Bestand | Meest gebruikte kleuren |
|---------|------------------------|
| `components/calculation.py` | `primary`, `text_light`, `secondary`, `background_alt`, `rule` |
| `components/check_block.py` | `text`, `text_light`, `accent`, `warning`, `rule`, `background_alt` |
| `components/map_block.py` | `text_light`, `secondary`, `rule` |
| `components/table_block.py` | `primary` (header bg), `text`, `rule`, `background_alt` |
| `core/toc.py` | `secondary` (TOC entries) |
| `core/styles.py` | Alle kleuren in stylesheet definitie |

**Minimale fix:** Corrigeer de `Colors` dataclass defaults:
```python
primary: str = "#401246"       # Was: #40124A
secondary: str = "#38BDAB"     # Was: #38BDA0
```

Dit fixt meteen alle 38 referenties zonder code wijzigingen in de componenten.
