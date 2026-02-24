"""FastAPI dependencies voor authenticatie.

Ondersteunt drie authenticatie-methoden (in volgorde van prioriteit):
1. X-API-Key header — statische key voor machine-to-machine (pyRevit, MCP, scripts)
2. httpOnly cookie — browser / frontend sessies
3. Authorization: Bearer <token> — JWT voor scripts die login() gebruiken
"""

from __future__ import annotations

import logging

from fastapi import HTTPException, Request, status

from bm_reports.auth.api_keys import ApiKeyDB
from bm_reports.auth.models import User, UserDB, UserRole
from bm_reports.auth.security import COOKIE_NAME, decode_access_token

logger = logging.getLogger(__name__)

# Module-level DB instances (worden gezet bij app startup)
_user_db: UserDB | None = None
_api_key_db: ApiKeyDB | None = None


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


async def get_current_user(request: Request) -> User:
    """Haal de huidige user op via API key, cookie, of Bearer token.

    Authenticatie volgorde:
    1. X-API-Key header (machine-to-machine)
    2. httpOnly cookie (browser / frontend)
    3. Authorization: Bearer <token> header (pyRevit login-flow)

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

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessie verlopen — log opnieuw in",
        )

    db = get_user_db()
    user = db.get_by_id(payload["sub"])
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Gebruiker niet gevonden of inactief",
        )

    return user


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
