"""Tests voor het self-registratie systeem."""

from __future__ import annotations

import os
import uuid

import pytest
from fastapi.testclient import TestClient

from openaec_reports.api import app


@pytest.fixture()
def client():
    """Ongeauthenticeerde TestClient."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def _enable_registration():
    """Zorg dat registratie aan staat voor tests."""
    os.environ["OPENAEC_REGISTRATION_ENABLED"] = "true"
    yield
    os.environ.pop("OPENAEC_REGISTRATION_ENABLED", None)


class TestRegistration:
    """Tests voor POST /api/auth/register."""

    def _unique_user(self) -> dict:
        """Genereer unieke test user data."""
        uid = uuid.uuid4().hex[:8]
        return {
            "username": f"reg_{uid}",
            "email": f"reg_{uid}@test.nl",
            "password": "veiligwachtwoord123",
            "display_name": f"Registrant {uid}",
        }

    def test_register_success(self, client):
        """Geldige registratie → 201 + cookie + user data."""
        user_data = self._unique_user()
        r = client.post("/api/auth/register", json=user_data)
        assert r.status_code == 201
        data = r.json()
        assert "user" in data
        assert data["user"]["username"] == user_data["username"]
        assert data["user"]["email"] == user_data["email"]
        assert data["user"]["display_name"] == user_data["display_name"]
        assert data["user"]["role"] == "user"
        assert "hashed_password" not in data["user"]
        # Cookie moet gezet zijn (direct ingelogd)
        assert "bm_access_token" in r.cookies

    def test_register_auto_login(self, client):
        """Na registratie is de user direct ingelogd — /me retourneert user."""
        user_data = self._unique_user()
        r = client.post("/api/auth/register", json=user_data)
        assert r.status_code == 201

        # Check sessie
        me = client.get("/api/auth/me")
        assert me.status_code == 200
        assert me.json()["user"]["username"] == user_data["username"]

    def test_register_default_display_name(self, client):
        """Zonder display_name wordt username als fallback gebruikt."""
        user_data = self._unique_user()
        del user_data["display_name"]
        r = client.post("/api/auth/register", json=user_data)
        assert r.status_code == 201
        assert r.json()["user"]["display_name"] == user_data["username"]

    def test_register_duplicate_username(self, client):
        """Dubbele username → 409."""
        user_data = self._unique_user()
        r1 = client.post("/api/auth/register", json=user_data)
        assert r1.status_code == 201

        # Tweede keer dezelfde username, ander email
        user_data["email"] = f"ander_{uuid.uuid4().hex[:6]}@test.nl"
        r2 = client.post("/api/auth/register", json=user_data)
        assert r2.status_code == 409
        assert "gebruikersnaam" in r2.json()["detail"].lower()

    def test_register_duplicate_email(self, client):
        """Dubbel email → 409."""
        user_data = self._unique_user()
        r1 = client.post("/api/auth/register", json=user_data)
        assert r1.status_code == 201

        # Andere username, zelfde email
        user_data["username"] = f"ander_{uuid.uuid4().hex[:6]}"
        r2 = client.post("/api/auth/register", json=user_data)
        assert r2.status_code == 409
        assert "e-mail" in r2.json()["detail"].lower()

    def test_register_short_password(self, client):
        """Te kort wachtwoord → 422."""
        user_data = self._unique_user()
        user_data["password"] = "kort"
        r = client.post("/api/auth/register", json=user_data)
        assert r.status_code == 422
        assert "wachtwoord" in r.json()["detail"].lower()

    def test_register_invalid_email(self, client):
        """Ongeldig email → 422."""
        user_data = self._unique_user()
        user_data["email"] = "geenemail"
        r = client.post("/api/auth/register", json=user_data)
        assert r.status_code == 422
        assert "e-mail" in r.json()["detail"].lower()

    def test_register_short_username(self, client):
        """Te korte username → 422."""
        user_data = self._unique_user()
        user_data["username"] = "ab"
        r = client.post("/api/auth/register", json=user_data)
        assert r.status_code == 422
        assert "gebruikersnaam" in r.json()["detail"].lower()

    def test_register_disabled(self, client):
        """Registratie uitgeschakeld → 403."""
        os.environ["OPENAEC_REGISTRATION_ENABLED"] = "false"
        user_data = self._unique_user()
        r = client.post("/api/auth/register", json=user_data)
        assert r.status_code == 403
        assert "uitgeschakeld" in r.json()["detail"].lower()


class TestRegistrationEnabled:
    """Tests voor GET /api/auth/registration-enabled."""

    def test_enabled_default(self, client):
        """Default: registratie is enabled."""
        r = client.get("/api/auth/registration-enabled")
        assert r.status_code == 200
        assert r.json()["enabled"] is True

    def test_disabled(self, client):
        """OPENAEC_REGISTRATION_ENABLED=false → disabled."""
        os.environ["OPENAEC_REGISTRATION_ENABLED"] = "false"
        r = client.get("/api/auth/registration-enabled")
        assert r.status_code == 200
        assert r.json()["enabled"] is False
