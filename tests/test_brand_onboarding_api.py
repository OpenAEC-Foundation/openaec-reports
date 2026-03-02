"""Tests voor Brand Onboarding API endpoints.

Gebruikt een standalone test-app met de brand_router om te testen
zonder de hoofd api.py te wijzigen. Auth dependency wordt overridden
zodat we zonder JWT kunnen testen.
"""

from __future__ import annotations

from io import BytesIO

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas

from openaec_reports.auth.dependencies import get_current_user
from openaec_reports.auth.models import User, UserRole
from openaec_reports.brand_api import BrandSession, brand_router

# Fake user voor auth bypass
_FAKE_USER = User(
    id="test-user-001",
    username="testuser",
    role=UserRole.user,
    is_active=True,
)

# Test app met brand router + auth override
_test_app = FastAPI()
_test_app.include_router(brand_router)
_test_app.dependency_overrides[get_current_user] = lambda: _FAKE_USER

# Fake session_id die NIET bestaat (12 hex chars, voldoet aan validatie)
_FAKE_SESSION_ID = "000000000000"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_test_pdf(text_elements: list[dict] | None = None) -> bytes:
    """Maak een test PDF met optionele tekst elementen.

    Args:
        text_elements: Lijst van dicts met x, y, text, en optioneel font/size.

    Returns:
        PDF content als bytes.
    """
    buf = BytesIO()
    c = pdf_canvas.Canvas(buf, pagesize=A4)
    if text_elements:
        for elem in text_elements:
            c.setFont(elem.get("font", "Helvetica"), elem.get("size", 12))
            c.drawString(elem["x"], elem["y"], elem["text"])
    c.showPage()
    c.save()
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def client() -> TestClient:
    """TestClient voor de brand onboarding API."""
    return TestClient(_test_app)


@pytest.fixture()
def reference_pdf() -> bytes:
    """Reference PDF met placeholder tekst."""
    return make_test_pdf([
        {"x": 100, "y": 700, "text": "[TITLE]", "font": "Helvetica-Bold", "size": 18},
        {"x": 100, "y": 670, "text": "[DATUM]", "font": "Helvetica", "size": 10},
        {"x": 100, "y": 640, "text": "Vast element", "font": "Helvetica", "size": 10},
    ])


@pytest.fixture()
def stationery_pdf() -> bytes:
    """Stationery PDF met alleen statische elementen."""
    return make_test_pdf([
        {"x": 100, "y": 640, "text": "Vast element", "font": "Helvetica", "size": 10},
    ])


@pytest.fixture()
def uploaded_session_id(
    client: TestClient,
    reference_pdf: bytes,
    stationery_pdf: bytes,
) -> str:
    """Upload een compleet paar en retourneer de session_id.

    Yields:
        Session ID.
    """
    response = client.post(
        "/api/brand/upload-pairs",
        files=[
            ("files", ("cover_reference.pdf", reference_pdf, "application/pdf")),
            ("files", ("cover_stationery.pdf", stationery_pdf, "application/pdf")),
        ],
        data={"brand_name": "Test Brand", "brand_slug": "test-brand"},
    )
    assert response.status_code == 200
    session_id = response.json()["session_id"]
    yield session_id
    # Cleanup
    BrandSession(session_id).cleanup()


@pytest.fixture()
def diffed_session_id(
    client: TestClient,
    uploaded_session_id: str,
) -> str:
    """Session met uitgevoerde diff.

    Yields:
        Session ID.
    """
    response = client.post(f"/api/brand/diff/{uploaded_session_id}/cover")
    assert response.status_code == 200
    return uploaded_session_id


# ===================================================================
# Upload Pairs
# ===================================================================


class TestUploadPairs:
    """Test POST /api/brand/upload-pairs."""

    def test_upload_complete_pair(
        self,
        client: TestClient,
        reference_pdf: bytes,
        stationery_pdf: bytes,
    ) -> None:
        """Upload een compleet reference+stationery paar."""
        response = client.post(
            "/api/brand/upload-pairs",
            files=[
                ("files", ("cover_reference.pdf", reference_pdf, "application/pdf")),
                ("files", ("cover_stationery.pdf", stationery_pdf, "application/pdf")),
            ],
            data={"brand_name": "Test Brand"},
        )
        assert response.status_code == 200
        data = response.json()

        assert "session_id" in data
        assert data["brand_slug"] == "test-brand"
        assert len(data["pairs"]) == 1
        assert data["pairs"][0]["page_type"] == "cover"
        assert data["pairs"][0]["complete"] is True
        assert data["warnings"] == []

        # Cleanup
        BrandSession(data["session_id"]).cleanup()

    def test_upload_incomplete_pair(
        self,
        client: TestClient,
        reference_pdf: bytes,
    ) -> None:
        """Upload alleen een reference (stationery ontbreekt)."""
        response = client.post(
            "/api/brand/upload-pairs",
            files=[
                ("files", ("cover_reference.pdf", reference_pdf, "application/pdf")),
            ],
            data={"brand_name": "Test Brand"},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["pairs"][0]["complete"] is False
        assert len(data["warnings"]) > 0
        assert "stationery ontbreekt" in data["warnings"][0]

        BrandSession(data["session_id"]).cleanup()

    def test_upload_multiple_types(
        self,
        client: TestClient,
        reference_pdf: bytes,
        stationery_pdf: bytes,
    ) -> None:
        """Upload meerdere pagina-types tegelijk."""
        response = client.post(
            "/api/brand/upload-pairs",
            files=[
                ("files", ("cover_reference.pdf", reference_pdf, "application/pdf")),
                ("files", ("cover_stationery.pdf", stationery_pdf, "application/pdf")),
                ("files", ("colofon_reference.pdf", reference_pdf, "application/pdf")),
                ("files", ("colofon_stationery.pdf", stationery_pdf, "application/pdf")),
            ],
            data={"brand_name": "Multi"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["pairs"]) == 2
        page_types = {p["page_type"] for p in data["pairs"]}
        assert page_types == {"cover", "colofon"}

        BrandSession(data["session_id"]).cleanup()


# ===================================================================
# Diff
# ===================================================================


class TestDiff:
    """Test POST /api/brand/diff/{session_id}/{page_type}."""

    def test_diff_detects_removed_text(
        self,
        client: TestClient,
        uploaded_session_id: str,
    ) -> None:
        """Diff detecteert tekst die in reference staat maar niet in stationery."""
        response = client.post(f"/api/brand/diff/{uploaded_session_id}/cover")
        assert response.status_code == 200

        data = response.json()
        assert data["page_type"] == "cover"
        assert data["orientation"] in ("portrait", "landscape")
        assert data["page_size"]["width_pt"] > 0
        assert data["page_size"]["height_pt"] > 0
        assert data["diff_image_url"].startswith("/api/brand/")

        # Moet [TITLE] en [DATUM] detecteren (niet in stationery)
        assert len(data["detected_fields"]) >= 2
        field_texts = {f["sample_text"] for f in data["detected_fields"]}
        assert "[TITLE]" in field_texts
        assert "[DATUM]" in field_texts

        # Kleuren en fonts moeten gedetecteerd zijn
        assert len(data["detected_colors"]) > 0
        assert len(data["detected_fonts"]) > 0

    def test_diff_nonexistent_session(self, client: TestClient) -> None:
        """Diff op niet-bestaande sessie geeft 404."""
        response = client.post(f"/api/brand/diff/{_FAKE_SESSION_ID}/cover")
        assert response.status_code == 404

    def test_diff_invalid_session_id(self, client: TestClient) -> None:
        """Diff met ongeldig session_id formaat geeft 400."""
        response = client.post("/api/brand/diff/not-valid-hex/cover")
        assert response.status_code == 400

    def test_diff_missing_reference(
        self,
        client: TestClient,
        stationery_pdf: bytes,
    ) -> None:
        """Diff zonder reference PDF geeft 400."""
        # Upload alleen stationery
        upload_resp = client.post(
            "/api/brand/upload-pairs",
            files=[
                ("files", ("cover_stationery.pdf", stationery_pdf, "application/pdf")),
            ],
            data={"brand_name": "Test"},
        )
        session_id = upload_resp.json()["session_id"]

        response = client.post(f"/api/brand/diff/{session_id}/cover")
        assert response.status_code == 400

        BrandSession(session_id).cleanup()


# ===================================================================
# Diff Image & Preview
# ===================================================================


class TestImages:
    """Test GET /api/brand/diff-image en /preview."""

    def test_diff_image_serves_png(
        self,
        client: TestClient,
        diffed_session_id: str,
    ) -> None:
        """Diff image endpoint serveert een PNG."""
        response = client.get(
            f"/api/brand/diff-image/{diffed_session_id}/cover",
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert len(response.content) > 100

    def test_reference_preview(
        self,
        client: TestClient,
        diffed_session_id: str,
    ) -> None:
        """Reference preview is beschikbaar."""
        response = client.get(
            f"/api/brand/preview/{diffed_session_id}/cover_reference.png",
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    def test_stationery_preview(
        self,
        client: TestClient,
        diffed_session_id: str,
    ) -> None:
        """Stationery preview is beschikbaar."""
        response = client.get(
            f"/api/brand/preview/{diffed_session_id}/cover_stationery.png",
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    def test_nonexistent_image_404(self, client: TestClient) -> None:
        """Niet-bestaande image geeft 404."""
        response = client.get(f"/api/brand/diff-image/{_FAKE_SESSION_ID}/cover")
        assert response.status_code == 404

    def test_invalid_session_id_400(self, client: TestClient) -> None:
        """Ongeldig session_id geeft 400."""
        response = client.get("/api/brand/diff-image/not_valid_hex/cover")
        assert response.status_code == 400


# ===================================================================
# Field Update
# ===================================================================


class TestFieldUpdate:
    """Test PUT /api/brand/fields/{session_id}/{page_type}."""

    def test_update_field_roles(
        self,
        client: TestClient,
        diffed_session_id: str,
    ) -> None:
        """Update veld-rollen werkt."""
        response = client.put(
            f"/api/brand/fields/{diffed_session_id}/cover",
            json={
                "fields": [
                    {"id": "field_001", "role": "title", "name": "report_title"},
                    {"id": "field_002", "role": "date", "name": "report_date"},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

        # Verifieer dat rollen zijn bijgewerkt
        fields = data["fields"]
        field_map = {f["id"]: f for f in fields}
        if "field_001" in field_map:
            assert field_map["field_001"]["role"] == "title"
        if "field_002" in field_map:
            assert field_map["field_002"]["role"] == "date"

    def test_update_nonexistent_session(self, client: TestClient) -> None:
        """Update op niet-bestaande sessie geeft 404."""
        response = client.put(
            f"/api/brand/fields/{_FAKE_SESSION_ID}/cover",
            json={"fields": [{"id": "x", "role": "title", "name": "t"}]},
        )
        assert response.status_code == 404

    def test_update_empty_fields(
        self,
        client: TestClient,
        diffed_session_id: str,
    ) -> None:
        """Lege velden lijst geeft 400."""
        response = client.put(
            f"/api/brand/fields/{diffed_session_id}/cover",
            json={"fields": []},
        )
        assert response.status_code == 400


# ===================================================================
# Generate
# ===================================================================


class TestGenerate:
    """Test POST /api/brand/generate/{session_id}."""

    def test_generate_brand_yaml(
        self,
        client: TestClient,
        diffed_session_id: str,
    ) -> None:
        """Genereer brand.yaml op basis van diff resultaten."""
        response = client.post(
            f"/api/brand/generate/{diffed_session_id}",
            json={
                "brand_name": "Test Brand",
                "brand_slug": "test-brand",
                "colors": {"primary": "#006FAB"},
                "modules": [],
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert "yaml" in data
        assert "Test Brand" in data["yaml"]
        assert data["download_url"].startswith("/api/brand/download/")
        assert "stationery_files" in data

    def test_generate_nonexistent_session(self, client: TestClient) -> None:
        """Generate op niet-bestaande sessie geeft 404."""
        response = client.post(
            f"/api/brand/generate/{_FAKE_SESSION_ID}",
            json={"brand_name": "X", "brand_slug": "x"},
        )
        assert response.status_code == 404


# ===================================================================
# Download
# ===================================================================


class TestDownload:
    """Test GET /api/brand/download/{session_id}/{filename}."""

    def test_download_zip(
        self,
        client: TestClient,
        diffed_session_id: str,
    ) -> None:
        """Download ZIP na generate."""
        # Eerst genereren
        client.post(
            f"/api/brand/generate/{diffed_session_id}",
            json={
                "brand_name": "Test",
                "brand_slug": "test",
                "colors": {},
                "modules": [],
            },
        )

        response = client.get(
            f"/api/brand/download/{diffed_session_id}/brand_package.zip",
        )
        assert response.status_code == 200
        assert "zip" in response.headers["content-type"]

    def test_download_brand_yaml(
        self,
        client: TestClient,
        diffed_session_id: str,
    ) -> None:
        """Download brand.yaml na generate."""
        client.post(
            f"/api/brand/generate/{diffed_session_id}",
            json={
                "brand_name": "Test",
                "brand_slug": "test",
                "colors": {},
                "modules": [],
            },
        )

        response = client.get(
            f"/api/brand/download/{diffed_session_id}/brand.yaml",
        )
        assert response.status_code == 200

    def test_download_nonexistent_file(
        self,
        client: TestClient,
        diffed_session_id: str,
    ) -> None:
        """Download van niet-bestaand bestand geeft 404."""
        response = client.get(
            f"/api/brand/download/{diffed_session_id}/nonexistent.txt",
        )
        assert response.status_code == 404

    def test_download_path_traversal(self, client: TestClient) -> None:
        """Path traversal in filename geeft 400."""
        # Filename met subdir (Path.name != origineel)
        response = client.get(
            f"/api/brand/download/{_FAKE_SESSION_ID}/subdir%5Csecret.txt",
        )
        assert response.status_code == 400


# ===================================================================
# Session Cleanup
# ===================================================================


class TestSessionCleanup:
    """Test DELETE /api/brand/session/{session_id}."""

    def test_delete_session(
        self,
        client: TestClient,
        reference_pdf: bytes,
        stationery_pdf: bytes,
    ) -> None:
        """Sessie verwijderen werkt."""
        # Upload om sessie te maken
        upload_resp = client.post(
            "/api/brand/upload-pairs",
            files=[
                ("files", ("cover_reference.pdf", reference_pdf, "application/pdf")),
            ],
            data={"brand_name": "Cleanup Test"},
        )
        session_id = upload_resp.json()["session_id"]

        response = client.delete(f"/api/brand/session/{session_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

        # Sessie is nu weg
        assert not BrandSession(session_id).exists()

    def test_delete_nonexistent_session(self, client: TestClient) -> None:
        """Verwijderen van niet-bestaande sessie geeft 404."""
        response = client.delete(f"/api/brand/session/{_FAKE_SESSION_ID}")
        assert response.status_code == 404


# ===================================================================
# Validatie tests
# ===================================================================


class TestValidation:
    """Test input validatie (path traversal, session_id format)."""

    def test_invalid_session_id_diff(self, client: TestClient) -> None:
        """Ongeldig session_id formaat bij diff geeft 400."""
        response = client.post("/api/brand/diff/INVALID_HEX_!/cover")
        assert response.status_code == 400

    def test_invalid_session_id_delete(self, client: TestClient) -> None:
        """Ongeldig session_id formaat bij delete geeft 400."""
        response = client.delete("/api/brand/session/not-hex-id")
        assert response.status_code == 400

    def test_invalid_filename_preview(self, client: TestClient) -> None:
        """Path traversal in preview filename geeft 400."""
        # Filename met backslash subdir (Path.name != origineel)
        response = client.get(
            f"/api/brand/preview/{_FAKE_SESSION_ID}/subdir%5Csecret.png",
        )
        assert response.status_code == 400


# ===================================================================
# BrandSession unit tests
# ===================================================================


class TestBrandSession:
    """Unit tests voor BrandSession class."""

    def test_create_and_exists(self) -> None:
        """Sessie aanmaken en checken."""
        session = BrandSession("test_unit_session")
        assert not session.exists()
        session.create()
        assert session.exists()
        session.cleanup()
        assert not session.exists()

    def test_metadata_roundtrip(self) -> None:
        """Metadata opslaan en laden."""
        session = BrandSession("test_meta_session")
        session.create()
        try:
            session.save_metadata({"brand_name": "Test", "key": "value"})
            loaded = session.load_metadata()
            assert loaded["brand_name"] == "Test"
            assert loaded["key"] == "value"
        finally:
            session.cleanup()

    def test_get_pairs_empty(self) -> None:
        """Lege sessie heeft geen paren."""
        session = BrandSession("test_empty_pairs")
        session.create()
        try:
            assert session.get_pairs() == {}
        finally:
            session.cleanup()
