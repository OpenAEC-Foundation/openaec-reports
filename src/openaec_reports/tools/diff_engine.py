"""Stationery diff engine — vergelijk reference met stationery PDF.

Detecteert dynamische velden (tekst aanwezig in reference maar niet in
stationery), kleuren, fonts en genereert diff images met rode overlay boxes.

Gebruikt ``pdf_extractor`` voor text extractie en PyMuPDF voor rendering.

Usage::

    result = run_diff(
        reference_pdf=Path("cover_reference.pdf"),
        stationery_pdf=Path("cover_stationery.pdf"),
        output_dir=Path("/tmp/output"),
        page_type="cover",
    )
    for field in result.fields:
        print(f"{field.sample_text} @ ({field.x_pt}, {field.y_pt})")
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import fitz
except ImportError:
    fitz = None  # type: ignore[assignment]

from openaec_reports.tools.pdf_extractor import TextElement, extract_pdf  # noqa: E402

# Render DPI voor preview/diff images
_DEFAULT_DPI = 150

# Heuristiek thresholds voor suggest_role
_TITLE_MIN_SIZE = 14.0
_DATE_PATTERN = re.compile(
    r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}"
    r"|[A-Za-z]+ \d{4}"
    r"|\d{4}-\d{2}-\d{2}"
    r"|\[.*datum.*\]",
    re.IGNORECASE,
)
_CONTACT_PATTERN = re.compile(
    r"@|tel[.:]\s*|telefoon|phone|\+\d{2}|www\.|http",
    re.IGNORECASE,
)
_PLACEHOLDER_PATTERN = re.compile(r"\[([A-Z_]+)\]")
_PAGE_NUM_PATTERN = re.compile(r"^\d{1,3}$|pagina|page", re.IGNORECASE)


@dataclass
class DetectedField:
    """Een dynamisch veld gedetecteerd door de diff.

    Attrs:
        id: Uniek veld ID.
        sample_text: Tekst uit de reference PDF.
        x_pt: X-positie in points (PDF origin).
        y_pt: Y-positie in points (top-down).
        width_pt: Breedte in points.
        height_pt: Hoogte in points.
        font: Font naam.
        font_size: Font grootte in points.
        color_hex: Kleur als hex string.
        suggested_role: Automatisch gesuggereerde semantische rol.
        role: Handmatig toegewezen rol (door gebruiker).
        name: Handmatig toegewezen veldnaam (door gebruiker).
    """

    id: str
    sample_text: str
    x_pt: float
    y_pt: float
    width_pt: float
    height_pt: float
    font: str
    font_size: float
    color_hex: str
    suggested_role: str | None = None
    role: str | None = None
    name: str | None = None


@dataclass
class DiffResult:
    """Resultaat van een reference vs stationery vergelijking.

    Attrs:
        page_type: Type pagina (cover, colofon, content, etc.).
        orientation: "portrait" of "landscape".
        width_pt: Pagina breedte in points.
        height_pt: Pagina hoogte in points.
        fields: Gedetecteerde dynamische velden.
        colors: Gevonden kleuren met frequentie.
        fonts: Gevonden fonts met frequentie en sizes.
        diff_image_path: Pad naar diff PNG.
        reference_image_path: Pad naar reference preview PNG.
        stationery_image_path: Pad naar stationery preview PNG.
    """

    page_type: str
    orientation: str
    width_pt: float
    height_pt: float
    fields: list[DetectedField] = field(default_factory=list)
    colors: list[dict] = field(default_factory=list)
    fonts: list[dict] = field(default_factory=list)
    diff_image_path: Path | None = None
    reference_image_path: Path | None = None
    stationery_image_path: Path | None = None


def run_diff(
    reference_pdf: Path,
    stationery_pdf: Path,
    output_dir: Path,
    page_type: str = "unknown",
) -> DiffResult:
    """Vergelijk reference met stationery en detecteer dynamische velden.

    Extraheert tekst uit beide PDF's en vindt tekstelementen die in de
    reference staan maar niet in de stationery (= dynamische velden).

    Args:
        reference_pdf: PDF met placeholder tekst.
        stationery_pdf: Schone achtergrond PDF.
        output_dir: Map voor output images.
        page_type: Naam van het pagina-type.

    Returns:
        DiffResult met gedetecteerde velden, kleuren en fonts.

    Raises:
        ImportError: Als PyMuPDF niet beschikbaar is.
        FileNotFoundError: Als een PDF niet bestaat.
    """
    if fitz is None:
        raise ImportError("PyMuPDF nodig: pip install PyMuPDF")

    reference_pdf = Path(reference_pdf)
    stationery_pdf = Path(stationery_pdf)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Extraheer tekst uit beide PDF's (pagina 1)
    ref_pages = extract_pdf(reference_pdf)
    stat_pages = extract_pdf(stationery_pdf)

    if not ref_pages:
        raise ValueError(f"Reference PDF is leeg: {reference_pdf}")

    ref_page = ref_pages[0]
    stat_texts_set = _text_fingerprints(stat_pages[0].texts if stat_pages else [])

    # Detecteer dynamische velden (in reference maar niet in stationery)
    fields: list[DetectedField] = []
    color_counter: Counter[str] = Counter()
    font_counter: Counter[str] = Counter()
    font_sizes: dict[str, set[float]] = {}

    for text_elem in ref_page.texts:
        fingerprint = _make_fingerprint(text_elem)
        if fingerprint not in stat_texts_set:
            field_id = f"field_{len(fields) + 1:03d}"
            suggested = suggest_role(
                text_elem.text,
                text_elem.font,
                text_elem.size,
                text_elem.color_hex,
            )
            fields.append(
                DetectedField(
                    id=field_id,
                    sample_text=text_elem.text,
                    x_pt=round(text_elem.x, 1),
                    y_pt=round(text_elem.y_top, 1),
                    width_pt=round(text_elem.x2 - text_elem.x, 1),
                    height_pt=round(text_elem.y_bottom - text_elem.y_top, 1),
                    font=text_elem.font,
                    font_size=text_elem.size,
                    color_hex=text_elem.color_hex,
                    suggested_role=suggested,
                )
            )

        # Tel kleuren en fonts (van alle reference tekst)
        color_counter[text_elem.color_hex] += 1
        font_counter[text_elem.font] += 1
        if text_elem.font not in font_sizes:
            font_sizes[text_elem.font] = set()
        font_sizes[text_elem.font].add(text_elem.size)

    # Orientatie bepalen
    width_pt = ref_page.width_pt
    height_pt = ref_page.height_pt
    orientation = "landscape" if width_pt > height_pt else "portrait"

    # Genereer preview images
    ref_img_path = output_dir / f"{page_type}_reference.png"
    stat_img_path = output_dir / f"{page_type}_stationery.png"
    diff_img_path = output_dir / f"{page_type}_diff.png"

    _render_page_to_png(reference_pdf, ref_img_path)
    _render_page_to_png(stationery_pdf, stat_img_path)
    generate_diff_image(reference_pdf, fields, diff_img_path)

    # Kleuren samenvatting
    colors = [
        {"hex": hex_val, "count": count}
        for hex_val, count in color_counter.most_common()
    ]

    # Fonts samenvatting
    fonts = [
        {
            "name": font_name,
            "count": count,
            "sizes": sorted(font_sizes.get(font_name, set())),
        }
        for font_name, count in font_counter.most_common()
    ]

    return DiffResult(
        page_type=page_type,
        orientation=orientation,
        width_pt=round(width_pt, 2),
        height_pt=round(height_pt, 2),
        fields=fields,
        colors=colors,
        fonts=fonts,
        diff_image_path=diff_img_path,
        reference_image_path=ref_img_path,
        stationery_image_path=stat_img_path,
    )


def generate_diff_image(
    reference_pdf: Path,
    fields: list[DetectedField],
    output_path: Path,
    dpi: int = _DEFAULT_DPI,
) -> Path:
    """Genereer PNG van reference met rode overlay boxes om dynamische velden.

    Args:
        reference_pdf: De reference PDF.
        fields: Gedetecteerde velden om te markeren.
        output_path: Pad voor output PNG.
        dpi: Render resolutie.

    Returns:
        Pad naar gegenereerde PNG.
    """
    if fitz is None:
        raise ImportError("PyMuPDF nodig: pip install PyMuPDF")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(reference_pdf))
    page = doc[0]

    # Teken rode boxes om gedetecteerde velden
    for fld in fields:
        rect = fitz.Rect(
            fld.x_pt,
            fld.y_pt,
            fld.x_pt + fld.width_pt,
            fld.y_pt + fld.height_pt,
        )
        # Rode outline (2pt dik)
        page.draw_rect(rect, color=(1, 0, 0), width=2)

    # Render naar PNG
    pix = page.get_pixmap(dpi=dpi)
    pix.save(str(output_path))
    doc.close()

    return output_path


def suggest_role(
    text: str,
    font: str,
    size: float,
    color: str,
) -> str | None:
    """Suggereer een semantische rol op basis van tekst en styling.

    Heuristieken:
    - Tekst bevat [PLACEHOLDER] → parse placeholder naam.
    - Groot + bold = title.
    - Datum-achtig formaat = date.
    - Email/telefoon patronen = contact.
    - Paginanummer patroon = page_number.

    Args:
        text: De tekst van het veld.
        font: Font naam.
        size: Font grootte.
        color: Hex kleur.

    Returns:
        Gesuggereerde rol, of None.
    """
    text_lower = text.lower().strip()

    # Placeholder patronen
    match = _PLACEHOLDER_PATTERN.search(text)
    if match:
        placeholder = match.group(1).lower()
        role_map = {
            # Cover
            "title": "title",
            "titel": "title",
            "factuurkop": "title",
            "subtitle": "subtitle",
            "subtitel": "subtitle",
            "ondertitel": "subtitle",
            "rapporttype": "report_type",
            "type": "report_type",
            "tagline": "tagline",
            # Document
            "datum": "date",
            "date": "date",
            "project": "project_name",
            "projectnaam": "project_name",
            "projectnummer": "project_number",
            "documentnummer": "document_number",
            "kenmerk": "kenmerk",
            "versie": "version",
            "status": "status",
            "fase": "fase",
            # Personen
            "klant": "client",
            "opdrachtgever": "client",
            "contactpersoon": "client_contact",
            "auteur": "author",
            "adviseur": "author",
            "bedrijf": "company_name",
            "bedrijfsnaam": "company_name",
            # Locatie
            "locatie": "location",
            "locatiecode": "location_code",
            "adres": "address",
            # Pagina-elementen
            "paginanummer": "page_number",
            "disclaimer": "disclaimer",
            "footer": "footer_text",
        }
        for key, role in role_map.items():
            if key in placeholder:
                return role

    # Datum patroon
    if _DATE_PATTERN.search(text):
        return "date"

    # Contact patroon
    if _CONTACT_PATTERN.search(text):
        return "contact"

    # Paginanummer
    if _PAGE_NUM_PATTERN.match(text_lower):
        return "page_number"

    # Groot + bold = title
    is_bold = "bold" in font.lower() or "heavy" in font.lower()
    if size >= _TITLE_MIN_SIZE and is_bold:
        return "title"

    # Wit op donker = overlay tekst
    if color.upper() == "#FFFFFF":
        return "overlay_text"

    return None


def _text_fingerprints(texts: list[TextElement]) -> set[str]:
    """Maak een set van text fingerprints voor snelle vergelijking."""
    return {_make_fingerprint(t) for t in texts}


def _make_fingerprint(text_elem: TextElement) -> str:
    """Maak een fingerprint van een tekstelement (tekst + positie).

    Gebruikt afgeronde posities om kleine rendering-verschillen te tolereren.
    """
    return (
        f"{text_elem.text}|"
        f"{round(text_elem.x, 0)}|"
        f"{round(text_elem.y_top, 0)}|"
        f"{text_elem.font}|"
        f"{text_elem.size}"
    )


def _render_page_to_png(
    pdf_path: Path,
    output_path: Path,
    page_num: int = 0,
    dpi: int = _DEFAULT_DPI,
) -> Path:
    """Render een PDF pagina naar PNG.

    Args:
        pdf_path: Pad naar PDF.
        output_path: Pad voor output PNG.
        page_num: 0-based pagina index.
        dpi: Render resolutie.

    Returns:
        Pad naar gegenereerde PNG.
    """
    if fitz is None:
        raise ImportError("PyMuPDF nodig: pip install PyMuPDF")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    page = doc[page_num]
    pix = page.get_pixmap(dpi=dpi)
    pix.save(str(output_path))
    doc.close()

    return output_path
