"""Title block — Titelblok voor voorblad."""

from __future__ import annotations

from pathlib import Path
from reportlab.platypus import Flowable

from bm_reports.core.document import MM_TO_PT


class TitleBlock(Flowable):
    """Titelblok voor het voorblad.

    Bevat:
    - Projectnaam (groot)
    - Ondertitel / rapporttype
    - Projectnummer
    - Opdrachtgever
    - Datum
    - Optionele afbeelding

    Args:
        project: Projectnaam.
        subtitle: Ondertitel.
        project_number: Projectnummer.
        client: Opdrachtgever.
        date_str: Datum.
        image_path: Optioneel pad naar cover afbeelding.
    """

    def __init__(
        self,
        project: str = "",
        subtitle: str = "",
        project_number: str = "",
        client: str = "",
        date_str: str = "",
        image_path: str | Path | None = None,
    ):
        super().__init__()
        self.project = project
        self.subtitle = subtitle
        self.project_number = project_number
        self.client = client
        self.date_str = date_str
        self.image_path = image_path

    def wrap(self, available_width, available_height):
        self.width = available_width
        self.height = available_height  # Voorblad vult hele pagina
        return (self.width, self.height)

    def draw(self):
        """Render het titelblok."""
        # TODO: Implementeer cover page layout
        # - Grafische elementen (balk, kleurvlak)
        # - Logo
        # - Project titel
        # - Ondertitel
        # - Projectinfo tabel
        # - Optionele afbeelding
        pass
