# PROMPT B-FINAL: Backend Afronding — renderer_v2 completeren + FastAPI + tests

## Context

Je werkt in `X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator`.

Er is een werkende **Proof of Concept** in `src/bm_reports/core/renderer_v2.py` die JSON → PDF genereert via PyMuPDF + ReportLab. Deze module genereert pixel-perfect 3BM huisstijl rapporten (bewezen met 10-pagina integratietest). 

De oude engine (`engine.py`) is volledig ReportLab-based en wordt NIET meer gebruikt. De nieuwe renderer_v2 is de productie-engine.

## Doel

Maak de backend **productierijp** in 3 stappen:

---

## STAP 1: renderer_v2.py completeren met ontbrekende block types

### Huidige staat
De `ContentRenderer` class in `renderer_v2.py` ondersteunt nu:
- `heading_1`, `heading_2`, `paragraph`, `bullet_list`

### Toe te voegen block types

**1a. Table rendering**
- Gebruik de styling uit `content_styles.yaml` → `blocks.table`:
  - Header: GothamBook 12pt, witte tekst (#FFFFFF) op teal achtergrond (#56B49B), hoogte 24pt
  - Body: GothamBook 9pt, #401246, regelafstand 20.8pt
  - x: 125.4, max_width: 415.9
- Render via PyMuPDF rectangles (header bg) + insert_text (cellen)
- Auto column width: verdeel max_width evenredig over kolommen, tenzij `column_widths` opgegeven
- JSON input format:
```json
{"type": "table", "title": "Overzicht", "headers": ["Kolom 1", "Kolom 2"], "rows": [["cel 1", "cel 2"]], "column_widths": null}
```

**1b. Image blocks**
- Accepteert `src` als bestandspad (string) of base64 dict `{"data": "...", "media_type": "image/png"}`
- Bij base64: schrijf naar temp file, insert in PDF
- Gebruik `page.insert_image()` in PyMuPDF
- Pas in content area (x=125.4, max_width=415.9), behoud aspect ratio
- Optionele `caption` onder afbeelding in 8pt GothamBook #401246 italic
- JSON input format:
```json
{"type": "image", "src": "path/to/image.png", "caption": "Figuur 1", "width_mm": 120}
```

**1c. Spacer block**
- Simpel: verhoog self.y met opgegeven hoogte
```json
{"type": "spacer", "height_mm": 10}
```

**1d. Page break block**
- Finaliseer huidige pagina (paginanummer) en start nieuwe pagina
```json
{"type": "page_break"}
```

**1e. Calculation block** (engineering specifiek)
- Render als gestructureerd blok met:
  - Titel in GothamBold 9.5pt
  - Formula + substitution in GothamBook 9.5pt  
  - Result met unit, eventueel reference
  - Achtergrond: licht grijs (#F5F5F5) rectangle
- JSON input:
```json
{"type": "calculation", "title": "Buigend moment", "formula": "M = q × l² / 8", "substitution": "M = 8.5 × 6.0² / 8", "result": "38.3", "unit": "kNm", "reference": "NEN-EN 1992-1-1 §6.1"}
```

**1f. Check block** (toetsing voldoet/voldoet niet)
- Render als gestructureerd blok met:
  - Beschrijving, required vs calculated value
  - Unity check waarde + groen/rood indicator
  - "VOLDOET" in groen (#56B49B) of "VOLDOET NIET" in rood (#FF0000)
- JSON input:
```json
{"type": "check", "description": "Buigend moment", "required_value": "38.3 kNm", "calculated_value": "32.1 kNm", "unity_check": 0.84, "result": "VOLDOET"}
```

### Implementatie-eisen
- Voeg alle block types toe aan `ContentRenderer._render_block()` dispatch
- Elke block method moet `_check_overflow()` gebruiken voor page breaks
- Gebruik `self.fonts.wrap_text()` voor text wrapping (accurate Gotham meting)
- Houd de YAML-driven aanpak: lees styling uit `self.blocks` dict

---

## STAP 2: FastAPI api.py updaten naar renderer_v2

### Huidige staat
`api.py` bestaat al met endpoints maar roept de OUDE `engine.py` aan via `Report.from_dict()`.

### Wijzigingen

**2a. `/api/generate` endpoint updaten:**
- Vervang `Report.from_dict()` + `report.build()` door `ReportGeneratorV2`
- De stationery directory moet configureerbaar zijn via environment variable:
  ```python
  STATIONERY_DIR = Path(os.environ.get(
      "BM_STATIONERY_DIR",
      str(Path(__file__).parent / "assets" / "stationery" / "3bm_cooperatie")
  ))
  ```
- Kopieer de stationery bestanden (colofon.pdf, standaard.pdf, bijlagen.pdf, achterblad.pdf, cover PNG) naar `src/bm_reports/assets/stationery/3bm_cooperatie/`
- JSON body gaat direct naar `generator.generate(data, stationery_dir, tmp_path)`

**2b. `/api/generate/v2` nieuw endpoint (naast bestaand):**
- Laat het oude `/api/generate` endpoint OOK bestaan voor backward compatibility
- Voeg `/api/generate/v2` toe die exclusief renderer_v2 gebruikt
- Accepteert dezelfde JSON body als het test bestand `tests/test_data/sample_report.json`

**2c. Image upload support:**
- Voeg een `/api/upload` endpoint toe voor het uploaden van afbeeldingen (cover foto, content images)
- Sla uploads op in een temp directory
- Return een pad dat in de JSON als `src` gebruikt kan worden
- Multipart form data met file upload

**2d. Stationery discovery endpoint:**
- `/api/stationery` — retourneer beschikbare brands en hun stationery status
- Check of alle benodigde bestanden aanwezig zijn per brand

### Code structuur:
```python
from bm_reports.core.renderer_v2 import ReportGeneratorV2

@app.post("/api/generate/v2")
async def generate_report_v2(request: Request):
    data = await request.json()
    generator = ReportGeneratorV2(brand=data.get("brand", "3bm_cooperatie"))
    # ... generate + return PDF
```

---

## STAP 3: Tests

### 3a. Unit tests voor renderer_v2 block types
Bestand: `tests/test_renderer_v2_blocks.py`
- Test elke block type individueel (paragraph, bullet_list, table, image, etc.)
- Verifieer dat PDF gegenereerd wordt zonder errors
- Check page count logica (overflow → nieuwe pagina)

### 3b. Integration test update
Update `tests/test_renderer_v2.py` (bestaand):
- Voeg table, image, calculation, check blocks toe aan sample_report.json
- Verifieer dat het volledige rapport genereert

### 3c. API endpoint tests
Bestand: `tests/test_api_v2.py`
- Gebruik `httpx` + `fastapi.testclient`
- Test `/api/health`, `/api/generate/v2`, `/api/stationery`
- Test met dezelfde sample_report.json

### 3d. Update sample_report.json
Voeg aan `tests/test_data/sample_report.json` toe:
- Een table block in hoofdstuk 2 (belastingoverzicht)
- Een calculation block in hoofdstuk 3
- Een check block in hoofdstuk 3
- Een spacer block
- Zodat alle block types getest worden

---

## Technische eisen

### Dependencies
- `pymupdf` (fitz) moet naar `dependencies` in pyproject.toml (staat nu onder `[project.optional-dependencies] brand-tools`)
- Verwijder `pdfrw` (niet meer nodig)

### Font paden
Fonts staan in: `src/bm_reports/assets/fonts/` (Gotham-Bold.ttf, Gotham-Book.ttf, Gotham-Medium.ttf)
De `FontManager` class in renderer_v2.py resolved dit automatisch via `FONT_DIR = ASSETS_DIR / "fonts"`

### Stationery bestanden
Kopieer van `huisstijl/paginas/` naar `src/bm_reports/assets/stationery/3bm_cooperatie/`:
- `colofon.pdf`
- `standaard.pdf`  
- `bijlagen.pdf`
- `achterblad.pdf`
- `2707_BBLrapportage_v01_1.png` (cover overlay)

### YAML templates
Staan al op de juiste plek: `src/bm_reports/assets/templates/3bm_cooperatie/`
- cover.yaml, colofon.yaml, toc.yaml, standaard.yaml, content_styles.yaml, bijlage.yaml

### Exports
Update `src/bm_reports/__init__.py`:
```python
from bm_reports.core.renderer_v2 import ReportGeneratorV2
__all__ = [..., "ReportGeneratorV2"]
```

---

## NIET doen
- Raak de frontend NIET aan (die komt later)
- Raak de oude engine.py NIET aan (backward compatibility)
- Maak GEEN nieuwe YAML templates — die zijn af
- Maak GEEN wijzigingen aan font bestanden
- Wijzig NIET de bestaande report.schema.json — de V2 renderer heeft zijn eigen JSON format

## Volgorde van uitvoering
1. Kopieer stationery bestanden naar assets
2. Update pyproject.toml dependencies
3. Completeer renderer_v2.py met alle block types
4. Update api.py met v2 endpoints
5. Update sample_report.json met alle block types  
6. Schrijf en run tests
7. Update __init__.py exports

## Verificatie
Na afloop moet dit werken:
```bash
cd X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator
python tests/test_renderer_v2.py          # Genereert PDF met alle block types
python -m pytest tests/ -v                 # Alle tests groen
python -m bm_reports.api                   # Server start op :8000
# POST naar http://localhost:8000/api/generate/v2 met sample JSON → PDF response
```
