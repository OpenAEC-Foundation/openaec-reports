"""Brand Onboarding API — endpoints voor de wizard flow.

Aparte router die gekoppeld wordt aan de hoofd FastAPI app.
Ondersteunt een stapsgewijze brand onboarding:

1. Upload reference + stationery PDF paren
2. Draai diff per paginatype → detecteer dynamische velden
3. Bekijk diff images en wijs veld-rollen toe
4. Genereer brand.yaml + stationery package (ZIP)

Usage (in api.py of integratie)::

    from openaec_reports.brand_api import brand_router
    app.include_router(brand_router)
"""

from __future__ import annotations

import json
import logging
import re
import shutil
import tempfile
import uuid
import zipfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from openaec_reports.auth.dependencies import get_current_user
from openaec_reports.auth.models import User
from openaec_reports.tools.diff_engine import (
    DetectedField,
    DiffResult,
    run_diff,
)

logger = logging.getLogger(__name__)

# Session opslag
SESSIONS_DIR = Path(tempfile.gettempdir()) / "bm_brand_sessions"

# Bekende pagina-types
_KNOWN_PAGE_TYPES = {
    "cover",
    "colofon",
    "content_portrait",
    "content_landscape",
    "backcover",
}

# Naamconventie: {page_type}_reference.pdf / {page_type}_stationery.pdf
_REFERENCE_SUFFIX = "_reference.pdf"
_STATIONERY_SUFFIX = "_stationery.pdf"

# Session TTL (niet automatisch, cleanup via DELETE endpoint)
_SESSION_METADATA_FILE = "session.json"
_DIFF_RESULTS_FILE = "diff_results.json"

brand_router = APIRouter(
    prefix="/api/brand",
    tags=["brand-onboarding"],
    dependencies=[Depends(get_current_user)],
)

# Validatie patterns
_SESSION_ID_PATTERN = re.compile(r"^[a-f0-9]{12}$")


def _validate_session_id(session_id: str) -> str:
    """Valideer session_id format (12 hex chars).

    Args:
        session_id: Te valideren ID.

    Returns:
        Het gevalideerde session_id.

    Raises:
        HTTPException: Bij ongeldig formaat.
    """
    if not _SESSION_ID_PATTERN.match(session_id):
        raise HTTPException(status_code=400, detail="Ongeldig session_id formaat")
    return session_id


def _validate_filename(filename: str) -> str:
    """Voorkom path traversal in bestandsnamen.

    Args:
        filename: Te valideren bestandsnaam.

    Returns:
        Gesanitizede bestandsnaam.

    Raises:
        HTTPException: Bij ongeldige bestandsnaam.
    """
    if "\\" in filename or "/" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Ongeldige bestandsnaam")
    safe = Path(filename).name
    if safe != filename:
        raise HTTPException(status_code=400, detail="Ongeldige bestandsnaam")
    return safe


def _to_slug(name: str) -> str:
    """Genereer URL-safe slug uit naam.

    Args:
        name: Merknaam.

    Returns:
        Slug (lowercase, alfanumeriek + dashes).
    """
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


# ============================================================
# Session Management
# ============================================================


class BrandSession:
    """Beheert uploads en resultaten voor een brand onboarding sessie.

    Attrs:
        session_id: Unieke sessie identifier.
        base_dir: Basis directory voor deze sessie.
        uploads_dir: Map voor geüploade PDF's.
        output_dir: Map voor gegenereerde output.
    """

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.base_dir = SESSIONS_DIR / session_id
        self.uploads_dir = self.base_dir / "uploads"
        self.output_dir = self.base_dir / "output"

    def create(self) -> None:
        """Maak session directories aan."""
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def exists(self) -> bool:
        """Check of de sessie bestaat."""
        return self.base_dir.is_dir()

    def get_pairs(self) -> dict[str, dict[str, bool]]:
        """Detecteer reference/stationery paren in uploads.

        Returns:
            Dict van page_type → {"has_reference": bool, "has_stationery": bool}.
        """
        pairs: dict[str, dict[str, bool]] = {}

        if not self.uploads_dir.exists():
            return pairs

        for pdf_file in self.uploads_dir.glob("*.pdf"):
            name = pdf_file.name.lower()
            if name.endswith(_REFERENCE_SUFFIX):
                page_type = name[: -len(_REFERENCE_SUFFIX)]
                pairs.setdefault(page_type, {"has_reference": False, "has_stationery": False})
                pairs[page_type]["has_reference"] = True
            elif name.endswith(_STATIONERY_SUFFIX):
                page_type = name[: -len(_STATIONERY_SUFFIX)]
                pairs.setdefault(page_type, {"has_reference": False, "has_stationery": False})
                pairs[page_type]["has_stationery"] = True

        return pairs

    def get_pdf_path(self, page_type: str, variant: str) -> Path:
        """Geef pad naar een specifieke PDF.

        Args:
            page_type: Pagina-type (cover, colofon, etc.).
            variant: "reference" of "stationery".

        Returns:
            Pad naar het PDF bestand.
        """
        suffix = _REFERENCE_SUFFIX if variant == "reference" else _STATIONERY_SUFFIX
        return self.uploads_dir / f"{page_type}{suffix}"

    def save_metadata(self, metadata: dict) -> None:
        """Sla sessie metadata op als JSON."""
        path = self.base_dir / _SESSION_METADATA_FILE
        path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    def load_metadata(self) -> dict:
        """Laad sessie metadata."""
        path = self.base_dir / _SESSION_METADATA_FILE
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {}

    def get_owner(self) -> str | None:
        """Retourneer de user_id van de sessie-eigenaar."""
        return self.load_metadata().get("owner_id")

    def verify_owner(self, user_id: str) -> None:
        """Verifieer dat de aanvrager de sessie-eigenaar is.

        Raises:
            HTTPException: Als de user niet de eigenaar is.
        """
        owner = self.get_owner()
        if owner and owner != user_id:
            raise HTTPException(
                status_code=403,
                detail="Geen toegang tot deze sessie",
            )

    def save_diff_result(self, page_type: str, result: DiffResult) -> None:
        """Sla diff resultaat op als JSON.

        Args:
            page_type: Pagina-type.
            result: DiffResult om op te slaan.
        """
        results = self._load_all_results()
        results[page_type] = _diff_result_to_dict(result)
        path = self.base_dir / _DIFF_RESULTS_FILE
        path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    def load_diff_result(self, page_type: str) -> dict | None:
        """Laad een eerder opgeslagen diff resultaat.

        Args:
            page_type: Pagina-type.

        Returns:
            Dict representatie of None.
        """
        results = self._load_all_results()
        return results.get(page_type)

    def update_fields(self, page_type: str, field_updates: list[dict]) -> dict | None:
        """Update veld-rollen in een opgeslagen diff resultaat.

        Args:
            page_type: Pagina-type.
            field_updates: Lijst van {"id": ..., "role": ..., "name": ...}.

        Returns:
            Bijgewerkt diff resultaat, of None.
        """
        results = self._load_all_results()
        diff_data = results.get(page_type)
        if diff_data is None:
            return None

        updates_map = {u["id"]: u for u in field_updates}
        for fld in diff_data.get("fields", []):
            if fld["id"] in updates_map:
                update = updates_map[fld["id"]]
                fld["role"] = update.get("role")
                fld["name"] = update.get("name")

        path = self.base_dir / _DIFF_RESULTS_FILE
        path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        return diff_data

    def generate_brand_package(self, config: dict) -> Path:
        """Genereer brand directory + ZIP.

        Args:
            config: Dict met brand_name, brand_slug, colors, modules.

        Returns:
            Pad naar gegenereerde ZIP.
        """
        slug = config.get("brand_slug", "new-brand")
        brand_dir = self.output_dir / slug
        brand_dir.mkdir(parents=True, exist_ok=True)

        # Kopieer stationery PDF's
        stationery_dir = brand_dir / "stationery"
        stationery_dir.mkdir(exist_ok=True)
        pairs = self.get_pairs()
        stationery_files = []

        for page_type, status in pairs.items():
            if status["has_stationery"]:
                src = self.get_pdf_path(page_type, "stationery")
                dst = stationery_dir / f"{page_type}.pdf"
                shutil.copy2(src, dst)
                stationery_files.append({
                    "page_type": page_type,
                    "filename": f"{page_type}.pdf",
                })

        # Genereer brand.yaml
        brand_yaml = _generate_brand_yaml(config, self._load_all_results(), stationery_files)
        yaml_path = brand_dir / "brand.yaml"
        yaml_path.write_text(brand_yaml, encoding="utf-8")

        # Maak lege directories
        (brand_dir / "logos").mkdir(exist_ok=True)
        (brand_dir / "fonts").mkdir(exist_ok=True)

        # ZIP
        zip_path = self.output_dir / "brand_package.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in brand_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.output_dir)
                    zf.write(file_path, arcname)

        return zip_path

    def cleanup(self) -> None:
        """Verwijder sessie directory."""
        if self.base_dir.exists():
            shutil.rmtree(self.base_dir)

    def _load_all_results(self) -> dict:
        """Laad alle diff resultaten."""
        path = self.base_dir / _DIFF_RESULTS_FILE
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {}


# ============================================================
# Endpoints
# ============================================================


@brand_router.post("/upload-pairs")
async def upload_pairs(
    files: list[UploadFile] = File(...),
    brand_name: str = Form(""),
    brand_slug: str = Form(""),
    user: User = Depends(get_current_user),
) -> JSONResponse:
    """Upload reference en stationery PDF paren.

    Accepteert meerdere PDF bestanden via multipart upload.
    Naamconventie: ``{page_type}_reference.pdf`` + ``{page_type}_stationery.pdf``

    Args:
        files: Lijst van PDF uploads.
        brand_name: Merknaam.
        brand_slug: Machine-leesbare identifier.
    """
    session_id = uuid.uuid4().hex[:12]
    session = BrandSession(session_id)
    session.create()

    # Sla bestanden op
    for upload_file in files:
        if not upload_file.filename:
            continue
        dest = session.uploads_dir / upload_file.filename.lower()
        content = await upload_file.read()
        dest.write_bytes(content)

    # Bepaal slug
    slug = brand_slug or _to_slug(brand_name)

    # Sla metadata op met eigenaar
    session.save_metadata({
        "brand_name": brand_name,
        "brand_slug": slug,
        "owner_id": user.id,
    })

    # Detecteer paren
    pairs = session.get_pairs()
    warnings: list[str] = []
    pair_list: list[dict[str, Any]] = []

    for page_type, status in sorted(pairs.items()):
        complete = status["has_reference"] and status["has_stationery"]
        pair_list.append({
            "page_type": page_type,
            "has_reference": status["has_reference"],
            "has_stationery": status["has_stationery"],
            "complete": complete,
        })
        if not status["has_stationery"]:
            warnings.append(f"{page_type}: stationery ontbreekt")
        if not status["has_reference"]:
            warnings.append(f"{page_type}: reference ontbreekt")

    return JSONResponse({
        "session_id": session_id,
        "brand_slug": slug,
        "pairs": pair_list,
        "warnings": warnings,
    })


@brand_router.post("/diff/{session_id}/{page_type}")
async def diff_page(
    session_id: str,
    page_type: str,
    user: User = Depends(get_current_user),
) -> JSONResponse:
    """Draai de stationery diff op één reference/stationery paar.

    Args:
        session_id: Sessie identifier.
        page_type: Pagina-type (cover, colofon, etc.).
    """
    _validate_session_id(session_id)
    session = BrandSession(session_id)
    if not session.exists():
        raise HTTPException(status_code=404, detail="Sessie niet gevonden")
    session.verify_owner(user.id)

    ref_path = session.get_pdf_path(page_type, "reference")
    stat_path = session.get_pdf_path(page_type, "stationery")

    if not ref_path.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Reference PDF ontbreekt voor {page_type}",
        )
    if not stat_path.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Stationery PDF ontbreekt voor {page_type}",
        )

    try:
        result = run_diff(
            reference_pdf=ref_path,
            stationery_pdf=stat_path,
            output_dir=session.output_dir,
            page_type=page_type,
        )
    except Exception as exc:
        logger.exception("Diff failed voor %s/%s", session_id, page_type)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Sla resultaat op
    session.save_diff_result(page_type, result)

    return JSONResponse({
        "page_type": result.page_type,
        "orientation": result.orientation,
        "page_size": {
            "width_pt": result.width_pt,
            "height_pt": result.height_pt,
        },
        "diff_image_url": f"/api/brand/diff-image/{session_id}/{page_type}",
        "reference_image_url": f"/api/brand/preview/{session_id}/{page_type}_reference.png",
        "stationery_image_url": f"/api/brand/preview/{session_id}/{page_type}_stationery.png",
        "detected_fields": [_field_to_dict(f) for f in result.fields],
        "detected_colors": result.colors,
        "detected_fonts": result.fonts,
    })


@brand_router.get("/diff-image/{session_id}/{page_type}")
async def get_diff_image(
    session_id: str,
    page_type: str,
    user: User = Depends(get_current_user),
) -> FileResponse:
    """Serveer de diff PNG met rode overlay boxes.

    Args:
        session_id: Sessie identifier.
        page_type: Pagina-type.
    """
    _validate_session_id(session_id)
    session = BrandSession(session_id)
    session.verify_owner(user.id)
    img_path = session.output_dir / f"{page_type}_diff.png"

    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Diff image niet gevonden")

    return FileResponse(img_path, media_type="image/png")


@brand_router.get("/preview/{session_id}/{filename}")
async def get_preview(
    session_id: str,
    filename: str,
    user: User = Depends(get_current_user),
) -> FileResponse:
    """Serveer een preview image (PNG render van een PDF pagina).

    Args:
        session_id: Sessie identifier.
        filename: Bestandsnaam (bijv. cover_reference.png).
    """
    _validate_session_id(session_id)
    safe_name = _validate_filename(filename)
    session = BrandSession(session_id)
    session.verify_owner(user.id)

    img_path = session.output_dir / safe_name

    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Preview niet gevonden")

    return FileResponse(img_path, media_type="image/png")


@brand_router.put("/fields/{session_id}/{page_type}")
async def update_fields(
    session_id: str,
    page_type: str,
    body: dict,
    user: User = Depends(get_current_user),
) -> JSONResponse:
    """Update veld-rollen na handmatige toewijzing in de frontend.

    Args:
        session_id: Sessie identifier.
        page_type: Pagina-type.
        body: Dict met "fields" lijst van {"id", "role", "name"}.
    """
    _validate_session_id(session_id)
    session = BrandSession(session_id)
    if not session.exists():
        raise HTTPException(status_code=404, detail="Sessie niet gevonden")
    session.verify_owner(user.id)

    field_updates = body.get("fields", [])
    if not field_updates:
        raise HTTPException(status_code=400, detail="Geen velden opgegeven")

    updated = session.update_fields(page_type, field_updates)
    if updated is None:
        raise HTTPException(
            status_code=404,
            detail=f"Geen diff resultaat voor {page_type}",
        )

    return JSONResponse({"status": "ok", "fields": updated.get("fields", [])})


@brand_router.post("/generate/{session_id}")
async def generate_brand(
    session_id: str,
    body: dict,
    user: User = Depends(get_current_user),
) -> JSONResponse:
    """Genereer de volledige brand configuratie.

    Args:
        session_id: Sessie identifier.
        body: Dict met brand_name, brand_slug, colors, modules.
    """
    _validate_session_id(session_id)
    session = BrandSession(session_id)
    if not session.exists():
        raise HTTPException(status_code=404, detail="Sessie niet gevonden")
    session.verify_owner(user.id)

    try:
        session.generate_brand_package(body)
    except Exception as exc:
        logger.exception("Brand generatie failed voor %s", session_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    slug = body.get("brand_slug", "new-brand")
    yaml_path = session.output_dir / slug / "brand.yaml"
    brand_yaml = yaml_path.read_text(encoding="utf-8") if yaml_path.exists() else ""

    # Stationery bestanden
    pairs = session.get_pairs()
    stationery_files = [
        {"page_type": pt, "filename": f"{pt}.pdf"}
        for pt, status in pairs.items()
        if status["has_stationery"]
    ]

    return JSONResponse({
        "yaml": brand_yaml,
        "download_url": f"/api/brand/download/{session_id}/brand_package.zip",
        "stationery_files": stationery_files,
    })


@brand_router.get("/download/{session_id}/{filename}")
async def download_file(
    session_id: str,
    filename: str,
    user: User = Depends(get_current_user),
) -> FileResponse:
    """Download gegenereerde bestanden (YAML, ZIP).

    Args:
        session_id: Sessie identifier.
        filename: Bestandsnaam.
    """
    _validate_session_id(session_id)
    safe_name = _validate_filename(filename)
    session = BrandSession(session_id)
    session.verify_owner(user.id)

    # Zoek in output dir (direct of in brand subdir)
    file_path = session.output_dir / safe_name
    if not file_path.exists() and session.output_dir.exists():
        # Zoek in brand subdirectories
        for subdir in session.output_dir.iterdir():
            if subdir.is_dir():
                candidate = subdir / safe_name
                if candidate.exists():
                    file_path = candidate
                    break

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Bestand niet gevonden")

    media_type = "application/zip" if safe_name.endswith(".zip") else "application/octet-stream"
    if safe_name.endswith(".yaml") or safe_name.endswith(".yml"):
        media_type = "text/yaml"

    return FileResponse(file_path, media_type=media_type, filename=safe_name)


@brand_router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    user: User = Depends(get_current_user),
) -> JSONResponse:
    """Verwijder een sessie en al haar bestanden.

    Args:
        session_id: Sessie identifier.
    """
    _validate_session_id(session_id)
    session = BrandSession(session_id)
    if not session.exists():
        raise HTTPException(status_code=404, detail="Sessie niet gevonden")
    session.verify_owner(user.id)

    session.cleanup()
    return JSONResponse({"status": "deleted", "session_id": session_id})


# ============================================================
# Helpers
# ============================================================


def _field_to_dict(field: DetectedField) -> dict:
    """Converteer DetectedField naar JSON-serialiseerbare dict."""
    return asdict(field)


def _diff_result_to_dict(result: DiffResult) -> dict:
    """Converteer DiffResult naar JSON-serialiseerbare dict."""
    data = asdict(result)
    # Paths naar strings
    for key in ("diff_image_path", "reference_image_path", "stationery_image_path"):
        if data[key] is not None:
            data[key] = str(data[key])
    return data


def _generate_brand_yaml(
    config: dict,
    all_results: dict,
    stationery_files: list[dict],
) -> str:
    """Genereer brand.yaml content uit config en diff resultaten.

    Args:
        config: Brand configuratie (name, slug, colors, modules).
        all_results: Alle diff resultaten per page_type.
        stationery_files: Lijst van stationery bestanden.

    Returns:
        YAML string.
    """
    brand_name = config.get("brand_name", "New Brand")
    brand_slug = config.get("brand_slug", "new-brand")
    colors = config.get("colors", {})
    modules = config.get("modules", [])

    # Verzamel alle gedetecteerde kleuren en fonts
    all_colors: dict[str, int] = {}
    all_fonts: dict[str, set[float]] = {}

    for page_type, result_data in all_results.items():
        for color_info in result_data.get("colors", []):
            hex_val = color_info["hex"]
            all_colors[hex_val] = all_colors.get(hex_val, 0) + color_info["count"]
        for font_info in result_data.get("fonts", []):
            font_name = font_info["name"]
            if font_name not in all_fonts:
                all_fonts[font_name] = set()
            all_fonts[font_name].update(font_info.get("sizes", []))

    # Bepaal primaire/secundaire kleuren (meest frequent als niet opgegeven)
    sorted_colors = sorted(all_colors.items(), key=lambda x: x[1], reverse=True)
    if "primary" not in colors and sorted_colors:
        colors["primary"] = sorted_colors[0][0]
    if "secondary" not in colors and len(sorted_colors) > 1:
        colors["secondary"] = sorted_colors[1][0]

    # Stationery mapping
    stationery = {}
    for sf in stationery_files:
        stationery[sf["page_type"]] = {"source": f"stationery/{sf['filename']}"}

    # Pages met text_zones uit diff resultaten
    pages: dict[str, dict] = {}
    for page_type, result_data in all_results.items():
        page_config: dict[str, Any] = {
            "orientation": result_data.get("orientation", "portrait"),
        }
        # Voeg assigned velden toe als text_zones
        text_zones = []
        for fld in result_data.get("fields", []):
            if fld.get("role") and fld.get("role") != "ignore":
                text_zones.append({
                    "name": fld.get("name") or fld.get("role"),
                    "role": fld["role"],
                    "x_pt": fld["x_pt"],
                    "y_pt": fld["y_pt"],
                    "font": fld["font"],
                    "size": fld["font_size"],
                    "color": fld["color_hex"],
                })
        if text_zones:
            page_config["text_zones"] = text_zones
        pages[page_type] = page_config

    # Bouw YAML structuur
    brand_data: dict[str, Any] = {
        "brand": {
            "name": brand_name,
            "slug": brand_slug,
            "tenant": brand_slug.replace("-", "_"),
        },
        "colors": {
            "primary": colors.get("primary", "#000000"),
            "secondary": colors.get("secondary", "#666666"),
            "text": colors.get("text", "#000000"),
            "text_light": colors.get("text_light", "#FFFFFF"),
        },
        "fonts": {},
        "stationery": stationery,
    }

    # Fonts (meest gebruikte als heading/body)
    sorted_fonts = sorted(all_fonts.items(), key=lambda x: len(x[1]), reverse=True)
    if sorted_fonts:
        bold_fonts = [f for f, _ in sorted_fonts if "bold" in f.lower()]
        regular_fonts = [f for f, _ in sorted_fonts if "bold" not in f.lower()]
        brand_data["fonts"]["heading"] = bold_fonts[0] if bold_fonts else sorted_fonts[0][0]
        brand_data["fonts"]["heading_fallback"] = "LiberationSans-Bold"
        brand_data["fonts"]["body"] = regular_fonts[0] if regular_fonts else sorted_fonts[0][0]
        brand_data["fonts"]["body_fallback"] = "LiberationSans"

    if modules:
        brand_data["tenant_modules"] = modules

    if pages:
        brand_data["pages"] = pages

    return yaml.dump(brand_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
