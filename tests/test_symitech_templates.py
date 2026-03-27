"""Tests voor Symitech template YAML configuraties (V3 TemplateEngine format)."""

from pathlib import Path

import pytest
import yaml

TEMPLATES_DIR = (
    Path(__file__).parent.parent / "tenants" / "symitech" / "templates"
)


class TestBicRapportTemplate:
    """Test bic_rapport.yaml template (V3 TemplateEngine format)."""

    @pytest.fixture()
    def template(self) -> dict:
        path = TEMPLATES_DIR / "bic_rapport.yaml"
        if not path.exists():
            pytest.skip("bic_rapport.yaml not found in tenant templates")
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_yaml_loads(self, template):
        assert template is not None

    def test_tenant_is_symitech(self, template):
        assert template["tenant"] == "symitech"

    def test_report_type(self, template):
        assert template["report_type"] == "bic_rapport"

    def test_name(self, template):
        assert template["name"] == "symitech_bic_rapport"

    def test_has_pages_list(self, template):
        """V3 format: pages is a list of page definitions."""
        assert "pages" in template
        assert isinstance(template["pages"], list)
        assert len(template["pages"]) > 0

    def test_first_page_is_voorblad(self, template):
        first = template["pages"][0]
        assert first["type"] == "special"
        assert first["page_type"] == "voorblad_bic"

    def test_last_page_is_achterblad(self, template):
        last = template["pages"][-1]
        assert last["type"] == "special"
        assert last["page_type"] == "achterblad"

    def test_has_inhoudsopgave(self, template):
        toc_pages = [p for p in template["pages"] if p.get("page_type") == "inhoudsopgave"]
        assert len(toc_pages) == 1

    def test_has_landscape_pages(self, template):
        landscape = [p for p in template["pages"] if p.get("orientation") == "landscape"]
        assert len(landscape) > 0, "Template should contain landscape pages"


class TestBicFactuurTemplate:
    """Test bic_factuur.yaml template."""

    @pytest.fixture()
    def template(self) -> dict:
        path = TEMPLATES_DIR / "bic_factuur.yaml"
        if not path.exists():
            pytest.skip("bic_factuur.yaml not found in tenant templates")
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_yaml_loads(self, template):
        assert template is not None

    def test_tenant_is_symitech(self, template):
        assert template["tenant"] == "symitech"

    def test_has_pages_list(self, template):
        assert "pages" in template
        assert isinstance(template["pages"], list)
