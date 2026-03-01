"""YAML-driven content module renderer.

Allows defining content modules via YAML configuration instead of writing
Python code for each module type. The YAML describes the visual layout
(elements, columns, spacing) while the generic renderer handles all canvas
drawing.

Two layout patterns are supported via composable element types:

- **Form elements**: ``title``, ``subtitle``, ``form_section``,
  ``field_list``, ``photo``, ``notes`` — for key-value pair pages
  like location_detail.
- **Columnar elements**: ``right_header``, ``column_headers``,
  ``sectioned_rows``, ``data_rows``, ``summary``, ``total_row``
  — for table pages like bic_table.

Usage::

    from bm_reports.modules.yaml_module import create_yaml_module_class

    config = yaml.safe_load(open("location_detail.yaml"))
    LocationDetail = create_yaml_module_class(config)

    # Register like any other module
    ModuleRegistry.register_tenant("symitech", "location_detail", LocationDetail)

    # Use it (same interface as ContentModule)
    module = LocationDetail(data_dict)
"""

from __future__ import annotations

import logging
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader

from bm_reports.modules.base import ContentModule

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default style constants (in points). Can be overridden per YAML config.
# ---------------------------------------------------------------------------
_DEFAULTS: dict[str, float] = {
    "title_height": 28.0,
    "subtitle_height": 22.0,
    "section_header_height": 22.0,
    "column_header_height": 18.0,
    "location_header_height": 24.0,
    "row_height": 16.0,
    "section_gap": 14.0,
    "double_line_gap": 2.7,
    "label_indent": 4.0,
    "label_col_frac": 0.35,
    "total_separator_height": 8.0,
    "total_row_height": 18.0,
    "photo_max_height": 300.0,
    "photo_top_margin": 16.0,
    "placeholder_height": 60.0,
    "bottom_padding": 8.0,
    "notes_line_height": 14.0,
    "notes_top_margin": 10.0,
    "chars_per_line": 80,
}

# Placeholder text color
_PLACEHOLDER_BG = "#F5F5F5"
_PLACEHOLDER_BORDER = "#CCCCCC"


class YamlModule(ContentModule):
    """Generic YAML-driven content module.

    Renders content based on a YAML layout definition stored as the class
    variable ``_layout``. Each element in the layout's ``elements`` list
    is dispatched to a ``_height_<type>`` / ``_draw_<type>`` method pair.

    Subclasses are created dynamically via :func:`create_yaml_module_class`.
    """

    _layout: dict = {}

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _s(self, key: str) -> float:
        """Get style value with fallback to module defaults."""
        return float(
            self._layout.get("style", {}).get(key, _DEFAULTS.get(key, 0.0))
        )

    def _color(self, name: str) -> HexColor:
        """Resolve a named color (primary/secondary/text/white) or hex."""
        colors = self.config.colors
        if name in colors:
            return HexColor(colors[name])
        if name.startswith("#"):
            return HexColor(name)
        return HexColor(colors.get("text", "#000000"))

    def _font(self, name: str) -> str:
        """Resolve a named font (heading/body) or pass through."""
        fonts = self.config.fonts
        return fonts.get(name, name)

    @staticmethod
    def _format_value(value: object, fmt: str | None) -> str:
        """Format a value for display."""
        if value is None:
            return ""
        if fmt == "currency_nl":
            try:
                v = float(value)  # type: ignore[arg-type]
                formatted = (
                    f"{v:,.2f}"
                    .replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                )
                return f"\u20ac {formatted}"
            except (ValueError, TypeError):
                return str(value)
        return str(value)

    # ------------------------------------------------------------------ #
    #  Shared drawing primitives                                           #
    # ------------------------------------------------------------------ #

    def _draw_double_line(self, y: float) -> None:
        """Draw a double horizontal line (Symitech style separator)."""
        c = self.canv
        w = self.available_width
        c.setStrokeColor(self._color("primary"))
        c.setLineWidth(self.config.line_width)
        c.line(0, y, w, y)
        c.line(0, y - self._s("double_line_gap"), w, y - self._s("double_line_gap"))

    def _draw_single_line(self, y: float) -> None:
        """Draw a single horizontal line."""
        c = self.canv
        w = self.available_width
        c.setStrokeColor(self._color("primary"))
        c.setLineWidth(self.config.line_width)
        c.line(0, y, w, y)

    def _draw_col_value(
        self,
        y: float,
        col: dict,
        value: object,
        *,
        force_bold: bool = False,
    ) -> None:
        """Draw a single column value at the configured position."""
        c = self.canv
        w = self.available_width

        text = self._format_value(value, col.get("format"))
        if not text:
            return

        x_frac = col.get("x_frac", 0.0)
        align = col.get("align", "left")
        offset = col.get("offset", 0.0)
        color = col.get("color", "text")
        font = "heading" if force_bold else col.get("font", "body")
        size = col.get("size", self.config.value_size)

        c.setFont(self._font(font), size)
        c.setFillColor(self._color(color))

        x = w * x_frac + offset
        if align == "right":
            c.drawRightString(x, y + 4, text)
        else:
            c.drawString(x, y + 4, text)

    @staticmethod
    def _wrap_text(text: str, max_chars: int = 80) -> list[str]:
        """Simple word-boundary text wrapping."""
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            if current and len(current) + 1 + len(word) > max_chars:
                lines.append(current)
                current = word
            elif current:
                current += " " + word
            else:
                current = word
        if current:
            lines.append(current)
        return lines or [""]

    # ------------------------------------------------------------------ #
    #  Height / Draw dispatch                                              #
    # ------------------------------------------------------------------ #

    def _calculate_height(self) -> float:
        h = 0.0
        for elem in self._layout.get("elements", []):
            h += self._element_height(elem)
        h += self._s("bottom_padding")
        return h

    def _element_height(self, elem: dict) -> float:
        method = getattr(self, f"_height_{elem['type']}", None)
        if method:
            return method(elem)
        logger.warning("YamlModule: unknown element type %r", elem.get("type"))
        return 0.0

    def draw(self) -> None:
        """Draw all elements top-down."""
        y = self.height
        for elem in self._layout.get("elements", []):
            y = self._draw_elem(y, elem)

    def _draw_elem(self, y: float, elem: dict) -> float:
        method = getattr(self, f"_draw_{elem['type']}", None)
        if method:
            return method(y, elem)
        return y

    # ================================================================== #
    #  ELEMENT: title                                                      #
    #  Large heading at top. Optional separator line below.                #
    # ================================================================== #

    def _height_title(self, elem: dict) -> float:  # noqa: ARG002
        return self._s("title_height")

    def _draw_title(self, y: float, elem: dict) -> float:
        c = self.canv
        field = elem.get("field", "title")
        text = self.data.get(field, elem.get("default", ""))

        y -= self._s("title_height")
        c.setFont(self._font("heading"), self.config.heading_size)
        c.setFillColor(self._color("primary"))
        c.drawString(0, y + 4, str(text))

        sep = elem.get("separator")
        if sep == "double_line":
            self._draw_double_line(y)
        elif sep == "single_line":
            self._draw_single_line(y)

        return y

    # ================================================================== #
    #  ELEMENT: subtitle                                                   #
    #  Secondary heading, only shown if data field is present.             #
    # ================================================================== #

    def _height_subtitle(self, elem: dict) -> float:
        field = elem.get("field", "")
        if self.data.get(field):
            return self._s("subtitle_height")
        return 0.0

    def _draw_subtitle(self, y: float, elem: dict) -> float:
        field = elem.get("field", "")
        text = self.data.get(field, "")
        if not text:
            return y

        c = self.canv
        size = elem.get("size", self.config.label_size + 2)

        y -= self._s("subtitle_height")
        c.setFont(self._font("heading"), size)
        c.setFillColor(self._color("text"))
        c.drawString(0, y + 4, str(text))

        return y

    # ================================================================== #
    #  ELEMENT: right_header                                               #
    #  Right-aligned heading (e.g. location name in bic_table).            #
    # ================================================================== #

    def _height_right_header(self, elem: dict) -> float:  # noqa: ARG002
        return self._s("location_header_height")

    def _draw_right_header(self, y: float, elem: dict) -> float:
        c = self.canv
        w = self.available_width
        field = elem.get("field", "")
        text = self.data.get(field, "")

        y -= self._s("location_header_height")
        if text:
            c.setFont(self._font("heading"), self.config.heading_size)
            c.setFillColor(self._color("primary"))
            c.drawRightString(w, y + 4, str(text))

        return y

    # ================================================================== #
    #  ELEMENT: form_section                                               #
    #  Section header + double line + key-value rows.                      #
    # ================================================================== #

    def _height_form_section(self, elem: dict) -> float:
        data_key = elem.get("data_key", "")
        section_data = self.data.get(data_key, {})
        if not section_data:
            return 0.0

        h = self._s("section_header_height")
        fields = elem.get("fields", [])
        skip_empty = elem.get("skip_empty", True)

        if skip_empty:
            count = sum(1 for f in fields if section_data.get(f["key"]))
        else:
            count = len(fields)

        h += count * self._s("row_height")
        h += self._s("section_gap")
        return h

    def _draw_form_section(self, y: float, elem: dict) -> float:
        data_key = elem.get("data_key", "")
        section_data = self.data.get(data_key, {})
        if not section_data:
            return y

        c = self.canv
        w = self.available_width
        cfg = self.config

        label_right = w * self._s("label_col_frac")
        value_x = label_right + 8

        # Section header
        y -= self._s("section_header_height")
        title_field = elem.get("title_field", "section_title")
        title = section_data.get(title_field, "")
        c.setFont(self._font("heading"), cfg.label_size)
        c.setFillColor(self._color("secondary"))
        c.drawString(0, y + 6, str(title))

        # Double line
        self._draw_double_line(y)

        # Key-value rows
        skip_empty = elem.get("skip_empty", True)
        for field_def in elem.get("fields", []):
            value = section_data.get(field_def["key"], "")
            if skip_empty and not value:
                continue

            y -= self._s("row_height")
            # Label (secondary color)
            c.setFont(self._font("body"), cfg.label_size)
            c.setFillColor(self._color("secondary"))
            c.drawString(self._s("label_indent"), y + 4, field_def.get("label", ""))
            # Value (text color)
            c.setFillColor(self._color("text"))
            c.drawString(value_x, y + 4, str(value))

        y -= self._s("section_gap")
        return y

    # ================================================================== #
    #  ELEMENT: field_list                                                 #
    #  Dynamic key-value list from data (e.g. object_description fields).  #
    #  Reads a list of {label, value} dicts from the data.                 #
    # ================================================================== #

    def _height_field_list(self, elem: dict) -> float:
        data_key = elem.get("data_key", "fields")
        fields = self.data.get(data_key, [])
        if not fields:
            return 0.0
        h = self._s("section_gap")  # space for double line
        h += len(fields) * self._s("row_height")
        h += self._s("section_gap")
        return h

    def _draw_field_list(self, y: float, elem: dict) -> float:
        data_key = elem.get("data_key", "fields")
        fields = self.data.get(data_key, [])
        if not fields:
            return y

        c = self.canv
        w = self.available_width
        cfg = self.config

        label_right = w * self._s("label_col_frac")
        value_x = label_right + 8
        label_key = elem.get("label_key", "label")
        value_key = elem.get("value_key", "value")

        # Double line separator
        y -= self._s("section_gap")
        self._draw_double_line(y)

        for fld in fields:
            y -= self._s("row_height")
            # Label (secondary color)
            c.setFont(self._font("body"), cfg.label_size)
            c.setFillColor(self._color("secondary"))
            c.drawString(self._s("label_indent"), y + 4, str(fld.get(label_key, "")))
            # Value (text color)
            c.setFillColor(self._color("text"))
            c.drawString(value_x, y + 4, str(fld.get(value_key, "")))

        y -= self._s("section_gap")
        return y

    # ================================================================== #
    #  ELEMENT: column_headers                                             #
    #  Table column header row with optional line below.                   #
    # ================================================================== #

    def _height_column_headers(self, elem: dict) -> float:  # noqa: ARG002
        return self._s("column_header_height")

    def _draw_column_headers(self, y: float, elem: dict) -> float:
        c = self.canv
        w = self.available_width
        cfg = self.config

        y -= self._s("column_header_height")
        c.setFont(self._font("heading"), cfg.label_size)
        c.setFillColor(self._color("secondary"))

        for label_def in elem.get("labels", []):
            text = label_def.get("text", "")
            x_frac = label_def.get("x_frac", 0.0)
            align = label_def.get("align", "left")
            offset = label_def.get("offset", 0.0)

            x = w * x_frac + offset
            if align == "right":
                c.drawRightString(x, y + 4, text)
            else:
                c.drawString(x, y + 4, text)

        if elem.get("line_below"):
            self._draw_single_line(y)

        return y

    # ================================================================== #
    #  ELEMENT: sectioned_rows                                             #
    #  Multiple sections, each with title + double line + columnar rows.   #
    # ================================================================== #

    def _height_sectioned_rows(self, elem: dict) -> float:
        data_key = elem.get("data_key", "sections")
        sections = self.data.get(data_key, [])
        section_gap = self._s("section_gap")
        section_title_h = self._s("section_header_height")
        row_h = self._s("row_height")

        h = 0.0
        for section in sections:
            h += section_gap  # gap before section
            h += section_title_h  # title + double line
            h += len(section.get("rows", [])) * row_h
            h += section_gap  # gap after rows
        return h

    def _draw_sectioned_rows(self, y: float, elem: dict) -> float:
        c = self.canv
        cfg = self.config
        data_key = elem.get("data_key", "sections")
        sections = self.data.get(data_key, [])
        columns = elem.get("columns", [])

        for section in sections:
            y -= self._s("section_gap")
            y -= self._s("section_header_height")

            # Section title + double line
            title_field = elem.get("title_field", "title")
            title = section.get(title_field, "")
            c.setFont(self._font("heading"), cfg.label_size)
            c.setFillColor(self._color("text"))
            c.drawString(0, y + 4, str(title))
            self._draw_double_line(y)

            # Data rows
            for row in section.get("rows", []):
                y -= self._s("row_height")
                for col in columns:
                    value = row.get(col["key"], "")
                    self._draw_col_value(y, col, value)

            y -= self._s("section_gap")

        return y

    # ================================================================== #
    #  ELEMENT: data_rows                                                  #
    #  Simple ungrouped data rows (no section titles).                     #
    # ================================================================== #

    def _height_data_rows(self, elem: dict) -> float:
        data_key = elem.get("data_key", "rows")
        rows = self.data.get(data_key, [])
        return len(rows) * self._s("row_height")

    def _draw_data_rows(self, y: float, elem: dict) -> float:
        data_key = elem.get("data_key", "rows")
        rows = self.data.get(data_key, [])
        columns = elem.get("columns", [])

        for row in rows:
            y -= self._s("row_height")
            for col in columns:
                value = row.get(col["key"], "")
                self._draw_col_value(y, col, value)

        return y

    # ================================================================== #
    #  ELEMENT: summary                                                    #
    #  Summary section with title, rows and optional total.                #
    # ================================================================== #

    def _height_summary(self, elem: dict) -> float:
        data_key = elem.get("data_key", "summary")
        summary = self.data.get(data_key)
        if not summary:
            return 0.0

        section_gap = self._s("section_gap")
        h = section_gap + self._s("section_header_height") + section_gap
        h += len(summary.get("rows", [])) * self._s("row_height")

        if summary.get(elem.get("total_key", "total")):
            h += self._s("total_separator_height") + self._s("row_height")

        h += section_gap
        return h

    def _draw_summary(self, y: float, elem: dict) -> float:
        c = self.canv
        cfg = self.config
        data_key = elem.get("data_key", "summary")
        summary = self.data.get(data_key)
        if not summary:
            return y

        columns = elem.get("columns", [])

        y -= self._s("section_gap")
        y -= self._s("section_header_height")

        # Summary title + double line
        title_field = elem.get("title_field", "title")
        title = summary.get(title_field, "Samenvatting")
        c.setFont(self._font("heading"), cfg.label_size)
        c.setFillColor(self._color("text"))
        c.drawString(0, y + 4, str(title))
        self._draw_double_line(y)

        # Summary rows
        for row in summary.get("rows", []):
            y -= self._s("row_height")
            for col in columns:
                value = row.get(col["key"], "")
                self._draw_col_value(y, col, value)

        # Total row
        total_key = elem.get("total_key", "total")
        total = summary.get(total_key)
        if total:
            y -= self._s("total_separator_height")
            self._draw_single_line(
                y + self._s("total_separator_height") / 2,
            )

            y -= self._s("row_height")
            for col in columns:
                value = total.get(col["key"], "")
                self._draw_col_value(y, col, value, force_bold=True)

        y -= self._s("section_gap")
        return y

    # ================================================================== #
    #  ELEMENT: total_row                                                  #
    #  Standalone total row with separator line.                           #
    # ================================================================== #

    def _height_total_row(self, elem: dict) -> float:
        data_key = elem.get("data_key", "total")
        if self.data.get(data_key) is not None:
            return self._s("total_separator_height") + self._s("total_row_height")
        return 0.0

    def _draw_total_row(self, y: float, elem: dict) -> float:
        c = self.canv
        w = self.available_width
        cfg = self.config
        data_key = elem.get("data_key", "total")
        value = self.data.get(data_key)
        if value is None:
            return y

        y -= self._s("total_separator_height")
        self._draw_single_line(y + self._s("total_separator_height") / 2)

        y -= self._s("total_row_height")
        label = elem.get("label", "Totaal")
        fmt = elem.get("format")
        indent = self._s("label_indent")

        c.setFont(self._font("heading"), cfg.value_size)
        c.setFillColor(self._color("text"))
        c.drawString(indent, y + 4, label)

        # Right-aligned formatted value
        text = self._format_value(value, fmt)
        c.drawRightString(w, y + 4, text)

        return y

    # ================================================================== #
    #  ELEMENT: photo                                                      #
    #  Image with placeholder fallback.                                    #
    # ================================================================== #

    def _height_photo(self, elem: dict) -> float:
        field = elem.get("field", "photo_path")
        photo_path = self.data.get(field)
        h = self._s("photo_top_margin")

        if photo_path and Path(photo_path).is_file():
            h += self._s("photo_max_height")
        else:
            h += self._s("placeholder_height")

        return h

    def _draw_photo(self, y: float, elem: dict) -> float:
        c = self.canv
        w = self.available_width
        field = elem.get("field", "photo_path")
        photo_path = self.data.get(field)

        y -= self._s("photo_top_margin")

        if photo_path and Path(photo_path).is_file():
            try:
                img = ImageReader(photo_path)
                img_w, img_h = img.getSize()
                max_h = self._s("photo_max_height")
                scale = min(w / img_w, max_h / img_h)
                draw_w = img_w * scale
                draw_h = img_h * scale
                x_offset = (w - draw_w) / 2
                c.drawImage(
                    photo_path,
                    x_offset,
                    y - draw_h,
                    width=draw_w,
                    height=draw_h,
                    preserveAspectRatio=True,
                )
                return y - draw_h
            except Exception:
                pass  # Fall through to placeholder

        # Placeholder
        ph = self._s("placeholder_height")
        placeholder_text = elem.get("placeholder_text", "[FOTO]")

        c.setStrokeColor(HexColor(_PLACEHOLDER_BORDER))
        c.setFillColor(HexColor(_PLACEHOLDER_BG))
        c.setLineWidth(0.5)
        c.rect(0, y - ph, w, ph, fill=1)

        c.setFont(self._font("body"), 9)
        c.setFillColor(self._color("text"))
        c.drawCentredString(w / 2, y - ph / 2 - 3, placeholder_text)

        return y - ph

    # ================================================================== #
    #  ELEMENT: notes                                                      #
    #  Wrapped text block with optional separator above.                   #
    # ================================================================== #

    def _height_notes(self, elem: dict) -> float:
        field = elem.get("field", "notes")
        text = self.data.get(field, "")
        if not text:
            return 0.0

        h = self._s("notes_top_margin")
        max_chars = int(self._s("chars_per_line"))
        num_lines = max(1, len(str(text)) // max_chars + 1)
        h += num_lines * self._s("notes_line_height")
        # Extra line for first line after separator
        h += self._s("notes_line_height")
        h += self._s("section_gap")
        return h

    def _draw_notes(self, y: float, elem: dict) -> float:
        c = self.canv
        field = elem.get("field", "notes")
        text = self.data.get(field, "")
        if not text:
            return y

        y -= self._s("notes_top_margin")

        # Separator above
        if elem.get("separator_above", True):
            self._draw_double_line(y)

        y -= self._s("notes_line_height")
        c.setFont(self._font("body"), self.config.value_size)
        c.setFillColor(self._color("text"))

        max_chars = int(self._s("chars_per_line"))
        for line in self._wrap_text(str(text), max_chars):
            c.drawString(self._s("label_indent"), y + 4, line)
            y -= self._s("notes_line_height")

        y -= self._s("section_gap")
        return y


# ====================================================================== #
#  Factory function                                                        #
# ====================================================================== #


def create_yaml_module_class(layout_config: dict) -> type[YamlModule]:
    """Create a new module class bound to a specific YAML layout.

    The returned class can be registered in :class:`ModuleRegistry` and
    instantiated with ``(data, config, available_width)`` just like any
    other :class:`ContentModule` subclass.

    Args:
        layout_config: Parsed YAML layout definition.

    Returns:
        A new class derived from :class:`YamlModule`.
    """
    name = layout_config.get("name", "YamlModule")
    class_name = "".join(
        part.capitalize() for part in name.split("_")
    ) + "YamlModule"

    return type(class_name, (YamlModule,), {"_layout": layout_config})


def load_yaml_modules_from_dir(
    directory: Path,
    tenant: str | None = None,
) -> dict[str, type[YamlModule]]:
    """Scan a directory for YAML module definitions and create classes.

    Args:
        directory: Path to directory containing ``*.yaml`` files.
        tenant: Optional tenant name (stored in result, not enforced).

    Returns:
        Dict mapping module name to created class.
    """
    import yaml

    modules: dict[str, type[YamlModule]] = {}
    directory = Path(directory)

    if not directory.is_dir():
        logger.debug("YAML modules directory not found: %s", directory)
        return modules

    for yaml_file in sorted(directory.glob("*.yaml")):
        try:
            config = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            if not isinstance(config, dict) or "elements" not in config:
                logger.debug("Skipping %s: no elements key", yaml_file.name)
                continue

            if "name" not in config:
                config["name"] = yaml_file.stem

            module_class = create_yaml_module_class(config)
            modules[config["name"]] = module_class
            logger.debug(
                "Loaded YAML module %r from %s",
                config["name"],
                yaml_file.name,
            )
        except Exception:
            logger.exception("Failed to load YAML module from %s", yaml_file)

    return modules
