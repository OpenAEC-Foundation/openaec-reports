"""Tests voor het authenticatie systeem."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from tests.conftest import TEST_PASSWORD, TEST_USERNAME

from bm_reports.api import app


@pytest.fixture()
def client():
    """Ongeauthenticeerde TestClient."""
    return TestClient(app)


class TestLogin:
    """Tests voor POST /api/auth/login."""

    def test_login_success(self, client, _ensure_test_users):
        """Correcte credentials → 200 + cookie + user data."""
        r = client.post(
            "/api/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
        )
        assert r.status_code == 200
        data = r.json()
        assert "user" in data
        assert data["user"]["username"] == TEST_USERNAME
        assert "hashed_password" not in data["user"]

        # Cookie moet gezet zijn
        assert "bm_access_token" in r.cookies

    def test_login_wrong_password(self, client, _ensure_test_users):
        """Fout wachtwoord → 401."""
        r = client.post(
            "/api/auth/login",
            json={"username": TEST_USERNAME, "password": "fout_wachtwoord"},
        )
        assert r.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Onbekende user → 401."""
        r = client.post(
            "/api/auth/login",
            json={"username": "bestaat_niet", "password": "whatever"},
        )
        assert r.status_code == 401

    def test_login_missing_fields(self, client):
        """Lege body → 422."""
        r = client.post("/api/auth/login", json={})
        assert r.status_code == 422


class TestLogout:
    """Tests voor POST /api/auth/logout."""

    def test_logout_clears_cookie(self, authenticated_client):
        """Logout verwijdert de cookie."""
        r = authenticated_client.post("/api/auth/logout")
        assert r.status_code == 200

        # Na logout: /me moet 401 geven
        r2 = authenticated_client.get("/api/auth/me")
        assert r2.status_code == 401


class TestMe:
    """Tests voor GET /api/auth/me."""

    def test_me_authenticated(self, authenticated_client):
        """Ingelogde user → user data."""
        r = authenticated_client.get("/api/auth/me")
        assert r.status_code == 200
        assert r.json()["user"]["username"] == TEST_USERNAME

    def test_me_unauthenticated(self, client):
        """Zonder cookie → 401."""
        r = client.get("/api/auth/me")
        assert r.status_code == 401


class TestProtectedEndpoints:
    """Tests dat business endpoints authenticatie vereisen."""

    def test_health_open(self, client):
        """/api/health is ALTIJD open."""
        r = client.get("/api/health")
        assert r.status_code == 200

    def test_templates_requires_auth(self, client):
        """GET /api/templates zonder auth → 401."""
        r = client.get("/api/templates")
        assert r.status_code == 401

    def test_templates_with_auth(self, authenticated_client):
        """GET /api/templates met auth → 200."""
        r = authenticated_client.get("/api/templates")
        assert r.status_code == 200
        assert "templates" in r.json()

    def test_brands_requires_auth(self, client):
        """GET /api/brands zonder auth → 401."""
        r = client.get("/api/brands")
        assert r.status_code == 401

    def test_brands_with_auth(self, authenticated_client):
        """GET /api/brands met auth → 200."""
        r = authenticated_client.get("/api/brands")
        assert r.status_code == 200

    def test_validate_requires_auth(self, client):
        """POST /api/validate zonder auth → 401."""
        r = client.post("/api/validate", json={"template": "test", "project": "Test"})
        assert r.status_code == 401

    def test_generate_requires_auth(self, client):
        """POST /api/generate zonder auth → 401."""
        r = client.post(
            "/api/generate",
            json={"template": "structural", "project": "Test", "sections": []},
        )
        assert r.status_code == 401

    def test_stationery_requires_auth(self, client):
        """GET /api/stationery zonder auth → 401."""
        r = client.get("/api/stationery")
        assert r.status_code == 401
