"""Table block — Tabellen voor resultaten, parameters, overzichten."""

from __future__ import annotations

from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.platypus import Table, TableStyle

from openaec_reports.components.base import BMFlowable
from openaec_reports.core.document import MM_TO_PT
from openaec_reports.core.styles import BM_COLORS, BM_FONTS


class TableBlock(BMFlowable):
    """Gestileerde tabel flowable in OpenAEC huisstijl.

    Args:
        headers: Kolomnamen.
        rows: Data rijen (list of lists).
        title: Optionele tabeltitel.
        col_widths_mm: Kolombreedte in mm (None = auto).
        zebra: Wisselende rijkleuren.
    """

    def __init__(
        self,
        headers: list[str],
        rows: list[list[Any]],
        title: str = "",
        col_widths_mm: list[float] | None = None,
        zebra: bool = True,
    ):
        super().__init__()
        self.headers = headers
        self.rows = rows
        self.title = title
        self.col_widths_mm = col_widths_mm
        self.zebra = zebra

    def _build_content(self, available_width: float) -> Table:
        """Bouw ReportLab Table met styling."""
        data = [self.headers] + self.rows

        col_widths = None
        if self.col_widths_mm:
            col_widths = [w * MM_TO_PT for w in self.col_widths_mm]

        table = Table(data, colWidths=col_widths)

        style_commands = [
            # Header styling
            ("BACKGROUND", (0, 0), (-1, 0), HexColor(BM_COLORS.table_header_bg)),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor(BM_COLORS.table_header_text)),
            ("FONTNAME", (0, 0), (-1, 0), BM_FONTS.heading),
            ("FONTSIZE", (0, 0), (-1, 0), BM_FONTS.body_size),
            # Body styling
            ("FONTNAME", (0, 1), (-1, -1), BM_FONTS.body),
            ("FONTSIZE", (0, 1), (-1, -1), BM_FONTS.body_size),
            ("TEXTCOLOR", (0, 1), (-1, -1), HexColor(BM_COLORS.text)),
            # Grid
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor(BM_COLORS.rule)),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ]

        if self.zebra:
            for i in range(1, len(data)):
                if i % 2 == 0:
                    style_commands.append(
                        ("BACKGROUND", (0, i), (-1, i), HexColor(BM_COLORS.background_alt))
                    )

        table.setStyle(TableStyle(style_commands))
        return table

    # wrap() en draw() worden geërfd van BMFlowable
