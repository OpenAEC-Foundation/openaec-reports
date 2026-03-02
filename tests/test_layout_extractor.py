"""Tests voor B5 — layout_extractor, PathElement, visual_diff, generate_pages_yaml."""

from __future__ import annotations

from pathlib import Path

import pytest

fitz = pytest.importorskip("fitz", reason="pymupdf niet geinstalleerd")

from openaec_reports.tools.config_generator import generate_brand_yaml, generate_pages_yaml  # noqa: E402
from openaec_reports.tools.layout_extractor import (  # noqa: E402
    _classify_image_role,
    _detect_badges,
    _find_clip_polygon,
    _find_photo_rect,
    _guess_text_role,
    _is_dynamic_text,
    extract_page_layouts,
)
from openaec_reports.tools.page_classifier import ClassifiedPage, PageType, classify_pages  # noqa: E402
from openaec_reports.tools.pdf_extractor import (  # noqa: E402
    ImageElement,
    PathElement,
    RawPageData,
    RectElement,
    TextElement,
    _detect_corner_radius,
    extract_pdf,
)

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def simple_page():
    """RawPageData met basiselementen."""
    return RawPageData(
        page_number=1,
        width_pt=595.0,
        height_pt=842.0,
        texts=[
            TextElement("Titel", 50, 200, 300, 230, "Gotham-Bold", 28.0, "#40124A"),
            TextElement("Subtitel", 50, 240, 300, 260, "Gotham-Book", 16.0, "#45243D"),
        ],
        rects=[
            RectElement(0, 0, 300, 500, "#40124A", None, 0.0, "rect", 0.0),
        ],
        images=[],
        paths=[],
    )


@pytest.fixture
def page_with_paths():
    """RawPageData met paths."""
    return RawPageData(
        page_number=1,
        width_pt=595.0,
        height_pt=842.0,
        texts=[],
        rects=[],
        images=[],
        paths=[
            PathElement(
                path_type="polygon",
                points=[(0.0, 0.0), (300.0, 0.0), (200.0, 500.0), (0.0, 500.0), (0.0, 0.0)],
                fill_hex="#40124A",
                stroke_hex=None,
                is_closed=True,
                bbox_x=0.0,
                bbox_y=0.0,
                bbox_width=300.0,
                bbox_height=500.0,
            ),
        ],
    )


@pytest.fixture
def page_with_badges():
    """RawPageData met rounded rects en tekst (badges)."""
    return RawPageData(
        page_number=1,
        width_pt=595.0,
        height_pt=842.0,
        texts=[
            TextElement("betrouwbaar", 105, 610, 200, 625, "Gotham-Bold", 9.0, "#FFFFFF"),
        ],
        rects=[
            RectElement(100, 605, 110, 25, "#38BDA0", None, 0.0, "rect", 8.0),
        ],
        images=[],
        paths=[],
    )


@pytest.fixture
def cover_page(simple_page):
    """ClassifiedPage als cover."""
    return ClassifiedPage(page=simple_page, page_type=PageType.COVER, confidence=0.95)


@pytest.fixture
def sample_pdf(tmp_path) -> Path:
    """Multi-page PDF met cover, content, backcover."""
    doc = fitz.open()

    # Cover — groot blok + polygon path + tekst
    page = doc.new_page(width=595, height=842)
    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(0, 0, 300, 500))
    shape.finish(fill=(0.25, 0.07, 0.28))
    # Teken een polygon (driehoek)
    shape.draw_line(fitz.Point(0, 0), fitz.Point(300, 0))
    shape.draw_line(fitz.Point(300, 0), fitz.Point(200, 400))
    shape.draw_line(fitz.Point(200, 400), fitz.Point(0, 0))
    shape.finish(fill=(0.22, 0.74, 0.67))
    shape.commit()
    page.insert_text(fitz.Point(50, 200), "Rapport Titel", fontsize=28)

    # Content
    page = doc.new_page(width=595, height=842)
    page.insert_text(fitz.Point(50, 50), "1. Inleiding", fontsize=18)

    # Backcover — volledig gekleurd + contactinfo
    page = doc.new_page(width=595, height=842)
    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(0, 0, 595, 842))
    shape.finish(fill=(0.22, 0.74, 0.67))
    shape.commit()
    page.insert_text(fitz.Point(50, 300), "T. +31 (0)30 123 4567", fontsize=10)
    page.insert_text(fitz.Point(50, 320), "www.3bm.co.nl", fontsize=10)

    pdf_path = tmp_path / "test_rapport.pdf"
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


# ============================================================
# PathElement
# ============================================================


class TestPathElement:
    def test_dataclass_creation(self):
        p = PathElement(
            path_type="polygon",
            points=[(0, 0), (100, 0), (100, 100)],
            fill_hex="#FF0000",
        )
        assert p.path_type == "polygon"
        assert len(p.points) == 3
        assert p.fill_hex == "#FF0000"
        assert p.is_closed is True

    def test_defaults(self):
        p = PathElement(path_type="bezier", points=[(0, 0), (50, 50), (100, 0)])
        assert p.stroke_hex is None
        assert p.stroke_width == 0.0
        assert p.bbox_x == 0.0

    def test_in_raw_page_data(self):
        """PathElement is correct opgenomen in RawPageData."""
        page = RawPageData(
            page_number=1, width_pt=595, height_pt=842,
            paths=[PathElement("polygon", [(0, 0), (100, 0), (100, 100)])],
        )
        assert len(page.paths) == 1
        assert page.paths[0].path_type == "polygon"


# ============================================================
# RectElement corner_radius
# ============================================================


class TestRectCornerRadius:
    def test_default_zero(self):
        r = RectElement(0, 0, 100, 50)
        assert r.corner_radius == 0.0

    def test_set_corner_radius(self):
        r = RectElement(0, 0, 100, 50, corner_radius=8.0)
        assert r.corner_radius == 8.0

    def test_detect_corner_radius_no_curves(self):
        """Geen curves → radius 0."""
        items = [("l", type("P", (), {"x": 0, "y": 0})(), type("P", (), {"x": 100, "y": 0})())]
        assert _detect_corner_radius(items) == 0.0

    def test_detect_corner_radius_empty(self):
        assert _detect_corner_radius([]) == 0.0


# ============================================================
# _extract_paths (integratie met fitz)
# ============================================================


class TestExtractPathsIntegration:
    def test_extract_paths_from_polygon(self, sample_pdf):
        """Polygon wordt geextraheerd als PathElement."""
        pages = extract_pdf(sample_pdf)
        cover = pages[0]
        # De cover heeft een polygon (driehoek)
        assert len(cover.paths) >= 1

    def test_path_has_points(self, sample_pdf):
        pages = extract_pdf(sample_pdf)
        for path in pages[0].paths:
            assert len(path.points) >= 3

    def test_path_has_bbox(self, sample_pdf):
        pages = extract_pdf(sample_pdf)
        for path in pages[0].paths:
            assert path.bbox_width >= 0
            assert path.bbox_height >= 0

    def test_no_paths_on_text_only_page(self, sample_pdf):
        """Content pagina met alleen tekst heeft geen paths."""
        pages = extract_pdf(sample_pdf)
        content = pages[1]
        assert len(content.paths) == 0


# ============================================================
# layout_extractor
# ============================================================


class TestExtractPageLayouts:
    def test_returns_dict(self, sample_pdf):
        pages = extract_pdf(sample_pdf)
        classified = classify_pages(pages)
        layouts = extract_page_layouts(classified)
        assert isinstance(layouts, dict)

    def test_cover_in_layouts(self, sample_pdf):
        pages = extract_pdf(sample_pdf)
        classified = classify_pages(pages)
        layouts = extract_page_layouts(classified)
        assert PageType.COVER in layouts

    def test_backcover_in_layouts(self, sample_pdf):
        pages = extract_pdf(sample_pdf)
        classified = classify_pages(pages)
        layouts = extract_page_layouts(classified)
        assert PageType.BACKCOVER in layouts

    def test_content_not_in_layouts(self, sample_pdf):
        pages = extract_pdf(sample_pdf)
        classified = classify_pages(pages)
        layouts = extract_page_layouts(classified)
        assert PageType.CONTENT not in layouts

    def test_layout_has_page_dimensions(self, sample_pdf):
        pages = extract_pdf(sample_pdf)
        classified = classify_pages(pages)
        layouts = extract_page_layouts(classified)
        cover = layouts[PageType.COVER]
        assert cover.width_pt == pytest.approx(595, abs=1)
        assert cover.height_pt == pytest.approx(842, abs=1)


class TestExtractSinglePageLayout:
    def test_static_elements_from_rects(self, cover_page):
        layouts = extract_page_layouts([cover_page])
        layout = layouts[PageType.COVER]
        rect_elements = [e for e in layout.static_elements if e.element_type == "rect"]
        assert len(rect_elements) >= 1

    def test_text_zones_from_texts(self, cover_page):
        layouts = extract_page_layouts([cover_page])
        layout = layouts[PageType.COVER]
        assert len(layout.text_zones) >= 2

    def test_polygon_from_paths(self, page_with_paths):
        cp = ClassifiedPage(page=page_with_paths, page_type=PageType.COVER, confidence=0.95)
        layouts = extract_page_layouts([cp])
        layout = layouts[PageType.COVER]
        polygon_elements = [e for e in layout.static_elements if e.element_type == "polygon"]
        assert len(polygon_elements) == 1
        assert polygon_elements[0].points is not None


# ============================================================
# Helper functies
# ============================================================


class TestClassifyImageRole:
    def test_small_corner_image_is_logo(self):
        page = RawPageData(1, 595, 842)
        img = ImageElement(10, 10, 50, 30, 1)
        assert _classify_image_role(img, page) == "logo"

    def test_large_image_is_photo(self):
        page = RawPageData(1, 595, 842)
        img = ImageElement(0, 0, 400, 300, 1)
        assert _classify_image_role(img, page) == "photo"

    def test_medium_image_is_decorative(self):
        page = RawPageData(1, 595, 842)
        img = ImageElement(200, 200, 80, 80, 1)
        assert _classify_image_role(img, page) == "decorative"


class TestIsDynamicText:
    def test_static_text_detected(self):
        t = TextElement("ontdek ons", 0, 0, 100, 20, "Gotham", 12, "#000")
        assert _is_dynamic_text(t, PageType.COVER) is False

    def test_large_cover_text_is_dynamic(self):
        t = TextElement("Project Titel", 0, 0, 300, 40, "Gotham", 28, "#000")
        assert _is_dynamic_text(t, PageType.COVER) is True

    def test_colofon_label_is_static(self):
        t = TextElement("project", 0, 0, 100, 20, "Gotham", 10, "#000")
        assert _is_dynamic_text(t, PageType.COLOFON) is False

    def test_colofon_value_is_dynamic(self):
        t = TextElement("Bouwplan Schoolgebouw", 0, 0, 300, 20, "Gotham", 10, "#000")
        assert _is_dynamic_text(t, PageType.COLOFON) is True


class TestGuessTextRole:
    def test_cover_title(self):
        t = TextElement("Titel", 0, 0, 300, 40, "Gotham", 28, "#000")
        assert _guess_text_role(t, PageType.COVER) == "title"

    def test_cover_subtitle(self):
        t = TextElement("Sub", 0, 0, 200, 30, "Gotham", 18, "#000")
        assert _guess_text_role(t, PageType.COVER) == "subtitle"

    def test_cover_ontdek(self):
        t = TextElement("ontdek ons", 0, 0, 200, 30, "Gotham", 10, "#000")
        assert _guess_text_role(t, PageType.COVER) == "ontdek_text"

    def test_colofon_report_type(self):
        t = TextElement("Constructief", 0, 0, 200, 30, "Gotham", 20, "#000")
        assert _guess_text_role(t, PageType.COLOFON) == "report_type"

    def test_appendix_number(self):
        t = TextElement("Bijlage 1", 0, 0, 200, 50, "Gotham", 36, "#000")
        assert _guess_text_role(t, PageType.APPENDIX_DIVIDER) == "appendix_number"

    def test_fallback_text_role(self):
        t = TextElement("iets", 0, 100, 50, 110, "Gotham", 8, "#000")
        assert _guess_text_role(t, PageType.CONTENT) == "text_100"


class TestDetectBadges:
    def test_detects_badge(self, page_with_badges):
        badges = _detect_badges(page_with_badges)
        assert len(badges) == 1
        assert badges[0].label == "betrouwbaar"
        assert badges[0].corner_radius == 8.0

    def test_no_badges_without_rounded_rects(self, simple_page):
        badges = _detect_badges(simple_page)
        assert len(badges) == 0


class TestFindClipPolygon:
    def test_finds_large_polygon(self, page_with_paths):
        result = _find_clip_polygon(page_with_paths)
        assert result is not None
        assert len(result) >= 5

    def test_no_polygon_without_paths(self, simple_page):
        result = _find_clip_polygon(simple_page)
        assert result is None


class TestFindPhotoRect:
    def test_no_photo_without_images(self, simple_page):
        result = _find_photo_rect(simple_page)
        assert result is None

    def test_finds_large_image(self):
        page = RawPageData(
            1, 595, 842,
            images=[ImageElement(0, 0, 400, 300, 1)],
        )
        result = _find_photo_rect(page)
        assert result is not None
        assert len(result) == 4


# ============================================================
# generate_pages_yaml
# ============================================================


class TestGeneratePagesYaml:
    def test_returns_dict(self, sample_pdf):
        pages = extract_pdf(sample_pdf)
        classified = classify_pages(pages)
        layouts = extract_page_layouts(classified)
        result = generate_pages_yaml(layouts)
        assert isinstance(result, dict)

    def test_cover_key_present(self, sample_pdf):
        pages = extract_pdf(sample_pdf)
        classified = classify_pages(pages)
        layouts = extract_page_layouts(classified)
        result = generate_pages_yaml(layouts)
        assert "cover" in result

    def test_backcover_key_present(self, sample_pdf):
        pages = extract_pdf(sample_pdf)
        classified = classify_pages(pages)
        layouts = extract_page_layouts(classified)
        result = generate_pages_yaml(layouts)
        assert "backcover" in result

    def test_integrated_in_brand_yaml(self, sample_pdf):
        """page_layouts parameter integreert in generate_brand_yaml output."""
        from openaec_reports.tools.pattern_detector import analyze_brand

        pages = extract_pdf(sample_pdf)
        classified = classify_pages(pages)
        layouts = extract_page_layouts(classified)
        analysis = analyze_brand(classified, str(sample_pdf))

        import yaml
        yaml_str = generate_brand_yaml(analysis, "Test", "test", page_layouts=layouts)
        data = yaml.safe_load(yaml_str)
        assert "pages" in data
        assert "cover" in data["pages"]


# ============================================================
# visual_diff (unit tests zonder volledige PDF vergelijking)
# ============================================================


class TestVisualDiff:
    def test_import(self):
        from openaec_reports.tools.visual_diff import PageDiff
        assert PageDiff is not None

    def test_page_diff_dataclass(self):
        from openaec_reports.tools.visual_diff import PageDiff
        d = PageDiff(page_number=1, similarity_pct=95.5)
        assert d.page_number == 1
        assert d.similarity_pct == 95.5
        assert d.notes == []

    def test_file_not_found(self, tmp_path):
        from openaec_reports.tools.visual_diff import compare_pdfs
        with pytest.raises(FileNotFoundError):
            compare_pdfs(tmp_path / "nope.pdf", tmp_path / "also_nope.pdf")

    def test_compare_identical_pdfs(self, sample_pdf, tmp_path):
        """Vergelijking van een PDF met zichzelf geeft ~100% match."""
        try:
            import numpy as np  # noqa: F401
            from PIL import Image  # noqa: F401
        except ImportError:
            pytest.skip("Pillow/numpy niet geinstalleerd")

        from openaec_reports.tools.visual_diff import compare_pdfs
        diffs = compare_pdfs(sample_pdf, sample_pdf, tmp_path / "diffs")
        assert len(diffs) == 3
        for d in diffs:
            assert d.similarity_pct > 99.0

    def test_compare_specific_pages(self, sample_pdf, tmp_path):
        """Vergelijk alleen specifieke pagina's."""
        try:
            import numpy as np  # noqa: F401
            from PIL import Image  # noqa: F401
        except ImportError:
            pytest.skip("Pillow/numpy niet geinstalleerd")

        from openaec_reports.tools.visual_diff import compare_pdfs
        diffs = compare_pdfs(sample_pdf, sample_pdf, pages=[1, 3])
        assert len(diffs) == 2

    def test_print_diff_report(self, capsys):
        from openaec_reports.tools.visual_diff import PageDiff, print_diff_report
        diffs = [
            PageDiff(1, 98.5),
            PageDiff(2, 85.0),
            PageDiff(3, 50.0),
        ]
        print_diff_report(diffs)
        out = capsys.readouterr().out
        assert "Visual Diff Report" in out
        assert "98.5%" in out
        assert "[OK]" in out
        assert "[WARN]" in out
        assert "[FAIL]" in out


# ============================================================
# CLI commands (extract-layout, visual-diff)
# ============================================================


class TestCLIExtractLayout:
    def test_extract_layout_parseable(self):
        """extract-layout subcommand is geregistreerd in argparse."""
        # Test dat parser het commando herkent
        from unittest.mock import patch

        from openaec_reports.cli import main
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["openaec-report", "extract-layout", "--help"]):
                main()

    def test_visual_diff_parseable(self):
        """visual-diff subcommand is geregistreerd in argparse."""
        from unittest.mock import patch

        from openaec_reports.cli import main
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["openaec-report", "visual-diff", "--help"]):
                main()
