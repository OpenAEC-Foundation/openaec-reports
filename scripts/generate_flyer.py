"""Genereer een A4 flyer voor het OpenAEC Reports platform."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

# -- Constanten --
PAGE_W, PAGE_H = A4
MARGIN = 20 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

# Kleuren
PRIMARY = HexColor("#40124A")
SECONDARY = HexColor("#38BDA0")
TEXT_DARK = HexColor("#2D1B33")
TEXT_LIGHT = HexColor("#6B5B73")
BG_LIGHT = HexColor("#F8F6F9")

# Fonts
FONTS_DIR = Path(__file__).parent.parent / "src" / "openaec_reports" / "assets" / "fonts"
OUTPUT_DIR = Path(__file__).parent.parent / "output"

FOOTER_H = 28 * mm


def _register_fonts() -> None:
    """Registreer Gotham fonts."""
    font_map = {
        "Gotham-Bold": "Gotham-Bold.ttf",
        "Gotham-Book": "Gotham-Book.ttf",
        "Gotham-Medium": "Gotham-Medium.ttf",
        "Gotham-BookItalic": "Gotham-BookItalic.ttf",
    }
    for name, filename in font_map.items():
        path = FONTS_DIR / filename
        if path.exists():
            pdfmetrics.registerFont(TTFont(name, str(path)))


def _draw_rounded_rect(
    c: Canvas, x: float, y: float, w: float, h: float, r: float, fill_color: Color
) -> None:
    """Teken een rounded rectangle."""
    c.saveState()
    c.setFillColor(fill_color)
    c.roundRect(x, y, w, h, r, fill=1, stroke=0)
    c.restoreState()


def generate_flyer(output_path: Path) -> Path:
    """Genereer de flyer PDF."""
    _register_fonts()

    c = Canvas(str(output_path), pagesize=A4)
    c.setTitle("OpenAEC Reports — Platform Flyer")
    c.setAuthor("OpenAEC Foundation")

    # ========================================
    # HEADER BAND — compact (90mm)
    # ========================================
    header_h = 88 * mm
    c.saveState()
    c.setFillColor(PRIMARY)
    c.rect(0, PAGE_H - header_h, PAGE_W, header_h, fill=1, stroke=0)

    # Accent lijn onderaan header
    c.setFillColor(SECONDARY)
    c.rect(0, PAGE_H - header_h, PAGE_W, 2.5, fill=1, stroke=0)

    # Decoratieve cirkels
    c.setFillColor(Color(1, 1, 1, alpha=0.035))
    c.circle(PAGE_W - 30 * mm, PAGE_H - 20 * mm, 70 * mm, fill=1, stroke=0)
    c.circle(-15 * mm, PAGE_H - header_h + 15 * mm, 50 * mm, fill=1, stroke=0)

    # Subtitel
    y = PAGE_H - 22 * mm
    c.setFillColor(SECONDARY)
    c.setFont("Gotham-Medium", 11)
    c.drawString(MARGIN, y, "OPEN SOURCE PLATFORM")

    # Titel
    y -= 13 * mm
    c.setFillColor(white)
    c.setFont("Gotham-Bold", 34)
    c.drawString(MARGIN, y, "OpenAEC Reports")

    # Ondertitel
    y -= 9 * mm
    c.setFont("Gotham-Book", 13)
    c.setFillColor(Color(1, 1, 1, alpha=0.85))
    c.drawString(MARGIN, y, "Professionele engineering rapporten, modulair opgebouwd")

    # 3 highlights
    y -= 16 * mm
    highlights = [
        ("PDF generatie", "JSON in, PDF uit"),
        ("Multi-tenant", "Huisstijl per organisatie"),
        ("Open source", "MIT licentie"),
    ]
    col_w = CONTENT_W / 3
    for i, (title, desc) in enumerate(highlights):
        fx = MARGIN + i * col_w
        c.setFillColor(SECONDARY)
        c.circle(fx + 4, y + 4, 2.5, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Gotham-Bold", 9.5)
        c.drawString(fx + 11, y, title)
        c.setFont("Gotham-Book", 8)
        c.setFillColor(Color(1, 1, 1, alpha=0.65))
        c.drawString(fx + 11, y - 11, desc)

    c.restoreState()

    # ========================================
    # HOE WERKT HET — 3 stappen
    # ========================================
    y = PAGE_H - header_h - 10 * mm
    c.setFillColor(TEXT_DARK)
    c.setFont("Gotham-Bold", 14)
    c.drawString(MARGIN, y, "Hoe werkt het?")

    y -= 5 * mm
    c.setFont("Gotham-Book", 8.5)
    c.setFillColor(TEXT_LIGHT)
    c.drawString(MARGIN, y, "In drie stappen van data naar professioneel rapport")

    y -= 12 * mm
    steps = [
        ("1", SECONDARY, "JSON data", "Vul rapportdata in via de\nweb-editor of lever JSON aan"),
        ("2", PRIMARY, "Template engine", "De engine combineert data met\nYAML templates en brand config"),
        ("3", HexColor("#2ECC71"), "PDF output", "Pixel-perfecte A4/A3 PDF\nklaar voor de klant"),
    ]

    step_w = (CONTENT_W - 12 * mm) / 3
    for i, (num, color, title, desc) in enumerate(steps):
        sx = MARGIN + i * (step_w + 6 * mm)

        # Nummer cirkel
        c.saveState()
        c.setFillColor(color)
        c.circle(sx + 12, y + 2, 10, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Gotham-Bold", 12)
        c.drawCentredString(sx + 12, y - 2, num)
        c.restoreState()

        # Pijl (getekend, niet unicode — Gotham mist arrow glyphs)
        if i < 2:
            arrow_x = sx + step_w + 1 * mm
            c.saveState()
            c.setStrokeColor(HexColor("#D1C4D6"))
            c.setFillColor(HexColor("#D1C4D6"))
            c.setLineWidth(1.5)
            shaft_y = y
            shaft_len = 5 * mm
            c.line(arrow_x - shaft_len / 2, shaft_y, arrow_x + shaft_len / 2, shaft_y)
            # Pijlpunt
            arrow_tip = arrow_x + shaft_len / 2
            p = c.beginPath()
            p.moveTo(arrow_tip, shaft_y)
            p.lineTo(arrow_tip - 3, shaft_y + 2.5)
            p.lineTo(arrow_tip - 3, shaft_y - 2.5)
            p.close()
            c.drawPath(p, fill=1, stroke=0)
            c.restoreState()

        # Titel
        c.setFillColor(TEXT_DARK)
        c.setFont("Gotham-Bold", 10)
        c.drawString(sx + 28, y, title)

        # Beschrijving
        c.setFillColor(TEXT_LIGHT)
        c.setFont("Gotham-Book", 8)
        for j, line in enumerate(desc.split("\n")):
            c.drawString(sx + 28, y - 12 - j * 10, line)

    # ========================================
    # FEATURES GRID — 2x3
    # ========================================
    y -= 34 * mm

    c.setFillColor(TEXT_DARK)
    c.setFont("Gotham-Bold", 14)
    c.drawString(MARGIN, y, "Features")
    y -= 10 * mm

    features = [
        ("YAML Templates", "Configureerbare rapport-templates\nper type en per klant"),
        ("Brand System", "Kleuren, fonts, logo's en stationery\nper tenant configureerbaar"),
        ("10+ Block Types", "Paragraaf, berekening, toetsing,\ntabel, afbeelding, kaart, ..."),
        ("REST API", "FastAPI backend: POST JSON,\nontvang PDF. Swagger docs"),
        ("Kadaster Integratie", "Automatische kaarten via\nPDOK WMS (gratis, geen key)"),
        ("Web Editor", "Visuele editor met drag & drop,\nundo/redo en live preview"),
    ]

    card_w = (CONTENT_W - 6 * mm) / 2
    card_h = 22 * mm
    card_r = 3

    for i, (title, desc) in enumerate(features):
        col = i % 2
        row = i // 2
        cx = MARGIN + col * (card_w + 6 * mm)
        cy = y - row * (card_h + 4 * mm)

        # Card
        _draw_rounded_rect(c, cx, cy - card_h + 6, card_w, card_h, card_r, BG_LIGHT)

        # Accent lijn links
        c.saveState()
        c.setFillColor(SECONDARY)
        c.roundRect(cx, cy - card_h + 6, 2.5, card_h, 1.5, fill=1, stroke=0)
        c.restoreState()

        # Titel
        c.setFillColor(TEXT_DARK)
        c.setFont("Gotham-Bold", 9.5)
        c.drawString(cx + 9, cy - 1, title)

        # Beschrijving
        c.setFillColor(TEXT_LIGHT)
        c.setFont("Gotham-Book", 7.5)
        for j, line in enumerate(desc.split("\n")):
            c.drawString(cx + 9, cy - 11 - j * 9.5, line)

    # ========================================
    # FOOTER — call to action
    # ========================================
    c.saveState()
    c.setFillColor(PRIMARY)
    c.rect(0, 0, PAGE_W, FOOTER_H, fill=1, stroke=0)

    # Accent lijn
    c.setFillColor(SECONDARY)
    c.rect(0, FOOTER_H - 2, PAGE_W, 2, fill=1, stroke=0)

    # Links
    c.setFillColor(white)
    c.setFont("Gotham-Bold", 11)
    c.drawString(MARGIN, FOOTER_H - 12 * mm, "Probeer het zelf")
    c.setFont("Gotham-Book", 8.5)
    c.setFillColor(Color(1, 1, 1, alpha=0.75))
    c.drawString(MARGIN, FOOTER_H - 18 * mm, "Open source onder MIT licentie")

    # Rechts
    rx = PAGE_W - MARGIN
    c.setFillColor(SECONDARY)
    c.setFont("Gotham-Medium", 9)
    c.drawRightString(rx, FOOTER_H - 12 * mm, "report.3bm.co.nl")
    c.setFillColor(Color(1, 1, 1, alpha=0.6))
    c.setFont("Gotham-Book", 7.5)
    c.drawRightString(rx, FOOTER_H - 18 * mm, "github.com/OpenAEC-Foundation/openaec-reports")

    c.restoreState()

    c.save()
    return output_path


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = generate_flyer(OUTPUT_DIR / "openaec_flyer.pdf")
    print(f"Flyer gegenereerd: {out}")
