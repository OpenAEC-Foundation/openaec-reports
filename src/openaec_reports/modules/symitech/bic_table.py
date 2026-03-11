"""Symitech BIC Table module — kostenopgave tabel.

Gebaseerd op de Symitech referentie-PDF (page_003.png).
Twee kolommen: "Conform opdracht" en "Werkelijke kosten".

Data schema voorbeeld::

    {
        "type": "bic_table",
        "location_name": "Amsterdam Noord",
        "sections": [
            {
                "title": "BIC Controles",
                "rows": [
                    {
                        "label": "Aantal BIC controles",
                        "ref_value": "12",
                        "actual_value": "14"
                    }
                ]
            }
        ],
        "summary": {
            "title": "Overzicht samenvatting",
            "rows": [
                {"label": "BIC controles", "ref_value": "...", "actual_value": "..."}
            ],
            "total": {"label": "Totaal", "ref_value": "...", "actual_value": "..."}
        }
    }
"""

from __future__ import annotations

from reportlab.lib.colors import HexColor

from openaec_reports.modules.base import ContentModule

# Layout constants (in points)
ROW_HEIGHT = 16.0
SECTION_TITLE_HEIGHT = 20.0
SECTION_GAP = 10.0
COLUMN_HEADER_HEIGHT = 18.0
LOCATION_HEADER_HEIGHT = 24.0
DOUBLE_LINE_GAP = 2.7
TOTAL_SEPARATOR_HEIGHT = 8.0

# Column positions (fractions of available_width)
LABEL_COL_FRAC = 0.50
REF_COL_FRAC = 0.75
LABEL_INDENT = 4.0


class BicTableModule(ContentModule):
    """Kostenopgave tabel met 'Conform opdracht' en 'Werkelijke kosten' kolommen.

    Toont per sectie een lijst regels met referentiewaarden en werkelijke waarden,
    afgesloten met een samenvattingsblok en totaalregel.
    """

    def _calculate_height(self) -> float:
        """Bereken totale hoogte op basis van secties en rijen."""
        h = LOCATION_HEADER_HEIGHT + COLUMN_HEADER_HEIGHT

        for section in self.data.get("sections", []):
            h += SECTION_TITLE_HEIGHT + SECTION_GAP
            h += len(section.get("rows", [])) * ROW_HEIGHT
            h += SECTION_GAP

        summary = self.data.get("summary")
        if summary:
            h += SECTION_GAP + SECTION_TITLE_HEIGHT + SECTION_GAP
            h += len(summary.get("rows", [])) * ROW_HEIGHT
            if summary.get("total"):
                h += TOTAL_SEPARATOR_HEIGHT + ROW_HEIGHT
            h += SECTION_GAP

        return h

    def draw(self) -> None:
        """Teken de BIC tabel op het canvas."""
        c = self.canv
        w = self.available_width
        cfg = self.config

        primary = HexColor(cfg.colors.get("primary", "#006FAB"))
        secondary = HexColor(cfg.colors.get("secondary", "#94571E"))
        text_color = HexColor(cfg.colors.get("text", "#000000"))
        heading_font = cfg.fonts.get("heading", "LiberationSans-Bold")
        body_font = cfg.fonts.get("body", "LiberationSans")

        ref_x = w * LABEL_COL_FRAC
        actual_x = w * REF_COL_FRAC
        ref_right = actual_x - 8
        y = self.height

        # -- Locatienaam rechtsboven (blauw) --
        location = self.data.get("location_name", "")
        if location:
            y -= LOCATION_HEADER_HEIGHT
            c.setFont(heading_font, cfg.heading_size)
            c.setFillColor(primary)
            c.drawRightString(w, y + 4, location)

        # -- Kolomkoppen --
        y -= COLUMN_HEADER_HEIGHT
        c.setFont(heading_font, cfg.label_size)
        c.setFillColor(secondary)
        c.drawString(ref_x, y + 4, "Conform opdracht")
        c.drawString(actual_x, y + 4, "Werkelijke kosten")

        # -- Secties --
        for section in self.data.get("sections", []):
            y -= SECTION_GAP
            y -= SECTION_TITLE_HEIGHT

            # Sectie-titel + dubbele lijn
            c.setFont(heading_font, cfg.label_size)
            c.setFillColor(text_color)
            c.drawString(0, y + 4, section.get("title", ""))
            self._draw_double_line(c, 0, y, w, primary)

            # Rijen
            for row in section.get("rows", []):
                y -= ROW_HEIGHT
                c.setFont(body_font, cfg.value_size)
                c.setFillColor(secondary)
                c.drawString(LABEL_INDENT, y + 4, row.get("label", ""))
                c.setFillColor(text_color)
                c.drawRightString(ref_right, y + 4, str(row.get("ref_value", "")))
                c.drawRightString(w, y + 4, str(row.get("actual_value", "")))

            y -= SECTION_GAP

        # -- Samenvatting --
        summary = self.data.get("summary")
        if summary:
            y -= SECTION_GAP
            y -= SECTION_TITLE_HEIGHT

            c.setFont(heading_font, cfg.label_size)
            c.setFillColor(text_color)
            c.drawString(0, y + 4, summary.get("title", "Samenvatting"))
            self._draw_double_line(c, 0, y, w, primary)

            for row in summary.get("rows", []):
                y -= ROW_HEIGHT
                c.setFont(body_font, cfg.value_size)
                c.setFillColor(secondary)
                c.drawString(LABEL_INDENT, y + 4, row.get("label", ""))
                c.setFillColor(text_color)
                c.drawRightString(ref_right, y + 4, str(row.get("ref_value", "")))
                c.drawRightString(w, y + 4, str(row.get("actual_value", "")))

            # Totaalregel
            total = summary.get("total")
            if total:
                y -= TOTAL_SEPARATOR_HEIGHT
                c.setStrokeColor(primary)
                c.setLineWidth(cfg.line_width)
                c.line(0, y + TOTAL_SEPARATOR_HEIGHT / 2, w, y + TOTAL_SEPARATOR_HEIGHT / 2)

                y -= ROW_HEIGHT
                c.setFont(heading_font, cfg.value_size)
                c.setFillColor(text_color)
                c.drawString(LABEL_INDENT, y + 4, total.get("label", "Totaal"))
                c.drawRightString(ref_right, y + 4, str(total.get("ref_value", "")))
                c.drawRightString(w, y + 4, str(total.get("actual_value", "")))

    def _draw_double_line(
        self,
        c,
        x_start: float,
        y: float,
        x_end: float,
        color: HexColor,
    ) -> None:
        """Teken dubbele blauwe lijn (Symitech stijl).

        Args:
            c: ReportLab canvas.
            x_start: Begin x-positie.
            y: Y-positie van de bovenste lijn.
            x_end: Eind x-positie.
            color: Lijnkleur.
        """
        c.setStrokeColor(color)
        c.setLineWidth(self.config.line_width)
        c.line(x_start, y, x_end, y)
        c.line(x_start, y - DOUBLE_LINE_GAP, x_end, y - DOUBLE_LINE_GAP)
