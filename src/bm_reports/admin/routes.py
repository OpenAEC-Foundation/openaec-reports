"""Admin API endpoints — user CRUD, tenant/template/brand beheer, brand extractie."""

from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
import tempfile
from pathlib import Path

import yaml
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from bm_reports.admin.brand_extraction import (
    MAX_PDF_SIZE_BYTES,
    generate_prompt_package,
    get_reference_pages_yaml,
    merge_brand_yaml,
    run_extraction,
)
from bm_reports.auth.dependencies import get_api_key_db, get_user_db, require_admin
from bm_reports.auth.models import User, UserRole
from bm_reports.auth.security import hash_password

logger = logging.getLogger(__name__)

# Maximum upload grootte voor YAML bestanden (1 MB)
MAX_YAML_SIZE_BYTES = 1_048_576

# Maximum upload grootte voor asset bestanden — PDF, PNG, SVG, TTF, OTF (10 MB)
MAX_ASSET_SIZE_BYTES = 10_485_760

# Toegestane extensies per asset categorie
ALLOWED_EXTENSIONS: dict[str, set[str]] = {
    "stationery": {".pdf", ".png"},
    "logos": {".svg", ".png"},
    "fonts": {".ttf", ".otf"},
}


def _resolve_tenants_base() -> Path:
    """Bepaal de basis directory voor tenants.

    Volgorde:
    1. BM_TENANTS_DIR environment variable (expliciet pad naar tenants/)
    2. Parent van BM_TENANT_DIR (als die gezet is, bijv. /app/tenants/3bm → /app/tenants)
    3. Relatief aan source tree (development fallback)

    Returns:
        Path naar de tenants directory.
    """
    tenants_dir = os.environ.get("BM_TENANTS_DIR") or os.environ.get(
        "BM_TENANTS_ROOT"
    )
    if tenants_dir:
        return Path(tenants_dir)

    tenant_dir = os.environ.get("BM_TENANT_DIR")
    if tenant_dir:
        return Path(tenant_dir).parent

    return Path(__file__).parent.parent.parent.parent / "tenants"

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

    email: str | None = None
    display_name: str | None = None
    role: str | None = None
    tenant: str | None = None
    is_active: bool | None = None


class ResetPasswordRequest(BaseModel):
    """Request model voor wachtwoord reset."""

    new_password: str = Field(..., min_length=6)


class CreateTenantRequest(BaseModel):
    """Request model voor het aanmaken van een tenant."""

    name: str = Field(..., min_length=2, max_length=50, pattern=r"^[\w\-]+$")
    display_name: str = Field(default="")


class CreateApiKeyRequest(BaseModel):
    """Request model voor het aanmaken van een API key."""

    name: str = Field(..., min_length=1, max_length=100)
    user_id: str = Field(...)
    expires_at: str | None = Field(default=None)


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
    return _resolve_tenants_base()


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


def _count_package_templates_for_tenant(tenant: str) -> int:
    """Tel package templates die bij een tenant horen.

    Scant de ingebouwde templates directory voor YAML bestanden
    met een ``tenant:`` veld dat matcht met de opgegeven tenant naam.

    Args:
        tenant: Tenant naam om op te filteren.

    Returns:
        Aantal matchende package templates.
    """
    package_dir = Path(__file__).parent.parent / "assets" / "templates"
    if not package_dir.exists():
        return 0
    count = 0
    for f in package_dir.glob("*.yaml"):
        try:
            with f.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
            if data and data.get("tenant") == tenant:
                count += 1
        except (yaml.YAMLError, OSError):
            continue
    return count


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
            if not entry.is_dir() or entry.name.startswith((".", "test_")):
                continue

            has_brand = (entry / "brand.yaml").exists()
            templates_dir = entry / "templates"
            tenant_template_count = (
                len(list(templates_dir.glob("*.yaml")))
                if templates_dir.exists()
                else 0
            )
            template_count = (
                tenant_template_count
                + _count_package_templates_for_tenant(entry.name)
            )
            stationery_dir = entry / "stationery"
            stationery_count = (
                len([
                    f for f in stationery_dir.iterdir()
                    if f.is_file()
                    and f.suffix.lower() in ALLOWED_EXTENSIONS["stationery"]
                ])
                if stationery_dir.exists()
                else 0
            )

            logos_dir = entry / "logos"
            logo_count = (
                len([
                    f for f in logos_dir.iterdir()
                    if f.is_file()
                    and f.suffix.lower() in ALLOWED_EXTENSIONS["logos"]
                ])
                if logos_dir.exists()
                else 0
            )

            fonts_dir = entry / "fonts"
            font_count = (
                len([
                    f for f in fonts_dir.iterdir()
                    if f.is_file()
                    and f.suffix.lower() in ALLOWED_EXTENSIONS["fonts"]
                ])
                if fonts_dir.exists()
                else 0
            )

            tenants.append({
                "name": entry.name,
                "has_brand": has_brand,
                "template_count": template_count,
                "stationery_count": stationery_count,
                "logo_count": logo_count,
                "font_count": font_count,
            })

    return {"tenants": tenants}


@admin_router.post("/tenants", status_code=status.HTTP_201_CREATED)
async def create_tenant(payload: CreateTenantRequest):
    """Maak een nieuwe tenant directory structuur aan.

    Args:
        payload: Tenant naam (slug) en optioneel display_name.

    Returns:
        Tenant info dict.
    """
    _validate_path_segment(payload.name, "tenant naam")

    tenants_base = _get_tenants_base()
    tenant_dir = tenants_base / payload.name

    if tenant_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant '{payload.name}' bestaat al",
        )

    # Maak directory structuur aan
    tenant_dir.mkdir(parents=True, exist_ok=True)
    (tenant_dir / "templates").mkdir()
    (tenant_dir / "stationery").mkdir()
    (tenant_dir / "logos").mkdir()
    (tenant_dir / "fonts").mkdir()

    # Genereer starter brand.yaml
    display = payload.display_name or payload.name
    brand_config = {
        "name": display,
        "fonts": {
            "heading": "Helvetica",
            "body": "Helvetica",
        },
        "colors": {
            "primary": "#333333",
            "secondary": "#666666",
            "text": "#000000",
        },
    }
    brand_path = tenant_dir / "brand.yaml"
    brand_path.write_text(
        yaml.dump(brand_config, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )

    logger.info("Tenant aangemaakt: %s", payload.name)
    return {
        "tenant": {
            "name": payload.name,
            "has_brand": True,
            "template_count": 0,
            "stationery_count": 0,
            "logo_count": 0,
            "font_count": 0,
        }
    }


@admin_router.delete("/tenants/{tenant}")
async def delete_tenant(tenant: str):
    """Verwijder een volledige tenant directory.

    Args:
        tenant: Tenant naam.

    Returns:
        Bevestigingsbericht.
    """
    _validate_path_segment(tenant, "tenant")

    tenants_base = _get_tenants_base()
    tenant_dir = tenants_base / tenant

    if not tenant_dir.exists() or not tenant_dir.is_dir():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant}' niet gevonden",
        )

    shutil.rmtree(tenant_dir)
    logger.info("Tenant verwijderd: %s", tenant)
    return {"detail": f"Tenant '{tenant}' verwijderd"}


# ============================================================
# Templates per tenant
# ============================================================


@admin_router.get("/tenants/{tenant}/templates")
async def list_tenant_templates(tenant: str):
    """Lijst template YAML bestanden voor een tenant.

    Toont zowel tenant-specifieke templates (uit de tenant directory)
    als package templates die bij de tenant horen (``tenant:`` veld matcht).

    Args:
        tenant: Tenant naam.

    Returns:
        Dict met lijst van template bestanden.
    """
    _validate_path_segment(tenant, "tenant")
    templates: list[dict] = []
    seen: set[str] = set()

    # 1. Tenant-specifieke templates (overschrijven package)
    templates_dir = _get_tenants_base() / tenant / "templates"
    if templates_dir.exists() and templates_dir.is_dir():
        for f in sorted(templates_dir.glob("*.yaml")):
            seen.add(f.stem)
            templates.append({
                "filename": f.name,
                "size": f.stat().st_size,
                "source": "tenant",
            })

    # 2. Package templates die bij deze tenant horen
    package_templates = Path(__file__).parent.parent / "assets" / "templates"
    if package_templates.exists():
        for f in sorted(package_templates.glob("*.yaml")):
            if f.stem in seen:
                continue
            try:
                with f.open("r", encoding="utf-8") as fh:
                    data = yaml.safe_load(fh)
                if data and data.get("tenant") == tenant:
                    seen.add(f.stem)
                    templates.append({
                        "filename": f.name,
                        "size": f.stat().st_size,
                        "source": "package",
                    })
            except (yaml.YAMLError, OSError):
                continue

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


# ============================================================
# Generiek asset beheer (stationery, logos, fonts)
# ============================================================


def _validate_asset_category(category: str) -> set[str]:
    """Valideer en retourneer toegestane extensies voor een asset categorie.

    Args:
        category: Asset categorie ("stationery", "logos", "fonts").

    Returns:
        Set van toegestane extensies.

    Raises:
        HTTPException: 400 bij ongeldige categorie.
    """
    allowed = ALLOWED_EXTENSIONS.get(category)
    if allowed is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ongeldige asset categorie: {category}",
        )
    return allowed


@admin_router.get("/tenants/{tenant}/assets/{category}")
async def list_tenant_assets(tenant: str, category: str):
    """Lijst bestanden in een asset categorie voor een tenant.

    Args:
        tenant: Tenant naam.
        category: Asset categorie ("stationery", "logos", "fonts").

    Returns:
        Dict met lijst van asset bestanden.
    """
    _validate_path_segment(tenant, "tenant")
    allowed_exts = _validate_asset_category(category)

    asset_dir = _get_tenants_base() / tenant / category
    assets: list[dict[str, str | int]] = []

    if asset_dir.exists() and asset_dir.is_dir():
        for f in sorted(asset_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in allowed_exts:
                assets.append({
                    "filename": f.name,
                    "size": f.stat().st_size,
                })

    return {"assets": assets}


@admin_router.post("/tenants/{tenant}/assets/{category}")
async def upload_tenant_asset(tenant: str, category: str, file: UploadFile):
    """Upload een asset bestand voor een tenant.

    Args:
        tenant: Tenant naam.
        category: Asset categorie ("stationery", "logos", "fonts").
        file: Het bestand (multipart upload).

    Returns:
        Bevestigingsbericht met bestandsinformatie.
    """
    _validate_path_segment(tenant, "tenant")
    allowed_exts = _validate_asset_category(category)

    filename = file.filename or "asset"
    _validate_path_segment(filename, "bestandsnaam")

    # Controleer extensie
    ext = Path(filename).suffix.lower()
    if ext not in allowed_exts:
        allowed_str = ", ".join(sorted(allowed_exts))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Alleen {allowed_str} bestanden zijn toegestaan "
            f"voor {category}",
        )

    content = await file.read()
    if len(content) > MAX_ASSET_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bestand te groot "
            f"(max {MAX_ASSET_SIZE_BYTES // (1024 * 1024)} MB)",
        )

    asset_dir = _get_tenants_base() / tenant / category
    asset_dir.mkdir(parents=True, exist_ok=True)

    dest = asset_dir / filename
    dest.write_bytes(content)

    logger.info("Asset geupload: %s/%s/%s", tenant, category, filename)
    return {
        "detail": f"Bestand '{filename}' geupload naar {category}",
        "filename": filename,
        "size": len(content),
    }


@admin_router.delete("/tenants/{tenant}/assets/{category}/{filename}")
async def delete_tenant_asset(
    tenant: str, category: str, filename: str
):
    """Verwijder een asset bestand.

    Args:
        tenant: Tenant naam.
        category: Asset categorie ("stationery", "logos", "fonts").
        filename: Bestandsnaam.

    Returns:
        Bevestigingsbericht.
    """
    _validate_path_segment(tenant, "tenant")
    _validate_asset_category(category)
    _validate_path_segment(filename, "bestandsnaam")

    filepath = _get_tenants_base() / tenant / category / filename
    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bestand '{filename}' niet gevonden in {category}",
        )

    filepath.unlink()
    logger.info("Asset verwijderd: %s/%s/%s", tenant, category, filename)
    return {"detail": f"Bestand '{filename}' verwijderd uit {category}"}


# ============================================================
# API Keys
# ============================================================


@admin_router.get("/api-keys")
async def list_api_keys():
    """Lijst alle API keys.

    Returns:
        Dict met lijst van API key metadata (zonder hashes).
    """
    db = get_api_key_db()
    keys = db.list_all()
    return {"api_keys": [k.to_dict() for k in keys]}


@admin_router.post("/api-keys", status_code=status.HTTP_201_CREATED)
async def create_api_key(payload: CreateApiKeyRequest):
    """Maak een nieuwe API key aan.

    De plaintext key wordt eenmalig geretourneerd — bewaar deze goed!

    Args:
        payload: Naam, user_id, en optionele verloopdatum.

    Returns:
        API key metadata + de plaintext key (eenmalig).
    """
    # Controleer dat de user bestaat
    user_db = get_user_db()
    user = user_db.get_by_id(payload.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gebruiker niet gevonden",
        )

    db = get_api_key_db()
    api_key, plaintext = db.create(
        name=payload.name,
        user_id=payload.user_id,
        expires_at=payload.expires_at,
    )

    return {
        "api_key": api_key.to_dict(),
        "plaintext_key": plaintext,
    }


@admin_router.post("/api-keys/{key_id}/revoke")
async def revoke_api_key(key_id: str):
    """Deactiveer een API key (soft delete).

    Args:
        key_id: ID van de API key.

    Returns:
        Bevestigingsbericht.
    """
    db = get_api_key_db()
    revoked = db.revoke(key_id)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key niet gevonden",
        )
    return {"detail": "API key ingetrokken"}


@admin_router.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: str):
    """Verwijder een API key permanent.

    Args:
        key_id: ID van de API key.

    Returns:
        Bevestigingsbericht.
    """
    db = get_api_key_db()
    deleted = db.delete(key_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key niet gevonden",
        )
    return {"detail": "API key verwijderd"}


# ============================================================
# Brand Extraction Wizard
# ============================================================


class BrandExtractRequest(BaseModel):
    """Request model voor brand extractie start."""

    brand_name: str = Field(..., min_length=1, max_length=100)
    brand_slug: str = Field(default="")
    dpi: int = Field(default=150, ge=72, le=300)


class BrandMergeRequest(BaseModel):
    """Request model voor het mergen van brand onderdelen."""

    edited_extraction: dict = Field(...)
    pages_yaml: str | None = Field(default=None)
    brand_name: str = Field(..., min_length=1)
    brand_slug: str = Field(default="")


class PromptPackageRequest(BaseModel):
    """Request model voor prompt package generatie."""

    edited_extraction: dict = Field(...)


@admin_router.post("/tenants/{tenant}/brand-extract")
async def start_brand_extraction(
    tenant: str,
    pdf_file: UploadFile,
    brand_name: str = "Brand",
    brand_slug: str = "",
    dpi: int = 150,
    stamkaart: UploadFile | None = None,
):
    """Start de brand extraction pipeline.

    Upload een referentie-PDF en ontvang gestructureerde extractie-data
    met kleuren, fonts, styles, page classificaties en layouts.

    Args:
        tenant: Tenant naam.
        pdf_file: Het referentie-rapport PDF bestand.
        brand_name: Weergavenaam van het merk.
        brand_slug: Machine-leesbare ID (default: tenant naam).
        dpi: DPI voor pagina renders (72-300).
        stamkaart: Optioneel stamkaart PDF bestand.

    Returns:
        Dict met extraction data, page images, en draft YAML.
    """
    _validate_path_segment(tenant, "tenant")

    if not brand_slug:
        brand_slug = tenant

    # Valideer DPI
    if dpi < 72 or dpi > 300:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DPI moet tussen 72 en 300 liggen",
        )

    # Lees en valideer PDF
    pdf_content = await pdf_file.read()
    if len(pdf_content) > MAX_PDF_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PDF te groot (max {MAX_PDF_SIZE_BYTES // (1024 * 1024)} MB)",
        )

    if not pdf_content[:5] == b"%PDF-":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bestand is geen geldig PDF",
        )

    # Lees optionele stamkaart
    stamkaart_content = None
    if stamkaart:
        stamkaart_content = await stamkaart.read()
        if not stamkaart_content[:5] == b"%PDF-":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stamkaart is geen geldig PDF",
            )

    tenants_base = _get_tenants_base()
    tenant_dir = tenants_base / tenant

    if not tenant_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant}' niet gevonden",
        )

    # Schrijf PDF naar tijdelijk bestand en draai extractie
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False
        ) as tmp_pdf:
            tmp_pdf.write(pdf_content)
            tmp_pdf_path = Path(tmp_pdf.name)

        stamkaart_path = None
        if stamkaart_content:
            with tempfile.NamedTemporaryFile(
                suffix=".pdf", delete=False
            ) as tmp_stamkaart:
                tmp_stamkaart.write(stamkaart_content)
                stamkaart_path = Path(tmp_stamkaart.name)

        # Draai extractie in threadpool (CPU-intensief)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: run_extraction(
                pdf_path=tmp_pdf_path,
                tenant_dir=tenant_dir,
                brand_name=brand_name,
                brand_slug=brand_slug,
                stamkaart_path=stamkaart_path,
                dpi=dpi,
            ),
        )

        logger.info(
            "Brand extractie voltooid voor tenant '%s': %d pagina's",
            tenant,
            len(result["extraction"]["page_classifications"]),
        )

        return result

    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PyMuPDF is niet beschikbaar: {exc}",
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Brand extractie gefaald voor tenant '%s'", tenant)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extractie gefaald: {exc}",
        )
    finally:
        # Cleanup tijdelijke bestanden
        if tmp_pdf_path.exists():
            tmp_pdf_path.unlink()
        if stamkaart_path and stamkaart_path.exists():
            stamkaart_path.unlink()


@admin_router.get("/tenants/{tenant}/analysis/pages/{filename}")
async def get_analysis_page_image(tenant: str, filename: str):
    """Serveer een gerenderde pagina-afbeelding uit de analyse directory.

    Args:
        tenant: Tenant naam.
        filename: Bestandsnaam (bijv. page_001.png).

    Returns:
        PNG afbeelding als FileResponse.
    """
    _validate_path_segment(tenant, "tenant")
    _validate_path_segment(filename, "bestandsnaam")

    if not filename.endswith(".png"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alleen .png bestanden zijn toegestaan",
        )

    filepath = _get_tenants_base() / tenant / "analysis" / "pages" / filename

    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pagina '{filename}' niet gevonden",
        )

    return FileResponse(filepath, media_type="image/png")


@admin_router.post("/tenants/{tenant}/brand-extract/prompt-package")
async def create_prompt_package(tenant: str, payload: PromptPackageRequest):
    """Genereer een prompt package voor Claude Desktop.

    Combineert de (gecorrigeerde) extractie-data met instructies
    en een referentie-template tot een copy-paste-ready markdown prompt.

    Args:
        tenant: Tenant naam.
        payload: Gecorrigeerde extractie data.

    Returns:
        Dict met de prompt markdown string en pagina-afbeeldingen.
    """
    _validate_path_segment(tenant, "tenant")

    tenants_base = _get_tenants_base()
    tenant_dir = tenants_base / tenant

    if not tenant_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant}' niet gevonden",
        )

    # Zoek beschikbare pagina-afbeeldingen
    pages_dir = tenant_dir / "analysis" / "pages"
    page_image_map: dict[str, str] = {}

    if pages_dir.exists():
        # Bouw map uit page_classifications in de extractie data
        for pc in payload.edited_extraction.get("page_classifications", []):
            page_type = pc.get("type", "")
            page_num = pc.get("page_number", 0)
            filename = f"page_{page_num:03d}.png"
            img_path = pages_dir / filename

            if img_path.exists() and page_type not in page_image_map:
                page_image_map[page_type] = filename

    # Haal referentie pages YAML op
    reference_yaml = get_reference_pages_yaml(tenants_base)

    # Genereer brand naam/slug uit extractie data
    brand_info = payload.edited_extraction.get("brand", {})
    brand_name = brand_info.get("name", tenant)
    brand_slug = brand_info.get("slug", tenant)

    prompt = generate_prompt_package(
        extraction=payload.edited_extraction,
        page_image_map=page_image_map,
        brand_name=brand_name,
        brand_slug=brand_slug,
        reference_pages_yaml=reference_yaml,
    )

    return {
        "prompt": prompt,
        "page_images": page_image_map,
        "pages_dir": f"/api/admin/tenants/{tenant}/analysis/pages",
    }


@admin_router.post("/tenants/{tenant}/brand-merge")
async def merge_brand(tenant: str, payload: BrandMergeRequest):
    """Merge alle brand onderdelen tot een complete brand.yaml.

    Combineert user-gecorrigeerde extractie data met het Claude Desktop
    artifact (pages-sectie) tot een volledige brand configuratie.

    Args:
        tenant: Tenant naam.
        payload: Gecorrigeerde data + pages YAML.

    Returns:
        Dict met de finale YAML string en bevestiging.
    """
    _validate_path_segment(tenant, "tenant")

    tenants_base = _get_tenants_base()
    tenant_dir = tenants_base / tenant

    if not tenant_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant}' niet gevonden",
        )

    brand_name = payload.brand_name
    brand_slug = payload.brand_slug or tenant

    try:
        final_yaml = merge_brand_yaml(
            edited_extraction=payload.edited_extraction,
            pages_yaml_str=payload.pages_yaml,
            brand_name=brand_name,
            brand_slug=brand_slug,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    # Schrijf brand.yaml
    brand_path = tenant_dir / "brand.yaml"
    brand_path.write_text(final_yaml, encoding="utf-8")

    logger.info("Brand YAML gemerged en opgeslagen: %s/brand.yaml", tenant)

    return {
        "detail": f"Brand configuratie voor '{tenant}' opgeslagen",
        "yaml": final_yaml,
        "path": str(brand_path),
    }
