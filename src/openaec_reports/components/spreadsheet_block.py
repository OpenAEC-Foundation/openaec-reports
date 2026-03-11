"""Spreadsheet block — Spreadsheet-achtige tabellen met formule-annotaties."""

from __future__ import annotations

import xml.sax.saxutils as saxutils
from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle

from openaec_reports.components.base import BMFlowable
from openaec_reports.core.document import MM_TO_PT
from openaec_reports.core.styles import BM_COLORS, BM_FONTS


class SpreadsheetBlock(BMFlowable):
    """Spreadsheet-achtige tabel flowable in OpenAEC huisstijl.

    Ondersteunt kolomheaders, rijlabels, formule-annotaties en
    verschillende celstijlen (normaal, totaalrij, opmaak-rij).

    Args:
        headers: Kolomnamen (eerste kolom is normaal een rijlabel).
        rows: Data rijen (list of lists). Elk element is een str of dict
              met optionele sleutels: ``value``, ``formula``, ``style``
              (``"total"``, ``"header"`` of ``"normal"``).
        title: Optionele tabel-/spreadsheet-titel.
        col_widths_mm: Kolombreedte in mm (None = auto verdeling).
        show_row_numbers: Toon rijnummers als eerste kolom.
        zebra: Wisselende rijkleuren voor betere leesbaarheid.
        note: Optionele voetnoot onder de tabel.
    """

    def __init__(
        self,
        headers: list[str],
        rows: list[list[Any]],
        title: str = "",
        col_widths_mm: list[float] | None = None,
        show_row_numbers: bool = False,
        zebra: bool = True,
        note: str = "",
    ):
        super().__init__()
        self.headers = headers
        self.rows = rows
        self.title = title
        self.col_widths_mm = col_widths_mm
        self.show_row_numbers = show_row_numbers
        self.zebra = zebra
        self.note = note

    def _cell_value(self, cell: Any) -> str:
        """Extraheer de weergave-waarde uit een cel.

        Args:
            cell: String of dict met ``value`` en optioneel ``formula``.

        Returns:
            Weergave-tekst voor de cel.
        """
        if isinstance(cell, dict):
            value = str(cell.get("value", ""))
            formula = cell.get("formula", "")
            if formula:
                return f"{value} <i>({saxutils.escape(formula)})</i>"
            return value
        return str(cell) if cell is not None else ""

    def _cell_style(self, cell: Any) -> str:
        """Extraheer de stijl-aanduiding uit een cel.

        Args:
            cell: String of dict met optioneel ``style`` sleutel.

        Returns:
            Stijlnaam: ``"total"``, ``"header"`` of ``"normal"``.
        """
        if isinstance(cell, dict):
            return cell.get("style", "normal")
        return "normal"

    def _build_content(self, available_width: float) -> Table:
        """Bouw ReportLab Table met spreadsheet-styling.

        Args:
            available_width: Beschikbare breedte in points.

        Returns:
            Gestileerde ReportLab Table.
        """
        # Paragraph styles
        header_style = ParagraphStyle(
            "SpreadsheetHeader",
            fontName=BM_FONTS.heading,
            fontSize=BM_FONTS.body_size,
            leading=BM_FONTS.body_size * 1.3,
            textColor=HexColor(BM_COLORS.table_header_text),
        )
        body_style = ParagraphStyle(
            "SpreadsheetBody",
            fontName=BM_FONTS.body,
            fontSize=BM_FONTS.body_size,
            leading=BM_FONTS.body_size * 1.3,
            textColor=HexColor(BM_COLORS.text),
        )
        total_style = ParagraphStyle(
            "SpreadsheetTotal",
            fontName=BM_FONTS.heading,
            fontSize=BM_FONTS.body_size,
            leading=BM_FONTS.body_size * 1.3,
            textColor=HexColor(BM_COLORS.text),
        )

        # Bouw header rij
        effective_headers = list(self.headers)
        if self.show_row_numbers:
            effective_headers = ["#"] + effective_headers

        header_row = [
            Paragraph(saxutils.escape(str(h)), header_style)
            for h in effective_headers
        ]

        # Bouw data rijen
        body_rows: list[list[Paragraph]] = []
        total_row_indices: list[int] = []  # Rij-indices (1-based incl. header) van totaalrijen

        for row_idx, row in enumerate(self.rows):
            effective_row = list(row)
            if self.show_row_numbers:
                effective_row = [str(row_idx + 1)] + effective_row

            row_is_total = False
            built_row: list[Paragraph] = []
            for col_idx, cell in enumerate(effective_row):
                cell_style_name = self._cell_style(cell)
                cell_text = self._cell_value(cell)
                if cell_style_name == "total":
                    row_is_total = True
                    style = total_style
                else:
                    style = body_style
                built_row.append(Paragraph(cell_text, style))

            if row_is_total:
                total_row_indices.append(row_idx + 1)  # +1 voor header rij offset

            body_rows.append(built_row)

        data = [header_row] + body_rows

        # Kolombreedte berekening
        n_cols = len(effective_headers) if effective_headers else 1
        if self.col_widths_mm:
            col_widths = [w * MM_TO_PT for w in self.col_widths_mm]
        else:
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

        # Zebra-striping voor data rijen
        if self.zebra:
            for i in range(1, len(data)):
                if i not in total_row_indices and i % 2 == 0:
                    style_commands.append(
                        ("BACKGROUND", (0, i), (-1, i), HexColor(BM_COLORS.background_alt))
                    )

        # Totaalrijen: lichte achtergrond + dikke bovenrand
        for i in total_row_indices:
            style_commands.append(
                ("BACKGROUND", (0, i), (-1, i), HexColor(BM_COLORS.table_header_bg))
            )
            style_commands.append(
                ("LINEABOVE", (0, i), (-1, i), 1.0, HexColor(BM_COLORS.rule))
            )

        table.setStyle(TableStyle(style_commands))
        return table

    # wrap(), draw() en split() worden geërfd van BMFlowable
