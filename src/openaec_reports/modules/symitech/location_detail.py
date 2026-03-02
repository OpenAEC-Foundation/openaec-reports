"""Symitech Location Detail module — locatie informatiepagina.

Gebaseerd op de Symitech referentie-PDF (page_002.png).
Twee secties met label-waarde paren, plus een optionele foto.

Data schema voorbeeld::

    {
        "type": "location_detail",
        "title": "Locatie",
        "client": {
            "section_title": "Opdrachtgever",
            "name": "Gemeente Amsterdam",
            "address": "Amstel 1",
            "city": "1011 PN Amsterdam"
        },
        "location": {
            "section_title": "Locatie van uitvoer",
            "name": "Depot Noord",
            "address": "Industrieweg 10",
            "city": "1013 AB Amsterdam",
            "code": "LOC-2026-001",
            "provision": "Grondwatermonitoring",
            "object": "Peilbuis PB-01"
        },
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
SECTION_HEADER_HEIGHT = 22.0
FIELD_ROW_HEIGHT = 16.0
SECTION_GAP = 14.0
DOUBLE_LINE_GAP = 2.7
PHOTO_HEIGHT = 300.0
PHOTO_TOP_MARGIN = 16.0
PLACEHOLDER_HEIGHT = 60.0
BOTTOM_PADDING = 8.0

# Label column width (fraction of available_width)
LABEL_COL_FRAC = 0.35
LABEL_INDENT = 4.0

# Fields voor client sectie
CLIENT_FIELDS = [
    ("name", "Naam"),
    ("address", "Adres"),
    ("city", "Plaats"),
]

# Fields voor location sectie
LOCATION_FIELDS = [
    ("name", "Naam"),
    ("address", "Adres"),
    ("city", "Plaats"),
    ("code", "Locatiecode"),
    ("provision", "Voorziening"),
    ("object", "Object"),
]


class LocationDetailModule(ContentModule):
    """Locatie informatiepagina met opdrachtgever- en locatiegegevens.

    Toont twee secties (opdrachtgever + locatie) met label-waarde paren,
    gevolgd door een optionele foto.
    """

    def _calculate_height(self) -> float:
        """Bereken totale hoogte op basis van secties en foto."""
        h = TITLE_HEIGHT

        # Client sectie
        client = self.data.get("client", {})
        if client:
            h += SECTION_HEADER_HEIGHT
            h += self._count_fields(client, CLIENT_FIELDS) * FIELD_ROW_HEIGHT
            h += SECTION_GAP

        # Location sectie
        location = self.data.get("location", {})
        if location:
            h += SECTION_HEADER_HEIGHT
            h += self._count_fields(location, LOCATION_FIELDS) * FIELD_ROW_HEIGHT
            h += SECTION_GAP

        # Foto
        photo_path = self.data.get("photo_path")
        if photo_path and Path(photo_path).is_file():
            h += PHOTO_TOP_MARGIN + PHOTO_HEIGHT
        else:
            h += PHOTO_TOP_MARGIN + PLACEHOLDER_HEIGHT

        h += BOTTOM_PADDING
        return h

    def draw(self) -> None:
        """Teken de locatie detail pagina op het canvas."""
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
        title = self.data.get("title", "Locatie")
        y -= TITLE_HEIGHT
        c.setFont(heading_font, cfg.heading_size)
        c.setFillColor(primary)
        c.drawString(0, y + 4, title)

        # -- Client sectie --
        client = self.data.get("client", {})
        if client:
            y = self._draw_section(
                c, y, w, client, CLIENT_FIELDS,
                heading_font, body_font,
                primary, secondary, text_color,
                label_right, value_x,
            )
            y -= SECTION_GAP

        # -- Location sectie --
        location = self.data.get("location", {})
        if location:
            y = self._draw_section(
                c, y, w, location, LOCATION_FIELDS,
                heading_font, body_font,
                primary, secondary, text_color,
                label_right, value_x,
            )
            y -= SECTION_GAP

        # -- Foto --
        y -= PHOTO_TOP_MARGIN
        photo_path = self.data.get("photo_path")
        if photo_path and Path(photo_path).is_file():
            self._draw_photo(c, y, w, photo_path)
        else:
            self._draw_placeholder(c, y, w, body_font, text_color)

    def _draw_section(
        self,
        c,
        y: float,
        w: float,
        section_data: dict,
        field_defs: list[tuple[str, str]],
        heading_font: str,
        body_font: str,
        primary: HexColor,
        secondary: HexColor,
        text_color: HexColor,
        label_right: float,
        value_x: float,
    ) -> float:
        """Teken een sectie met header en label-waarde paren.

        Args:
            c: ReportLab canvas.
            y: Huidige y-positie (top).
            w: Beschikbare breedte.
            section_data: Dict met sectie gegevens.
            field_defs: Lijst van (key, label) tuples.
            heading_font: Font voor sectie-header.
            body_font: Font voor veldwaarden.
            primary: Primaire kleur (lijnen).
            secondary: Secundaire kleur (labels).
            text_color: Tekstkleur (waarden).
            label_right: Rechterrand van label-kolom.
            value_x: Start x van waarde-kolom.

        Returns:
            Nieuwe y-positie na de sectie.
        """
        cfg = self.config

        # Sectie-header (bruin, bold, met dubbele blauwe lijn)
        y -= SECTION_HEADER_HEIGHT
        section_title = section_data.get("section_title", "")
        c.setFont(heading_font, cfg.label_size)
        c.setFillColor(secondary)
        c.drawString(0, y + 6, section_title)

        # Dubbele blauwe lijn
        c.setStrokeColor(primary)
        c.setLineWidth(cfg.line_width)
        c.line(0, y, w, y)
        c.line(0, y - DOUBLE_LINE_GAP, w, y - DOUBLE_LINE_GAP)

        # Velden
        for key, label in field_defs:
            value = section_data.get(key, "")
            if not value:
                continue
            y -= FIELD_ROW_HEIGHT
            # Label (bruin)
            c.setFont(body_font, cfg.label_size)
            c.setFillColor(secondary)
            c.drawString(LABEL_INDENT, y + 4, label)
            # Waarde (zwart)
            c.setFillColor(text_color)
            c.drawString(value_x, y + 4, str(value))

        return y

    def _draw_photo(
        self,
        c,
        y: float,
        w: float,
        photo_path: str,
    ) -> None:
        """Teken een foto gecentreerd op de pagina.

        Args:
            c: ReportLab canvas.
            y: Y-positie (bovenkant van foto-area).
            w: Beschikbare breedte.
            photo_path: Pad naar de afbeelding.
        """
        try:
            img = ImageReader(photo_path)
            img_w, img_h = img.getSize()
            # Schaal zodat foto past binnen beschikbare breedte en max hoogte
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
            # Fallback bij ongeldige afbeelding
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
        # Grijze rechthoek
        c.setStrokeColor(HexColor("#CCCCCC"))
        c.setFillColor(HexColor("#F5F5F5"))
        c.setLineWidth(0.5)
        c.rect(0, y - PLACEHOLDER_HEIGHT, w, PLACEHOLDER_HEIGHT, fill=1)

        # Placeholder tekst
        c.setFont(font, 9)
        c.setFillColor(color)
        c.drawCentredString(
            w / 2, y - PLACEHOLDER_HEIGHT / 2 - 3,
            "[LOCATIEFOTO]",
        )

    @staticmethod
    def _count_fields(section_data: dict, field_defs: list[tuple[str, str]]) -> int:
        """Tel het aantal niet-lege velden in een sectie.

        Args:
            section_data: Dict met sectie gegevens.
            field_defs: Lijst van (key, label) tuples.

        Returns:
            Aantal velden met waarde.
        """
        return sum(1 for key, _ in field_defs if section_data.get(key))
