"""Template renderer — Generieke canvas renderer voor pixel-perfect pagina templates.

Leest een TemplateConfig (uit YAML) en tekent elke pagina layer-voor-layer
op een ReportLab canvas. Bureau-onafhankelijk: dezelfde renderer werkt voor
elk template YAML.

Drawing model:
    - Alle coördinaten in PDF y-up systeem (origin = linksonder pagina).
    - Tekst y-waarden zijn baselines tenzij anders aangegeven.
    - $colors.primary en $fonts.heading worden geresolved tegen template config.
    - `bind` velden worden geresolved tegen rapport data dict.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import mm

from bm_reports.core.template_schema import (
    BadgeGroupLayer,
    ClippedImageLayer,
    ImageLayer,
    LayerBase,
    LineLayer,
    PageConfig,
    PageNumberLayer,
    PolygonLayer,
    RectLayer,
    TableLayer,
    TemplateConfig,
    TextBlockLayer,
    TextLayer,
)

logger = logging.getLogger(__name__)

# Assets directory
ASSETS_DIR = Path(__file__).parent.parent / "assets"


class TemplateRenderer:
    """Generieke renderer die template layers tekent op een ReportLab canvas.

    Args:
        template: Geladen TemplateConfig.
        assets_dir: Pad naar assets directory voor afbeeldingen.
    """

    def __init__(
        self,
        template: TemplateConfig,
        assets_dir: Path | None = None,
    ) -> None:
        self.template = template
        self.assets_dir = assets_dir or ASSETS_DIR

    # ============================================================
    # Publieke API
    # ============================================================

    def draw_page(
        self,
        canvas,
        page_key: str,
        data: dict[str, Any] | None = None,
        page_number: int | None = None,
    ) -> None:
        """Teken een complete pagina op het canvas.

        Args:
            canvas: ReportLab canvas.
            page_key: Pagina type sleutel (bijv. 'cover', 'colofon').
            data: Rapport data dict voor dynamische velden.
            page_number: Huidig paginanummer.
        """
        page_cfg = self.template.pages.get(page_key)
        if page_cfg is None:
            logger.warning("Pagina '%s' niet gevonden in template", page_key)
            return

        canvas.saveState()
        for layer in page_cfg.layers:
            self._draw_layer(canvas, layer, data or {}, page_number)
        canvas.restoreState()

    # ============================================================
    # Color & Font resolution
    # ============================================================

    def _resolve_color(self, ref: str) -> HexColor | None:
        """Resolve een kleur referentie naar HexColor.

        Ondersteunt:
            - Direct hex: '#401146'
            - Template ref: '$colors.primary'
            - Speciale waarden: 'white', 'black'
        """
        if not ref:
            return None

        if ref == "white":
            return white
        if ref == "black":
            return black

        if ref.startswith("$colors."):
            key = ref.split(".", 1)[1]
            hex_val = self.template.colors.get(key)
            if hex_val:
                return HexColor(hex_val)
            logger.warning("Kleur referentie niet gevonden: %s", ref)
            return None

        if ref.startswith("#"):
            return HexColor(ref)

        # Probeer als directe kleurnaam
        hex_val = self.template.colors.get(ref)
        if hex_val:
            return HexColor(hex_val)

        return None

    def _resolve_font(self, ref: str) -> str:
        """Resolve een font referentie naar font naam.

        Ondersteunt:
            - Direct: 'Helvetica-Bold'
            - Template ref: '$fonts.heading'
        """
        if not ref:
            return "Helvetica"

        if ref.startswith("$fonts."):
            key = ref.split(".", 1)[1]
            font_name = self.template.fonts.get(key)
            if font_name:
                return font_name
            logger.warning("Font referentie niet gevonden: %s", ref)
            return "Helvetica"

        return ref

    def _resolve_bind(self, bind: str, data: dict[str, Any]) -> Any:
        """Resolve een bind pad naar een waarde uit de data dict.

        Ondersteunt geneste paden: 'cover.image' → data['cover']['image']
        """
        if not bind:
            return None

        parts = bind.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
            if current is None:
                return None
        return current

    # ============================================================
    # Layer drawing
    # ============================================================

    def _draw_layer(
        self,
        canvas,
        layer: LayerBase,
        data: dict[str, Any],
        page_number: int | None,
    ) -> None:
        """Dispatch een layer naar de juiste teken-methode."""

        # Conditionele layer: skip als bind-waarde leeg is
        if layer.condition:
            val = self._resolve_bind(layer.condition, data)
            if not val:
                return

        # Skip dynamische layers zonder data als bind is gezet maar leeg
        if not layer.static and layer.bind:
            val = self._resolve_bind(layer.bind, data)
            if val is None and layer.type not in ("table",):
                # Table layers mogen leeg zijn (worden dan overgeslagen)
                return

        dispatch = {
            "rect": self._draw_rect,
            "polygon": self._draw_polygon,
            "image": self._draw_image,
            "clipped_image": self._draw_clipped_image,
            "text": self._draw_text,
            "text_block": self._draw_text_block,
            "badge_group": self._draw_badge_group,
            "line": self._draw_line,
            "page_number": self._draw_page_number,
            "table": self._draw_table,
        }

        handler = dispatch.get(layer.type)
        if handler:
            try:
                handler(canvas, layer, data, page_number)
            except Exception:
                logger.exception("Fout bij tekenen layer: %s (%s)", layer.role, layer.type)
        else:
            logger.warning("Geen handler voor layer type: %s", layer.type)

    def _draw_rect(self, canvas, layer: RectLayer, data, page_number) -> None:
        """Teken een gevulde rechthoek."""
        color = self._resolve_color(layer.fill)
        if color:
            canvas.setFillColor(color)

        stroke_color = self._resolve_color(layer.stroke)
        has_stroke = bool(stroke_color)
        if has_stroke:
            canvas.setStrokeColor(stroke_color)
            canvas.setLineWidth(layer.stroke_width or 0.5)

        if layer.radius > 0:
            canvas.roundRect(
                layer.x, layer.y, layer.w, layer.h,
                layer.radius,
                fill=1 if color else 0,
                stroke=1 if has_stroke else 0,
            )
        else:
            canvas.rect(
                layer.x, layer.y, layer.w, layer.h,
                fill=1 if color else 0,
                stroke=1 if has_stroke else 0,
            )

    def _draw_polygon(self, canvas, layer: PolygonLayer, data, page_number) -> None:
        """Teken een gevuld polygon."""
        if len(layer.points) < 3:
            return

        color = self._resolve_color(layer.fill)
        if color:
            canvas.setFillColor(color)

        path = canvas.beginPath()
        path.moveTo(layer.points[0][0], layer.points[0][1])
        for pt in layer.points[1:]:
            path.lineTo(pt[0], pt[1])
        path.close()
        canvas.drawPath(path, fill=1 if color else 0, stroke=0)

    def _draw_image(self, canvas, layer: ImageLayer, data, page_number) -> None:
        """Teken een afbeelding (statisch of dynamisch)."""
        if layer.static:
            img_path = self.assets_dir / layer.source
        else:
            val = self._resolve_bind(layer.bind, data)
            if not val:
                return
            img_path = Path(val)

        if not img_path.exists():
            logger.warning("Afbeelding niet gevonden: %s", img_path)
            return

        suffix = img_path.suffix.lower()
        if suffix == ".svg":
            self._draw_svg(canvas, img_path, layer.x, layer.y, layer.w, layer.h)
        else:
            kwargs = {"x": layer.x, "y": layer.y, "mask": layer.mask}
            if layer.w > 0:
                kwargs["width"] = layer.w
            if layer.h > 0:
                kwargs["height"] = layer.h
            if (layer.w > 0) != (layer.h > 0):
                kwargs["preserveAspectRatio"] = True
            canvas.drawImage(str(img_path), **kwargs)

    def _draw_svg(self, canvas, path: Path, x, y, w, h) -> None:
        """Teken een SVG afbeelding."""
        try:
            from reportlab.graphics import renderPDF
            from svglib.svglib import svg2rlg

            drawing = svg2rlg(str(path))
            if drawing is None:
                return

            if w > 0 or h > 0:
                orig_w, orig_h = drawing.width, drawing.height
                if w > 0 and h > 0:
                    sx, sy = w / orig_w, h / orig_h
                elif w > 0:
                    sx = sy = w / orig_w
                else:
                    sx = sy = h / orig_h
                drawing.width = orig_w * sx
                drawing.height = orig_h * sy
                drawing.scale(sx, sy)

            renderPDF.draw(drawing, canvas, x, y)
        except Exception:
            logger.exception("SVG render fout: %s", path)

    def _draw_clipped_image(
        self, canvas, layer: ClippedImageLayer, data, page_number,
    ) -> None:
        """Teken een afbeelding met clip-path polygon."""
        # Resolve image path
        img_path_val = self._resolve_bind(layer.bind, data)
        if not img_path_val:
            return
        img_path = Path(img_path_val)
        if not img_path.exists():
            logger.warning("Clipped image niet gevonden: %s", img_path)
            return

        if len(layer.clip_polygon) < 3:
            logger.warning("Clip polygon heeft < 3 punten")
            return

        rect = layer.image_rect

        canvas.saveState()

        # Bouw clip path
        clip = canvas.beginPath()
        clip.moveTo(layer.clip_polygon[0][0], layer.clip_polygon[0][1])
        for pt in layer.clip_polygon[1:]:
            clip.lineTo(pt[0], pt[1])
        clip.close()
        canvas.clipPath(clip, stroke=0, fill=0)

        # Teken afbeelding binnen clip
        canvas.drawImage(
            str(img_path),
            x=rect.get("x", 0),
            y=rect.get("y", 0),
            width=rect.get("w", 0),
            height=rect.get("h", 0),
            mask="auto",
        )

        canvas.restoreState()

    def _draw_text(self, canvas, layer: TextLayer, data, page_number) -> None:
        """Teken een tekstregel."""
        # Bepaal tekst
        if layer.static:
            text = layer.content
        else:
            text = self._resolve_bind(layer.bind, data)
            if text is None:
                text = layer.content  # Fallback naar statische content
        text = str(text)

        if not text:
            return

        font = self._resolve_font(layer.font)
        color = self._resolve_color(layer.color)
        if color:
            canvas.setFillColor(color)

        canvas.setFont(font, layer.size)

        if layer.align == "right":
            canvas.drawRightString(layer.x, layer.y, text)
        elif layer.align == "center":
            canvas.drawCentredString(layer.x, layer.y, text)
        else:
            canvas.drawString(layer.x, layer.y, text)

    def _draw_text_block(
        self, canvas, layer: TextBlockLayer, data, page_number,
    ) -> None:
        """Teken meerdere tekst-spans op dezelfde of nabije posities."""
        for span in layer.spans:
            content = span.get("content", "")
            if not content and span.get("bind"):
                content = str(self._resolve_bind(span["bind"], data) or "")
            if not content:
                continue

            font = self._resolve_font(span.get("font", ""))
            size = float(span.get("size", 10))
            color = self._resolve_color(span.get("color", ""))
            x = float(span.get("x", 0))
            y = float(span.get("y", 0))

            if color:
                canvas.setFillColor(color)
            canvas.setFont(font, size)
            canvas.drawString(x, y, content)

    def _draw_badge_group(
        self, canvas, layer: BadgeGroupLayer, data, page_number,
    ) -> None:
        """Teken een groep rounded-rect badges met tekst."""
        for badge in layer.badges:
            if len(badge.rect) < 4:
                continue

            bx, by, bw, bh = badge.rect
            radius = badge.radius

            # Achtergrond
            fill_color = self._resolve_color(badge.fill)
            if fill_color:
                canvas.setFillColor(fill_color)
                canvas.roundRect(bx, by, bw, bh, radius, fill=1, stroke=0)

            # Tekst gecentreerd in badge
            text_color = self._resolve_color(badge.text_color)
            if text_color:
                canvas.setFillColor(text_color)

            font = self._resolve_font(badge.font) if badge.font else self._resolve_font("$fonts.medium")
            canvas.setFont(font, badge.font_size)
            canvas.drawCentredString(
                bx + bw / 2,
                by + (bh - badge.font_size) / 2 + 1,  # Verticaal centreren
                badge.text,
            )

    def _draw_line(self, canvas, layer: LineLayer, data, page_number) -> None:
        """Teken een lijn."""
        color = self._resolve_color(layer.color)
        if color:
            canvas.setStrokeColor(color)
        canvas.setLineWidth(layer.width)

        if layer.dash:
            canvas.setDash(layer.dash)

        canvas.line(layer.x1, layer.y1, layer.x2, layer.y2)

        if layer.dash:
            canvas.setDash([])  # Reset

    def _draw_page_number(
        self, canvas, layer: PageNumberLayer, data, page_number,
    ) -> None:
        """Teken een paginanummer."""
        if page_number is None:
            return

        font = self._resolve_font(layer.font)
        color = self._resolve_color(layer.color)
        if color:
            canvas.setFillColor(color)
        canvas.setFont(font, layer.size)

        text = str(page_number)
        if layer.align == "right":
            canvas.drawRightString(layer.x, layer.y, text)
        elif layer.align == "center":
            canvas.drawCentredString(layer.x, layer.y, text)
        else:
            canvas.drawString(layer.x, layer.y, text)

    def _draw_table(self, canvas, layer: TableLayer, data, page_number) -> None:
        """Teken een twee-koloms metadata tabel (colofon stijl)."""
        label_font = self._resolve_font(layer.label_font)
        value_font = self._resolve_font(layer.value_font)
        label_color = self._resolve_color(layer.label_color)
        value_color = self._resolve_color(layer.value_color)
        sep_color = self._resolve_color(layer.separator_color)

        current_y = layer.y_start

        for row in layer.rows:
            label = row.get("label", "")
            # Waarde: statisch of gebind
            if row.get("bind"):
                value = self._resolve_bind(row["bind"], data)
                value = str(value) if value else ""
            else:
                value = row.get("value", "")

            if not label and not value:
                continue

            # Label
            if label_color:
                canvas.setFillColor(label_color)
            canvas.setFont(label_font, layer.label_size)
            canvas.drawString(layer.col1_x, current_y, label)

            # Waarde
            if value:
                if value_color:
                    canvas.setFillColor(value_color)
                canvas.setFont(value_font, layer.value_size)
                # Multi-line support (waarde kan \n bevatten)
                lines = str(value).split("\n") if "\n" in str(value) else [str(value)]
                line_y = current_y
                for line in lines:
                    canvas.drawString(layer.col2_x, line_y, line)
                    line_y -= layer.value_size * 1.3

            # Scheidingslijn
            if sep_color and layer.separator_width > 0:
                canvas.setStrokeColor(sep_color)
                canvas.setLineWidth(layer.separator_width)
                sep_y = current_y - layer.row_height + 6
                canvas.line(
                    layer.col1_x, sep_y,
                    layer.separator_x_end or layer.col2_x + 200, sep_y,
                )

            current_y -= layer.row_height
