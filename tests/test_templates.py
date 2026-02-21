"""Tests voor template loader."""

import pytest
from pathlib import Path

from bm_reports.core.template_loader import TemplateLoader, TemplateConfig, TEMPLATES_DIR


class TestTemplateLoader:
    def test_load_structural_template(self):
        loader = TemplateLoader()
        config = loader.load("structural_report")

        assert isinstance(config, TemplateConfig)
        assert config.name == "structural_report"
        assert config.report_type == "structural"
        assert config.format == "A4"
        assert config.orientation == "portrait"

    def test_load_structural_margins(self):
        loader = TemplateLoader()
        config = loader.load("structural_report")

        assert config.margins["top"] == 25
        assert config.margins["bottom"] == 20
        assert config.margins["left"] == 20
        assert config.margins["right"] == 15

    def test_load_structural_structure(self):
        loader = TemplateLoader()
        config = loader.load("structural_report")

        assert "cover" in config.structure
        assert "colofon" in config.structure
        assert "toc" in config.structure
        assert "backcover" in config.structure

    def test_load_structural_toc_config(self):
        loader = TemplateLoader()
        config = loader.load("structural_report")

        assert config.toc.get("enabled") is True
        assert config.toc.get("max_depth") == 3

    def test_load_structural_raw_data(self):
        loader = TemplateLoader()
        config = loader.load("structural_report")

        assert isinstance(config.raw, dict)
        assert "report_type" in config.raw

    def test_load_nonexistent_raises(self):
        loader = TemplateLoader()
        with pytest.raises(FileNotFoundError, match="niet gevonden"):
            loader.load("nonexistent_template")

    def test_list_templates(self):
        loader = TemplateLoader()
        templates = loader.list_templates()

        assert isinstance(templates, list)
        assert len(templates) >= 1

        names = [t["name"] for t in templates]
        assert "structural_report" in names

    def test_list_templates_contains_report_type(self):
        loader = TemplateLoader()
        templates = loader.list_templates()

        structural = next(t for t in templates if t["name"] == "structural_report")
        assert structural["report_type"] == "structural"

    def test_load_with_yaml_extension(self):
        loader = TemplateLoader()
        config = loader.load("structural_report.yaml")
        assert config.report_type == "structural"

    def test_custom_templates_dir(self, tmp_path):
        # Maak een test YAML aan
        test_yaml = tmp_path / "test_report.yaml"
        test_yaml.write_text("report_type: test\nformat: A3\n", encoding="utf-8")

        loader = TemplateLoader(templates_dir=tmp_path)
        config = loader.load("test_report")

        assert config.report_type == "test"
        assert config.format == "A3"

    def test_list_templates_empty_dir(self, tmp_path):
        loader = TemplateLoader(templates_dir=tmp_path)
        templates = loader.list_templates()
        assert templates == []

    def test_templates_dir_constant(self):
        assert TEMPLATES_DIR.name == "templates"
        assert TEMPLATES_DIR.parent.name == "assets"
