"""Brand renderer — Tekent header/footer elementen op de ReportLab canvas."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from reportlab.lib.colors import HexColor

from openaec_reports.core.brand import BrandConfig, ElementConfig, ZoneConfig
from openaec_reports.core.document import MM_TO_PT, DocumentConfig
from openaec_reports.core.styles import BM_COLORS

logger = logging.getLogger(__name__)


class BrandRenderer:
    """Tekent brand header/footer elementen op een ReportLab canvas.

    Coördinatensysteem:
        - x: mm vanaf linker paginarand (0 = linkerkant pagina)
        - y: mm vanaf onderkant van de zone
        - Footer zone: onderkant = onderkant pagina (y=0 is pagerand)
        - Header zone: onderkant = bovenkant pagina minus header hoogte

    Usage:
        renderer = BrandRenderer(brand, assets_dir)
        # In PageTemplate onPage callback:
        renderer.draw_page(canvas, doc, config)
    """

    def __init__(self, brand: BrandConfig, assets_dir: Path):
        self._brand = brand
        self._assets_dir = assets_dir

    def draw_page(self, canvas, doc, config: DocumentConfig) -> None:
        """Teken header en footer op de huidige pagina.

        Args:
            canvas: ReportLab canvas.
            doc: ReportLab BaseDocTemplate.
            config: Document configuratie met projectinfo.
        """
        page_num = canvas.getPageNumber()
        variables = self._build_variables(config, page_num)

        self.draw_header(canvas, config, variables)
        self.draw_footer(canvas, config, variables)

    def draw_header(
        self,
        canvas,
        config: DocumentConfig,
        variables: dict[str, str],
    ) -> None:
        """Teken header elementen. Skipt als height=0."""
        zone = self._brand.header
        if zone.height <= 0:
            return

        # Header zone origin: bovenkant pagina minus header hoogte
        page_h = config.effective_height_pt
        zone_origin_y = page_h - zone.height * MM_TO_PT

        self._draw_zone(canvas, zone, zone_origin_y, variables)

    def draw_footer(
        self,
        canvas,
        config: DocumentConfig,
        variables: dict[str, str],
    ) -> None:
        """Teken footer elementen. Skipt als height=0."""
        zone = self._brand.footer
        if zone.height <= 0:
            return

        # Footer zone origin: onderkant pagina (y=0)
        zone_origin_y = 0.0

        self._draw_zone(canvas, zone, zone_origin_y, variables)

    def _draw_zone(
        self,
        canvas,
        zone: ZoneConfig,
        zone_origin_y: float,
        variables: dict[str, str],
    ) -> None:
        """Teken alle elementen in een zone.

        Args:
            canvas: ReportLab canvas.
            zone: Zone configuratie.
            zone_origin_y: Absolute y-positie van de onderkant van de zone (in points).
            variables: Template variabelen voor tekst substitutie.
        """
        canvas.saveState()

        for elem in zone.elements:
            try:
                if elem.type == "rect":
                    self._draw_rect(canvas, elem, zone_origin_y)
                elif elem.type == "text":
                    self._draw_text(canvas, elem, zone_origin_y, variables)
                elif elem.type == "line":
                    self._draw_line(canvas, elem, zone_origin_y)
                elif elem.type == "image":
                    self._draw_image(canvas, elem, zone_origin_y)
                else:
                    logger.warning("Onbekend element type: %s", elem.type)
            except (ValueError, OSError, KeyError):
                logger.exception("Fout bij tekenen van %s element", elem.type)

        canvas.restoreState()

    def _draw_rect(self, canvas, elem: ElementConfig, zone_y: float) -> None:
        """Teken een rechthoek."""
        x = elem.x * MM_TO_PT
        y = zone_y + elem.y * MM_TO_PT
        w = elem.width * MM_TO_PT
        h = elem.height * MM_TO_PT

        fill = 1 if elem.fill else 0
        stroke = 1 if elem.stroke else 0

        if elem.fill:
            canvas.setFillColor(HexColor(self._resolve_color(elem.fill)))
        if elem.stroke:
            canvas.setStrokeColor(HexColor(self._resolve_color(elem.stroke)))
            canvas.setLineWidth(elem.stroke_width)

        canvas.rect(x, y, w, h, fill=fill, stroke=stroke)

    def _draw_text(
        self,
        canvas,
        elem: ElementConfig,
        zone_y: float,
        variables: dict[str, str],
    ) -> None:
        """Teken tekst met variabele substitutie."""
        x = elem.x * MM_TO_PT
        y = zone_y + elem.y * MM_TO_PT

        # Resolve font en kleur
        font = self._resolve_font(elem.font) if elem.font else "Helvetica"
        size = elem.size if elem.size > 0 else 9.0
        color = self._resolve_color(elem.color) if elem.color else BM_COLORS.text

        canvas.setFont(font, size)
        canvas.setFillColor(HexColor(color))

        # Variabele substitutie
        text = self._resolve_variables(elem.content, variables)

        if elem.align == "right":
            canvas.drawRightString(x, y, text)
        elif elem.align == "center":
            canvas.drawCentredString(x, y, text)
        else:
            canvas.drawString(x, y, text)

    def _draw_line(self, canvas, elem: ElementConfig, zone_y: float) -> None:
        """Teken een horizontale lijn."""
        x1 = elem.x * MM_TO_PT
        y = zone_y + elem.y * MM_TO_PT
        x2 = x1 + elem.width * MM_TO_PT

        color = self._resolve_color(elem.color) if elem.color else BM_COLORS.text
        canvas.setStrokeColor(HexColor(color))
        canvas.setLineWidth(elem.stroke_width)
        canvas.line(x1, y, x2, y)

    def _draw_image(self, canvas, elem: ElementConfig, zone_y: float) -> None:
        """Teken een afbeelding (PNG of SVG)."""
        x = elem.x * MM_TO_PT
        y = zone_y + elem.y * MM_TO_PT

        image_path = self._assets_dir / elem.src
        if not image_path.exists():
            logger.warning("Afbeelding niet gevonden: %s", image_path)
            return

        suffix = image_path.suffix.lower()

        if suffix == ".svg":
            self._draw_svg(canvas, image_path, x, y, elem)
        else:
            # PNG, JPG, etc.
            kwargs: dict = {"x": x, "y": y}
            if elem.width > 0:
                kwargs["width"] = elem.width * MM_TO_PT
            if elem.height > 0:
                kwargs["height"] = elem.height * MM_TO_PT
            # preserveAspectRatio als slechts één dimensie opgegeven
            if (elem.width > 0) != (elem.height > 0):
                kwargs["preserveAspectRatio"] = True
            kwargs["mask"] = "auto"
            canvas.drawImage(str(image_path), **kwargs)

    def _draw_svg(
        self,
        canvas,
        path: Path,
        x: float,
        y: float,
        elem: ElementConfig,
    ) -> None:
        """Teken een SVG afbeelding via svglib conversie."""
        try:
            from reportlab.graphics import renderPDF
            from svglib.svglib import svg2rlg

            drawing = svg2rlg(str(path))
            if drawing is None:
                logger.warning("SVG kon niet worden geladen: %s", path)
                return

            # Schaal indien nodig
            if elem.width > 0 or elem.height > 0:
                orig_w = drawing.width
                orig_h = drawing.height
                if elem.width > 0 and elem.height > 0:
                    sx = (elem.width * MM_TO_PT) / orig_w
                    sy = (elem.height * MM_TO_PT) / orig_h
                elif elem.width > 0:
                    sx = sy = (elem.width * MM_TO_PT) / orig_w
                else:
                    sx = sy = (elem.height * MM_TO_PT) / orig_h
                drawing.width = orig_w * sx
                drawing.height = orig_h * sy
                drawing.scale(sx, sy)

            renderPDF.draw(drawing, canvas, x, y)
        except ImportError:
            logger.warning("svglib niet geïnstalleerd, SVG overgeslagen: %s", path)
        except (ValueError, OSError):
            logger.exception("Fout bij SVG rendering: %s", path)

    def _resolve_color(self, ref: str) -> str:
        """Resolve een kleur referentie naar hex waarde.

        Args:
            ref: "$primary" (opzoeken in brand.colors) of "#38BDA0" (direct).

        Returns:
            Hex kleurwaarde.
        """
        if ref.startswith("$"):
            key = ref[1:]
            return self._brand.colors.get(key, BM_COLORS.text)
        return ref

    def _resolve_font(self, ref: str) -> str:
        """Resolve een font referentie naar font naam.

        Args:
            ref: "$heading" (opzoeken in brand.fonts) of "Helvetica-Bold" (direct).

        Returns:
            Font naam.
        """
        if ref.startswith("$"):
            key = ref[1:]
            return self._brand.fonts.get(key, "Helvetica")
        return ref

    def _resolve_variables(self, template: str, variables: dict[str, str]) -> str:
        """Vervang {variabelen} in template tekst.

        Args:
            template: Tekst met {page}, {project}, etc.
            variables: Dict van variabele naam → waarde.

        Returns:
            Ingevulde tekst.
        """
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    def _build_variables(
        self,
        config: DocumentConfig,
        page_num: int,
    ) -> dict[str, str]:
        """Bouw variabelen dict op basis van document config.

        Args:
            config: Document configuratie.
            page_num: Huidig paginanummer.

        Returns:
            Dict met alle beschikbare variabelen.
        """
        return {
            "page": str(page_num),
            "project": config.project,
            "project_number": config.project_number,
            "client": config.client,
            "author": config.author,
            "date": date.today().isoformat(),
            "report_type": config.report_type,
        }
