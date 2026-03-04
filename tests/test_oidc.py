"""Tests voor OIDC integratie en user model uitbreidingen."""

from __future__ import annotations

import json
import time
import uuid
from unittest.mock import MagicMock, patch

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from openaec_reports.auth.models import User, UserDB, UserRole
from openaec_reports.auth.oidc import OidcClaims, clear_jwks_cache, validate_oidc_token
from openaec_reports.auth.security import hash_password


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture()
def tmp_db(tmp_path):
    """Verse UserDB in tijdelijke directory."""
    db_path = tmp_path / "test_auth.db"
    return UserDB(db_path=db_path)


@pytest.fixture()
def rsa_keypair():
    """Genereer RSA keypair voor OIDC token signing."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()

    # JWK representatie van de public key
    public_numbers = public_key.public_numbers()

    def _int_to_base64url(n: int, length: int = 0) -> str:
        byte_length = length or (n.bit_length() + 7) // 8
        n_bytes = n.to_bytes(byte_length, byteorder="big")
        import base64
        return base64.urlsafe_b64encode(n_bytes).rstrip(b"=").decode("ascii")

    kid = "test-key-1"
    jwk = {
        "kty": "RSA",
        "kid": kid,
        "use": "sig",
        "alg": "RS256",
        "n": _int_to_base64url(public_numbers.n, 256),
        "e": _int_to_base64url(public_numbers.e),
    }

    return {
        "private_key": private_key,
        "public_key": public_key,
        "jwk": jwk,
        "kid": kid,
    }


@pytest.fixture()
def mock_jwks(rsa_keypair):
    """JWKS response met de test key."""
    return {"keys": [rsa_keypair["jwk"]]}


def _create_oidc_token(
    rsa_keypair: dict,
    issuer: str = "https://auth.test.nl/application/o/test/",
    audience: str = "test-client-id",
    subject: str = "test-subject-123",
    email: str = "test@test.nl",
    name: str = "Test User",
    extra_claims: dict | None = None,
    expired: bool = False,
) -> str:
    """Maak een gesigned OIDC token voor testing."""
    now = time.time()
    payload = {
        "iss": issuer,
        "aud": audience,
        "sub": subject,
        "email": email,
        "name": name,
        "preferred_username": email.split("@")[0],
        "iat": int(now),
        "exp": int(now - 3600) if expired else int(now + 3600),
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload,
        rsa_keypair["private_key"],
        algorithm="RS256",
        headers={"kid": rsa_keypair["kid"]},
    )


# ============================================================
# User Model Tests
# ============================================================


class TestUserModelExtension:
    """Tests voor de uitgebreide User fields."""

    def test_user_has_new_fields(self):
        """User dataclass heeft SSO/profiel velden."""
        user = User(
            username="test",
            email="test@test.nl",
            hashed_password="hash",
            phone="+31612345678",
            job_title="Constructeur",
            registration_number="IBS-12345",
            company="3BM Coöperatie",
            auth_provider="oidc",
            oidc_subject="sub-123",
        )
        assert user.phone == "+31612345678"
        assert user.job_title == "Constructeur"
        assert user.registration_number == "IBS-12345"
        assert user.company == "3BM Coöperatie"
        assert user.auth_provider == "oidc"
        assert user.oidc_subject == "sub-123"

    def test_user_defaults(self):
        """Nieuwe velden hebben lege defaults."""
        user = User(username="test", hashed_password="hash")
        assert user.phone == ""
        assert user.job_title == ""
        assert user.registration_number == ""
        assert user.company == ""
        assert user.auth_provider == "local"
        assert user.oidc_subject == ""

    def test_to_dict_includes_new_fields(self):
        """to_dict() bevat de nieuwe velden (maar niet oidc_subject/hashed_password)."""
        user = User(
            username="test",
            hashed_password="hash",
            phone="+31 6 123",
            job_title="Adviseur",
            auth_provider="oidc",
            oidc_subject="sub-123",
        )
        d = user.to_dict()
        assert d["phone"] == "+31 6 123"
        assert d["job_title"] == "Adviseur"
        assert d["auth_provider"] == "oidc"
        assert "hashed_password" not in d
        assert "oidc_subject" not in d


class TestUserDBMigration:
    """Tests voor SQLite migratie van nieuwe kolommen."""

    def test_new_columns_exist(self, tmp_db):
        """Migratie voegt alle nieuwe kolommen toe."""
        user = User(
            username="migtest",
            hashed_password=hash_password("test123"),
            phone="+31 6 000",
            job_title="Engineer",
            registration_number="REG-001",
            company="TestBV",
            auth_provider="local",
            oidc_subject="",
        )
        created = tmp_db.create(user)
        assert created.phone == "+31 6 000"

        fetched = tmp_db.get_by_id(created.id)
        assert fetched is not None
        assert fetched.phone == "+31 6 000"
        assert fetched.job_title == "Engineer"
        assert fetched.registration_number == "REG-001"
        assert fetched.company == "TestBV"
        assert fetched.auth_provider == "local"

    def test_update_new_fields(self, tmp_db):
        """Nieuwe velden kunnen geupdate worden."""
        user = User(
            username="updtest",
            hashed_password=hash_password("test123"),
        )
        tmp_db.create(user)

        updated = tmp_db.update(
            user.id,
            phone="+31 6 111",
            job_title="Senior Engineer",
            oidc_subject="new-subject",
        )
        assert updated is not None
        assert updated.phone == "+31 6 111"
        assert updated.job_title == "Senior Engineer"
        assert updated.oidc_subject == "new-subject"


class TestUserDBNewMethods:
    """Tests voor get_by_oidc_subject() en get_by_email()."""

    def test_get_by_oidc_subject(self, tmp_db):
        """Zoek user op OIDC subject ID."""
        user = User(
            username="oidcuser",
            email="oidc@test.nl",
            hashed_password=hash_password("test123"),
            oidc_subject="authentik-sub-456",
        )
        tmp_db.create(user)

        found = tmp_db.get_by_oidc_subject("authentik-sub-456")
        assert found is not None
        assert found.username == "oidcuser"

    def test_get_by_oidc_subject_not_found(self, tmp_db):
        """Onbekend subject → None."""
        assert tmp_db.get_by_oidc_subject("nonexistent") is None

    def test_get_by_oidc_subject_empty(self, tmp_db):
        """Lege subject → None (geen match op default lege string)."""
        assert tmp_db.get_by_oidc_subject("") is None

    def test_get_by_email(self, tmp_db):
        """Zoek user op e-mail (case insensitive)."""
        user = User(
            username="emailuser",
            email="Test@Example.NL",
            hashed_password=hash_password("test123"),
        )
        tmp_db.create(user)

        found = tmp_db.get_by_email("test@example.nl")
        assert found is not None
        assert found.username == "emailuser"

    def test_get_by_email_not_found(self, tmp_db):
        """Onbekend e-mail → None."""
        assert tmp_db.get_by_email("nobody@test.nl") is None

    def test_get_by_email_empty(self, tmp_db):
        """Leeg e-mail → None."""
        assert tmp_db.get_by_email("") is None


# ============================================================
# OIDC Token Validation Tests
# ============================================================


class TestOidcTokenValidation:
    """Tests voor OIDC token validatie met mock JWKS."""

    @pytest.fixture(autouse=True)
    def _setup_oidc_env(self, monkeypatch):
        """Stel OIDC environment variabelen in voor tests."""
        monkeypatch.setenv(
            "OPENAEC_OIDC_ISSUER",
            "https://auth.test.nl/application/o/test/",
        )
        monkeypatch.setenv("OPENAEC_OIDC_CLIENT_ID", "test-client-id")
        clear_jwks_cache()

    def test_validate_valid_token(self, rsa_keypair, mock_jwks):
        """Geldig OIDC token → OidcClaims."""
        token = _create_oidc_token(rsa_keypair)

        with patch("openaec_reports.auth.oidc._fetch_jwks", return_value=mock_jwks):
            claims = validate_oidc_token(token)

        assert isinstance(claims, OidcClaims)
        assert claims.subject == "test-subject-123"
        assert claims.email == "test@test.nl"
        assert claims.name == "Test User"

    def test_validate_expired_token(self, rsa_keypair, mock_jwks):
        """Verlopen token → ValueError."""
        token = _create_oidc_token(rsa_keypair, expired=True)

        with patch("openaec_reports.auth.oidc._fetch_jwks", return_value=mock_jwks):
            with pytest.raises(ValueError, match="verlopen"):
                validate_oidc_token(token)

    def test_validate_wrong_audience(self, rsa_keypair, mock_jwks):
        """Token met verkeerde audience → ValueError."""
        token = _create_oidc_token(rsa_keypair, audience="wrong-client")

        with patch("openaec_reports.auth.oidc._fetch_jwks", return_value=mock_jwks):
            with pytest.raises(ValueError, match="audience"):
                validate_oidc_token(token)

    def test_validate_wrong_issuer(self, rsa_keypair, mock_jwks):
        """Token met verkeerde issuer → ValueError."""
        token = _create_oidc_token(
            rsa_keypair, issuer="https://evil.example.com/"
        )

        with patch("openaec_reports.auth.oidc._fetch_jwks", return_value=mock_jwks):
            with pytest.raises(ValueError, match="issuer"):
                validate_oidc_token(token)

    def test_validate_custom_claims(self, rsa_keypair, mock_jwks):
        """Custom openaec_profile claims worden correct geparsed."""
        token = _create_oidc_token(
            rsa_keypair,
            extra_claims={
                "job_title": "Constructeur",
                "phone": "+31612345678",
                "registration_number": "IBS-001",
                "company": "TestBV",
                "tenant": "3bm_cooperatie",
            },
        )

        with patch("openaec_reports.auth.oidc._fetch_jwks", return_value=mock_jwks):
            claims = validate_oidc_token(token)

        assert claims.job_title == "Constructeur"
        assert claims.phone == "+31612345678"
        assert claims.registration_number == "IBS-001"
        assert claims.company == "TestBV"
        assert claims.tenant == "3bm_cooperatie"

    def test_oidc_not_configured(self, monkeypatch):
        """OIDC niet geconfigureerd → ValueError."""
        monkeypatch.setenv("OPENAEC_OIDC_ISSUER", "")
        monkeypatch.setenv("OPENAEC_OIDC_CLIENT_ID", "")

        with pytest.raises(ValueError, match="niet geconfigureerd"):
            validate_oidc_token("some.token.here")


# ============================================================
# OIDC is_oidc_enabled Tests
# ============================================================


class TestOidcEnabled:
    """Tests voor is_oidc_enabled()."""

    def test_enabled_with_both_vars(self, monkeypatch):
        """Beide env vars gezet → enabled."""
        from openaec_reports.auth.oidc import is_oidc_enabled

        monkeypatch.setenv("OPENAEC_OIDC_ISSUER", "https://auth.test.nl/")
        monkeypatch.setenv("OPENAEC_OIDC_CLIENT_ID", "test-id")
        assert is_oidc_enabled() is True

    def test_disabled_without_issuer(self, monkeypatch):
        """Geen issuer → disabled."""
        from openaec_reports.auth.oidc import is_oidc_enabled

        monkeypatch.setenv("OPENAEC_OIDC_ISSUER", "")
        monkeypatch.setenv("OPENAEC_OIDC_CLIENT_ID", "test-id")
        assert is_oidc_enabled() is False

    def test_disabled_without_client_id(self, monkeypatch):
        """Geen client_id → disabled."""
        from openaec_reports.auth.oidc import is_oidc_enabled

        monkeypatch.setenv("OPENAEC_OIDC_ISSUER", "https://auth.test.nl/")
        monkeypatch.setenv("OPENAEC_OIDC_CLIENT_ID", "")
        assert is_oidc_enabled() is False


# ============================================================
# API Endpoint Tests
# ============================================================


class TestOidcConfigEndpoint:
    """Tests voor GET /api/auth/oidc/config."""

    def test_config_when_disabled(self, monkeypatch):
        """OIDC disabled → {enabled: false}."""
        monkeypatch.setenv("OPENAEC_OIDC_ISSUER", "")
        monkeypatch.setenv("OPENAEC_OIDC_CLIENT_ID", "")
        client = TestClient(app)
        r = client.get("/api/auth/oidc/config")
        assert r.status_code == 200
        assert r.json()["enabled"] is False

    def test_config_when_enabled(self, monkeypatch):
        """OIDC enabled → config met issuer en client_id."""
        monkeypatch.setenv(
            "OPENAEC_OIDC_ISSUER",
            "https://auth.test.nl/application/o/test/",
        )
        monkeypatch.setenv("OPENAEC_OIDC_CLIENT_ID", "my-client-id")
        client = TestClient(app)
        r = client.get("/api/auth/oidc/config")
        data = r.json()
        assert data["enabled"] is True
        assert "auth.test.nl" in data["issuer"]
        assert data["client_id"] == "my-client-id"


class TestOidcTokenExchangeEndpoint:
    """Tests voor POST /api/auth/oidc/token-exchange."""

    def test_exchange_when_disabled(self, monkeypatch):
        """OIDC disabled → 400."""
        monkeypatch.setenv("OPENAEC_OIDC_ISSUER", "")
        monkeypatch.setenv("OPENAEC_OIDC_CLIENT_ID", "")
        client = TestClient(app)
        r = client.post(
            "/api/auth/oidc/token-exchange",
            json={"id_token": "some.token"},
        )
        assert r.status_code == 400

    def test_exchange_missing_token(self, monkeypatch):
        """Geen token → 422."""
        monkeypatch.setenv(
            "OPENAEC_OIDC_ISSUER",
            "https://auth.test.nl/application/o/test/",
        )
        monkeypatch.setenv("OPENAEC_OIDC_CLIENT_ID", "test-id")
        client = TestClient(app)
        r = client.post(
            "/api/auth/oidc/token-exchange",
            json={},
        )
        assert r.status_code == 422


# ============================================================
# Colofon Auto-fill Tests
# ============================================================


class TestColofonAutoFill:
    """Tests voor user profiel defaults in API generate endpoints."""

    def test_inject_user_profile_defaults(self):
        """_inject_user_profile_defaults vult lege colofon velden in."""
        from openaec_reports.api import _inject_user_profile_defaults

        user = User(
            username="test",
            email="test@3bm.nl",
            display_name="Ir. J. Test",
            hashed_password="hash",
            phone="+31 6 123",
            job_title="Constructeur",
            registration_number="IBS-001",
            company="3BM Coöperatie",
        )

        data: dict = {"colofon": {}}
        _inject_user_profile_defaults(data, user)

        assert data["colofon"]["adviseur_naam"] == "Ir. J. Test"
        assert data["colofon"]["adviseur_email"] == "test@3bm.nl"
        assert data["colofon"]["adviseur_telefoon"] == "+31 6 123"
        assert data["colofon"]["adviseur_functie"] == "Constructeur"
        assert data["colofon"]["adviseur_registratie"] == "IBS-001"
        assert data["colofon"]["adviseur_bedrijf"] == "3BM Coöperatie"

    def test_inject_does_not_overwrite_existing(self):
        """Bestaande colofon waarden worden niet overschreven."""
        from openaec_reports.api import _inject_user_profile_defaults

        user = User(
            username="test",
            email="test@3bm.nl",
            display_name="Ir. J. Test",
            hashed_password="hash",
            phone="+31 6 123",
        )

        data: dict = {"colofon": {"adviseur_naam": "Bestaande Naam"}}
        _inject_user_profile_defaults(data, user)

        # Bestaande waarde behouden
        assert data["colofon"]["adviseur_naam"] == "Bestaande Naam"
        # Nieuwe waarden wel ingevuld
        assert data["colofon"]["adviseur_email"] == "test@3bm.nl"

    def test_inject_creates_colofon_if_missing(self):
        """Als colofon niet bestaat, wordt het aangemaakt."""
        from openaec_reports.api import _inject_user_profile_defaults

        user = User(
            username="test",
            display_name="Test",
            hashed_password="hash",
        )

        data: dict = {}
        _inject_user_profile_defaults(data, user)

        assert "colofon" in data
        assert data["colofon"]["adviseur_naam"] == "Test"

    def test_inject_skips_empty_user_fields(self):
        """Lege user velden worden niet in colofon gezet."""
        from openaec_reports.api import _inject_user_profile_defaults

        user = User(
            username="test",
            hashed_password="hash",
            # Alle nieuwe velden zijn leeg (default)
        )

        data: dict = {"colofon": {}}
        _inject_user_profile_defaults(data, user)

        # Geen adviseur velden toegevoegd
        assert "adviseur_naam" not in data["colofon"]
        assert "adviseur_email" not in data["colofon"]


# Importeer app voor TestClient (moet na alle patches)
from openaec_reports.api import app
