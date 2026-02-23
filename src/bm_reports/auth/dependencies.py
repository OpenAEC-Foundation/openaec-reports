"""FastAPI dependencies voor authenticatie."""

from __future__ import annotations

from fastapi import HTTPException, Request, status

from bm_reports.auth.models import User, UserDB, UserRole
from bm_reports.auth.security import COOKIE_NAME, decode_access_token

# Module-level DB instance (wordt gezet bij app startup)
_user_db: UserDB | None = None


def init_user_db(db: UserDB) -> None:
    """Stel de module-level UserDB instance in.

    Wordt eenmalig aangeroepen bij app startup.

    Args:
        db: UserDB instance.
    """
    global _user_db  # noqa: PLW0603
    _user_db = db


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


async def get_current_user(request: Request) -> User:
    """Haal de huidige user op uit cookie of Bearer token.

    Ondersteunt twee authenticatie-methoden:
    1. httpOnly cookie (browser / frontend)
    2. Authorization: Bearer <token> header (pyRevit / scripts)

    Args:
        request: FastAPI Request object.

    Returns:
        De geauthenticeerde User.

    Raises:
        HTTPException: 401 als geen token aanwezig, verlopen, of de user
            niet bestaat/inactief is.
    """
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
