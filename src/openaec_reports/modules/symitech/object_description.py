"""Symitech Object Description module — objectbeschrijving pagina.

Eenvoudige layout met key-value velden, optionele notities en foto.

Data schema voorbeeld::

    {
        "type": "object_description",
        "title": "Objectbeschrijving",
        "object_name": "Peilbuis PB-01",
        "fields": [
            {"label": "Type", "value": "Grondwaterpeilbuis"},
            {"label": "Diameter", "value": "50 mm"},
            {"label": "Diepte", "value": "12,5 m-mv"}
        ],
        "notes": "Geplaatst in 2019, jaarlijkse controle.",
        "photo_path": null
    }
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader

from openaec_reports.modules.base import ContentModule

# Layout constants (in points)
TITLE_HEIGHT = 28.0
OBJECT_NAME_HEIGHT = 22.0
FIELD_ROW_HEIGHT = 16.0
SECTION_GAP = 14.0
DOUBLE_LINE_GAP = 2.7
NOTES_LINE_HEIGHT = 14.0
NOTES_TOP_MARGIN = 10.0
PHOTO_HEIGHT = 250.0
PHOTO_TOP_MARGIN = 16.0
PLACEHOLDER_HEIGHT = 60.0
BOTTOM_PADDING = 8.0

# Label column width (fraction of available_width)
LABEL_COL_FRAC = 0.30
LABEL_INDENT = 4.0

# Approximate characters per line for notes wrapping
CHARS_PER_LINE = 80


class ObjectDescriptionModule(ContentModule):
    """Objectbeschrijving pagina met velden, notities en optionele foto.

    Toont een objectnaam als sub-titel, gevolgd door een lijst key-value
    velden, optionele notities, en een optionele foto.
    """

    def _calculate_height(self) -> float:
        """Bereken totale hoogte op basis van velden, notes en foto."""
        h = TITLE_HEIGHT

        if self.data.get("object_name"):
            h += OBJECT_NAME_HEIGHT

        # Velden
        fields = self.data.get("fields", [])
        if fields:
            h += SECTION_GAP  # ruimte voor dubbele lijn
            h += len(fields) * FIELD_ROW_HEIGHT
            h += SECTION_GAP

        # Notes
        notes = self.data.get("notes", "")
        if notes:
            h += NOTES_TOP_MARGIN
            num_lines = max(1, len(notes) // CHARS_PER_LINE + 1)
            h += num_lines * NOTES_LINE_HEIGHT
            h += SECTION_GAP

        # Foto
        photo_path = self.data.get("photo_path")
        if photo_path and Path(photo_path).is_file():
            h += PHOTO_TOP_MARGIN + PHOTO_HEIGHT
        elif photo_path is not None:
            # Expliciete null/leeg = geen placeholder
            pass
        else:
            h += PHOTO_TOP_MARGIN + PLACEHOLDER_HEIGHT

        h += BOTTOM_PADDING
        return h

    def draw(self) -> None:
        """Teken de objectbeschrijving op het canvas."""
        c = self.canv
        w = self.available_width
        cfg = self.config

        primary = HexColor(cfg.colors.get("primary", "#006FAB"))
        secondary = HexColor(cfg.colors.get("secondary", "#94571E"))
        text_color = HexColor(cfg.colors.get("text", "#000000"))
        heading_font = cfg.fonts.get("heading", "Helvetica-Bold")
        body_font = cfg.fonts.get("body", "Helvetica")

        label_right = w * LABEL_COL_FRAC
        value_x = label_right + 8
        y = self.height

        # -- Pagina-titel (blauw, 14pt) --
        title = self.data.get("title", "Objectbeschrijving")
        y -= TITLE_HEIGHT
        c.setFont(heading_font, cfg.heading_size)
        c.setFillColor(primary)
        c.drawString(0, y + 4, title)

        # -- Objectnaam --
        object_name = self.data.get("object_name", "")
        if object_name:
            y -= OBJECT_NAME_HEIGHT
            c.setFont(heading_font, cfg.label_size + 2)
            c.setFillColor(text_color)
            c.drawString(0, y + 4, object_name)

        # -- Velden --
        fields = self.data.get("fields", [])
        if fields:
            # Dubbele blauwe lijn
            y -= SECTION_GAP
            c.setStrokeColor(primary)
            c.setLineWidth(cfg.line_width)
            c.line(0, y, w, y)
            c.line(0, y - DOUBLE_LINE_GAP, w, y - DOUBLE_LINE_GAP)

            for fld in fields:
                y -= FIELD_ROW_HEIGHT
                # Label (bruin)
                c.setFont(body_font, cfg.label_size)
                c.setFillColor(secondary)
                c.drawString(LABEL_INDENT, y + 4, fld.get("label", ""))
                # Waarde (zwart)
                c.setFillColor(text_color)
                c.drawString(value_x, y + 4, str(fld.get("value", "")))

            y -= SECTION_GAP

        # -- Notes --
        notes = self.data.get("notes", "")
        if notes:
            y -= NOTES_TOP_MARGIN

            # Dubbele blauwe lijn boven notities
            c.setStrokeColor(primary)
            c.setLineWidth(cfg.line_width)
            c.line(0, y, w, y)
            c.line(0, y - DOUBLE_LINE_GAP, w, y - DOUBLE_LINE_GAP)

            y -= NOTES_LINE_HEIGHT
            c.setFont(body_font, cfg.value_size)
            c.setFillColor(text_color)

            # Eenvoudige tekst wrapping
            for line in self._wrap_text(notes):
                c.drawString(LABEL_INDENT, y + 4, line)
                y -= NOTES_LINE_HEIGHT

            y -= SECTION_GAP

        # -- Foto --
        photo_path = self.data.get("photo_path")
        if photo_path and Path(photo_path).is_file():
            y -= PHOTO_TOP_MARGIN
            self._draw_photo(c, y, w, photo_path)
        elif photo_path is None:
            y -= PHOTO_TOP_MARGIN
            self._draw_placeholder(c, y, w, body_font, text_color)

    def _draw_photo(
        self,
        c,
        y: float,
        w: float,
        photo_path: str,
    ) -> None:
        """Teken een foto gecentreerd.

        Args:
            c: ReportLab canvas.
            y: Y-positie (bovenkant van foto-area).
            w: Beschikbare breedte.
            photo_path: Pad naar de afbeelding.
        """
        try:
            img = ImageReader(photo_path)
            img_w, img_h = img.getSize()
            scale = min(w / img_w, PHOTO_HEIGHT / img_h)
            draw_w = img_w * scale
            draw_h = img_h * scale
            x_offset = (w - draw_w) / 2
            c.drawImage(
                photo_path,
                x_offset, y - draw_h,
                width=draw_w, height=draw_h,
                preserveAspectRatio=True,
            )
        except Exception:
            self._draw_placeholder(
                c, y, w,
                self.config.fonts.get("body", "Helvetica"),
                HexColor(self.config.colors.get("text", "#000000")),
            )

    def _draw_placeholder(
        self,
        c,
        y: float,
        w: float,
        font: str,
        color: HexColor,
    ) -> None:
        """Teken een foto-placeholder.

        Args:
            c: ReportLab canvas.
            y: Y-positie (bovenkant).
            w: Beschikbare breedte.
            font: Font naam.
            color: Tekstkleur.
        """
        c.setStrokeColor(HexColor("#CCCCCC"))
        c.setFillColor(HexColor("#F5F5F5"))
        c.setLineWidth(0.5)
        c.rect(0, y - PLACEHOLDER_HEIGHT, w, PLACEHOLDER_HEIGHT, fill=1)

        c.setFont(font, 9)
        c.setFillColor(color)
        c.drawCentredString(
            w / 2, y - PLACEHOLDER_HEIGHT / 2 - 3,
            "[OBJECTFOTO]",
        )

    @staticmethod
    def _wrap_text(text: str, max_chars: int = CHARS_PER_LINE) -> list[str]:
        """Eenvoudige tekst-wrapping op woordgrenzen.

        Args:
            text: Te wrappen tekst.
            max_chars: Maximum karakters per regel.

        Returns:
            Lijst van regels.
        """
        words = text.split()
        lines: list[str] = []
        current_line = ""

        for word in words:
            if current_line and len(current_line) + 1 + len(word) > max_chars:
                lines.append(current_line)
                current_line = word
            elif current_line:
                current_line += " " + word
            else:
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines or [""]
