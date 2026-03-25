"""Nextcloud WebDAV integration for cloud storage of generated reports.

Provides REST endpoints to list Nextcloud project directories and save
generated PDF reports directly to the project's cloud folder.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import date
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from urllib.parse import quote, unquote
from xml.etree import ElementTree as ET

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from openaec_reports.auth.dependencies import get_current_user
from openaec_reports.auth.models import User

logger = logging.getLogger(__name__)

# Tool-specific subdirectory inside 99_overige_documenten/
TOOL_SUBDIR = "reports"

# Nextcloud configuration from environment
NEXTCLOUD_URL = os.getenv("NEXTCLOUD_URL", "")
NEXTCLOUD_USER = os.getenv("NEXTCLOUD_SERVICE_USER", "")
NEXTCLOUD_PASS = os.getenv("NEXTCLOUD_SERVICE_PASS", "")

DAV_NAMESPACE = {"d": "DAV:"}


def is_cloud_configured() -> bool:
    """Check if Nextcloud environment variables are set."""
    return bool(NEXTCLOUD_URL and NEXTCLOUD_USER and NEXTCLOUD_PASS)


def _dav_base() -> str:
    """WebDAV base URL for the service account's Projects folder."""
    base = NEXTCLOUD_URL.rstrip("/")
    return f"{base}/remote.php/dav/files/{NEXTCLOUD_USER}/Projects"


def _tool_path(project: str) -> str:
    """Full WebDAV URL for a project's tool subdirectory."""
    return f"{_dav_base()}/{quote(project)}/99_overige_documenten/{TOOL_SUBDIR}"


def _file_url(project: str, filename: str) -> str:
    """Full WebDAV URL for a specific file."""
    return f"{_tool_path(project)}/{quote(filename)}"


def _get_client() -> httpx.Client:
    """Create an httpx client with Nextcloud Basic auth."""
    return httpx.Client(
        auth=(NEXTCLOUD_USER, NEXTCLOUD_PASS),
        timeout=30.0,
    )


def _parse_collections(xml_text: str) -> list[str]:
    """Parse PROPFIND XML to extract collection (directory) names."""
    names: list[str] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return names

    for response in root.findall("d:response", DAV_NAMESPACE):
        href_el = response.find("d:href", DAV_NAMESPACE)
        if href_el is None or href_el.text is None:
            continue

        # Check if it's a collection
        restype = response.find(".//d:resourcetype/d:collection", DAV_NAMESPACE)
        if restype is None:
            continue

        href = unquote(href_el.text.rstrip("/"))
        # Skip the base directory itself (ends with /Projects)
        if href.endswith("/Projects"):
            continue

        name = href.rsplit("/", 1)[-1]
        if name:
            names.append(name)

    return names


def _parse_files(xml_text: str, extension: str = ".pdf") -> list[dict[str, Any]]:
    """Parse PROPFIND XML to extract file entries."""
    files: list[dict[str, Any]] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return files

    for response in root.findall("d:response", DAV_NAMESPACE):
        href_el = response.find("d:href", DAV_NAMESPACE)
        if href_el is None or href_el.text is None:
            continue

        # Skip collections
        restype = response.find(".//d:resourcetype/d:collection", DAV_NAMESPACE)
        if restype is not None:
            continue

        name = unquote(href_el.text.rstrip("/")).rsplit("/", 1)[-1]
        if not name.endswith(extension):
            continue

        size_el = response.find(".//d:getcontentlength", DAV_NAMESPACE)
        modified_el = response.find(".//d:getlastmodified", DAV_NAMESPACE)

        files.append({
            "name": name,
            "size": int(size_el.text) if size_el is not None and size_el.text else 0,
            "last_modified": modified_el.text if modified_el is not None else "",
        })

    return files


def _ensure_directory(client: httpx.Client, url: str) -> None:
    """Ensure a WebDAV directory exists, creating it if needed."""
    res = client.request("PROPFIND", url, headers={"Depth": "0"})
    if res.status_code < 400:
        return

    res = client.request("MKCOL", url)
    if res.status_code not in (201, 405):  # 405 = already exists
        logger.warning("MKCOL %s failed: %s", url, res.status_code)


def _slugify(text: str) -> str:
    """Convert text to a safe filename slug."""
    text = re.sub(r"[^\w\s-]", "", text.strip().lower())
    return re.sub(r"[\s]+", "_", text)


# --- FastAPI Router ---

cloud_router = APIRouter(
    prefix="/api/cloud",
    tags=["cloud"],
    dependencies=[Depends(get_current_user)],
)


@cloud_router.get("/projects")
async def list_projects() -> list[dict[str, str]]:
    """List available Nextcloud project directories."""
    with _get_client() as client:
        res = client.request(
            "PROPFIND",
            f"{_dav_base()}/",
            headers={"Depth": "1"},
        )

    if res.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"Nextcloud returned {res.status_code}",
        )

    projects = _parse_collections(res.text)
    return [{"name": p} for p in projects]


@cloud_router.get("/projects/{project}/files")
async def list_files(project: str) -> list[dict[str, Any]]:
    """List PDF files in a project's reports directory."""
    with _get_client() as client:
        res = client.request(
            "PROPFIND",
            f"{_tool_path(project)}/",
            headers={"Depth": "1"},
        )

    # 404 = directory doesn't exist yet
    if res.status_code == 404:
        return []

    if res.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"Nextcloud returned {res.status_code}",
        )

    return _parse_files(res.text)


@cloud_router.get("/projects/{project}/files/{filename}")
async def get_file(project: str, filename: str) -> Response:
    """Download a specific file from Nextcloud."""
    with _get_client() as client:
        res = client.get(_file_url(project, filename))

    if res.status_code == 404:
        raise HTTPException(status_code=404, detail=f"Bestand '{filename}' niet gevonden")

    if res.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"Nextcloud returned {res.status_code}",
        )

    return Response(
        content=res.content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@cloud_router.post("/projects/{project}/save")
async def save_report_to_cloud(
    project: str,
    request: Request,
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Generate a PDF report and save it directly to Nextcloud.

    Accepts the same JSON body as /api/generate.
    """
    # Import here to avoid circular imports
    from openaec_reports.api import _generate_and_respond, _resolve_brand_with_tenant_check
    from openaec_reports.core.engine import Report

    data = await request.json()

    if not data.get("project"):
        raise HTTPException(status_code=422, detail="Veld 'project' is verplicht")
    if not data.get("template"):
        raise HTTPException(status_code=422, detail="Veld 'template' is verplicht")

    brand = _resolve_brand_with_tenant_check(data, user)
    report = Report.from_dict(data, brand=brand)

    # Generate PDF to temp file
    output_path: Path | None = None
    try:
        with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            output_path = Path(tmp.name)

        report.build(output_path)
        pdf_bytes = output_path.read_bytes()
    finally:
        if output_path and output_path.exists():
            output_path.unlink(missing_ok=True)

    # Build filename: slugified project name + title + date
    title_slug = _slugify(data.get("project", "rapport"))
    date_str = date.today().isoformat()
    filename = f"{title_slug}_{date_str}.pdf"

    # Upload to Nextcloud
    with _get_client() as client:
        overige_url = f"{_dav_base()}/{quote(project)}/99_overige_documenten/"
        _ensure_directory(client, overige_url)

        tool_url = f"{_tool_path(project)}/"
        _ensure_directory(client, tool_url)

        res = client.put(
            _file_url(project, filename),
            content=pdf_bytes,
            headers={"Content-Type": "application/pdf"},
        )

    if res.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"Upload naar Nextcloud mislukt: {res.status_code}",
        )

    return {
        "status": "saved",
        "filename": filename,
        "project": project,
    }
