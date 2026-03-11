"""Fonts module — Registreer custom en fallback fonts voor ReportLab.

Zoekt naar Gotham TTF/OTF bestanden in assets/fonts/.
Als ze beschikbaar zijn, worden ze geregistreerd in ReportLab's pdfmetrics.

Bij ontbrekende custom fonts valt de module terug op Liberation Sans — een
open-source TTF font dat altijd EMBEDDED wordt in de PDF. Dit vervangt de
oude Helvetica fallback (Type1 referentie, nooit embedded).

Bundled fonts (altijd beschikbaar):
    - LiberationSans-Regular.ttf    (vervangt Helvetica)
    - LiberationSans-Bold.ttf       (vervangt Helvetica-Bold)
    - LiberationSans-Italic.ttf     (vervangt Helvetica-Oblique)
    - LiberationSans-BoldItalic.ttf (vervangt Helvetica-BoldOblique)
    - LiberationMono-Regular.ttf    (vervangt Courier)

Custom fonts (optioneel):
    - Gotham-Bold.ttf / .otf
    - Gotham-Book.ttf / .otf
    - Gotham-Medium.ttf / .otf
    - Gotham-BookItalic.ttf / .otf
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Standaard locatie van font bestanden binnen het package
FONTS_DIR = Path(__file__).parent.parent / "assets" / "fonts"

# ---------------------------------------------------------------------------
# Liberation Sans — embedded fallback fonts (bundled, Apache 2.0)
# ---------------------------------------------------------------------------

_LIBERATION_FONTS: dict[str, str] = {
    "LiberationSans": "LiberationSans-Regular.ttf",
    "LiberationSans-Bold": "LiberationSans-Bold.ttf",
    "LiberationSans-Italic": "LiberationSans-Italic.ttf",
    "LiberationSans-BoldItalic": "LiberationSans-BoldItalic.ttf",
    "LiberationMono": "LiberationMono-Regular.ttf",
}

# Mapping: Helvetica (Type1, nooit embedded) → Liberation Sans (TTF, altijd embedded)
_HELVETICA_TO_LIBERATION: dict[str, str] = {
    "Helvetica": "LiberationSans",
    "Helvetica-Bold": "LiberationSans-Bold",
    "Helvetica-Oblique": "LiberationSans-Italic",
    "Helvetica-BoldOblique": "LiberationSans-BoldItalic",
    "Courier": "LiberationMono",
}

# ---------------------------------------------------------------------------
# Gotham — custom 3BM fonts
# ---------------------------------------------------------------------------

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

# Fallback mapping: Gotham naam → Liberation Sans equivalent (was: Helvetica)
_FALLBACK_FONTS: dict[str, str] = {
    "GothamBold": "LiberationSans-Bold",
    "GothamBook": "LiberationSans",
    "GothamMedium": "LiberationSans",
    "GothamBookItalic": "LiberationSans-Italic",
}

# Globale staat: welke fonts zijn succesvol geregistreerd
_registered: dict[str, bool] = {}

# Vlag: Liberation Sans registratie al uitgevoerd
_liberation_registered: bool = False


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


def register_liberation_fonts(fonts_dir: Path | None = None) -> None:
    """Registreer Liberation Sans fonts als embedded fallback.

    Deze fonts worden altijd geregistreerd bij eerste aanroep.
    Ze zijn gebundeld in het package en worden embedded in elke PDF.

    Args:
        fonts_dir: Directory met font bestanden. Standaard: assets/fonts/.
    """
    global _liberation_registered
    if _liberation_registered:
        return

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    search_dir = fonts_dir or FONTS_DIR

    for font_name, filename in _LIBERATION_FONTS.items():
        if _registered.get(font_name, False):
            continue

        font_path = search_dir / filename
        if font_path.exists():
            try:
                pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
                _registered[font_name] = True
                logger.info("Liberation font geregistreerd: %s", font_name)
            except (OSError, ValueError):
                logger.exception("Fout bij registreren Liberation font %s", font_name)
                _registered[font_name] = False
        else:
            logger.warning(
                "Liberation font niet gevonden: %s → %s (verwacht in %s)",
                font_name,
                filename,
                search_dir,
            )
            _registered[font_name] = False

    _liberation_registered = True


def register_fonts(fonts_dir: Path | None = None) -> dict[str, str]:
    """Registreer Gotham fonts + Liberation Sans fallback in ReportLab.

    Registreert eerst Liberation Sans (altijd, als embedded fallback).
    Zoekt daarna naar Gotham font bestanden in de opgegeven directory.
    Voor ontbrekende Gotham fonts wordt Liberation Sans als fallback gebruikt.

    Args:
        fonts_dir: Directory met font bestanden. Standaard: assets/fonts/.

    Returns:
        Dict van font naam → geregistreerde naam (Gotham of Liberation fallback).
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Altijd eerst Liberation Sans registreren als embedded fallback
    register_liberation_fonts(fonts_dir)

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


def register_tenant_fonts(font_files: dict[str, str], fonts_dir: Path) -> dict[str, str]:
    """Registreer tenant-specifieke fonts in ReportLab.

    Args:
        font_files: Mapping van ReportLab font naam naar bestandsnaam,
                    bijv. {"Arial": "arial.ttf", "Arial-Bold": "arialbd.ttf"}.
        fonts_dir: Directory met de font bestanden.

    Returns:
        Dict van font naam → geregistreerde naam.
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Zorg dat Liberation Sans beschikbaar is als ultieme fallback
    register_liberation_fonts()

    result: dict[str, str] = {}
    for font_name, filename in font_files.items():
        if font_name in _registered and _registered[font_name]:
            result[font_name] = font_name
            continue

        font_path = fonts_dir / filename
        if font_path.exists():
            try:
                pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
                _registered[font_name] = True
                result[font_name] = font_name
                logger.info("Tenant font geregistreerd: %s (%s)", font_name, font_path.name)
            except (OSError, ValueError):
                logger.exception("Fout bij registreren van tenant font %s", font_name)
                result[font_name] = font_name  # val terug op letterlijke naam
        else:
            logger.warning("Tenant font niet gevonden: %s → %s", font_name, font_path)
            result[font_name] = font_name

    return result


def get_font_name(font_name: str) -> str:
    """Geef de effectieve font naam voor gebruik in ReportLab.

    Controleert of een font geregistreerd is (Gotham, tenant fonts, etc.).
    Onderschept Helvetica-varianten en vervangt ze door Liberation Sans
    zodat fonts altijd embedded worden in de PDF.

    Args:
        font_name: Gewenste font naam (bijv. 'GothamBold', 'Arial', 'Helvetica-Bold').

    Returns:
        Effectieve font naam voor ReportLab (altijd een embedded TTF font).
    """
    # Zorg dat Liberation Sans geregistreerd is
    register_liberation_fonts()

    # Tenant of custom font geregistreerd?
    if _registered.get(font_name, False):
        return font_name
    # Gotham fallback → Liberation Sans
    if font_name in _FALLBACK_FONTS:
        return _FALLBACK_FONTS[font_name]
    # Helvetica → Liberation Sans (kernfix voor font embedding)
    if font_name in _HELVETICA_TO_LIBERATION:
        return _HELVETICA_TO_LIBERATION[font_name]
    # Letterlijke naam (voor andere geregistreerde fonts)
    return font_name


def get_liberation_font_path(variant: str = "regular") -> Path | None:
    """Geef het pad naar een Liberation Sans font bestand.

    Handig voor PyMuPDF (fitz) die een fontfile pad nodig heeft.

    Args:
        variant: 'regular', 'bold', 'italic', of 'bolditalic'.

    Returns:
        Path naar het TTF bestand, of None als niet gevonden.
    """
    mapping = {
        "regular": "LiberationSans-Regular.ttf",
        "bold": "LiberationSans-Bold.ttf",
        "italic": "LiberationSans-Italic.ttf",
        "bolditalic": "LiberationSans-BoldItalic.ttf",
        "mono": "LiberationMono-Regular.ttf",
    }
    filename = mapping.get(variant)
    if not filename:
        return None
    path = FONTS_DIR / filename
    return path if path.exists() else None


def gotham_available() -> bool:
    """Controleer of minstens één Gotham font beschikbaar is.

    Returns:
        True als een of meer Gotham fonts geregistreerd zijn.
    """
    return any(
        _registered.get(name, False) for name in _FONT_CANDIDATES
    )


def fonts_status() -> dict[str, str]:
    """Geef de status van alle fonts terug.

    Returns:
        Dict met font naam → 'registered' of 'fallback: <font>'.
    """
    status = {}
    # Liberation Sans
    for font_name in _LIBERATION_FONTS:
        if _registered.get(font_name, False):
            status[font_name] = "registered (embedded fallback)"
        else:
            status[font_name] = "NOT registered"
    # Gotham
    for font_name in _FONT_CANDIDATES:
        if _registered.get(font_name, False):
            status[font_name] = "registered"
        else:
            fallback = _FALLBACK_FONTS.get(font_name, "LiberationSans")
            status[font_name] = f"fallback: {fallback}"
    return status
