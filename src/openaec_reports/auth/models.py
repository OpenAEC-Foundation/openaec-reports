"""User model en SQLite CRUD voor authenticatie."""

from __future__ import annotations

import logging
import sqlite3
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = "data/auth.db"


class UserRole(str, Enum):
    """Gebruikersrollen."""

    admin = "admin"
    user = "user"


@dataclass
class User:
    """Gebruiker in het authenticatiesysteem."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    username: str = ""
    email: str = ""
    display_name: str = ""
    role: UserRole = UserRole.user
    tenant: str = ""
    is_active: bool = True
    hashed_password: str = ""
    # SSO / profiel velden
    phone: str = ""
    job_title: str = ""
    registration_number: str = ""
    company: str = ""
    auth_provider: str = "local"  # "local" of "oidc"
    oidc_subject: str = ""  # Authentik persistent subject ID
    organisation_id: str = ""  # FK naar organisations tabel

    def to_dict(self) -> dict:
        """Publieke representatie (zonder wachtwoord hash).

        Returns:
            Dict met user gegevens, zonder hashed_password.
        """
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "display_name": self.display_name,
            "role": self.role.value,
            "tenant": self.tenant,
            "is_active": self.is_active,
            "phone": self.phone,
            "job_title": self.job_title,
            "registration_number": self.registration_number,
            "company": self.company,
            "auth_provider": self.auth_provider,
            "organisation_id": self.organisation_id,
        }


class UserDB:
    """SQLite wrapper voor user CRUD operaties.

    Args:
        db_path: Pad naar de SQLite database.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        import os

        self.db_path = Path(db_path or os.environ.get("OPENAEC_AUTH_DB", DEFAULT_DB_PATH))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
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

    # Kolommen die via migratie worden toegevoegd aan bestaande databases
    _MIGRATION_COLUMNS: list[tuple[str, str]] = [
        ("phone", "TEXT NOT NULL DEFAULT ''"),
        ("job_title", "TEXT NOT NULL DEFAULT ''"),
        ("registration_number", "TEXT NOT NULL DEFAULT ''"),
        ("company", "TEXT NOT NULL DEFAULT ''"),
        ("auth_provider", "TEXT NOT NULL DEFAULT 'local'"),
        ("oidc_subject", "TEXT NOT NULL DEFAULT ''"),
        ("organisation_id", "TEXT NOT NULL DEFAULT ''"),
    ]

    def _ensure_schema(self) -> None:
        """Maak de users tabel aan en voer migraties uit voor nieuwe kolommen."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT NOT NULL DEFAULT '',
                    display_name TEXT NOT NULL DEFAULT '',
                    role TEXT NOT NULL DEFAULT 'user',
                    tenant TEXT NOT NULL DEFAULT '',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    hashed_password TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                    phone TEXT NOT NULL DEFAULT '',
                    job_title TEXT NOT NULL DEFAULT '',
                    registration_number TEXT NOT NULL DEFAULT '',
                    company TEXT NOT NULL DEFAULT '',
                    auth_provider TEXT NOT NULL DEFAULT 'local',
                    oidc_subject TEXT NOT NULL DEFAULT '',
                    organisation_id TEXT NOT NULL DEFAULT ''
                )
            """)
            # Migratie: voeg ontbrekende kolommen toe aan bestaande databases
            existing = {
                row[1]
                for row in conn.execute("PRAGMA table_info(users)").fetchall()
            }
            for col_name, col_def in self._MIGRATION_COLUMNS:
                if col_name not in existing:
                    conn.execute(
                        f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"
                    )
                    logger.info("Migratie: kolom '%s' toegevoegd aan users", col_name)
            conn.commit()

    def _row_to_user(self, row: sqlite3.Row) -> User:
        """Converteer een database row naar een User object.

        Args:
            row: SQLite Row object.

        Returns:
            User instance.
        """
        return User(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            display_name=row["display_name"],
            role=UserRole(row["role"]),
            tenant=row["tenant"],
            is_active=bool(row["is_active"]),
            hashed_password=row["hashed_password"],
            phone=row["phone"] if "phone" in row.keys() else "",
            job_title=row["job_title"] if "job_title" in row.keys() else "",
            registration_number=(
                row["registration_number"]
                if "registration_number" in row.keys()
                else ""
            ),
            company=row["company"] if "company" in row.keys() else "",
            auth_provider=(
                row["auth_provider"] if "auth_provider" in row.keys() else "local"
            ),
            oidc_subject=(
                row["oidc_subject"] if "oidc_subject" in row.keys() else ""
            ),
            organisation_id=(
                row["organisation_id"] if "organisation_id" in row.keys() else ""
            ),
        )

    def get_by_username(self, username: str) -> User | None:
        """Zoek een user op basis van username.

        Args:
            username: De gebruikersnaam.

        Returns:
            User of None als niet gevonden.
        """
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
            return self._row_to_user(row) if row else None

    def get_by_id(self, user_id: str) -> User | None:
        """Zoek een user op basis van ID.

        Args:
            user_id: De user UUID.

        Returns:
            User of None als niet gevonden.
        """
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            return self._row_to_user(row) if row else None

    def get_by_oidc_subject(self, subject: str) -> User | None:
        """Zoek een user op basis van OIDC subject identifier.

        Args:
            subject: Authentik persistent subject ID.

        Returns:
            User of None als niet gevonden.
        """
        if not subject:
            return None
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE oidc_subject = ?", (subject,)
            ).fetchone()
            return self._row_to_user(row) if row else None

    def get_by_email(self, email: str) -> User | None:
        """Zoek een user op basis van e-mailadres.

        Args:
            email: E-mailadres.

        Returns:
            User of None als niet gevonden.
        """
        if not email:
            return None
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ? COLLATE NOCASE",
                (email,),
            ).fetchone()
            return self._row_to_user(row) if row else None

    def create(self, user: User) -> User:
        """Maak een nieuwe user aan.

        Args:
            user: User object met alle velden ingevuld.

        Returns:
            De aangemaakte User.

        Raises:
            sqlite3.IntegrityError: Als de username al bestaat.
        """
        with self._get_connection() as conn:
            conn.execute(
                """INSERT INTO users (id, username, email, display_name, role, tenant,
                   is_active, hashed_password, phone, job_title,
                   registration_number, company, auth_provider, oidc_subject,
                   organisation_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    user.id,
                    user.username,
                    user.email,
                    user.display_name,
                    user.role.value,
                    user.tenant,
                    int(user.is_active),
                    user.hashed_password,
                    user.phone,
                    user.job_title,
                    user.registration_number,
                    user.company,
                    user.auth_provider,
                    user.oidc_subject,
                    user.organisation_id,
                ),
            )
            conn.commit()
        logger.info("User aangemaakt: %s (role=%s)", user.username, user.role.value)
        return user

    def list_all(self) -> list[User]:
        """Lijst alle users.

        Returns:
            Lijst van User objecten.
        """
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM users ORDER BY username").fetchall()
            return [self._row_to_user(row) for row in rows]

    def list_by_tenant(self, tenant: str) -> list[User]:
        """Lijst alle users voor een specifieke tenant.

        Args:
            tenant: De tenant identifier.

        Returns:
            Lijst van User objecten voor de tenant.
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM users WHERE tenant = ? ORDER BY username",
                (tenant,),
            ).fetchall()
            return [self._row_to_user(row) for row in rows]

    def update(self, user_id: str, **fields: str | bool) -> User | None:
        """Update een user met dynamische velden.

        Alleen whitelisted velden worden geaccepteerd.

        Args:
            user_id: De user UUID.
            **fields: Velden om te updaten (email, display_name, role, tenant,
                is_active, hashed_password).

        Returns:
            De geupdate User of None als niet gevonden.

        Raises:
            ValueError: Als een niet-toegestaan veld wordt meegegeven.
        """
        allowed = {
            "email", "display_name", "role", "tenant",
            "is_active", "hashed_password", "phone", "job_title",
            "registration_number", "company", "auth_provider", "oidc_subject",
            "organisation_id",
        }
        invalid = set(fields.keys()) - allowed
        if invalid:
            raise ValueError(f"Niet-toegestane velden: {invalid}")
        if not fields:
            return self.get_by_id(user_id)

        set_clauses = []
        values: list = []
        for key, value in fields.items():
            set_clauses.append(f"{key} = ?")
            if key == "is_active":
                values.append(int(value))
            else:
                values.append(value)

        set_clauses.append("updated_at = datetime('now')")
        values.append(user_id)

        sql = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?"
        with self._get_connection() as conn:
            cursor = conn.execute(sql, values)
            conn.commit()
            if cursor.rowcount == 0:
                return None

        logger.info("User %s geupdate: %s", user_id, list(fields.keys()))
        return self.get_by_id(user_id)

    def delete(self, user_id: str) -> bool:
        """Verwijder een user.

        Args:
            user_id: De user UUID.

        Returns:
            True als de user verwijderd is, False als niet gevonden.
        """
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
        if deleted:
            logger.info("User %s verwijderd", user_id)
        return deleted


@dataclass
class Organisation:
    """Organisatie (bedrijf/bureau) in het systeem."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    name: str = ""
    address: str = ""
    postal_code: str = ""
    city: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    kvk_number: str = ""
    is_active: bool = True

    def to_dict(self) -> dict:
        """Publieke representatie van de organisatie.

        Returns:
            Dict met organisatie gegevens.
        """
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "postal_code": self.postal_code,
            "city": self.city,
            "phone": self.phone,
            "email": self.email,
            "website": self.website,
            "kvk_number": self.kvk_number,
            "is_active": self.is_active,
        }


class OrganisationDB:
    """SQLite wrapper voor organisatie CRUD operaties.

    Args:
        db_path: Pad naar de SQLite database.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        import os
        self.db_path = Path(db_path or os.environ.get("OPENAEC_AUTH_DB", DEFAULT_DB_PATH))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
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
        """Maak de organisations tabel aan als die nog niet bestaat."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS organisations (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL DEFAULT '',
                    address TEXT NOT NULL DEFAULT '',
                    postal_code TEXT NOT NULL DEFAULT '',
                    city TEXT NOT NULL DEFAULT '',
                    phone TEXT NOT NULL DEFAULT '',
                    email TEXT NOT NULL DEFAULT '',
                    website TEXT NOT NULL DEFAULT '',
                    kvk_number TEXT NOT NULL DEFAULT '',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
            conn.commit()

    def _row_to_org(self, row: sqlite3.Row) -> Organisation:
        """Converteer een database row naar een Organisation object.

        Args:
            row: SQLite Row object.

        Returns:
            Organisation instance.
        """
        return Organisation(
            id=row["id"],
            name=row["name"],
            address=row["address"],
            postal_code=row["postal_code"],
            city=row["city"],
            phone=row["phone"],
            email=row["email"],
            website=row["website"],
            kvk_number=row["kvk_number"],
            is_active=bool(row["is_active"]),
        )

    def get_by_id(self, org_id: str) -> Organisation | None:
        """Zoek een organisatie op basis van ID.

        Args:
            org_id: De organisatie UUID.

        Returns:
            Organisation of None als niet gevonden.
        """
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM organisations WHERE id = ?", (org_id,)).fetchone()
            return self._row_to_org(row) if row else None

    def list_all(self) -> list[Organisation]:
        """Lijst alle organisaties alfabetisch op naam.

        Returns:
            Lijst van Organisation objecten.
        """
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM organisations ORDER BY name").fetchall()
            return [self._row_to_org(row) for row in rows]

    def create(self, org: Organisation) -> Organisation:
        """Maak een nieuwe organisatie aan.

        Args:
            org: Organisation object met alle velden ingevuld.

        Returns:
            De aangemaakte Organisation.
        """
        with self._get_connection() as conn:
            conn.execute(
                """INSERT INTO organisations (id, name, address, postal_code, city,
                   phone, email, website, kvk_number, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (org.id, org.name, org.address, org.postal_code, org.city,
                 org.phone, org.email, org.website, org.kvk_number, int(org.is_active)),
            )
            conn.commit()
        logger.info("Organisatie aangemaakt: %s", org.name)
        return org

    def update(self, org_id: str, **fields) -> Organisation | None:
        """Update een organisatie met dynamische velden.

        Alleen whitelisted velden worden geaccepteerd.

        Args:
            org_id: De organisatie UUID.
            **fields: Velden om te updaten.

        Returns:
            De geupdate Organisation of None als niet gevonden.

        Raises:
            ValueError: Als een niet-toegestaan veld wordt meegegeven.
        """
        allowed = {
            "name", "address", "postal_code", "city",
            "phone", "email", "website", "kvk_number", "is_active",
        }
        invalid = set(fields.keys()) - allowed
        if invalid:
            raise ValueError(f"Niet-toegestane velden: {invalid}")
        if not fields:
            return self.get_by_id(org_id)
        set_clauses = []
        values = []
        for key, value in fields.items():
            set_clauses.append(f"{key} = ?")
            values.append(int(value) if key == "is_active" else value)
        set_clauses.append("updated_at = datetime('now')")
        values.append(org_id)
        sql = f"UPDATE organisations SET {', '.join(set_clauses)} WHERE id = ?"
        with self._get_connection() as conn:
            cursor = conn.execute(sql, values)
            conn.commit()
            if cursor.rowcount == 0:
                return None
        return self.get_by_id(org_id)

    def delete(self, org_id: str) -> bool:
        """Verwijder een organisatie.

        Args:
            org_id: De organisatie UUID.

        Returns:
            True als verwijderd, False als niet gevonden.
        """
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM organisations WHERE id = ?", (org_id,))
            conn.commit()
            return cursor.rowcount > 0
