"""Tests voor brand extraction wizard — backend logica en endpoints."""

from __future__ import annotations

import pytest
import yaml
from fastapi.testclient import TestClient

from openaec_reports.admin.brand_extraction import (
    _generate_modules_scaffold,
    _generate_stationery_scaffold,
    _serialize_layouts,
    generate_prompt_package,
    get_reference_pages_yaml,
    merge_brand_yaml,
)
from openaec_reports.api import app

# ============================================================
# Unit tests: brand_extraction.py functies
# ============================================================


class TestMergeBrandYaml:
    """Tests voor merge_brand_yaml()."""

    def test_minimal_merge(self):
        """Merge met minimale data produceert geldige YAML."""
        edited = {
            "colors": {"primary": "#40124A", "text": "#45243D"},
            "fonts": {"heading": "Inter-Bold", "body": "Inter-Regular"},
            "header": {"height": 0, "elements": []},
            "footer": {"height": 17, "elements": []},
            "styles": {
                "Normal": {
                    "fontName": "Inter-Regular",
                    "fontSize": 9.5,
                    "leading": 12.0,
                    "textColor": "#45243D",
                },
            },
        }

        result = merge_brand_yaml(
            edited_extraction=edited,
            pages_yaml_str=None,
            brand_name="Test Bureau",
            brand_slug="test-bureau",
        )

        parsed = yaml.safe_load(result)
        assert parsed["brand"]["name"] == "Test Bureau"
        assert parsed["brand"]["slug"] == "test-bureau"
        assert parsed["colors"]["primary"] == "#40124A"
        assert parsed["fonts"]["heading"] == "Inter-Bold"
        assert "stationery" in parsed
        assert "modules" in parsed

    def test_merge_with_pages_yaml(self):
        """Merge met pages YAML integreert de pages sectie."""
        edited = {
            "colors": {"primary": "#333"},
            "fonts": {"body": "Arial"},
        }

        pages_yaml = """
pages:
  cover:
    purple_rect_y_ref: 218.0
    clip_polygon:
      - [350, 160]
      - [538, 347]
  backcover:
    white_polygon:
      - [0, 0]
      - [0, 698]
"""

        result = merge_brand_yaml(
            edited_extraction=edited,
            pages_yaml_str=pages_yaml,
            brand_name="Test",
            brand_slug="test",
        )

        parsed = yaml.safe_load(result)
        assert "pages" in parsed
        assert "cover" in parsed["pages"]
        assert parsed["pages"]["cover"]["purple_rect_y_ref"] == 218.0
        assert len(parsed["pages"]["cover"]["clip_polygon"]) == 2
        assert "backcover" in parsed["pages"]

    def test_merge_pages_yaml_without_wrapper(self):
        """Merge werkt ook als pages YAML geen 'pages:' key heeft."""
        edited = {"colors": {}, "fonts": {}}

        pages_yaml = """
cover:
  title_size_ref: 28.9
backcover:
  logo_key: main
"""

        result = merge_brand_yaml(
            edited_extraction=edited,
            pages_yaml_str=pages_yaml,
            brand_name="Test",
            brand_slug="test",
        )

        parsed = yaml.safe_load(result)
        assert parsed["pages"]["cover"]["title_size_ref"] == 28.9

    def test_merge_invalid_pages_yaml_raises(self):
        """Ongeldige pages YAML geeft ValueError."""
        edited = {"colors": {}, "fonts": {}}
        invalid_yaml = "cover:\n  - [invalid: {yaml"

        with pytest.raises(ValueError, match="Ongeldige pages YAML"):
            merge_brand_yaml(
                edited_extraction=edited,
                pages_yaml_str=invalid_yaml,
                brand_name="Test",
                brand_slug="test",
            )

    def test_merge_includes_contact(self):
        """Contact info wordt correct meegenomen."""
        edited = {
            "colors": {},
            "fonts": {},
            "contact": {
                "name": "Bureau X",
                "address": "Straat 1",
                "website": "bureau-x.nl",
            },
        }

        result = merge_brand_yaml(
            edited_extraction=edited,
            pages_yaml_str=None,
            brand_name="Bureau X",
            brand_slug="bureau-x",
        )

        parsed = yaml.safe_load(result)
        assert parsed["contact"]["name"] == "Bureau X"
        assert parsed["contact"]["website"] == "bureau-x.nl"

    def test_merge_default_logos(self):
        """Zonder logos in extractie worden defaults gegenereerd."""
        edited = {"colors": {}, "fonts": {}}

        result = merge_brand_yaml(
            edited_extraction=edited,
            pages_yaml_str=None,
            brand_name="Test",
            brand_slug="my-brand",
        )

        parsed = yaml.safe_load(result)
        assert parsed["logos"]["main"] == "logos/my-brand.png"
        assert parsed["logos"]["white"] == "logos/my-brand-wit.png"


class TestGeneratePromptPackage:
    """Tests voor generate_prompt_package()."""

    def test_basic_prompt(self):
        """Prompt bevat alle verwachte secties."""
        extraction = {
            "colors": {"primary": "#40124A", "secondary": "#38BDA0"},
            "fonts": {"heading": "Inter-Bold", "body": "Inter-Regular"},
            "styles": {
                "Normal": {
                    "fontName": "Inter-Regular",
                    "fontSize": 9.5,
                    "leading": 12.0,
                    "textColor": "#45243D",
                },
            },
            "page_classifications": [
                {"page_number": 1, "type": "cover", "confidence": 0.95},
                {"page_number": 2, "type": "colofon", "confidence": 0.85},
            ],
        }

        page_images = {"cover": "page_001.png", "colofon": "page_002.png"}

        result = generate_prompt_package(
            extraction=extraction,
            page_image_map=page_images,
            brand_name="OpenAEC Test",
            brand_slug="openaec-test",
        )

        assert "# Brand Extraction — OpenAEC Test" in result
        assert "#40124A" in result
        assert "Inter-Bold" in result
        assert "page_001.png" in result
        assert "COVER" in result
        assert "Coordinatensysteem" in result

    def test_prompt_with_reference(self):
        """Prompt bevat referentie voorbeeld als meegegeven."""
        extraction = {
            "colors": {},
            "fonts": {},
            "styles": {},
            "page_classifications": [],
        }

        ref_yaml = "pages:\n  cover:\n    title_size_ref: 28.9"

        result = generate_prompt_package(
            extraction=extraction,
            page_image_map={},
            brand_name="Test",
            brand_slug="test",
            reference_pages_yaml=ref_yaml,
        )

        assert "Referentie Voorbeeld" in result
        assert "title_size_ref: 28.9" in result

    def test_prompt_with_layouts(self):
        """Prompt bevat layout data als beschikbaar."""
        extraction = {
            "colors": {},
            "fonts": {},
            "styles": {},
            "page_classifications": [],
            "page_layouts": {
                "cover": {
                    "badges": [{"label": "MEEDENKEN", "bg_color": "#f0c385"}],
                },
            },
        }

        result = generate_prompt_package(
            extraction=extraction,
            page_image_map={},
            brand_name="Test",
            brand_slug="test",
        )

        assert "MEEDENKEN" in result
        assert "Gedetecteerde Layout" in result


class TestGetReferencePages:
    """Tests voor get_reference_pages_yaml()."""

    def test_returns_none_for_missing(self, tmp_path):
        """Retourneert None als default niet bestaat."""
        result = get_reference_pages_yaml(tmp_path)
        assert result is None

    def test_returns_pages_yaml(self, tmp_path):
        """Retourneert pages-sectie uit bestaande brand.yaml."""
        tenant_dir = tmp_path / "default"
        tenant_dir.mkdir()

        brand_data = {
            "brand": {"name": "OpenAEC"},
            "colors": {"primary": "#40124A"},
            "pages": {
                "cover": {"title_size_ref": 28.9},
                "backcover": {"logo_key": "main"},
            },
        }
        (tenant_dir / "brand.yaml").write_text(
            yaml.dump(brand_data), encoding="utf-8"
        )

        result = get_reference_pages_yaml(tmp_path)
        assert result is not None
        assert "title_size_ref" in result
        assert "28.9" in result


class TestScaffolds:
    """Tests voor de auto-gegenereerde scaffolds."""

    def test_stationery_scaffold(self):
        """Stationery scaffold bevat alle verwachte page types."""
        scaffold = _generate_stationery_scaffold()
        expected = {"cover", "colofon", "content", "toc",
                    "appendix_divider", "backcover"}
        assert set(scaffold.keys()) == expected
        assert scaffold["content"]["content_frame"]["x_pt"] == 90.0

    def test_modules_scaffold(self):
        """Modules scaffold bevat table, calculation, check."""
        scaffold = _generate_modules_scaffold()
        assert "table" in scaffold
        assert "calculation" in scaffold
        assert "check" in scaffold
        assert scaffold["table"]["header_bg"] == "$colors.table_header_bg"


class TestSerializeLayouts:
    """Tests voor _serialize_layouts()."""

    def test_empty_layouts(self):
        """Lege input geeft leeg resultaat."""
        assert _serialize_layouts({}) == {}

    def test_serializes_basic_layout(self):
        """Layout met elementen wordt correct geserialiseerd."""
        from openaec_reports.tools.layout_extractor import (
            BadgeSpec,
            PageLayout,
            StaticElement,
            TextZone,
        )
        from openaec_reports.tools.page_classifier import PageType

        layout = PageLayout(
            page_type=PageType.COVER,
            page_number=1,
            width_pt=595.28,
            height_pt=841.89,
            static_elements=[
                StaticElement(
                    element_type="rect",
                    x_pt=0,
                    y_pt=218.3,
                    width_pt=595.3,
                    height_pt=623.6,
                    fill_color="#40124A",
                ),
            ],
            text_zones=[
                TextZone(
                    name="title",
                    x_pt=54.3,
                    y_pt=93.5,
                    font="Inter-Bold",
                    size=28.9,
                    color="#FFFFFF",
                    is_dynamic=True,
                ),
            ],
            badges=[
                BadgeSpec(
                    label="MEEDENKEN",
                    bg_color="#f0c385",
                    text_color="#40124A",
                    x_pt=297.6,
                    y_pt=298.8,
                    width_pt=112.0,
                    height_pt=34.0,
                    corner_radius=17.0,
                    font_size=10.2,
                ),
            ],
            clip_polygon=[(350.8, 159.8), (538.6, 347.6)],
            photo_rect=(55.6, 161.6, 484.0, 560.8),
        )

        result = _serialize_layouts({PageType.COVER: layout})

        assert "cover" in result
        cover = result["cover"]
        assert cover["page_number"] == 1
        assert len(cover["static_elements"]) == 1
        assert cover["static_elements"][0]["fill_color"] == "#40124A"
        assert len(cover["text_zones"]) == 1
        assert cover["text_zones"][0]["name"] == "title"
        assert len(cover["badges"]) == 1
        assert cover["badges"][0]["label"] == "MEEDENKEN"
        assert cover["clip_polygon"] == [[350.8, 159.8], [538.6, 347.6]]
        assert cover["photo_rect"] == [55.6, 161.6, 484.0, 560.8]


# ============================================================
# API endpoint tests
# ============================================================


class TestBrandExtractEndpoints:
    """Tests voor de brand extraction API endpoints."""

    def test_extract_requires_auth(self):
        """Brand extract zonder auth → 401."""
        client = TestClient(app)
        r = client.post(
            "/api/admin/tenants/test/brand-extract",
            files={"pdf_file": ("test.pdf", b"%PDF-dummy", "application/pdf")},
        )
        assert r.status_code == 401

    def test_extract_invalid_pdf(self, admin_client):
        """Brand extract met niet-PDF bestand → 400."""
        r = admin_client.post(
            "/api/admin/tenants/test/brand-extract",
            files={"pdf_file": ("test.txt", b"not a pdf", "text/plain")},
            data={"brand_name": "Test"},
        )
        assert r.status_code == 400
        assert "geldig PDF" in r.json()["detail"]

    def test_extract_nonexistent_tenant(self, admin_client, tmp_path, monkeypatch):
        """Brand extract voor onbekende tenant → 404."""
        monkeypatch.setenv("OPENAEC_TENANTS_DIR", str(tmp_path))

        r = admin_client.post(
            "/api/admin/tenants/nonexistent/brand-extract",
            files={"pdf_file": ("test.pdf", b"%PDF-dummy", "application/pdf")},
            data={"brand_name": "Test"},
        )
        assert r.status_code == 404

    def test_analysis_page_image_not_found(self, admin_client, tmp_path, monkeypatch):
        """Niet-bestaande pagina-afbeelding → 404."""
        monkeypatch.setenv("OPENAEC_TENANTS_DIR", str(tmp_path))
        tenant_dir = tmp_path / "test-tenant"
        tenant_dir.mkdir()

        r = admin_client.get(
            "/api/admin/tenants/test-tenant/analysis/pages/page_001.png"
        )
        assert r.status_code == 404

    def test_analysis_page_image_non_png(self, admin_client):
        """Niet-PNG bestand → 400."""
        r = admin_client.get(
            "/api/admin/tenants/test/analysis/pages/page_001.jpg"
        )
        assert r.status_code == 400
        assert "png" in r.json()["detail"].lower()

    def test_analysis_page_image_served(
        self, admin_client, tmp_path, monkeypatch
    ):
        """Bestaande pagina-afbeelding wordt correct geserveerd."""
        monkeypatch.setenv("OPENAEC_TENANTS_DIR", str(tmp_path))
        tenant_dir = tmp_path / "test-tenant"
        pages_dir = tenant_dir / "analysis" / "pages"
        pages_dir.mkdir(parents=True)

        # Maak een dummy PNG (minimale header)
        png_header = (
            b"\x89PNG\r\n\x1a\n"
            + b"\x00" * 100  # Dummy data
        )
        (pages_dir / "page_001.png").write_bytes(png_header)

        r = admin_client.get(
            "/api/admin/tenants/test-tenant/analysis/pages/page_001.png"
        )
        assert r.status_code == 200
        assert r.headers["content-type"] == "image/png"

    def test_prompt_package_endpoint(
        self, admin_client, tmp_path, monkeypatch
    ):
        """Prompt package endpoint retourneert markdown."""
        monkeypatch.setenv("OPENAEC_TENANTS_DIR", str(tmp_path))
        tenant_dir = tmp_path / "test-tenant"
        tenant_dir.mkdir()

        r = admin_client.post(
            "/api/admin/tenants/test-tenant/brand-extract/prompt-package",
            json={
                "edited_extraction": {
                    "brand": {"name": "Test Bureau", "slug": "test-bureau"},
                    "colors": {"primary": "#333"},
                    "fonts": {"body": "Arial"},
                    "styles": {},
                    "page_classifications": [],
                },
            },
        )

        assert r.status_code == 200
        data = r.json()
        assert "prompt" in data
        assert "# Brand Extraction" in data["prompt"]
        assert "page_images" in data

    def test_merge_endpoint(self, admin_client, tmp_path, monkeypatch):
        """Brand merge endpoint schrijft brand.yaml."""
        monkeypatch.setenv("OPENAEC_TENANTS_DIR", str(tmp_path))
        tenant_dir = tmp_path / "merge-test"
        tenant_dir.mkdir()

        pages_yaml = "pages:\n  cover:\n    title_size_ref: 28.9"

        r = admin_client.post(
            "/api/admin/tenants/merge-test/brand-merge",
            json={
                "edited_extraction": {
                    "colors": {"primary": "#40124A"},
                    "fonts": {"body": "Inter-Regular"},
                    "styles": {},
                },
                "pages_yaml": pages_yaml,
                "brand_name": "Merge Test",
                "brand_slug": "merge-test",
            },
        )

        assert r.status_code == 200
        data = r.json()
        assert "yaml" in data
        assert "Merge Test" in data["yaml"]

        # Controleer dat brand.yaml geschreven is
        brand_path = tenant_dir / "brand.yaml"
        assert brand_path.exists()
        saved = yaml.safe_load(brand_path.read_text(encoding="utf-8"))
        assert saved["brand"]["name"] == "Merge Test"
        assert saved["pages"]["cover"]["title_size_ref"] == 28.9

    def test_merge_invalid_pages_yaml(self, admin_client, tmp_path, monkeypatch):
        """Merge met ongeldige pages YAML → 422."""
        monkeypatch.setenv("OPENAEC_TENANTS_DIR", str(tmp_path))
        tenant_dir = tmp_path / "bad-merge"
        tenant_dir.mkdir()

        r = admin_client.post(
            "/api/admin/tenants/bad-merge/brand-merge",
            json={
                "edited_extraction": {"colors": {}, "fonts": {}},
                "pages_yaml": "cover:\n  - [invalid: {yaml",
                "brand_name": "Test",
            },
        )

        assert r.status_code == 422

    def test_merge_without_pages(self, admin_client, tmp_path, monkeypatch):
        """Merge zonder pages YAML werkt (alleen auto-generated secties)."""
        monkeypatch.setenv("OPENAEC_TENANTS_DIR", str(tmp_path))
        tenant_dir = tmp_path / "no-pages"
        tenant_dir.mkdir()

        r = admin_client.post(
            "/api/admin/tenants/no-pages/brand-merge",
            json={
                "edited_extraction": {
                    "colors": {"primary": "#333"},
                    "fonts": {"body": "Arial"},
                },
                "brand_name": "No Pages Test",
            },
        )

        assert r.status_code == 200
        saved = yaml.safe_load(
            (tenant_dir / "brand.yaml").read_text(encoding="utf-8")
        )
        assert "pages" not in saved  # Geen pages als niet meegegeven
        assert "stationery" in saved
        assert "modules" in saved
