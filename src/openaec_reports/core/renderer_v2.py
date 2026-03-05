"""
Renderer V2 — PyMuPDF-based PDF report generator.

Accepts JSON data (conforming to report.schema.json) and generates
pixel-perfect PDF reports using YAML-driven templates and stationery overlays.

Architecture:
    JSON input → ReportGeneratorV2 → loads YAML templates → renders pages → PDF output

    Cover:      ReportLab canvas (3-layer: photo + PNG overlay + text)
    Colofon:    PyMuPDF insert_text on colofon.pdf stationery
    TOC:        PyMuPDF dynamic rendering on standaard.pdf
    Content:    PyMuPDF dynamic rendering on standaard.pdf (H1, H2, paragraph, bullets)
    Bijlage:    PyMuPDF insert_text on bijlagen.pdf stationery
    Achterblad: Static PDF insert
"""

from __future__ import annotations

import base64
import json
import logging
import re
import tempfile
from pathlib import Path
from typing import Any

import fitz
import yaml
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ASSETS_DIR = Path(__file__).parent.parent / "assets"
FONT_DIR = ASSETS_DIR / "fonts"
TEMPLATES_DIR = ASSETS_DIR / "templates"

# A4 page dimensions in points (1 pt = 1/72 inch)
A4_PORTRAIT_WIDTH = 595.28
A4_PORTRAIT_HEIGHT = 841.89
A4_LANDSCAPE_WIDTH = 841.89
A4_LANDSCAPE_HEIGHT = 595.28

# Maximum y coordinate for content (bottom boundary)
Y_MAX_PORTRAIT = 780.0
Y_MAX_LANDSCAPE = 533.0


def _hex_to_rgb(h: str) -> tuple[float, float, float]:
    """Convert hex color string to (r, g, b) tuple with 0-1 range."""
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))


_RE_HTML_TAG = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    """Strip HTML tags from text, preserving readable content."""
    if "<" not in text:
        return text
    clean = _RE_HTML_TAG.sub("", text)
    # Collapse whitespace from removed tags
    clean = re.sub(r"[ \t]+", " ", clean).strip()
    return clean


# ---------------------------------------------------------------------------
# Template Loader
# ---------------------------------------------------------------------------
class TemplateSet:
    """Loads and holds all YAML templates + stationery paths for a brand."""

    def __init__(self, brand: str = "3bm_cooperatie"):
        self.brand = brand
        self.dir = TEMPLATES_DIR / brand
        if not self.dir.exists():
            raise FileNotFoundError(f"Template directory not found: {self.dir}")

        self.cover = self._load("cover.yaml")
        self.colofon = self._load("colofon.yaml")
        self.toc = self._load("toc.yaml")
        self.standaard = self._load("standaard.yaml")
        self.content_styles = self._load("content_styles.yaml")
        self.bijlage = self._load("bijlage.yaml")

    def _load(self, filename: str) -> dict:
        path = self.dir / filename
        if not path.exists():
            logger.warning("Template not found: %s", path)
            return {}
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @property
    def blocks(self) -> dict:
        return self.content_styles.get("blocks", {})

    @property
    def page_number(self) -> dict:
        return self.content_styles.get("page_number", {})


# ---------------------------------------------------------------------------
# Font Manager
# ---------------------------------------------------------------------------
class FontManager:
    """Manages font registration for both ReportLab and PyMuPDF.

    Ondersteunt twee modi:
    - Custom fonts (Gotham): laad TTF bestanden uit font_dir
    - Standaard fonts (Helvetica, Arial): gebruik fitz ingebouwde fonts
    """

    _DEFAULT_FONT_MAP = {
        "GothamBold": "Gotham-Bold.ttf",
        "GothamBook": "Gotham-Book.ttf",
        "GothamMedium": "Gotham-Medium.ttf",
    }

    _BUILTIN_FONTS = {
        "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique",
        "Courier", "Courier-Bold", "Courier-Oblique", "Courier-BoldOblique",
        "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic",
        "Symbol", "ZapfDingbats",
        "Arial", "ArialMT", "Arial-BoldMT",
    }

    def __init__(self, font_dir: Path | None = None, brand_fonts: dict | None = None):
        self.font_dir = font_dir or FONT_DIR
        self._rl_registered = False
        self._fitz_fonts: dict[str, fitz.Font] = {}
        self._uses_custom_fonts = True

        # Bepaal of we custom fonts of builtin fonts gebruiken
        if brand_fonts:
            heading = brand_fonts.get("heading", "")
            body = brand_fonts.get("body", "")
            heading_fb = brand_fonts.get("heading_fallback", heading)
            body_fb = brand_fonts.get("body_fallback", body)
            if self._is_builtin(heading or heading_fb) and self._is_builtin(body or body_fb):
                self._uses_custom_fonts = False

        if self._uses_custom_fonts:
            self.FONT_MAP = dict(self._DEFAULT_FONT_MAP)
            for name, filename in self.FONT_MAP.items():
                path = self.font_dir / filename
                if path.exists():
                    self._fitz_fonts[name] = fitz.Font(fontfile=str(path))
            self._bold_font = self._fitz_fonts.get("GothamBold") or fitz.Font("helv")
            self._book_font = self._fitz_fonts.get("GothamBook") or fitz.Font("helv")
        else:
            self.FONT_MAP = {}
            self._bold_font = fitz.Font("helv")
            self._book_font = fitz.Font("helv")

    @property
    def gotham_book(self) -> fitz.Font:
        """Backward compatibility alias."""
        return self._book_font

    @property
    def gotham_bold(self) -> fitz.Font:
        """Backward compatibility alias."""
        return self._bold_font

    @classmethod
    def _is_builtin(cls, fontname: str) -> bool:
        """Check of een fontnaam een ingebouwde PDF font is."""
        return (
            fontname in cls._BUILTIN_FONTS
            or fontname.startswith("Helvetica")
            or fontname.startswith("Arial")
        )

    def register_reportlab(self) -> None:
        """Register fonts with ReportLab (once)."""
        if self._rl_registered:
            return
        for name, filename in self.FONT_MAP.items():
            path = self.font_dir / filename
            if path.exists():
                try:
                    pdfmetrics.registerFont(TTFont(name, str(path)))
                except (OSError, ValueError):
                    logger.warning("Could not register font: %s", name)
        self._rl_registered = True

    def insert_into_page(self, page: fitz.Page) -> None:
        """Insert custom fonts into a PyMuPDF page."""
        if not self._uses_custom_fonts:
            return
        for name, filename in self.FONT_MAP.items():
            path = self.font_dir / filename
            if path.exists():
                page.insert_font(fontname=name, fontfile=str(path))

    def get_fitz_font(self, fontname: str) -> fitz.Font:
        """Return fitz.Font object for given fontname string."""
        if fontname in self._fitz_fonts:
            return self._fitz_fonts[fontname]
        is_bold = "bold" in fontname.lower() or "Bold" in fontname
        return self._bold_font if is_bold else self._book_font

    def measure(self, text: str, fontsize: float, bold: bool = False) -> float:
        """Measure text width using font metrics."""
        font = self._bold_font if bold else self._book_font
        return font.text_length(text, fontsize=fontsize)

    def wrap_text(
        self, text: str, fontsize: float, max_width: float, bold: bool = False
    ) -> list[str]:
        """Word-wrap text to fit within max_width.

        Splits on spaces first, then on underscores/hyphens for long tokens,
        and finally breaks mid-character as last resort.
        """
        if not text:
            return [""]
        if max_width <= 0:
            return [text]

        # First split on spaces
        tokens = text.split()
        lines: list[str] = []
        current = ""

        for token in tokens:
            test = f"{current} {token}".strip()
            if self.measure(test, fontsize, bold) <= max_width:
                current = test
                continue

            # Token doesn't fit on current line
            if current:
                lines.append(current)
                current = ""

            # Check if single token fits on a fresh line
            if self.measure(token, fontsize, bold) <= max_width:
                current = token
                continue

            # Token too wide — split on underscores/hyphens first
            sub_parts = re.split(r"(?<=[_\-/.])", token)  # keep delimiter at end of part
            for sp in sub_parts:
                if not sp:
                    continue
                test = f"{current}{sp}" if current else sp
                if self.measure(test, fontsize, bold) <= max_width:
                    current = test
                else:
                    if current:
                        lines.append(current)
                    # If sub-part itself is too wide, break by character
                    if self.measure(sp, fontsize, bold) > max_width:
                        current = ""
                        for ch in sp:
                            test_ch = current + ch
                            if self.measure(test_ch, fontsize, bold) > max_width and current:
                                lines.append(current)
                                current = ch
                            else:
                                current = test_ch
                    else:
                        current = sp

        if current:
            lines.append(current)
        return lines if lines else [""]


# ---------------------------------------------------------------------------
# Shared image resolver
# ---------------------------------------------------------------------------


def _resolve_image(src) -> Path | None:
    """Resolve image source: file path, base64 dict, or None."""
    if not src:
        return None

    if isinstance(src, dict):
        # Base64 encoded image
        data = src.get("data", "")
        media_type = src.get("media_type", "image/png")
        ext = ".png" if "png" in media_type else ".jpg"
        try:
            raw = base64.b64decode(data)
            tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
            tmp.write(raw)
            tmp.close()
            return Path(tmp.name)
        except (ValueError, OSError) as e:
            logger.warning("Base64 decode failed: %s", e)
            return None

    # File path
    p = Path(src)
    if p.exists():
        return p
    return None


# ---------------------------------------------------------------------------
# Cover Generator (ReportLab)
# ---------------------------------------------------------------------------
class CoverGenerator:
    """Generates cover page using ReportLab 3-layer approach."""

    def __init__(self, templates: TemplateSet, fonts: FontManager):
        self.tpl = templates.cover
        self.fonts = fonts

    def generate(
        self, data: dict, stationery: Path | None, output: Path, cover_is_pdf: bool = False,
    ) -> Path:
        """Generate cover PDF.

        Twee modi:
        - PNG overlay (3BM): ReportLab canvas met foto + PNG overlay + tekst
        - PDF stationery (Symitech): PyMuPDF insert tekst op PDF stationery
        """
        if cover_is_pdf and stationery and stationery.exists():
            return self._generate_from_pdf(data, stationery, output)
        return self._generate_from_png(data, stationery, output)

    def _generate_from_pdf(self, data: dict, stationery_pdf: Path, output: Path) -> Path:
        """Cover via PyMuPDF: tekst op PDF stationery."""
        doc = fitz.open(str(stationery_pdf))
        page = doc[0]
        self.fonts.insert_into_page(page)

        fields = self.tpl.get("dynamic_fields", {})

        # Rapport type
        tf = fields.get("rapport_type", {})
        title_text = data.get("report_type", "")
        if title_text:
            font_obj = self.fonts.get_fitz_font(tf.get("font", "Helvetica-Bold"))
            size = tf.get("size", 28)
            y_bl = tf.get("y_bl", tf.get("y", 93))
            y_td = page.rect.height - y_bl
            tw = fitz.TextWriter(page.rect)
            tw.append((tf.get("x", 54), y_td), title_text, font=font_obj, fontsize=size)
            tw.write_text(page, color=_hex_to_rgb(tf.get("color", "#006FAB")))

        # Project naam
        sf = fields.get("project_naam", {})
        subtitle_text = data.get("project", "")
        if subtitle_text:
            font_obj = self.fonts.get_fitz_font(sf.get("font", "Helvetica"))
            size = sf.get("size", 17)
            y_bl = sf.get("y_bl", sf.get("y", 63))
            y_td = page.rect.height - y_bl
            tw = fitz.TextWriter(page.rect)
            tw.append((sf.get("x", 55), y_td), subtitle_text, font=font_obj, fontsize=size)
            tw.write_text(page, color=_hex_to_rgb(sf.get("color", "#94571E")))

        # Cover image (als beschikbaar en er is een foto-zone in de template)
        photo_cfg = self.tpl.get("photo")
        cover_image_src = data.get("cover", {}).get("image")
        if photo_cfg and cover_image_src:
            cover_image_path = _resolve_image(cover_image_src)
            if cover_image_path:
                px = photo_cfg.get("x", 55.6)
                py_bl = photo_cfg.get("y", 161.7)
                pw = photo_cfg.get("width", 484.0)
                ph = photo_cfg.get("height", 560.8)
                py_td = page.rect.height - py_bl - ph
                rect = fitz.Rect(px, py_td, px + pw, py_td + ph)
                try:
                    page.insert_image(rect, filename=str(cover_image_path))
                except (OSError, ValueError, RuntimeError) as e:
                    logger.warning("Cover image insert failed: %s", e)

        doc.save(str(output))
        doc.close()
        return output

    def _generate_from_png(self, data: dict, stationery_png: Path | None, output: Path) -> Path:
        """Bestaande ReportLab PNG overlay cover (3BM)."""
        self.fonts.register_reportlab()
        w, h = A4
        c = rl_canvas.Canvas(str(output), pagesize=A4)

        # Layer 1: Project photo placeholder (or actual image)
        cover_image_src = data.get("cover", {}).get("image")
        cover_image_path = _resolve_image(cover_image_src)
        if cover_image_path:
            from reportlab.lib.utils import ImageReader

            img = ImageReader(str(cover_image_path))
            iw, ih = img.getSize()
            box_w, box_h = 484.0, 560.8
            box_x, box_y = 55.6, 161.7
            scale = max(box_w / iw, box_h / ih)
            draw_w = iw * scale
            draw_h = ih * scale
            draw_x = box_x - (draw_w - box_w) / 2
            draw_y = box_y - (draw_h - box_h) / 2
            c.saveState()
            p = c.beginPath()
            p.rect(box_x, box_y, box_w, box_h)
            c.clipPath(p, stroke=0)
            c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h)
            c.restoreState()
        else:
            c.setFillColor(HexColor("#38BDAB"))
            c.rect(55.6, 161.7, 484.0, 560.8, fill=1, stroke=0)
            c.setFillColor(Color(0.15, 0.35, 0.35, alpha=0.4))
            c.rect(55.6, 161.7, 484.0, 280, fill=1, stroke=0)
            c.setFillColor(HexColor("#FFFFFF"))
            c.setFont("Helvetica", 16)
            c.drawCentredString(w / 2, 440, "[ PROJECTFOTO ]")

        # Layer 2: Stationery overlay (with alpha channel)
        if stationery_png and stationery_png.exists():
            from reportlab.lib.utils import ImageReader

            img = ImageReader(str(stationery_png))
            c.drawImage(img, 0, 0, width=w, height=h, mask="auto", preserveAspectRatio=False)

        # Layer 3: Dynamic text
        fields = self.tpl.get("dynamic_fields", {})

        tf = fields.get("rapport_type", {})
        title_text = data.get("report_type", "")
        if title_text:
            c.setFont(tf.get("font", "GothamBold"), tf.get("size", 28.9))
            c.setFillColor(HexColor(tf.get("color", "#401246")))
            c.drawString(tf.get("x", 54.3), tf.get("y_bl", 120.5), title_text)

        sf = fields.get("project_naam", {})
        subtitle_text = data.get("project", "")
        if subtitle_text:
            c.setFont(sf.get("font", "GothamBook"), sf.get("size", 17.8))
            c.setFillColor(HexColor(sf.get("color", "#38BDAB")))
            c.drawString(sf.get("x", 55.0), sf.get("y_bl", 78.6), subtitle_text)

        c.save()
        return output


# ---------------------------------------------------------------------------
# Colofon Generator (PyMuPDF)
# ---------------------------------------------------------------------------
class ColofonGenerator:
    """Generates colofon page by inserting text onto stationery PDF."""

    def __init__(self, templates: TemplateSet, fonts: FontManager):
        self.tpl = templates.colofon
        self.fonts = fonts

    def generate(
        self, data: dict, stationery_pdf: Path, output: Path, page_number: int = 2
    ) -> Path:
        """Generate colofon PDF."""
        doc = fitz.open(str(stationery_pdf))
        page = doc[0]
        self.fonts.insert_into_page(page)

        # Title
        title_cfg = self.tpl.get("dynamic_fields", {}).get("titel", {})
        report_type = data.get("report_type", "")
        if report_type:
            font_obj = self.fonts.get_fitz_font(
                title_cfg.get("font", "Helvetica-Bold")
            )
            tw = fitz.TextWriter(page.rect)
            tw.append(
                (
                    title_cfg.get("x", 70.9),
                    title_cfg.get("y_td", 57.3) + title_cfg.get("size", 22) * 0.8,
                ),
                report_type, font=font_obj, fontsize=title_cfg.get("size", 22),
            )
            tw.write_text(
                page, color=_hex_to_rgb(title_cfg.get("color", "#40124A"))
            )

        # Subtitle
        sub_cfg = self.tpl.get("dynamic_fields", {}).get("subtitel", {})
        project_name = data.get("project", "")
        if project_name:
            font_obj = self.fonts.get_fitz_font(
                sub_cfg.get("font", "Helvetica")
            )
            tw = fitz.TextWriter(page.rect)
            tw.append(
                (sub_cfg.get("x", 70.9), sub_cfg.get("y_td", 86.8) + sub_cfg.get("size", 14) * 0.8),
                project_name, font=font_obj, fontsize=sub_cfg.get("size", 14),
            )
            tw.write_text(
                page, color=_hex_to_rgb(sub_cfg.get("color", "#38BDA0"))
            )

        # Table values — map JSON fields to colofon positions
        colofon_data = data.get("colofon", {})
        field_map = self._build_field_map(data, colofon_data)
        table_cfg = self.tpl.get("table", {})
        value_x = table_cfg.get("value_x", 229.1)
        value_size = table_cfg.get("value_size", 10)
        value_font = table_cfg.get("value_font", "Helvetica")
        value_color = _hex_to_rgb(table_cfg.get("value_color", "#40124A"))

        for field_key, y_td in self._get_field_positions():
            text = field_map.get(field_key, "")
            if text:
                font_obj = self.fonts.get_fitz_font(value_font)
                for i, line in enumerate(text.split("\n")):
                    tw = fitz.TextWriter(page.rect)
                    tw.append(
                        (value_x, y_td + i * 12.8 + value_size * 0.8),
                        line, font=font_obj, fontsize=value_size,
                    )
                    tw.write_text(page, color=value_color)

        # Revision history (optional)
        rev_cfg = self.tpl.get("revision_history", {})
        revisions = colofon_data.get("revision_history", [])
        current_y = rev_cfg.get("y_td", 670.0)
        if revisions:
            # Label
            lbl_font_name = rev_cfg.get("label_font", "Helvetica-Bold")
            lbl_size = rev_cfg.get("label_size", 10.0)
            lbl_color = _hex_to_rgb(rev_cfg.get("label_color", "#38BDA0"))
            lbl_x = rev_cfg.get("label_x", 103.0)
            font_obj = self.fonts.get_fitz_font(lbl_font_name)
            tw = fitz.TextWriter(page.rect)
            tw.append(
                (lbl_x, current_y + lbl_size * 0.8),
                "Revisiehistorie", font=font_obj, fontsize=lbl_size,
            )
            tw.write_text(page, color=lbl_color)
            current_y += lbl_size * 1.8

            # Table
            tbl_x = rev_cfg.get("table_x", 103.0)
            tbl_end_x = rev_cfg.get("table_end_x", 420.0)
            hdr_font_name = rev_cfg.get("header_font", "Helvetica-Bold")
            hdr_size = rev_cfg.get("header_size", 8.0)
            hdr_color = _hex_to_rgb(rev_cfg.get("header_color", "#40124A"))
            body_font_name = rev_cfg.get("body_font", "Helvetica")
            body_size = rev_cfg.get("body_size", 8.0)
            body_color = _hex_to_rgb(rev_cfg.get("body_color", "#45243D"))
            row_h = rev_cfg.get("row_height", 14.0)

            tbl_width = tbl_end_x - tbl_x
            col_ratios = rev_cfg.get("col_widths", [0.12, 0.18, 0.25, 0.45])
            col_xs = [tbl_x]
            for ratio in col_ratios[:-1]:
                col_xs.append(col_xs[-1] + tbl_width * ratio)

            # Header row
            headers = ["Versie", "Datum", "Auteur", "Omschrijving"]
            hdr_font = self.fonts.get_fitz_font(hdr_font_name)
            for i, header in enumerate(headers):
                tw = fitz.TextWriter(page.rect)
                tw.append(
                    (col_xs[i], current_y + hdr_size * 0.8),
                    header, font=hdr_font, fontsize=hdr_size,
                )
                tw.write_text(page, color=hdr_color)
            current_y += row_h

            # Separator line
            page.draw_line(
                fitz.Point(tbl_x, current_y - row_h * 0.3),
                fitz.Point(tbl_end_x, current_y - row_h * 0.3),
                color=hdr_color, width=0.5,
            )

            # Data rows
            body_font = self.fonts.get_fitz_font(body_font_name)
            for rev in revisions:
                cells = [
                    rev.get("version", ""),
                    rev.get("date", ""),
                    rev.get("author", ""),
                    rev.get("description", ""),
                ]
                for i, cell in enumerate(cells):
                    if cell:
                        tw = fitz.TextWriter(page.rect)
                        tw.append(
                            (col_xs[i], current_y + body_size * 0.8),
                            str(cell), font=body_font, fontsize=body_size,
                        )
                        tw.write_text(page, color=body_color)
                current_y += row_h

        # Disclaimer (optional)
        disclaimer = colofon_data.get("disclaimer", "")
        if disclaimer:
            discl_cfg = self.tpl.get("disclaimer", {})
            discl_x = discl_cfg.get("x", 103.0)
            discl_font_name = discl_cfg.get("font", "Helvetica-Oblique")
            discl_size = discl_cfg.get("size", 7.0)
            discl_color = _hex_to_rgb(discl_cfg.get("color", "#7F8C8D"))
            discl_y = current_y + 8.0

            discl_font = self.fonts.get_fitz_font(discl_font_name)
            for i, line in enumerate(disclaimer.split("\n")):
                tw = fitz.TextWriter(page.rect)
                tw.append(
                    (discl_x, discl_y + i * (discl_size * 1.6) + discl_size * 0.8),
                    line.strip(), font=discl_font, fontsize=discl_size,
                )
                tw.write_text(page, color=discl_color)

        # Page number
        pn_cfg = self.tpl.get("page_number", {})
        pn_size = pn_cfg.get("size", 8)
        font_obj = self.fonts.get_fitz_font(
            pn_cfg.get("font", "Helvetica-Bold")
        )
        tw = fitz.TextWriter(page.rect)
        tw.append(
            (pn_cfg.get("x", 534.0), pn_cfg.get("y_td", 796.3) + pn_size * 0.8),
            str(page_number), font=font_obj, fontsize=pn_size,
        )
        tw.write_text(
            page, color=_hex_to_rgb(pn_cfg.get("color", "#38BDA0"))
        )

        doc.save(str(output))
        doc.close()
        return output

    def _build_field_map(self, data: dict, colofon: dict) -> dict[str, str]:
        """Build mapping from field keys to display values."""
        pn = data.get("project_number", "")
        pname = data.get("project", "")
        return {
            "project": f"{pn} - {pname}" if pn else pname,
            "opdrachtgever_contact": colofon.get("opdrachtgever_contact", ""),
            "opdrachtgever_naam": colofon.get("opdrachtgever_naam", data.get("client", "")),
            "opdrachtgever_adres": colofon.get("opdrachtgever_adres", ""),
            "adviseur_bedrijf": colofon.get(
                "adviseur_bedrijf", data.get("author", "3BM Coöperatie")
            ),
            "adviseur_naam": colofon.get("adviseur_naam", ""),
            "adviseur_email": colofon.get("adviseur_email", ""),
            "adviseur_telefoon": colofon.get("adviseur_telefoon", ""),
            "adviseur_functie": colofon.get("adviseur_functie", ""),
            "adviseur_registratie": colofon.get("adviseur_registratie", ""),
            "normen": colofon.get("normen", ""),
            "documentgegevens": colofon.get("documentgegevens", ""),
            "datum": colofon.get("datum", data.get("date", "")),
            "fase": colofon.get("fase", ""),
            "status": colofon.get("status_colofon", data.get("status", "CONCEPT")),
            "kenmerk": colofon.get("kenmerk", ""),
        }

    def _get_field_positions(self) -> list[tuple[str, float]]:
        """Return (field_key, y_td) for each colofon table row."""
        rows = self.tpl.get("table", {}).get("rows", [])
        if rows:
            return [(r["key"], r["y_td"]) for r in rows]
        # Fallback: hardcoded from reference
        return [
            ("project", 321.1),
            ("opdrachtgever_contact", 369.1),
            ("opdrachtgever_naam", 381.8),
            ("opdrachtgever_adres", 394.6),
            ("adviseur_bedrijf", 489.1),
            ("adviseur_naam", 501.1),
            ("normen", 525.1),
            ("documentgegevens", 549.1),
            ("datum", 573.1),
            ("fase", 597.1),
            ("status", 621.1),
            ("kenmerk", 645.1),
        ]


# ---------------------------------------------------------------------------
# Content Renderer (PyMuPDF)
# ---------------------------------------------------------------------------
class ContentRenderer:
    """Renders dynamic content pages: TOC, chapters, appendices, backcover.

    Uses PyMuPDF to overlay text on stationery PDF pages with accurate
    Gotham font measurements for word-wrapping.
    """

    def __init__(
        self,
        templates: TemplateSet,
        fonts: FontManager,
        stationery: dict[str, Path],
        brand_config=None,
    ):
        self.tpl = templates
        self.fonts = fonts
        self.stationery = stationery  # {"standaard": Path, "bijlagen": Path, "achterblad": Path}
        self.blocks = templates.blocks
        self._brand_config = brand_config

        # Content frame uit brand config of defaults
        if brand_config and brand_config.stationery:
            content_spec = brand_config.stationery.get("content")
            if content_spec and content_spec.content_frame:
                cf = content_spec.content_frame
                self._default_y_max_portrait = cf.get("y_pt", 38.9) + cf.get("height_pt", 746.0)
            else:
                self._default_y_max_portrait = Y_MAX_PORTRAIT

            landscape_spec = brand_config.stationery.get("content_landscape")
            if landscape_spec and landscape_spec.content_frame:
                cf = landscape_spec.content_frame
                self._default_y_max_landscape = cf.get("y_pt", 38.9) + cf.get("height_pt", 517.5)
            else:
                self._default_y_max_landscape = Y_MAX_LANDSCAPE
        else:
            self._default_y_max_portrait = Y_MAX_PORTRAIT
            self._default_y_max_landscape = Y_MAX_LANDSCAPE

        self.doc = fitz.open()
        self.page: fitz.Page | None = None
        self.y = 0.0
        self.page_count = 0
        self.y_max = self._default_y_max_portrait
        self.current_page_nr = 3  # starts after cover (1) + colofon (2)
        self._orientation: str = "portrait"

    # --- Low level ---

    def _new_page(self, template_key: str = "standaard") -> None:
        """Insert a new page from stationery template.

        Selecteert automatisch de juiste stationery en paginagrootte
        op basis van de huidige oriëntatie (``_orientation``).

        Args:
            template_key: Stationery key (bijv. 'standaard', 'bijlagen').
        """
        # Kies stationery op basis van oriëntatie
        if self._orientation == "landscape" and template_key == "standaard":
            landscape_key = "content_landscape"
            pdf_path = self.stationery.get(landscape_key)
        else:
            pdf_path = self.stationery.get(template_key)

        if pdf_path and pdf_path.exists():
            src = fitz.open(str(pdf_path))
            self.doc.insert_pdf(src)
            src.close()
        elif self._orientation == "landscape":
            self.doc.new_page(
                width=A4_LANDSCAPE_WIDTH, height=A4_LANDSCAPE_HEIGHT
            )
        else:
            self.doc.new_page(
                width=A4_PORTRAIT_WIDTH, height=A4_PORTRAIT_HEIGHT
            )

        self.page_count += 1
        self.page = self.doc[-1]
        self.fonts.insert_into_page(self.page)

        margins = self.tpl.standaard.get("margins", {})
        self.y = margins.get("top", 74.9)

        # Y-max instellen op basis van oriëntatie
        if self._orientation == "landscape":
            self.y_max = self._default_y_max_landscape
        else:
            self.y_max = self._default_y_max_portrait

    def _check_overflow(self, needed: float) -> bool:
        """Check if content fits; if not, finalize page and start new one."""
        if self.y + needed > self.y_max:
            self._add_page_number()
            self._new_page()
            return True
        return False

    def _add_page_number(self) -> None:
        """Add page number to current page."""
        pn = self.tpl.page_number
        if not pn or not self.page:
            return
        self._text(
            pn["x"], pn["y_td"],
            str(self.current_page_nr),
            pn.get("font", "GothamBook"),
            pn["size"],
            pn["color"],
        )
        self.current_page_nr += 1

    def _text(
        self,
        x: float,
        y_td: float,
        text: str,
        fontname: str,
        size: float,
        color_hex: str,
    ) -> None:
        """Insert text met embedded font subset via TextWriter."""
        if not self.page or not text:
            return
        font_obj = self.fonts.get_fitz_font(fontname)
        tw = fitz.TextWriter(self.page.rect)
        tw.append((x, y_td + size * 0.8), text, font=font_obj, fontsize=size)
        tw.write_text(self.page, color=_hex_to_rgb(color_hex))

    # --- TOC ---

    def render_toc(self, entries: list[tuple]) -> None:
        """Render table of contents.

        Args:
            entries: List of (level, number, title, page_number) tuples.
        """
        self._new_page()
        toc_cfg = self.tpl.toc

        # Title
        title_cfg = toc_cfg.get("title", {})
        self._text(
            title_cfg.get("x", 90.0),
            title_cfg.get("y_td", 74.9),
            title_cfg.get("text", "Inhoud"),
            title_cfg.get("font", "GothamBook"),
            title_cfg.get("size", 18.0),
            title_cfg.get("color", "#401246"),
        )

        self.y = toc_cfg.get("entries_start_y", 127.2)

        levels = toc_cfg.get("levels", {})
        lv1 = levels.get("1", {})
        lv2 = levels.get("2", {})

        for level, number, title, pg in entries:
            if level == 1:
                self.y += lv1.get("spacing_before", 17.0)
                self._check_overflow(20)
                self._text(
                    lv1.get("number_x", 90.0),
                    self.y,
                    number,
                    lv1.get("font", "GothamBook"),
                    lv1.get("size", 12.0),
                    lv1.get("color", "#56B49B"),
                )
                self._text(
                    lv1.get("title_x", 160.9),
                    self.y,
                    title,
                    lv1.get("font", "GothamBook"),
                    lv1.get("size", 12.0),
                    lv1.get("color", "#56B49B"),
                )
                self._text(
                    lv1.get("page_x", 515.4),
                    self.y,
                    str(pg),
                    lv1.get("font", "GothamBook"),
                    lv1.get("size", 12.0),
                    lv1.get("color", "#56B49B"),
                )
                self.y += lv1.get("spacing_after", 20.0)
            else:
                self._check_overflow(17.3)
                self._text(
                    lv2.get("number_x", 90.0),
                    self.y,
                    number,
                    lv2.get("font", "GothamBook"),
                    lv2.get("size", 9.5),
                    lv2.get("color", "#401246"),
                )
                self._text(
                    lv2.get("title_x", 160.9),
                    self.y,
                    title,
                    lv2.get("font", "GothamBook"),
                    lv2.get("size", 9.5),
                    lv2.get("color", "#401246"),
                )
                self._text(
                    lv2.get("page_x", 515.4),
                    self.y,
                    str(pg),
                    lv2.get("font", "GothamBook"),
                    lv2.get("size", 9.5),
                    lv2.get("color", "#401246"),
                )
                self.y += lv2.get("spacing_after", 17.3)

        self._add_page_number()

    # --- Content blocks ---

    def heading_1(self, number: str, title: str) -> None:
        s = self.blocks.get("heading_1", {})
        n = s.get("number", {})
        t = s.get("title", {})
        self._check_overflow(n.get("size", 18) + s.get("spacing_after", 33.9))
        self._text(n["x"], self.y, number, n["font"], n["size"], n["color"])
        self._text(t["x"], self.y, title, t["font"], t["size"], t["color"])
        self.y += n["size"] + s.get("spacing_after", 33.9)

    def heading_2(self, number: str, title: str) -> None:
        s = self.blocks.get("heading_2", {})
        n = s.get("number", {})
        t = s.get("title", {})
        self.y += s.get("spacing_before", 30.0)
        self._check_overflow(t.get("size", 13) + s.get("spacing_after", 20.5))
        self._text(n["x"], self.y, number, n["font"], n["size"], n["color"])
        y_title = self.y - (t["size"] - n["size"]) * 0.3
        self._text(t["x"], y_title, title, t["font"], t["size"], t["color"])
        self.y += t["size"] + s.get("spacing_after", 20.5)

    def paragraph(self, text: str) -> None:
        s = self.blocks.get("paragraph", {})
        self.y += s.get("spacing_before", 12.0)
        text = _strip_html(text)
        lines = self.fonts.wrap_text(text, s["size"], s["max_width"])
        self._check_overflow(len(lines) * s["line_height"])
        for line in lines:
            self._text(s["x"], self.y, line, s["font"], s["size"], s["color"])
            self.y += s["line_height"]
        self.y += s.get("spacing_after", 12.0)

    def bullet_list(self, items: list[str]) -> None:
        sb = self.blocks.get("bullet_list", {})
        marker = sb.get("marker", {})
        text_s = sb.get("text", {})
        for item in items:
            item = _strip_html(item)
            lines = self.fonts.wrap_text(item, text_s["size"], text_s["max_width"])
            needed = len(lines) * text_s["line_height"] + sb.get("spacing_between", 10.1)
            self._check_overflow(needed)
            # Bullet marker
            self._text(
                marker["x"], self.y,
                "\u2022",
                marker.get("font", "Helvetica"),
                marker["size"],
                marker["color"],
            )
            for line in lines:
                self._text(
                    text_s["x"], self.y, line, text_s["font"], text_s["size"], text_s["color"]
                )
                self.y += text_s["line_height"]
            self.y += sb.get("spacing_between", 10.1)

    # --- Table ---

    def table(self, block: dict) -> None:
        """Render a table block with header and rows.

        Supports:
        - column_widths as proportional values (scaled to available width)
        - auto-fit when column_widths not provided
        - style "striped" for alternating row colors
        - vertical grid lines between columns
        - multi-line text wrapping in cells with dynamic row height
        """
        s = self.blocks.get("table", {})
        header_s = s.get("header", {})
        body_s = s.get("body", {})
        x = s.get("x", 125.4)
        max_w = s.get("max_width", 415.9)

        headers = block.get("headers", [])
        rows = block.get("rows", [])
        raw_widths = block.get("column_widths")
        title = block.get("title", "")
        style = block.get("style", "")
        num_cols = len(headers) if headers else (len(rows[0]) if rows else 0)
        if num_cols == 0:
            return

        # --- Resolve column widths ---
        cell_pad = 5  # horizontal padding per side
        if raw_widths and len(raw_widths) >= num_cols:
            total = sum(raw_widths[:num_cols])
            if total > 0:
                col_widths_pt = [(w / total) * max_w for w in raw_widths[:num_cols]]
            else:
                col_widths_pt = [max_w / num_cols] * num_cols
        else:
            # Auto-fit: measure header + sample row data
            header_font_size = header_s.get("size", 9)
            measured = []
            for i in range(num_cols):
                h_text = str(headers[i]) if i < len(headers) else ""
                max_cell_w = self.fonts.measure(h_text, header_font_size, bold=True)
                body_font_size = body_s.get("size", 8)
                for row in rows[:10]:
                    if i < len(row):
                        cell_w = self.fonts.measure(str(row[i]), body_font_size)
                        max_cell_w = max(max_cell_w, cell_w)
                measured.append(max_cell_w + cell_pad * 2)
            total_measured = sum(measured)
            if total_measured > 0:
                col_widths_pt = [(m / total_measured) * max_w for m in measured]
            else:
                col_widths_pt = [max_w / num_cols] * num_cols

        # --- Enforce minimum column widths ---
        # Prevent narrow columns from becoming too small to display their
        # widest single word/token, which causes unwanted line breaks.
        body_font_size = body_s.get("size", 8)
        header_font_size = header_s.get("size", 9)
        min_widths = []
        for i in range(num_cols):
            # Widest single token in header
            h_text = str(headers[i]) if i < len(headers) else ""
            h_tokens = h_text.split() or [""]
            min_w = max(
                self.fonts.measure(t, header_font_size, bold=True) for t in h_tokens
            )
            # Widest single token in body rows
            for row in rows:
                cell_val = str(row[i]) if i < len(row) else ""
                tokens = cell_val.split() or [""]
                token_max = max(self.fonts.measure(t, body_font_size) for t in tokens)
                min_w = max(min_w, token_max)
            min_widths.append(min_w + cell_pad * 2)

        # Redistribute: bump undersized columns, shrink oversized ones
        deficit = 0.0
        flexible_width = 0.0
        for i in range(num_cols):
            if col_widths_pt[i] < min_widths[i]:
                deficit += min_widths[i] - col_widths_pt[i]
            else:
                flexible_width += col_widths_pt[i]

        if deficit > 0 and flexible_width > 0:
            shrink_factor = max((flexible_width - deficit) / flexible_width, 0.5)
            for i in range(num_cols):
                if col_widths_pt[i] < min_widths[i]:
                    col_widths_pt[i] = min_widths[i]
                else:
                    col_widths_pt[i] *= shrink_factor

        h_fontname = header_s.get("font", "GothamBold")
        h_fontsize = header_s.get("size", 9)
        h_color = _hex_to_rgb(header_s.get("color", "#FFFFFF"))
        b_fontname = body_s.get("font", "GothamBook")
        b_fontsize = body_s.get("size", 8)
        b_color = _hex_to_rgb(body_s.get("color", "#401246"))
        bg_color = _hex_to_rgb(header_s.get("background", "#56B49B"))
        stripe_color = _hex_to_rgb(s.get("stripe_color", "#F5F5F5"))
        grid_color = _hex_to_rgb(s.get("grid_color", "#E0E0E0"))
        line_color_hdr = _hex_to_rgb(s.get("header_grid_color", "#FFFFFF"))
        cell_line_h = b_fontsize * 1.35  # line height within cells

        # Pre-wrap all header cells
        header_wrapped: list[list[str]] = []
        for i, h in enumerate(headers):
            w = col_widths_pt[i] if i < len(col_widths_pt) else col_widths_pt[-1]
            lines = self.fonts.wrap_text(str(h), h_fontsize, w - cell_pad * 2, bold=True)
            header_wrapped.append(lines if lines else [""])
        header_max_lines = max((len(lines) for lines in header_wrapped), default=1)
        header_h = max(header_max_lines * (h_fontsize * 1.35) + 8, 20.0)

        self.y += s.get("spacing_before", 20.0)

        # Title above table
        if title:
            title_s = s.get("title", {})
            self._check_overflow(16 + header_h)
            self._text(
                x, self.y, title,
                title_s.get("font", "GothamBold"),
                title_s.get("size", 9.5),
                title_s.get("color", "#401246"),
            )
            self.y += 16

        self._check_overflow(header_h + cell_line_h + 8)  # at least header + 1 row line

        # --- Render header helper ---
        def render_header():
            header_rect = fitz.Rect(x, self.y, x + max_w, self.y + header_h)
            self.page.draw_rect(header_rect, color=None, fill=bg_color)
            cx = x
            for i, lines in enumerate(header_wrapped):
                w = col_widths_pt[i] if i < len(col_widths_pt) else col_widths_pt[-1]
                # Vertically center the wrapped text block
                text_block_h = len(lines) * (h_fontsize * 1.35)
                y_start = self.y + (header_h - text_block_h) / 2
                for li, line in enumerate(lines):
                    font_obj = self.fonts.get_fitz_font(h_fontname)
                    tw = fitz.TextWriter(self.page.rect)
                    tw.append(
                        (cx + cell_pad, y_start + h_fontsize * 0.8 + li * (h_fontsize * 1.35)),
                        line, font=font_obj, fontsize=h_fontsize,
                    )
                    tw.write_text(self.page, color=h_color)
                cx += w
            # Vertical grid lines in header
            cx = x
            for i in range(num_cols - 1):
                cx += col_widths_pt[i]
                self.page.draw_line(
                    fitz.Point(cx, self.y),
                    fitz.Point(cx, self.y + header_h),
                    color=line_color_hdr,
                    width=0.5,
                )

        render_header()
        self.y += header_h

        # --- Body rows ---
        for row_idx, row in enumerate(rows):
            # Pre-wrap all cells to determine row height
            row_wrapped: list[list[str]] = []
            for i in range(num_cols):
                cell_val = str(row[i]) if i < len(row) else ""
                w = col_widths_pt[i] if i < len(col_widths_pt) else col_widths_pt[-1]
                lines = self.fonts.wrap_text(cell_val, b_fontsize, w - cell_pad * 2)
                row_wrapped.append(lines if lines else [""])
            max_lines = max(len(lines) for lines in row_wrapped)
            row_h = max(max_lines * cell_line_h + 6, cell_line_h + 6)

            if self._check_overflow(row_h):
                # Re-render header on new page
                render_header()
                self.y += header_h

            # Striped background
            if style == "striped" and row_idx % 2 == 1:
                row_rect = fitz.Rect(x, self.y, x + max_w, self.y + row_h)
                self.page.draw_rect(row_rect, color=None, fill=stripe_color)

            # Cell text (wrapped)
            cx = x
            for i, lines in enumerate(row_wrapped):
                w = col_widths_pt[i] if i < len(col_widths_pt) else col_widths_pt[-1]
                y_text = self.y + 3  # top padding
                for li, line in enumerate(lines):
                    font_obj = self.fonts.get_fitz_font(b_fontname)
                    tw = fitz.TextWriter(self.page.rect)
                    tw.append(
                        (cx + cell_pad, y_text + b_fontsize * 0.8 + li * cell_line_h),
                        line, font=font_obj, fontsize=b_fontsize,
                    )
                    tw.write_text(self.page, color=b_color)
                cx += w

            # Vertical grid lines between columns
            cx = x
            for i in range(num_cols - 1):
                cx += col_widths_pt[i]
                self.page.draw_line(
                    fitz.Point(cx, self.y),
                    fitz.Point(cx, self.y + row_h),
                    color=grid_color,
                    width=0.3,
                )

            # Bottom border
            self.page.draw_line(
                fitz.Point(x, self.y + row_h),
                fitz.Point(x + max_w, self.y + row_h),
                color=grid_color,
                width=0.3,
            )

            self.y += row_h

        # Final bottom border
        self.page.draw_line(
            fitz.Point(x, self.y),
            fitz.Point(x + max_w, self.y),
            color=grid_color,
            width=0.5,
        )

        self.y += s.get("spacing_after", 20.0)

    # --- Image ---

    def image(self, block: dict) -> None:
        """Render an image block with optional caption."""
        s = self.blocks.get("paragraph", {})  # use paragraph x/max_width
        img_s = self.blocks.get("image", {})
        caption_s = img_s.get("caption", {})
        error_s = img_s.get("error", {})
        x = s.get("x", 125.4)
        max_w = s.get("max_width", 393.0)

        src = block.get("src", "")
        caption = block.get("caption", "")
        width_mm = block.get("width_mm")

        # Resolve image source
        img_path = self._resolve_image(src)
        if not img_path:
            # Placeholder text
            self.y += 12
            self._text(
                x, self.y, f"[Image: {src or 'niet gevonden'}]",
                error_s.get("font", "GothamBook"),
                error_s.get("size", 9.5),
                error_s.get("color", "#FF0000"),
            )
            self.y += 16
            return

        # Calculate dimensions
        target_w = (width_mm * 2.8346) if width_mm else max_w
        target_w = min(target_w, max_w)

        # Get image aspect ratio
        try:
            from PIL import Image as PILImage

            with PILImage.open(img_path) as im:
                iw, ih = im.size
            aspect = ih / iw
        except (ImportError, OSError, ZeroDivisionError):
            aspect = 0.75  # fallback 4:3

        target_h = target_w * aspect
        max_h = self.y_max - self.y - 30  # leave room for caption
        if target_h > max_h and max_h > 50:
            target_h = max_h
            target_w = target_h / aspect

        self._check_overflow(target_h + 20)

        self.y += 8
        rect = fitz.Rect(x, self.y, x + target_w, self.y + target_h)
        try:
            self.page.insert_image(rect, filename=str(img_path))
        except (OSError, ValueError, RuntimeError) as e:
            logger.warning("Image insert failed: %s", e)
            self._text(
                x, self.y, f"[Image error: {e}]",
                error_s.get("font", "GothamBook"),
                error_s.get("size", 9.5),
                error_s.get("color", "#FF0000"),
            )

        self.y += target_h + 4

        if caption:
            self._text(
                x, self.y, caption,
                caption_s.get("font", "GothamBook"),
                caption_s.get("size", 8.0),
                caption_s.get("color", "#401246"),
            )
            self.y += 14

        self.y += 8

    def _resolve_image(self, src) -> Path | None:
        """Resolve image source: file path or base64 dict."""
        return _resolve_image(src)

    # --- Map ---

    def map_block(self, block: dict) -> None:
        """Render map images from PDOK services with POI marker.

        Accepts:
            address: Dutch address string (geocoded via PDOK)
            center: {lat, lon} coordinates (used if no address)
            zoom: Zoom level (default 16, ~1:5000)
            layers: List of layer keys: "brt", "brt_grijs", "luchtfoto", "kadastraal"
            width_mm: Image width in report (default: full content width)
            height_mm: Image height in report (default: auto from aspect)
            cadastral: Optional dict with kadastrale gegevens:
                - identificatie: "LDN03-H-8575"
                - gemeentecode: "LDN03"
                - gemeentenaam: "Loosduinen"
                - sectie: "H"
                - perceelnummer: 8575
                - grootte: area in m²
        """
        from openaec_reports.core.map_generator import MapGenerator

        s = self.blocks.get("paragraph", {})
        map_s = self.blocks.get("map", {})
        caption_s = map_s.get("caption", {})
        error_s = map_s.get("error", {})
        x = s.get("x", 125.4)
        max_w = s.get("max_width", 393.0)

        address = block.get("address", "")
        center = block.get("center", {})
        lat = center.get("lat")
        lon = center.get("lon")
        zoom = block.get("zoom", 16)
        layers = block.get("layers", ["brt"])
        width_mm = block.get("width_mm")
        height_mm = block.get("height_mm")
        caption = block.get("caption", "")
        cadastral = block.get("cadastral")

        # Normalize layer names
        layer_map = {
            "topografie": "brt",
            "topo": "brt",
            "standaard": "brt",
            "grijs": "brt_grijs",
            "luchtfoto": "luchtfoto",
            "satellite": "luchtfoto",
            "aerial": "luchtfoto",
            "kadastraal": "kadastraal",
            "kadaster": "kadastraal",
            "cadastral": "kadastraal",
        }
        normalized_layers = [layer_map.get(layer.lower(), layer.lower()) for layer in layers]

        # Calculate image dimensions in points
        target_w = (width_mm * 2.8346) if width_mm else max_w
        target_w = min(target_w, max_w)
        if height_mm:
            target_h = height_mm * 2.8346
        else:
            target_h = target_w * 0.667  # 3:2

        # WMS pixel dimensions (higher res for print quality)
        px_w = int(target_w * 2.5)
        px_h = int(target_h * 2.5)

        try:
            gen = MapGenerator(timeout=20)

            if address:
                maps = gen.generate_maps(
                    address,
                    layers=normalized_layers,
                    zoom=zoom,
                    width_px=px_w,
                    height_px=px_h,
                    show_poi=True,
                )
            elif lat is not None and lon is not None:
                maps = gen.generate_maps_from_coords(
                    lat,
                    lon,
                    layers=normalized_layers,
                    zoom=zoom,
                    width_px=px_w,
                    height_px=px_h,
                    show_poi=True,
                )
            else:
                self.y += 12
                self._text(
                    x,
                    self.y,
                    "[Kaart: geen adres of coördinaten opgegeven]",
                    error_s.get("font", "GothamBook"),
                    error_s.get("size", 9.5),
                    error_s.get("color", "#FF0000"),
                )
                self.y += 20
                return

            if not maps:
                self.y += 12
                loc_str = address or f"{lat}, {lon}"
                self._text(
                    x,
                    self.y,
                    f"[Kaart kon niet worden opgehaald voor: {loc_str}]",
                    error_s.get("font", "GothamBook"),
                    error_s.get("size", 9.5),
                    error_s.get("color", "#FF0000"),
                )
                self.y += 20
                return

            # Render each map layer as an image
            for map_result in maps:
                img_path = map_result["path"]
                map_caption = caption or map_result.get("caption", "")

                needed = target_h + 24
                self._check_overflow(needed)

                self.y += 8
                rect = fitz.Rect(x, self.y, x + target_w, self.y + target_h)
                try:
                    self.page.insert_image(rect, filename=str(img_path))
                except (OSError, ValueError, RuntimeError) as e:
                    logger.warning("Map image insert failed: %s", e)
                    self._text(
                        x, self.y + 10, f"[Kaart fout: {e}]",
                        error_s.get("font", "GothamBook"),
                        error_s.get("size", 9.5),
                        error_s.get("color", "#FF0000"),
                    )
                self.y += target_h + 4

                if map_caption:
                    self._text(
                        x, self.y, map_caption,
                        caption_s.get("font", "GothamBook"),
                        caption_s.get("size", 8.0),
                        caption_s.get("color", "#401246"),
                    )
                    self.y += 14

                self.y += 8

                try:
                    img_path.unlink(missing_ok=True)
                except OSError:
                    pass

            # Render cadastral info below all maps
            if cadastral:
                self._render_cadastral_info(x, max_w, cadastral)

        except ImportError:
            logger.warning("Map generator dependencies not available")
            self.y += 12
            self._text(
                x,
                self.y,
                "[Kaartmodule niet beschikbaar — PIL/requests ontbreekt]",
                error_s.get("font", "GothamBook"),
                error_s.get("size", 9.5),
                error_s.get("color", "#FF0000"),
            )
            self.y += 20
        except (OSError, ValueError, RuntimeError) as e:
            logger.error("Map generation failed: %s", e)
            self.y += 12
            self._text(
                x, self.y, f"[Kaart fout: {e}]",
                error_s.get("font", "GothamBook"),
                error_s.get("size", 9.5),
                error_s.get("color", "#FF0000"),
            )
            self.y += 20

    def _render_cadastral_info(self, x: float, max_w: float, cadastral: dict) -> None:
        """Render cadastral parcel information below map images.

        Renders a styled info box with:
        - Kadastraal perceel: GEM-SECTIE-NUMMER
        - Gemeente: naam (code)
        - Oppervlakte: xxx m²
        """
        cad_s = self.blocks.get("cadastral", {})
        title_s = cad_s.get("title", {})
        body_s = cad_s.get("body", {})

        identificatie = cadastral.get("identificatie", "")
        gemeentenaam = cadastral.get("gemeentenaam", "")
        gemeentecode = cadastral.get("gemeentecode", "")
        grootte = cadastral.get("grootte", 0)

        if not identificatie:
            return

        # Calculate block height
        lines = 1  # perceel ID
        if gemeentenaam:
            lines += 1
        if grootte:
            lines += 1
        block_h = lines * 14 + 12  # line height + padding

        self._check_overflow(block_h + 8)

        # Light background box
        bg_color = _hex_to_rgb(cad_s.get("background", "#F8F8F8"))
        bg_rect = fitz.Rect(x, self.y, x + max_w, self.y + block_h)
        self.page.draw_rect(bg_rect, color=None, fill=bg_color)
        # Left accent bar
        accent_color = _hex_to_rgb(cad_s.get("accent_color", "#56B49B"))
        accent_rect = fitz.Rect(x, self.y, x + 3, self.y + block_h)
        self.page.draw_rect(accent_rect, color=None, fill=accent_color)

        inner_x = x + 10
        y_line = self.y + 4

        # Perceel identification (bold)
        self._text(
            inner_x, y_line, f"Kadastraal perceel:  {identificatie}",
            title_s.get("font", "GothamBold"),
            title_s.get("size", 8.5),
            title_s.get("color", "#401246"),
        )
        y_line += 14

        # Gemeente
        if gemeentenaam:
            gem_str = f"Kadastrale gemeente:  {gemeentenaam}"
            if gemeentecode:
                gem_str += f" ({gemeentecode})"
            self._text(
                inner_x, y_line, gem_str,
                body_s.get("font", "GothamBook"),
                body_s.get("size", 8.5),
                body_s.get("color", "#401246"),
            )
            y_line += 14

        # Oppervlakte
        if grootte:
            opp_str = f"Perceeloppervlakte:  {grootte:,.0f} m²".replace(",", ".")
            self._text(
                inner_x, y_line, opp_str,
                body_s.get("font", "GothamBook"),
                body_s.get("size", 8.5),
                body_s.get("color", "#401246"),
            )
            y_line += 14

        self.y += block_h + 8

    # --- Spacer ---

    def spacer(self, block: dict) -> None:
        """Add vertical space."""
        height_mm = block.get("height_mm", 10)
        height_pt = height_mm * 2.8346
        self._check_overflow(height_pt)
        self.y += height_pt

    # --- Page break ---

    def page_break(self) -> None:
        """Force a page break."""
        self._add_page_number()
        self._new_page()

    # --- Calculation block ---

    def calculation(self, block: dict) -> None:
        """Render engineering calculation block with formula/result."""
        calc_s = self.blocks.get("calculation", {})
        title_s = calc_s.get("title", {})
        body_s = calc_s.get("body", {})
        result_s = calc_s.get("result", {})
        ref_s = calc_s.get("reference", {})

        title = block.get("title", "")
        formula = block.get("formula", "")
        substitution = block.get("substitution", "")
        result = block.get("result", "")
        unit = block.get("unit", "")
        reference = block.get("reference", "")

        x = self.blocks.get("paragraph", {}).get("x", 125.4)
        max_w = self.blocks.get("paragraph", {}).get("max_width", 393.0)

        # Calculate needed height
        lines_needed = 1  # title
        if formula:
            lines_needed += 1
        if substitution:
            lines_needed += 1
        lines_needed += 1  # result
        if reference:
            lines_needed += 1
        block_h = lines_needed * 16 + 16  # padding

        self.y += 12
        self._check_overflow(block_h)

        # Background rect
        bg_color = _hex_to_rgb(calc_s.get("background", "#F5F5F5"))
        bg_rect = fitz.Rect(x - 4, self.y - 2, x + max_w + 4, self.y + block_h - 8)
        self.page.draw_rect(bg_rect, color=None, fill=bg_color)

        # Title
        self._text(
            x, self.y, title,
            title_s.get("font", "GothamBold"),
            title_s.get("size", 9.5),
            title_s.get("color", "#401246"),
        )
        self.y += 16

        # Formula
        if formula:
            self._text(
                x + 8, self.y, formula,
                body_s.get("font", "GothamBook"),
                body_s.get("size", 9.5),
                body_s.get("color", "#401246"),
            )
            self.y += 16

        # Substitution
        if substitution:
            self._text(
                x + 8, self.y, substitution,
                body_s.get("font", "GothamBook"),
                body_s.get("size", 9.5),
                body_s.get("color", "#401246"),
            )
            self.y += 16

        # Result
        result_text = f"{result} {unit}".strip()
        self._text(
            x + 8, self.y, result_text,
            result_s.get("font", "GothamBold"),
            result_s.get("size", 9.5),
            result_s.get("color", "#401246"),
        )
        self.y += 16

        # Reference
        if reference:
            self._text(
                x + 8, self.y, f"Ref: {reference}",
                ref_s.get("font", "GothamBook"),
                ref_s.get("size", 8.0),
                ref_s.get("color", "#56B49B"),
            )
            self.y += 14

        self.y += 12

    # --- Check block ---

    def check(self, block: dict) -> None:
        """Render engineering check block (voldoet/voldoet niet)."""
        chk_s = self.blocks.get("check", {})
        title_s = chk_s.get("title", {})
        body_s = chk_s.get("body", {})
        result_s = chk_s.get("result", {})

        description = block.get("description", "")
        required = block.get("required_value", "")
        calculated = block.get("calculated_value", "")
        unity = block.get("unity_check", 0)
        result = block.get("result", "VOLDOET")

        x = self.blocks.get("paragraph", {}).get("x", 125.4)
        max_w = self.blocks.get("paragraph", {}).get("max_width", 393.0)

        block_h = 80
        self.y += 12
        self._check_overflow(block_h)

        # Background rect
        bg_color = _hex_to_rgb(chk_s.get("background", "#F5F5F5"))
        bg_rect = fitz.Rect(x - 4, self.y - 2, x + max_w + 4, self.y + block_h - 16)
        self.page.draw_rect(bg_rect, color=None, fill=bg_color)

        # Description
        self._text(
            x, self.y, description,
            title_s.get("font", "GothamBold"),
            title_s.get("size", 9.5),
            title_s.get("color", "#401246"),
        )
        self.y += 16

        # Required vs calculated
        self._text(
            x + 8, self.y, f"Vereist: {required}",
            body_s.get("font", "GothamBook"),
            body_s.get("size", 9.5),
            body_s.get("color", "#401246"),
        )
        self.y += 14
        self._text(
            x + 8, self.y, f"Berekend: {calculated}",
            body_s.get("font", "GothamBook"),
            body_s.get("size", 9.5),
            body_s.get("color", "#401246"),
        )
        self.y += 14

        # Unity check
        uc_text = f"Unity check: {unity:.2f}"
        self._text(
            x + 8, self.y, uc_text,
            body_s.get("font", "GothamBook"),
            body_s.get("size", 9.5),
            body_s.get("color", "#401246"),
        )

        # Result indicator
        is_ok = result.upper() == "VOLDOET"
        ok = chk_s.get("ok_color", "#56B49B")
        fail = chk_s.get("fail_color", "#FF0000")
        result_color = ok if is_ok else fail
        self._text(
            x + 200, self.y, result,
            result_s.get("font", "GothamBold"),
            result_s.get("size", 9.5),
            result_color,
        )
        self.y += 20

    # --- Section rendering ---

    def render_section(self, section: dict) -> None:
        """Render a single section (chapter) with its content blocks.

        Ondersteunt per-sectie oriëntatie via ``section["orientation"]``.
        Bij een oriëntatiewisseling wordt een nieuwe pagina gestart met
        de juiste paginagrootte en stationery. Na de sectie wordt de
        vorige oriëntatie hersteld.
        """
        level = section.get("level", 1)
        title = section.get("title", "")
        number = section.get("number", "")

        # Per-sectie orientation switch
        section_orientation = section.get("orientation", self._orientation)
        previous_orientation = self._orientation
        orientation_changed = section_orientation != self._orientation

        if orientation_changed:
            # Finaliseer huidige pagina voor de wissel
            if self.page is not None:
                self._add_page_number()
            self._orientation = section_orientation

        if section.get("page_break_before", False) or level == 1:
            self._new_page()
        elif orientation_changed:
            # Forceer nieuwe pagina bij oriëntatiewissel
            self._new_page()

        if level == 1 and number:
            self.heading_1(number, title)
        elif level == 2 and number:
            self.heading_2(number, title)

        for block in section.get("content", []):
            self._render_block(block)

        # Add page number if this was a top-level section start
        if level == 1:
            self._add_page_number()

        # Herstel vorige oriëntatie na de sectie
        if orientation_changed:
            self._orientation = previous_orientation
            self.y_max = (
                self._default_y_max_landscape
                if self._orientation == "landscape"
                else self._default_y_max_portrait
            )

    def _render_block(self, block: dict) -> None:
        """Dispatch a content block to the appropriate renderer."""
        block_type = block.get("type", "")
        if block_type == "paragraph":
            style = block.get("style", "")
            if style in ("Heading1", "heading_1"):
                self.heading_1(block.get("number", ""), block.get("text", ""))
            elif style in ("Heading2", "heading_2"):
                self.heading_2(block.get("number", ""), block.get("text", ""))
            else:
                self.paragraph(block.get("text", ""))
        elif block_type == "bullet_list":
            self.bullet_list(block.get("items", []))
        elif block_type == "heading_2":
            self.heading_2(block.get("number", ""), block.get("title", ""))
        elif block_type == "heading_1":
            self.heading_1(block.get("number", ""), block.get("title", ""))
        elif block_type == "table":
            self.table(block)
        elif block_type == "image":
            self.image(block)
        elif block_type == "spacer":
            self.spacer(block)
        elif block_type == "page_break":
            self.page_break()
        elif block_type == "calculation":
            self.calculation(block)
        elif block_type == "check":
            self.check(block)
        elif block_type == "map":
            self.map_block(block)
        else:
            logger.warning("Unsupported block type: %s", block_type)

    # --- Bijlage ---

    def render_bijlage_divider(self, nummer: str, titel: str) -> None:
        """Render appendix divider page."""
        self._new_page("bijlagen")
        # Number
        bijl_cfg = self.tpl.bijlage.get("dynamic_fields", {})
        nr_cfg = bijl_cfg.get("nummer", {})
        self._text(
            nr_cfg.get("x", 103.0),
            nr_cfg.get("y_td", 193.9),
            nummer,
            nr_cfg.get("font", "GothamBold"),
            nr_cfg.get("size", 41.4),
            nr_cfg.get("color", "#401246"),
        )

        # Title (fixed 20pt, multiline)
        ti_cfg = bijl_cfg.get("titel", {})
        fontsize = ti_cfg.get("size", 20.0)
        line_height = fontsize * 1.6
        for i, line in enumerate(titel.split("\n")):
            y_td = ti_cfg.get("y_td", 262.2) + i * line_height
            self._text(
                ti_cfg.get("x", 136.1),
                y_td,
                line,
                ti_cfg.get("font", "GothamBook"),
                fontsize,
                ti_cfg.get("color", "#FFFFFF"),
            )
        # No page number on divider, but increment counter
        self.current_page_nr += 1

    def render_achterblad(self) -> None:
        """Append static backcover PDF."""
        path = self.stationery.get("achterblad")
        if path and path.exists():
            src = fitz.open(str(path))
            self.doc.insert_pdf(src)
            src.close()

    def save(self, output_path: Path) -> None:
        """Save the assembled PyMuPDF document."""
        self.doc.save(str(output_path))
        self.doc.close()


# ---------------------------------------------------------------------------
# Main Generator — orchestrates all parts
# ---------------------------------------------------------------------------
class ReportGeneratorV2:
    """Top-level report generator. Accepts JSON, produces PDF.

    Usage:
        gen = ReportGeneratorV2(brand="3bm_cooperatie")
        gen.generate(data, stationery_dir, output_pdf)

    Or from JSON file:
        gen = ReportGeneratorV2.from_json("report.json", stationery_dir, output)
    """

    def __init__(self, brand: str = "3bm_cooperatie"):
        self.brand_name = brand
        self.templates = TemplateSet(brand)

        # Laad brand config voor stationery mapping en font info
        from openaec_reports.core.brand import BrandLoader

        try:
            loader = BrandLoader()
            self.brand_config = loader.load(brand)
        except FileNotFoundError:
            self.brand_config = None
            logger.warning("Brand config niet gevonden voor '%s', gebruik defaults", brand)

        # FontManager met brand font info
        brand_fonts = self.brand_config.fonts if self.brand_config else None
        font_dir = None
        if self.brand_config and self.brand_config.brand_dir:
            candidate = self.brand_config.brand_dir / "fonts"
            if candidate.exists() and any(candidate.glob("*.ttf")):
                font_dir = candidate
        self.fonts = FontManager(font_dir=font_dir, brand_fonts=brand_fonts)

    def _resolve_stationery(self, stationery_dir: Path) -> dict[str, Path]:
        """Resolve stationery bestandspaden uit brand config of fallback naar conventie."""
        result = {}
        stationery_mapping = {
            "cover": {
                "brand_keys": ["cover"],
                "fallbacks": ["cover.pdf", "cover_stationery.pdf"],
            },
            "colofon": {
                "brand_keys": ["colofon"],
                "fallbacks": ["colofon.pdf", "colofon_stationery.pdf"],
            },
            "standaard": {
                "brand_keys": ["content", "content_portrait"],
                "fallbacks": [
                    "standaard.pdf",
                    "content_portrait_stationery.pdf",
                    "content_portrait.pdf",
                ],
            },
            "content_landscape": {
                "brand_keys": ["content_landscape"],
                "fallbacks": [
                    "standaard_landscape.pdf",
                    "content_landscape_stationery.pdf",
                    "content_landscape.pdf",
                ],
            },
            "bijlagen": {
                "brand_keys": ["appendix", "bijlagen"],
                "fallbacks": ["bijlagen.pdf", "bijlagen_stationery.pdf"],
            },
            "achterblad": {
                "brand_keys": ["backcover", "achterblad"],
                "fallbacks": [
                    "achterblad.pdf",
                    "backcover_stationery.pdf",
                    "backcover.pdf",
                ],
            },
        }

        for key, config in stationery_mapping.items():
            resolved = None

            # 1. Probeer brand config
            if self.brand_config and self.brand_config.stationery:
                for brand_key in config["brand_keys"]:
                    spec = self.brand_config.stationery.get(brand_key)
                    if spec and spec.source:
                        # Relatief t.o.v. brand_dir
                        if self.brand_config.brand_dir:
                            candidate = self.brand_config.brand_dir / spec.source
                            if candidate.exists():
                                resolved = candidate
                                break
                        # Zoek op bestandsnaam in stationery_dir
                        candidate = stationery_dir / Path(spec.source).name
                        if candidate.exists():
                            resolved = candidate
                            break

            # 2. Fallback: zoek in stationery_dir op conventie-naam
            if resolved is None:
                for fallback_name in config["fallbacks"]:
                    candidate = stationery_dir / fallback_name
                    if candidate.exists():
                        resolved = candidate
                        break

            if resolved:
                result[key] = resolved

        return result

    def generate(
        self,
        data: dict[str, Any],
        stationery_dir: Path,
        output_path: Path,
    ) -> Path:
        """Generate a complete PDF report.

        Args:
            data: Report data dict (conforming to report.schema.json).
            stationery_dir: Directory with stationery PDFs and PNG overlay.
            output_path: Output PDF path.

        Returns:
            Path to generated PDF.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Resolve stationery via brand config
        stationery = self._resolve_stationery(stationery_dir)

        # Cover: bepaal modus (PDF of PNG)
        cover_stationery = stationery.get("cover")
        cover_is_pdf = bool(cover_stationery and cover_stationery.suffix.lower() == ".pdf")

        # PNG overlay (legacy 3BM)
        if not cover_is_pdf:
            overlay_name = self.templates.cover.get("overlay", {}).get("file")
            stationery_png = (stationery_dir / overlay_name) if overlay_name else None
            # Fallback: zoek bekende PNG overlay
            if (not stationery_png or not stationery_png.exists()):
                legacy_png = stationery_dir / "2707_BBLrapportage_v01_1.png"
                if legacy_png.exists():
                    stationery_png = legacy_png
        else:
            stationery_png = None

        tmp_dir = output_path.parent
        tmp_cover = tmp_dir / "_tmp_cover.pdf"
        tmp_colofon = tmp_dir / "_tmp_colofon.pdf"
        tmp_content = tmp_dir / "_tmp_content.pdf"

        try:
            parts: list[Path] = []

            # 1. Cover (optioneel)
            if data.get("cover", {}).get("enabled", True):
                logger.info("Generating cover...")
                cover_gen = CoverGenerator(self.templates, self.fonts)
                if cover_is_pdf:
                    cover_gen.generate(data, cover_stationery, tmp_cover, cover_is_pdf=True)
                else:
                    cover_gen.generate(data, stationery_png, tmp_cover, cover_is_pdf=False)
                parts.append(tmp_cover)

            # 2. Colofon (optioneel)
            colofon_stationery = stationery.get("colofon")
            colofon_enabled = data.get("colofon", {}).get("enabled", True)
            if colofon_enabled and colofon_stationery and colofon_stationery.exists():
                logger.info("Generating colofon...")
                colofon_gen = ColofonGenerator(self.templates, self.fonts)
                colofon_gen.generate(data, colofon_stationery, tmp_colofon)
                parts.append(tmp_colofon)

            # 3. Content (TOC + sections + appendices + backcover)
            logger.info("Generating content...")
            content = ContentRenderer(
                self.templates, self.fonts, stationery,
                brand_config=self.brand_config,
            )
            # Adjust page numbering based on which parts are included
            content.current_page_nr = len(parts) + 1
            self._render_content(content, data)
            content.save(tmp_content)
            parts.append(tmp_content)

            # 4. Merge
            logger.info("Merging PDF...")
            self._merge_pdfs(parts, output_path)

            # Report stats
            result = fitz.open(str(output_path))
            page_count = result.page_count
            result.close()
            logger.info("Report ready: %s (%d pages)", output_path, page_count)
            return output_path

        finally:
            # Cleanup temp files
            for tmp in [tmp_cover, tmp_colofon, tmp_content]:
                tmp.unlink(missing_ok=True)

    def _render_content(self, renderer: ContentRenderer, data: dict) -> None:
        """Orchestrate rendering of TOC, sections, appendices, backcover."""

        # TOC
        toc_cfg = data.get("toc", {})
        if toc_cfg.get("enabled", True):
            toc_entries = self._build_toc_entries(data)
            renderer.render_toc(toc_entries)

        # Sections
        for section in data.get("sections", []):
            renderer.render_section(section)

        # Finalize last content page number if not already done
        if renderer.page is not None:
            renderer._add_page_number()

        # Appendices
        for appendix in data.get("appendices", []):
            nummer = appendix.get("label", f"Bijlage {appendix.get('number', 1)}")
            titel = appendix.get("title", "")
            renderer.render_bijlage_divider(nummer, titel)

            # Appendix content pages
            for section in appendix.get("content_sections", []):
                renderer.render_section(section)
            if appendix.get("content_sections"):
                renderer._add_page_number()

        # Backcover
        if data.get("backcover", {}).get("enabled", True):
            renderer.render_achterblad()

    def _build_toc_entries(self, data: dict) -> list[tuple]:
        """Build TOC entries from sections data.

        Returns list of (level, number, title, estimated_page).
        """
        entries = []
        # Start page estimation: cover(1) + colofon(2) + toc(3) = content starts at 4
        page_est = 4

        for section in data.get("sections", []):
            level = section.get("level", 1)
            number = section.get("number", "")
            title = section.get("title", "")
            entries.append((level, number, title, page_est))

            # Rough page estimation based on content volume
            if level == 1:
                page_est += 1

            # Sub-sections
            for block in section.get("content", []):
                if block.get("type") == "heading_2":
                    entries.append(
                        (
                            2,
                            block.get("number", ""),
                            block.get("title", ""),
                            page_est,
                        )
                    )

        return entries

    @staticmethod
    def _merge_pdfs(input_paths: list[Path], output_path: Path) -> None:
        """Merge multiple PDFs into one."""
        final = fitz.open()
        for path in input_paths:
            if path.exists():
                src = fitz.open(str(path))
                final.insert_pdf(src)
                src.close()
        final.save(str(output_path))
        final.close()

    @classmethod
    def from_json(
        cls,
        json_path: str | Path,
        stationery_dir: str | Path,
        output_path: str | Path,
        brand: str = "3bm_cooperatie",
    ) -> Path:
        """Generate report directly from JSON file.

        Args:
            json_path: Path to JSON report definition.
            stationery_dir: Directory with stationery PDFs.
            output_path: Output PDF path.
            brand: Template brand name.

        Returns:
            Path to generated PDF.
        """
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        gen = cls(brand=brand)
        return gen.generate(data, Path(stationery_dir), Path(output_path))
