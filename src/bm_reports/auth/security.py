"""Wachtwoord hashing en JWT token management."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

logger = logging.getLogger(__name__)

# --- JWT configuratie ---

_DEFAULT_SECRET = "CHANGE-ME-in-production"  # noqa: S105
JWT_SECRET_KEY = os.environ.get("BM_JWT_SECRET", _DEFAULT_SECRET)
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.environ.get("BM_TOKEN_EXPIRE_MINUTES", "480")
)

# --- Cookie configuratie ---

COOKIE_NAME = "bm_access_token"
COOKIE_SAMESITE = "lax"


def get_cookie_secure() -> bool:
    """Lees COOKIE_SECURE dynamisch uit environment.

    Returns:
        True als cookies alleen via HTTPS verstuurd mogen worden.
    """
    return os.environ.get("BM_COOKIE_SECURE", "true").lower() == "true"


def get_cookie_domain() -> str | None:
    """Lees COOKIE_DOMAIN dynamisch uit environment.

    Returns:
        Cookie domain of None.
    """
    return os.environ.get("BM_COOKIE_DOMAIN", None)


def is_default_secret() -> bool:
    """Controleer of de JWT secret nog op de default staat.

    Returns:
        True als de default secret actief is.
    """
    return JWT_SECRET_KEY == _DEFAULT_SECRET


def hash_password(password: str) -> str:
    """Hash een wachtwoord met bcrypt.

    Args:
        password: Platte tekst wachtwoord.

    Returns:
        Gehashte wachtwoord string.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifieer een wachtwoord tegen de hash.

    Args:
        plain_password: Ingevoerd wachtwoord.
        hashed_password: Opgeslagen hash.

    Returns:
        True als het wachtwoord klopt.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(
    user_id: str,
    username: str,
    role: str,
    expires_minutes: int | None = None,
) -> str:
    """Maak een JWT access token aan.

    Args:
        user_id: User UUID.
        username: Gebruikersnaam.
        role: Gebruikersrol.
        expires_minutes: Optionele override voor token geldigheid.

    Returns:
        Gecodeerde JWT token string.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Decodeer en valideer een JWT token.

    Args:
        token: JWT token string.

    Returns:
        Payload dict of None bij ongeldige/verlopen token.
    """
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.debug("Token verlopen")
        return None
    except jwt.InvalidTokenError:
        logger.debug("Ongeldige token")
        return None
