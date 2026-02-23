"""Tests voor core modules."""

import pytest

from bm_reports.core.document import A3, A4, MM_TO_PT, Document, DocumentConfig, Margins


class TestPageFormat:
    def test_a4_dimensions(self):
        assert A4.width_mm == 210
        assert A4.height_mm == 297

    def test_a3_dimensions(self):
        assert A3.width_mm == 297
        assert A3.height_mm == 420

    def test_size_pt_conversion(self):
        w, h = A4.size_pt
        assert abs(w - 210 * MM_TO_PT) < 0.01
        assert abs(h - 297 * MM_TO_PT) < 0.01


class TestMargins:
    def test_default_margins(self):
        m = Margins()
        assert m.top == 25.0
        assert m.bottom == 20.0
        assert m.left == 20.0
        assert m.right == 15.0

    def test_custom_margins(self):
        m = Margins(top=30, bottom=25, left=25, right=20)
        assert m.top_pt == pytest.approx(30 * MM_TO_PT, rel=1e-3)


class TestDocumentConfig:
    def test_content_dimensions(self):
        config = DocumentConfig()
        # A4: 210mm breed - 20mm links - 15mm rechts = 175mm
        expected_width = 175 * MM_TO_PT
        assert abs(config.content_width_pt - expected_width) < 0.1


class TestDocument:
    def test_create_document(self):
        doc = Document(project="Test", project_number="2026-001")
        assert doc.config.project == "Test"
        assert doc.config.project_number == "2026-001"
        assert len(doc.elements) == 0

    def test_add_element(self):
        doc = Document()
        doc.add_element("dummy")
        assert len(doc.elements) == 1


class TestPageTemplates:
    def test_create_page_templates_returns_five(self):
        from bm_reports.core.page_templates import create_page_templates

        config = DocumentConfig()
        templates = create_page_templates(config)
        assert len(templates) == 5

    def test_template_ids(self):
        from bm_reports.core.page_templates import create_page_templates

        config = DocumentConfig()
        templates = create_page_templates(config)
        ids = [t.id for t in templates]
        assert ids == ["cover", "colofon", "content", "appendix_divider", "backcover"]

    def test_content_template_has_onpage(self):
        from bm_reports.core.page_templates import create_page_templates

        config = DocumentConfig()
        templates = create_page_templates(config)
        # content is nu de derde template (index 2)
        content_template = templates[2]
        assert content_template.id == "content"
        # Content template moet een onPage callback hebben
        assert content_template.onPage is not None


class TestStyles:
    def test_bm_colors(self):
        from bm_reports.core.styles import BM_COLORS

        assert BM_COLORS.primary == "#40124A"
        assert BM_COLORS.secondary == "#38BDA0"
        assert BM_COLORS.accent == "#2ECC71"
        assert BM_COLORS.warning == "#E74C3C"

    def test_bm_colors_as_hex(self):
        from reportlab.lib.colors import Color

        from bm_reports.core.styles import BM_COLORS

        color = BM_COLORS.as_hex("primary")
        assert isinstance(color, Color)

    def test_bm_colors_hex_shortcut(self):
        from reportlab.lib.colors import Color

        from bm_reports.core.styles import BM_COLORS

        color = BM_COLORS.hex("primary")
        assert isinstance(color, Color)

    def test_create_stylesheet_has_expected_styles(self):
        from bm_reports.core.styles import create_stylesheet

        styles = create_stylesheet()
        expected_names = [
            "Normal", "Heading1", "Heading2", "Heading3",
            "Caption", "Footer", "CoverTitle", "CoverSubtitle",
        ]
        for name in expected_names:
            assert name in styles, f"Style '{name}' ontbreekt in stylesheet"


class TestSmokeImports:
    """Smoke tests: controleer dat imports werken na architectuur opschoning."""

    def test_import_bm_reports(self):
        from bm_reports import A3, A4, Document, Report

        assert Report is not None
        assert A4 is not None
        assert A3 is not None
        assert Document is not None

    def test_no_header_footer_in_components(self):
        try:
            import bm_reports.components as comp
        except ImportError:
            pytest.skip("Optional dependency (svglib) not installed")

        assert not hasattr(comp, "Header"), "Header mag niet meer in components staan"
        assert not hasattr(comp, "Footer"), "Footer mag niet meer in components staan"

    def test_components_exports(self):
        try:
            from bm_reports.components import (
                CalculationBlock,
                CheckBlock,  # noqa: F401
                ImageBlock,  # noqa: F401
                KadasterMap,  # noqa: F401
                TableBlock,  # noqa: F401
                TitleBlock,
            )
        except ImportError:
            pytest.skip("Optional dependency (svglib) not installed")

        assert TitleBlock is not None
        assert CalculationBlock is not None

    def test_bm_doc_template_exists(self):
        from bm_reports.core.engine import BMDocTemplate

        assert BMDocTemplate is not None
