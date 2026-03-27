"""Tests voor CR-K5 — SQL identifier quoting.

Verifieert dat quote_identifier() veilig identifiers escaped
en onveilige input afwijst.
"""

from __future__ import annotations

import pytest

from openaec_reports.storage.sql_utils import quote_identifier


class TestQuoteIdentifier:
    """Tests voor de quote_identifier() helper."""

    def test_simple_column_name(self) -> None:
        """Gewone kolomnaam wordt gequote."""
        assert quote_identifier("name") == '"name"'

    def test_column_with_underscore(self) -> None:
        """Kolomnaam met underscore wordt gequote."""
        assert quote_identifier("display_name") == '"display_name"'

    def test_column_starting_with_underscore(self) -> None:
        """Kolomnaam die begint met underscore is geldig."""
        assert quote_identifier("_internal") == '"_internal"'

    def test_column_with_numbers(self) -> None:
        """Kolomnaam met cijfers is geldig."""
        assert quote_identifier("field2") == '"field2"'

    def test_empty_string_raises(self) -> None:
        """Lege string gooit ValueError."""
        with pytest.raises(ValueError, match="mag niet leeg"):
            quote_identifier("")

    def test_sql_injection_semicolon(self) -> None:
        """SQL injection met puntkomma wordt geweigerd."""
        with pytest.raises(ValueError, match="Onveilige SQL identifier"):
            quote_identifier("name; DROP TABLE users")

    def test_sql_injection_dash_dash(self) -> None:
        """SQL injection met comment wordt geweigerd."""
        with pytest.raises(ValueError, match="Onveilige SQL identifier"):
            quote_identifier("name--")

    def test_sql_injection_space(self) -> None:
        """Kolomnaam met spatie wordt geweigerd."""
        with pytest.raises(ValueError, match="Onveilige SQL identifier"):
            quote_identifier("name = 1")

    def test_starts_with_number(self) -> None:
        """Kolomnaam die begint met een cijfer wordt geweigerd."""
        with pytest.raises(ValueError, match="Onveilige SQL identifier"):
            quote_identifier("1column")

    def test_special_characters(self) -> None:
        """Speciale tekens worden geweigerd."""
        for char in ["(", ")", "'", '"', ",", ".", "*", "/"]:
            with pytest.raises(ValueError, match="Onveilige SQL identifier"):
                quote_identifier(f"col{char}")

    def test_known_whitelisted_fields_pass(self) -> None:
        """Alle whitelisted velden uit de codebase moeten geldig zijn."""
        allowed_fields = [
            # storage/models.py — projects
            "name", "description",
            # storage/models.py — reports
            "title", "template", "project_id",
            # auth/models.py — users
            "email", "display_name", "role", "tenant",
            "is_active", "hashed_password", "phone", "job_title",
            "registration_number", "company", "auth_provider",
            "oidc_subject", "organisation_id",
            # auth/models.py — organisations
            "address", "postal_code", "city", "website", "kvk_number",
        ]
        for field_name in allowed_fields:
            result = quote_identifier(field_name)
            assert result == f'"{field_name}"'
