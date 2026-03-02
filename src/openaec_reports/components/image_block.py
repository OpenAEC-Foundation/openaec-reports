"""Image block — Afbeeldingen in rapporten (PNG, JPG, SVG)."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, Paragraph, Table, TableStyle
from svglib.svglib import svg2rlg

from openaec_reports.components.base import BMFlowable
from openaec_reports.core.document import MM_TO_PT
from openaec_reports.core.styles import BM_STYLES


class ImageBlock(BMFlowable):
    """Afbeelding flowable met auto-scaling en caption.

    Ondersteunt PNG, JPG, en SVG (via svglib).
    Berekent automatisch de juiste afmetingen met behoud van aspect ratio.
    Gebruikt intern een Table voor layout (image + caption).

    Args:
        path: Pad naar afbeelding.
        width_mm: Gewenste breedte in mm (None = auto-fit binnen beschikbare breedte).
        height_mm: Gewenste hoogte in mm (None = auto op basis van aspect ratio).
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

        self._natural_size: tuple[float, float] | None = None

    def _get_natural_size(self) -> tuple[float, float]:
        """Bepaal natuurlijke afmetingen in points (1 px = 1 pt bij 72 DPI).

        Resultaat wordt gecached na eerste aanroep.
        """
        if self._natural_size is not None:
            return self._natural_size

        if self.path.suffix.lower() == ".svg":
            drawing = svg2rlg(str(self.path))
            if drawing:
                self._natural_size = (float(drawing.width), float(drawing.height))
            else:
                self._natural_size = (100.0, 100.0)
        else:
            reader = ImageReader(str(self.path))
            w_px, h_px = reader.getSize()
            self._natural_size = (float(w_px), float(h_px))

        return self._natural_size

    def _load_image(self, target_w: float, target_h: float):
        """Laad afbeelding als ReportLab object met opgegeven afmetingen.

        Args:
            target_w: Doelbreedte in points.
            target_h: Doelhoogte in points.
        """
        if self.path.suffix.lower() == ".svg":
            drawing = svg2rlg(str(self.path))
            if drawing and drawing.width > 0 and drawing.height > 0:
                sx = target_w / drawing.width
                sy = target_h / drawing.height
                drawing.width = target_w
                drawing.height = target_h
                drawing.scale(sx, sy)
                return drawing
            return None
        return Image(str(self.path), width=target_w, height=target_h)

    def _build_content(self, available_width: float) -> Table:
        """Bouw intern Table object met afbeelding en optioneel caption."""
        nat_w, nat_h = self._get_natural_size()
        if nat_w <= 0 or nat_h <= 0:
            nat_w, nat_h = 100.0, 100.0
        aspect = nat_h / nat_w

        # Bepaal target breedte
        if self.width_mm:
            target_w = min(self.width_mm * MM_TO_PT, available_width)
        else:
            target_w = min(nat_w, available_width)

        # Bereken hoogte met aspect ratio
        target_h = target_w * aspect

        # Optionele hoogte-constraint
        if self.height_mm:
            max_h = self.height_mm * MM_TO_PT
            if target_h > max_h:
                target_h = max_h
                target_w = target_h / aspect

        img = self._load_image(target_w, target_h)
        if img is None:
            img = Paragraph(
                "<i>[Afbeelding kon niet geladen worden]</i>",
                BM_STYLES["Caption"],
            )

        data = [[img]]
        if self.caption:
            data.append([Paragraph(self.caption, BM_STYLES["Caption"])])

        table = Table(data, colWidths=[available_width])
        align_map = {"left": "LEFT", "center": "CENTER", "right": "RIGHT"}
        rl_align = align_map.get(self.align, "CENTER")

        style_cmds = [
            ("ALIGN", (0, 0), (0, 0), rl_align),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]
        if self.caption:
            style_cmds.append(("TOPPADDING", (0, 1), (0, 1), 4))
            style_cmds.append(("ALIGN", (0, 1), (0, 1), "CENTER"))

        table.setStyle(TableStyle(style_cmds))
        return table

    # wrap() en draw() worden geërfd van BMFlowable
