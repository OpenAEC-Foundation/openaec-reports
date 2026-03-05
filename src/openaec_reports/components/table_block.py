"""Table block — Tabellen voor resultaten, parameters, overzichten."""

from __future__ import annotations

import xml.sax.saxutils as saxutils
from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle

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
        """Bouw ReportLab Table met styling en text-wrapping."""
        # Paragraph styles voor cellen — zorgt voor automatische word-wrap
        header_style = ParagraphStyle(
            "TableHeader",
            fontName=BM_FONTS.heading,
            fontSize=BM_FONTS.body_size,
            leading=BM_FONTS.body_size * 1.3,
            textColor=HexColor(BM_COLORS.table_header_text),
        )
        body_style = ParagraphStyle(
            "TableBody",
            fontName=BM_FONTS.body,
            fontSize=BM_FONTS.body_size,
            leading=BM_FONTS.body_size * 1.3,
            textColor=HexColor(BM_COLORS.text),
        )

        # Wrap celinhoud in Paragraph objecten voor automatische text-wrap
        header_row = [
            Paragraph(saxutils.escape(str(h)), header_style)
            for h in self.headers
        ]
        body_rows = [
            [Paragraph(saxutils.escape(str(cell)), body_style) for cell in row]
            for row in self.rows
        ]
        data = [header_row] + body_rows

        # Kolombreedte: expliciet, of gelijk verdeeld over beschikbare breedte
        if self.col_widths_mm:
            col_widths = [w * MM_TO_PT for w in self.col_widths_mm]
        else:
            n_cols = len(self.headers) if self.headers else 1
            col_widths = [available_width / n_cols] * n_cols

        table = Table(data, colWidths=col_widths, repeatRows=1)

        style_commands = [
            # Header styling
            ("BACKGROUND", (0, 0), (-1, 0), HexColor(BM_COLORS.table_header_bg)),
            # Grid
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor(BM_COLORS.rule)),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]

        if self.zebra:
            for i in range(1, len(data)):
                if i % 2 == 0:
                    style_commands.append(
                        ("BACKGROUND", (0, i), (-1, i), HexColor(BM_COLORS.background_alt))
                    )

        table.setStyle(TableStyle(style_commands))
        return table

    # wrap(), draw() en split() worden geërfd van BMFlowable
