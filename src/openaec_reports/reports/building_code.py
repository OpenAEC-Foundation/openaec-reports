"""Building code report — Bouwbesluit toetsing rapport."""

from __future__ import annotations

from typing import Any

from openaec_reports.reports.base_report import BaseReport


class BuildingCodeReport(BaseReport):
    """Rapporttype: Bouwbesluit toetsing.

    Generiek toetsingsrapport dat meerdere Bouwbesluit artikelen
    kan bevatten. Elke toets wordt gepresenteerd met:
    - Artikelreferentie
    - Eis
    - Berekende/gemeten waarde
    - Toetsresultaat

    Standaard secties:
    - Projectgegevens en uitgangspunten
    - Toetsingen per hoofdstuk/afdeling
    - Samenvattend overzicht
    - Conclusie
    """

    report_type = "building_code"
    default_template = "building_code_report"

    def build_sections(self) -> list[dict[str, Any]]:
        """Bouw secties voor bouwbesluit toetsing."""
        sections = []
        # TODO: Implementeer bouwbesluit toetsingssecties
        # Gebruik self._data met structuur vanuit bouwbesluit JSON
        return sections
