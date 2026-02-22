"""Fonts module — Registreer custom fonts (Gotham) voor ReportLab.

Zoekt naar Gotham TTF/OTF bestanden in assets/fonts/.
Als ze beschikbaar zijn, worden ze geregistreerd in ReportLab's pdfmetrics.
Bij ontbrekende bestanden valt de module terug op Helvetica (graceful fallback).

Font bestanden die verwacht worden in assets/fonts/:
    - Gotham-Bold.ttf of Gotham-Bold.otf
    - Gotham-Book.ttf of Gotham-Book.otf
    - Gotham-Medium.ttf of Gotham-Medium.otf
    - Gotham-BookItalic.ttf of Gotham-BookItalic.otf

TODO: Plaats de Gotham TTF/OTF bestanden in:
    src/bm_reports/assets/fonts/
om de 3BM huisstijl fonts te activeren.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Standaard locatie van font bestanden binnen het package
FONTS_DIR = Path(__file__).parent.parent / "assets" / "fonts"

# Mapping van ReportLab font naam → mogelijke bestandsnamen (meerdere varianten)
_FONT_CANDIDATES: dict[str, list[str]] = {
    "GothamBold": [
        "Gotham-Bold.ttf",
        "Gotham-Bold.otf",
        "GothamBold.ttf",
        "GothamBold.otf",
        "Gotham Bold.ttf",
    ],
    "GothamBook": [
        "Gotham-Book.ttf",
        "Gotham-Book.otf",
        "GothamBook.ttf",
        "GothamBook.otf",
        "Gotham Book.ttf",
    ],
    "GothamMedium": [
        "Gotham-Medium.ttf",
        "Gotham-Medium.otf",
        "GothamMedium.ttf",
        "GothamMedium.otf",
        "Gotham Medium.ttf",
    ],
    "GothamBookItalic": [
        "Gotham-BookItalic.ttf",
        "Gotham-BookItalic.otf",
        "GothamBookItalic.ttf",
        "Gotham-Book-Italic.ttf",
        "Gotham Book Italic.ttf",
    ],
}

# Fallback mapping: Gotham naam → Helvetica equivalent
_FALLBACK_FONTS: dict[str, str] = {
    "GothamBold": "Helvetica-Bold",
    "GothamBook": "Helvetica",
    "GothamMedium": "Helvetica",
    "GothamBookItalic": "Helvetica-Oblique",
}

# Globale staat: welke fonts zijn succesvol geregistreerd
_registered: dict[str, bool] = {}


def _find_font_file(font_name: str, fonts_dir: Path) -> Path | None:
    """Zoek een font bestand in de fonts directory.

    Probeert alle kandidaat bestandsnamen voor een font.

    Args:
        font_name: ReportLab font naam (bijv. 'GothamBold').
        fonts_dir: Directory om in te zoeken.

    Returns:
        Path naar het gevonden font bestand, of None als niet gevonden.
    """
    candidates = _FONT_CANDIDATES.get(font_name, [])
    for candidate in candidates:
        path = fonts_dir / candidate
        if path.exists():
            return path
    return None


def register_fonts(fonts_dir: Path | None = None) -> dict[str, str]:
    """Registreer Gotham fonts in ReportLab.

    Zoekt naar font bestanden in de opgegeven directory.
    Voor elke gevonden font registreert het ReportLab TTFont.
    Voor ontbrekende fonts wordt de Helvetica fallback gebruikt.

    Args:
        fonts_dir: Directory met font bestanden. Standaard: assets/fonts/.

    Returns:
        Dict van font naam → geregistreerde naam (Gotham of Helvetica fallback).
        Bijv. {"GothamBold": "GothamBold"} als gevonden,
              {"GothamBold": "Helvetica-Bold"} als fallback.
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    search_dir = fonts_dir or FONTS_DIR
    result: dict[str, str] = {}

    for font_name in _FONT_CANDIDATES:
        if font_name in _registered and _registered[font_name]:
            # Al succesvol geregistreerd — cache hit
            result[font_name] = font_name
            continue

        # Als een custom fonts_dir is opgegeven en font niet eerder geregistreerd,
        # probeer opnieuw (tenant dir kan andere fonts hebben)
        if font_name in _registered and not _registered[font_name] and fonts_dir is None:
            result[font_name] = _FALLBACK_FONTS[font_name]
            continue

        font_path = _find_font_file(font_name, search_dir)

        if font_path is not None:
            try:
                pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
                _registered[font_name] = True
                result[font_name] = font_name
                logger.info("Font geregistreerd: %s (%s)", font_name, font_path.name)
            except (OSError, ValueError):
                logger.exception("Fout bij registreren van font %s: %s", font_name, font_path)
                _registered[font_name] = False
                result[font_name] = _FALLBACK_FONTS[font_name]
        else:
            _registered[font_name] = False
            result[font_name] = _FALLBACK_FONTS[font_name]
            logger.debug(
                "Font niet gevonden: %s — fallback naar %s. Plaats het font in: %s",
                font_name,
                _FALLBACK_FONTS[font_name],
                search_dir,
            )

    return result


def get_font_name(gotham_name: str) -> str:
    """Geef de effectieve font naam voor gebruik in ReportLab.

    Als Gotham geregistreerd is, retourneer de Gotham naam.
    Anders retourneer de Helvetica fallback.

    Args:
        gotham_name: Gewenste Gotham font naam (bijv. 'GothamBold').

    Returns:
        Effectieve font naam voor ReportLab (Gotham of Helvetica fallback).
    """
    if _registered.get(gotham_name, False):
        return gotham_name
    return _FALLBACK_FONTS.get(gotham_name, "Helvetica")


def gotham_available() -> bool:
    """Controleer of minstens één Gotham font beschikbaar is.

    Returns:
        True als een of meer Gotham fonts geregistreerd zijn.
    """
    return any(_registered.values())


def fonts_status() -> dict[str, str]:
    """Geef de status van alle fonts terug.

    Returns:
        Dict met font naam → 'registered' of 'fallback: <font>'.
    """
    status = {}
    for font_name in _FONT_CANDIDATES:
        if _registered.get(font_name, False):
            status[font_name] = "registered"
        else:
            fallback = _FALLBACK_FONTS.get(font_name, "Helvetica")
            status[font_name] = f"fallback: {fallback}"
    return status
