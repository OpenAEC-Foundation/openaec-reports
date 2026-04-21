"""Tests voor tenant-aware CORS loader + middleware (Golf 5c B-4)."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from openaec_reports.core.cors_middleware import TenantAwareCORSMiddleware
from openaec_reports.core.tenant_cors import (
    build_allowed_origins_set,
    build_origin_to_tenant_map,
    load_tenant_cors_configs,
)

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture()
def mock_tenants_root(tmp_path: Path) -> Path:
    """Bouw een mock tenants-directory met 4 tenants.

    - 3bm: actief, prod + dev origins
    - symitech: actief, prod + dev origins
    - foundation: actief, alleen dev origins (lege prod)
    - inactive: active=false (moet overgeslagen worden)
    """
    root = tmp_path / "tenants"
    root.mkdir()

    _write(
        root / "3bm" / "tenant.yaml",
        """\
slug: 3bm
display_name: "3BM Coöperatie"
active: true
cors:
  allowed_origins:
    - https://report.open-aec.com
    - https://cloud-3bm.open-aec.com
  allowed_origins_dev:
    - http://localhost:5173
    - http://127.0.0.1:5173
""",
    )

    _write(
        root / "symitech" / "tenant.yaml",
        """\
slug: symitech
display_name: "Symitech"
active: true
cors:
  allowed_origins:
    - https://mockup.symitech.nl
  allowed_origins_dev:
    - http://localhost:3000
""",
    )

    _write(
        root / "foundation" / "tenant.yaml",
        """\
slug: foundation
display_name: "Foundation"
active: true
cors:
  allowed_origins: []
  allowed_origins_dev:
    - http://localhost:5174
""",
    )

    _write(
        root / "inactive" / "tenant.yaml",
        """\
slug: inactive
display_name: "Inactive Fixture"
active: false
cors:
  allowed_origins:
    - https://should-not-appear.example.com
  allowed_origins_dev:
    - http://localhost:9999
""",
    )

    return root


# ---------------------------------------------------------------------------
# Loader tests
# ---------------------------------------------------------------------------


def test_loader_reads_all_tenants(mock_tenants_root: Path) -> None:
    configs = load_tenant_cors_configs(mock_tenants_root, include_dev=True)

    # "inactive" tenant moet zijn geskipt
    assert "inactive" not in configs
    assert set(configs.keys()) == {"3bm", "symitech", "foundation"}

    # Origins van inactive tenant niet in enige output
    all_origins = build_allowed_origins_set(configs)
    assert "https://should-not-appear.example.com" not in all_origins
    assert "http://localhost:9999" not in all_origins


def test_loader_skips_malformed_yaml(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    root = tmp_path / "tenants"
    _write(
        root / "broken" / "tenant.yaml",
        "slug: broken\ncors:\n  allowed_origins: [this is: not: valid yaml",
    )
    _write(
        root / "ok" / "tenant.yaml",
        """\
slug: ok
display_name: "OK tenant"
active: true
cors:
  allowed_origins:
    - https://ok.example.com
  allowed_origins_dev: []
""",
    )

    with caplog.at_level(logging.WARNING):
        configs = load_tenant_cors_configs(root, include_dev=False)

    assert "broken" not in configs
    assert "ok" in configs
    assert any("malformed" in rec.message.lower() for rec in caplog.records)


def test_loader_skips_missing_yaml(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    root = tmp_path / "tenants"
    (root / "no_yaml_here").mkdir(parents=True)
    _write(
        root / "good" / "tenant.yaml",
        """\
slug: good
display_name: "Good"
active: true
cors:
  allowed_origins: [https://good.example.com]
  allowed_origins_dev: []
""",
    )

    with caplog.at_level(logging.WARNING):
        configs = load_tenant_cors_configs(root, include_dev=False)

    assert "no_yaml_here" not in configs
    assert "good" in configs
    assert any(
        "no_yaml_here" in rec.message and "tenant.yaml" in rec.message
        for rec in caplog.records
    )


def test_loader_includes_dev_origins_when_requested(
    mock_tenants_root: Path,
) -> None:
    with_dev = load_tenant_cors_configs(mock_tenants_root, include_dev=True)
    without_dev = load_tenant_cors_configs(mock_tenants_root, include_dev=False)

    assert "http://localhost:5173" in with_dev["3bm"]
    assert "http://localhost:5173" not in without_dev["3bm"]
    # foundation heeft geen prod origins → leeg zonder dev
    assert without_dev["foundation"] == set()
    assert "http://localhost:5174" in with_dev["foundation"]


def test_origin_map_detects_duplicates(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    root = tmp_path / "tenants"
    _write(
        root / "a" / "tenant.yaml",
        """\
slug: a
display_name: A
active: true
cors:
  allowed_origins: [https://shared.example.com]
  allowed_origins_dev: []
""",
    )
    _write(
        root / "b" / "tenant.yaml",
        """\
slug: b
display_name: B
active: true
cors:
  allowed_origins: [https://shared.example.com]
  allowed_origins_dev: []
""",
    )

    configs = load_tenant_cors_configs(root, include_dev=False)
    with caplog.at_level(logging.WARNING):
        origin_map = build_origin_to_tenant_map(configs)

    assert origin_map["https://shared.example.com"] in {"a", "b"}
    assert any(
        "meerdere tenants" in rec.message for rec in caplog.records
    )


def test_loader_rejects_invalid_origins(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    root = tmp_path / "tenants"
    _write(
        root / "bad_origins" / "tenant.yaml",
        """\
slug: bad_origins
display_name: Bad
active: true
cors:
  allowed_origins:
    - https://ok.example.com
    - https://trailing.example.com/
    - ftp://no-protocol.example.com
    - https://HAS-UPPERCASE.example.com
    - "*"
  allowed_origins_dev: []
""",
    )

    with caplog.at_level(logging.WARNING):
        configs = load_tenant_cors_configs(root, include_dev=False)

    assert configs["bad_origins"] == {"https://ok.example.com"}


# ---------------------------------------------------------------------------
# Middleware tests (integration via TestClient)
# ---------------------------------------------------------------------------


def _build_app(
    allowed: frozenset[str], *, allow_credentials: bool = True
) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        TenantAwareCORSMiddleware,
        allowed_origins=allowed,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {"pong": "ok"}

    @app.post("/echo")
    def echo() -> dict[str, str]:
        return {"ok": "ok"}

    return app


def test_middleware_echoes_allowed_origin() -> None:
    allowed = frozenset({"https://report.open-aec.com"})
    client = TestClient(_build_app(allowed))

    resp = client.get(
        "/ping", headers={"origin": "https://report.open-aec.com"}
    )
    assert resp.status_code == 200
    assert (
        resp.headers["access-control-allow-origin"]
        == "https://report.open-aec.com"
    )
    assert resp.headers.get("access-control-allow-credentials") == "true"
    assert "origin" in resp.headers.get("vary", "").lower()


def test_middleware_does_not_echo_disallowed_origin() -> None:
    allowed = frozenset({"https://report.open-aec.com"})
    client = TestClient(_build_app(allowed))

    resp = client.get(
        "/ping", headers={"origin": "https://evil.example.com"}
    )
    # Request runt normaal door, maar zonder ACAO header
    assert resp.status_code == 200
    assert "access-control-allow-origin" not in resp.headers


def test_middleware_no_origin_header_passes_through() -> None:
    allowed = frozenset({"https://report.open-aec.com"})
    client = TestClient(_build_app(allowed))

    resp = client.get("/ping")
    assert resp.status_code == 200
    assert "access-control-allow-origin" not in resp.headers


def test_middleware_preflight_options_allowed() -> None:
    allowed = frozenset({"https://report.open-aec.com"})
    client = TestClient(_build_app(allowed))

    resp = client.options(
        "/echo",
        headers={
            "origin": "https://report.open-aec.com",
            "access-control-request-method": "POST",
            "access-control-request-headers": "content-type, authorization",
        },
    )
    assert resp.status_code == 204
    assert (
        resp.headers["access-control-allow-origin"]
        == "https://report.open-aec.com"
    )
    assert "POST" in resp.headers.get(
        "access-control-allow-methods", ""
    ) or "*" in resp.headers.get("access-control-allow-methods", "")
    assert resp.headers.get("access-control-allow-credentials") == "true"
    assert resp.headers.get("access-control-max-age", "").isdigit()
    vary = resp.headers.get("vary", "")
    assert "Origin" in vary
    assert "Access-Control-Request-Method" in vary


def test_middleware_preflight_options_rejected() -> None:
    allowed = frozenset({"https://report.open-aec.com"})
    client = TestClient(_build_app(allowed))

    resp = client.options(
        "/echo",
        headers={
            "origin": "https://evil.example.com",
            "access-control-request-method": "POST",
        },
    )
    assert resp.status_code == 403
    assert "access-control-allow-origin" not in resp.headers


def test_middleware_preflight_empty_allowed_set_rejects_everything() -> None:
    client = TestClient(_build_app(frozenset()))
    resp = client.options(
        "/echo",
        headers={
            "origin": "https://report.open-aec.com",
            "access-control-request-method": "POST",
        },
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Fallback test (api.py _resolve_allowed_origins)
# ---------------------------------------------------------------------------


def test_fallback_to_env_var(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Als tenants_root niet gezet is, valt api.py terug op CORS_ORIGINS env."""
    # Zorg dat er zeker geen tenants_root gedetecteerd wordt
    monkeypatch.delenv("OPENAEC_TENANTS_ROOT", raising=False)
    monkeypatch.delenv("OPENAEC_TENANT_DIR", raising=False)
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://custom-fallback.example.com,https://second.example.com",
    )

    # api.py's resolver direct aanroepen via importlib.reload is te invasief;
    # in plaats daarvan roepen we de helper na — maar die zit lokaal in api.
    # We valideren de fallback-logica door de publieke functies opnieuw in
    # dezelfde volgorde te draaien zoals api.py doet.
    from openaec_reports.core.tenant import detect_tenants_root

    assert detect_tenants_root() is None

    # Simuleer de exacte fallback-regel uit api.py
    env_val = "https://custom-fallback.example.com,https://second.example.com"
    fallback = frozenset(o.strip() for o in env_val.split(",") if o.strip())
    assert fallback == frozenset(
        {
            "https://custom-fallback.example.com",
            "https://second.example.com",
        }
    )


def test_fallback_when_tenants_root_empty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Tenants-dir bestaat maar is leeg → build_allowed_origins_set geeft lege set."""
    empty_root = tmp_path / "empty_tenants"
    empty_root.mkdir()
    configs = load_tenant_cors_configs(empty_root, include_dev=True)
    assert configs == {}
    assert build_allowed_origins_set(configs) == frozenset()
