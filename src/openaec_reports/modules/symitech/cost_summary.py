"""Symitech Cost Summary module — samenvattende kostentabel.

Eenvoudige tabel met kolommen, rijen en totaal.
Waarden in Nederlands valutaformaat.

Data schema voorbeeld::

    {
        "type": "cost_summary",
        "title": "Kostenopgave",
        "columns": ["Omschrijving", "Aantal", "Eenheidsprijs", "Totaal"],
        "rows": [
            {
                "description": "BIC controles",
                "quantity": 12,
                "unit_price": 283.33,
                "total": 3400.00
            }
        ],
        "total": 4550.00
    }
"""

from __future__ import annotations

from reportlab.lib.colors import HexColor

from openaec_reports.modules.base import ContentModule

# Layout constants (in points)
TITLE_HEIGHT = 28.0
COLUMN_HEADER_HEIGHT = 20.0
ROW_HEIGHT = 16.0
TOTAL_SEPARATOR_HEIGHT = 8.0
TOTAL_ROW_HEIGHT = 18.0
BOTTOM_PADDING = 8.0
DOUBLE_LINE_GAP = 2.7

# Column widths (fractions of available_width)
COL_DESC_FRAC = 0.45
COL_QTY_FRAC = 0.15
COL_UNIT_FRAC = 0.20
COL_TOTAL_FRAC = 0.20

LABEL_INDENT = 4.0


def _format_currency_nl(value: float) -> str:
    """Format als Nederlands valuta: ``€ 1.234,56``.

    Args:
        value: Bedrag in euro's.

    Returns:
        Geformateerde string.
    """
    formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"\u20ac {formatted}"


class CostSummaryModule(ContentModule):
    """Samenvattende kostentabel met kolommen, rijen en totaal.

    Kan portrait of landscape zijn. Kolommen: omschrijving, aantal,
    eenheidsprijs, totaal.
    """

    def _calculate_height(self) -> float:
        """Bereken totale hoogte."""
        h = TITLE_HEIGHT + COLUMN_HEADER_HEIGHT
        h += len(self.data.get("rows", [])) * ROW_HEIGHT
        if self.data.get("total") is not None:
            h += TOTAL_SEPARATOR_HEIGHT + TOTAL_ROW_HEIGHT
        h += BOTTOM_PADDING
        return h

    def draw(self) -> None:
        """Teken de kostentabel op het canvas."""
        c = self.canv
        w = self.available_width
        cfg = self.config

        primary = HexColor(cfg.colors.get("primary", "#006FAB"))
        secondary = HexColor(cfg.colors.get("secondary", "#94571E"))
        text_color = HexColor(cfg.colors.get("text", "#000000"))
        heading_font = cfg.fonts.get("heading", "Helvetica-Bold")
        body_font = cfg.fonts.get("body", "Helvetica")

        # Column x-positions
        col_desc_x = 0
        col_qty_x = w * COL_DESC_FRAC
        col_unit_x = col_qty_x + w * COL_QTY_FRAC
        col_total_x = col_unit_x + w * COL_UNIT_FRAC

        y = self.height

        # -- Titel --
        title = self.data.get("title", "Kostenopgave")
        y -= TITLE_HEIGHT
        c.setFont(heading_font, cfg.heading_size)
        c.setFillColor(primary)
        c.drawString(0, y + 4, title)

        # Dubbele lijn onder titel
        self._draw_double_line(c, 0, y, w, primary)

        # -- Kolomkoppen --
        columns = self.data.get("columns", [
            "Omschrijving", "Aantal", "Eenheidsprijs", "Totaal",
        ])
        y -= COLUMN_HEADER_HEIGHT
        c.setFont(heading_font, cfg.label_size)
        c.setFillColor(secondary)

        col_positions = [col_desc_x, col_qty_x, col_unit_x, col_total_x]
        for i, col_label in enumerate(columns):
            if i < len(col_positions):
                if i == 0:
                    c.drawString(col_positions[i] + LABEL_INDENT, y + 4, col_label)
                else:
                    # Numerieke kolommen rechts uitlijnen
                    right_edge = (
                        col_positions[i + 1] if i + 1 < len(col_positions) else w
                    )
                    c.drawRightString(right_edge, y + 4, col_label)

        # Lijn onder kolomkoppen
        c.setStrokeColor(primary)
        c.setLineWidth(cfg.line_width)
        c.line(0, y, w, y)

        # -- Rijen --
        for row in self.data.get("rows", []):
            y -= ROW_HEIGHT
            c.setFont(body_font, cfg.value_size)

            # Omschrijving
            c.setFillColor(text_color)
            c.drawString(
                col_desc_x + LABEL_INDENT, y + 4,
                str(row.get("description", "")),
            )

            # Aantal
            qty = row.get("quantity")
            if qty is not None:
                c.drawRightString(col_unit_x, y + 4, str(qty))

            # Eenheidsprijs
            unit_price = row.get("unit_price")
            if unit_price is not None:
                c.drawRightString(col_total_x, y + 4, _format_currency_nl(unit_price))

            # Totaal
            total = row.get("total")
            if total is not None:
                c.drawRightString(w, y + 4, _format_currency_nl(total))

        # -- Totaalregel --
        grand_total = self.data.get("total")
        if grand_total is not None:
            y -= TOTAL_SEPARATOR_HEIGHT
            c.setStrokeColor(primary)
            c.setLineWidth(cfg.line_width)
            c.line(0, y + TOTAL_SEPARATOR_HEIGHT / 2, w, y + TOTAL_SEPARATOR_HEIGHT / 2)

            y -= TOTAL_ROW_HEIGHT
            c.setFont(heading_font, cfg.value_size)
            c.setFillColor(text_color)
            c.drawString(col_desc_x + LABEL_INDENT, y + 4, "Totaal")
            c.drawRightString(w, y + 4, _format_currency_nl(grand_total))

    def _draw_double_line(
        self,
        c,
        x_start: float,
        y: float,
        x_end: float,
        color: HexColor,
    ) -> None:
        """Teken dubbele blauwe lijn (Symitech stijl)."""
        c.setStrokeColor(color)
        c.setLineWidth(self.config.line_width)
        c.line(x_start, y, x_end, y)
        c.line(x_start, y - DOUBLE_LINE_GAP, x_end, y - DOUBLE_LINE_GAP)
