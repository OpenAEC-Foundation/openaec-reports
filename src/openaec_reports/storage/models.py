"""Project en rapport metadata — SQLite CRUD + bestandssysteem opslag."""

from __future__ import annotations

import json
import logging
import re
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Maximale rapport JSON grootte (10 MB)
MAX_REPORT_SIZE_BYTES = 10 * 1024 * 1024

DEFAULT_REPORTS_DIR = "data/reports"


def _now_iso() -> str:
    """Retourneer huidige UTC tijd als ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Project:
    """Project container voor rapporten."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    user_id: str = ""
    name: str = ""
    description: str = ""
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        """Publieke representatie.

        Returns:
            Dict met project gegevens.
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class ReportMeta:
    """Rapport metadata (opgeslagen in SQLite)."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    user_id: str = ""
    project_id: str | None = None
    title: str = ""
    template: str = ""
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        """Publieke representatie.

        Returns:
            Dict met rapport metadata.
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "title": self.title,
            "template": self.template,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class ReportDB:
    """SQLite wrapper voor project en rapport CRUD operaties.

    Gebruikt dezelfde database als UserDB (auth.db) zodat foreign keys
    werken. Rapport JSON wordt opgeslagen op het bestandssysteem.

    Args:
        db_path: Pad naar de SQLite database.
        reports_dir: Pad voor rapport JSON bestanden.
    """

    def __init__(
        self,
        db_path: str | Path | None = None,
        reports_dir: str | Path | None = None,
    ) -> None:
        import os

        self.db_path = Path(
            db_path
            or os.environ.get("OPENAEC_AUTH_DB", "data/auth.db")
        )
        self.reports_dir = Path(
            reports_dir
            or os.environ.get("OPENAEC_REPORTS_DIR", DEFAULT_REPORTS_DIR)
        )
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Maak een nieuwe connectie met WAL mode.

        Returns:
            SQLite connectie.
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        """Maak de projects en reports tabellen aan."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    project_id TEXT,
                    title TEXT NOT NULL,
                    template TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            # Indexes voor snelle lookups
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_projects_user "
                "ON projects(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_reports_user "
                "ON reports(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_reports_project "
                "ON reports(project_id)"
            )
            conn.commit()

    # ================================================================
    # Projecten
    # ================================================================

    def create_project(self, project: Project) -> Project:
        """Maak een nieuw project aan.

        Args:
            project: Project object.

        Returns:
            Het aangemaakte Project.
        """
        with self._get_connection() as conn:
            conn.execute(
                """INSERT INTO projects
                   (id, user_id, name, description, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    project.id,
                    project.user_id,
                    project.name,
                    project.description,
                    project.created_at,
                    project.updated_at,
                ),
            )
            conn.commit()
        logger.info("Project aangemaakt: %s (%s)", project.name, project.id)
        return project

    def get_project(self, project_id: str) -> Project | None:
        """Haal een project op.

        Args:
            project_id: Project UUID.

        Returns:
            Project of None als niet gevonden.
        """
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM projects WHERE id = ?",
                (project_id,),
            ).fetchone()
            return self._row_to_project(row) if row else None

    def list_projects(self, user_id: str) -> list[dict]:
        """Lijst alle projecten van een user, inclusief rapport-telling.

        Args:
            user_id: User UUID.

        Returns:
            Lijst van project dicts met report_count.
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                """SELECT p.*, COUNT(r.id) as report_count
                   FROM projects p
                   LEFT JOIN reports r ON r.project_id = p.id
                   WHERE p.user_id = ?
                   GROUP BY p.id
                   ORDER BY p.updated_at DESC""",
                (user_id,),
            ).fetchall()
            result = []
            for row in rows:
                proj = self._row_to_project(row)
                d = proj.to_dict()
                d["report_count"] = row["report_count"]
                result.append(d)
            return result

    def update_project(
        self,
        project_id: str,
        user_id: str,
        **fields: str,
    ) -> Project | None:
        """Update een project.

        Args:
            project_id: Project UUID.
            user_id: User UUID (eigendom check).
            **fields: Velden om te updaten (name, description).

        Returns:
            Geupdate Project of None als niet gevonden.
        """
        allowed = {"name", "description"}
        invalid = set(fields.keys()) - allowed
        if invalid:
            raise ValueError(f"Niet-toegestane velden: {invalid}")
        if not fields:
            return self.get_project(project_id)

        set_clauses = [f"{k} = ?" for k in fields]
        set_clauses.append("updated_at = ?")
        values = list(fields.values()) + [_now_iso(), project_id, user_id]

        sql = (
            f"UPDATE projects SET {', '.join(set_clauses)} "
            f"WHERE id = ? AND user_id = ?"
        )
        with self._get_connection() as conn:
            cursor = conn.execute(sql, values)
            conn.commit()
            if cursor.rowcount == 0:
                return None
        return self.get_project(project_id)

    def delete_project(self, project_id: str, user_id: str) -> bool:
        """Verwijder een project en alle bijbehorende rapporten.

        Args:
            project_id: Project UUID.
            user_id: User UUID (eigendom check).

        Returns:
            True als verwijderd.
        """
        # Verwijder eerst alle rapporten in het project
        reports = self.list_reports(user_id, project_id=project_id)
        for r in reports:
            self.delete_report(r["id"], user_id)

        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM projects WHERE id = ? AND user_id = ?",
                (project_id, user_id),
            )
            conn.commit()
            deleted = cursor.rowcount > 0
        if deleted:
            logger.info("Project %s verwijderd", project_id)
        return deleted

    # ================================================================
    # Rapporten (metadata)
    # ================================================================

    def save_report(
        self,
        meta: ReportMeta,
        content: dict,
    ) -> ReportMeta:
        """Sla een rapport op (metadata in DB, JSON op disk).

        Args:
            meta: Rapport metadata.
            content: Volledige rapport JSON data.

        Returns:
            De opgeslagen ReportMeta.

        Raises:
            ValueError: Als de JSON te groot is.
        """
        json_bytes = json.dumps(content, ensure_ascii=False).encode("utf-8")
        if len(json_bytes) > MAX_REPORT_SIZE_BYTES:
            raise ValueError(
                f"Rapport JSON is te groot "
                f"({len(json_bytes)} bytes, max {MAX_REPORT_SIZE_BYTES})"
            )

        # Check of rapport al bestaat (update vs insert)
        existing = self.get_report_meta(meta.id)
        now = _now_iso()

        with self._get_connection() as conn:
            if existing:
                conn.execute(
                    """UPDATE reports SET
                       title = ?, template = ?, project_id = ?,
                       updated_at = ?
                       WHERE id = ? AND user_id = ?""",
                    (
                        meta.title,
                        meta.template,
                        meta.project_id,
                        now,
                        meta.id,
                        meta.user_id,
                    ),
                )
                meta.updated_at = now
            else:
                meta.created_at = now
                meta.updated_at = now
                conn.execute(
                    """INSERT INTO reports
                       (id, user_id, project_id, title, template,
                        created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        meta.id,
                        meta.user_id,
                        meta.project_id,
                        meta.title,
                        meta.template,
                        meta.created_at,
                        meta.updated_at,
                    ),
                )
            conn.commit()

        # Schrijf JSON naar disk
        self._write_report_json(meta.user_id, meta.id, json_bytes)

        logger.info("Rapport opgeslagen: %s (%s)", meta.title, meta.id)
        return meta

    def get_report_meta(self, report_id: str) -> ReportMeta | None:
        """Haal rapport metadata op.

        Args:
            report_id: Rapport UUID.

        Returns:
            ReportMeta of None.
        """
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM reports WHERE id = ?",
                (report_id,),
            ).fetchone()
            return self._row_to_report(row) if row else None

    def get_report(
        self,
        report_id: str,
        user_id: str,
    ) -> tuple[ReportMeta, dict] | None:
        """Haal rapport op (metadata + JSON content).

        Args:
            report_id: Rapport UUID.
            user_id: User UUID (eigendom check).

        Returns:
            Tuple van (ReportMeta, content dict) of None.
        """
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM reports WHERE id = ? AND user_id = ?",
                (report_id, user_id),
            ).fetchone()
            if not row:
                return None

        meta = self._row_to_report(row)
        content = self._read_report_json(meta.user_id, meta.id)
        if content is None:
            return None
        return meta, content

    def list_reports(
        self,
        user_id: str,
        project_id: str | None = None,
    ) -> list[dict]:
        """Lijst rapporten van een user.

        Args:
            user_id: User UUID.
            project_id: Optioneel project filter.

        Returns:
            Lijst van rapport metadata dicts.
        """
        with self._get_connection() as conn:
            if project_id is not None:
                rows = conn.execute(
                    """SELECT * FROM reports
                       WHERE user_id = ? AND project_id = ?
                       ORDER BY updated_at DESC""",
                    (user_id, project_id),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM reports
                       WHERE user_id = ?
                       ORDER BY updated_at DESC""",
                    (user_id,),
                ).fetchall()
            return [self._row_to_report(row).to_dict() for row in rows]

    def update_report_meta(
        self,
        report_id: str,
        user_id: str,
        **fields: str | None,
    ) -> ReportMeta | None:
        """Update rapport metadata.

        Args:
            report_id: Rapport UUID.
            user_id: User UUID (eigendom check).
            **fields: Velden om te updaten (title, template, project_id).

        Returns:
            Geupdate ReportMeta of None.
        """
        allowed = {"title", "template", "project_id"}
        invalid = set(fields.keys()) - allowed
        if invalid:
            raise ValueError(f"Niet-toegestane velden: {invalid}")
        if not fields:
            return self.get_report_meta(report_id)

        set_clauses = [f"{k} = ?" for k in fields]
        set_clauses.append("updated_at = ?")
        values = list(fields.values()) + [_now_iso(), report_id, user_id]

        sql = (
            f"UPDATE reports SET {', '.join(set_clauses)} "
            f"WHERE id = ? AND user_id = ?"
        )
        with self._get_connection() as conn:
            cursor = conn.execute(sql, values)
            conn.commit()
            if cursor.rowcount == 0:
                return None
        return self.get_report_meta(report_id)

    def delete_report(self, report_id: str, user_id: str) -> bool:
        """Verwijder een rapport (DB + bestand).

        Args:
            report_id: Rapport UUID.
            user_id: User UUID (eigendom check).

        Returns:
            True als verwijderd.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM reports WHERE id = ? AND user_id = ?",
                (report_id, user_id),
            )
            conn.commit()
            deleted = cursor.rowcount > 0

        if deleted:
            self._delete_report_json(user_id, report_id)
            logger.info("Rapport %s verwijderd", report_id)
        return deleted

    def move_report_to_project(
        self,
        report_id: str,
        user_id: str,
        project_id: str | None,
    ) -> ReportMeta | None:
        """Verplaats een rapport naar een ander project.

        Args:
            report_id: Rapport UUID.
            user_id: User UUID (eigendom check).
            project_id: Doel project UUID (None = los rapport).

        Returns:
            Geupdate ReportMeta of None.
        """
        return self.update_report_meta(
            report_id, user_id, project_id=project_id
        )

    def count_reports(self, project_id: str) -> int:
        """Tel het aantal rapporten in een project.

        Args:
            project_id: Project UUID.

        Returns:
            Aantal rapporten.
        """
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM reports WHERE project_id = ?",
                (project_id,),
            ).fetchone()
            return row["cnt"] if row else 0

    # ================================================================
    # Bestandssysteem helpers
    # ================================================================

    _SAFE_ID = re.compile(r"^[a-zA-Z0-9_-]+$")

    def _report_path(self, user_id: str, report_id: str) -> Path:
        """Pad naar rapport JSON bestand.

        Valideert dat IDs geen path traversal componenten bevatten
        en dat het resulterende pad binnen reports_dir blijft.

        Args:
            user_id: User identifier.
            report_id: Rapport identifier.

        Returns:
            Path naar het JSON bestand.

        Raises:
            ValueError: Bij ongeldig ID formaat of path traversal.
        """
        if not self._SAFE_ID.match(user_id) or not self._SAFE_ID.match(report_id):
            raise ValueError("Ongeldig ID formaat")
        path = self.reports_dir / user_id / f"{report_id}.json"
        # Verifieer dat resolved pad binnen reports_dir blijft
        if not path.resolve().is_relative_to(self.reports_dir.resolve()):
            raise ValueError("Pad buiten reports directory")
        return path

    def _write_report_json(
        self,
        user_id: str,
        report_id: str,
        json_bytes: bytes,
    ) -> None:
        """Schrijf rapport JSON naar disk.

        Args:
            user_id: User UUID.
            report_id: Rapport UUID.
            json_bytes: JSON data als bytes.
        """
        path = self._report_path(user_id, report_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(json_bytes)

    def _read_report_json(
        self,
        user_id: str,
        report_id: str,
    ) -> dict | None:
        """Lees rapport JSON van disk.

        Args:
            user_id: User UUID.
            report_id: Rapport UUID.

        Returns:
            Parsed JSON dict of None als bestand niet bestaat.
        """
        path = self._report_path(user_id, report_id)
        if not path.exists():
            logger.warning("Rapport JSON niet gevonden: %s", path)
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def _delete_report_json(self, user_id: str, report_id: str) -> None:
        """Verwijder rapport JSON van disk.

        Args:
            user_id: User UUID.
            report_id: Rapport UUID.
        """
        path = self._report_path(user_id, report_id)
        if path.exists():
            path.unlink()
            # Verwijder lege user directory
            if path.parent.exists() and not any(path.parent.iterdir()):
                path.parent.rmdir()

    # ================================================================
    # Row conversie helpers
    # ================================================================

    @staticmethod
    def _row_to_project(row: sqlite3.Row) -> Project:
        """Converteer database row naar Project.

        Args:
            row: SQLite Row.

        Returns:
            Project instance.
        """
        return Project(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            description=row["description"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_report(row: sqlite3.Row) -> ReportMeta:
        """Converteer database row naar ReportMeta.

        Args:
            row: SQLite Row.

        Returns:
            ReportMeta instance.
        """
        return ReportMeta(
            id=row["id"],
            user_id=row["user_id"],
            project_id=row["project_id"],
            title=row["title"],
            template=row["template"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
