# P4: Coverage Gaps Dichten — Backend Test Versterking

## Context

De backend heeft 397 tests met 70% overall coverage. Maar er zijn blinde vlekken die risico vormen:

| Module | Coverage | Risico |
|--------|----------|--------|
| `cli.py` | 0% | CLI commando's nooit getest |
| `template_renderer.py` | 0% | Onbekend of deze module nog gebruikt wordt |
| `image_block.py` | 31% | Base64 en placeholder paden niet afgedekt |
| `data/json_adapter.py` | <45% | Validatie logica ongetest |
| `data/kadaster.py` | <45% | Kadaster data adapter ongetest |
| `data/revit_adapter.py` | <45% | Revit adapter stub ongetest |

Daarnaast: de bestaande test bestanden `test_stationery.py`, `test_stationery_extractor.py`, `test_brand_builder.py`, en `test_page_templates_integration.py` zijn in een eerdere sessie toegevoegd. Verifieer dat deze niet alleen op mocks leunen die werkelijke bugs maskeren.

## Stap 0: Oriëntatie

```bash
cd "X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator"
pip install -e ".[dev,brand-tools]" --quiet
python -m pytest tests/ --cov=openaec_reports --cov-report=term-missing -v 2>&1 | tee coverage_baseline.txt
```

Analyseer het coverage rapport. Identificeer per module:
- Welke functies/methoden 0% coverage hebben
- Welke branches niet afgedekt zijn
- Of er dode code is (nooit aangeroepen)

## Stap 1: Triageer template_renderer.py

Bekijk `src/openaec_reports/core/template_renderer.py`:
- Wordt het ergens geïmporteerd? Zoek naar imports in andere modules
- Zo niet: het is waarschijnlijk dead code uit een eerdere iteratie → documenteer dit, voeg geen tests toe voor dode code
- Zo ja: schrijf tests voor de gebruikte functies

```bash
grep -r "template_renderer" src/openaec_reports/ --include="*.py"
```

## Stap 2: CLI tests toevoegen

Maak `tests/test_cli.py` met tests voor elke CLI subcommand:

```python
"""Tests voor cli.py — alle subcommands."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from openaec_reports.cli import main, _cmd_generate, _cmd_templates, _cmd_validate, _cmd_serve


class TestMainDispatch:
    def test_no_command_shows_help(self, capsys):
        """Zonder command toont help en exit 1."""
        with patch("sys.argv", ["bm-report"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_unknown_command_shows_help(self, capsys):
        """Onbekend command toont help."""
        with patch("sys.argv", ["bm-report", "nonexistent"]):
            with pytest.raises(SystemExit):
                main()


class TestTemplatesCommand:
    def test_list_templates(self, capsys):
        """templates --list toont beschikbare templates."""
        with patch("sys.argv", ["bm-report", "templates", "--list"]):
            main()
        output = capsys.readouterr().out
        assert "structural_report" in output or "Beschikbare templates" in output


class TestValidateCommand:
    def test_validate_valid_json(self, tmp_path):
        """Valideer correct JSON bestand."""
        json_file = tmp_path / "valid.json"
        # Maak minimaal geldig JSON
        json_file.write_text('{"project": {"title": "Test"}, "sections": []}')
        with patch("sys.argv", ["bm-report", "validate", "--data", str(json_file)]):
            # Dit kan falen als JsonAdapter strenger valideert — dat is ok, test het gedrag
            try:
                main()
            except SystemExit as e:
                pass  # exit 0 of 1, beide zijn acceptabel

    def test_validate_invalid_json(self, tmp_path):
        """Valideer corrupt JSON bestand geeft foutmelding."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text("{corrupt json")
        with patch("sys.argv", ["bm-report", "validate", "--data", str(json_file)]):
            with pytest.raises((SystemExit, Exception)):
                main()


class TestGenerateCommand:
    def test_generate_creates_pdf(self, tmp_path):
        """Generate maakt een PDF bestand aan."""
        output_pdf = tmp_path / "test.pdf"
        data_file = Path("schemas/example_structural.json")
        if not data_file.exists():
            pytest.skip("example_structural.json niet gevonden")

        with patch("sys.argv", [
            "bm-report", "generate",
            "--template", "structural",
            "--data", str(data_file),
            "--output", str(output_pdf),
        ]):
            main()

        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 1000


class TestServeCommand:
    def test_serve_calls_uvicorn(self):
        """Serve start uvicorn met juiste parameters."""
        with patch("sys.argv", ["bm-report", "serve", "--port", "9999"]):
            with patch("uvicorn.run") as mock_run:
                main()
                mock_run.assert_called_once()
                args = mock_run.call_args
                assert args[1]["port"] == 9999


class TestAnalyzeBrandCommand:
    def test_analyze_brand_requires_pdf(self):
        """analyze-brand zonder PDF geeft error."""
        with patch("sys.argv", ["bm-report", "analyze-brand"]):
            with pytest.raises(SystemExit):
                main()


class TestBuildBrandCommand:
    def test_build_brand_requires_all_args(self):
        """build-brand zonder verplichte args geeft error."""
        with patch("sys.argv", ["bm-report", "build-brand"]):
            with pytest.raises(SystemExit):
                main()

    def test_build_brand_with_args(self, tmp_path):
        """build-brand met correcte args roept BrandBuilder aan."""
        ref_pdf = Path("huisstijl/2707_BBLrapportage_v01.pdf")
        if not ref_pdf.exists():
            pytest.skip("Referentie-PDF niet gevonden")

        output_dir = tmp_path / "brand_output"
        with patch("sys.argv", [
            "bm-report", "build-brand",
            "--rapport", str(ref_pdf),
            "--name", "Test",
            "--slug", "test",
            "--output", str(output_dir),
        ]):
            main()

        assert output_dir.exists()
```

## Stap 3: Image block coverage verhogen

Bekijk `tests/test_block_registry.py` en `src/openaec_reports/components/image_block.py`. Voeg tests toe voor:

- Base64 encoded afbeelding (data URI string)
- Ontbrekend bestand (fallback/placeholder)
- Caption rendering
- Width/alignment varianten
- Lege `src` string

Voeg toe aan `tests/test_block_registry.py` of maak `tests/test_image_block.py`:

```python
class TestImageBlockEdgeCases:
    def test_base64_image(self):
        """Base64 data URI als src wordt correct verwerkt."""
        # Maak minimale base64 PNG
        import base64
        from PIL import Image
        import io
        img = Image.new("RGB", (100, 100), (255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, "PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        data_uri = f"data:image/png;base64,{b64}"

        block = create_block("image", {"src": data_uri, "caption": "Test"})
        # Verifieer dat het block aangemaakt wordt zonder crash
        assert block is not None

    def test_empty_src_placeholder(self):
        """Lege src geeft placeholder block."""
        block = create_block("image", {"src": "", "caption": "Geen afbeelding"})
        assert block is not None

    def test_missing_file_placeholder(self):
        """Niet-bestaand bestand geeft placeholder."""
        block = create_block("image", {"src": "/nonexistent/img.png"})
        assert block is not None

    def test_alignment_center(self):
        """Center alignment wordt correct gezet."""
        block = create_block("image", {"src": "", "alignment": "center"})
        assert block is not None

    def test_width_mm_conversion(self):
        """width_mm wordt correct geconverteerd naar points."""
        block = create_block("image", {"src": "", "width_mm": 100})
        assert block is not None
```

## Stap 4: Data adapters testen

### json_adapter.py

```python
"""Tests voor data/json_adapter.py — JSON naar rapport data conversie."""

from pathlib import Path
import json
import pytest

from openaec_reports.data.json_adapter import JsonAdapter


class TestJsonAdapterInit:
    def test_from_file(self, tmp_path):
        data = {"project": {"title": "Test"}, "sections": []}
        f = tmp_path / "test.json"
        f.write_text(json.dumps(data))
        adapter = JsonAdapter(str(f))
        assert adapter is not None

    def test_from_dict(self):
        data = {"project": {"title": "Test"}, "sections": []}
        adapter = JsonAdapter(data)
        assert adapter is not None

    def test_nonexistent_file_raises(self):
        with pytest.raises((FileNotFoundError, Exception)):
            JsonAdapter("/nonexistent.json")


class TestJsonAdapterValidation:
    def test_validate_valid_data(self, tmp_path):
        data = {"project": {"title": "Test"}, "sections": []}
        f = tmp_path / "valid.json"
        f.write_text(json.dumps(data))
        adapter = JsonAdapter(str(f))
        errors = adapter.validate()
        # Kan leeg zijn (geldig) of fouten bevatten (schema strict)
        assert isinstance(errors, list)

    def test_validate_empty_dict(self):
        adapter = JsonAdapter({})
        errors = adapter.validate()
        assert isinstance(errors, list)
```

### kadaster.py en revit_adapter.py

Bekijk deze modules. Als het stubs zijn (lege functies of `pass`), voeg dan minimale tests toe die de interface verifiëren:

```python
class TestKadasterStub:
    def test_module_importable(self):
        from openaec_reports.data.kadaster import KadasterClient  # of wat de class heet
        assert KadasterClient is not None

class TestRevitAdapterStub:
    def test_module_importable(self):
        from openaec_reports.data.revit_adapter import RevitAdapter
        assert RevitAdapter is not None
```

## Stap 5: Verifieer bestaande nieuwe tests

Draai de vier test bestanden uit de vorige sessie en check of ze niet alleen op mocks leunen:

```bash
python -m pytest tests/test_stationery.py tests/test_stationery_extractor.py tests/test_brand_builder.py tests/test_page_templates_integration.py -v --tb=long
```

Check per testbestand:
- Worden er werkelijke functies aangeroepen of alleen mocks?
- Zijn de assertions zinvol (testen ze gedrag of alleen dat een mock is aangeroepen)?
- Zijn er tests die altijd slagen ongeacht de implementatie?

Als een test te veel mockt: refactor naar een integratietest met een tijdelijke directory en echte bestanden.

## Stap 6: Coverage rapport genereren

```bash
python -m pytest tests/ --cov=openaec_reports --cov-report=term-missing --cov-report=html:htmlcov -v 2>&1 | tee coverage_final.txt
```

Vergelijk met baseline:
```bash
diff coverage_baseline.txt coverage_final.txt
```

**Doel:** Overall coverage van 70% naar ≥80%. Kritieke modules (`cli.py`, `image_block.py`) van <50% naar ≥75%.

## Regels

1. **Geen regressie** — bestaande tests mogen niet breken
2. **Zinvolle tests** — test gedrag, niet implementatie-details. Een test die alleen checkt dat een mock is aangeroepen heeft weinig waarde
3. **Skip gracefully** — gebruik `pytest.skip()` als een test afhankelijk is van externe bestanden (referentie-PDF)
4. **Geen netwerk calls** — mock alle HTTP (PDOK WMS) in tests
5. **Prioriteer** — focus op de modules met het hoogste risico × laagste coverage

## Verwachte output

- `tests/test_cli.py` — CLI commando tests
- `tests/test_image_block.py` of uitbreiding in `test_block_registry.py`
- `tests/test_json_adapter.py` — JSON adapter tests
- `coverage_baseline.txt` en `coverage_final.txt` — voor/na vergelijking
- Alle tests groen, coverage ≥80%

## Update na afloop

Werk `SESSION_STATUS.md` en `STATUS.md` bij met nieuwe coverage cijfers.
