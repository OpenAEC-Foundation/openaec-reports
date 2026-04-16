"""Auth endpoints — sessie-info, profielbeheer en (lokale) login/registratie.

Sinds de Authentik unified-SSO migratie wordt browser-authenticatie
volledig door Caddy + Authentik forward_auth gedaan. De backend
exposeert hier nog:

- ``GET /api/auth/me`` — huidige user op basis van Authentik headers
- ``GET /api/auth/profile`` + ``PATCH /api/auth/profile`` — profiel-API
- ``POST /api/auth/logout`` — wist legacy cookie + verwijst naar Authentik logout
- ``POST /api/auth/login`` / ``/register`` — alleen actief als
  ``OPENAEC_LOCAL_AUTH_ENABLED=true`` (lokale dev / tests). In productie
  geven deze routes 403.

OIDC-discovery, token-exchange en PKCE code-exchange endpoints zijn
verwijderd; die functionaliteit ligt nu volledig bij Caddy + Authentik.
"""

from __future__ import annotations

import logging
import os
import re

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from openaec_reports.auth.dependencies import get_current_user, get_user_db
from openaec_reports.auth.models import User, UserRole
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


def _is_local_auth_enabled() -> bool:
    """Check of lokale (username/password) login is toegestaan.

    Returns:
        True als lokale authenticatie is ingeschakeld.
    """
    return os.environ.get("OPENAEC_LOCAL_AUTH_ENABLED", "false").lower() == "true"


def _is_registration_enabled() -> bool:
    """Check of open registratie aan staat via environment variable.

    Returns:
        True als registratie is toegestaan.
    """
    if not _is_local_auth_enabled():
        return False
    return os.environ.get("OPENAEC_REGISTRATION_ENABLED", "true").lower() == "true"


@auth_router.post("/login")
async def login(request: Request):
    """Authenticeer met username + password.

    Body:
        {"username": "...", "password": "..."}

    Returns:
        User data (zonder wachtwoord) + httpOnly cookie.
    """
    if not _is_local_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Lokale login is uitgeschakeld. Gebruik SSO.",
        )

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
    if not _is_local_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Lokale registratie is uitgeschakeld. Gebruik SSO.",
        )

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

    De Authentik forward_auth sessie wordt door Caddy/Authentik
    afgehandeld; clients kunnen na deze call doorverwijzen naar
    ``/outpost.goauthentik.io/sign_out`` om volledig uit te loggen.

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

    Gebruikt de Authentik forward_auth headers (Caddy) als primaire bron;
    valt terug op legacy cookie/JWT auth voor lokale dev.

    Returns:
        User data (zonder wachtwoord).
    """
    user = await get_current_user(request)
    return {"user": user.to_dict()}


@auth_router.get("/profile")
async def get_profile(request: Request):
    """Retourneer het volledige profiel van de huidige gebruiker inclusief organisatie.

    Returns:
        User data inclusief gekoppelde organisatie (indien aanwezig).
    """
    user = await get_current_user(request)
    result = user.to_dict()
    if user.organisation_id:
        from openaec_reports.auth.dependencies import get_organisation_db
        try:
            org_db = get_organisation_db()
            org = org_db.get_by_id(user.organisation_id)
            if org:
                result["organisation"] = org.to_dict()
        except RuntimeError:
            pass
    return {"user": result}


@auth_router.patch("/profile")
async def update_profile(request: Request):
    """Update het profiel van de huidige gebruiker.

    Body (optionele velden):
        display_name, email, phone, job_title, company

    Returns:
        De geupdate user data.
    """
    user = await get_current_user(request)
    body = await request.json()
    allowed = {"display_name", "email", "phone", "job_title", "company"}
    fields = {k: v for k, v in body.items() if k in allowed and v is not None}
    if not fields:
        return {"user": user.to_dict()}
    db = get_user_db()
    updated = db.update(user.id, **fields)
    return {"user": updated.to_dict() if updated else user.to_dict()}
