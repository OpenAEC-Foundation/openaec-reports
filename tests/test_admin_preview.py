"""Tests voor admin preview module — page-type preview rendering."""

from __future__ import annotations

import pytest
import yaml

from openaec_reports.admin.preview import (
    _generate_sample_data,
    _placeholder_for_field,
    render_page_type_preview,
)
from openaec_reports.core.template_config import PageType, parse_page_type


# ============================================================
# Sample data generation tests
# ============================================================


class TestPlaceholderForField:
    """Test de placeholder generator."""

    def test_known_field_name(self):
        assert _placeholder_for_field("name") == "Jan de Vries"

    def test_company_field(self):
        assert "B.V." in _placeholder_for_field("company_name")

    def test_date_field(self):
        assert "-" in _placeholder_for_field("invoice_date")

    def test_unknown_field(self):
        result = _placeholder_for_field("custom_field_xyz")
        assert result == "[custom_field_xyz]"

    def test_amount_with_row_index(self):
        r0 = _placeholder_for_field("amount", row_index=0)
        r1 = _placeholder_for_field("amount", row_index=1)
        assert r0 != r1  # Verschillende waarden per rij


class TestGenerateSampleData:
    """Test sample data generatie op basis van PageType."""

    def test_simple_text_zones(self):
        pt = parse_page_type({
            "name": "test",
            "text_zones": [
                {"bind": "client.name", "x_mm": 20, "y_mm": 30},
                {"bind": "project.title", "x_mm": 20, "y_mm": 40},
            ],
        })
        data = _generate_sample_data(pt)
        assert "client" in data
        assert "name" in data["client"]
        assert "project" in data
        assert "title" in data["project"]

    def test_skips_special_bindings(self):
        pt = parse_page_type({
            "name": "test",
            "text_zones": [
                {"bind": "_page_number", "x_mm": 180, "y_mm": 287},
                {"bind": "_static.Label", "x_mm": 20, "y_mm": 10},
            ],
        })
        data = _generate_sample_data(pt)
        # Special bindings should NOT create data entries
        assert "_page_number" not in data
        assert "_static" not in data

    def test_table_data_generation(self):
        pt = parse_page_type({
            "name": "test",
            "table": {
                "data_bind": "invoice.lines",
                "columns": [
                    {"field": "description"},
                    {"field": "amount"},
                ],
            },
        })
        data = _generate_sample_data(pt)
        assert "invoice" in data
        assert "lines" in data["invoice"]
        assert len(data["invoice"]["lines"]) == 3  # 3 sample rows
        assert "description" in data["invoice"]["lines"][0]
        assert "amount" in data["invoice"]["lines"][0]

    def test_empty_page_type(self):
        pt = parse_page_type({"name": "empty"})
        data = _generate_sample_data(pt)
        assert data == {}


# ============================================================
# Render tests
# ============================================================


MINIMAL_YAML = yaml.dump({
    "name": "test_preview",
    "text_zones": [
        {"bind": "client.name", "x_mm": 20, "y_mm": 30, "font": "body", "size": 12},
    ],
})

YAML_WITH_TABLE = yaml.dump({
    "name": "test_table",
    "text_zones": [
        {"bind": "_static.Factuur", "x_mm": 20, "y_mm": 10, "size": 18},
    ],
    "table": {
        "data_bind": "items",
        "columns": [
            {"field": "description", "width_mm": 80},
            {"field": "amount", "width_mm": 30, "align": "right"},
        ],
        "origin": {"x_mm": 20, "y_mm": 50},
        "row_height_mm": 6,
        "max_y_mm": 260,
    },
})

YAML_WITH_LINES = yaml.dump({
    "name": "test_lines",
    "line_zones": [
        {"x0_mm": 20, "y_mm": 100, "x1_mm": 190, "width_pt": 1, "color": "primary"},
    ],
})


class TestRenderPageTypePreview:
    """Test de preview render pipeline."""

    @pytest.fixture()
    def tenants_dir(self, tmp_path):
        """Maak een minimale tenant directory."""
        tenant_dir = tmp_path / "test_tenant"
        tenant_dir.mkdir()
        (tenant_dir / "stationery").mkdir()
        # Maak een minimal brand.yaml
        brand = {
            "name": "Test Brand",
            "slug": "test",
            "colors": {
                "primary": "#40124A",
                "secondary": "#38BDA0",
                "text": "#333333",
                "white": "#FFFFFF",
            },
            "fonts": {
                "body": "Helvetica",
                "heading": "Helvetica-Bold",
            },
        }
        (tenant_dir / "brand.yaml").write_text(yaml.dump(brand), encoding="utf-8")
        return tmp_path

    def test_minimal_yaml(self, tenants_dir):
        """Render een minimale page-type YAML."""
        png_bytes, width, height = render_page_type_preview(
            yaml_content=MINIMAL_YAML,
            tenant="test_tenant",
            tenants_dir=tenants_dir,
            dpi=72,
        )
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 100  # Minimaal een PNG header
        assert width > 0
        assert height > 0
        # PNG magic bytes
        assert png_bytes[:4] == b"\x89PNG"

    def test_yaml_with_table(self, tenants_dir):
        """Render met tabel en sample data."""
        png_bytes, width, height = render_page_type_preview(
            yaml_content=YAML_WITH_TABLE,
            tenant="test_tenant",
            tenants_dir=tenants_dir,
            dpi=72,
        )
        assert isinstance(png_bytes, bytes)
        assert png_bytes[:4] == b"\x89PNG"

    def test_yaml_with_lines(self, tenants_dir):
        """Render met line zones."""
        png_bytes, _, _ = render_page_type_preview(
            yaml_content=YAML_WITH_LINES,
            tenant="test_tenant",
            tenants_dir=tenants_dir,
            dpi=72,
        )
        assert png_bytes[:4] == b"\x89PNG"

    def test_custom_sample_data(self, tenants_dir):
        """Render met custom sample data."""
        sample = {"client": {"name": "Test Bedrijf"}}
        png_bytes, _, _ = render_page_type_preview(
            yaml_content=MINIMAL_YAML,
            tenant="test_tenant",
            tenants_dir=tenants_dir,
            sample_data=sample,
            dpi=72,
        )
        assert png_bytes[:4] == b"\x89PNG"

    def test_dpi_clamping(self, tenants_dir):
        """DPI wordt geclamped naar 72-300 bereik."""
        # Te laag → 72
        _, w_low, _ = render_page_type_preview(
            yaml_content=MINIMAL_YAML,
            tenant="test_tenant",
            tenants_dir=tenants_dir,
            dpi=10,
        )
        _, w_72, _ = render_page_type_preview(
            yaml_content=MINIMAL_YAML,
            tenant="test_tenant",
            tenants_dir=tenants_dir,
            dpi=72,
        )
        assert w_low == w_72

    def test_invalid_yaml_raises_valueerror(self, tenants_dir):
        """Ongeldige YAML gooit ValueError."""
        with pytest.raises(ValueError, match="Ongeldige YAML"):
            render_page_type_preview(
                yaml_content=": invalid: yaml: [",
                tenant="test_tenant",
                tenants_dir=tenants_dir,
            )

    def test_non_dict_yaml_raises_valueerror(self, tenants_dir):
        """Niet-dict YAML gooit ValueError."""
        with pytest.raises(ValueError, match="dict"):
            render_page_type_preview(
                yaml_content="- just a list",
                tenant="test_tenant",
                tenants_dir=tenants_dir,
            )

    def test_missing_stationery_still_renders(self, tenants_dir):
        """Ontbrekende stationery geeft geen fout — alleen witte achtergrond."""
        yaml_with_stationery = yaml.dump({
            "name": "test",
            "stationery": "non_existent.pdf",
            "text_zones": [{"bind": "client.name", "x_mm": 20, "y_mm": 30}],
        })
        png_bytes, _, _ = render_page_type_preview(
            yaml_content=yaml_with_stationery,
            tenant="test_tenant",
            tenants_dir=tenants_dir,
            dpi=72,
        )
        assert png_bytes[:4] == b"\x89PNG"
