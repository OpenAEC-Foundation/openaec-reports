"""Admin API endpoints — user CRUD, tenant/template/brand beheer."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

import yaml
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field

from bm_reports.auth.dependencies import get_user_db, require_admin
from bm_reports.auth.models import User, UserRole
from bm_reports.auth.security import hash_password

logger = logging.getLogger(__name__)

# Maximum upload grootte voor YAML bestanden (1 MB)
MAX_YAML_SIZE_BYTES = 1_048_576

# Basis directory voor tenants (relatief aan project root)
_TENANTS_BASE = Path(__file__).parent.parent.parent.parent / "tenants"

admin_router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


# ============================================================
# Pydantic modellen
# ============================================================


class CreateUserRequest(BaseModel):
    """Request model voor het aanmaken van een user."""

    username: str = Field(..., min_length=2, max_length=50)
    email: str = Field(default="")
    display_name: str = Field(default="")
    password: str = Field(..., min_length=6)
    role: str = Field(default="user")
    tenant: str = Field(default="")


class UpdateUserRequest(BaseModel):
    """Request model voor het updaten van een user."""

    email: Optional[str] = None
    display_name: Optional[str] = None
    role: Optional[str] = None
    tenant: Optional[str] = None
    is_active: Optional[bool] = None


class ResetPasswordRequest(BaseModel):
    """Request model voor wachtwoord reset."""

    new_password: str = Field(..., min_length=6)


# ============================================================
# Security helpers
# ============================================================


def _validate_path_segment(segment: str, label: str = "parameter") -> None:
    """Valideer een pad-segment tegen path traversal.

    Args:
        segment: Het pad-segment om te valideren.
        label: Label voor foutmelding.

    Raises:
        HTTPException: 400 bij onveilig pad-segment.
    """
    if not segment or ".." in segment or "/" in segment or "\\" in segment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ongeldig {label}: pad-traversal niet toegestaan",
        )
    if not re.match(r"^[\w\-. ]+$", segment):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ongeldig {label}: alleen letters, cijfers, "
            f"underscores, streepjes en punten toegestaan",
        )


def _get_tenants_base() -> Path:
    """Retourneer de basis directory voor tenants.

    Returns:
        Path naar de tenants directory.
    """
    return _TENANTS_BASE


# ============================================================
# User CRUD
# ============================================================


@admin_router.get("/users")
async def list_users():
    """Lijst alle users.

    Returns:
        Dict met lijst van user dicts.
    """
    db = get_user_db()
    users = db.list_all()
    return {"users": [u.to_dict() for u in users]}


@admin_router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(payload: CreateUserRequest):
    """Maak een nieuwe user aan.

    Args:
        payload: User gegevens.

    Returns:
        De aangemaakte user dict.
    """
    try:
        role = UserRole(payload.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Ongeldige rol: {payload.role}. Kies 'admin' of 'user'.",
        )

    db = get_user_db()
    existing = db.get_by_username(payload.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Gebruikersnaam '{payload.username}' bestaat al",
        )

    user = User(
        username=payload.username,
        email=payload.email,
        display_name=payload.display_name,
        role=role,
        tenant=payload.tenant,
        hashed_password=hash_password(payload.password),
    )
    db.create(user)
    return {"user": user.to_dict()}


@admin_router.get("/users/{user_id}")
async def get_user(user_id: str):
    """Haal user details op.

    Args:
        user_id: De user UUID.

    Returns:
        User dict.
    """
    db = get_user_db()
    user = db.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gebruiker niet gevonden",
        )
    return {"user": user.to_dict()}


@admin_router.patch("/users/{user_id}")
async def update_user(user_id: str, payload: UpdateUserRequest, request: Request):
    """Update een user (partial).

    Args:
        user_id: De user UUID.
        payload: Velden om te updaten.
        request: FastAPI Request (voor admin check).

    Returns:
        De geupdate user dict.
    """
    db = get_user_db()
    existing = db.get_by_id(user_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gebruiker niet gevonden",
        )

    fields: dict = {}
    if payload.email is not None:
        fields["email"] = payload.email
    if payload.display_name is not None:
        fields["display_name"] = payload.display_name
    if payload.role is not None:
        try:
            UserRole(payload.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Ongeldige rol: {payload.role}",
            )
        fields["role"] = payload.role
    if payload.tenant is not None:
        fields["tenant"] = payload.tenant
    if payload.is_active is not None:
        fields["is_active"] = payload.is_active

    if not fields:
        return {"user": existing.to_dict()}

    updated = db.update(user_id, **fields)
    return {"user": updated.to_dict() if updated else existing.to_dict()}


@admin_router.post("/users/{user_id}/reset-password")
async def reset_password(user_id: str, payload: ResetPasswordRequest):
    """Reset het wachtwoord van een user.

    Args:
        user_id: De user UUID.
        payload: Nieuw wachtwoord.

    Returns:
        Bevestigingsbericht.
    """
    db = get_user_db()
    user = db.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gebruiker niet gevonden",
        )

    hashed = hash_password(payload.new_password)
    db.update(user_id, hashed_password=hashed)
    return {"detail": f"Wachtwoord van '{user.username}' is gereset"}


@admin_router.delete("/users/{user_id}")
async def delete_user(user_id: str, request: Request):
    """Verwijder een user.

    Admin kan zichzelf niet verwijderen.

    Args:
        user_id: De user UUID.
        request: FastAPI Request.

    Returns:
        Bevestigingsbericht.
    """
    # Haal de huidige admin op via de dependency
    admin_user = await require_admin(request)
    if admin_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Je kunt jezelf niet verwijderen",
        )

    db = get_user_db()
    deleted = db.delete(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gebruiker niet gevonden",
        )
    return {"detail": "Gebruiker verwijderd"}


# ============================================================
# Tenants
# ============================================================


@admin_router.get("/tenants")
async def list_tenants():
    """Scan de tenants directory en retourneer een overzicht.

    Returns:
        Dict met lijst van tenant info.
    """
    tenants_base = _get_tenants_base()
    tenants = []

    if tenants_base.exists() and tenants_base.is_dir():
        for entry in sorted(tenants_base.iterdir()):
            if not entry.is_dir() or entry.name.startswith("."):
                continue

            has_brand = (entry / "brand.yaml").exists()
            templates_dir = entry / "templates"
            template_count = (
                len(list(templates_dir.glob("*.yaml")))
                if templates_dir.exists()
                else 0
            )
            has_stationery = (entry / "stationery").exists()
            has_fonts = (entry / "fonts").exists()

            tenants.append({
                "name": entry.name,
                "has_brand": has_brand,
                "template_count": template_count,
                "has_stationery": has_stationery,
                "has_fonts": has_fonts,
            })

    return {"tenants": tenants}


# ============================================================
# Templates per tenant
# ============================================================


@admin_router.get("/tenants/{tenant}/templates")
async def list_tenant_templates(tenant: str):
    """Lijst template YAML bestanden voor een tenant.

    Args:
        tenant: Tenant naam.

    Returns:
        Dict met lijst van template bestanden.
    """
    _validate_path_segment(tenant, "tenant")
    templates_dir = _get_tenants_base() / tenant / "templates"

    templates = []
    if templates_dir.exists() and templates_dir.is_dir():
        for f in sorted(templates_dir.glob("*.yaml")):
            templates.append({
                "filename": f.name,
                "size": f.stat().st_size,
            })

    return {"templates": templates}


@admin_router.post("/tenants/{tenant}/templates")
async def upload_tenant_template(tenant: str, file: UploadFile):
    """Upload een YAML template bestand voor een tenant.

    Args:
        tenant: Tenant naam.
        file: Het YAML bestand (multipart upload).

    Returns:
        Bevestigingsbericht met bestandsinformatie.
    """
    _validate_path_segment(tenant, "tenant")

    filename = file.filename or "template.yaml"
    _validate_path_segment(filename, "bestandsnaam")

    if not filename.endswith(".yaml"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alleen .yaml bestanden zijn toegestaan",
        )

    content = await file.read()
    if len(content) > MAX_YAML_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bestand te groot (max {MAX_YAML_SIZE_BYTES // 1024} KB)",
        )

    # Valideer YAML
    try:
        yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Ongeldig YAML bestand: {e}",
        )

    templates_dir = _get_tenants_base() / tenant / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    dest = templates_dir / filename
    dest.write_bytes(content)

    logger.info("Template geupload: %s/%s", tenant, filename)
    return {
        "detail": f"Template '{filename}' geupload",
        "filename": filename,
        "size": len(content),
    }


@admin_router.delete("/tenants/{tenant}/templates/{filename}")
async def delete_tenant_template(tenant: str, filename: str):
    """Verwijder een template bestand.

    Args:
        tenant: Tenant naam.
        filename: Bestandsnaam.

    Returns:
        Bevestigingsbericht.
    """
    _validate_path_segment(tenant, "tenant")
    _validate_path_segment(filename, "bestandsnaam")

    filepath = _get_tenants_base() / tenant / "templates" / filename
    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{filename}' niet gevonden",
        )

    filepath.unlink()
    logger.info("Template verwijderd: %s/%s", tenant, filename)
    return {"detail": f"Template '{filename}' verwijderd"}


# ============================================================
# Brand per tenant
# ============================================================


@admin_router.get("/tenants/{tenant}/brand")
async def get_tenant_brand(tenant: str):
    """Lees de brand.yaml van een tenant.

    Args:
        tenant: Tenant naam.

    Returns:
        Dict met parsed brand config en raw YAML tekst.
    """
    _validate_path_segment(tenant, "tenant")
    brand_path = _get_tenants_base() / tenant / "brand.yaml"

    if not brand_path.exists():
        return {"exists": False, "parsed": None, "raw": ""}

    raw = brand_path.read_text(encoding="utf-8")
    try:
        parsed = yaml.safe_load(raw)
    except yaml.YAMLError:
        parsed = None

    return {"exists": True, "parsed": parsed, "raw": raw}


@admin_router.post("/tenants/{tenant}/brand")
async def upload_tenant_brand(tenant: str, file: UploadFile):
    """Upload een brand.yaml voor een tenant.

    Args:
        tenant: Tenant naam.
        file: Het YAML bestand (multipart upload).

    Returns:
        Bevestigingsbericht.
    """
    _validate_path_segment(tenant, "tenant")

    content = await file.read()
    if len(content) > MAX_YAML_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bestand te groot (max {MAX_YAML_SIZE_BYTES // 1024} KB)",
        )

    # Valideer YAML
    try:
        yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Ongeldig YAML bestand: {e}",
        )

    tenant_dir = _get_tenants_base() / tenant
    tenant_dir.mkdir(parents=True, exist_ok=True)

    dest = tenant_dir / "brand.yaml"
    dest.write_bytes(content)

    logger.info("Brand geupload: %s/brand.yaml", tenant)
    return {"detail": f"Brand configuratie voor '{tenant}' geupload"}
