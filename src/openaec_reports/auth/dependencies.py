"""FastAPI dependencies voor authenticatie.

Sinds de Authentik unified-SSO migratie (april 2026) draait Reports
achter Caddy + Authentik proxy outpost. Caddy doet de OIDC-flow en
forwardt het resultaat als ``X-Authentik-*`` headers naar de backend.
Het backend hoeft dus geen JWKS meer te valideren.

Authenticatie volgorde voor browser-traffic:
1. ``X-Authentik-Username`` header (forward_auth) → primair pad
2. Lokale legacy login (``OPENAEC_LOCAL_AUTH_ENABLED=true``):
   - ``X-API-Key`` header (machine clients via legacy DB-keys)
   - httpOnly cookie ``bm_access_token`` (eigen JWT)
   - ``Authorization: Bearer <local-jwt>`` (pyRevit / scripts)
3. ``Authorization: Bearer ak_*`` (Authentik service-tokens, fase 6 — TODO)

Bij ontbreken van alle bovenstaande → 401.
"""

from __future__ import annotations

import logging
import os
import uuid
from functools import lru_cache

from fastapi import HTTPException, Request, status

from openaec_reports.auth.api_keys import ApiKeyDB
from openaec_reports.auth.models import OrganisationDB, User, UserDB, UserRole
from openaec_reports.auth.oidc import (
    AuthentikHeaders,
    is_authentik_enabled,
    parse_authentik_headers,
)
from openaec_reports.auth.security import COOKIE_NAME, decode_access_token, hash_password

logger = logging.getLogger(__name__)

# Module-level DB instances (worden gezet bij app startup)
_user_db: UserDB | None = None
_api_key_db: ApiKeyDB | None = None
_organisation_db: OrganisationDB | None = None


def init_user_db(db: UserDB) -> None:
    """Stel de module-level UserDB instance in.

    Wordt eenmalig aangeroepen bij app startup.

    Args:
        db: UserDB instance.
    """
    global _user_db  # noqa: PLW0603
    _user_db = db


def init_api_key_db(db: ApiKeyDB) -> None:
    """Stel de module-level ApiKeyDB instance in.

    Wordt eenmalig aangeroepen bij app startup.

    Args:
        db: ApiKeyDB instance.
    """
    global _api_key_db  # noqa: PLW0603
    _api_key_db = db


def init_organisation_db(db: OrganisationDB) -> None:
    """Stel de module-level OrganisationDB instance in.

    Wordt eenmalig aangeroepen bij app startup.

    Args:
        db: OrganisationDB instance.
    """
    global _organisation_db  # noqa: PLW0603
    _organisation_db = db


def get_user_db() -> UserDB:
    """Haal de actieve UserDB op.

    Returns:
        De UserDB instance.

    Raises:
        RuntimeError: Als init_user_db() niet is aangeroepen.
    """
    if _user_db is None:
        raise RuntimeError("UserDB niet geinitialiseerd — roep init_user_db() aan")
    return _user_db


def get_api_key_db() -> ApiKeyDB:
    """Haal de actieve ApiKeyDB op.

    Returns:
        De ApiKeyDB instance.

    Raises:
        RuntimeError: Als init_api_key_db() niet is aangeroepen.
    """
    if _api_key_db is None:
        raise RuntimeError("ApiKeyDB niet geinitialiseerd — roep init_api_key_db() aan")
    return _api_key_db


def get_organisation_db() -> OrganisationDB:
    """Haal de actieve OrganisationDB op.

    Returns:
        De OrganisationDB instance.

    Raises:
        RuntimeError: Als init_organisation_db() niet is aangeroepen.
    """
    if _organisation_db is None:
        raise RuntimeError("OrganisationDB niet geinitialiseerd — roep init_organisation_db() aan")
    return _organisation_db


def _extract_token(request: Request) -> str | None:
    """Extraheer JWT token uit cookie of Authorization header.

    Volgorde:
    1. httpOnly cookie (browser / frontend)
    2. Authorization: Bearer <token> header (pyRevit / scripts / API clients)

    Args:
        request: FastAPI Request object.

    Returns:
        JWT token string of None als niet aanwezig.
    """
    # Cookie eerst (frontend)
    token = request.cookies.get(COOKIE_NAME)
    if token:
        return token

    # Fallback: Authorization header (pyRevit / scripts)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None


def _authenticate_via_api_key(request: Request) -> User | None:
    """Probeer authenticatie via X-API-Key header.

    Zoekt de key op in de database, valideert actief/verlopen,
    en retourneert de gekoppelde user.

    Args:
        request: FastAPI Request object.

    Returns:
        User of None als geen API key aanwezig of ongeldig.
    """
    api_key_value = request.headers.get("X-API-Key", "").strip()
    if not api_key_value:
        return None

    if _api_key_db is None:
        logger.warning("API key ontvangen maar ApiKeyDB niet geinitialiseerd")
        return None

    api_key = _api_key_db.get_by_key(api_key_value)
    if api_key is None:
        logger.debug("Ongeldige of verlopen API key: %s...", api_key_value[:12])
        return None

    # Haal de gekoppelde user op
    db = get_user_db()
    user = db.get_by_id(api_key.user_id)
    if user is None or not user.is_active:
        logger.warning(
            "API key %s verwijst naar inactieve user %s",
            api_key.key_prefix,
            api_key.user_id,
        )
        return None

    logger.debug("Auth via API key: %s → user %s", api_key.key_prefix, user.username)
    return user


def _authenticate_via_authentik(request: Request) -> User | None:
    """Probeer authenticatie via Caddy + Authentik forward_auth headers.

    Leest ``X-Authentik-*`` headers, koppelt of provisioneert een
    lokale ``User`` record (zodat bestaande FK-relaties met projecten en
    rapporten blijven werken) en synct profiel-velden bij elke call.

    Args:
        request: FastAPI Request object.

    Returns:
        User of None als de verplichte ``X-Authentik-Username``
        header ontbreekt.
    """
    parsed = parse_authentik_headers(request.headers)
    if parsed is None:
        return None

    db = get_user_db()

    # 1. Zoek op stabiele subject (Authentik UID of username fallback)
    user = db.get_by_oidc_subject(parsed.subject)

    # 2. Fallback: email-matching (migratie van bestaande lokale user)
    if user is None and parsed.email:
        email_matches = db.get_all_by_email(parsed.email)
        if len(email_matches) == 1:
            user = email_matches[0]
            db.update(
                user.id,
                oidc_subject=parsed.subject,
                auth_provider="authentik",
            )
            logger.info(
                "Lokale user '%s' gekoppeld aan Authentik subject %s",
                user.username,
                parsed.subject,
            )
        elif len(email_matches) > 1:
            logger.warning(
                "Authentik email '%s' matcht %d users — auto-koppeling overgeslagen",
                parsed.email,
                len(email_matches),
            )

    # 3. Auto-provisioning: maak nieuwe user aan
    if user is None:
        user = User(
            id=uuid.uuid4().hex,
            username=parsed.username,
            email=parsed.email,
            display_name=parsed.name or parsed.username,
            role=UserRole.user,
            tenant=parsed.tenant,
            is_active=True,
            hashed_password=hash_password(uuid.uuid4().hex),  # Random, niet bruikbaar
            phone=parsed.phone,
            job_title=parsed.job_title,
            registration_number=parsed.registration_number,
            company=parsed.company,
            auth_provider="authentik",
            oidc_subject=parsed.subject,
        )
        try:
            db.create(user)
            logger.info(
                "Authentik auto-provisioning: user '%s' aangemaakt",
                user.username,
            )
        except Exception:
            # Username conflict — probeer met suffix
            user.username = f"{user.username}_{parsed.subject[:8]}"
            db.create(user)
            logger.info(
                "Authentik auto-provisioning (met suffix): user '%s' aangemaakt",
                user.username,
            )

    # Profiel sync bij elke request — zodat de eigen DB altijd in sync
    # loopt met de Authentik attributen (geen aparte oidc_profile-call meer)
    sync_fields = _diff_authentik_to_user(parsed, user)
    if sync_fields:
        db.update(user.id, **sync_fields)
        user = db.get_by_id(user.id) or user
        logger.debug(
            "Authentik profiel sync voor '%s': %s", user.username, list(sync_fields.keys())
        )

    if not user.is_active:
        return None

    return user


def _diff_authentik_to_user(parsed: AuthentikHeaders, user: User) -> dict[str, str]:
    """Vergelijk header-claims met de bewaarde user en geef te updaten velden terug.

    Args:
        parsed: De geparseerde Authentik headers.
        user: De huidige in DB opgeslagen ``User``.

    Returns:
        Dict van veld → nieuwe waarde voor velden die afwijken.
    """
    sync: dict[str, str] = {}
    if parsed.email and parsed.email != user.email:
        sync["email"] = parsed.email
    if parsed.name and parsed.name != user.display_name:
        sync["display_name"] = parsed.name
    if parsed.phone and parsed.phone != user.phone:
        sync["phone"] = parsed.phone
    if parsed.job_title and parsed.job_title != user.job_title:
        sync["job_title"] = parsed.job_title
    if parsed.registration_number and parsed.registration_number != user.registration_number:
        sync["registration_number"] = parsed.registration_number
    if parsed.company and parsed.company != user.company:
        sync["company"] = parsed.company
    if parsed.tenant and parsed.tenant != user.tenant:
        sync["tenant"] = parsed.tenant
    return sync


def _is_authentik_service_token(request: Request) -> bool:
    """Detecteer een Authentik machine-client token in de Authorization header.

    Behandelt elke ``Authorization: Bearer`` die GEEN lokale JWT is (JWTs
    beginnen met ``eyJ``). Validatie gebeurt in
    :func:`_authenticate_via_authentik_token` tegen Authentik's
    ``/api/v3/core/users/me/`` endpoint met een 5 min cache.
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return False
    token = auth[7:].strip()
    return bool(token) and not token.startswith("eyJ")


# ---------------------------------------------------------------------------
# Authentik service-token authentication (Fase 6)
# ---------------------------------------------------------------------------
_AUTHENTIK_API_URL = os.environ.get(
    "AUTHENTIK_API_URL", "https://auth.open-aec.com"
).rstrip("/")
_AUTHENTIK_ME_ENDPOINT = f"{_AUTHENTIK_API_URL}/api/v3/core/users/me/"
_TOKEN_CACHE_TTL = 300  # 5 min


@lru_cache(maxsize=256)
def _cached_authentik_user(token_fingerprint: str, bucket_minute: int, token: str) -> dict | None:
    """5-min bucketed token validation. Bucket-minute forceert TTL expiry."""
    try:
        import httpx  # lazy import — alleen geladen bij eerste gebruik
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(
                _AUTHENTIK_ME_ENDPOINT,
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 200:
                return resp.json().get("user")
            logger.debug(
                "Authentik token validation returned %s for fingerprint %s",
                resp.status_code, token_fingerprint,
            )
    except Exception as e:  # pragma: no cover — defensief
        logger.warning(
            "Authentik token validation error (fingerprint=%s): %s",
            token_fingerprint, e,
        )
    return None


def _authenticate_via_authentik_token(request: Request) -> User | None:
    """Probeer authenticatie via Authentik service-token.

    Flow:
    1. Strip ``Bearer`` prefix, skip JWTs (die zijn lokaal).
    2. Valideer tegen Authentik ``/api/v3/core/users/me/`` (5 min cache).
    3. Auto-provision lokale User record op basis van service-account.
    4. Honorer optionele ``X-Original-Tenant`` header voor backend-to-backend
       impersonation — vertrouwd omdat de Bearer al door Authentik gevalideerd is.

    Returns:
        User als Authentik het token accepteert, anders None.
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:].strip()
    if not token or token.startswith("eyJ"):  # JWT → fallthrough naar lokaal pad
        return None

    # Cache key: sha256 van token (eerste 16 hex) + 5-min bucket
    import hashlib
    import time as _time
    fingerprint = hashlib.sha256(token.encode()).hexdigest()[:16]
    bucket = int(_time.time()) // _TOKEN_CACHE_TTL
    ak_user = _cached_authentik_user(fingerprint, bucket, token)
    if ak_user is None:
        logger.debug("Authentik token niet geaccepteerd (fingerprint=%s)", fingerprint)
        return None

    username = ak_user.get("username") or ""
    attributes = ak_user.get("attributes") or {}
    tenant = attributes.get("tenant", "")
    display_name = ak_user.get("name") or username

    if not username:
        logger.warning("Authentik token valide maar username ontbreekt")
        return None

    # Honorer X-Original-Tenant voor backend-to-backend impersonation.
    # Alleen geaccepteerd als Bearer al is gevalideerd (hierboven).
    override_tenant = request.headers.get("X-Original-Tenant", "").strip()
    effective_tenant = override_tenant or tenant

    db = get_user_db()
    # Lookup via stabiele subject 'authentik-svc:<username>'
    subject = f"authentik-svc:{username}"
    user = db.get_by_oidc_subject(subject)

    if user is None:
        # Auto-provision service-account als lokale User
        user = User(
            id=uuid.uuid4().hex,
            username=f"svc_{username.replace('-', '_')}"[:50],
            email=f"{username}@service.openaec.local",
            display_name=display_name,
            role=UserRole.user,
            tenant=effective_tenant,
            is_active=True,
            hashed_password=hash_password(uuid.uuid4().hex),  # nooit bruikbaar
            auth_provider="authentik-token",
            oidc_subject=subject,
        )
        try:
            db.create(user)
            logger.info(
                "Authentik token: auto-provisioned service user '%s' (tenant=%s)",
                username, effective_tenant,
            )
        except Exception:
            user.username = f"{user.username}_{fingerprint[:6]}"
            db.create(user)
    elif override_tenant and user.tenant != override_tenant:
        # Service gebruikt X-Original-Tenant voor on-behalf-of call — update live
        db.update(user.id, tenant=override_tenant)
        user = db.get_by_id(user.id) or user

    if not user.is_active:
        return None

    return user


async def get_current_user(request: Request) -> User:
    """Haal de huidige user op via Authentik-headers, API key of cookie.

    Volgorde:
    1. ``X-Authentik-Username`` (Caddy forward_auth) — primair pad
    2. ``X-API-Key`` (legacy machine clients in de DB)
    3. Lokale JWT via cookie of ``Authorization: Bearer`` header
    4. Authentik service token ``Bearer ak_*`` — TODO fase 6 (501)

    Args:
        request: FastAPI Request object.

    Returns:
        De geauthenticeerde User.

    Raises:
        HTTPException: 401 als geen geldige authenticatie aanwezig.
        HTTPException: 501 voor nog niet geïmplementeerde Authentik
            service-token validatie (zie fase 6 van het SSO-plan).
    """
    # Methode 1: Authentik forward_auth headers
    user = _authenticate_via_authentik(request)
    if user is not None:
        return user

    # Methode 2: Authentik service-token (Bearer, niet-JWT)
    user = _authenticate_via_authentik_token(request)
    if user is not None:
        return user

    # Methode 3: legacy DB API key (alleen relevant als geen Authentik headers)
    user = _authenticate_via_api_key(request)
    if user is not None:
        return user

    # Methode 4: lokale JWT (cookie of Bearer) — uitsluitend voor lokale dev/tests
    token = _extract_token(request)
    if token:
        payload = decode_access_token(token)
        if payload is not None:
            db = get_user_db()
            user = db.get_by_id(payload["sub"])
            if user is not None and user.is_active:
                return user

    # Geen enkel pad werkte
    if is_authentik_enabled():
        # In productie verwacht we forward_auth — geef diagnostische hint
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Authentik forward_auth headers ontbreken. "
                "Controleer de Caddy configuratie."
            ),
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Niet ingelogd",
    )


async def require_admin(request: Request) -> User:
    """Vereis dat de huidige user een admin is.

    Roept get_current_user() aan en controleert de rol.

    Args:
        request: FastAPI Request object.

    Returns:
        De geauthenticeerde admin User.

    Raises:
        HTTPException: 401 als niet ingelogd, 403 als geen admin.
    """
    user = await get_current_user(request)
    if user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin rechten vereist",
        )
    return user
