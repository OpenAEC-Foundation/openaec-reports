"""Structural report — Constructieve berekening rapport."""

from __future__ import annotations

from typing import Any

from openaec_reports.reports.base_report import BaseReport


class StructuralReport(BaseReport):
    """Rapporttype: Constructieve berekening.

    Standaard secties:
    - Uitgangspunten
    - Belastingen & belastingcombinaties
    - Berekeningen per element
    - Unity checks overzicht
    - Conclusie
    """

    report_type = "structural"
    default_template = "structural_report"

    def build_sections(self) -> list[dict[str, Any]]:
        """Bouw secties voor constructief rapport."""
        sections = []

        # TODO: Implementeer sectie-opbouw vanuit self._data
        # Voorbeeld structuur:
        # sections.append({
        #     "title": "Uitgangspunten",
        #     "content": [...],  # Lijst van flowables
        #     "level": 1,
        # })

        return sections
