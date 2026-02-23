"""FastAPI dependencies voor authenticatie."""

from __future__ import annotations

from fastapi import HTTPException, Request, status

from bm_reports.auth.models import User, UserDB
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


async def get_current_user(request: Request) -> User:
    """Haal de huidige user op uit de httpOnly cookie.

    Leest het JWT token uit de cookie, decodeert het, en zoekt
    de user op in de database.

    Args:
        request: FastAPI Request object.

    Returns:
        De geauthenticeerde User.

    Raises:
        HTTPException: 401 als de cookie ontbreekt, verlopen is, of de user
            niet bestaat/inactief is.
    """
    token = request.cookies.get(COOKIE_NAME)
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
