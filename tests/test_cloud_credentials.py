"""Tests voor CR-K6 — Nextcloud credentials lazy loading.

Verifieert dat cloud.py geen module-level credential constanten
bevat en dat credentials pas bij aanroep worden opgehaald.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest


def _get_module_level_names() -> set[str]:
    """Parse cloud.py AST en retourneer alle module-level assignment targets."""
    cloud_path = (
        Path(__file__).parent.parent
        / "src"
        / "openaec_reports"
        / "cloud.py"
    )
    tree = ast.parse(cloud_path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
    return names


class TestNoModuleLevelCredentials:
    """Verifieer dat credentials niet als module-level constanten bestaan."""

    def test_no_nextcloud_url_constant(self) -> None:
        """NEXTCLOUD_URL mag niet als module-level constante bestaan."""
        names = _get_module_level_names()
        assert "NEXTCLOUD_URL" not in names

    def test_no_nextcloud_user_constant(self) -> None:
        """NEXTCLOUD_USER mag niet als module-level constante bestaan."""
        names = _get_module_level_names()
        assert "NEXTCLOUD_USER" not in names

    def test_no_nextcloud_pass_constant(self) -> None:
        """NEXTCLOUD_PASS mag niet als module-level constante bestaan."""
        names = _get_module_level_names()
        assert "NEXTCLOUD_PASS" not in names


class TestLazyLoading:
    """Verifieer dat credentials lazy worden opgehaald."""

    def test_get_nextcloud_url_reads_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """_get_nextcloud_url() leest NEXTCLOUD_URL uit environment."""
        monkeypatch.setenv("NEXTCLOUD_URL", "https://cloud.example.com")
        from openaec_reports import cloud

        importlib.reload(cloud)
        assert cloud._get_nextcloud_url() == "https://cloud.example.com"

    def test_get_nextcloud_user_reads_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """_get_nextcloud_user() leest NEXTCLOUD_SERVICE_USER uit environment."""
        monkeypatch.setenv("NEXTCLOUD_SERVICE_USER", "svc_user")
        from openaec_reports import cloud

        importlib.reload(cloud)
        assert cloud._get_nextcloud_user() == "svc_user"

    def test_get_nextcloud_pass_reads_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """_get_nextcloud_pass() leest NEXTCLOUD_SERVICE_PASS uit environment."""
        monkeypatch.setenv("NEXTCLOUD_SERVICE_PASS", "s3cret!")
        from openaec_reports import cloud

        importlib.reload(cloud)
        assert cloud._get_nextcloud_pass() == "s3cret!"

    def test_is_cloud_configured_lazy(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """is_cloud_configured() reageert op runtime env changes."""
        monkeypatch.delenv("NEXTCLOUD_URL", raising=False)
        monkeypatch.delenv("NEXTCLOUD_SERVICE_USER", raising=False)
        monkeypatch.delenv("NEXTCLOUD_SERVICE_PASS", raising=False)
        from openaec_reports import cloud

        importlib.reload(cloud)
        assert cloud.is_cloud_configured() is False

        monkeypatch.setenv("NEXTCLOUD_URL", "https://nc.test")
        monkeypatch.setenv("NEXTCLOUD_SERVICE_USER", "user")
        monkeypatch.setenv("NEXTCLOUD_SERVICE_PASS", "pass")
        assert cloud.is_cloud_configured() is True

    def test_defaults_empty_without_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Zonder environment variables retourneren functies lege strings."""
        monkeypatch.delenv("NEXTCLOUD_URL", raising=False)
        monkeypatch.delenv("NEXTCLOUD_SERVICE_USER", raising=False)
        monkeypatch.delenv("NEXTCLOUD_SERVICE_PASS", raising=False)
        from openaec_reports import cloud

        importlib.reload(cloud)
        assert cloud._get_nextcloud_url() == ""
        assert cloud._get_nextcloud_user() == ""
        assert cloud._get_nextcloud_pass() == ""
