"""Auth endpoints — login, logout, en sessie-info."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from openaec_reports.auth.dependencies import get_current_user, get_user_db
from openaec_reports.auth.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    COOKIE_NAME,
    COOKIE_SAMESITE,
    create_access_token,
    get_cookie_domain,
    get_cookie_secure,
    verify_password,
)

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


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
