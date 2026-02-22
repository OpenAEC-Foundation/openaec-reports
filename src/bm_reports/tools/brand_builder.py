"""Brand Builder — genereer complete brand config uit huisstijl-documenten."""

from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from bm_reports.tools.config_generator import generate_analysis_report, generate_brand_yaml
    from bm_reports.tools.page_classifier import PageType, classify_pages
    from bm_reports.tools.pattern_detector import analyze_brand
    from bm_reports.tools.pdf_extractor import extract_pdf
    from bm_reports.tools.stationery_extractor import StationeryExtractor
except ImportError as e:
    logger.warning(f"Brand builder dependencies niet beschikbaar: {e}")


class BrandBuilder:
    """Genereert een volledige brand directory uit huisstijl-documenten."""

    def __init__(self, output_dir: Path, brand_name: str, brand_slug: str):
        self.output_dir = Path(output_dir)
        self.brand_name = brand_name
        self.brand_slug = brand_slug

    def build(
        self,
        referentie_rapport: Path,
        stamkaart: Path | None = None,
        briefpapier: Path | None = None,
        logo_dir: Path | None = None,
        font_dir: Path | None = None,
        base_brand: Path | None = None,
        dpi: int = 150,
        extract_layouts: bool = True,
    ) -> Path:
        """Voer de volledige pipeline uit.

        Args:
            extract_layouts: Als True, extraheer per-pagina layouts en genereer pages-sectie.

        Returns pad naar output directory.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        stationery_dir = self.output_dir / "stationery"
        stationery_dir.mkdir(exist_ok=True)
        analysis_dir = self.output_dir / "analysis"
        analysis_dir.mkdir(exist_ok=True)
        logos_dir = self.output_dir / "logos"
        logos_dir.mkdir(exist_ok=True)

        # --- Stap 1: Analyseer referentie-rapport ---
        logger.info(f"[1/7] Analyseer {referentie_rapport.name}...")
        print(f"  [1/7] Analyseer {referentie_rapport.name}...")
        pages_dir = analysis_dir / "pages"
        raw_pages = extract_pdf(referentie_rapport, pages_dir, dpi=dpi)
        classified = classify_pages(raw_pages)
        page_images = [p.page_image_path for p in raw_pages if p.page_image_path]
        analysis = analyze_brand(classified, str(referentie_rapport), page_images)

        # --- Stap 2: Verrijk kleuren uit stamkaart ---
        if stamkaart and stamkaart.exists():
            logger.info(f"[2/7] Verrijk kleuren uit {stamkaart.name}...")
            print(f"  [2/7] Verrijk kleuren uit {stamkaart.name}...")
            stamkaart_pages = extract_pdf(stamkaart)
            stamkaart_colors = self._extract_stamkaart_colors(stamkaart_pages)
            if stamkaart_colors:
                analysis.colors.update(stamkaart_colors)
                print(f"         Stamkaart kleuren: {stamkaart_colors}")
        else:
            print("  [2/7] Geen stamkaart — skip")

        # --- Stap 3: Extraheer stationery ---
        print("  [3/7] Extraheer stationery...")
        extractor = StationeryExtractor(referentie_rapport)
        self._extract_stationery(extractor, classified, stationery_dir)

        # --- Stap 4: Kopieer briefpapier ---
        if briefpapier and briefpapier.exists():
            print(f"  [4/7] Kopieer briefpapier: {briefpapier.name}")
            shutil.copy(briefpapier, stationery_dir / "briefpapier.pdf")
        else:
            print("  [4/7] Geen briefpapier — skip")

        # --- Stap 5: Kopieer logo's ---
        if logo_dir and logo_dir.exists():
            print(f"  [5/7] Kopieer logo's uit {logo_dir}")
            for logo_file in logo_dir.iterdir():
                if logo_file.suffix.lower() in (".svg", ".png", ".pdf", ".eps"):
                    shutil.copy(logo_file, logos_dir / logo_file.name)
        else:
            print("  [5/7] Geen logo directory — skip")

        # --- Stap 6: Kopieer fonts ---
        if font_dir and font_dir.exists():
            fonts_dir = self.output_dir / "fonts"
            fonts_dir.mkdir(exist_ok=True)
            print(f"  [6/7] Kopieer fonts uit {font_dir}")
            for font_file in font_dir.iterdir():
                if font_file.suffix.lower() in (".ttf", ".otf", ".woff", ".woff2"):
                    shutil.copy(font_file, fonts_dir / font_file.name)
        else:
            print("  [6/7] Geen font directory — skip")

        # --- Stap 7: Extraheer per-pagina layouts ---
        page_layouts = None
        if extract_layouts:
            print("  [7/9] Extraheer per-pagina layouts...")
            try:
                from bm_reports.tools.layout_extractor import extract_page_layouts

                page_layouts = extract_page_layouts(classified)
                for pt, lay in page_layouts.items():
                    print(
                        f"         {pt.value}: {len(lay.static_elements)} elementen, "
                        f"{len(lay.text_zones)} zones, {len(lay.badges)} badges"
                    )
            except Exception as e:
                logger.warning(f"Layout extractie gefaald: {e}")
                print(f"  [7/9] Layout extractie gefaald: {e}")
        else:
            print("  [7/9] Layout extractie overgeslagen")

        # --- Stap 8: Genereer brand.yaml + rapport ---
        print("  [8/9] Genereer brand.yaml...")
        yaml_str = generate_brand_yaml(
            analysis,
            self.brand_name,
            self.brand_slug,
            page_layouts=page_layouts,
        )
        (self.output_dir / "brand.yaml").write_text(yaml_str, encoding="utf-8")

        report_str = generate_analysis_report(analysis)
        (analysis_dir / "report.md").write_text(report_str, encoding="utf-8")

        # --- Stap 9: Visuele verificatie (optioneel) ---
        print("  [9/9] Verificatie...")
        print(f"\n  Brand directory gereed: {self.output_dir}")
        print("  Gebruik 'bm-report visual-diff' om te vergelijken met referentie.")
        return self.output_dir

    def _extract_stationery(self, extractor, classified, stationery_dir):
        """Extraheer stationery per paginatype."""
        for cp in classified:
            page_idx = cp.page.page_number - 1  # 0-based

            if cp.page_type == PageType.BACKCOVER:
                path = extractor.extract_full_page(page_idx, stationery_dir / "backcover.pdf")
                print(f"         Backcover: pagina {cp.page.page_number} → {path.name}")

            elif cp.page_type == PageType.APPENDIX_DIVIDER:
                strip_zones = self._detect_appendix_strip_zones(cp.page)
                path = extractor.extract_stripped_page(
                    page_idx,
                    stationery_dir / "appendix_divider.pdf",
                    strip_zones,
                )
                print(f"         Appendix divider: pagina {cp.page.page_number} → {path.name}")

            elif cp.page_type == PageType.COVER:
                strip_zones = self._detect_cover_strip_zones(cp.page)
                path = extractor.extract_stripped_page(
                    page_idx,
                    stationery_dir / "cover.pdf",
                    strip_zones,
                )
                print(f"         Cover: pagina {cp.page.page_number} → {path.name}")

    def _detect_cover_strip_zones(self, page):
        """Bepaal welke tekst-zones op de cover geript moeten worden."""
        if not page.texts:
            return []

        sorted_texts = sorted(page.texts, key=lambda t: t.size, reverse=True)
        zones = []

        # Grootste tekst = titel
        if sorted_texts:
            t = sorted_texts[0]
            zones.append((t.x - 5, t.y_top - 5, t.x2 + 5, t.y_bottom + 5))

        # Op-één-na-grootste = subtitel (als het echt een subtitel is)
        if len(sorted_texts) > 1:
            t = sorted_texts[1]
            if t.size > 12:
                zones.append((t.x - 5, t.y_top - 5, t.x2 + 5, t.y_bottom + 5))

        return zones

    def _detect_appendix_strip_zones(self, page):
        """Bepaal welke tekst-zones op de appendix divider geript moeten worden."""
        if not page.texts:
            return []

        zones = []
        for t in page.texts:
            if t.size > 20:
                zones.append((t.x - 5, t.y_top - 5, t.x2 + 5, t.y_bottom + 5))

        return zones

    def _extract_stamkaart_colors(self, pages):
        """Extraheer kleuren uit stamkaart (best effort)."""
        colors = {}
        for page_data in pages:
            for t in page_data.texts:
                text = t.text.strip()

                # Patroon: "R123 G45 B67" of "123 / 45 / 67"
                rgb_match = re.match(
                    r"R?\s*(\d{1,3})\s*[/\s]+G?\s*(\d{1,3})\s*[/\s]+B?\s*(\d{1,3})", text
                )
                if rgb_match:
                    r, g, b = (
                        int(rgb_match.group(1)),
                        int(rgb_match.group(2)),
                        int(rgb_match.group(3)),
                    )
                    if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                        hex_color = f"#{r:02X}{g:02X}{b:02X}"
                        label = self._find_color_label(t, page_data.texts)
                        if label:
                            colors[label] = hex_color

                # Patroon: "#401246" (direct hex)
                hex_match = re.match(r"#([0-9A-Fa-f]{6})", text)
                if hex_match:
                    hex_color = f"#{hex_match.group(1).upper()}"
                    label = self._find_color_label(t, page_data.texts)
                    if label:
                        colors[label] = hex_color

        return colors

    def _find_color_label(self, color_text, all_texts):
        """Zoek een label-tekst dichtbij de kleurcode-tekst."""
        for t in all_texts:
            if t is color_text:
                continue
            if abs(t.x - color_text.x) < 50 and 0 < (color_text.y_top - t.y_bottom) < 50:
                label = t.text.strip().lower().replace(" ", "_")
                if label and not any(c.isdigit() for c in label):
                    return label
        return None
