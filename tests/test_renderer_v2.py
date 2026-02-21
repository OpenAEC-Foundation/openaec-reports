"""Tests voor ReportGeneratorV2 — integratie + block types."""

from __future__ import annotations

from pathlib import Path

import pytest

fitz = pytest.importorskip("fitz", reason="pymupdf niet geinstalleerd")

from bm_reports.core.renderer_v2 import (
    ReportGeneratorV2, TemplateSet, FontManager, ContentRenderer,
    CoverGenerator, ColofonGenerator, _hex_to_rgb,
)

BASE = Path(__file__).parent.parent
STATIONERY_DIR = BASE / "src" / "bm_reports" / "assets" / "stationery" / "default"
JSON_PATH = BASE / "tests" / "test_data" / "sample_report.json"

SKIP_NO_STATIONERY = pytest.mark.skipif(
    not STATIONERY_DIR.exists() or not (STATIONERY_DIR / "standaard.pdf").exists(),
    reason="Stationery bestanden niet aanwezig",
)


# ============================================================
# Helpers
# ============================================================


class TestHexToRgb:
    def test_black(self):
        assert _hex_to_rgb("#000000") == (0.0, 0.0, 0.0)

    def test_white(self):
        r, g, b = _hex_to_rgb("#FFFFFF")
        assert r == pytest.approx(1.0)
        assert g == pytest.approx(1.0)

    def test_purple(self):
        r, g, b = _hex_to_rgb("#401246")
        assert r == pytest.approx(64 / 255)


# ============================================================
# TemplateSet
# ============================================================


class TestTemplateSet:
    def test_load_openaec(self):
        ts = TemplateSet("default")
        assert ts.cover
        assert ts.colofon
        assert ts.content_styles

    def test_blocks_property(self):
        ts = TemplateSet("default")
        assert "heading_1" in ts.blocks
        assert "paragraph" in ts.blocks
        assert "table" in ts.blocks

    def test_page_number_property(self):
        ts = TemplateSet("default")
        pn = ts.page_number
        assert "x" in pn
        assert "y_td" in pn

    def test_missing_brand_raises(self):
        with pytest.raises(FileNotFoundError):
            TemplateSet("nonexistent_brand_xyz")


# ============================================================
# FontManager
# ============================================================


class TestFontManager:
    def test_create(self):
        fm = FontManager()
        assert fm.inter_book is not None
        assert fm.inter_bold is not None

    def test_measure(self):
        fm = FontManager()
        w = fm.measure("Hello", 12.0)
        assert w > 0

    def test_wrap_text(self):
        fm = FontManager()
        lines = fm.wrap_text("Dit is een lange tekst die gewrapped moet worden", 9.5, 200)
        assert len(lines) >= 1

    def test_wrap_single_word(self):
        fm = FontManager()
        lines = fm.wrap_text("Kort", 9.5, 500)
        assert lines == ["Kort"]


# ============================================================
# ContentRenderer — block types
# ============================================================


@SKIP_NO_STATIONERY
class TestContentRendererBlocks:
    """Test alle block types in isolatie."""

    @pytest.fixture
    def renderer(self):
        ts = TemplateSet("default")
        fm = FontManager()
        stationery = {
            "standaard": STATIONERY_DIR / "standaard.pdf",
            "bijlagen": STATIONERY_DIR / "bijlagen.pdf",
            "achterblad": STATIONERY_DIR / "achterblad.pdf",
        }
        cr = ContentRenderer(ts, fm, stationery)
        cr._new_page()
        return cr

    def test_paragraph(self, renderer, tmp_path):
        y_before = renderer.y
        renderer.paragraph("Dit is een test paragraaf.")
        assert renderer.y > y_before
        renderer.save(tmp_path / "para.pdf")

    def test_heading_1(self, renderer, tmp_path):
        renderer.heading_1("1", "Hoofdstuk titel")
        renderer.save(tmp_path / "h1.pdf")

    def test_heading_2(self, renderer, tmp_path):
        renderer.heading_2("1.1", "Paragraaf titel")
        renderer.save(tmp_path / "h2.pdf")

    def test_bullet_list(self, renderer, tmp_path):
        renderer.bullet_list(["Item een", "Item twee", "Item drie"])
        renderer.save(tmp_path / "bullets.pdf")

    def test_table(self, renderer, tmp_path):
        y_before = renderer.y
        renderer.table({
            "title": "Testtabel",
            "headers": ["Kolom A", "Kolom B"],
            "rows": [["Waarde 1", "Waarde 2"], ["Waarde 3", "Waarde 4"]],
        })
        assert renderer.y > y_before
        renderer.save(tmp_path / "table.pdf")

    def test_table_no_title(self, renderer, tmp_path):
        renderer.table({
            "headers": ["X", "Y"],
            "rows": [["1", "2"]],
        })
        renderer.save(tmp_path / "table_notitle.pdf")

    def test_table_empty(self, renderer, tmp_path):
        """Lege tabel genereert geen error."""
        renderer.table({"headers": [], "rows": []})
        renderer.save(tmp_path / "table_empty.pdf")

    def test_spacer(self, renderer, tmp_path):
        y_before = renderer.y
        renderer.spacer({"height_mm": 20})
        expected_delta = 20 * 2.8346
        assert renderer.y - y_before == pytest.approx(expected_delta, abs=1)
        renderer.save(tmp_path / "spacer.pdf")

    def test_page_break(self, renderer, tmp_path):
        pages_before = renderer.page_count
        renderer.page_break()
        assert renderer.page_count == pages_before + 1
        renderer.save(tmp_path / "pagebreak.pdf")

    def test_calculation(self, renderer, tmp_path):
        y_before = renderer.y
        renderer.calculation({
            "title": "Buigend moment",
            "formula": "M = q * l^2 / 8",
            "substitution": "M = 8.5 * 7.2^2 / 8",
            "result": "55.1",
            "unit": "kNm",
            "reference": "NEN-EN 1992-1-1",
        })
        assert renderer.y > y_before
        renderer.save(tmp_path / "calc.pdf")

    def test_calculation_minimal(self, renderer, tmp_path):
        renderer.calculation({"title": "Simpele berekening", "result": "42", "unit": "kN"})
        renderer.save(tmp_path / "calc_min.pdf")

    def test_check_voldoet(self, renderer, tmp_path):
        renderer.check({
            "description": "Toetsing buigend moment",
            "required_value": "55.1 kNm",
            "calculated_value": "72.4 kNm",
            "unity_check": 0.76,
            "result": "VOLDOET",
        })
        renderer.save(tmp_path / "check_ok.pdf")

    def test_check_voldoet_niet(self, renderer, tmp_path):
        renderer.check({
            "description": "Toetsing dwarskracht",
            "required_value": "120 kN",
            "calculated_value": "115 kN",
            "unity_check": 1.04,
            "result": "VOLDOET NIET",
        })
        renderer.save(tmp_path / "check_fail.pdf")

    def test_image_missing(self, renderer, tmp_path):
        """Ontbrekende image geeft placeholder, geen crash."""
        renderer.image({"src": "/nonexistent/image.png"})
        renderer.save(tmp_path / "img_missing.pdf")

    def test_image_no_src(self, renderer, tmp_path):
        """Image zonder src genereert placeholder."""
        renderer.image({})
        renderer.save(tmp_path / "img_nosrc.pdf")

    def test_render_block_dispatch(self, renderer, tmp_path):
        """_render_block dispatcht naar juiste methode."""
        renderer._render_block({"type": "paragraph", "text": "Test"})
        renderer._render_block({"type": "spacer", "height_mm": 5})
        renderer._render_block({"type": "calculation", "title": "T", "result": "1"})
        renderer._render_block({"type": "check", "description": "T", "unity_check": 0.5, "result": "VOLDOET"})
        renderer.save(tmp_path / "dispatch.pdf")

    def test_unknown_block_type(self, renderer, tmp_path):
        """Onbekend block type logt warning, geen crash."""
        renderer._render_block({"type": "nonexistent_block_xyz"})
        renderer.save(tmp_path / "unknown.pdf")


# ============================================================
# Full integration test
# ============================================================


@SKIP_NO_STATIONERY
class TestIntegration:
    def test_from_json_generates_pdf(self, tmp_path):
        """Volledig rapport genereren van sample_report.json."""
        if not JSON_PATH.exists():
            pytest.skip("sample_report.json niet aanwezig")

        output = tmp_path / "rapport.pdf"
        result = ReportGeneratorV2.from_json(
            json_path=JSON_PATH,
            stationery_dir=STATIONERY_DIR,
            output_path=output,
            brand="default",
        )
        assert result.exists()
        assert result.stat().st_size > 10000

        # Verify page count
        doc = fitz.open(str(result))
        assert doc.page_count >= 5  # cover + colofon + toc + content + backcover
        doc.close()

    def test_generate_with_dict(self, tmp_path):
        """Genereer rapport vanuit dict (API use case)."""
        import json
        if not JSON_PATH.exists():
            pytest.skip("sample_report.json niet aanwezig")

        data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
        output = tmp_path / "rapport_dict.pdf"

        gen = ReportGeneratorV2(brand="default")
        result = gen.generate(data, STATIONERY_DIR, output)

        assert result.exists()
        assert result.stat().st_size > 10000
