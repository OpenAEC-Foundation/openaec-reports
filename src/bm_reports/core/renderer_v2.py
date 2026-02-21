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
        with open(path, "r", encoding="utf-8") as f:
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
    """Manages font registration for both ReportLab and PyMuPDF."""

    FONT_MAP = {
        "GothamBold": "Gotham-Bold.ttf",
        "GothamBook": "Gotham-Book.ttf",
        "GothamMedium": "Gotham-Medium.ttf",
    }

    def __init__(self, font_dir: Path | None = None):
        self.font_dir = font_dir or FONT_DIR
        self._rl_registered = False
        # PyMuPDF font objects for accurate text measurement
        self.gotham_book = fitz.Font(
            fontfile=str(self.font_dir / "Gotham-Book.ttf")
        )
        self.gotham_bold = fitz.Font(
            fontfile=str(self.font_dir / "Gotham-Bold.ttf")
        )

    def register_reportlab(self) -> None:
        """Register Gotham fonts with ReportLab (once)."""
        if self._rl_registered:
            return
        for name, filename in self.FONT_MAP.items():
            path = self.font_dir / filename
            if path.exists():
                try:
                    pdfmetrics.registerFont(TTFont(name, str(path)))
                except Exception:
                    logger.warning("Could not register font: %s", name)
        self._rl_registered = True

    def insert_into_page(self, page: fitz.Page) -> None:
        """Insert Gotham fonts into a PyMuPDF page."""
        for name, filename in self.FONT_MAP.items():
            path = self.font_dir / filename
            if path.exists():
                page.insert_font(fontname=name, fontfile=str(path))

    def measure(self, text: str, fontsize: float, bold: bool = False) -> float:
        """Measure text width using actual Gotham font metrics."""
        font = self.gotham_bold if bold else self.gotham_book
        return font.text_length(text, fontsize=fontsize)

    def wrap_text(
        self, text: str, fontsize: float, max_width: float, bold: bool = False
    ) -> list[str]:
        """Word-wrap text to fit within max_width."""
        words = text.split()
        lines: list[str] = []
        current = ""
        for w in words:
            test = f"{current} {w}".strip()
            if self.measure(test, fontsize, bold) > max_width and current:
                lines.append(current)
                current = w
            else:
                current = test
        if current:
            lines.append(current)
        return lines


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
        except Exception as e:
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

    def generate(self, data: dict, stationery_png: Path, output: Path) -> Path:
        """Generate cover PDF.

        Args:
            data: Report data dict with project info.
            stationery_png: Path to RGBA overlay PNG.
            output: Output PDF path.
        """
        self.fonts.register_reportlab()
        w, h = A4
        c = rl_canvas.Canvas(str(output), pagesize=A4)

        # Layer 1: Project photo placeholder (or actual image)
        cover_image_src = data.get("cover", {}).get("image")
        cover_image_path = _resolve_image(cover_image_src)
        if cover_image_path:
            from reportlab.lib.utils import ImageReader

            img = ImageReader(str(cover_image_path))
            # "Cover" style: fill entire area, crop overflow
            iw, ih = img.getSize()
            box_w, box_h = 484.0, 560.8
            box_x, box_y = 55.6, 161.7
            scale = max(box_w / iw, box_h / ih)
            draw_w = iw * scale
            draw_h = ih * scale
            # Center the oversized image within the box
            draw_x = box_x - (draw_w - box_w) / 2
            draw_y = box_y - (draw_h - box_h) / 2
            # Clip to the box area
            c.saveState()
            p = c.beginPath()
            p.rect(box_x, box_y, box_w, box_h)
            c.clipPath(p, stroke=0)
            c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h)
            c.restoreState()
        else:
            # Teal gradient placeholder
            c.setFillColor(HexColor("#38BDAB"))
            c.rect(55.6, 161.7, 484.0, 560.8, fill=1, stroke=0)
            c.setFillColor(Color(0.15, 0.35, 0.35, alpha=0.4))
            c.rect(55.6, 161.7, 484.0, 280, fill=1, stroke=0)
            c.setFillColor(HexColor("#FFFFFF"))
            c.setFont("Helvetica", 16)
            c.drawCentredString(w / 2, 440, "[ PROJECTFOTO ]")

        # Layer 2: Stationery overlay (with alpha channel)
        if stationery_png.exists():
            from reportlab.lib.utils import ImageReader

            img = ImageReader(str(stationery_png))
            c.drawImage(img, 0, 0, width=w, height=h,
                        mask="auto", preserveAspectRatio=False)

        # Layer 3: Dynamic text
        fields = self.tpl.get("dynamic_fields", {})

        # Rapport type (title)
        tf = fields.get("rapport_type", {})
        title_text = data.get("report_type", "")
        if title_text:
            c.setFont(tf.get("font", "GothamBold"), tf.get("size", 28.9))
            c.setFillColor(HexColor(tf.get("color", "#401246")))
            c.drawString(tf.get("x", 54.3), tf.get("y_bl", 120.5), title_text)

        # Project naam (subtitle)
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

        purple = _hex_to_rgb("#401246")
        teal = _hex_to_rgb("#56B49B")

        # Title
        title_cfg = self.tpl.get("dynamic_fields", {}).get("titel", {})
        report_type = data.get("report_type", "")
        if report_type:
            page.insert_text(
                (title_cfg.get("x", 70.9),
                 title_cfg.get("y_td", 57.3) + title_cfg.get("size", 22) * 0.8),
                report_type,
                fontname="GothamBold",
                fontsize=title_cfg.get("size", 22),
                color=purple,
            )

        # Subtitle
        sub_cfg = self.tpl.get("dynamic_fields", {}).get("subtitel", {})
        project_name = data.get("project", "")
        if project_name:
            page.insert_text(
                (sub_cfg.get("x", 70.9),
                 sub_cfg.get("y_td", 86.8) + sub_cfg.get("size", 14) * 0.8),
                project_name,
                fontname="GothamBook",
                fontsize=sub_cfg.get("size", 14),
                color=teal,
            )

        # Table values — map JSON fields to colofon positions
        colofon_data = data.get("colofon", {})
        field_map = self._build_field_map(data, colofon_data)
        value_x = self.tpl.get("table", {}).get("value_x", 229.1)
        value_size = self.tpl.get("table", {}).get("value_size", 10)

        for field_key, y_td in self._get_field_positions():
            text = field_map.get(field_key, "")
            if text:
                for i, line in enumerate(text.split("\n")):
                    page.insert_text(
                        (value_x, y_td + i * 12.8 + value_size * 0.8),
                        line,
                        fontname="GothamBook",
                        fontsize=value_size,
                        color=purple,
                    )

        # Page number
        pn_cfg = self.tpl.get("page_number", {})
        page.insert_text(
            (pn_cfg.get("x", 534.0), pn_cfg.get("y_td", 796.3) + 8 * 0.8),
            str(page_number),
            fontname="GothamBold",
            fontsize=8,
            color=teal,
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
            "adviseur_bedrijf": colofon.get("adviseur_bedrijf", data.get("author", "3BM Coöperatie")),
            "adviseur_naam": colofon.get("adviseur_naam", ""),
            "normen": colofon.get("normen", ""),
            "documentgegevens": colofon.get("documentgegevens", ""),
            "datum": data.get("date", ""),
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
    ):
        self.tpl = templates
        self.fonts = fonts
        self.stationery = stationery  # {"standaard": Path, "bijlagen": Path, "achterblad": Path}
        self.blocks = templates.blocks

        self.doc = fitz.open()
        self.page: fitz.Page | None = None
        self.y = 0.0
        self.page_count = 0
        self.y_max = 780.0
        self.current_page_nr = 3  # starts after cover (1) + colofon (2)

    # --- Low level ---

    def _new_page(self, template_key: str = "standaard") -> None:
        """Insert a new page from stationery template."""
        pdf_path = self.stationery.get(template_key)
        if pdf_path and pdf_path.exists():
            src = fitz.open(str(pdf_path))
            self.doc.insert_pdf(src)
            src.close()
        else:
            # Fallback: blank A4
            self.doc.new_page(width=595.3, height=841.9)

        self.page_count += 1
        self.page = self.doc[-1]
        self.fonts.insert_into_page(self.page)

        margins = self.tpl.standaard.get("margins", {})
        self.y = margins.get("top", 74.9)

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
        self.page.insert_text(
            (pn["x"], pn["y_td"] + pn["size"] * 0.8),
            str(self.current_page_nr),
            fontname=pn.get("font", "GothamBook"),
            fontsize=pn["size"],
            color=_hex_to_rgb(pn["color"]),
        )
        self.current_page_nr += 1

    def _text(
        self, x: float, y_td: float, text: str,
        fontname: str, size: float, color_hex: str,
    ) -> None:
        """Insert text at position (x, y_td) using top-down coordinates."""
        self.page.insert_text(
            (x, y_td + size * 0.8),
            text,
            fontname=fontname,
            fontsize=size,
            color=_hex_to_rgb(color_hex),
        )

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
                self._text(lv1.get("number_x", 90.0), self.y, number,
                           lv1.get("font", "GothamBook"), lv1.get("size", 12.0),
                           lv1.get("color", "#56B49B"))
                self._text(lv1.get("title_x", 160.9), self.y, title,
                           lv1.get("font", "GothamBook"), lv1.get("size", 12.0),
                           lv1.get("color", "#56B49B"))
                self._text(lv1.get("page_x", 515.4), self.y, str(pg),
                           lv1.get("font", "GothamBook"), lv1.get("size", 12.0),
                           lv1.get("color", "#56B49B"))
                self.y += lv1.get("spacing_after", 20.0)
            else:
                self._check_overflow(17.3)
                self._text(lv2.get("number_x", 90.0), self.y, number,
                           lv2.get("font", "GothamBook"), lv2.get("size", 9.5),
                           lv2.get("color", "#401246"))
                self._text(lv2.get("title_x", 160.9), self.y, title,
                           lv2.get("font", "GothamBook"), lv2.get("size", 9.5),
                           lv2.get("color", "#401246"))
                self._text(lv2.get("page_x", 515.4), self.y, str(pg),
                           lv2.get("font", "GothamBook"), lv2.get("size", 9.5),
                           lv2.get("color", "#401246"))
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
            self.page.insert_text(
                (marker["x"], self.y + marker["size"] * 0.8),
                "\u2022",
                fontname="GothamBook",
                fontsize=marker["size"],
                color=_hex_to_rgb(marker["color"]),
            )
            for line in lines:
                self._text(text_s["x"], self.y, line,
                           text_s["font"], text_s["size"], text_s["color"])
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
        - text truncation for cells that exceed column width
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
        # Interpret column_widths as proportional values and scale to max_w
        cell_pad = 6  # horizontal padding per cell
        if raw_widths and len(raw_widths) >= num_cols:
            total = sum(raw_widths[:num_cols])
            if total > 0:
                col_widths_pt = [(w / total) * max_w for w in raw_widths[:num_cols]]
            else:
                col_widths_pt = [max_w / num_cols] * num_cols
        else:
            # Auto-fit: measure header text and distribute proportionally
            header_font_size = header_s.get("size", 9)
            measured = []
            for i in range(num_cols):
                h_text = str(headers[i]) if i < len(headers) else ""
                # Also check a sample of row data for wider content
                max_cell_w = self.fonts.measure(h_text, header_font_size, bold=True)
                body_font_size = body_s.get("size", 8)
                for row in rows[:10]:  # sample first 10 rows
                    if i < len(row):
                        cell_w = self.fonts.measure(str(row[i]), body_font_size)
                        max_cell_w = max(max_cell_w, cell_w)
                measured.append(max_cell_w + cell_pad * 2)
            total_measured = sum(measured)
            if total_measured > 0:
                col_widths_pt = [(m / total_measured) * max_w for m in measured]
            else:
                col_widths_pt = [max_w / num_cols] * num_cols

        header_h = header_s.get("height", 20.0)
        row_h = body_s.get("line_height", 16.0)
        total_h = header_h + len(rows) * row_h
        self.y += s.get("spacing_before", 20.0)

        # Title above table
        if title:
            self._check_overflow(16 + total_h)
            self._text(x, self.y, title, "GothamBold", 9.5, "#401246")
            self.y += 16

        self._check_overflow(header_h + row_h)  # at least header + 1 row

        # --- Header row ---
        bg_color = _hex_to_rgb(header_s.get("background", "#56B49B"))
        header_rect = fitz.Rect(x, self.y, x + max_w, self.y + header_h)
        self.page.draw_rect(header_rect, color=None, fill=bg_color)

        h_fontname = header_s.get("font", "GothamBold")
        h_fontsize = header_s.get("size", 9)
        h_color = _hex_to_rgb(header_s.get("color", "#FFFFFF"))
        cx = x
        for i, h in enumerate(headers):
            w = col_widths_pt[i] if i < len(col_widths_pt) else col_widths_pt[-1]
            # Truncate text to fit column
            cell_text = self._truncate_text(str(h), h_fontsize, w - cell_pad * 2, bold=True)
            self.page.insert_text(
                (cx + cell_pad, self.y + h_fontsize * 0.8 + (header_h - h_fontsize) / 2),
                cell_text,
                fontname=h_fontname,
                fontsize=h_fontsize,
                color=h_color,
            )
            cx += w

        # Vertical grid lines in header
        line_color = _hex_to_rgb("#FFFFFF")
        cx = x
        for i in range(num_cols - 1):
            cx += col_widths_pt[i]
            self.page.draw_line(
                fitz.Point(cx, self.y),
                fitz.Point(cx, self.y + header_h),
                color=line_color, width=0.5,
            )

        self.y += header_h

        # --- Body rows ---
        b_fontname = body_s.get("font", "GothamBook")
        b_fontsize = body_s.get("size", 8)
        b_color = _hex_to_rgb(body_s.get("color", "#401246"))
        stripe_color = _hex_to_rgb("#F5F5F5")
        grid_color = _hex_to_rgb("#E0E0E0")

        for row_idx, row in enumerate(rows):
            if self._check_overflow(row_h):
                # Re-render header on new page
                header_rect = fitz.Rect(x, self.y, x + max_w, self.y + header_h)
                self.page.draw_rect(header_rect, color=None, fill=bg_color)
                cx = x
                for i, h in enumerate(headers):
                    w = col_widths_pt[i] if i < len(col_widths_pt) else col_widths_pt[-1]
                    cell_text = self._truncate_text(str(h), h_fontsize, w - cell_pad * 2, bold=True)
                    self.page.insert_text(
                        (cx + cell_pad, self.y + h_fontsize * 0.8 + (header_h - h_fontsize) / 2),
                        cell_text,
                        fontname=h_fontname,
                        fontsize=h_fontsize,
                        color=h_color,
                    )
                    cx += w
                # Vertical lines in repeated header
                cx = x
                for i in range(num_cols - 1):
                    cx += col_widths_pt[i]
                    self.page.draw_line(
                        fitz.Point(cx, self.y),
                        fitz.Point(cx, self.y + header_h),
                        color=line_color, width=0.5,
                    )
                self.y += header_h

            # Striped background
            if style == "striped" and row_idx % 2 == 1:
                row_rect = fitz.Rect(x, self.y, x + max_w, self.y + row_h)
                self.page.draw_rect(row_rect, color=None, fill=stripe_color)

            # Bottom border for each row
            self.page.draw_line(
                fitz.Point(x, self.y + row_h),
                fitz.Point(x + max_w, self.y + row_h),
                color=grid_color, width=0.3,
            )

            # Cell text
            cx = x
            for i, cell in enumerate(row):
                w = col_widths_pt[i] if i < len(col_widths_pt) else col_widths_pt[-1]
                cell_text = self._truncate_text(str(cell), b_fontsize, w - cell_pad * 2)
                self.page.insert_text(
                    (cx + cell_pad, self.y + b_fontsize * 0.8 + (row_h - b_fontsize) / 2),
                    cell_text,
                    fontname=b_fontname,
                    fontsize=b_fontsize,
                    color=b_color,
                )
                cx += w

            # Vertical grid lines between columns
            cx = x
            for i in range(num_cols - 1):
                cx += col_widths_pt[i]
                self.page.draw_line(
                    fitz.Point(cx, self.y),
                    fitz.Point(cx, self.y + row_h),
                    color=grid_color, width=0.3,
                )

            self.y += row_h

        # Outer border
        table_top = self.y - len(rows) * row_h - header_h
        # Only draw if we didn't page-break (simplified: draw bottom border)
        self.page.draw_line(
            fitz.Point(x, self.y),
            fitz.Point(x + max_w, self.y),
            color=grid_color, width=0.5,
        )

        self.y += s.get("spacing_after", 20.0)

    def _truncate_text(self, text: str, fontsize: float, max_width: float, bold: bool = False) -> str:
        """Truncate text with ellipsis if it exceeds max_width."""
        if max_width <= 0:
            return ""
        if self.fonts.measure(text, fontsize, bold) <= max_width:
            return text
        # Binary search for truncation point
        for end in range(len(text), 0, -1):
            truncated = text[:end] + "…"
            if self.fonts.measure(truncated, fontsize, bold) <= max_width:
                return truncated
        return "…"

    # --- Image ---

    def image(self, block: dict) -> None:
        """Render an image block with optional caption."""
        s = self.blocks.get("paragraph", {})  # use paragraph x/max_width
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
            self._text(x, self.y, f"[Image: {src or 'niet gevonden'}]",
                       "GothamBook", 9.5, "#FF0000")
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
        except Exception:
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
        except Exception as e:
            logger.warning("Image insert failed: %s", e)
            self._text(x, self.y, f"[Image error: {e}]", "GothamBook", 9.5, "#FF0000")

        self.y += target_h + 4

        if caption:
            self._text(x, self.y, caption, "GothamBook", 8.0, "#401246")
            self.y += 14

        self.y += 8

    def _resolve_image(self, src) -> Path | None:
        """Resolve image source: file path or base64 dict."""
        return _resolve_image(src)

    # --- Map ---

    def map_block(self, block: dict) -> None:
        """Render a map block placeholder (PDOK WMS not available in v2 yet)."""
        s = self.blocks.get("paragraph", {})
        x = s.get("x", 125.4)
        max_w = s.get("max_width", 393.0)

        self.y += 12
        self._check_overflow(60)

        # Placeholder box
        rect = fitz.Rect(x, self.y, x + max_w, self.y + 50)
        self.page.draw_rect(rect, color=_hex_to_rgb("#CCCCCC"), fill=_hex_to_rgb("#F0F0F0"))

        center = block.get("center", {})
        lat = center.get("lat", "?")
        lon = center.get("lon", "?")
        self._text(x + 8, self.y + 12, f"[Kaart: {lat}, {lon}]", "GothamBook", 9.5, "#666666")
        layers = ", ".join(block.get("layers", []))
        if layers:
            self._text(x + 8, self.y + 28, f"Lagen: {layers}", "GothamBook", 8.0, "#999999")

        self.y += 58

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
        bg_rect = fitz.Rect(x - 4, self.y - 2, x + max_w + 4, self.y + block_h - 8)
        self.page.draw_rect(bg_rect, color=None, fill=_hex_to_rgb("#F5F5F5"))

        # Title
        self._text(x, self.y, title, "GothamBold", 9.5, "#401246")
        self.y += 16

        # Formula
        if formula:
            self._text(x + 8, self.y, formula, "GothamBook", 9.5, "#401246")
            self.y += 16

        # Substitution
        if substitution:
            self._text(x + 8, self.y, substitution, "GothamBook", 9.5, "#401246")
            self.y += 16

        # Result
        result_text = f"{result} {unit}".strip()
        self._text(x + 8, self.y, result_text, "GothamBold", 9.5, "#401246")
        self.y += 16

        # Reference
        if reference:
            self._text(x + 8, self.y, f"Ref: {reference}", "GothamBook", 8.0, "#56B49B")
            self.y += 14

        self.y += 12

    # --- Check block ---

    def check(self, block: dict) -> None:
        """Render engineering check block (voldoet/voldoet niet)."""
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
        bg_rect = fitz.Rect(x - 4, self.y - 2, x + max_w + 4, self.y + block_h - 16)
        self.page.draw_rect(bg_rect, color=None, fill=_hex_to_rgb("#F5F5F5"))

        # Description
        self._text(x, self.y, description, "GothamBold", 9.5, "#401246")
        self.y += 16

        # Required vs calculated
        self._text(x + 8, self.y, f"Vereist: {required}", "GothamBook", 9.5, "#401246")
        self.y += 14
        self._text(x + 8, self.y, f"Berekend: {calculated}", "GothamBook", 9.5, "#401246")
        self.y += 14

        # Unity check
        uc_text = f"Unity check: {unity:.2f}"
        self._text(x + 8, self.y, uc_text, "GothamBook", 9.5, "#401246")

        # Result indicator
        is_ok = result.upper() == "VOLDOET"
        result_color = "#56B49B" if is_ok else "#FF0000"
        self._text(x + 200, self.y, result, "GothamBold", 9.5, result_color)
        self.y += 20

    # --- Section rendering ---

    def render_section(self, section: dict) -> None:
        """Render a single section (chapter) with its content blocks."""
        level = section.get("level", 1)
        title = section.get("title", "")
        number = section.get("number", "")

        if section.get("page_break_before", False) or level == 1:
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
            nr_cfg.get("x", 103.0), nr_cfg.get("y_td", 193.9),
            nummer, nr_cfg.get("font", "GothamBold"),
            nr_cfg.get("size", 41.4), nr_cfg.get("color", "#401246"),
        )

        # Title (fixed 20pt, multiline)
        ti_cfg = bijl_cfg.get("titel", {})
        fontsize = ti_cfg.get("size", 20.0)
        line_height = fontsize * 1.6
        for i, line in enumerate(titel.split("\n")):
            y_td = ti_cfg.get("y_td", 262.2) + i * line_height
            self._text(
                ti_cfg.get("x", 136.1), y_td, line,
                ti_cfg.get("font", "GothamBook"),
                fontsize, ti_cfg.get("color", "#FFFFFF"),
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
        self.templates = TemplateSet(brand)
        self.fonts = FontManager()

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

        # Resolve stationery files
        stationery_png = stationery_dir / "2707_BBLrapportage_v01_1.png"
        stationery = {
            "colofon": stationery_dir / "colofon.pdf",
            "standaard": stationery_dir / "standaard.pdf",
            "bijlagen": stationery_dir / "bijlagen.pdf",
            "achterblad": stationery_dir / "achterblad.pdf",
        }

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
                cover_gen.generate(data, stationery_png, tmp_cover)
                parts.append(tmp_cover)

            # 2. Colofon (optioneel)
            if data.get("colofon", {}).get("enabled", True):
                logger.info("Generating colofon...")
                colofon_gen = ColofonGenerator(self.templates, self.fonts)
                colofon_gen.generate(data, stationery["colofon"], tmp_colofon)
                parts.append(tmp_colofon)

            # 3. Content (TOC + sections + appendices + backcover)
            logger.info("Generating content...")
            content = ContentRenderer(self.templates, self.fonts, stationery)
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
                    entries.append((
                        2,
                        block.get("number", ""),
                        block.get("title", ""),
                        page_est,
                    ))

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
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        gen = cls(brand=brand)
        return gen.generate(data, Path(stationery_dir), Path(output_path))
