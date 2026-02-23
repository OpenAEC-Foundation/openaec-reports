"""Tests voor de FastAPI HTTP API."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bm_reports.api import app

# Ongeauthenticeerde client voor health checks en helper tests
_unauth_client = TestClient(app)


class TestHealth:
    """Tests voor GET /api/health (open endpoint)."""

    def test_health_returns_ok(self):
        r = _unauth_client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_contains_version(self):
        r = _unauth_client.get("/api/health")
        assert "version" in r.json()


class TestTemplates:
    """Tests voor GET /api/templates."""

    def test_list_templates(self, authenticated_client):
        r = authenticated_client.get("/api/templates")
        assert r.status_code == 200
        assert "templates" in r.json()
        assert isinstance(r.json()["templates"], list)

    def test_templates_have_name(self, authenticated_client):
        r = authenticated_client.get("/api/templates")
        templates = r.json()["templates"]
        if templates:
            assert "name" in templates[0]


class TestBrands:
    """Tests voor GET /api/brands."""

    def test_list_brands(self, authenticated_client):
        r = authenticated_client.get("/api/brands")
        assert r.status_code == 200
        assert "brands" in r.json()
        assert isinstance(r.json()["brands"], list)

    def test_brands_have_name(self, authenticated_client):
        r = authenticated_client.get("/api/brands")
        brands = r.json()["brands"]
        if brands:
            assert "name" in brands[0]


class TestScaffold:
    """Tests voor GET /api/templates/{name}/scaffold."""

    def test_scaffold_structural_report(self, authenticated_client):
        r = authenticated_client.get("/api/templates/structural_report/scaffold")
        assert r.status_code == 200
        data = r.json()
        assert data["template"] == "structural_report"
        assert "sections" in data
        assert isinstance(data["sections"], list)

    def test_scaffold_has_cover(self, authenticated_client):
        r = authenticated_client.get("/api/templates/structural_report/scaffold")
        data = r.json()
        assert "cover" in data
        assert "subtitle" in data["cover"]

    def test_scaffold_has_colofon(self, authenticated_client):
        r = authenticated_client.get("/api/templates/structural_report/scaffold")
        data = r.json()
        assert data["colofon"]["enabled"] is True

    def test_scaffold_blank(self, authenticated_client):
        r = authenticated_client.get("/api/templates/blank/scaffold")
        assert r.status_code == 200
        data = r.json()
        assert data["colofon"]["enabled"] is False
        assert data["toc"]["enabled"] is False

    def test_scaffold_404(self, authenticated_client):
        r = authenticated_client.get("/api/templates/nonexistent/scaffold")
        assert r.status_code == 404


class TestValidate:
    """Tests voor POST /api/validate."""

    def test_validate_valid_data(self, authenticated_client):
        data = {"template": "structural", "project": "Test", "sections": []}
        r = authenticated_client.post("/api/validate", json=data)
        assert r.status_code == 200
        assert r.json()["valid"] is True

    def test_validate_invalid_data(self, authenticated_client):
        data = {"sections": []}  # missing required 'project' and 'template'
        r = authenticated_client.post("/api/validate", json=data)
        assert r.status_code == 200
        assert r.json()["valid"] is False
        assert len(r.json()["errors"]) > 0

    def test_validate_errors_have_path_and_message(self, authenticated_client):
        data = {}
        r = authenticated_client.post("/api/validate", json=data)
        errors = r.json()["errors"]
        assert len(errors) > 0
        for err in errors:
            assert "path" in err
            assert "message" in err


class TestGenerate:
    """Tests voor POST /api/generate."""

    def test_generate_minimal(self, authenticated_client):
        data = {
            "template": "structural",
            "project": "API Test",
            "project_number": "T-001",
            "sections": [
                {
                    "title": "Test",
                    "content": [
                        {"type": "paragraph", "text": "Hallo."},
                    ],
                }
            ],
        }
        r = authenticated_client.post("/api/generate", json=data)
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert len(r.content) > 500
        # Check PDF magic bytes
        assert r.content[:4] == b"%PDF"

    def test_generate_with_cover(self, authenticated_client):
        data = {
            "template": "structural",
            "project": "Cover API Test",
            "project_number": "T-002",
            "cover": {"subtitle": "Test ondertitel"},
            "colofon": {"enabled": True},
            "sections": [
                {"title": "Inhoud", "content": []},
            ],
            "backcover": {"enabled": True},
        }
        r = authenticated_client.post("/api/generate", json=data)
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert len(r.content) > 500

    def test_generate_content_disposition(self, authenticated_client):
        data = {
            "template": "structural",
            "project": "Mijn Project",
            "project_number": "2026-001",
            "sections": [
                {
                    "title": "Test",
                    "content": [{"type": "paragraph", "text": "Test."}],
                }
            ],
        }
        r = authenticated_client.post("/api/generate", json=data)
        assert r.status_code == 200
        cd = r.headers.get("content-disposition", "")
        assert ".pdf" in cd

    def test_generate_missing_project_returns_422(self, authenticated_client):
        data = {"template": "structural", "sections": []}
        r = authenticated_client.post("/api/generate", json=data)
        assert r.status_code == 422

    def test_generate_missing_template_returns_422(self, authenticated_client):
        data = {"project": "Test", "sections": []}
        r = authenticated_client.post("/api/generate", json=data)
        assert r.status_code == 422

    def test_generate_empty_body_returns_error(self, authenticated_client):
        r = authenticated_client.post("/api/generate", json={})
        assert r.status_code in (422, 500)


class TestGenerateErrorHandling:
    """Tests voor temp file cleanup bij fouten."""

    def test_generate_invalid_brand_cleans_temp(self, authenticated_client):
        """Bij ongeldige brand mag er geen temp file achterblijven."""
        import tempfile

        before = set(Path(tempfile.gettempdir()).glob("*.pdf"))

        data = {
            "template": "structural",
            "project": "Test",
            "brand": "nonexistent_brand_xyz",
            "sections": [],
        }
        r = authenticated_client.post("/api/generate", json=data)
        assert r.status_code in (404, 500)

        after = set(Path(tempfile.gettempdir()).glob("*.pdf"))
        leaked = after - before
        # Geen nieuwe temp files achtergebleven
        assert len(leaked) == 0


class TestValidateSchemaPath:
    """Tests voor robuuste schema resolving."""

    def test_validate_endpoint_available(self, authenticated_client):
        """Validate endpoint moet bereikbaar zijn (200 of 500, niet 404)."""
        data = {"template": "test", "project": "Test"}
        r = authenticated_client.post("/api/validate", json=data)
        assert r.status_code in (200, 500)


class TestSafeFilename:
    """Tests voor _safe_filename helper."""

    def test_basic_filename(self):
        from bm_reports.api import _safe_filename

        result = _safe_filename("2026-001", "Mijn Project")
        assert result.endswith(".pdf")
        assert " " not in result

    def test_empty_parts(self):
        from bm_reports.api import _safe_filename

        result = _safe_filename("", "")
        assert result == "rapport.pdf"

    def test_special_chars_removed(self):
        from bm_reports.api import _safe_filename

        result = _safe_filename("Test/Project<>|")
        assert "/" not in result
        assert "<" not in result
        assert ">" not in result

    def test_custom_extension(self):
        from bm_reports.api import _safe_filename

        result = _safe_filename("Test", extension=".xlsx")
        assert result.endswith(".xlsx")
