"""Tests voor BrandBuilder — volledige brand directory generatie."""

from pathlib import Path

import pytest
import yaml

fitz = pytest.importorskip("fitz", reason="pymupdf niet geïnstalleerd")

from bm_reports.tools.brand_builder import BrandBuilder  # noqa: E402


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
        from bm_reports.tools.pdf_extractor import extract_pdf

        pages = extract_pdf(sample_pdf)

        bb = BrandBuilder(output_dir=tmp_path, brand_name="T", brand_slug="t")
        zones = bb._detect_cover_strip_zones(pages[0])
        assert isinstance(zones, list)

    def test_extract_stamkaart_colors_empty(self, tmp_path):
        """Pagina's zonder kleurcodes retourneren lege dict."""
        from bm_reports.tools.pdf_extractor import extract_pdf

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
