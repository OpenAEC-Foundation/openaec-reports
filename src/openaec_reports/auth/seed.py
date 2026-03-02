"""Interactieve user aanmaak voor CLI."""

from __future__ import annotations

import getpass
import uuid

from openaec_reports.auth.models import User, UserDB, UserRole
from openaec_reports.auth.security import hash_password


def create_user_interactive(
    db_path: str | None = None,
    role: UserRole = UserRole.user,
) -> User:
    """Maak een user aan via interactieve CLI prompts.

    Args:
        db_path: Optioneel pad naar de SQLite database.
        role: Rol voor de nieuwe user.

    Returns:
        De aangemaakte User.
    """
    db = UserDB(db_path)

    print(f"Nieuwe gebruiker aanmaken (rol: {role.value})")
    print("-" * 40)

    username = input("Username: ").strip()
    if not username:
        print("Fout: username mag niet leeg zijn")
        raise SystemExit(1)

    existing = db.get_by_username(username)
    if existing:
        print(f"Fout: gebruiker '{username}' bestaat al")
        raise SystemExit(1)

    email = input("Email: ").strip()
    display_name = input("Weergavenaam: ").strip() or username

    password = getpass.getpass("Wachtwoord: ")
    if len(password) < 8:
        print("Fout: wachtwoord moet minimaal 8 tekens zijn")
        raise SystemExit(1)

    password_confirm = getpass.getpass("Wachtwoord (bevestig): ")
    if password != password_confirm:
        print("Fout: wachtwoorden komen niet overeen")
        raise SystemExit(1)

    user = User(
        id=uuid.uuid4().hex,
        username=username,
        email=email,
        display_name=display_name,
        role=role,
        hashed_password=hash_password(password),
    )

    db.create(user)
    print(f"\nGebruiker aangemaakt: {username} (rol: {role.value})")
    return user
