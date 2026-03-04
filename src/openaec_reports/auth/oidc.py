"""OIDC token validatie via JWKS (RS256).

Valideert access tokens en ID tokens die door Authentik (of een andere
OIDC-conforme IdP) zijn uitgegeven. Gebruikt PyJWT met cryptography
voor RS256 signature verification.

Configuratie via environment variables:
    OPENAEC_OIDC_ISSUER    — OIDC issuer URL (bijv. https://auth.3bm.co.nl/...)
    OPENAEC_OIDC_CLIENT_ID — OAuth2 client ID
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass

import jwt
import requests

logger = logging.getLogger(__name__)

# JWKS cache: refresh elke 3600 seconden (1 uur)
_JWKS_CACHE_TTL = 3600
_jwks_cache: dict | None = None
_jwks_cache_time: float = 0


def _get_oidc_issuer() -> str:
    """Lees OIDC issuer URL uit environment.

    Returns:
        Issuer URL (exact zoals geconfigureerd, inclusief eventuele trailing slash).
    """
    return os.environ.get("OPENAEC_OIDC_ISSUER", "")


def _get_oidc_client_id() -> str:
    """Lees OIDC client ID uit environment.

    Returns:
        Client ID string.
    """
    return os.environ.get("OPENAEC_OIDC_CLIENT_ID", "")


def is_oidc_enabled() -> bool:
    """Check of OIDC configuratie aanwezig is.

    Returns:
        True als zowel issuer als client_id geconfigureerd zijn.
    """
    return bool(_get_oidc_issuer() and _get_oidc_client_id())


@dataclass
class OidcClaims:
    """Gevalideerde OIDC token claims."""

    subject: str  # Persistent user identifier
    email: str
    name: str
    preferred_username: str
    # Custom openaec_profile scope claims
    job_title: str
    phone: str
    registration_number: str
    company: str
    tenant: str
    raw: dict  # Volledige payload


def _get_jwks_uri() -> str:
    """Bouw de JWKS URI vanuit de issuer.

    Returns:
        JWKS endpoint URL.
    """
    issuer = _get_oidc_issuer().rstrip("/")
    return f"{issuer}/.well-known/jwks.json"


def _get_discovery_url() -> str:
    """Bouw de OIDC discovery URL.

    Returns:
        OpenID Connect discovery endpoint URL.
    """
    issuer = _get_oidc_issuer().rstrip("/")
    return f"{issuer}/.well-known/openid-configuration"


def _fetch_jwks() -> dict:
    """Haal JWKS op van de IdP (met caching).

    Returns:
        JWKS dict met signing keys.

    Raises:
        RuntimeError: Als JWKS niet opgehaald kan worden.
    """
    global _jwks_cache, _jwks_cache_time  # noqa: PLW0603

    now = time.time()
    if _jwks_cache and (now - _jwks_cache_time) < _JWKS_CACHE_TTL:
        return _jwks_cache

    # Probeer eerst via discovery document
    try:
        discovery = requests.get(_get_discovery_url(), timeout=10)
        discovery.raise_for_status()
        jwks_uri = discovery.json().get("jwks_uri", _get_jwks_uri())
    except Exception:
        jwks_uri = _get_jwks_uri()

    try:
        response = requests.get(jwks_uri, timeout=10)
        response.raise_for_status()
        _jwks_cache = response.json()
        _jwks_cache_time = now
        logger.info("JWKS opgehaald van %s (%d keys)", jwks_uri, len(_jwks_cache.get("keys", [])))
        return _jwks_cache
    except Exception as exc:
        logger.error("Kan JWKS niet ophalen van %s: %s", jwks_uri, exc)
        raise RuntimeError(f"JWKS ophalen mislukt: {exc}") from exc


def validate_oidc_token(token: str) -> OidcClaims:
    """Valideer een OIDC token (access of ID token) via JWKS.

    Voert uit:
    1. JWKS ophalen (gecached)
    2. RS256 signature verificatie
    3. Issuer en audience validatie
    4. Expiry check (standaard door PyJWT)
    5. Claims extractie

    Args:
        token: Raw JWT token string.

    Returns:
        OidcClaims met gevalideerde claims.

    Raises:
        ValueError: Bij ongeldige, verlopen, of onbetrouwbare token.
    """
    issuer = _get_oidc_issuer()
    client_id = _get_oidc_client_id()

    if not issuer or not client_id:
        raise ValueError("OIDC niet geconfigureerd (issuer/client_id ontbreekt)")

    jwks_data = _fetch_jwks()

    try:
        # Haal de signing key op basis van de token header
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        # Zoek de juiste key
        rsa_key = None
        for key in jwks_data.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = key
                break

        if rsa_key is None:
            # Probeer JWKS te vernieuwen (key rotation)
            global _jwks_cache_time  # noqa: PLW0603
            _jwks_cache_time = 0
            jwks_data = _fetch_jwks()
            for key in jwks_data.get("keys", []):
                if key.get("kid") == kid:
                    rsa_key = key
                    break

        if rsa_key is None:
            raise ValueError(f"Geen matching JWKS key gevonden voor kid={kid}")

        # Bouw public key van JWK
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(rsa_key)

        # Decodeer en valideer
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=client_id,
            issuer=issuer,
            options={
                "verify_exp": True,
                "verify_iss": True,
                "verify_aud": True,
            },
        )
    except jwt.ExpiredSignatureError as exc:
        raise ValueError("OIDC token verlopen") from exc
    except jwt.InvalidAudienceError as exc:
        raise ValueError("OIDC token audience mismatch") from exc
    except jwt.InvalidIssuerError as exc:
        raise ValueError("OIDC token issuer mismatch") from exc
    except jwt.InvalidTokenError as exc:
        raise ValueError(f"Ongeldig OIDC token: {exc}") from exc

    return OidcClaims(
        subject=payload.get("sub", ""),
        email=payload.get("email", ""),
        name=payload.get("name", payload.get("preferred_username", "")),
        preferred_username=payload.get("preferred_username", ""),
        job_title=payload.get("job_title", ""),
        phone=payload.get("phone", payload.get("phone_number", "")),
        registration_number=payload.get("registration_number", ""),
        company=payload.get("company", ""),
        tenant=payload.get("tenant", ""),
        raw=payload,
    )


def clear_jwks_cache() -> None:
    """Reset de JWKS cache (voor testing)."""
    global _jwks_cache, _jwks_cache_time  # noqa: PLW0603
    _jwks_cache = None
    _jwks_cache_time = 0
