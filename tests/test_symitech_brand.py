"""Tests voor Symitech brand configuratie."""

from pathlib import Path

import pytest
import yaml

from bm_reports.core.brand import BRANDS_DIR, BrandConfig, BrandLoader

SYMITECH_BRAND_DIR = BRANDS_DIR / "symitech"
SYMITECH_BRAND_YAML = SYMITECH_BRAND_DIR / "brand.yaml"


class TestSymitechBrandYaml:
    """Test dat brand.yaml geldig YAML is en de juiste structuur heeft."""

    def test_yaml_loads_without_errors(self):
        with SYMITECH_BRAND_YAML.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data is not None

    def test_brand_section_exists(self):
        with SYMITECH_BRAND_YAML.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "brand" in data
        assert "name" in data["brand"]
        assert "slug" in data["brand"]

    def test_colors_defined(self):
        with SYMITECH_BRAND_YAML.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        colors = data["colors"]
        assert colors["primary"] == "#006FAB"
        assert colors["secondary"] == "#94571E"
        assert colors["text"] == "#000000"

    def test_fonts_defined(self):
        with SYMITECH_BRAND_YAML.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        fonts = data["fonts"]
        assert "heading" in fonts
        assert "body" in fonts
        assert "heading_fallback" in fonts


class TestSymitechBrandLoader:
    """Test dat de BrandLoader de Symitech brand correct laadt."""

    def test_load_symitech(self):
        loader = BrandLoader()
        brand = loader.load("symitech")
        assert isinstance(brand, BrandConfig)
        assert brand.name == "Symitech B.V."

    def test_tenant_is_symitech(self):
        loader = BrandLoader()
        brand = loader.load("symitech")
        assert brand.tenant == "symitech"

    def test_slug_is_symitech(self):
        loader = BrandLoader()
        brand = loader.load("symitech")
        assert brand.slug == "symitech"

    def test_tagline(self):
        loader = BrandLoader()
        brand = loader.load("symitech")
        assert brand.tagline == "Synergie in Milieutechniek"

    def test_tenant_modules_has_four_items(self):
        loader = BrandLoader()
        brand = loader.load("symitech")
        assert len(brand.tenant_modules) == 4
        assert "bic_table" in brand.tenant_modules
        assert "cost_summary" in brand.tenant_modules
        assert "location_detail" in brand.tenant_modules
        assert "object_description" in brand.tenant_modules

    def test_module_config_colors_and_sizes(self):
        loader = BrandLoader()
        brand = loader.load("symitech")
        mc = brand.module_config
        assert mc["label_size"] == 10.0
        assert mc["value_size"] == 10.0
        assert mc["heading_size"] == 14.0
        assert mc["section_header_color"] == "#006FAB"
        assert mc["label_color"] == "#94571E"
        assert mc["value_color"] == "#000000"
        assert mc["line_color"] == "#006FAB"
        assert mc["line_width"] == 0.5
        assert mc["double_line_spacing"] == 2.7

    def test_stationery_defined(self):
        loader = BrandLoader()
        brand = loader.load("symitech")
        assert "cover" in brand.stationery
        assert "colofon" in brand.stationery
        assert "content_portrait" in brand.stationery
        assert "content_landscape" in brand.stationery
        assert "backcover" in brand.stationery

    def test_stationery_sources(self):
        loader = BrandLoader()
        brand = loader.load("symitech")
        assert brand.stationery["cover"].source == "stationery/cover.pdf"
        assert brand.stationery["backcover"].source == "stationery/backcover.pdf"

    def test_pages_has_all_types(self):
        loader = BrandLoader()
        brand = loader.load("symitech")
        assert "cover" in brand.pages
        assert "colofon" in brand.pages
        assert "content" in brand.pages
        assert "content_landscape" in brand.pages
        assert "backcover" in brand.pages

    def test_brand_dir_set(self):
        loader = BrandLoader()
        brand = loader.load("symitech")
        assert brand.brand_dir == SYMITECH_BRAND_DIR

    def test_logos_defined(self):
        loader = BrandLoader()
        brand = loader.load("symitech")
        assert "main" in brand.logos
        assert brand.logos["main"] == "logos/symitech_logo.png"


class TestSymitechBackwardCompatibility:
    """Test dat de bestaande 3BM brand nog steeds correct laadt."""

    def test_3bm_still_loads(self):
        loader = BrandLoader()
        brand = loader.load("3bm_cooperatie")
        assert brand.name == "3BM Coöperatie"
        assert brand.slug == "3bm-cooperatie"

    def test_3bm_modules_still_dict(self):
        loader = BrandLoader()
        brand = loader.load("3bm_cooperatie")
        assert isinstance(brand.modules, dict)
        assert "table" in brand.modules

    def test_3bm_tenant_modules_empty(self):
        loader = BrandLoader()
        brand = loader.load("3bm_cooperatie")
        assert brand.tenant_modules == []

    def test_default_brand_still_loads(self):
        loader = BrandLoader()
        brand = loader.load("default")
        assert brand.name == "Default"
