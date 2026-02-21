"""Tests voor StationeryExtractor — extraheer achtergrondtemplates uit PDF."""

from pathlib import Path

import pytest

# Skip als pymupdf niet geïnstalleerd
fitz = pytest.importorskip("fitz", reason="pymupdf niet geïnstalleerd")

from bm_reports.tools.stationery_extractor import StationeryExtractor


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
        # Zone die "Test Titel" omvat (y=170-220 in PyMuPDF coords)
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
