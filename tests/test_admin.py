"""Tests voor de admin API endpoints."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from tests.conftest import TEST_USERNAME

from bm_reports.api import app
from bm_reports.auth.dependencies import get_user_db


@pytest.fixture()
def client():
    """Ongeauthenticeerde TestClient."""
    return TestClient(app)


# ============================================================
# Toegangscontrole
# ============================================================


class TestAdminAccess:
    """Tests dat admin endpoints correct beveiligd zijn."""

    def test_unauthenticated_returns_401(self, client):
        """Zonder cookie → 401."""
        r = client.get("/api/admin/users")
        assert r.status_code == 401

    def test_non_admin_returns_403(self, authenticated_client):
        """Gewone user → 403."""
        r = authenticated_client.get("/api/admin/users")
        assert r.status_code == 403

    def test_admin_returns_200(self, admin_client):
        """Admin user → 200."""
        r = admin_client.get("/api/admin/users")
        assert r.status_code == 200
        assert "users" in r.json()


# ============================================================
# User CRUD
# ============================================================


class TestUserList:
    """Tests voor GET /api/admin/users."""

    def test_list_users(self, admin_client):
        """Admin kan alle users opvragen."""
        r = admin_client.get("/api/admin/users")
        assert r.status_code == 200
        users = r.json()["users"]
        assert isinstance(users, list)
        assert len(users) >= 2  # testuser + testadmin

    def test_user_has_no_password(self, admin_client):
        """User data bevat geen hashed_password."""
        r = admin_client.get("/api/admin/users")
        for user in r.json()["users"]:
            assert "hashed_password" not in user


class TestUserCreate:
    """Tests voor POST /api/admin/users."""

    def test_create_user(self, admin_client):
        """Admin kan een nieuwe user aanmaken."""
        unique = uuid.uuid4().hex[:8]
        r = admin_client.post("/api/admin/users", json={
            "username": f"newuser_{unique}",
            "password": "veiligwachtwoord",
            "email": f"{unique}@test.nl",
            "display_name": "Nieuwe Gebruiker",
            "role": "user",
            "tenant": "",
        })
        assert r.status_code == 201
        user = r.json()["user"]
        assert user["username"] == f"newuser_{unique}"
        assert user["role"] == "user"

    def test_create_user_duplicate_username(self, admin_client):
        """Dubbele username → 409."""
        r = admin_client.post("/api/admin/users", json={
            "username": TEST_USERNAME,
            "password": "whatever123",
        })
        assert r.status_code == 409

    def test_create_user_invalid_role(self, admin_client):
        """Ongeldige rol → 422."""
        unique = uuid.uuid4().hex[:8]
        r = admin_client.post("/api/admin/users", json={
            "username": f"invalid_{unique}",
            "password": "veiligwachtwoord",
            "role": "superadmin",
        })
        assert r.status_code == 422

    def test_create_user_short_password(self, admin_client):
        """Kort wachtwoord → 422."""
        unique = uuid.uuid4().hex[:8]
        r = admin_client.post("/api/admin/users", json={
            "username": f"short_{unique}",
            "password": "ab",
        })
        assert r.status_code == 422


class TestUserGet:
    """Tests voor GET /api/admin/users/{id}."""

    def test_get_existing_user(self, admin_client):
        """Bestaande user ophalen."""
        # Maak een user aan
        unique = uuid.uuid4().hex[:8]
        r = admin_client.post("/api/admin/users", json={
            "username": f"getme_{unique}",
            "password": "veiligwachtwoord",
        })
        user_id = r.json()["user"]["id"]

        r2 = admin_client.get(f"/api/admin/users/{user_id}")
        assert r2.status_code == 200
        assert r2.json()["user"]["id"] == user_id

    def test_get_nonexistent_user(self, admin_client):
        """Niet-bestaande user → 404."""
        r = admin_client.get("/api/admin/users/nonexistent_id")
        assert r.status_code == 404


class TestUserUpdate:
    """Tests voor PATCH /api/admin/users/{id}."""

    def test_update_display_name(self, admin_client):
        """Display name updaten."""
        unique = uuid.uuid4().hex[:8]
        r = admin_client.post("/api/admin/users", json={
            "username": f"update_{unique}",
            "password": "veiligwachtwoord",
            "display_name": "Oud",
        })
        user_id = r.json()["user"]["id"]

        r2 = admin_client.patch(f"/api/admin/users/{user_id}", json={
            "display_name": "Nieuw",
        })
        assert r2.status_code == 200
        assert r2.json()["user"]["display_name"] == "Nieuw"

    def test_update_role(self, admin_client):
        """Rol wijzigen."""
        unique = uuid.uuid4().hex[:8]
        r = admin_client.post("/api/admin/users", json={
            "username": f"role_{unique}",
            "password": "veiligwachtwoord",
            "role": "user",
        })
        user_id = r.json()["user"]["id"]

        r2 = admin_client.patch(f"/api/admin/users/{user_id}", json={
            "role": "admin",
        })
        assert r2.status_code == 200
        assert r2.json()["user"]["role"] == "admin"

    def test_deactivate_user(self, admin_client):
        """User deactiveren."""
        unique = uuid.uuid4().hex[:8]
        r = admin_client.post("/api/admin/users", json={
            "username": f"deact_{unique}",
            "password": "veiligwachtwoord",
        })
        user_id = r.json()["user"]["id"]

        r2 = admin_client.patch(f"/api/admin/users/{user_id}", json={
            "is_active": False,
        })
        assert r2.status_code == 200
        assert r2.json()["user"]["is_active"] is False


class TestUserResetPassword:
    """Tests voor POST /api/admin/users/{id}/reset-password."""

    def test_reset_password(self, admin_client):
        """Wachtwoord resetten en daarna inloggen met het nieuwe wachtwoord."""
        unique = uuid.uuid4().hex[:8]
        username = f"reset_{unique}"
        r = admin_client.post("/api/admin/users", json={
            "username": username,
            "password": "oud_wachtwoord",
        })
        user_id = r.json()["user"]["id"]

        # Reset wachtwoord
        r2 = admin_client.post(f"/api/admin/users/{user_id}/reset-password", json={
            "new_password": "nieuw_wachtwoord",
        })
        assert r2.status_code == 200

        # Login met nieuw wachtwoord
        login_client = TestClient(app)
        r3 = login_client.post("/api/auth/login", json={
            "username": username,
            "password": "nieuw_wachtwoord",
        })
        assert r3.status_code == 200


class TestUserDelete:
    """Tests voor DELETE /api/admin/users/{id}."""

    def test_delete_user(self, admin_client):
        """User verwijderen."""
        unique = uuid.uuid4().hex[:8]
        r = admin_client.post("/api/admin/users", json={
            "username": f"delme_{unique}",
            "password": "veiligwachtwoord",
        })
        user_id = r.json()["user"]["id"]

        r2 = admin_client.delete(f"/api/admin/users/{user_id}")
        assert r2.status_code == 200

        # Moet nu 404 geven
        r3 = admin_client.get(f"/api/admin/users/{user_id}")
        assert r3.status_code == 404

    def test_cannot_delete_self(self, admin_client):
        """Admin kan zichzelf niet verwijderen."""
        # Haal eigen user ID op
        me = admin_client.get("/api/auth/me")
        my_id = me.json()["user"]["id"]

        r = admin_client.delete(f"/api/admin/users/{my_id}")
        assert r.status_code == 400
        assert "jezelf" in r.json()["detail"].lower()


# ============================================================
# Tenants
# ============================================================


class TestTenants:
    """Tests voor GET /api/admin/tenants."""

    def test_list_tenants(self, admin_client):
        """Admin kan tenants opvragen."""
        r = admin_client.get("/api/admin/tenants")
        assert r.status_code == 200
        assert "tenants" in r.json()
        assert isinstance(r.json()["tenants"], list)


# ============================================================
# Templates per tenant
# ============================================================


class TestTemplateManagement:
    """Tests voor template CRUD per tenant."""

    def test_list_templates_nonexistent_tenant(self, admin_client):
        """Templates lijst voor onbekende tenant → lege lijst."""
        r = admin_client.get("/api/admin/tenants/nonexistent/templates")
        assert r.status_code == 200
        assert r.json()["templates"] == []

    def test_path_traversal_in_tenant_rejected(self, admin_client):
        """Path traversal patronen in tenant naam → 400."""
        # '..' in de tenant naam (zonder /) bereikt de handler
        r = admin_client.get("/api/admin/tenants/..secret/templates")
        assert r.status_code == 400

    def test_special_chars_in_tenant_rejected(self, admin_client):
        """Speciale tekens in tenant naam → 400."""
        r = admin_client.get("/api/admin/tenants/tenant%3B%20rm/templates")
        assert r.status_code == 400

    def test_upload_and_delete_template(self, admin_client, tmp_path):
        """Upload + delete cycle voor een template."""
        tenant = "test_tenant_templates"
        yaml_content = b"title: Test Template\ntype: structural\n"

        # Upload
        r = admin_client.post(
            f"/api/admin/tenants/{tenant}/templates",
            files={"file": ("test_template.yaml", yaml_content, "application/x-yaml")},
        )
        assert r.status_code == 200
        assert r.json()["filename"] == "test_template.yaml"

        # Lijst moet het bevatten
        r2 = admin_client.get(f"/api/admin/tenants/{tenant}/templates")
        filenames = [t["filename"] for t in r2.json()["templates"]]
        assert "test_template.yaml" in filenames

        # Delete
        r3 = admin_client.delete(f"/api/admin/tenants/{tenant}/templates/test_template.yaml")
        assert r3.status_code == 200

    def test_upload_invalid_yaml(self, admin_client):
        """Ongeldig YAML bestand → 422."""
        r = admin_client.post(
            "/api/admin/tenants/test_tenant/templates",
            files={"file": ("bad.yaml", b"{{invalid: yaml: [}", "application/x-yaml")},
        )
        assert r.status_code == 422

    def test_upload_non_yaml_rejected(self, admin_client):
        """Niet-.yaml bestand → 400."""
        r = admin_client.post(
            "/api/admin/tenants/test_tenant/templates",
            files={"file": ("readme.txt", b"hello", "text/plain")},
        )
        assert r.status_code == 400


# ============================================================
# Brand per tenant
# ============================================================


class TestBrandManagement:
    """Tests voor brand CRUD per tenant."""

    def test_get_brand_nonexistent(self, admin_client):
        """Brand ophalen voor tenant zonder brand → exists=false."""
        r = admin_client.get("/api/admin/tenants/nonexistent_brand/brand")
        assert r.status_code == 200
        assert r.json()["exists"] is False

    def test_upload_and_read_brand(self, admin_client):
        """Upload + lees cycle voor brand.yaml."""
        tenant = "test_tenant_brand"
        yaml_content = b"name: Test Brand\nprimary_color: '#FF0000'\n"

        # Upload
        r = admin_client.post(
            f"/api/admin/tenants/{tenant}/brand",
            files={"file": ("brand.yaml", yaml_content, "application/x-yaml")},
        )
        assert r.status_code == 200

        # Lees
        r2 = admin_client.get(f"/api/admin/tenants/{tenant}/brand")
        assert r2.status_code == 200
        data = r2.json()
        assert data["exists"] is True
        assert data["parsed"]["name"] == "Test Brand"
        assert "primary_color" in data["raw"]

    def test_upload_invalid_brand_yaml(self, admin_client):
        """Ongeldig YAML als brand → 422."""
        r = admin_client.post(
            "/api/admin/tenants/test_tenant/brand",
            files={"file": ("brand.yaml", b"{{bad", "application/x-yaml")},
        )
        assert r.status_code == 422


# ============================================================
# UserDB model tests
# ============================================================


class TestUserDBExtensions:
    """Tests voor de nieuwe UserDB methodes."""

    def test_list_by_tenant(self, _ensure_test_users):
        """list_by_tenant retourneert alleen users van die tenant."""
        db = get_user_db()
        unique = uuid.uuid4().hex[:8]
        from bm_reports.auth.models import User
        from bm_reports.auth.security import hash_password

        tenant_name = f"tenant_{unique}"
        db.create(User(
            username=f"t1_{unique}",
            tenant=tenant_name,
            hashed_password=hash_password("pw123456"),
        ))
        db.create(User(
            username=f"t2_{unique}",
            tenant=tenant_name,
            hashed_password=hash_password("pw123456"),
        ))

        result = db.list_by_tenant(tenant_name)
        assert len(result) == 2
        assert all(u.tenant == tenant_name for u in result)

    def test_update_user(self, _ensure_test_users):
        """update() wijzigt specifieke velden."""
        db = get_user_db()
        unique = uuid.uuid4().hex[:8]
        from bm_reports.auth.models import User
        from bm_reports.auth.security import hash_password

        user = db.create(User(
            username=f"upd_{unique}",
            display_name="Oud",
            hashed_password=hash_password("pw123456"),
        ))

        updated = db.update(user.id, display_name="Nieuw", email="new@test.nl")
        assert updated is not None
        assert updated.display_name == "Nieuw"
        assert updated.email == "new@test.nl"

    def test_update_invalid_field_raises(self, _ensure_test_users):
        """update() met ongeldig veld → ValueError."""
        db = get_user_db()
        unique = uuid.uuid4().hex[:8]
        from bm_reports.auth.models import User
        from bm_reports.auth.security import hash_password

        user = db.create(User(
            username=f"inv_{unique}",
            hashed_password=hash_password("pw123456"),
        ))

        with pytest.raises(ValueError, match="Niet-toegestane velden"):
            db.update(user.id, username="hacked")

    def test_delete_user(self, _ensure_test_users):
        """delete() verwijdert een user."""
        db = get_user_db()
        unique = uuid.uuid4().hex[:8]
        from bm_reports.auth.models import User
        from bm_reports.auth.security import hash_password

        user = db.create(User(
            username=f"del_{unique}",
            hashed_password=hash_password("pw123456"),
        ))

        assert db.delete(user.id) is True
        assert db.get_by_id(user.id) is None

    def test_delete_nonexistent(self):
        """delete() voor niet-bestaande user → False."""
        db = get_user_db()
        assert db.delete("nonexistent_id_12345") is False


# ============================================================
# Asset beheer (stationery, logos, fonts)
# ============================================================


class TestAssetManagement:
    """Tests voor asset CRUD endpoints."""

    def test_list_assets_empty(self, admin_client):
        """Lege asset lijst voor onbekende tenant."""
        r = admin_client.get(
            "/api/admin/tenants/nonexistent/assets/stationery"
        )
        assert r.status_code == 200
        assert r.json()["assets"] == []

    def test_invalid_category_rejected(self, admin_client):
        """Ongeldige asset categorie → 400."""
        r = admin_client.get(
            "/api/admin/tenants/test_tenant/assets/secrets"
        )
        assert r.status_code == 400

    def test_upload_and_delete_stationery(self, admin_client):
        """Upload + delete cycle voor stationery PDF."""
        tenant = "test_tenant_assets"
        pdf_content = b"%PDF-1.4 fake pdf content"

        # Upload
        r = admin_client.post(
            f"/api/admin/tenants/{tenant}/assets/stationery",
            files={
                "file": (
                    "standaard.pdf",
                    pdf_content,
                    "application/pdf",
                )
            },
        )
        assert r.status_code == 200
        assert r.json()["filename"] == "standaard.pdf"

        # Lijst moet het bevatten
        r2 = admin_client.get(
            f"/api/admin/tenants/{tenant}/assets/stationery"
        )
        filenames = [a["filename"] for a in r2.json()["assets"]]
        assert "standaard.pdf" in filenames

        # Delete
        r3 = admin_client.delete(
            f"/api/admin/tenants/{tenant}/assets/stationery/standaard.pdf"
        )
        assert r3.status_code == 200

    def test_upload_logo_svg(self, admin_client):
        """Upload SVG logo."""
        tenant = "test_tenant_assets"
        svg_content = b'<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>'

        r = admin_client.post(
            f"/api/admin/tenants/{tenant}/assets/logos",
            files={"file": ("logo.svg", svg_content, "image/svg+xml")},
        )
        assert r.status_code == 200
        assert r.json()["filename"] == "logo.svg"

        # Cleanup
        admin_client.delete(
            f"/api/admin/tenants/{tenant}/assets/logos/logo.svg"
        )

    def test_upload_font(self, admin_client):
        """Upload TTF font."""
        tenant = "test_tenant_assets"
        ttf_content = b"\x00\x01\x00\x00 fake ttf"

        r = admin_client.post(
            f"/api/admin/tenants/{tenant}/assets/fonts",
            files={"file": ("Test.ttf", ttf_content, "font/ttf")},
        )
        assert r.status_code == 200
        assert r.json()["filename"] == "Test.ttf"

        # Cleanup
        admin_client.delete(
            f"/api/admin/tenants/{tenant}/assets/fonts/Test.ttf"
        )

    def test_upload_wrong_extension_rejected(self, admin_client):
        """Upload .exe naar stationery → 400."""
        r = admin_client.post(
            "/api/admin/tenants/test_tenant/assets/stationery",
            files={"file": ("hack.exe", b"bad", "application/octet-stream")},
        )
        assert r.status_code == 400

    def test_upload_wrong_extension_for_category(self, admin_client):
        """Upload .pdf naar fonts → 400."""
        r = admin_client.post(
            "/api/admin/tenants/test_tenant/assets/fonts",
            files={"file": ("font.pdf", b"data", "application/pdf")},
        )
        assert r.status_code == 400

    def test_delete_nonexistent_asset(self, admin_client):
        """Verwijder niet-bestaand asset → 404."""
        r = admin_client.delete(
            "/api/admin/tenants/test_tenant/assets/stationery/nope.pdf"
        )
        assert r.status_code == 404

    def test_path_traversal_in_asset_filename(self, admin_client):
        """Path traversal in bestandsnaam → 400."""
        r = admin_client.delete(
            "/api/admin/tenants/test_tenant/assets/stationery/..secret.pdf"
        )
        assert r.status_code == 400
