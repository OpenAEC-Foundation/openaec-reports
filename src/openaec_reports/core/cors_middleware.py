"""Tenant-aware CORS middleware voor FastAPI/Starlette.

Vervangt ``starlette.middleware.cors.CORSMiddleware`` met een variant die:

- Een **runtime** toegestane-origin set gebruikt (union van alle tenant
  origins uit ``tenant.yaml``, opgebouwd bij backend-startup).
- Exact het Origin-header echo't i.p.v. een wildcard ``*`` — vereist voor
  requests met credentials.
- Onbekende origins stilzwijgend afwijst door simpelweg geen
  ``Access-Control-Allow-Origin`` header te sturen (browser blokkeert de
  XHR dan zelf).
- Preflight (OPTIONS) met onbekende origin afwijst met **403 Forbidden**
  in plaats van een 200 zonder ACAO — duidelijker signaal aan ontwikkelaars.

Implementatie-keuze: pure ASGI wrapper i.p.v. ``BaseHTTPMiddleware``.
``BaseHTTPMiddleware`` wrap de request body in een ``Request`` en gebruikt
een extra async-generator voor de response — meetbare overhead op hot-path.
De CORS-check hier doet alleen header-inspectie en header-injectie, dus de
ASGI variant is strikt beter.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)

_DEFAULT_MAX_AGE = 600


def _headers_from_scope(scope: Scope) -> Headers:
    return Headers(scope=scope)


class TenantAwareCORSMiddleware:
    """Pure ASGI middleware voor tenant-aware CORS.

    Args:
        app: Downstream ASGI app.
        allowed_origins: Frozenset van toegestane origin-strings (exact match).
        allow_credentials: Zet ``Access-Control-Allow-Credentials: true`` bij match.
        allow_methods: Iterable van HTTP methods (of ``["*"]``).
        allow_headers: Iterable van request headers (of ``["*"]``).
        max_age: ``Access-Control-Max-Age`` seconden voor preflight caching.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        allowed_origins: frozenset[str],
        allow_credentials: bool = True,
        allow_methods: Iterable[str] = ("*",),
        allow_headers: Iterable[str] = ("*",),
        max_age: int = _DEFAULT_MAX_AGE,
    ) -> None:
        self.app = app
        self.allowed_origins = allowed_origins
        self.allow_credentials = allow_credentials
        self.allow_methods = ", ".join(allow_methods)
        self.allow_headers = ", ".join(allow_headers)
        self.max_age = str(max_age)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_headers = _headers_from_scope(scope)
        origin = request_headers.get("origin")
        method = scope.get("method", "").upper()

        # Geen Origin header → geen CORS-beslissing, pass-through.
        if origin is None:
            await self.app(scope, receive, send)
            return

        origin_allowed = origin in self.allowed_origins

        # Preflight request
        if (
            method == "OPTIONS"
            and request_headers.get("access-control-request-method") is not None
        ):
            await self._handle_preflight(
                origin=origin, allowed=origin_allowed, send=send
            )
            return

        # Simple / actual request — downstream runnen, headers injecteren bij match
        if origin_allowed:
            await self._run_with_cors_headers(origin, scope, receive, send)
        else:
            # Onbekende origin → downstream loopt normaal maar krijgt geen ACAO.
            # Browser blokkeert de response in dat geval zelf voor cross-origin
            # XHR. Same-origin/curl verkeer blijft werken.
            logger.debug(
                "CORS: origin %r niet in allowed_origins (%d entries) — geen ACAO",
                origin,
                len(self.allowed_origins),
            )
            await self.app(scope, receive, send)

    async def _handle_preflight(
        self, *, origin: str, allowed: bool, send: Send
    ) -> None:
        """Behandel een OPTIONS preflight-request zelf af."""
        if not allowed:
            logger.info(
                "CORS preflight afgewezen: origin %r niet toegestaan", origin
            )
            await send(
                {
                    "type": "http.response.start",
                    "status": 403,
                    "headers": [
                        (b"content-type", b"text/plain; charset=utf-8"),
                        (b"vary", b"Origin"),
                    ],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b"CORS origin not allowed",
                }
            )
            return

        headers: list[tuple[bytes, bytes]] = [
            (b"access-control-allow-origin", origin.encode("latin-1")),
            (b"access-control-allow-methods", self.allow_methods.encode("latin-1")),
            (b"access-control-allow-headers", self.allow_headers.encode("latin-1")),
            (b"access-control-max-age", self.max_age.encode("latin-1")),
            (
                b"vary",
                b"Origin, Access-Control-Request-Method, Access-Control-Request-Headers",
            ),
            (b"content-length", b"0"),
        ]
        if self.allow_credentials:
            headers.append((b"access-control-allow-credentials", b"true"))

        await send(
            {
                "type": "http.response.start",
                "status": 204,
                "headers": headers,
            }
        )
        await send({"type": "http.response.body", "body": b""})

    async def _run_with_cors_headers(
        self, origin: str, scope: Scope, receive: Receive, send: Send
    ) -> None:
        """Draai downstream app en injecteer CORS-headers in de response."""

        async def send_with_cors(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["access-control-allow-origin"] = origin
                if self.allow_credentials:
                    headers["access-control-allow-credentials"] = "true"
                # Voeg Origin toe aan Vary (append, geen overwrite)
                existing_vary = headers.get("vary")
                vary_value = "Origin"
                if existing_vary:
                    # Vermijd duplicates
                    parts = [
                        p.strip()
                        for p in existing_vary.split(",")
                        if p.strip() and p.strip().lower() != "origin"
                    ]
                    parts.append("Origin")
                    vary_value = ", ".join(parts)
                headers["vary"] = vary_value
            await send(message)

        await self.app(scope, receive, send_with_cors)


__all__ = ["TenantAwareCORSMiddleware"]
