# Test Suite: Volledige regressie + ontbrekende dekking

## Context

De backend codebase is feature-complete voor de huidige scope. Er zijn 14 testbestanden in `tests/`. Deze prompt draait de volledige suite, fixt falende tests, en voegt ontbrekende coverage toe voor drie modules die géén dedicated tests hebben.

## Stap 0: Oriëntatie

Bekijk voor je begint:
- `pyproject.toml` — dependencies en test configuratie (`[tool.pytest.ini_options]`)
- `tests/` directory — alle bestaande testbestanden
- `src/openaec_reports/core/stationery.py` — StationeryRenderer (GEEN tests)
- `src/openaec_reports/tools/stationery_extractor.py` — StationeryExtractor (GEEN tests)
- `src/openaec_reports/tools/brand_builder.py` — BrandBuilder (GEEN tests)
- `src/openaec_reports/core/page_templates.py` — stationery-first callbacks + `_draw_text_zones()` + `_resolve_binding()` (NIET getest)

## Stap 1: Draai de volledige bestaande suite

```bash
cd X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator
pip install -e ".[dev,brand-tools]" --quiet
python -m pytest tests/ -v --tb=short 2>&1 | tee test_results.txt
```

**Noteer:**
- Welke tests PASS
- Welke tests FAIL (met foutmelding)
- Welke tests SKIP (en waarom)
- Totaal: X passed, Y failed, Z skipped

## Stap 2: Fix alle falende tests

Voor elke falende test:
1. Analyseer de foutmelding
2. Bepaal of de fout in de **test** zit of in de **productie code**
3. Fix de juiste kant — productie code heeft prioriteit over testcode
4. Draai de specifieke test opnieuw: `python -m pytest tests/test_xxx.py::TestClass::test_method -v`

**Regels:**
- Verander GEEN werkende productie-logica om een test te laten slagen — pas de test aan als de verwachting verkeerd is
- Als productie code een bug heeft: fix die bug, documenteer wat er fout was
- Als een import faalt: check of de dependency geïnstalleerd is

## Stap 3: Voeg ontbrekende tests toe

### 3A: `tests/test_stationery.py` — StationeryRenderer

Test de drie render paden: PDF, PNG, en fallback bij ontbrekend bestand.

```python
"""Tests voor StationeryRenderer — achtergrond PDF/PNG op canvas."""

from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
import pytest

from openaec_reports.core.stationery import StationeryRenderer


class TestStationeryRendererInit:
    def test_create_without_brand_dir(self):
        renderer = StationeryRenderer()
        assert renderer._brand_dir is None

    def test_create_with_brand_dir(self, tmp_path):
        renderer = StationeryRenderer(brand_dir=tmp_path)
        assert renderer._brand_dir == tmp_path


class TestResolvePath:
    def test_absolute_path_exists(self, tmp_path):
        f = tmp_path / "bg.pdf"
        f.write_bytes(b"dummy")
        renderer = StationeryRenderer()
        assert renderer._resolve_path(str(f)) == f

    def test_absolute_path_not_exists(self):
        renderer = StationeryRenderer()
        assert renderer._resolve_path("/nonexistent/bg.pdf") is None

    def test_relative_path_with_brand_dir(self, tmp_path):
        (tmp_path / "stationery").mkdir()
        f = tmp_path / "stationery" / "cover.pdf"
        f.write_bytes(b"dummy")
        renderer = StationeryRenderer(brand_dir=tmp_path)
        result = renderer._resolve_path("stationery/cover.pdf")
        assert result == f

    def test_relative_path_without_brand_dir(self):
        renderer = StationeryRenderer()
        result = renderer._resolve_path("stationery/cover.pdf")
        assert result is None


class TestDrawFallback:
    def test_draw_none_source(self):
        canvas = MagicMock()
        renderer = StationeryRenderer()
        result = renderer.draw(canvas, None, 595, 842)
        assert result is False

    def test_draw_empty_source(self):
        canvas = MagicMock()
        renderer = StationeryRenderer()
        result = renderer.draw(canvas, "", 595, 842)
        assert result is False

    def test_draw_nonexistent_file(self):
        canvas = MagicMock()
        renderer = StationeryRenderer()
        result = renderer.draw(canvas, "/nonexistent.pdf", 595, 842)
        assert result is False

    def test_draw_unknown_extension(self, tmp_path):
        f = tmp_path / "bg.bmp"
        f.write_bytes(b"dummy")
        canvas = MagicMock()
        renderer = StationeryRenderer(brand_dir=tmp_path)
        result = renderer.draw(canvas, str(f), 595, 842)
        assert result is False


class TestDrawImage:
    def test_draw_png(self, tmp_path):
        """PNG achtergrond wordt gerendered via drawImage."""
        # Maak minimale PNG
        from tests.test_map_block import _make_white_png
        png_bytes = _make_white_png(100, 100)
        f = tmp_path / "bg.png"
        f.write_bytes(png_bytes)

        canvas = MagicMock()
        renderer = StationeryRenderer(brand_dir=tmp_path)
        result = renderer.draw(canvas, str(f), 595, 842)

        assert result is True
        canvas.drawImage.assert_called_once()

    def test_draw_jpg(self, tmp_path):
        """JPG achtergrond wordt gerendered via drawImage."""
        from PIL import Image
        img = Image.new("RGB", (100, 100), (255, 255, 255))
        f = tmp_path / "bg.jpg"
        img.save(f, "JPEG")

        canvas = MagicMock()
        renderer = StationeryRenderer(brand_dir=tmp_path)
        result = renderer.draw(canvas, str(f), 595, 842)

        assert result is True
        canvas.drawImage.assert_called_once()


class TestDrawPdf:
    def test_draw_pdf_calls_doForm(self, tmp_path):
        """PDF achtergrond wordt gerendered via pdfrw → doForm."""
        # Maak minimale PDF met ReportLab
        from reportlab.pdfgen import canvas as rl_canvas
        pdf_path = tmp_path / "bg.pdf"
        c = rl_canvas.Canvas(str(pdf_path), pagesize=(595, 842))
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.rect(0, 0, 595, 842, fill=1)
        c.save()

        mock_canvas = MagicMock()
        mock_canvas.transform = MagicMock()
        renderer = StationeryRenderer(brand_dir=tmp_path)
        result = renderer.draw(mock_canvas, str(pdf_path), 595, 842)

        assert result is True
        mock_canvas.saveState.assert_called_once()
        mock_canvas.restoreState.assert_called_once()
        mock_canvas.doForm.assert_called_once()

    def test_pdf_caching(self, tmp_path):
        """Tweede aanroep gebruikt cache (pdfrw leest niet opnieuw)."""
        from reportlab.pdfgen import canvas as rl_canvas
        pdf_path = tmp_path / "bg.pdf"
        c = rl_canvas.Canvas(str(pdf_path), pagesize=(595, 842))
        c.rect(0, 0, 595, 842, fill=1)
        c.save()

        mock_canvas = MagicMock()
        mock_canvas.transform = MagicMock()
        renderer = StationeryRenderer(brand_dir=tmp_path)

        renderer.draw(mock_canvas, str(pdf_path), 595, 842)
        renderer.draw(mock_canvas, str(pdf_path), 595, 842)

        # Cache key moet bestaan
        assert len(renderer._cache) == 1

    def test_draw_pdf_without_pdfrw_returns_false(self, tmp_path):
        """Als pdfrw niet beschikbaar is, retourneer False."""
        from reportlab.pdfgen import canvas as rl_canvas
        pdf_path = tmp_path / "bg.pdf"
        c = rl_canvas.Canvas(str(pdf_path), pagesize=(595, 842))
        c.save()

        mock_canvas = MagicMock()
        renderer = StationeryRenderer(brand_dir=tmp_path)

        with patch.dict("sys.modules", {"pdfrw": None, "pdfrw.buildxobj": None, "pdfrw.toreportlab": None}):
            # Dit test is lastig omdat de import al gedaan is.
            # Skip als pdfrw al geladen is — het punt is dat de code graceful faalt.
            pass
```

**Implementeer alle tests hierboven.** Pas aan waar nodig als de mock niet klopt met de werkelijke signatuur. De structuur en test-intentie moeten overeind blijven.

### 3B: `tests/test_stationery_extractor.py` — StationeryExtractor

Test extractie modi met een echte mini-PDF als fixture.

```python
"""Tests voor StationeryExtractor — extraheer achtergrondtemplates uit PDF."""

from pathlib import Path
import pytest

# Skip als pymupdf niet geïnstalleerd
fitz = pytest.importorskip("fitz", reason="pymupdf niet geïnstalleerd")

from openaec_reports.tools.stationery_extractor import StationeryExtractor


@pytest.fixture
def sample_pdf(tmp_path) -> Path:
    """Maak een minimale test-PDF met tekst en een gekleurd rectangle."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)

    # Teken een gekleurd blok (graphics)
    rect = fitz.Rect(0, 0, 200, 100)
    shape = page.new_shape()
    shape.draw_rect(rect)
    shape.finish(color=(0, 0, 0), fill=(0.25, 0.07, 0.28))  # paars
    shape.commit()

    # Voeg tekst toe
    page.insert_text(fitz.Point(50, 200), "Test Titel", fontsize=24)
    page.insert_text(fitz.Point(50, 300), "Body tekst hier", fontsize=10)

    pdf_path = tmp_path / "test_source.pdf"
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


class TestExtractorInit:
    def test_create_with_valid_pdf(self, sample_pdf):
        extractor = StationeryExtractor(sample_pdf)
        assert extractor._source == sample_pdf

    def test_create_with_nonexistent_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="niet gevonden"):
            StationeryExtractor(tmp_path / "nonexistent.pdf")

    def test_create_without_pymupdf(self):
        """Test dat ImportError wordt gegooid als fitz niet beschikbaar is."""
        # Dit wordt al afgedekt door importorskip, maar documenteert het gedrag
        pass


class TestExtractFullPage:
    def test_extracts_single_page_pdf(self, sample_pdf, tmp_path):
        extractor = StationeryExtractor(sample_pdf)
        output = tmp_path / "full.pdf"
        result = extractor.extract_full_page(0, output)

        assert result.exists()
        assert result.stat().st_size > 0
        # Verify het is een geldige PDF
        doc = fitz.open(str(result))
        assert len(doc) == 1
        doc.close()

    def test_creates_parent_dirs(self, sample_pdf, tmp_path):
        output = tmp_path / "deep" / "nested" / "full.pdf"
        result = StationeryExtractor(sample_pdf).extract_full_page(0, output)
        assert result.exists()

    def test_preserves_graphics(self, sample_pdf, tmp_path):
        """Geëxtraheerde pagina bevat nog steeds het gekleurde blok."""
        output = tmp_path / "full.pdf"
        StationeryExtractor(sample_pdf).extract_full_page(0, output)

        doc = fitz.open(str(output))
        page = doc[0]
        # Pagina moet tekst bevatten (full page = alles behouden)
        text = page.get_text()
        assert "Test Titel" in text
        doc.close()


class TestExtractStrippedPage:
    def test_strips_text_in_zone(self, sample_pdf, tmp_path):
        """Tekst in strip zone wordt verwijderd."""
        output = tmp_path / "stripped.pdf"
        # Zone die "Test Titel" omvat (y=170-210 in PyMuPDF coords)
        strip_zones = [(40, 170, 300, 220)]

        StationeryExtractor(sample_pdf).extract_stripped_page(0, output, strip_zones)

        doc = fitz.open(str(output))
        page = doc[0]
        text = page.get_text()
        # "Test Titel" moet weg zijn
        assert "Test Titel" not in text
        # "Body tekst hier" moet nog bestaan (buiten de zone)
        assert "Body tekst" in text
        doc.close()

    def test_empty_strip_zones_preserves_all(self, sample_pdf, tmp_path):
        output = tmp_path / "stripped_empty.pdf"
        StationeryExtractor(sample_pdf).extract_stripped_page(0, output, [])

        doc = fitz.open(str(output))
        text = doc[0].get_text()
        assert "Test Titel" in text
        assert "Body tekst" in text
        doc.close()


class TestExtractGraphicsOnly:
    def test_removes_all_text(self, sample_pdf, tmp_path):
        """Alle tekst wordt verwijderd."""
        output = tmp_path / "graphics_only.pdf"
        StationeryExtractor(sample_pdf).extract_graphics_only(0, output)

        doc = fitz.open(str(output))
        text = doc[0].get_text().strip()
        assert text == "" or "Test" not in text
        doc.close()


class TestExtractAsPng:
    def test_creates_png(self, sample_pdf, tmp_path):
        output = tmp_path / "page.png"
        result = StationeryExtractor(sample_pdf).extract_as_png(0, output, dpi=72)

        assert result.exists()
        assert result.suffix == ".png"
        assert result.stat().st_size > 100
```

**Implementeer alle tests.** De `sample_pdf` fixture maakt een echte mini-PDF zodat we geen externe bestanden nodig hebben. Pas de strip_zones coördinaten aan als de tekst op andere posities terechtkomt (check met `page.get_text("dict")` in een debug stap als tests falen).

### 3C: `tests/test_brand_builder.py` — BrandBuilder

Test de pipeline stappen met mocks waar nodig.

```python
"""Tests voor BrandBuilder — volledige brand directory generatie."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

fitz = pytest.importorskip("fitz", reason="pymupdf niet geïnstalleerd")

from openaec_reports.tools.brand_builder import BrandBuilder


@pytest.fixture
def sample_pdf(tmp_path) -> Path:
    """Maak een multi-page test-PDF met herkenbare paginatypes."""
    doc = fitz.open()

    # Cover (pagina 1) — groot gekleurd blok + grote tekst
    page = doc.new_page(width=595, height=842)
    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(0, 0, 300, 500))
    shape.finish(fill=(0.25, 0.07, 0.28))
    shape.commit()
    page.insert_text(fitz.Point(50, 200), "Rapport Titel", fontsize=28)

    # Content (pagina 2) — body tekst
    page = doc.new_page(width=595, height=842)
    page.insert_text(fitz.Point(50, 50), "1. Uitgangspunten", fontsize=18)
    page.insert_text(fitz.Point(50, 100), "Dit is body tekst.", fontsize=10)

    # Backcover (pagina 3) — volledig gekleurd
    page = doc.new_page(width=595, height=842)
    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(0, 0, 595, 842))
    shape.finish(fill=(0.22, 0.74, 0.67))
    shape.commit()

    pdf_path = tmp_path / "test_rapport.pdf"
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


class TestBrandBuilderInit:
    def test_create(self, tmp_path):
        bb = BrandBuilder(
            output_dir=tmp_path / "output",
            brand_name="Test Brand",
            brand_slug="test-brand",
        )
        assert bb.brand_name == "Test Brand"
        assert bb.brand_slug == "test-brand"


class TestBrandBuilderBuild:
    def test_build_creates_directory_structure(self, sample_pdf, tmp_path):
        """Build maakt stationery/, analysis/, logos/ mappen aan."""
        output = tmp_path / "brand_output"
        bb = BrandBuilder(output_dir=output, brand_name="Test", brand_slug="test")
        bb.build(referentie_rapport=sample_pdf)

        assert (output / "stationery").is_dir()
        assert (output / "analysis").is_dir()
        assert (output / "logos").is_dir()

    def test_build_creates_brand_yaml(self, sample_pdf, tmp_path):
        """Build genereert brand.yaml."""
        output = tmp_path / "brand_output"
        bb = BrandBuilder(output_dir=output, brand_name="Test", brand_slug="test")
        bb.build(referentie_rapport=sample_pdf)

        yaml_path = output / "brand.yaml"
        assert yaml_path.exists()
        assert yaml_path.stat().st_size > 50

    def test_build_creates_analysis_report(self, sample_pdf, tmp_path):
        """Build genereert analysis/report.md."""
        output = tmp_path / "brand_output"
        bb = BrandBuilder(output_dir=output, brand_name="Test", brand_slug="test")
        bb.build(referentie_rapport=sample_pdf)

        report = output / "analysis" / "report.md"
        assert report.exists()

    def test_build_brand_yaml_parseable(self, sample_pdf, tmp_path):
        """brand.yaml is geldig YAML met verwachte structuur."""
        import yaml

        output = tmp_path / "brand_output"
        bb = BrandBuilder(output_dir=output, brand_name="MijnBrand", brand_slug="mijn-brand")
        bb.build(referentie_rapport=sample_pdf)

        data = yaml.safe_load((output / "brand.yaml").read_text(encoding="utf-8"))
        assert "brand" in data
        assert data["brand"]["name"] == "MijnBrand"
        assert data["brand"]["slug"] == "mijn-brand"
        assert "colors" in data

    def test_build_with_logo_dir(self, sample_pdf, tmp_path):
        """Logo's worden gekopieerd naar output/logos/."""
        logos = tmp_path / "logos_src"
        logos.mkdir()
        (logos / "logo.png").write_bytes(b"\x89PNG" + b"\x00" * 50)
        (logos / "logo.svg").write_text("<svg></svg>", encoding="utf-8")

        output = tmp_path / "brand_output"
        bb = BrandBuilder(output_dir=output, brand_name="Test", brand_slug="test")
        bb.build(referentie_rapport=sample_pdf, logo_dir=logos)

        assert (output / "logos" / "logo.png").exists()
        assert (output / "logos" / "logo.svg").exists()

    def test_build_with_font_dir(self, sample_pdf, tmp_path):
        """Fonts worden gekopieerd naar output/fonts/."""
        fonts = tmp_path / "fonts_src"
        fonts.mkdir()
        (fonts / "Regular.ttf").write_bytes(b"\x00" * 50)
        (fonts / "Bold.otf").write_bytes(b"\x00" * 50)

        output = tmp_path / "brand_output"
        bb = BrandBuilder(output_dir=output, brand_name="Test", brand_slug="test")
        bb.build(referentie_rapport=sample_pdf, font_dir=fonts)

        assert (output / "fonts" / "Regular.ttf").exists()
        assert (output / "fonts" / "Bold.otf").exists()


class TestHelperMethods:
    def test_detect_cover_strip_zones_returns_list(self, sample_pdf, tmp_path):
        from openaec_reports.tools.pdf_extractor import extract_pdf
        pages = extract_pdf(sample_pdf)

        bb = BrandBuilder(output_dir=tmp_path, brand_name="T", brand_slug="t")
        zones = bb._detect_cover_strip_zones(pages[0])
        assert isinstance(zones, list)

    def test_extract_stamkaart_colors_empty(self, tmp_path):
        """Pagina's zonder kleurcodes retourneren lege dict."""
        from openaec_reports.tools.pdf_extractor import extract_pdf

        # Maak simpele PDF zonder kleurcodes
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(fitz.Point(50, 50), "Geen kleuren", fontsize=12)
        pdf = tmp_path / "no_colors.pdf"
        doc.save(str(pdf))
        doc.close()

        pages = extract_pdf(pdf)
        bb = BrandBuilder(output_dir=tmp_path, brand_name="T", brand_slug="t")
        colors = bb._extract_stamkaart_colors(pages)
        assert colors == {}
```

**Implementeer alle tests.** De `sample_pdf` fixture maakt een mini-rapport; het hoeft niet de volledige 36-pagina referentie-PDF te zijn. De tests verifiëren de pipeline structuur en output, niet de pixel-perfecte analyse (daarvoor is `test_brand_analyzer.py` met de echte PDF).

### 3D: `tests/test_page_templates_integration.py` — Stationery-first callbacks

Test de stationery-first logica in page_templates.py.

```python
"""Tests voor page_templates.py — stationery-first callbacks en text zones."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from openaec_reports.core.brand import BrandConfig, BrandLoader, StationeryPageConfig, ZoneConfig
from openaec_reports.core.document import A4, DocumentConfig
from openaec_reports.core.page_templates import (
    _draw_text_zones,
    _resolve_binding,
    create_page_templates,
)


def _make_config(**kwargs) -> DocumentConfig:
    defaults = {
        "project": "Test Project",
        "project_number": "2026-001",
        "client": "Test BV",
        "author": "Ing. Test",
        "report_type": "structural",
        "subtitle": "Test subtitle",
    }
    defaults.update(kwargs)
    return DocumentConfig(format=A4, **defaults)


class TestCreatePageTemplates:
    def test_returns_five_templates(self):
        config = _make_config()
        templates = create_page_templates(config)
        assert len(templates) == 5

    def test_template_ids_correct(self):
        config = _make_config()
        templates = create_page_templates(config)
        ids = [t.id for t in templates]
        assert ids == ["cover", "colofon", "content", "appendix_divider", "backcover"]

    def test_with_brand_parameter(self):
        config = _make_config()
        brand = BrandLoader().load("3bm_cooperatie")
        templates = create_page_templates(config, brand=brand)
        assert len(templates) == 5

    def test_content_frame_from_brand(self):
        """Content frame dimensies komen uit brand stationery config."""
        config = _make_config()
        brand = BrandLoader().load("3bm_cooperatie")
        templates = create_page_templates(config, brand=brand)

        content = templates[2]  # content template
        frame = content.frames[0]
        # 3bm_cooperatie heeft content_frame.x_pt=90.0
        assert abs(frame._x1 - 90.0) < 1.0


class TestResolveBinding:
    def test_project(self):
        config = _make_config(project="Mijn Project")
        brand = BrandConfig()
        result = _resolve_binding("project", config, brand)
        assert result == "Mijn Project"

    def test_project_number(self):
        config = _make_config(project_number="2026-042")
        brand = BrandConfig()
        result = _resolve_binding("project_number", config, brand)
        assert result == "2026-042"

    def test_client(self):
        config = _make_config(client="Klant BV")
        brand = BrandConfig()
        result = _resolve_binding("client", config, brand)
        assert result == "Klant BV"

    def test_author(self):
        config = _make_config(author="Ing. J. Test")
        brand = BrandConfig()
        result = _resolve_binding("author", config, brand)
        assert result == "Ing. J. Test"

    def test_subtitle(self):
        config = _make_config(subtitle="Constructief")
        brand = BrandConfig()
        result = _resolve_binding("subtitle", config, brand)
        assert result == "Constructief"

    def test_contact_binding(self):
        config = _make_config()
        brand = BrandConfig(contact={"name": "3BM", "website": "3bm.co.nl"})
        result = _resolve_binding("contact.name", config, brand)
        assert result == "3BM"

    def test_unknown_binding_returns_empty(self):
        config = _make_config()
        brand = BrandConfig()
        result = _resolve_binding("nonexistent", config, brand)
        assert result == ""

    def test_contact_unknown_key_returns_empty(self):
        config = _make_config()
        brand = BrandConfig(contact={"name": "3BM"})
        result = _resolve_binding("contact.unknown", config, brand)
        assert result == ""


class TestDrawTextZones:
    def test_draws_text_with_correct_font(self):
        canvas = MagicMock()
        config = _make_config(project="TestProject")
        brand = BrandConfig(
            fonts={"body": "Helvetica", "heading": "Helvetica-Bold"},
            colors={"text": "#000000"},
        )
        text_zones = [
            {
                "type": "text",
                "bind": "project",
                "font": "$fonts.body",
                "color": "$colors.text",
                "size": 12.0,
                "x_pt": 100,
                "y_pt": 200,
            }
        ]

        _draw_text_zones(canvas, text_zones, config, brand, 595, 842)

        canvas.saveState.assert_called()
        canvas.setFont.assert_called()
        canvas.drawString.assert_called_once()
        drawn_text = canvas.drawString.call_args[0][2]
        assert drawn_text == "TestProject"

    def test_skips_non_text_zones(self):
        canvas = MagicMock()
        config = _make_config()
        brand = BrandConfig()
        text_zones = [
            {"type": "clipped_image", "src": "something.png"},
        ]

        _draw_text_zones(canvas, text_zones, config, brand, 595, 842)

        canvas.drawString.assert_not_called()

    def test_skips_empty_binding(self):
        canvas = MagicMock()
        config = _make_config(project="")
        brand = BrandConfig(fonts={"body": "Helvetica"}, colors={"text": "#000"})
        text_zones = [
            {
                "type": "text",
                "bind": "project",
                "font": "$fonts.body",
                "color": "$colors.text",
                "size": 10,
                "x_pt": 50,
                "y_pt": 100,
            }
        ]

        _draw_text_zones(canvas, text_zones, config, brand, 595, 842)

        canvas.drawString.assert_not_called()

    def test_right_alignment(self):
        canvas = MagicMock()
        config = _make_config(project="Test")
        brand = BrandConfig(fonts={"body": "Helvetica"}, colors={"text": "#000"})
        text_zones = [
            {
                "type": "text",
                "bind": "project",
                "font": "$fonts.body",
                "color": "$colors.text",
                "size": 10,
                "x_pt": 500,
                "y_pt": 100,
                "align": "right",
            }
        ]

        _draw_text_zones(canvas, text_zones, config, brand, 595, 842)

        canvas.drawRightString.assert_called_once()

    def test_center_alignment(self):
        canvas = MagicMock()
        config = _make_config(project="Test")
        brand = BrandConfig(fonts={"body": "Helvetica"}, colors={"text": "#000"})
        text_zones = [
            {
                "type": "text",
                "bind": "project",
                "font": "$fonts.body",
                "color": "$colors.text",
                "size": 10,
                "x_pt": 300,
                "y_pt": 100,
                "align": "center",
            }
        ]

        _draw_text_zones(canvas, text_zones, config, brand, 595, 842)

        canvas.drawCentredString.assert_called_once()

    def test_y_coordinate_conversion(self):
        """y_pt (top-down) wordt geconverteerd naar ReportLab (bottom-up)."""
        canvas = MagicMock()
        config = _make_config(project="Test")
        brand = BrandConfig(fonts={"body": "Helvetica"}, colors={"text": "#000"})
        ph = 842.0
        y_pt = 200.0
        text_zones = [
            {
                "type": "text",
                "bind": "project",
                "font": "$fonts.body",
                "color": "$colors.text",
                "size": 10,
                "x_pt": 50,
                "y_pt": y_pt,
            }
        ]

        _draw_text_zones(canvas, text_zones, config, brand, 595, ph)

        # ReportLab y = ph - y_pt = 842 - 200 = 642
        args = canvas.drawString.call_args[0]
        rl_y = args[1]
        assert abs(rl_y - (ph - y_pt)) < 0.1
```

**Implementeer alle tests.** Focus op de `_resolve_binding` en `_draw_text_zones` functies — dit is de kern van het stationery text zone systeem.

## Stap 4: Draai de volledige suite opnieuw

```bash
python -m pytest tests/ -v --tb=short 2>&1 | tee test_results_final.txt
```

**Doel:** 0 failures, 0 errors. Skips zijn acceptabel (bijv. `test_brand_analyzer` als de referentie-PDF niet aanwezig is).

## Stap 5: Coverage rapport (optioneel maar gewenst)

```bash
python -m pytest tests/ --cov=openaec_reports --cov-report=term-missing -v 2>&1 | tee coverage_report.txt
```

Noteer welke modules nog <50% coverage hebben. Dat hoeft nu niet gefixed te worden, maar het geeft richting voor een volgende ronde.

## Samenvatting verwachte output

Na afloop moeten bestaan:
- `tests/test_stationery.py` — StationeryRenderer tests
- `tests/test_stationery_extractor.py` — StationeryExtractor tests (skip als geen pymupdf)
- `tests/test_brand_builder.py` — BrandBuilder pipeline tests (skip als geen pymupdf)
- `tests/test_page_templates_integration.py` — Stationery-first + text zone tests
- `test_results_final.txt` — Uitvoer van de laatste pytest run
- Optioneel: `coverage_report.txt`

## Regels

1. **Geen regressie** — bestaande PASS tests mogen niet breken
2. **Fix productie code** als een test een echte bug blootlegt
3. **Pas test verwachtingen aan** als de test een verkeerde aanname maakte
4. **Skip gracefully** — gebruik `pytest.importorskip("fitz")` voor pymupdf-afhankelijke tests
5. **Geen externe netwerk calls** — mock alle HTTP (PDOK, WMS) in tests
6. **Deterministic** — tests mogen niet afhankelijk zijn van timing of willekeurige data
