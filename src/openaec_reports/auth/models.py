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

    def _ensure_schema(self) -> None:
        """Maak de users tabel aan als deze niet bestaat."""
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
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
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
                   is_active, hashed_password)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    user.id,
                    user.username,
                    user.email,
                    user.display_name,
                    user.role.value,
                    user.tenant,
                    int(user.is_active),
                    user.hashed_password,
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
            "is_active", "hashed_password",
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
