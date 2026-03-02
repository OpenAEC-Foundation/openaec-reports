"""Title block — Titelblok voor voorblad.

.. deprecated::
    TitleBlock wordt niet gebruikt door de engine en wordt vervangen
    door canvas-functies in core/special_pages.py (cover page).
    Niet gebruiken voor nieuwe code.
"""

from __future__ import annotations

import warnings
from pathlib import Path

from reportlab.platypus import Flowable


class TitleBlock(Flowable):
    """Titelblok voor het voorblad.

    .. deprecated::
        Wordt vervangen door draw_cover_page() in core/special_pages.py.
        De engine gebruikt TitleBlock niet — cover wordt direct op het
        canvas getekend.
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
        warnings.warn(
            "TitleBlock is deprecated en wordt vervangen door "
            "draw_cover_page() in core/special_pages.py",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__()
        self.project = project
        self.subtitle = subtitle
        self.project_number = project_number
        self.client = client
        self.date_str = date_str
        self.image_path = image_path

    def wrap(self, available_width, available_height):
        self.width = available_width
        self.height = available_height
        return (self.width, self.height)

    def draw(self):
        """Render het titelblok (no-op, deprecated)."""
