"""Header component — Koptekst met logo en projectinformatie."""

from __future__ import annotations

from reportlab.platypus import Flowable
from reportlab.lib.units import mm

from bm_reports.core.document import MM_TO_PT


class Header(Flowable):
    """Koptekst flowable voor rapportpagina's.

    Bevat:
    - Logo (SVG/PNG) rechts
    - Projectnummer + naam links
    - Optionele horizontale lijn

    Args:
        height_mm: Hoogte van de header in mm.
        logo_path: Pad naar logo bestand (SVG of PNG).
        project_number: Projectnummer.
        project_name: Projectnaam.
        show_rule: Toon horizontale lijn onder header.
    """

    def __init__(
        self,
        height_mm: float = 15.0,
        logo_path: str | None = None,
        project_number: str = "",
        project_name: str = "",
        show_rule: bool = True,
    ):
        super().__init__()
        self.height_mm = height_mm
        self.logo_path = logo_path
        self.project_number = project_number
        self.project_name = project_name
        self.show_rule = show_rule

    def wrap(self, available_width, available_height):
        self.width = available_width
        self.height = self.height_mm * MM_TO_PT
        return (self.width, self.height)

    def draw(self):
        """Render de header op het canvas."""
        # TODO: Implementeer header rendering
        # - Logo rechts uitlijnen
        # - Projectinfo links
        # - Horizontale lijn onderaan
        pass
