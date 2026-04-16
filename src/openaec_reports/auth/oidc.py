"""Authentik forward_auth helpers — vervangt voormalige OIDC/JWKS validatie.

Reports draait achter Caddy + Authentik proxy outpost. Caddy doet de
authenticatie en stuurt de resultaten als ``X-Authentik-*`` HTTP headers
naar de upstream container. Deze module bevat enkel de helpers die nodig
zijn om die headers te interpreteren — JWKS, PKCE en token-exchange code
is verwijderd (zie git-historie).

Trust-model: netwerk-isolatie. De backend container is alleen bereikbaar
via Caddy op het ``openaec_platform`` Docker network, dus de headers
worden vertrouwd zoals geconfigureerd.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Header-namen — single source of truth zodat dependencies + tests overeenkomen
# ---------------------------------------------------------------------------

HEADER_USERNAME = "X-Authentik-Meta-Username"
HEADER_EMAIL = "X-Authentik-Meta-Email"
HEADER_NAME = "X-Authentik-Meta-Name"
HEADER_GROUPS = "X-Authentik-Meta-Groups"
HEADER_UID = "X-Authentik-Uid"
HEADER_TENANT = "X-Authentik-Meta-Tenant"
HEADER_COMPANY = "X-Authentik-Meta-Company"
HEADER_JOB_TITLE = "X-Authentik-Meta-JobTitle"
HEADER_PHONE = "X-Authentik-Meta-Phone"
HEADER_REGISTRATION_NUMBER = "X-Authentik-Meta-RegNumber"


@dataclass
class AuthentikHeaders:
    """Geparseerde Authentik headers van Caddy forward_auth.

    Alle velden zijn strings (mogelijk leeg). De ``subject`` waarde is
    de stabiele identifier waaronder we de user in onze eigen database
    opslaan; we gebruiken bij voorkeur ``X-Authentik-Meta-Username``
    omdat dat ook in de Caddyfile ``copy_headers`` lijst zit en stabiel
    is bij Authentik gebruikersnaam-wissels.
    """

    subject: str
    username: str
    email: str
    name: str
    groups: list[str]
    tenant: str
    company: str
    job_title: str
    phone: str
    registration_number: str


def parse_authentik_headers(headers) -> AuthentikHeaders | None:
    """Parse de Authentik forward_auth headers uit een Starlette/FastAPI request.

    Args:
        headers: Het ``request.headers`` mapping object (case-insensitive).

    Returns:
        ``AuthentikHeaders`` als de verplichte ``X-Authentik-Meta-Username``
        aanwezig is, anders ``None``.
    """
    username = (headers.get(HEADER_USERNAME) or "").strip()
    if not username:
        return None

    raw_groups = (headers.get(HEADER_GROUPS) or "").strip()
    groups = [g.strip() for g in raw_groups.split("|") if g.strip()] if raw_groups else []

    # Subject: prefereer de stabiele Authentik UID, val terug op username
    subject = (headers.get(HEADER_UID) or "").strip() or username

    return AuthentikHeaders(
        subject=subject,
        username=username,
        email=(headers.get(HEADER_EMAIL) or "").strip(),
        name=(headers.get(HEADER_NAME) or "").strip(),
        groups=groups,
        tenant=(headers.get(HEADER_TENANT) or "").strip(),
        company=(headers.get(HEADER_COMPANY) or "").strip(),
        job_title=(headers.get(HEADER_JOB_TITLE) or "").strip(),
        phone=(headers.get(HEADER_PHONE) or "").strip(),
        registration_number=(headers.get(HEADER_REGISTRATION_NUMBER) or "").strip(),
    )


def is_authentik_enabled() -> bool:
    """Of de backend Authentik forward_auth verwacht.

    In productie staat ``OPENAEC_AUTH_MODE=authentik``; in lokale tests
    valt dit terug op ``local`` (cookie/JWT login blijft beschikbaar).

    Returns:
        True als forward_auth headers verwacht worden.
    """
    return os.environ.get("OPENAEC_AUTH_MODE", "authentik").lower() == "authentik"
