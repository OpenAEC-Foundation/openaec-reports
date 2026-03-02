"""Tests voor landscape oriëntatie ondersteuning."""

from __future__ import annotations

from openaec_reports import A3, A4, Report
from openaec_reports.core.document import DocumentConfig


class TestEffectivePagesize:
    """Tests voor DocumentConfig.effective_pagesize property."""

    def test_portrait_effective_size(self):
        config = DocumentConfig(format=A4, orientation="portrait")
        assert config.effective_height_pt > config.effective_width_pt

    def test_landscape_effective_size(self):
        config = DocumentConfig(format=A4, orientation="landscape")
        assert config.effective_width_pt > config.effective_height_pt

    def test_landscape_swaps_dimensions(self):
        config = DocumentConfig(format=A4, orientation="landscape")
        assert config.effective_width_pt == A4.height_pt
        assert config.effective_height_pt == A4.width_pt

    def test_portrait_keeps_dimensions(self):
        config = DocumentConfig(format=A4, orientation="portrait")
        assert config.effective_width_pt == A4.width_pt
        assert config.effective_height_pt == A4.height_pt

    def test_landscape_a3(self):
        config = DocumentConfig(format=A3, orientation="landscape")
        assert config.effective_width_pt == A3.height_pt
        assert config.effective_height_pt == A3.width_pt

    def test_content_width_uses_effective(self):
        config_p = DocumentConfig(format=A4, orientation="portrait")
        config_l = DocumentConfig(format=A4, orientation="landscape")
        # Landscape content_width should be wider than portrait
        assert config_l.content_width_pt > config_p.content_width_pt

    def test_content_height_uses_effective(self):
        config_p = DocumentConfig(format=A4, orientation="portrait")
        config_l = DocumentConfig(format=A4, orientation="landscape")
        # Landscape content_height should be shorter than portrait
        assert config_l.content_height_pt < config_p.content_height_pt


class TestLandscapeBuild:
    """Tests voor het bouwen van landscape rapporten."""

    def test_landscape_build(self, tmp_path):
        report = Report(format=A4, project="Landscape Test", brand="default")
        report.document.config.orientation = "landscape"
        report.add_section("Test", content=["Landscape content."])
        output = tmp_path / "landscape.pdf"
        report.build(output)
        assert output.exists()
        assert output.stat().st_size > 500

    def test_landscape_with_cover(self, tmp_path):
        report = Report(format=A4, project="Landscape Cover", brand="default")
        report.document.config.orientation = "landscape"
        report.add_cover(subtitle="Landscape test")
        report.add_section("Test", content=["Content."])
        report.add_backcover()
        output = tmp_path / "landscape_cover.pdf"
        report.build(output)
        assert output.exists()
        assert output.stat().st_size > 500

    def test_from_dict_landscape(self, tmp_path):
        data = {
            "template": "structural",
            "project": "Landscape Dict Test",
            "format": "A4",
            "orientation": "landscape",
            "sections": [
                {
                    "title": "Test",
                    "content": [
                        {"type": "paragraph", "text": "Landscape paragraph."},
                    ],
                }
            ],
        }
        report = Report.from_dict(data)
        assert report.document.config.orientation == "landscape"
        output = tmp_path / "landscape_dict.pdf"
        report.build(output)
        assert output.exists()
        assert output.stat().st_size > 500

    def test_from_dict_default_portrait(self):
        data = {
            "template": "structural",
            "project": "Default Orientation",
            "sections": [],
        }
        report = Report.from_dict(data)
        assert report.document.config.orientation == "portrait"

    def test_from_dict_landscape_a3(self, tmp_path):
        data = {
            "template": "structural",
            "project": "A3 Landscape",
            "format": "A3",
            "orientation": "landscape",
            "sections": [
                {
                    "title": "Test",
                    "content": [{"type": "paragraph", "text": "A3 landscape."}],
                }
            ],
        }
        report = Report.from_dict(data)
        assert report.document.config.orientation == "landscape"
        output = tmp_path / "a3_landscape.pdf"
        report.build(output)
        assert output.exists()
