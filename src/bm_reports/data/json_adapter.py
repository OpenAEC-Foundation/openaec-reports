"""JSON adapter — Generieke data import vanuit JSON bestanden."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonAdapter:
    """Laad projectdata vanuit JSON bestanden.

    Dit is de primaire data-interface voor de report generator.
    Alle andere adapters (Revit, ERPNext) exporteren naar dit formaat.

    Standaard JSON structuur:
    ```json
    {
        "project": "Projectnaam",
        "project_number": "2026-001",
        "client": "Opdrachtgever",
        "author": "3BM Bouwkunde",
        "report_type": "structural",
        "subtitle": "Constructieve berekening",
        "date": "2026-02-11",
        "sections": [
            {
                "title": "Uitgangspunten",
                "level": 1,
                "content": [...]
            }
        ]
    }
    ```
    """

    def __init__(self, json_path: str | Path | None = None):
        self.data: dict[str, Any] = {}
        if json_path:
            self.load(json_path)

    def load(self, json_path: str | Path) -> dict[str, Any]:
        """Laad data uit JSON bestand.

        Args:
            json_path: Pad naar JSON bestand.

        Returns:
            Geladen data dictionary.
        """
        path = Path(json_path)
        with path.open("r", encoding="utf-8") as f:
            self.data = json.load(f)
        return self.data

    def load_string(self, json_string: str) -> dict[str, Any]:
        """Laad data uit JSON string."""
        self.data = json.loads(json_string)
        return self.data

    def get_project_info(self) -> dict[str, str]:
        """Extraheer projectinformatie."""
        return {
            "project": self.data.get("project", ""),
            "project_number": self.data.get("project_number", ""),
            "client": self.data.get("client", ""),
            "author": self.data.get("author", "3BM Bouwkunde"),
            "report_type": self.data.get("report_type", ""),
            "subtitle": self.data.get("subtitle", ""),
        }

    def get_sections(self) -> list[dict[str, Any]]:
        """Extraheer secties."""
        return self.data.get("sections", [])

    def validate(self) -> list[str]:
        """Valideer de data structuur.

        Returns:
            Lijst van validatie fouten (leeg = geldig).
        """
        errors = []
        if not self.data.get("project"):
            errors.append("Verplicht veld ontbreekt: 'project'")
        if not self.data.get("project_number"):
            errors.append("Verplicht veld ontbreekt: 'project_number'")
        return errors
