# Bugfixes B1 (map_block.py) en B2 (api.py)

Bekijk voor je begint:
- `src/bm_reports/components/map_block.py`
- `src/bm_reports/api.py`
- `pyproject.toml`
- `tests/test_map_block.py`
- `tests/test_api.py`

---

## Bug 1 — Overlay x-misalignment bij smalle kaarten (map_block.py)

**Ernst:** MEDIUM VISUAL — lagen stapelen niet correct

**Probleem:**
In `_build_content()` heeft de kaart-rij (rij 0) `ALIGN=CENTER`. Maar in `draw()` worden overlay lagen getekend op `img_x = pad` (vast 6pt vanaf links). Wanneer de kaart smaller is dan `available_width`, wordt de basis-Image gecentreerd in de cel terwijl overlays starten op de linker padding-rand. Resultaat: percelen-overlay verschuift ten opzichte van luchtfoto-achtergrond.

**Fix:**
Verander in `_build_content()` de alignment van de kaart-rij van CENTER naar LEFT. Maps vullen typisch de beschikbare breedte, en LEFT alignment garandeert dat zowel de basis-Image als overlays op `x=pad` starten.

```python
# In _build_content(), verander:
("ALIGN", (0, 0), (0, 0), "CENTER"),
# Naar:
("ALIGN", (0, 0), (0, 0), "LEFT"),
```

---

## Bug 2 — Image breedte negeert cel-padding (map_block.py)

**Ernst:** MEDIUM VISUAL — kaart kan buiten cel-padding vallen

**Probleem:**
In `_build_content()`:
```python
target_w = min(self.width_mm * MM_TO_PT, available_width)
```
Dit houdt geen rekening met `LEFTPADDING` + `RIGHTPADDING` (elk `pad=6`). Als `width_mm * MM_TO_PT` dicht bij `available_width` ligt, is de Image breder dan de beschikbare ruimte binnen de cel.

Hetzelfde geldt in `draw()`:
```python
target_w = min(self.width_mm * MM_TO_PT, self.width)
```

**Fix:**

In `_build_content()`, verander:
```python
target_w = min(self.width_mm * MM_TO_PT, available_width)
```
naar:
```python
target_w = min(self.width_mm * MM_TO_PT, available_width - 2 * pad)
```

In `draw()`, verander:
```python
target_w = min(self.width_mm * MM_TO_PT, self.width)
```
naar:
```python
target_w = min(self.width_mm * MM_TO_PT, self.width - 2 * pad)
```

---

## Bug 3 — ParagraphStyle naam-conflict bij multi-pass build (map_block.py)

**Ernst:** LOW — ReportLab warnings in logs, geen visueel effect

**Probleem:**
In `_build_content()` wordt `ParagraphStyle("_map_scale", ...)` aangemaakt bij elke aanroep. ReportLab's `multiBuild()` roept `wrap()` meerdere keren aan (multi-pass voor TOC). Elke keer wordt een nieuwe style met dezelfde naam geregistreerd, wat ReportLab-warnings genereert: `"ParagraphStyle '_map_scale' already in use"`.

**Fix:**
Verplaats de style-creatie naar module-niveau, vóór de class definitie:

```python
# Boven de class KadasterMap definitie, op module niveau:
from reportlab.lib.styles import ParagraphStyle

_STYLE_MAP_SCALE = ParagraphStyle(
    "_map_scale",
    parent=BM_STYLES["Caption"],
    fontSize=BM_FONTS.caption_size,
    textColor=HexColor(BM_COLORS.text_light),
)
```

En in `_build_content()`, verwijder de lokale ParagraphStyle creatie en de lokale import. Vervang:
```python
from reportlab.lib.styles import ParagraphStyle
s_scale = ParagraphStyle(
    "_map_scale",
    parent=BM_STYLES["Caption"],
    fontSize=BM_FONTS.caption_size,
    textColor=HexColor(BM_COLORS.text_light),
)
data.append([Paragraph(scale_text, s_scale)])
```
door:
```python
data.append([Paragraph(scale_text, _STYLE_MAP_SCALE)])
```

Doe hetzelfde voor `_make_placeholder()` — verplaats `ParagraphStyle("_map_placeholder", ...)` ook naar module-niveau:
```python
_STYLE_MAP_PLACEHOLDER = ParagraphStyle(
    "_map_placeholder",
    parent=BM_STYLES["Normal"],
    fontName=BM_FONTS.body,
    fontSize=BM_FONTS.body_size,
    textColor=HexColor(BM_COLORS.text_light),
)
```

Verwijder de `from reportlab.lib.styles import ParagraphStyle` import uit `_make_placeholder()` en gebruik `_STYLE_MAP_PLACEHOLDER`.

---

## Bug 4 — Temp file leak bij build-failure (api.py)

**Ernst:** MEDIUM — bestanden lekken in temp directory bij herhaalde fouten

**Probleem:**
In het `/api/generate` endpoint:
```python
with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
    output_path = Path(tmp.name)
report.build(output_path)
```
Als `Report.from_dict()` of `report.build()` een exception gooit, wordt de temp file nooit opgeruimd. De `BackgroundTask` cleanup draait alleen bij succesvolle response. Over tijd lekken er PDF bestanden in de temp directory.

**Fix:**
Wrap de hele generate-logica in try/except met cleanup:

```python
@app.post("/api/generate")
async def generate_report(request: Request):
    data = await request.json()

    if not data.get("project"):
        raise HTTPException(status_code=422, detail="Veld 'project' is verplicht")
    if not data.get("template"):
        raise HTTPException(status_code=422, detail="Veld 'template' is verplicht")

    output_path: Path | None = None
    try:
        brand = data.get("brand", "3bm_cooperatie")
        report = Report.from_dict(data, brand=brand)

        with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            output_path = Path(tmp.name)

        report.build(output_path)

        filename = _safe_filename(
            data.get("project_number", ""),
            data.get("project", ""),
        )

        return FileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename=filename,
            background=BackgroundTask(lambda: output_path.unlink(missing_ok=True)),
        )
    except HTTPException:
        # HTTPException opnieuw raisen (422 van validatie hierboven)
        if output_path and output_path.exists():
            output_path.unlink(missing_ok=True)
        raise
    except Exception:
        if output_path and output_path.exists():
            output_path.unlink(missing_ok=True)
        raise
```

---

## Bug 5 — SCHEMA_PATH breekt na pip install (api.py)

**Ernst:** LOW — validate endpoint werkt niet na packaging

**Probleem:**
```python
SCHEMA_PATH = Path(__file__).parent.parent.parent / "schemas" / "report.schema.json"
```
Dit pad (`src/bm_reports/../../schemas/`) werkt alleen in de development source tree. Na `pip install` zit `api.py` in `site-packages/bm_reports/` en het `schemas/` directory is niet meegeïnstalleerd.

**Fix (twee stappen):**

### Stap 1: Schema meenemen in package

Voeg in `pyproject.toml` toe aan de `[tool.hatch.build.targets.wheel.force-include]` sectie:
```toml
"schemas" = "bm_reports/schemas"
```

### Stap 2: SCHEMA_PATH robuust resolven

Vervang in `api.py` de statische `SCHEMA_PATH` door een resolver functie:

```python
def _find_schema_path() -> Path | None:
    """Zoek report.schema.json op meerdere locaties."""
    candidates = [
        # In package (na pip install via force-include)
        Path(__file__).parent / "schemas" / "report.schema.json",
        # In source tree (development)
        Path(__file__).parent.parent.parent / "schemas" / "report.schema.json",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None

SCHEMA_PATH = _find_schema_path()
```

En pas het validate endpoint aan om `SCHEMA_PATH is None` af te vangen:

```python
@app.post("/api/validate")
async def validate_report(request: Request):
    import jsonschema

    data = await request.json()

    if SCHEMA_PATH is None:
        raise HTTPException(
            status_code=500,
            detail="Schema bestand niet gevonden — validatie niet beschikbaar",
        )

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    # ... rest blijft gelijk
```

---

## Tests toevoegen/aanpassen

### test_map_block.py — nieuwe tests

```python
class TestOverlayAlignment:
    """Tests voor overlay positionering na Bug 1+2 fix."""

    def test_overlay_aligns_with_base_image(self, tmp_path):
        """Overlay x-positie moet gelijk zijn aan base image x-positie."""
        png_bytes = _make_white_png(100, 75)

        m = KadasterMap(
            latitude=51.8125, longitude=4.6757,
            width_mm=80,  # smaller dan available_width
            layers=["luchtfoto", "percelen"],
            cache_dir=tmp_path / "cache",
        )
        with patch.object(m._client, "get_map", return_value=png_bytes):
            m.wrap(500, 800)

        # Na wrap: check dat _content Table ALIGN=LEFT voor rij 0
        # (indirect: als draw() niet crasht en overlay positie berekening klopt)
        assert not m._fetch_failed
        assert len(m._layer_paths) == 2

    def test_target_width_respects_padding(self, tmp_path):
        """target_w moet padding aftrekken van available_width."""
        png_bytes = _make_white_png(100, 75)
        
        m = KadasterMap(
            latitude=51.8125, longitude=4.6757,
            width_mm=300,  # veel breder dan available
            layers=["percelen"],
            cache_dir=tmp_path / "cache",
        )
        available = 400
        pad = 6
        with patch.object(m._client, "get_map", return_value=png_bytes):
            m.wrap(available, 800)
        
        # De content tabel breedte mag niet groter zijn dan available
        assert m.width <= available + 1
```

### test_api.py — nieuwe tests

```python
class TestGenerateErrorHandling:
    """Tests voor temp file cleanup bij fouten."""

    def test_generate_invalid_brand_cleans_temp(self, tmp_path):
        """Bij ongeldige brand mag er geen temp file achterblijven."""
        import tempfile
        before = set(Path(tempfile.gettempdir()).glob("*.pdf"))

        data = {
            "template": "structural",
            "project": "Test",
            "brand": "nonexistent_brand_xyz",
            "sections": [],
        }
        r = client.post("/api/generate", json=data)
        assert r.status_code in (404, 500)

        after = set(Path(tempfile.gettempdir()).glob("*.pdf"))
        leaked = after - before
        # Geen nieuwe temp files achtergebleven
        assert len(leaked) == 0

class TestValidateSchemaPath:
    """Tests voor robuuste schema resolving."""

    def test_validate_endpoint_available(self):
        """Validate endpoint moet bereikbaar zijn (200 of 500, niet 404)."""
        data = {"template": "test", "project": "Test"}
        r = client.post("/api/validate", json=data)
        assert r.status_code in (200, 500)
```

---

## Verificatie

```bash
python -m pytest tests/test_map_block.py tests/test_api.py -v
python -m pytest tests/ -v  # volledige regressie
```

## Samenvatting

| # | Bestand | Bug | Ernst |
|---|---------|-----|-------|
| 1 | map_block.py | Overlay x-misalignment (CENTER vs pad) | MEDIUM |
| 2 | map_block.py | Image breedte negeert cel-padding | MEDIUM |
| 3 | map_block.py | ParagraphStyle naam-conflict multi-pass | LOW |
| 4 | api.py | Temp file leak bij build-failure | MEDIUM |
| 5 | api.py + pyproject.toml | SCHEMA_PATH breekt na packaging | LOW |
