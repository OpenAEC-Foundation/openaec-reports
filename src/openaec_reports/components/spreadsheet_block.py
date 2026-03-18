"""Spreadsheet block — Excel-achtige tabellen met celstijlen en samenvoegen."""

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
    """Excel-achtige tabel flowable met celstijlen, merged cells en rijhoogtes.

    Args:
        headers: Kolomnamen.
        rows: Data rijen (list of lists). Elk element is een str, getal,
              of dict met ``value``, ``formula``, ``style``.
        title: Optionele titel boven de tabel.
        col_widths_mm: Kolombreedte in mm (None = auto).
        row_heights_mm: Rijhoogte in mm per data-rij (None = auto).
        default_row_height_mm: Standaard rijhoogte in mm.
        show_row_numbers: Toon rijnummers als eerste kolom.
        zebra: Wisselende rijkleuren.
        note: Optionele voetnoot.
        merged_cells: Lijst van merge-definities (row, col, rowspan, colspan).
        cell_styles: Per-cel styling, sleutel is "rij,kolom".
    """

    def __init__(
        self,
        headers: list[str],
        rows: list[list[Any]],
        title: str = "",
        col_widths_mm: list[float] | None = None,
        row_heights_mm: list[float] | None = None,
        default_row_height_mm: float = 7.0,
        show_row_numbers: bool = False,
        zebra: bool = True,
        note: str = "",
        merged_cells: list[dict] | None = None,
        cell_styles: dict[str, dict] | None = None,
    ):
        super().__init__()
        self.headers = headers
        self.rows = rows
        self.title = title
        self.col_widths_mm = col_widths_mm
        self.row_heights_mm = row_heights_mm
        self.default_row_height_mm = default_row_height_mm
        self.show_row_numbers = show_row_numbers
        self.zebra = zebra
        self.note = note
        self.merged_cells = merged_cells or []
        self.cell_styles = cell_styles or {}

    def _cell_value(self, cell: Any) -> str:
        """Extraheer de weergave-waarde uit een cel."""
        if isinstance(cell, dict):
            value = str(cell.get("value", ""))
            formula = cell.get("formula", "")
            if formula:
                return f"{value} <i>({saxutils.escape(formula)})</i>"
            return value
        return str(cell) if cell is not None else ""

    def _cell_style(self, cell: Any) -> str:
        """Extraheer de stijl-aanduiding uit een cel."""
        if isinstance(cell, dict):
            return cell.get("style", "normal")
        return "normal"

    def _make_para_style(
        self,
        base_style: ParagraphStyle,
        row_idx: int,
        col_idx: int,
    ) -> ParagraphStyle:
        """Maak een ParagraphStyle met per-cel overrides."""
        key = f"{row_idx},{col_idx}"
        cs = self.cell_styles.get(key)
        if not cs:
            return base_style

        overrides: dict[str, Any] = {}
        if cs.get("bold") and cs.get("italic"):
            # Geen standaard bold-italic font, gebruik bold
            overrides["fontName"] = BM_FONTS.heading
        elif cs.get("bold"):
            overrides["fontName"] = BM_FONTS.heading
        elif cs.get("italic"):
            overrides["fontName"] = BM_FONTS.italic

        if cs.get("text_color"):
            overrides["textColor"] = HexColor(cs["text_color"])
        if cs.get("font_size"):
            overrides["fontSize"] = cs["font_size"]
            overrides["leading"] = cs["font_size"] * 1.3

        align_map = {"left": 0, "center": 1, "right": 2}
        if cs.get("align") and cs["align"] in align_map:
            overrides["alignment"] = align_map[cs["align"]]

        if not overrides:
            return base_style

        return ParagraphStyle(
            f"Cell_{key}",
            parent=base_style,
            **overrides,
        )

    def _build_content(self, available_width: float) -> Table:
        """Bouw ReportLab Table met spreadsheet-styling."""
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

        # Bepaal welke cellen verborgen zijn door merges
        hidden_cells: set[tuple[int, int]] = set()
        for mc in self.merged_cells:
            r, c = mc["row"], mc["col"]
            rs, cs = mc.get("rowspan", 1), mc.get("colspan", 1)
            for dr in range(rs):
                for dc in range(cs):
                    if dr != 0 or dc != 0:
                        hidden_cells.add((r + dr, c + dc))

        # Header rij
        effective_headers = list(self.headers)
        if self.show_row_numbers:
            effective_headers = ["#"] + effective_headers

        header_row = [
            Paragraph(saxutils.escape(str(h)), header_style)
            for h in effective_headers
        ]

        # Data rijen
        body_rows: list[list[Any]] = []
        total_row_indices: list[int] = []

        for row_idx, row in enumerate(self.rows):
            effective_row = list(row)
            if self.show_row_numbers:
                effective_row = [str(row_idx + 1)] + effective_row

            row_is_total = False
            built_row: list[Any] = []
            for col_idx, cell in enumerate(effective_row):
                # Verborgen cel door merge → lege string
                actual_col = col_idx - (1 if self.show_row_numbers else 0)
                actual_row = row_idx
                if (actual_row, actual_col) in hidden_cells:
                    built_row.append("")
                    continue

                cell_style_name = self._cell_style(cell)
                cell_text = self._cell_value(cell)
                if cell_style_name == "total":
                    row_is_total = True
                    style = total_style
                else:
                    style = body_style

                # Per-cel styling
                style = self._make_para_style(style, actual_row, actual_col)
                built_row.append(Paragraph(cell_text, style))

            if row_is_total:
                total_row_indices.append(row_idx + 1)
            body_rows.append(built_row)

        data = [header_row] + body_rows

        # Kolombreedte
        n_cols = len(effective_headers) if effective_headers else 1
        if self.col_widths_mm:
            col_widths = [w * MM_TO_PT for w in self.col_widths_mm]
            if self.show_row_numbers:
                col_widths = [25] + col_widths
        else:
            col_widths = [available_width / n_cols] * n_cols

        # Rijhoogte
        row_heights_pt = None
        if self.row_heights_mm:
            header_h = self.default_row_height_mm * MM_TO_PT
            data_h = [h * MM_TO_PT for h in self.row_heights_mm]
            # Pad met default als er minder heights dan rows zijn
            while len(data_h) < len(self.rows):
                data_h.append(self.default_row_height_mm * MM_TO_PT)
            row_heights_pt = [header_h] + data_h

        table = Table(
            data,
            colWidths=col_widths,
            rowHeights=row_heights_pt,
            repeatRows=1,
        )

        style_commands: list[tuple[Any, ...]] = [
            ("BACKGROUND", (0, 0), (-1, 0), HexColor(BM_COLORS.table_header_bg)),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor(BM_COLORS.rule)),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]

        # Zebra-striping
        if self.zebra:
            for i in range(1, len(data)):
                if i not in total_row_indices and i % 2 == 0:
                    style_commands.append(
                        ("BACKGROUND", (0, i), (-1, i),
                         HexColor(BM_COLORS.background_alt))
                    )

        # Totaalrijen
        for i in total_row_indices:
            style_commands.append(
                ("BACKGROUND", (0, i), (-1, i),
                 HexColor(BM_COLORS.table_header_bg))
            )
            style_commands.append(
                ("LINEABOVE", (0, i), (-1, i), 1.0,
                 HexColor(BM_COLORS.rule))
            )

        # Merged cells → SPAN commands
        col_offset = 1 if self.show_row_numbers else 0
        for mc in self.merged_cells:
            r = mc["row"] + 1  # +1 voor header rij
            c = mc["col"] + col_offset
            rs = mc.get("rowspan", 1)
            cs = mc.get("colspan", 1)
            style_commands.append(
                ("SPAN", (c, r), (c + cs - 1, r + rs - 1))
            )

        # Per-cel achtergrondkleur
        for key, cs in self.cell_styles.items():
            if cs.get("bg_color"):
                parts = key.split(",")
                if len(parts) == 2:
                    r = int(parts[0]) + 1  # +1 header offset
                    c = int(parts[1]) + col_offset
                    style_commands.append(
                        ("BACKGROUND", (c, r), (c, r),
                         HexColor(cs["bg_color"]))
                    )
            if cs.get("align"):
                parts = key.split(",")
                if len(parts) == 2:
                    r = int(parts[0]) + 1
                    c = int(parts[1]) + col_offset
                    align_val = cs["align"].upper()
                    style_commands.append(
                        ("ALIGN", (c, r), (c, r), align_val)
                    )

        table.setStyle(TableStyle(style_commands))
        return table
