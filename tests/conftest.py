"""Gedeelde test fixtures voor de hele test suite."""

from __future__ import annotations

import os
import uuid

# Secure cookie uitzetten voor tests (TestClient gebruikt HTTP, niet HTTPS)
os.environ.setdefault("OPENAEC_COOKIE_SECURE", "false")
# Lokale login inschakelen voor tests (productie is SSO-only)
os.environ.setdefault("OPENAEC_LOCAL_AUTH_ENABLED", "true")

import pytest
from fastapi.testclient import TestClient

from openaec_reports.api import app
from openaec_reports.auth.dependencies import get_user_db
from openaec_reports.auth.models import User, UserRole
from openaec_reports.auth.security import hash_password

# Test user credentials
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpassword123"
TEST_ADMIN_USERNAME = "testadmin"
TEST_ADMIN_PASSWORD = "adminpassword123"


@pytest.fixture()
def _ensure_test_users():
    """Zorg dat test users bestaan in de database."""
    db = get_user_db()

    if not db.get_by_username(TEST_USERNAME):
        db.create(
            User(
                id=uuid.uuid4().hex,
                username=TEST_USERNAME,
                email="test@test.nl",
                display_name="Test User",
                role=UserRole.user,
                hashed_password=hash_password(TEST_PASSWORD),
            )
        )

    if not db.get_by_username(TEST_ADMIN_USERNAME):
        db.create(
            User(
                id=uuid.uuid4().hex,
                username=TEST_ADMIN_USERNAME,
                email="admin@test.nl",
                display_name="Test Admin",
                role=UserRole.admin,
                hashed_password=hash_password(TEST_ADMIN_PASSWORD),
            )
        )


@pytest.fixture()
def authenticated_client(_ensure_test_users) -> TestClient:
    """TestClient die automatisch ingelogd is als test user.

    Returns:
        TestClient met auth cookie.
    """
    client = TestClient(app)
    response = client.post(
        "/api/auth/login",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return client


@pytest.fixture()
def admin_client(_ensure_test_users) -> TestClient:
    """TestClient die ingelogd is als admin user.

    Returns:
        TestClient met admin auth cookie.
    """
    client = TestClient(app)
    response = client.post(
        "/api/auth/login",
        json={"username": TEST_ADMIN_USERNAME, "password": TEST_ADMIN_PASSWORD},
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return client
