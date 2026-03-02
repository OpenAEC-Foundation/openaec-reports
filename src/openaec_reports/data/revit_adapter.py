"""Revit adapter — Data import vanuit Autodesk Revit via pyRevit."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # Revit API types alleen beschikbaar in pyRevit context
    pass


class RevitAdapter:
    """Adapter voor het ophalen van data uit een Revit model.

    Twee gebruiksmodi:
    1. Direct in pyRevit: RevitAdapter(doc) — werkt met Revit Document object
    2. Ontkoppeld: RevitAdapter.from_json("data.json") — werkt met geëxporteerde data

    De adapter exporteert altijd naar het standaard JSON formaat
    dat de report generator consumeert.
    """

    def __init__(self, doc=None):
        """Initialiseer met optioneel Revit Document.

        Args:
            doc: Revit Document object (alleen in pyRevit context).
        """
        self.doc = doc
        self._data: dict[str, Any] = {}

    def get_project_info(self) -> dict[str, str]:
        """Haal projectinformatie op uit Revit.

        Returns:
            Dict met project, project_number, client, etc.
        """
        if self.doc is None:
            raise RuntimeError("Geen Revit document beschikbaar")

        # TODO: Implementeer Revit ProjectInfo uitlezing
        # info = self.doc.ProjectInformation
        # return {
        #     "project": info.Name,
        #     "project_number": info.Number,
        #     "client": info.ClientName,
        #     ...
        # }
        raise NotImplementedError("Revit project info uitlezing niet geïmplementeerd")

    def get_structural_elements(
        self,
        category: str = "Structural Framing",
    ) -> list[dict[str, Any]]:
        """Haal constructieve elementen op uit Revit.

        Args:
            category: Revit categorie naam.

        Returns:
            Lijst van element dictionaries.
        """
        # TODO: Implementeer element ophaling via FilteredElementCollector
        raise NotImplementedError("Structural elements ophaling niet geïmplementeerd")

    def get_rooms(self) -> list[dict[str, Any]]:
        """Haal ruimtes op (voor daglicht/bouwbesluit rapporten)."""
        # TODO: Implementeer room ophaling
        raise NotImplementedError("Room ophaling niet geïmplementeerd")

    def export_to_json(self, output_path: str | Path) -> Path:
        """Exporteer alle relevante data naar JSON.

        Args:
            output_path: Pad voor JSON output.

        Returns:
            Path naar geëxporteerd bestand.
        """
        import json

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "source": "revit",
            "project_info": self.get_project_info(),
            # TODO: Voeg element data toe
        }

        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return path

    @classmethod
    def from_json(cls, json_path: str | Path) -> RevitAdapter:
        """Maak adapter instantie vanuit eerder geëxporteerde JSON.

        Args:
            json_path: Pad naar JSON export.

        Returns:
            RevitAdapter met geladen data.
        """
        import json

        adapter = cls(doc=None)
        with Path(json_path).open("r", encoding="utf-8") as f:
            adapter._data = json.load(f)
        return adapter
