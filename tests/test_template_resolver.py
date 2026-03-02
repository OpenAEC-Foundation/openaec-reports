"""Tests voor template_resolver.py — YAML loading + caching."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from openaec_reports.core.template_config import PageType, TemplateConfig
from openaec_reports.core.template_resolver import TemplateResolver

# ============================================================
# Fixtures — YAML bestanden in tmp_path
# ============================================================


def _write_yaml(path: Path, data: dict) -> None:
    """Helper: schrijf YAML naar path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False)


@pytest.fixture()
def tenants_dir(tmp_path: Path) -> Path:
    """Maak een fake tenant structuur in tmp_path."""
    tenant = "test_co"
    templates_dir = tmp_path / tenant / "templates"
    page_types_dir = tmp_path / tenant / "page_types"

    # Template YAML
    _write_yaml(templates_dir / "rapport_a.yaml", {
        "name": "rapport_a",
        "tenant": "test_co",
        "pages": [
            {"type": "special", "page_type": "voorblad"},
            {"type": "fixed", "page_type": "inhoud", "repeat": "auto"},
            {"type": "special", "page_type": "achterblad"},
        ],
    })

    # Page type YAML's
    _write_yaml(page_types_dir / "voorblad.yaml", {
        "name": "voorblad",
        "stationery": "cover.pdf",
        "text_zones": [
            {"bind": "meta.title", "x_mm": 20, "y_mm": 100, "font": "heading", "size": 14},
        ],
    })

    _write_yaml(page_types_dir / "inhoud.yaml", {
        "name": "inhoud",
        "stationery": "content.pdf",
        "table": {
            "data_bind": "items",
            "columns": [
                {"field": "label", "width_mm": 80},
                {"field": "value", "width_mm": 40, "align": "right"},
            ],
        },
    })

    _write_yaml(page_types_dir / "achterblad.yaml", {
        "name": "achterblad",
        "stationery": "back.pdf",
    })

    return tmp_path


# ============================================================
# load_template
# ============================================================


class TestLoadTemplate:
    def test_loads_yaml(self, tenants_dir: Path) -> None:
        resolver = TemplateResolver(tenants_dir=tenants_dir)
        template = resolver.load_template("rapport_a", tenant="test_co")
        assert isinstance(template, TemplateConfig)
        assert template.name == "rapport_a"
        assert template.tenant == "test_co"
        assert len(template.pages) == 3

    def test_cached(self, tenants_dir: Path) -> None:
        resolver = TemplateResolver(tenants_dir=tenants_dir)
        t1 = resolver.load_template("rapport_a", tenant="test_co")
        t2 = resolver.load_template("rapport_a", tenant="test_co")
        assert t1 is t2

    def test_not_found_raises(self, tenants_dir: Path) -> None:
        resolver = TemplateResolver(tenants_dir=tenants_dir)
        with pytest.raises(FileNotFoundError):
            resolver.load_template("niet_bestaand", tenant="test_co")

    def test_auto_set_tenant(self, tenants_dir: Path) -> None:
        """Als 'tenant' ontbreekt in YAML, wordt het automatisch gezet."""
        no_tenant_yaml = tenants_dir / "test_co" / "templates" / "no_tenant.yaml"
        _write_yaml(no_tenant_yaml, {"name": "no_tenant", "pages": []})

        resolver = TemplateResolver(tenants_dir=tenants_dir)
        template = resolver.load_template("no_tenant", tenant="test_co")
        assert template.tenant == "test_co"


# ============================================================
# load_page_type
# ============================================================


class TestLoadPageType:
    def test_loads_yaml(self, tenants_dir: Path) -> None:
        resolver = TemplateResolver(tenants_dir=tenants_dir)
        pt = resolver.load_page_type("voorblad", tenant="test_co")
        assert isinstance(pt, PageType)
        assert pt.name == "voorblad"
        assert pt.stationery == "cover.pdf"
        assert len(pt.text_zones) == 1

    def test_cached(self, tenants_dir: Path) -> None:
        resolver = TemplateResolver(tenants_dir=tenants_dir)
        p1 = resolver.load_page_type("voorblad", tenant="test_co")
        p2 = resolver.load_page_type("voorblad", tenant="test_co")
        assert p1 is p2

    def test_not_found_raises(self, tenants_dir: Path) -> None:
        resolver = TemplateResolver(tenants_dir=tenants_dir)
        with pytest.raises(FileNotFoundError):
            resolver.load_page_type("onbekend", tenant="test_co")

    def test_auto_set_name(self, tenants_dir: Path) -> None:
        """Als 'name' ontbreekt in YAML, wordt het automatisch gezet."""
        no_name_yaml = tenants_dir / "test_co" / "page_types" / "no_name.yaml"
        _write_yaml(no_name_yaml, {"stationery": "x.pdf"})

        resolver = TemplateResolver(tenants_dir=tenants_dir)
        pt = resolver.load_page_type("no_name", tenant="test_co")
        assert pt.name == "no_name"

    def test_with_table(self, tenants_dir: Path) -> None:
        resolver = TemplateResolver(tenants_dir=tenants_dir)
        pt = resolver.load_page_type("inhoud", tenant="test_co")
        assert pt.table is not None
        assert pt.table.data_bind == "items"
        assert len(pt.table.columns) == 2


# ============================================================
# load_all_page_types
# ============================================================


class TestLoadAllPageTypes:
    def test_loads_all(self, tenants_dir: Path) -> None:
        resolver = TemplateResolver(tenants_dir=tenants_dir)
        template = resolver.load_template("rapport_a", tenant="test_co")
        page_types = resolver.load_all_page_types(template)

        assert isinstance(page_types, dict)
        assert "voorblad" in page_types
        assert "inhoud" in page_types
        assert "achterblad" in page_types
        assert len(page_types) == 3

    def test_deduplicates(self, tenants_dir: Path) -> None:
        """Als template dezelfde page_type meerdere keren gebruikt, één keer laden."""
        dup_yaml = tenants_dir / "test_co" / "templates" / "dup.yaml"
        _write_yaml(dup_yaml, {
            "name": "dup",
            "tenant": "test_co",
            "pages": [
                {"type": "special", "page_type": "voorblad"},
                {"type": "special", "page_type": "voorblad"},
            ],
        })

        resolver = TemplateResolver(tenants_dir=tenants_dir)
        template = resolver.load_template("dup", tenant="test_co")
        page_types = resolver.load_all_page_types(template)
        assert len(page_types) == 1
        assert "voorblad" in page_types


# ============================================================
# _load_yaml edge cases
# ============================================================


class TestLoadYaml:
    def test_non_dict_raises(self, tmp_path: Path) -> None:
        """YAML bestand dat geen dict is → ValueError."""
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("- item1\n- item2\n", encoding="utf-8")
        with pytest.raises(ValueError, match="geen dict"):
            TemplateResolver._load_yaml(bad_yaml)
