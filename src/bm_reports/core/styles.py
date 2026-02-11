"""Huisstijl definities — kleuren, fonts, spacing, paragraph styles."""

from dataclasses import dataclass
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import StyleSheet1, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT


# ============================================================
# 3BM Huisstijl Kleuren
# ============================================================
# TODO: Vervang met daadwerkelijke 3BM huisstijl kleuren

@dataclass(frozen=True)
class Colors:
    """3BM Huisstijl kleurenpalet."""

    primary: str = "#1B3A5C"       # Donkerblauw
    secondary: str = "#4A90A4"     # Middenblauw
    accent: str = "#2ECC71"        # Groen (voldoet)
    warning: str = "#E74C3C"       # Rood (voldoet niet)
    text: str = "#2C3E50"          # Donkergrijs
    text_light: str = "#7F8C8D"    # Lichtgrijs
    background: str = "#FFFFFF"    # Wit
    background_alt: str = "#F8F9FA"  # Lichtgrijs achtergrond
    rule: str = "#BDC3C7"          # Lijn kleur

    def as_hex(self, name: str) -> HexColor:
        """Retourneer kleur als ReportLab HexColor."""
        return HexColor(getattr(self, name))


BM_COLORS = Colors()


# ============================================================
# Font Configuratie
# ============================================================
# TODO: Registreer custom fonts (bijv. eigen huisstijl font)

@dataclass(frozen=True)
class FontConfig:
    """Font configuratie."""

    heading: str = "Helvetica-Bold"
    body: str = "Helvetica"
    mono: str = "Courier"
    body_size: float = 9.0
    heading1_size: float = 16.0
    heading2_size: float = 13.0
    heading3_size: float = 11.0
    caption_size: float = 8.0
    footer_size: float = 7.5


BM_FONTS = FontConfig()


# ============================================================
# Stylesheet
# ============================================================

def create_stylesheet() -> StyleSheet1:
    """Maak de 3BM stylesheet met alle paragraph styles."""
    styles = StyleSheet1()

    styles.add(ParagraphStyle(
        name="Normal",
        fontName=BM_FONTS.body,
        fontSize=BM_FONTS.body_size,
        leading=BM_FONTS.body_size * 1.4,
        textColor=HexColor(BM_COLORS.text),
        alignment=TA_LEFT,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name="Heading1",
        parent=styles["Normal"],
        fontName=BM_FONTS.heading,
        fontSize=BM_FONTS.heading1_size,
        leading=BM_FONTS.heading1_size * 1.3,
        textColor=HexColor(BM_COLORS.primary),
        spaceBefore=12,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name="Heading2",
        parent=styles["Normal"],
        fontName=BM_FONTS.heading,
        fontSize=BM_FONTS.heading2_size,
        leading=BM_FONTS.heading2_size * 1.3,
        textColor=HexColor(BM_COLORS.primary),
        spaceBefore=10,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name="Heading3",
        parent=styles["Normal"],
        fontName=BM_FONTS.heading,
        fontSize=BM_FONTS.heading3_size,
        leading=BM_FONTS.heading3_size * 1.3,
        textColor=HexColor(BM_COLORS.secondary),
        spaceBefore=8,
        spaceAfter=3,
    ))

    styles.add(ParagraphStyle(
        name="Caption",
        parent=styles["Normal"],
        fontSize=BM_FONTS.caption_size,
        textColor=HexColor(BM_COLORS.text_light),
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name="Footer",
        parent=styles["Normal"],
        fontSize=BM_FONTS.footer_size,
        textColor=HexColor(BM_COLORS.text_light),
    ))

    styles.add(ParagraphStyle(
        name="CoverTitle",
        parent=styles["Normal"],
        fontName=BM_FONTS.heading,
        fontSize=28,
        leading=34,
        textColor=HexColor(BM_COLORS.primary),
        alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        name="CoverSubtitle",
        parent=styles["Normal"],
        fontName=BM_FONTS.body,
        fontSize=14,
        leading=18,
        textColor=HexColor(BM_COLORS.secondary),
        alignment=TA_LEFT,
    ))

    return styles


BM_STYLES = create_stylesheet()
