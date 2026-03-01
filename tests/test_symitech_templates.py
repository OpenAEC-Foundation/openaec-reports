"""Tests voor Symitech template YAML configuraties."""

from pathlib import Path

import pytest
import yaml

TEMPLATES_DIR = (
    Path(__file__).parent.parent / "src" / "bm_reports" / "assets" / "templates"
)


class TestBicRapportTemplate:
    """Test symitech_bic_rapport.yaml template."""

    @pytest.fixture()
    def template(self) -> dict:
        path = TEMPLATES_DIR / "symitech_bic_rapport.yaml"
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_yaml_loads(self, template):
        assert template is not None

    def test_tenant_is_symitech(self, template):
        assert template["tenant"] == "symitech"

    def test_report_type(self, template):
        assert template["report_type"] == "bic_rapport"

    def test_format_and_orientation(self, template):
        assert template["format"] == "A4"
        assert template["orientation"] == "portrait"

    def test_structure(self, template):
        structure = template["structure"]
        assert "cover" in structure
        assert "colofon" in structure
        assert "sections" in structure
        assert "backcover" in structure

    def test_toc_disabled(self, template):
        assert template["toc"]["enabled"] is False

    def test_colofon_enabled(self, template):
        assert template["colofon"]["enabled"] is True

    def test_backcover_enabled(self, template):
        assert template["backcover"]["enabled"] is True

    def test_section_presets_defined(self, template):
        presets = template["section_presets"]
        assert len(presets) == 4

    def test_section_preset_titles(self, template):
        titles = [p["title"] for p in template["section_presets"]]
        assert "Locatie" in titles
        assert "BIC Controles" in titles
        assert "Kostenopgave" in titles
        assert "Objectbeschrijving" in titles

    def test_section_preset_block_types(self, template):
        presets = template["section_presets"]
        block_types = [p["default_blocks"][0]["type"] for p in presets]
        assert "location_detail" in block_types
        assert "bic_table" in block_types
        assert "cost_summary" in block_types
        assert "object_description" in block_types

    def test_kostenopgave_landscape(self, template):
        kosten = [p for p in template["section_presets"] if p["title"] == "Kostenopgave"]
        assert len(kosten) == 1
        assert kosten[0]["orientation"] == "landscape"


class TestSaneringTemplate:
    """Test symitech_sanering.yaml template."""

    @pytest.fixture()
    def template(self) -> dict:
        path = TEMPLATES_DIR / "symitech_sanering.yaml"
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_yaml_loads(self, template):
        assert template is not None

    def test_tenant_is_symitech(self, template):
        assert template["tenant"] == "symitech"

    def test_report_type(self, template):
        assert template["report_type"] == "sanering"

    def test_format_and_orientation(self, template):
        assert template["format"] == "A4"
        assert template["orientation"] == "portrait"

    def test_structure_includes_toc(self, template):
        structure = template["structure"]
        assert "cover" in structure
        assert "colofon" in structure
        assert "toc" in structure
        assert "sections" in structure
        assert "backcover" in structure

    def test_toc_enabled(self, template):
        assert template["toc"]["enabled"] is True
        assert template["toc"]["title"] == "Inhoudsopgave"

    def test_section_presets(self, template):
        presets = template["section_presets"]
        assert len(presets) == 4
        titles = [p["title"] for p in presets]
        assert "Locatie" in titles
        assert "Saneringswerkzaamheden" in titles
        assert "Objectbeschrijving" in titles
        assert "Kostenopgave" in titles

    def test_kostenopgave_landscape(self, template):
        kosten = [p for p in template["section_presets"] if p["title"] == "Kostenopgave"]
        assert len(kosten) == 1
        assert kosten[0]["orientation"] == "landscape"

    def test_saneringswerkzaamheden_uses_paragraph(self, template):
        sanering = [
            p for p in template["section_presets"]
            if p["title"] == "Saneringswerkzaamheden"
        ]
        assert len(sanering) == 1
        assert sanering[0]["default_blocks"][0]["type"] == "paragraph"
