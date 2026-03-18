"""Tests voor rapport opslag en projecten CRUD."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from openaec_reports.api import app
from openaec_reports.storage.models import Project, ReportDB, ReportMeta

# ============================================================
# Unit tests — ReportDB
# ============================================================


@pytest.fixture()
def report_db(tmp_path):
    """Maak een verse ReportDB met tijdelijke database en directory."""
    db_path = tmp_path / "test.db"
    reports_dir = tmp_path / "reports"
    return ReportDB(db_path=db_path, reports_dir=reports_dir)


class TestReportDBProjects:
    """Tests voor project CRUD in ReportDB."""

    def test_create_and_get_project(self, report_db):
        """Maak een project aan en haal het op."""
        project = Project(user_id="user1", name="Test Project")
        report_db.create_project(project)

        result = report_db.get_project(project.id)
        assert result is not None
        assert result.name == "Test Project"
        assert result.user_id == "user1"

    def test_list_projects(self, report_db):
        """Lijst projecten per user."""
        report_db.create_project(
            Project(user_id="user1", name="Project A")
        )
        report_db.create_project(
            Project(user_id="user1", name="Project B")
        )
        report_db.create_project(
            Project(user_id="user2", name="Other user")
        )

        projects = report_db.list_projects("user1")
        assert len(projects) == 2
        names = {p["name"] for p in projects}
        assert names == {"Project A", "Project B"}

    def test_list_projects_with_report_count(self, report_db):
        """Lijst projecten bevat report_count."""
        project = Project(user_id="user1", name="Test")
        report_db.create_project(project)

        # Voeg 2 rapporten toe
        for i in range(2):
            meta = ReportMeta(
                user_id="user1",
                project_id=project.id,
                title=f"Report {i}",
            )
            report_db.save_report(meta, {"test": True})

        projects = report_db.list_projects("user1")
        assert projects[0]["report_count"] == 2

    def test_update_project(self, report_db):
        """Update project naam."""
        project = Project(user_id="user1", name="Oud")
        report_db.create_project(project)

        updated = report_db.update_project(
            project.id, "user1", name="Nieuw"
        )
        assert updated is not None
        assert updated.name == "Nieuw"

    def test_update_project_wrong_user(self, report_db):
        """Kan project van andere user niet updaten."""
        project = Project(user_id="user1", name="Test")
        report_db.create_project(project)

        result = report_db.update_project(
            project.id, "user2", name="Hack"
        )
        assert result is None

    def test_delete_project_cascades(self, report_db):
        """Verwijder project verwijdert ook rapporten."""
        project = Project(user_id="user1", name="Test")
        report_db.create_project(project)

        meta = ReportMeta(
            user_id="user1",
            project_id=project.id,
            title="Report in project",
        )
        report_db.save_report(meta, {"data": "test"})

        deleted = report_db.delete_project(project.id, "user1")
        assert deleted is True
        assert report_db.get_project(project.id) is None
        assert report_db.get_report_meta(meta.id) is None


class TestReportDBReports:
    """Tests voor rapport CRUD in ReportDB."""

    def test_save_and_get_report(self, report_db):
        """Sla een rapport op en haal het op (metadata + content)."""
        content = {"template": "structural", "project": "Test"}
        meta = ReportMeta(
            user_id="user1",
            title="Constructief advies",
            template="structural",
        )
        report_db.save_report(meta, content)

        result = report_db.get_report(meta.id, "user1")
        assert result is not None
        loaded_meta, loaded_content = result
        assert loaded_meta.title == "Constructief advies"
        assert loaded_content["template"] == "structural"

    def test_save_report_update(self, report_db):
        """Update een bestaand rapport."""
        content_v1 = {"version": 1}
        meta = ReportMeta(user_id="user1", title="V1")
        report_db.save_report(meta, content_v1)

        content_v2 = {"version": 2}
        meta.title = "V2"
        report_db.save_report(meta, content_v2)

        result = report_db.get_report(meta.id, "user1")
        assert result is not None
        _, loaded = result
        assert loaded["version"] == 2

    def test_list_reports(self, report_db):
        """Lijst rapporten per user."""
        for i in range(3):
            meta = ReportMeta(
                user_id="user1",
                title=f"Report {i}",
            )
            report_db.save_report(meta, {"i": i})

        # Ander user
        meta = ReportMeta(user_id="user2", title="Other")
        report_db.save_report(meta, {"other": True})

        reports = report_db.list_reports("user1")
        assert len(reports) == 3

    def test_list_reports_by_project(self, report_db):
        """Filter rapporten op project."""
        project = Project(user_id="user1", name="P1")
        report_db.create_project(project)

        meta1 = ReportMeta(
            user_id="user1",
            project_id=project.id,
            title="In project",
        )
        report_db.save_report(meta1, {"in": True})

        meta2 = ReportMeta(
            user_id="user1",
            title="Los rapport",
        )
        report_db.save_report(meta2, {"loose": True})

        in_project = report_db.list_reports("user1", project_id=project.id)
        assert len(in_project) == 1
        assert in_project[0]["title"] == "In project"

    def test_delete_report(self, report_db):
        """Verwijder rapport (DB + bestand)."""
        meta = ReportMeta(user_id="user1", title="Delete me")
        report_db.save_report(meta, {"data": True})

        # Bestand bestaat
        path = report_db._report_path("user1", meta.id)
        assert path.exists()

        deleted = report_db.delete_report(meta.id, "user1")
        assert deleted is True
        assert not path.exists()
        assert report_db.get_report_meta(meta.id) is None

    def test_delete_report_wrong_user(self, report_db):
        """Kan rapport van andere user niet verwijderen."""
        meta = ReportMeta(user_id="user1", title="Protected")
        report_db.save_report(meta, {"safe": True})

        deleted = report_db.delete_report(meta.id, "user2")
        assert deleted is False
        assert report_db.get_report_meta(meta.id) is not None

    def test_move_report_to_project(self, report_db):
        """Verplaats rapport naar project."""
        project = Project(user_id="user1", name="Target")
        report_db.create_project(project)

        meta = ReportMeta(user_id="user1", title="Movable")
        report_db.save_report(meta, {"data": True})

        result = report_db.move_report_to_project(
            meta.id, "user1", project.id
        )
        assert result is not None
        assert result.project_id == project.id

    def test_report_size_limit(self, report_db):
        """Te groot rapport → ValueError."""
        # Maak content van > 10 MB
        huge = {"data": "x" * (11 * 1024 * 1024)}
        meta = ReportMeta(user_id="user1", title="Too big")
        with pytest.raises(ValueError, match="te groot"):
            report_db.save_report(meta, huge)

    def test_get_report_wrong_user(self, report_db):
        """User A kan rapport van user B niet lezen."""
        meta = ReportMeta(user_id="user1", title="Private")
        report_db.save_report(meta, {"secret": True})

        result = report_db.get_report(meta.id, "user2")
        assert result is None


# ============================================================
# Integration tests — API endpoints
# ============================================================


@pytest.fixture()
def client():
    """Ongeauthenticeerde TestClient."""
    return TestClient(app)


class TestProjectAPI:
    """Tests voor /api/projects endpoints."""

    def test_projects_require_auth(self, client):
        """Projecten endpoints vereisen authenticatie."""
        r = client.get("/api/projects")
        assert r.status_code == 401

    def test_create_and_list_projects(self, authenticated_client):
        """Maak project aan via API en lijst het."""
        r = authenticated_client.post(
            "/api/projects",
            json={"name": "API Test Project", "description": "Test"},
        )
        assert r.status_code == 201
        project_id = r.json()["id"]

        r = authenticated_client.get("/api/projects")
        assert r.status_code == 200
        projects = r.json()["projects"]
        ids = [p["id"] for p in projects]
        assert project_id in ids

    def test_create_project_empty_name(self, authenticated_client):
        """Leeg projectnaam → 422."""
        r = authenticated_client.post(
            "/api/projects",
            json={"name": ""},
        )
        assert r.status_code == 422

    def test_delete_project(self, authenticated_client):
        """Verwijder project via API."""
        r = authenticated_client.post(
            "/api/projects",
            json={"name": "Delete Me"},
        )
        assert r.status_code == 201
        project_id = r.json()["id"]

        r = authenticated_client.delete(f"/api/projects/{project_id}")
        assert r.status_code == 200

        r = authenticated_client.get(f"/api/projects/{project_id}")
        assert r.status_code == 404


class TestReportAPI:
    """Tests voor /api/reports endpoints."""

    def test_reports_require_auth(self, client):
        """Rapport endpoints vereisen authenticatie."""
        r = client.get("/api/reports")
        assert r.status_code == 401

    def test_save_and_load_report(self, authenticated_client):
        """Sla rapport op en haal het weer op."""
        r = authenticated_client.post(
            "/api/reports",
            json={
                "title": "Test Rapport",
                "template": "structural",
                "content": {
                    "template": "structural",
                    "project": "Testgebouw",
                    "sections": [],
                },
            },
        )
        assert r.status_code == 201
        report_id = r.json()["id"]
        assert report_id

        # Laden
        r = authenticated_client.get(f"/api/reports/{report_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["title"] == "Test Rapport"
        assert data["content"]["project"] == "Testgebouw"

    def test_save_report_no_title(self, authenticated_client):
        """Rapport zonder titel → 422."""
        r = authenticated_client.post(
            "/api/reports",
            json={"title": "", "content": {"test": True}},
        )
        assert r.status_code == 422

    def test_save_report_no_content(self, authenticated_client):
        """Rapport zonder content → 422."""
        r = authenticated_client.post(
            "/api/reports",
            json={"title": "Test"},
        )
        assert r.status_code == 422

    def test_delete_report(self, authenticated_client):
        """Verwijder rapport via API."""
        r = authenticated_client.post(
            "/api/reports",
            json={
                "title": "Delete Me",
                "content": {"test": True},
            },
        )
        assert r.status_code == 201
        report_id = r.json()["id"]

        r = authenticated_client.delete(f"/api/reports/{report_id}")
        assert r.status_code == 200

        r = authenticated_client.get(f"/api/reports/{report_id}")
        assert r.status_code == 404

    def test_move_report_to_project(self, authenticated_client):
        """Verplaats rapport naar project via API."""
        # Maak project
        r = authenticated_client.post(
            "/api/projects",
            json={"name": "Move Target"},
        )
        assert r.status_code == 201
        project_id = r.json()["id"]

        # Maak rapport
        r = authenticated_client.post(
            "/api/reports",
            json={
                "title": "Movable Report",
                "content": {"test": True},
            },
        )
        assert r.status_code == 201
        report_id = r.json()["id"]

        # Verplaats
        r = authenticated_client.put(
            f"/api/reports/{report_id}/move",
            json={"project_id": project_id},
        )
        assert r.status_code == 200
        assert r.json()["project_id"] == project_id

    def test_list_reports_filter_project(self, authenticated_client):
        """Filter rapporten op project_id."""
        # Maak project
        r = authenticated_client.post(
            "/api/projects",
            json={"name": "Filter Test"},
        )
        project_id = r.json()["id"]

        # Rapport in project
        authenticated_client.post(
            "/api/reports",
            json={
                "title": "In project",
                "project_id": project_id,
                "content": {"in": True},
            },
        )
        # Los rapport
        authenticated_client.post(
            "/api/reports",
            json={
                "title": "Loose",
                "content": {"loose": True},
            },
        )

        r = authenticated_client.get(
            f"/api/reports?project_id={project_id}"
        )
        assert r.status_code == 200
        reports = r.json()["reports"]
        assert all(r["project_id"] == project_id for r in reports)
