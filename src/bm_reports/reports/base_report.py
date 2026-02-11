"""Base report — Abstracte basis klasse voor alle rapporttypen."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from bm_reports.core.document import A4, PageFormat


class BaseReport(ABC):
    """Abstracte basis voor rapporttype definities.

    Elke subklasse definieert:
    - Standaard template (YAML)
    - Verplichte en optionele secties
    - Specifieke componenten (bijv. UC checks voor constructie)

    Subklassen moeten `default_template` en `build_sections()` implementeren.
    """

    report_type: str = "generic"
    default_template: str = ""  # YAML template naam

    def __init__(
        self,
        project: str = "",
        project_number: str = "",
        client: str = "",
        format: PageFormat = A4,
        **kwargs,
    ):
        self.project = project
        self.project_number = project_number
        self.client = client
        self.format = format
        self.extra = kwargs
        self._data: dict[str, Any] = {}

    def load_data(self, data: dict[str, Any]) -> None:
        """Laad project/berekeningsdata.

        Args:
            data: Dictionary met input data voor het rapport.
        """
        self._data = data

    def load_json(self, json_path: str | Path) -> None:
        """Laad data uit JSON bestand."""
        import json

        with Path(json_path).open("r", encoding="utf-8") as f:
            self._data = json.load(f)

    @abstractmethod
    def build_sections(self) -> list[dict[str, Any]]:
        """Bouw de secties voor dit rapporttype.

        Returns:
            Lijst van sectie-definities met titel, content, en level.
        """
        ...

    def generate(self, output_path: str | Path) -> Path:
        """Genereer het rapport.

        Args:
            output_path: Pad voor output PDF.

        Returns:
            Path naar gegenereerd PDF bestand.
        """
        from bm_reports.core.engine import Report

        report = Report(
            format=self.format,
            project=self.project,
            project_number=self.project_number,
            client=self.client,
            report_type=self.report_type,
            template=self.default_template,
        )

        report.add_cover(subtitle=self._data.get("subtitle", ""))
        report.add_colofon()

        for section in self.build_sections():
            report.add_section(**section)

        report.add_backcover()
        return report.build(output_path)
