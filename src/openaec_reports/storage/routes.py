"""API endpoints voor projecten en rapporten (CRUD + bestandsopslag)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from openaec_reports.auth.dependencies import get_current_user
from openaec_reports.auth.models import User
from openaec_reports.storage.models import Project, ReportDB, ReportMeta

logger = logging.getLogger(__name__)

# Module-level DB instance (wordt gezet bij app startup)
_report_db: ReportDB | None = None


def init_report_db(db: ReportDB) -> None:
    """Stel de module-level ReportDB instance in.

    Args:
        db: ReportDB instance.
    """
    global _report_db  # noqa: PLW0603
    _report_db = db


def get_report_db() -> ReportDB:
    """Haal de actieve ReportDB op.

    Returns:
        De ReportDB instance.

    Raises:
        RuntimeError: Als init_report_db() niet is aangeroepen.
    """
    if _report_db is None:
        raise RuntimeError(
            "ReportDB niet geinitialiseerd — roep init_report_db() aan"
        )
    return _report_db


# ============================================================
# Routers
# ============================================================

project_router = APIRouter(
    prefix="/api/projects",
    tags=["projects"],
    dependencies=[Depends(get_current_user)],
)

report_router = APIRouter(
    prefix="/api/reports",
    tags=["reports"],
    dependencies=[Depends(get_current_user)],
)


# ============================================================
# Project endpoints
# ============================================================


@project_router.get("")
async def list_projects(user: User = Depends(get_current_user)):
    """Lijst projecten van de huidige user.

    Returns:
        Dict met lijst van projecten (incl. report_count).
    """
    db = get_report_db()
    projects = db.list_projects(user.id)
    return {"projects": projects}


@project_router.post("")
async def create_project(
    request: Request,
    user: User = Depends(get_current_user),
):
    """Maak een nieuw project aan.

    Body:
        {"name": "...", "description": "..."}

    Returns:
        Het aangemaakte project.
    """
    body = await request.json()
    name = body.get("name", "").strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Projectnaam is verplicht",
        )

    db = get_report_db()
    project = Project(
        user_id=user.id,
        name=name,
        description=body.get("description", "").strip(),
    )
    db.create_project(project)

    result = project.to_dict()
    result["report_count"] = 0
    return JSONResponse(content=result, status_code=status.HTTP_201_CREATED)


@project_router.get("/{project_id}")
async def get_project(
    project_id: str,
    user: User = Depends(get_current_user),
):
    """Haal project detail op inclusief rapportenlijst.

    Args:
        project_id: Project UUID.

    Returns:
        Project metadata + lijst van rapporten.
    """
    db = get_report_db()
    project = db.get_project(project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project niet gevonden",
        )

    reports = db.list_reports(user.id, project_id=project_id)
    result = project.to_dict()
    result["reports"] = reports
    return result


@project_router.put("/{project_id}")
async def update_project(
    project_id: str,
    request: Request,
    user: User = Depends(get_current_user),
):
    """Update project naam/beschrijving.

    Args:
        project_id: Project UUID.

    Body:
        {"name": "...", "description": "..."}

    Returns:
        Geupdate project.
    """
    body = await request.json()
    fields: dict[str, str] = {}
    if "name" in body:
        name = body["name"].strip()
        if not name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Projectnaam mag niet leeg zijn",
            )
        fields["name"] = name
    if "description" in body:
        fields["description"] = body["description"].strip()

    db = get_report_db()
    project = db.update_project(project_id, user.id, **fields)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project niet gevonden",
        )
    return project.to_dict()


@project_router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    user: User = Depends(get_current_user),
):
    """Verwijder een project en alle bijbehorende rapporten.

    Args:
        project_id: Project UUID.

    Returns:
        Bevestigingsbericht.
    """
    db = get_report_db()
    deleted = db.delete_project(project_id, user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project niet gevonden",
        )
    return {"detail": "Project verwijderd"}


# ============================================================
# Report endpoints
# ============================================================


@report_router.get("")
async def list_reports(
    project_id: str | None = None,
    user: User = Depends(get_current_user),
):
    """Lijst rapporten van de huidige user.

    Query parameters:
        project_id: Optioneel filter op project.

    Returns:
        Dict met lijst van rapporten.
    """
    db = get_report_db()
    reports = db.list_reports(user.id, project_id=project_id)
    return {"reports": reports}


@report_router.post("")
async def save_report(
    request: Request,
    user: User = Depends(get_current_user),
):
    """Sla een rapport op (nieuw of update).

    Body:
        {
            "id": "...",          // Optioneel (voor update)
            "title": "...",
            "template": "...",
            "project_id": "...",  // Optioneel
            "content": {...}      // Volledige rapport JSON
        }

    Returns:
        Rapport metadata.
    """
    body = await request.json()
    title = body.get("title", "").strip()
    if not title:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Rapporttitel is verplicht",
        )

    content = body.get("content")
    if not content or not isinstance(content, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Rapport content is verplicht (JSON object)",
        )

    db = get_report_db()

    # Als er een ID is, check eigendom
    report_id = body.get("id", "")
    if report_id:
        existing = db.get_report_meta(report_id)
        if existing and existing.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Geen toegang tot dit rapport",
            )

    meta = ReportMeta(
        id=report_id if report_id else None,  # None → auto-generate
        user_id=user.id,
        project_id=body.get("project_id"),
        title=title,
        template=body.get("template", ""),
    )
    # Herstel auto-generated ID als niet meegegeven
    if not meta.id:
        from uuid import uuid4
        meta.id = uuid4().hex

    saved = db.save_report(meta, content)
    return JSONResponse(
        content=saved.to_dict(),
        status_code=status.HTTP_201_CREATED if not report_id else 200,
    )


@report_router.get("/{report_id}")
async def get_report(
    report_id: str,
    user: User = Depends(get_current_user),
):
    """Haal rapport op (metadata + JSON content).

    Args:
        report_id: Rapport UUID.

    Returns:
        Dict met metadata en content.
    """
    db = get_report_db()
    result = db.get_report(report_id, user.id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rapport niet gevonden",
        )

    meta, content = result
    return {
        **meta.to_dict(),
        "content": content,
    }


@report_router.put("/{report_id}")
async def update_report(
    report_id: str,
    request: Request,
    user: User = Depends(get_current_user),
):
    """Update een rapport (metadata + content).

    Args:
        report_id: Rapport UUID.

    Body:
        {"title": "...", "template": "...", "project_id": "...", "content": {...}}

    Returns:
        Geupdate rapport metadata.
    """
    body = await request.json()
    db = get_report_db()

    # Check eigendom
    existing = db.get_report_meta(report_id)
    if not existing or existing.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rapport niet gevonden",
        )

    # Update content als meegegeven
    content = body.get("content")
    if content and isinstance(content, dict):
        meta = ReportMeta(
            id=report_id,
            user_id=user.id,
            project_id=body.get("project_id", existing.project_id),
            title=body.get("title", existing.title).strip(),
            template=body.get("template", existing.template),
        )
        saved = db.save_report(meta, content)
        return saved.to_dict()

    # Alleen metadata update
    fields: dict[str, str | None] = {}
    if "title" in body:
        fields["title"] = body["title"].strip()
    if "template" in body:
        fields["template"] = body["template"]
    if "project_id" in body:
        fields["project_id"] = body["project_id"]

    updated = db.update_report_meta(report_id, user.id, **fields)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rapport niet gevonden",
        )
    return updated.to_dict()


@report_router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    user: User = Depends(get_current_user),
):
    """Verwijder een rapport.

    Args:
        report_id: Rapport UUID.

    Returns:
        Bevestigingsbericht.
    """
    db = get_report_db()
    deleted = db.delete_report(report_id, user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rapport niet gevonden",
        )
    return {"detail": "Rapport verwijderd"}


@report_router.put("/{report_id}/move")
async def move_report(
    report_id: str,
    request: Request,
    user: User = Depends(get_current_user),
):
    """Verplaats een rapport naar een ander project.

    Args:
        report_id: Rapport UUID.

    Body:
        {"project_id": "..." | null}

    Returns:
        Geupdate rapport metadata.
    """
    body = await request.json()
    project_id = body.get("project_id")  # None = los rapport

    # Als project_id meegegeven, check eigendom
    if project_id:
        db = get_report_db()
        project = db.get_project(project_id)
        if not project or project.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doelproject niet gevonden",
            )

    db = get_report_db()
    updated = db.move_report_to_project(report_id, user.id, project_id)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rapport niet gevonden",
        )
    return updated.to_dict()
