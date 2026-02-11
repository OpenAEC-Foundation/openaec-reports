"""Image block — Afbeeldingen in rapporten (PNG, JPG, SVG)."""

from __future__ import annotations

from pathlib import Path
from reportlab.platypus import Flowable, Image
from svglib.svglib import svg2rlg

from bm_reports.core.document import MM_TO_PT


class ImageBlock(Flowable):
    """Afbeelding flowable met auto-scaling en caption.

    Ondersteunt PNG, JPG, en SVG (via svglib).

    Args:
        path: Pad naar afbeelding.
        width_mm: Gewenste breedte in mm (None = auto).
        height_mm: Gewenste hoogte in mm (None = auto).
        caption: Bijschrift onder de afbeelding.
        align: Uitlijning ('left', 'center', 'right').
    """

    SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".svg", ".gif", ".bmp"}

    def __init__(
        self,
        path: str | Path,
        width_mm: float | None = None,
        height_mm: float | None = None,
        caption: str = "",
        align: str = "center",
    ):
        super().__init__()
        self.path = Path(path)
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.caption = caption
        self.align = align

        if not self.path.exists():
            raise FileNotFoundError(f"Afbeelding niet gevonden: {self.path}")

        suffix = self.path.suffix.lower()
        if suffix not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Niet-ondersteund formaat: {suffix}")

    def _load_image(self):
        """Laad afbeelding als ReportLab object."""
        if self.path.suffix.lower() == ".svg":
            return svg2rlg(str(self.path))
        else:
            kwargs = {}
            if self.width_mm:
                kwargs["width"] = self.width_mm * MM_TO_PT
            if self.height_mm:
                kwargs["height"] = self.height_mm * MM_TO_PT
            return Image(str(self.path), **kwargs)

    def wrap(self, available_width, available_height):
        # TODO: Bereken afmetingen op basis van aspect ratio
        self.width = available_width
        self.height = 100  # Placeholder
        return (self.width, self.height)

    def draw(self):
        """Render de afbeelding met optioneel bijschrift."""
        # TODO: Implementeer image rendering + caption
        pass
