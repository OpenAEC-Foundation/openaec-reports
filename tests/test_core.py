"""Tests voor core modules."""

import pytest

from bm_reports.core.document import A4, A3, PageFormat, Margins, DocumentConfig, Document, MM_TO_PT


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
