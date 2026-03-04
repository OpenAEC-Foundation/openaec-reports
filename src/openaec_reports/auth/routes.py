"""Auth endpoints — login, logout, sessie-info, registratie en OIDC token exchange."""

from __future__ import annotations

import logging
import os
import re

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from openaec_reports.auth.dependencies import get_current_user, get_user_db
from openaec_reports.auth.models import User, UserRole
from openaec_reports.auth.oidc import is_oidc_enabled
from openaec_reports.auth.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    COOKIE_NAME,
    COOKIE_SAMESITE,
    create_access_token,
    get_cookie_domain,
    get_cookie_secure,
    hash_password,
    verify_password,
)

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])

# Minimale wachtwoordlengte
MIN_PASSWORD_LENGTH = 8

# E-mail regex (eenvoudig maar effectief)
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _is_registration_enabled() -> bool:
    """Check of open registratie aan staat via environment variable.

    Returns:
        True als registratie is toegestaan.
    """
    return os.environ.get("OPENAEC_REGISTRATION_ENABLED", "true").lower() == "true"


@auth_router.post("/login")
async def login(request: Request):
    """Authenticeer met username + password.

    Body:
        {"username": "...", "password": "..."}

    Returns:
        User data (zonder wachtwoord) + httpOnly cookie.
    """
    body = await request.json()
    username = body.get("username", "").strip()
    password = body.get("password", "")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username en password zijn verplicht",
        )

    db = get_user_db()
    user = db.get_by_username(username)

    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ongeldige gebruikersnaam of wachtwoord",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is gedeactiveerd",
        )

    token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role.value,
    )

    response = JSONResponse(content={"user": user.to_dict(), "token": token})
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=get_cookie_secure(),
        samesite=COOKIE_SAMESITE,
        domain=get_cookie_domain(),
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    logger.info("Login: %s", user.username)
    return response


@auth_router.post("/register")
async def register(request: Request):
    """Registreer een nieuw account (self-service).

    Vereist dat OPENAEC_REGISTRATION_ENABLED=true (default).

    Body:
        {"username": "...", "email": "...", "password": "...", "display_name": "..."}

    Returns:
        User data (zonder wachtwoord) + httpOnly cookie (direct ingelogd).
    """
    if not _is_registration_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registratie is uitgeschakeld",
        )

    body = await request.json()
    username = body.get("username", "").strip()
    email = body.get("email", "").strip()
    password = body.get("password", "")
    display_name = body.get("display_name", "").strip()

    # Validatie
    errors: list[str] = []
    if not username or len(username) < 3:
        errors.append("Gebruikersnaam moet minimaal 3 tekens zijn")
    if not email or not _EMAIL_RE.match(email):
        errors.append("Ongeldig e-mailadres")
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        errors.append(
            f"Wachtwoord moet minimaal {MIN_PASSWORD_LENGTH} tekens zijn"
        )

    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=errors[0] if len(errors) == 1 else errors,
        )

    db = get_user_db()

    # Uniciteit checks
    if db.get_by_username(username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Gebruikersnaam is al in gebruik",
        )
    if db.get_by_email(email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mailadres is al geregistreerd",
        )

    user = User(
        username=username,
        email=email,
        display_name=display_name or username,
        role=UserRole.user,
        hashed_password=hash_password(password),
        auth_provider="local",
    )
    db.create(user)

    # Direct inloggen na registratie
    token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role.value,
    )

    response = JSONResponse(
        content={"user": user.to_dict()},
        status_code=status.HTTP_201_CREATED,
    )
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=get_cookie_secure(),
        samesite=COOKIE_SAMESITE,
        domain=get_cookie_domain(),
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    logger.info("Registratie: %s (%s)", user.username, user.email)
    return response


@auth_router.get("/registration-enabled")
async def registration_enabled():
    """Check of self-registratie aan staat.

    Returns:
        {"enabled": true/false}
    """
    return {"enabled": _is_registration_enabled()}


@auth_router.post("/logout")
async def logout():
    """Verwijder de auth cookie.

    Returns:
        Bevestigingsbericht + cookie deletion.
    """
    response = JSONResponse(content={"detail": "Uitgelogd"})
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        domain=get_cookie_domain(),
    )
    return response


@auth_router.get("/me")
async def me(request: Request):
    """Retourneer de huidige gebruiker.

    Returns:
        User data (zonder wachtwoord).
    """
    user = await get_current_user(request)
    return {"user": user.to_dict()}


@auth_router.get("/oidc/config")
async def oidc_config():
    """Retourneer OIDC configuratie voor de frontend.

    Returns:
        Dict met enabled status en publieke OIDC settings.
    """
    import os

    enabled = is_oidc_enabled()
    if not enabled:
        return {"enabled": False}

    return {
        "enabled": True,
        "issuer": os.environ.get("OPENAEC_OIDC_ISSUER", ""),
        "client_id": os.environ.get("OPENAEC_OIDC_CLIENT_ID", ""),
    }


@auth_router.post("/oidc/token-exchange")
async def oidc_token_exchange(request: Request):
    """Exchange OIDC tokens voor een lokale sessie.

    De frontend stuurt het access_token en/of id_token na de
    OIDC Authorization Code flow. Backend valideert, synct de user,
    en zet een httpOnly cookie.

    Body:
        {"access_token": "...", "id_token": "..."}

    Returns:
        User data + httpOnly cookie.
    """
    from openaec_reports.auth.dependencies import _authenticate_via_oidc

    if not is_oidc_enabled():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OIDC is niet geconfigureerd",
        )

    body = await request.json()
    # Gebruik bij voorkeur het id_token (bevat user claims),
    # fallback naar access_token
    token = body.get("id_token") or body.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="access_token of id_token is verplicht",
        )

    user = _authenticate_via_oidc(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OIDC token validatie mislukt",
        )

    # Maak lokale JWT voor cookie-based sessie
    local_token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role.value,
    )

    response = JSONResponse(content={"user": user.to_dict()})
    response.set_cookie(
        key=COOKIE_NAME,
        value=local_token,
        httponly=True,
        secure=get_cookie_secure(),
        samesite=COOKIE_SAMESITE,
        domain=get_cookie_domain(),
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    logger.info("OIDC token exchange: %s", user.username)
    return response
