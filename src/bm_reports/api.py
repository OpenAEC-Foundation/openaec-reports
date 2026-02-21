"""HTTP API — FastAPI server voor PDF rapport generatie."""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import uuid
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask

from bm_reports import __version__
from bm_reports.core.brand import BrandLoader
from bm_reports.core.engine import Report
from bm_reports.core.renderer_v2 import ReportGeneratorV2
from bm_reports.core.template_loader import TemplateLoader
from bm_reports.core.tenant import TenantConfig

logger = logging.getLogger(__name__)


def _find_schema_path() -> Path | None:
    """Zoek report.schema.json op meerdere locaties."""
    candidates = [
        # In package (na pip install via force-include)
        Path(__file__).parent / "schemas" / "report.schema.json",
        # In source tree (development)
        Path(__file__).parent.parent.parent / "schemas" / "report.schema.json",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


SCHEMA_PATH = _find_schema_path()

# Tenant configuratie — leest BM_TENANT_DIR environment variable
tenant_config = TenantConfig()

STATIONERY_DIR = tenant_config.stationery_dir or Path(os.environ.get(
    "BM_STATIONERY_DIR",
    str(Path(__file__).parent / "assets" / "stationery" / "3bm_cooperatie"),
))
UPLOAD_DIR = Path(os.environ.get("BM_UPLOAD_DIR", str(Path(__file__).parent.parent.parent / "uploads")))
ASSETS_DIR = Path(__file__).parent / "assets"

app = FastAPI(
    title="3BM Report Generator API",
    description="HTTP API voor het genereren van professionele engineering rapporten.",
    version=__version__,
)

# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "https://report.3bm.co.nl",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Helpers
# ============================================================

def _safe_filename(*parts: str, extension: str = ".pdf") -> str:
    """Maak een veilige bestandsnaam van project info.

    Args:
        *parts: Onderdelen van de bestandsnaam (project_number, project, etc.).
        extension: Bestandsextensie.

    Returns:
        Gesanitizede bestandsnaam.
    """
    combined = "_".join(p for p in parts if p)
    safe = re.sub(r"[^\w\s-]", "", combined).strip()
    safe = re.sub(r"[-\s]+", "_", safe)
    return (safe or "rapport") + extension


# ============================================================
# Exception handlers
# ============================================================

@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request: Request, exc: FileNotFoundError):
    """Ontbrekende template of brand → 404."""
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc), "type": "FileNotFoundError"},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Ongeldige data → 422."""
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc), "type": "ValueError"},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Onverwachte fout → 500 met type info."""
    logger.exception("Onverwachte fout bij %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Interne serverfout", "type": type(exc).__name__},
    )


# ============================================================
# Endpoints
# ============================================================

@app.get("/api/health")
async def health():
    """Health check endpoint.

    Returns:
        Status en versie-informatie.
    """
    return {"status": "ok", "version": __version__}


@app.get("/api/templates")
async def list_templates():
    """Lijst beschikbare rapport templates.

    Returns:
        Dict met lijst van templates (naam + type).
    """
    loader = TemplateLoader(templates_dirs=tenant_config.templates_dirs)
    return {"templates": loader.list_templates()}


@app.get("/api/templates/{name}/scaffold")
async def get_template_scaffold(name: str):
    """Retourneer een leeg JSON scaffold voor een template.

    De frontend kan dit laden als startpunt voor een nieuw rapport.

    Args:
        name: Template naam.

    Returns:
        Dict conform report.schema.json met defaults uit het template.
    """
    loader = TemplateLoader(templates_dirs=tenant_config.templates_dirs)
    scaffold = loader.to_scaffold(name)
    return scaffold


@app.get("/api/brands")
async def list_brands():
    """Lijst beschikbare brand configuraties.

    Returns:
        Dict met lijst van brands (naam + slug).
    """
    loader = BrandLoader(tenant_config=tenant_config)
    return {"brands": loader.list_brands()}


@app.post("/api/validate")
async def validate_report(request: Request):
    """Valideer JSON data tegen report.schema.json.

    Body:
        JSON data conform report.schema.json.

    Returns:
        {"valid": true} of {"valid": false, "errors": [...]}.
    """
    import jsonschema

    data = await request.json()

    if SCHEMA_PATH is None:
        raise HTTPException(
            status_code=500,
            detail="Schema bestand niet gevonden — validatie niet beschikbaar",
        )

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft7Validator(schema)
    errors = [
        {
            "path": "/".join(str(p) for p in e.absolute_path),
            "message": e.message,
        }
        for e in validator.iter_errors(data)
    ]
    return {"valid": len(errors) == 0, "errors": errors}


@app.post("/api/generate")
async def generate_report(request: Request):
    """Genereer PDF rapport uit JSON data.

    Body:
        JSON data conform report.schema.json.

    Returns:
        PDF bestand als binary response (application/pdf).
    """
    data = await request.json()

    if not data.get("project"):
        raise HTTPException(status_code=422, detail="Veld 'project' is verplicht")
    if not data.get("template"):
        raise HTTPException(status_code=422, detail="Veld 'template' is verplicht")

    output_path: Path | None = None
    try:
        brand = data.get("brand", "3bm_cooperatie")
        report = Report.from_dict(data, brand=brand)

        with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            output_path = Path(tmp.name)

        report.build(output_path)

        filename = _safe_filename(
            data.get("project_number", ""),
            data.get("project", ""),
        )

        return FileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename=filename,
            background=BackgroundTask(lambda: output_path.unlink(missing_ok=True)),
        )
    except HTTPException:
        if output_path and output_path.exists():
            output_path.unlink(missing_ok=True)
        raise
    except Exception:
        if output_path and output_path.exists():
            output_path.unlink(missing_ok=True)
        raise


# ============================================================
# V2 Endpoints — ReportGeneratorV2
# ============================================================


@app.post("/api/generate/v2")
async def generate_report_v2(request: Request):
    """Genereer PDF rapport via renderer_v2 (pixel-perfect huisstijl).

    Body:
        JSON data met project info, sections, appendices.

    Returns:
        PDF bestand als binary response.
    """
    data = await request.json()

    if not data.get("project"):
        raise HTTPException(status_code=422, detail="Veld 'project' is verplicht")

    output_path: Path | None = None
    try:
        brand = data.get("brand", "3bm_cooperatie")
        stationery_dir = STATIONERY_DIR

        # Check tenant stationery eerst, dan brand-specifiek in package
        if tenant_config.stationery_dir and tenant_config.stationery_dir.exists():
            stationery_dir = tenant_config.stationery_dir
        else:
            brand_stationery = ASSETS_DIR / "stationery" / brand
            if brand_stationery.exists():
                stationery_dir = brand_stationery

        generator = ReportGeneratorV2(brand=brand)

        with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            output_path = Path(tmp.name)

        generator.generate(data, stationery_dir, output_path)

        filename = _safe_filename(
            data.get("project_number", ""),
            data.get("project", ""),
        )

        return FileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename=filename,
            background=BackgroundTask(lambda: output_path.unlink(missing_ok=True)),
        )
    except HTTPException:
        if output_path and output_path.exists():
            output_path.unlink(missing_ok=True)
        raise
    except Exception:
        if output_path and output_path.exists():
            output_path.unlink(missing_ok=True)
        raise


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload een afbeelding voor gebruik in rapporten.

    Returns:
        Dict met pad dat als `src` in JSON content gebruikt kan worden.
    """
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Genereer unieke bestandsnaam
    ext = Path(file.filename or "upload.png").suffix or ".png"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / unique_name

    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {
        "path": str(dest),
        "filename": unique_name,
        "size": dest.stat().st_size,
    }


@app.get("/api/stationery")
async def list_stationery():
    """Retourneer beschikbare brands en hun stationery status.

    Controleert zowel tenant stationery als package stationery.

    Returns:
        Dict met brands en per brand de beschikbare stationery bestanden.
    """
    required = ["colofon.pdf", "standaard.pdf", "bijlagen.pdf", "achterblad.pdf"]
    brands = {}

    def _scan_stationery_dir(sdir: Path, label: str) -> None:
        if not sdir.exists() or not sdir.is_dir():
            return
        files = {f.name: True for f in sdir.iterdir() if f.is_file()}
        if files:
            brands[label] = {
                "complete": all(r in files for r in required),
                "files": list(files.keys()),
                "missing": [r for r in required if r not in files],
            }

    # Tenant stationery
    tenant_stat = tenant_config.stationery_dir
    if tenant_stat and tenant_stat.exists():
        _scan_stationery_dir(tenant_stat, tenant_stat.name if tenant_stat.name != "stationery" else "tenant")

    # Package stationery (als aanvulling)
    stationery_base = ASSETS_DIR / "stationery"
    if stationery_base.exists():
        for brand_dir in sorted(stationery_base.iterdir()):
            if not brand_dir.is_dir() or brand_dir.name in brands:
                continue
            _scan_stationery_dir(brand_dir, brand_dir.name)

    return {"brands": brands}


# ============================================================
# Static frontend (moet ONDERAAN staan, na alle API routes)
# ============================================================

_static_dir = Path(__file__).parent.parent.parent / "static"
if _static_dir.exists():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")


# ============================================================
# Entrypoint
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("bm_reports.api:app", host="0.0.0.0", port=8000, reload=True)
