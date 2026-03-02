"""Tests voor API v2 endpoints — ReportGeneratorV2 via FastAPI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

fitz = pytest.importorskip("fitz", reason="pymupdf niet geinstalleerd")
httpx = pytest.importorskip("httpx", reason="httpx niet geinstalleerd")

from fastapi.testclient import TestClient  # noqa: E402

from openaec_reports.api import app  # noqa: E402

BASE = Path(__file__).parent.parent
JSON_PATH = BASE / "tests" / "test_data" / "sample_report.json"
STATIONERY_DIR = BASE / "src" / "openaec_reports" / "assets" / "stationery" / "default"

SKIP_NO_STATIONERY = pytest.mark.skipif(
    not STATIONERY_DIR.exists() or not (STATIONERY_DIR / "standaard.pdf").exists(),
    reason="Stationery bestanden niet aanwezig",
)


@pytest.fixture()
def client():
    """Ongeauthenticeerde client (alleen voor health check)."""
    return TestClient(app)


@pytest.fixture()
def sample_data():
    if JSON_PATH.exists():
        return json.loads(JSON_PATH.read_text(encoding="utf-8"))
    return None


# ============================================================
# Health + discovery endpoints
# ============================================================


class TestHealthEndpoint:
    def test_health(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestStationeryEndpoint:
    def test_stationery_returns_brands(self, authenticated_client):
        r = authenticated_client.get("/api/stationery")
        assert r.status_code == 200
        data = r.json()
        assert "brands" in data

    @SKIP_NO_STATIONERY
    def test_default_complete(self, authenticated_client):
        r = authenticated_client.get("/api/stationery")
        data = r.json()
        brands = data["brands"]
        assert "default" in brands
        assert brands["default"]["complete"] is True


# ============================================================
# Generate V2 endpoint
# ============================================================


@SKIP_NO_STATIONERY
class TestGenerateV2:
    def test_generate_v2_returns_pdf(self, authenticated_client, sample_data):
        if not sample_data:
            pytest.skip("sample_report.json niet aanwezig")

        r = authenticated_client.post("/api/generate/v2", json=sample_data)
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert len(r.content) > 5000

    def test_generate_v2_missing_project(self, authenticated_client):
        r = authenticated_client.post(
            "/api/generate/v2", json={"template": "default"}
        )
        assert r.status_code == 422

    def test_generate_v2_minimal(self, authenticated_client):
        """Minimaal rapport: alleen project naam."""
        data = {
            "template": "default",
            "project": "Test Project",
            "report_type": "Testrapport",
            "sections": [
                {
                    "number": "1",
                    "title": "Test",
                    "level": 1,
                    "content": [
                        {"type": "paragraph", "text": "Dit is een test."}
                    ],
                }
            ],
            "backcover": {"enabled": True},
        }
        r = authenticated_client.post("/api/generate/v2", json=data)
        assert r.status_code == 200
        assert len(r.content) > 1000


# ============================================================
# Upload endpoint
# ============================================================


class TestUploadEndpoint:
    def test_upload_image(self, authenticated_client, tmp_path):
        # Create a minimal PNG (1x1 pixel)
        import struct
        import zlib

        def create_png():
            signature = b'\x89PNG\r\n\x1a\n'
            ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
            ihdr_crc = struct.pack('>I', zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff)
            ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + ihdr_crc
            raw = b'\x00\xff\x00\x00'
            compressed = zlib.compress(raw)
            idat_crc = struct.pack('>I', zlib.crc32(b'IDAT' + compressed) & 0xffffffff)
            idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + idat_crc
            iend_crc = struct.pack('>I', zlib.crc32(b'IEND') & 0xffffffff)
            iend = struct.pack('>I', 0) + b'IEND' + iend_crc
            return signature + ihdr + idat + iend

        png_data = create_png()
        r = authenticated_client.post(
            "/api/upload",
            files={"file": ("test.png", png_data, "image/png")},
        )
        assert r.status_code == 200
        data = r.json()
        assert "path" in data
        assert data["filename"].endswith(".png")
        assert data["size"] > 0

        # Cleanup
        Path(data["path"]).unlink(missing_ok=True)


# ============================================================
# Old generate endpoint (backward compat)
# ============================================================


class TestOldGenerateEndpoint:
    def test_old_generate_still_exists(self, authenticated_client):
        """Het oude /api/generate endpoint is nog steeds aanwezig."""
        r = authenticated_client.post("/api/generate", json={"project": "Test"})
        # 422 want 'template' is verplicht, maar endpoint is er wel
        assert r.status_code == 422
