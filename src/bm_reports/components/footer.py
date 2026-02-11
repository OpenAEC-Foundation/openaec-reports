"""Footer component — Voettekst met paginanummering en bedrijfsinfo."""

from __future__ import annotations

from reportlab.platypus import Flowable

from bm_reports.core.document import MM_TO_PT


class Footer(Flowable):
    """Voettekst flowable voor rapportpagina's.

    Bevat:
    - Horizontale lijn bovenaan
    - Bedrijfsnaam + datum links
    - Paginanummer rechts ("Pagina X van Y")
    - Optionele grafische elementen

    Args:
        height_mm: Hoogte van de footer in mm.
        company: Bedrijfsnaam.
        date_str: Datum string.
        show_rule: Toon horizontale lijn boven footer.
    """

    def __init__(
        self,
        height_mm: float = 12.0,
        company: str = "3BM Bouwkunde",
        date_str: str = "",
        show_rule: bool = True,
    ):
        super().__init__()
        self.height_mm = height_mm
        self.company = company
        self.date_str = date_str
        self.show_rule = show_rule

    def wrap(self, available_width, available_height):
        self.width = available_width
        self.height = self.height_mm * MM_TO_PT
        return (self.width, self.height)

    def draw(self):
        """Render de footer op het canvas.

        Paginanummering wordt via ReportLab PageTemplate
        callbacks afgehandeld (canvasmaker of onPage).
        """
        # TODO: Implementeer footer rendering
        pass
