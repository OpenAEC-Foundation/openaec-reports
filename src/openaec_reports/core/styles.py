"""Huisstijl definities — kleuren, fonts, spacing, paragraph styles."""

from __future__ import annotations

import functools
from dataclasses import dataclass
from typing import TYPE_CHECKING

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle, StyleSheet1

from openaec_reports.core.fonts import get_font_name, register_fonts

if TYPE_CHECKING:
    from openaec_reports.core.brand import BrandConfig


@functools.cache
def _ensure_fonts_registered() -> None:
    """Registreer fonts eenmalig (lazy, bij eerste gebruik)."""
    register_fonts()


# ============================================================
# 3BM Huisstijl Kleuren
# ============================================================


@dataclass(frozen=True)
class Colors:
    """3BM Huisstijl kleurenpalet."""

    primary: str = "#40124A"  # Donkerpaars (3BM huisstijl)
    secondary: str = "#38BDA0"  # Turquoise (3BM huisstijl)
    accent: str = "#2ECC71"  # Groen (voldoet)
    warning: str = "#E74C3C"  # Rood (voldoet niet)
    text: str = "#45243D"  # Donkerpaars tekst
    text_accent: str = "#56B49B"  # H2/H3 headings, TOC level 1
    text_light: str = "#7F8C8D"  # Lichtgrijs
    background: str = "#FFFFFF"  # Wit
    background_alt: str = "#F8F9FA"  # Lichtgrijs achtergrond
    rule: str = "#BDC3C7"  # Lijn kleur
    table_header_bg: str = "#45233C"  # Tabel header achtergrond
    table_header_text: str = "#FFFFFF"  # Tabel header tekst
    table_footer_bg: str = "#55B49B"  # Tabel footer/totaal rij
    separator: str = "#E0D0E8"  # Scheidingslijnen

    def as_hex(self, name: str) -> HexColor:
        """Retourneer kleur als ReportLab HexColor.

        Args:
            name: Kleurnaam (bijv. 'primary', 'text_light').
        """
        return HexColor(getattr(self, name))

    # Alias voor backward compatibility
    hex = as_hex


BM_COLORS = Colors()

# Gedeelde padding constante voor content block componenten (in points)
BLOCK_PADDING = 6


# ============================================================
# Font Configuratie
# ============================================================


@dataclass(frozen=True)
class FontConfig:
    """Font configuratie.

    Gebruikt Gotham fonts als ze beschikbaar zijn in assets/fonts/.
    Valt automatisch terug op Helvetica als Gotham niet geïnstalleerd is.
    """

    heading: str = "GothamBold"  # Fallback: Helvetica-Bold
    body: str = "GothamBook"  # Fallback: Helvetica
    medium: str = "GothamMedium"  # Fallback: Helvetica
    italic: str = "GothamBookItalic"  # Fallback: Helvetica-Oblique
    mono: str = "Courier"
    body_size: float = 9.5
    heading1_size: float = 18.0
    heading2_size: float = 13.0
    heading3_size: float = 11.0
    caption_size: float = 8.0
    footer_size: float = 7.5


def _make_font_config() -> FontConfig:
    """Maak FontConfig met effectieve font namen (Gotham of Helvetica fallback)."""
    _ensure_fonts_registered()
    return FontConfig(
        heading=get_font_name("GothamBold"),
        body=get_font_name("GothamBook"),
        medium=get_font_name("GothamMedium"),
        italic=get_font_name("GothamBookItalic"),
    )


BM_FONTS = _make_font_config()


# ============================================================
# Stylesheet
# ============================================================


def create_stylesheet(brand: BrandConfig | None = None) -> StyleSheet1:
    """Maak de 3BM stylesheet, optioneel met brand-specifieke overrides.

    Args:
        brand: Optionele brand configuratie met style overrides.

    Returns:
        StyleSheet1 met alle paragraph styles.
    """
    styles = StyleSheet1()

    styles.add(
        ParagraphStyle(
            name="Normal",
            fontName=BM_FONTS.body,
            fontSize=BM_FONTS.body_size,
            leading=BM_FONTS.body_size * 1.4,
            textColor=HexColor(BM_COLORS.text),
            alignment=TA_LEFT,
            spaceAfter=4,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Heading1",
            parent=styles["Normal"],
            fontName=BM_FONTS.body,  # GothamBook, NIET Bold
            fontSize=BM_FONTS.heading1_size,
            leading=BM_FONTS.heading1_size * 1.3,
            textColor=HexColor(BM_COLORS.text),  # text kleur, NIET primary
            spaceBefore=12,
            spaceAfter=6,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Heading2",
            parent=styles["Normal"],
            fontName=BM_FONTS.body,  # GothamBook
            fontSize=BM_FONTS.heading2_size,
            leading=BM_FONTS.heading2_size * 1.3,
            textColor=HexColor(BM_COLORS.text_accent),  # turquoise
            spaceBefore=10,
            spaceAfter=4,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Heading3",
            parent=styles["Normal"],
            fontName=BM_FONTS.body,  # GothamBook
            fontSize=BM_FONTS.heading3_size,
            leading=BM_FONTS.heading3_size * 1.3,
            textColor=HexColor(BM_COLORS.text_accent),  # turquoise
            spaceBefore=8,
            spaceAfter=3,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Caption",
            parent=styles["Normal"],
            fontSize=BM_FONTS.caption_size,
            textColor=HexColor(BM_COLORS.text_light),
            alignment=TA_CENTER,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Footer",
            parent=styles["Normal"],
            fontSize=BM_FONTS.footer_size,
            textColor=HexColor(BM_COLORS.text_light),
        )
    )

    styles.add(
        ParagraphStyle(
            name="CoverTitle",
            parent=styles["Normal"],
            fontName=BM_FONTS.heading,
            fontSize=28,
            leading=34,
            textColor=HexColor(BM_COLORS.primary),
            alignment=TA_LEFT,
        )
    )

    styles.add(
        ParagraphStyle(
            name="CoverSubtitle",
            parent=styles["Normal"],
            fontName=BM_FONTS.body,
            fontSize=14,
            leading=18,
            textColor=HexColor(BM_COLORS.secondary),
            alignment=TA_LEFT,
        )
    )

    # Brand style overrides toepassen
    if brand and brand.styles:
        for style_name, overrides in brand.styles.items():
            if style_name in styles.byName:
                style = styles[style_name]
                for attr, value in overrides.items():
                    if attr == "textColor":
                        value = HexColor(value)
                    elif attr == "fontName":
                        value = get_font_name(value)
                    setattr(style, attr, value)

    return styles


BM_STYLES = create_stylesheet()


# ============================================================
# Gedeelde block styles (calculation / check_block)
# ============================================================


def block_style_reference() -> ParagraphStyle:
    """Referentie-stijl: klein, rechts uitgelijnd, lichtgrijs."""
    from reportlab.lib.enums import TA_RIGHT

    return ParagraphStyle(
        "_block_ref",
        parent=BM_STYLES["Normal"],
        fontSize=BM_FONTS.caption_size,
        leading=BM_FONTS.caption_size * 1.3,
        textColor=HexColor(BM_COLORS.text_light),
        alignment=TA_RIGHT,
        spaceAfter=0,
    )


def block_style_heading(text_color: str | None = None) -> ParagraphStyle:
    """Heading-stijl: bold, body size."""
    return ParagraphStyle(
        "_block_heading",
        parent=BM_STYLES["Normal"],
        fontName=BM_FONTS.heading,
        fontSize=BM_FONTS.body_size,
        leading=BM_FONTS.body_size * 1.3,
        textColor=HexColor(text_color or BM_COLORS.primary),
        spaceAfter=0,
    )


def block_style_body() -> ParagraphStyle:
    """Body-stijl: normaal, iets meer leading."""
    return ParagraphStyle(
        "_block_body",
        parent=BM_STYLES["Normal"],
        fontSize=BM_FONTS.body_size,
        leading=BM_FONTS.body_size * 1.4,
        spaceAfter=0,
    )


def block_style_mono() -> ParagraphStyle:
    """Monospace-stijl: Courier, body size."""
    return ParagraphStyle(
        "_block_mono",
        parent=BM_STYLES["Normal"],
        fontName=BM_FONTS.mono,
        fontSize=BM_FONTS.body_size,
        leading=BM_FONTS.body_size * 1.4,
        spaceAfter=0,
    )


def block_style_result(text_color: str | None = None) -> ParagraphStyle:
    """Resultaat-stijl: bold, iets groter, opvallend."""
    return ParagraphStyle(
        "_block_result",
        parent=BM_STYLES["Normal"],
        fontName=BM_FONTS.heading,
        fontSize=BM_FONTS.body_size + 1,
        leading=(BM_FONTS.body_size + 1) * 1.3,
        textColor=HexColor(text_color or BM_COLORS.primary),
        spaceAfter=0,
    )
