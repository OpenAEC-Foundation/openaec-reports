"""FastAPI dependencies voor authenticatie.

Ondersteunt vier authenticatie-methoden (in volgorde van prioriteit):
1. X-API-Key header — statische key voor machine-to-machine (pyRevit, MCP, scripts)
2. httpOnly cookie — browser / frontend sessies
3. Authorization: Bearer <token> — lokale JWT voor scripts die login() gebruiken
4. Authorization: Bearer <token> — OIDC token (RS256) van Authentik
"""

from __future__ import annotations

import logging

from fastapi import HTTPException, Request, status

from openaec_reports.auth.api_keys import ApiKeyDB
from openaec_reports.auth.models import OrganisationDB, User, UserDB, UserRole
from openaec_reports.auth.security import COOKIE_NAME, decode_access_token

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


def _authenticate_via_oidc(token: str) -> User | None:
    """Probeer authenticatie via OIDC token (RS256 van Authentik).

    Valideert het token, zoekt de user op via oidc_subject of email,
    en maakt indien nodig een nieuwe user aan (auto-provisioning).

    Args:
        token: Bearer token string.

    Returns:
        User of None als OIDC niet enabled of token ongeldig.
    """
    from openaec_reports.auth.oidc import is_oidc_enabled, validate_oidc_token

    if not is_oidc_enabled():
        return None

    try:
        claims = validate_oidc_token(token)
    except ValueError as exc:
        logger.debug("OIDC token validatie mislukt: %s", exc)
        return None

    db = get_user_db()

    # 1. Zoek op oidc_subject (bestaande SSO user)
    user = db.get_by_oidc_subject(claims.subject)

    # 2. Fallback: email-matching (migratie van lokale user)
    #    Alleen koppelen als er PRECIES één user met dit emailadres is.
    #    Bij meerdere matches is niet duidelijk welke user bedoeld is.
    if user is None and claims.email:
        email_matches = db.get_all_by_email(claims.email)
        if len(email_matches) == 1:
            user = email_matches[0]
            # Koppel bestaande lokale user aan OIDC
            db.update(
                user.id,
                oidc_subject=claims.subject,
                auth_provider="oidc",
            )
            logger.info(
                "Lokale user '%s' gekoppeld aan OIDC subject %s",
                user.username,
                claims.subject,
            )
        elif len(email_matches) > 1:
            logger.warning(
                "OIDC email '%s' matcht %d users — auto-koppeling overgeslagen. "
                "Koppel handmatig via oidc_subject.",
                claims.email,
                len(email_matches),
            )

    # 3. Auto-provisioning: maak nieuwe user aan
    if user is None:
        import uuid

        from openaec_reports.auth.security import hash_password

        user = User(
            id=uuid.uuid4().hex,
            username=claims.preferred_username or claims.email.split("@")[0],
            email=claims.email,
            display_name=claims.name,
            role=UserRole.user,
            tenant=claims.tenant,
            is_active=True,
            hashed_password=hash_password(uuid.uuid4().hex),  # Random, niet bruikbaar
            phone=claims.phone,
            job_title=claims.job_title,
            registration_number=claims.registration_number,
            company=claims.company,
            auth_provider="oidc",
            oidc_subject=claims.subject,
        )
        try:
            db.create(user)
            logger.info(
                "OIDC auto-provisioning: user '%s' aangemaakt",
                user.username,
            )
        except Exception:
            # Username conflict — probeer met suffix
            user.username = f"{user.username}_{claims.subject[:8]}"
            db.create(user)
            logger.info(
                "OIDC auto-provisioning (met suffix): user '%s' aangemaakt",
                user.username,
            )

    # Profiel sync bij elke login
    sync_fields: dict[str, str] = {}
    if claims.email and claims.email != user.email:
        sync_fields["email"] = claims.email
    if claims.name and claims.name != user.display_name:
        sync_fields["display_name"] = claims.name
    if claims.phone and claims.phone != user.phone:
        sync_fields["phone"] = claims.phone
    if claims.job_title and claims.job_title != user.job_title:
        sync_fields["job_title"] = claims.job_title
    if claims.registration_number and claims.registration_number != user.registration_number:
        sync_fields["registration_number"] = claims.registration_number
    if claims.company and claims.company != user.company:
        sync_fields["company"] = claims.company
    if claims.tenant and claims.tenant != user.tenant:
        sync_fields["tenant"] = claims.tenant

    if sync_fields:
        db.update(user.id, **sync_fields)
        # Herlaad user met gesyncte velden
        user = db.get_by_id(user.id) or user
        logger.debug("OIDC profiel sync voor '%s': %s", user.username, list(sync_fields.keys()))

    if not user.is_active:
        return None

    logger.debug("Auth via OIDC: subject %s → user %s", claims.subject, user.username)
    return user


async def get_current_user(request: Request) -> User:
    """Haal de huidige user op via API key, cookie, of Bearer token.

    Authenticatie volgorde:
    1. X-API-Key header (machine-to-machine)
    2. httpOnly cookie (browser / frontend)
    3. Authorization: Bearer <token> — lokale JWT
    4. Authorization: Bearer <token> — OIDC token (RS256, Authentik)

    Args:
        request: FastAPI Request object.

    Returns:
        De geauthenticeerde User.

    Raises:
        HTTPException: 401 als geen geldige authenticatie aanwezig.
    """
    # Methode 1: API Key
    user = _authenticate_via_api_key(request)
    if user is not None:
        return user

    # Methode 2 + 3: JWT (cookie of Bearer header)
    token = _extract_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Niet ingelogd",
        )

    # Probeer eerst lokale JWT
    payload = decode_access_token(token)
    if payload is not None:
        db = get_user_db()
        user = db.get_by_id(payload["sub"])
        if user is not None and user.is_active:
            return user

    # Methode 4: OIDC token (als lokale JWT mislukt)
    user = _authenticate_via_oidc(token)
    if user is not None:
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sessie verlopen — log opnieuw in",
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
