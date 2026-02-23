"""Tests voor brand analyzer pipeline (PDF → classificatie → config)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REFERENCE_PDF = Path(__file__).parent.parent / "huisstijl" / "2707_BBLrapportage_v01.pdf"
SKIP_NO_PDF = pytest.mark.skipif(
    not REFERENCE_PDF.exists(), reason="Referentie PDF niet aanwezig"
)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(scope="module")
def raw_pages():
    """Extraheer alle pagina's uit de referentie-PDF (zonder renders)."""
    if not REFERENCE_PDF.exists():
        pytest.skip("Referentie PDF niet aanwezig")
    from bm_reports.tools import extract_pdf
    return extract_pdf(REFERENCE_PDF)


@pytest.fixture(scope="module")
def classified(raw_pages):
    """Classificeer alle pagina's."""
    from bm_reports.tools import classify_pages
    return classify_pages(raw_pages)


@pytest.fixture(scope="module")
def analysis(classified):
    """Voer volledige brand analyse uit."""
    from bm_reports.tools import analyze_brand
    return analyze_brand(classified, str(REFERENCE_PDF))


# ============================================================
# TestPdfExtractor
# ============================================================

@SKIP_NO_PDF
class TestPdfExtractor:
    """Tests voor PDF extractie."""

    def test_extract_page_count(self, raw_pages):
        assert len(raw_pages) == 36

    def test_extract_page_dimensions(self, raw_pages):
        p1 = raw_pages[0]
        assert abs(p1.width_pt - 595.3) < 1
        assert abs(p1.height_pt - 841.9) < 1

    def test_extract_cover_text(self, raw_pages):
        p1 = raw_pages[0]
        found = False
        for t in p1.texts:
            if "BBL" in t.text and "rapport" in t.text.lower():
                assert "Gotham" in t.font or "gotham" in t.font.lower()
                assert t.size > 25
                found = True
                break
        assert found, "BBL-toetsingsrapportage niet gevonden op cover"

    def test_extract_cover_rects(self, raw_pages):
        p1 = raw_pages[0]
        # Zoek groot paars rect
        purple_rects = [
            r for r in p1.rects
            if r.fill_hex and r.fill_hex.upper().startswith("#40")
            and r.width > 100 and r.height > 100
        ]
        assert len(purple_rects) > 0, "Geen paars rect gevonden op cover"

    def test_extract_colofon_text(self, raw_pages):
        p2 = raw_pages[1]
        texts = " ".join(t.text for t in p2.texts).lower()
        assert "project" in texts
        assert "adviseur" in texts or "opdracht" in texts

    def test_extract_colofon_lines(self, raw_pages):
        p2 = raw_pages[1]
        h_lines = [
            r for r in p2.rects
            if r.element_type == "line" and r.width > 50
        ]
        assert len(h_lines) >= 5, f"Verwachtte >5 scheidingslijnen, vond {len(h_lines)}"

    def test_extract_content_text(self, raw_pages):
        p5 = raw_pages[4]
        body_texts = [
            t for t in p5.texts
            if "Gotham" in t.font and "Book" in t.font and abs(t.size - 9.5) < 1
        ]
        assert len(body_texts) > 0, "Geen Gotham-Book 9.5pt tekst op pagina 5"

    def test_extract_page_images(self, raw_pages):
        p1 = raw_pages[0]
        assert len(p1.images) >= 1, "Geen images op cover"

    def test_extract_without_images_dir(self, raw_pages):
        # raw_pages fixture is zonder output_dir
        assert raw_pages[0].page_image_path is None


# ============================================================
# TestPageClassifier
# ============================================================

@SKIP_NO_PDF
class TestPageClassifier:
    """Tests voor pagina classificatie."""

    def test_classify_cover(self, classified):
        from bm_reports.tools import PageType
        assert classified[0].page_type == PageType.COVER

    def test_classify_backcover(self, classified):
        from bm_reports.tools import PageType
        assert classified[-1].page_type == PageType.BACKCOVER

    def test_classify_colofon(self, classified):
        from bm_reports.tools import PageType
        assert classified[1].page_type == PageType.COLOFON

    def test_classify_toc(self, classified):
        from bm_reports.tools import PageType
        assert classified[2].page_type == PageType.TOC

    def test_classify_appendix_divider(self, classified):
        from bm_reports.tools import PageType
        # Pagina 21 (index 20) zou APPENDIX_DIVIDER moeten zijn
        assert classified[20].page_type == PageType.APPENDIX_DIVIDER

    def test_classify_content(self, classified):
        from bm_reports.tools import PageType
        # Pagina 4-20 zouden CONTENT moeten zijn
        for i in [3, 4, 5, 10, 15, 19]:
            assert classified[i].page_type == PageType.CONTENT, (
                f"Pagina {i + 1} verwacht CONTENT, kreeg {classified[i].page_type}"
            )

    def test_all_pages_classified(self, classified):
        from bm_reports.tools import PageType
        for cp in classified:
            assert cp.page_type != PageType.UNKNOWN, (
                f"Pagina {cp.page.page_number} is UNKNOWN"
            )


# ============================================================
# TestPatternDetector
# ============================================================

@SKIP_NO_PDF
class TestPatternDetector:
    """Tests voor patroon detectie."""

    def test_color_palette_primary(self, analysis):
        assert "primary" in analysis.colors
        assert analysis.colors["primary"].upper().startswith("#40")

    def test_color_palette_secondary(self, analysis):
        assert "secondary" in analysis.colors
        # Turquoise/groen-achtig
        from bm_reports.tools.pattern_detector import _hex_to_rgb
        r, g, b = _hex_to_rgb(analysis.colors["secondary"])
        assert g > r, f"Secondary {analysis.colors['secondary']} is niet groen/turquoise"

    def test_color_palette_text(self, analysis):
        assert "text" in analysis.colors
        # Donkerpaurs ~#45243D
        from bm_reports.tools.pattern_detector import _hex_to_rgb
        r, g, b = _hex_to_rgb(analysis.colors["text"])
        assert r + g + b < 300, f"Text kleur {analysis.colors['text']} is niet donker"

    def test_font_map_heading(self, analysis):
        assert "heading" in analysis.fonts
        heading = analysis.fonts["heading"].lower()
        assert "gotham" in heading
        assert "bold" in heading

    def test_font_map_body(self, analysis):
        assert "body" in analysis.fonts
        body = analysis.fonts["body"].lower()
        assert "gotham" in body
        assert "book" in body

    def test_margins_left(self, analysis):
        # Body text indent can be wider than the absolute margin (section numbers are further left)
        assert 29 < analysis.margins_mm["left"] < 50

    def test_margins_right(self, analysis):
        assert 15 < analysis.margins_mm["right"] < 22

    def test_header_zone_empty(self, analysis):
        assert analysis.header_zone["height_mm"] == 0

    def test_footer_zone_page_number(self, analysis):
        elements = analysis.footer_zone.get("elements", [])
        has_page = any(
            e.get("content") == "{page}" for e in elements if e.get("type") == "text"
        )
        assert has_page, "Footer bevat geen paginanummer element"

    def test_footer_zone_height(self, analysis):
        assert analysis.footer_zone["height_mm"] < 20

    def test_style_heading1_size(self, analysis):
        assert "Heading1" in analysis.styles
        assert 16 <= analysis.styles["Heading1"]["size"] <= 20

    def test_style_heading2_size(self, analysis):
        assert "Heading2" in analysis.styles
        assert 12 <= analysis.styles["Heading2"]["size"] <= 15

    def test_style_normal_size(self, analysis):
        assert "Normal" in analysis.styles
        assert 7 <= analysis.styles["Normal"]["size"] <= 11

    def test_style_heading1_not_bold(self, analysis):
        h1_font = analysis.styles["Heading1"]["font"].lower()
        assert "bold" not in h1_font, f"Heading1 font mag NIET bold zijn: {h1_font}"

    def test_table_style_detected(self, analysis):
        assert analysis.table_style is not None
        assert "header_bg" in analysis.table_style
        from bm_reports.tools.pattern_detector import _hex_to_rgb
        r, g, b = _hex_to_rgb(analysis.table_style["header_bg"])
        assert r + g + b < 500, "Table header_bg zou donker moeten zijn"


# ============================================================
# TestConfigGenerator
# ============================================================

@SKIP_NO_PDF
class TestConfigGenerator:
    """Tests voor config generatie."""

    def test_generate_yaml_parseable(self, analysis):
        from bm_reports.tools import generate_brand_yaml
        yaml_str = generate_brand_yaml(analysis, "Test Brand", "test-brand")
        data = yaml.safe_load(yaml_str)
        assert isinstance(data, dict)

    def test_generate_yaml_has_brand_section(self, analysis):
        from bm_reports.tools import generate_brand_yaml
        yaml_str = generate_brand_yaml(analysis, "Test Brand", "test-brand")
        data = yaml.safe_load(yaml_str)
        assert "brand" in data
        assert data["brand"]["name"] == "Test Brand"
        assert data["brand"]["slug"] == "test-brand"

    def test_generate_yaml_has_colors(self, analysis):
        from bm_reports.tools import generate_brand_yaml
        yaml_str = generate_brand_yaml(analysis, "Test", "test")
        data = yaml.safe_load(yaml_str)
        assert "colors" in data
        assert "primary" in data["colors"]

    def test_generate_yaml_has_footer(self, analysis):
        from bm_reports.tools import generate_brand_yaml
        yaml_str = generate_brand_yaml(analysis, "Test", "test")
        data = yaml.safe_load(yaml_str)
        assert "footer" in data
        assert "height" in data["footer"]
        assert "elements" in data["footer"]

    def test_generate_yaml_has_styles(self, analysis):
        from bm_reports.tools import generate_brand_yaml
        yaml_str = generate_brand_yaml(analysis, "Test", "test")
        data = yaml.safe_load(yaml_str)
        assert "styles" in data
        assert "Normal" in data["styles"]
        assert "Heading1" in data["styles"]

    def test_generate_report_is_markdown(self, analysis):
        from bm_reports.tools import generate_analysis_report
        report = generate_analysis_report(analysis)
        assert "# " in report

    def test_generate_report_contains_colors(self, analysis):
        from bm_reports.tools import generate_analysis_report
        report = generate_analysis_report(analysis)
        assert "primary" in report
        assert "#" in report


# ============================================================
# TestCLI
# ============================================================

@SKIP_NO_PDF
class TestCLI:
    """Tests voor CLI command."""

    def test_cli_analyze_brand_creates_files(self, tmp_path):
        from bm_reports.tools import (
            analyze_brand,
            classify_pages,
            extract_pdf,
            generate_analysis_report,
            generate_brand_yaml,
        )

        pages = extract_pdf(REFERENCE_PDF)
        classified = classify_pages(pages)
        analysis = analyze_brand(classified, str(REFERENCE_PDF))

        yaml_str = generate_brand_yaml(analysis, "3BM Test", "3bm-test")
        yaml_path = tmp_path / "3bm-test.yaml"
        yaml_path.write_text(yaml_str, encoding="utf-8")

        report_str = generate_analysis_report(analysis)
        report_path = tmp_path / "analysis_report.md"
        report_path.write_text(report_str, encoding="utf-8")

        assert yaml_path.exists()
        assert report_path.exists()
        assert yaml_path.stat().st_size > 100
        assert report_path.stat().st_size > 100
