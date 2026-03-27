"""SQL utility functies — veilige identifier quoting.

Voorkomt SQL injection via dynamisch samengestelde kolomnamen
door identifiers te quoten met dubbele aanhalingstekens (SQL standaard).
"""

from __future__ import annotations

import re

# Alleen alfanumeriek en underscores zijn toegestaan als SQL identifiers
_SAFE_IDENTIFIER = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def quote_identifier(name: str) -> str:
    """Quote een SQL identifier veilig met dubbele aanhalingstekens.

    Valideert dat de identifier alleen veilige tekens bevat en
    escaped eventuele dubbele aanhalingstekens in de naam.

    Args:
        name: Kolomnaam of tabelnaam.

    Returns:
        Gequote identifier, bijv. ``"name"``.

    Raises:
        ValueError: Bij een lege of onveilige identifier.
    """
    if not name:
        raise ValueError("SQL identifier mag niet leeg zijn")

    if not _SAFE_IDENTIFIER.match(name):
        raise ValueError(
            f"Onveilige SQL identifier: {name!r}. "
            "Alleen letters, cijfers en underscores zijn toegestaan."
        )

    # Defense-in-depth: escape dubbele aanhalingstekens
    escaped = name.replace('"', '""')
    return f'"{escaped}"'
