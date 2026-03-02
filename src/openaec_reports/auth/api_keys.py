"""API Key model en SQLite CRUD voor machine-to-machine authenticatie.

API Keys bieden een alternatief voor username/password login.
Bedoeld voor headless integraties zoals pyRevit, MCP servers,
en CI/CD pipelines.

Elke key is gekoppeld aan een user (owner) en erft diens rechten.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Prefix voor herkenbare keys (bijv. "3bm_k_abc123...")
API_KEY_PREFIX = "3bm_k_"
API_KEY_BYTES = 32  # 256-bit entropy


def generate_api_key() -> str:
    """Genereer een nieuwe API key met prefix.

    Returns:
        API key string (bijv. "3bm_k_a1b2c3d4e5f6...").
    """
    return API_KEY_PREFIX + secrets.token_hex(API_KEY_BYTES)


def hash_api_key(key: str) -> str:
    """Hash een API key voor opslag (SHA-256).

    We slaan nooit de plaintext key op — alleen de hash.

    Args:
        key: Plaintext API key.

    Returns:
        SHA-256 hex digest.
    """
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


@dataclass
class ApiKey:
    """Een API Key in het systeem."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    name: str = ""
    key_hash: str = ""
    key_prefix: str = ""  # Eerste 12 chars voor identificatie (bijv. "3bm_k_a1b2")
    user_id: str = ""  # Gekoppelde user (owner)
    is_active: bool = True
    created_at: str = ""
    expires_at: str | None = None  # None = geen verloopdatum

    def to_dict(self) -> dict:
        """Publieke representatie (zonder key hash).

        Returns:
            Dict met key metadata.
        """
        return {
            "id": self.id,
            "name": self.name,
            "key_prefix": self.key_prefix,
            "user_id": self.user_id,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }


class ApiKeyDB:
    """SQLite wrapper voor API Key CRUD.

    Deelt dezelfde database als UserDB (auth.db).

    Args:
        db_path: Pad naar de SQLite database.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        import os

        from openaec_reports.auth.models import DEFAULT_DB_PATH

        self.db_path = Path(db_path or os.environ.get("OPENAEC_AUTH_DB", DEFAULT_DB_PATH))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Maak een nieuwe connectie.

        Returns:
            SQLite connectie.
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        """Maak de api_keys tabel aan als deze niet bestaat."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL DEFAULT '',
                    key_hash TEXT UNIQUE NOT NULL,
                    key_prefix TEXT NOT NULL DEFAULT '',
                    user_id TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    expires_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            # Index op key_hash voor snelle lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_api_keys_hash
                ON api_keys(key_hash)
            """)
            conn.commit()

    def _row_to_api_key(self, row: sqlite3.Row) -> ApiKey:
        """Converteer een database row naar ApiKey.

        Args:
            row: SQLite Row.

        Returns:
            ApiKey instance.
        """
        return ApiKey(
            id=row["id"],
            name=row["name"],
            key_hash=row["key_hash"],
            key_prefix=row["key_prefix"],
            user_id=row["user_id"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            expires_at=row["expires_at"],
        )

    def create(self, name: str, user_id: str, expires_at: str | None = None) -> tuple[ApiKey, str]:
        """Maak een nieuwe API key aan.

        Args:
            name: Beschrijvende naam (bijv. "pyRevit productie").
            user_id: ID van de user waaraan de key gekoppeld wordt.
            expires_at: Optionele verloopdatum (ISO format).

        Returns:
            Tuple van (ApiKey, plaintext_key).
            De plaintext key wordt alleen hier geretourneerd — bewaar hem!
        """
        plaintext = generate_api_key()
        key_hash_val = hash_api_key(plaintext)
        key_prefix = plaintext[:12]

        now = datetime.now(timezone.utc).isoformat()
        api_key = ApiKey(
            name=name,
            key_hash=key_hash_val,
            key_prefix=key_prefix,
            user_id=user_id,
            created_at=now,
            expires_at=expires_at,
        )

        with self._get_connection() as conn:
            conn.execute(
                """INSERT INTO api_keys (id, name, key_hash, key_prefix, user_id,
                   is_active, created_at, expires_at)
                   VALUES (?, ?, ?, ?, ?, 1, ?, ?)""",
                (api_key.id, api_key.name, api_key.key_hash,
                 api_key.key_prefix, api_key.user_id, now,
                 api_key.expires_at),
            )
            conn.commit()

        logger.info("API key aangemaakt: %s (%s) voor user %s", name, key_prefix, user_id)
        return api_key, plaintext

    def get_by_key(self, plaintext_key: str) -> ApiKey | None:
        """Zoek een API key op basis van de plaintext key.

        Args:
            plaintext_key: De volledige API key.

        Returns:
            ApiKey of None als niet gevonden/inactief/verlopen.
        """
        key_hash_val = hash_api_key(plaintext_key)

        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM api_keys WHERE key_hash = ? AND is_active = 1",
                (key_hash_val,),
            ).fetchone()

        if not row:
            return None

        api_key = self._row_to_api_key(row)

        # Check verloopdatum
        if api_key.expires_at:
            try:
                exp = datetime.fromisoformat(api_key.expires_at)
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) > exp:
                    logger.debug("API key verlopen: %s", api_key.key_prefix)
                    return None
            except ValueError:
                pass  # Ongeldige datum → negeer expiry

        return api_key

    def list_by_user(self, user_id: str) -> list[ApiKey]:
        """Lijst alle keys voor een user.

        Args:
            user_id: User ID.

        Returns:
            Lijst van ApiKey objecten.
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM api_keys WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        return [self._row_to_api_key(row) for row in rows]

    def list_all(self) -> list[ApiKey]:
        """Lijst alle API keys (admin).

        Returns:
            Lijst van ApiKey objecten.
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM api_keys ORDER BY created_at DESC"
            ).fetchall()
        return [self._row_to_api_key(row) for row in rows]

    def revoke(self, key_id: str) -> bool:
        """Deactiveer een API key.

        Args:
            key_id: ID van de key.

        Returns:
            True als de key gedeactiveerd is.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE api_keys SET is_active = 0 WHERE id = ?",
                (key_id,),
            )
            conn.commit()
            revoked = cursor.rowcount > 0

        if revoked:
            logger.info("API key ingetrokken: %s", key_id)
        return revoked

    def delete(self, key_id: str) -> bool:
        """Verwijder een API key permanent.

        Args:
            key_id: ID van de key.

        Returns:
            True als verwijderd.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM api_keys WHERE id = ?",
                (key_id,),
            )
            conn.commit()
            deleted = cursor.rowcount > 0

        if deleted:
            logger.info("API key verwijderd: %s", key_id)
        return deleted
