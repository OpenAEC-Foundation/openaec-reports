# Fase B3: Template → JSON Scaffold & Landschapsmodus

## Context

`TemplateLoader` kan YAML templates lezen (`structural_report.yaml`, `3bm_cooperatie.yaml`), maar er is geen mechanisme om een template om te zetten naar een **leeg JSON scaffold** dat de frontend kan laden als startpunt. Daarnaast wordt `orientation: landscape` in `DocumentConfig` niet doorvertaald naar de page size.

Bekijk voor je begint:
- `src/bm_reports/core/template_loader.py` — `TemplateLoader`, `TemplateConfig`
- `src/bm_reports/core/engine.py` — `Report.from_dict()`
- `src/bm_reports/core/document.py` — `DocumentConfig`, `PageFormat`, `A4`, `A3`
- `src/bm_reports/api.py` — (na Fase B2) het scaffold endpoint placeholder
- `src/bm_reports/assets/templates/structural_report.yaml` — voorbeeld template
- `schemas/report.schema.json` — het JSON schema

## Deel 1: Template Scaffold Generator

### Wat moet er komen

Voeg een methode toe aan `TemplateLoader` die een template vertaalt naar een leeg JSON object conform `report.schema.json`:

```python
# In template_loader.py

class TemplateLoader:
    ...
    
    def to_scaffold(self, name: str) -> dict[str, Any]:
        """Genereer een leeg JSON scaffold vanuit een template.
        
        Het scaffold bevat:
        - Alle metadata velden met defaults uit het template
        - Cover/colofon/toc/backcover configuratie
        - Lege secties op basis van de template structure
        - Placeholder waarden voor verplichte velden
        
        Args:
            name: Template naam.
            
        Returns:
            Dict conform report.schema.json, klaar voor de frontend.
        """
```

### Scaffold structuur

Gegeven `structural_report.yaml`, moet `to_scaffold("structural_report")` dit retourneren:

```json
{
    "template": "structural_report",
    "format": "A4",
    "orientation": "portrait",
    "project": "",
    "project_number": "",
    "client": "",
    "author": "3BM Bouwkunde",
    "date": "2026-02-19",
    "version": "1.0",
    "status": "CONCEPT",
    "report_type": "structural",
    "cover": {
        "subtitle": ""
    },
    "colofon": {
        "enabled": true,
        "extra_fields": {},
        "revision_history": [
            {
                "version": "0.1",
                "date": "2026-02-19",
                "author": "",
                "description": "Eerste opzet"
            }
        ],
        "disclaimer": "Dit rapport is opgesteld door 3BM Bouwkunde en is uitsluitend bedoeld voor de opdrachtgever. Verspreiding aan derden is niet toegestaan zonder schriftelijke toestemming."
    },
    "toc": {
        "enabled": true,
        "title": "Inhoudsopgave",
        "max_depth": 3
    },
    "sections": [],
    "backcover": {
        "enabled": true
    },
    "metadata": {}
}
```

### Implementatie details

1. **Datum:** Gebruik `datetime.date.today().isoformat()` voor `date` en revision_history entry
2. **Disclaimer:** Haal uit template YAML (`colofon.disclaimer`). Als niet aanwezig, gebruik een standaard 3BM disclaimer
3. **Secties:** De `structure` lijst in de YAML bevat items als "cover", "colofon", "toc", "sections", "backcover". Filter op "sections" — deze zijn niet als pre-gedefinieerde secties bedoeld maar als placeholder. Retourneer een lege `sections: []` array
4. **Cover/colofon/toc/backcover:** Map de template settings naar schema-conforme objecten. Negeer styling properties (background_color, elements) — die worden door de brand/engine afgehandeld
5. **Verplichte velden:** `project` en `template` zijn required in het schema. Laat `project` leeg (de frontend vult dit in)

### Maak extra templates

Maak naast `structural_report.yaml` ook:

**`assets/templates/daylight.yaml`:**
```yaml
report_type: daylight
format: A4
orientation: portrait
cover:
  subtitle_hint: "Daglichtberekening"
colofon:
  enabled: true
  disclaimer: |
    Dit rapport is opgesteld door 3BM Bouwkunde en is uitsluitend
    bedoeld voor de opdrachtgever.
toc:
  enabled: true
  title: "Inhoudsopgave"
  max_depth: 2
backcover:
  enabled: true
structure:
  - cover
  - colofon
  - toc
  - sections
  - backcover
```

**`assets/templates/building_code.yaml`:**
```yaml
report_type: building_code
format: A4
orientation: portrait
cover:
  subtitle_hint: "Bouwbesluit toetsing"
colofon:
  enabled: true
toc:
  enabled: true
  title: "Inhoudsopgave"
  max_depth: 2
backcover:
  enabled: true
structure:
  - cover
  - colofon
  - toc
  - sections
  - backcover
```

**`assets/templates/blank.yaml`:**
```yaml
report_type: custom
format: A4
orientation: portrait
cover:
  subtitle_hint: ""
colofon:
  enabled: false
toc:
  enabled: false
backcover:
  enabled: false
structure:
  - sections
```

### API endpoint invullen

Pas het placeholder endpoint in `api.py` aan (uit Fase B2):

```python
@app.get("/api/templates/{name}/scaffold")
async def get_template_scaffold(name: str):
    """Retourneer een leeg JSON scaffold voor een template.
    
    De frontend kan dit laden als startpunt voor een nieuw rapport.
    """
    try:
        loader = TemplateLoader()
        scaffold = loader.to_scaffold(name)
        return scaffold
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Template '{name}' niet gevonden")
```

## Deel 2: Landscape oriëntatie fixen

### Probleem

`DocumentConfig` heeft een `orientation` field maar `Report.build()` negeert het. Als `orientation: landscape`, moeten width en height omgewisseld worden.

### Fix in `document.py`

Voeg een property toe aan `DocumentConfig` die de effectieve pagesize retourneert:

```python
@dataclass
class DocumentConfig:
    ...
    
    @property
    def effective_pagesize(self) -> tuple[float, float]:
        """Retourneer (width, height) in points, rekening houdend met oriëntatie."""
        if self.orientation == "landscape":
            return (self.format.height_pt, self.format.width_pt)
        return self.format.size_pt
    
    @property
    def effective_width_pt(self) -> float:
        return self.effective_pagesize[0]
    
    @property
    def effective_height_pt(self) -> float:
        return self.effective_pagesize[1]
```

### Fix in `engine.py`

In `Report.build()`, vervang:
```python
pagesize=config.format.size_pt,
```
door:
```python
pagesize=config.effective_pagesize,
```

### Fix in `engine.py` `from_dict()`

Voeg orientation parsing toe:
```python
# Na format bepalen:
orientation = data.get("orientation", "portrait")

report = cls(
    format=fmt,
    ...
)
report.document.config.orientation = orientation
```

**Let op:** `DocumentConfig` is momenteel een `@dataclass` zonder `frozen=True`, dus direct toewijzen werkt.

### Fix in special_pages.py

De special pages gebruiken `config.format.width_pt` en `config.format.height_pt`. Bij landscape moeten ze de effectieve afmetingen gebruiken. Vervang in alle drie de draw functies (`draw_cover_page`, `draw_colofon_page`, `draw_backcover_page`):

```python
# Oud:
pw = config.format.width_pt
ph = config.format.height_pt

# Nieuw:
pw = config.effective_width_pt
ph = config.effective_height_pt
```

Doe hetzelfde in `page_templates.py`:
```python
page_w = config.effective_width_pt
page_h = config.effective_height_pt
```

### Fix in brand_renderer.py

Check of `brand_renderer.py` ook `config.format.width_pt` gebruikt en vervang door `config.effective_width_pt`. (Lees het bestand eerst.)

## Deel 3: JSON Schema validatie verbeteren

### Probleem

`JsonAdapter.validate()` doet alleen simpele field checks ("project" en "project_number"). Het zou het volledige JSON schema moeten valideren.

### Fix in `json_adapter.py`

```python
import json
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent.parent.parent.parent / "schemas" / "report.schema.json"

class JsonAdapter:
    ...
    
    def validate(self) -> list[str]:
        """Valideer data tegen report.schema.json.
        
        Returns:
            Lijst van validatie fouten (leeg = geldig).
        """
        try:
            import jsonschema
        except ImportError:
            # Fallback: basis validatie als jsonschema niet geïnstalleerd
            return self._validate_basic()
        
        if not SCHEMA_PATH.exists():
            return self._validate_basic()
        
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        validator = jsonschema.Draft7Validator(schema)
        return [
            f"{'/'.join(str(p) for p in e.absolute_path)}: {e.message}"
            for e in validator.iter_errors(self.data)
        ]
    
    def _validate_basic(self) -> list[str]:
        """Basis validatie zonder jsonschema library."""
        errors = []
        if not self.data.get("project"):
            errors.append("Verplicht veld ontbreekt: 'project'")
        if not self.data.get("template"):
            errors.append("Verplicht veld ontbreekt: 'template'")
        return errors
```

## Tests

### test_template_scaffold.py

```python
def test_scaffold_has_required_fields():
    loader = TemplateLoader()
    scaffold = loader.to_scaffold("structural_report")
    assert scaffold["template"] == "structural_report"
    assert "project" in scaffold
    assert "sections" in scaffold
    assert isinstance(scaffold["sections"], list)

def test_scaffold_has_cover():
    loader = TemplateLoader()
    scaffold = loader.to_scaffold("structural_report")
    assert "cover" in scaffold
    assert "subtitle" in scaffold["cover"]

def test_scaffold_has_colofon_with_disclaimer():
    loader = TemplateLoader()
    scaffold = loader.to_scaffold("structural_report")
    assert scaffold["colofon"]["enabled"] is True
    assert len(scaffold["colofon"]["disclaimer"]) > 0

def test_scaffold_blank_template():
    loader = TemplateLoader()
    scaffold = loader.to_scaffold("blank")
    assert scaffold["colofon"]["enabled"] is False
    assert scaffold["toc"]["enabled"] is False
    assert scaffold["backcover"]["enabled"] is False

def test_scaffold_has_today_date():
    from datetime import date
    loader = TemplateLoader()
    scaffold = loader.to_scaffold("structural_report")
    assert scaffold["date"] == date.today().isoformat()

def test_scaffold_nonexistent_template():
    loader = TemplateLoader()
    with pytest.raises(FileNotFoundError):
        loader.to_scaffold("does_not_exist")
```

### test_landscape.py

```python
def test_landscape_effective_size():
    config = DocumentConfig(format=A4, orientation="landscape")
    assert config.effective_width_pt > config.effective_height_pt

def test_portrait_effective_size():
    config = DocumentConfig(format=A4, orientation="portrait")
    assert config.effective_height_pt > config.effective_width_pt

def test_landscape_build(tmp_path):
    report = Report(format=A4, project="Landscape Test", brand="3bm_cooperatie")
    report.document.config.orientation = "landscape"
    report.add_section("Test", content=["Landscape content."])
    output = tmp_path / "landscape.pdf"
    report.build(output)
    assert output.exists()

def test_from_dict_landscape(tmp_path):
    data = {
        "template": "structural",
        "project": "Landscape Dict Test",
        "format": "A4",
        "orientation": "landscape",
        "sections": [{"title": "Test", "content": [{"type": "paragraph", "text": "OK"}]}]
    }
    report = Report.from_dict(data)
    assert report.document.config.orientation == "landscape"
    output = tmp_path / "landscape_dict.pdf"
    report.build(output)
    assert output.exists()
```

### API test toevoegen (in test_api.py)

```python
def test_scaffold_endpoint():
    r = client.get("/api/templates/structural_report/scaffold")
    assert r.status_code == 200
    data = r.json()
    assert data["template"] == "structural_report"
    assert "sections" in data

def test_scaffold_404():
    r = client.get("/api/templates/nonexistent/scaffold")
    assert r.status_code == 404
```

## Verificatie

```bash
python -m pytest tests/test_template_scaffold.py tests/test_landscape.py -v
python -m pytest tests/ -v  # volledige regressie

# Handmatig:
python -c "
from bm_reports.core.template_loader import TemplateLoader
import json
loader = TemplateLoader()
for name in ['structural_report', 'daylight', 'building_code', 'blank']:
    scaffold = loader.to_scaffold(name)
    print(f'{name}: {json.dumps(scaffold, indent=2)[:200]}...')
"
```

## Volgorde

1. Template YAML bestanden aanmaken (daylight, building_code, blank)
2. `to_scaffold()` methode implementeren
3. Landscape fix (document.py → engine.py → special_pages.py → page_templates.py → brand_renderer.py)
4. JsonAdapter validatie upgrade
5. API endpoint invullen (als B2 al klaar is)
6. Tests
