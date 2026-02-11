"""Daylight report — Daglichtberekening rapport."""

from __future__ import annotations

from typing import Any

from bm_reports.reports.base_report import BaseReport


class DaylightReport(BaseReport):
    """Rapporttype: Daglichtberekening (Bouwbesluit Art. 3.74 / NEN 2057).

    Standaard secties:
    - Uitgangspunten
    - Situatie en oriëntatie
    - Berekening equivalente daglichtoppervlakte per verblijfsgebied
    - Toetsing aan Bouwbesluit eisen
    - Conclusie
    """

    report_type = "daylight"
    default_template = "daylight_report"

    def build_sections(self) -> list[dict[str, Any]]:
        """Bouw secties voor daglichrapport."""
        sections = []
        # TODO: Implementeer daglichtsecties
        return sections
