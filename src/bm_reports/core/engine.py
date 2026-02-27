"""Report engine — Hoofdklasse voor het genereren van PDF rapporten."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.platypus import (
    BaseDocTemplate,
    NextPageTemplate,
    PageBreak,
    Paragraph,
    Spacer,
)

from bm_reports.core.block_registry import create_block
from bm_reports.core.brand import BrandConfig, BrandLoader
from bm_reports.core.document import A3, A4, Document, DocumentConfig, PageFormat
from bm_reports.core.page_templates import create_page_templates
from bm_reports.core.styles import create_stylesheet
from bm_reports.core.toc import TOC_HEADING_STYLES, TOCBuilder


class BMDocTemplate(BaseDocTemplate):
    """Custom ReportLab DocTemplate met TOC-integratie.

    Detecteert heading-flowables na rendering en registreert ze
    bij de TOCBuilder voor automatische inhoudsopgave-generatie.
    """

    def __init__(self, filename: str, toc_builder: TOCBuilder | None = None, **kwargs):
        super().__init__(filename, **kwargs)
        self.toc_builder = toc_builder

    def afterFlowable(self, flowable):  # noqa: N802 — ReportLab API naam
        """Hook die na elke flowable wordt aangeroepen door ReportLab.

        Detecteert Paragraph flowables met heading-stijlen en
        registreert ze bij de TOCBuilder.
        """
        if self.toc_builder is None:
            return

        if not isinstance(flowable, Paragraph):
            return

        style_name = flowable.style.name
        if style_name not in TOC_HEADING_STYLES:
            return

        # Bepaal TOC level op basis van heading style
        level = TOC_HEADING_STYLES.index(style_name)
        title = flowable.getPlainText()

        # Registreer bij ReportLab's TOC mechanisme (voedt TableOfContents)
        self.notify("TOCEntry", (level, title, self.page))

        # Registreer bookmarks voor PDF navigatie
        self.toc_builder.notify(self.canv, title, level)


class Report:
    """Hoofdklasse voor het bouwen en genereren van 3BM rapporten.

    Usage:
        report = Report(
            format=A4,
            project="Mijn Project",
            project_number="2026-001",
            client="Opdrachtgever",
        )
        report.add_cover(subtitle="Constructieve berekening")
        report.add_section("Uitgangspunten", content=[...])
        report.build("output/rapport.pdf")
    """

    def __init__(
        self,
        format: PageFormat = A4,
        project: str = "",
        project_number: str = "",
        client: str = "",
        author: str = "3BM Bouwkunde",
        report_type: str = "",
        template: str | None = None,
        brand: str | BrandConfig | None = None,
    ):
        self.document = Document(
            config=DocumentConfig(
                format=format,
                project=project,
                project_number=project_number,
                client=client,
                author=author,
                report_type=report_type,
            )
        )
        self.template_name = template

        # Brand laden
        if isinstance(brand, BrandConfig):
            self._brand = brand
        elif isinstance(brand, str):
            self._brand = BrandLoader().load(brand)
        else:
            self._brand = BrandLoader().load_default()

        # Brand-aware stylesheet
        self._styles = create_stylesheet(brand=self._brand)

        self._sections: list[dict[str, Any]] = []
        self._appendices: list[dict[str, Any]] = []
        self._has_cover = False
        self._has_colofon = False
        self._has_backcover = False
        self._has_toc = True  # TOC standaard aan
        self._toc_title = "Inhoudsopgave"
        self._toc_max_depth = 3
        self._toc_builder = TOCBuilder()
        self._cover_image: str | Path | None = None

        # Extra metadata (ingevuld via from_dict/from_json)
        self.date: str | None = None
        self.version: str = "1.0"
        self.status: str = "CONCEPT"
        self._metadata: dict[str, Any] = {}
        self._colofon: dict[str, Any] | None = None

    def add_cover(
        self,
        subtitle: str = "",
        image: str | Path | None = None,
        **kwargs,
    ) -> Report:
        """Voeg een voorblad toe.

        Het voorblad wordt getekend via draw_cover_page() in special_pages.py.
        De cover PageTemplate's onPage callback tekent het paarse vlak, logo,
        projecttitel en ondertitel direct op het canvas.

        Args:
            subtitle: Ondertitel op het voorblad.
            image: Pad naar een cover afbeelding (toekomstige feature).
        """
        self._has_cover = True
        self.document.config.subtitle = subtitle
        self._cover_image = image
        return self

    def add_colofon(self, **kwargs) -> Report:
        """Voeg een colofon/informatiepagina toe (pagina 2).

        De colofon wordt getekend via draw_colofon_page() in special_pages.py.
        Extra kwargs worden samengevoegd met de colofon data.
        """
        self._has_colofon = True
        if kwargs:
            if self._colofon is None:
                self._colofon = {}
            self._colofon.update(kwargs)
        return self

    def add_section(
        self,
        title: str,
        content: list[Any] | None = None,
        level: int = 1,
        page_break_before: bool = False,
    ) -> Report:
        """Voeg een sectie toe aan het rapport.

        Args:
            title: Sectietitel (wordt opgenomen in TOC).
            content: Lijst van content elementen.
            level: Heading level (1-3) voor TOC hiërarchie.
            page_break_before: Forceer nieuwe pagina voor deze sectie.
        """
        self._sections.append(
            {
                "title": title,
                "content": content or [],
                "level": level,
                "page_break_before": page_break_before,
            }
        )
        return self

    def _append_block(self, block) -> None:
        """Voeg een content block toe aan de laatste sectie.

        Als er geen secties zijn, wordt een impliciete sectie aangemaakt.
        """
        if self._sections:
            self._sections[-1]["content"].append(block)
        else:
            self.add_section("", content=[block])

    def add_calculation(
        self,
        title: str,
        formula: str = "",
        substitution: str = "",
        result: str = "",
        unit: str = "",
        reference: str = "",
        **kwargs,
    ) -> Report:
        """Voeg een berekeningsblok toe.

        Args:
            title: Naam van de berekening.
            formula: Wiskundige formule (tekst representatie).
            substitution: Ingevulde waarden.
            result: Berekend resultaat.
            unit: Eenheid.
            reference: Normatieve referentie.
        """
        from bm_reports.components.calculation import CalculationBlock

        block = CalculationBlock(
            title=title,
            formula=formula,
            substitution=substitution,
            result=result,
            unit=unit,
            reference=reference,
        )
        self._append_block(block)
        return self

    def add_check(
        self,
        description: str,
        required: str = "",
        calculated: str = "",
        unity_check: float | None = None,
        limit: float = 1.0,
        result: str | None = None,
        reference: str = "",
        **kwargs,
    ) -> Report:
        """Voeg een toetsingsblok toe (voldoet/voldoet niet).

        Args:
            description: Omschrijving van de toets.
            required: Eis / grenswaarde als tekst.
            calculated: Berekende waarde als tekst.
            unity_check: Unity check waarde (optioneel).
            limit: Grenswaarde.
            result: Expliciet resultaat ("VOLDOET" / "VOLDOET NIET").
            reference: Normatieve referentie.
        """
        from bm_reports.components.check_block import CheckBlock

        block = CheckBlock(
            description=description,
            required=required,
            calculated=calculated,
            unity_check=unity_check,
            limit=limit,
            result=result,
            reference=reference,
        )
        self._append_block(block)
        return self

    def add_table(
        self,
        headers: list[str],
        rows: list[list[Any]],
        title: str = "",
        col_widths_mm: list[float] | None = None,
        zebra: bool = True,
        **kwargs,
    ) -> Report:
        """Voeg een tabel toe.

        Args:
            headers: Kolomnamen.
            rows: Data rijen.
            title: Optionele tabeltitel.
            col_widths_mm: Kolombreedte in mm (None = auto).
            zebra: Wisselende rijkleuren.
        """
        from bm_reports.components.table_block import TableBlock

        block = TableBlock(
            headers=headers,
            rows=rows,
            title=title,
            col_widths_mm=col_widths_mm,
            zebra=zebra,
        )
        self._append_block(block)
        return self

    def add_image(
        self,
        path: str | Path,
        caption: str = "",
        width_mm: float | None = None,
        height_mm: float | None = None,
        align: str = "center",
        **kwargs,
    ) -> Report:
        """Voeg een afbeelding toe.

        Args:
            path: Pad naar afbeelding (PNG, JPG, SVG).
            caption: Bijschrift.
            width_mm: Breedte in mm (auto-scaled als None).
            height_mm: Hoogte in mm (auto op basis van aspect ratio).
            align: Uitlijning ('left', 'center', 'right').
        """
        from bm_reports.components.image_block import ImageBlock

        block = ImageBlock(
            path=path,
            width_mm=width_mm,
            height_mm=height_mm,
            caption=caption,
            align=align,
        )
        self._append_block(block)
        return self

    def add_appendix(
        self,
        title: str,
        number: int | None = None,
        content: list[Any] | None = None,
    ) -> Report:
        """Voeg een bijlage toe met scheidingspagina.

        Args:
            title: Bijlage titel (getoond op divider).
            number: Bijlage nummer (auto-increment als None).
            content: Optionele content na de divider.
        """
        if number is None:
            number = len(self._appendices) + 1
        self._appendices.append(
            {
                "title": title,
                "number": number,
                "content": content or [],
            }
        )
        return self

    def add_backcover(self, **kwargs) -> Report:
        """Voeg een achterblad toe."""
        self._has_backcover = True
        return self

    def build(self, output_path: str | Path) -> Path:
        """Genereer het PDF rapport.

        Args:
            output_path: Pad voor het output PDF bestand.

        Returns:
            Path naar het gegenereerde PDF bestand.
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        config = self.document.config

        # 1. BMDocTemplate initialiseren
        doc = BMDocTemplate(
            filename=str(output),
            pagesize=config.effective_pagesize,
            topMargin=config.margins.top_pt,
            bottomMargin=config.margins.bottom_pt,
            leftMargin=config.margins.left_pt,
            rightMargin=config.margins.right_pt,
            toc_builder=self._toc_builder,
        )

        # 2. PageTemplates registreren (met colofon data voor de colofon template)
        doc.addPageTemplates(
            create_page_templates(
                config,
                brand=self._brand,
                colofon_data=self._colofon,
                cover_image=self._cover_image,
            )
        )

        # 3. Dynamische appendix divider templates registreren
        if self._appendices:
            from reportlab.platypus import Frame, PageTemplate

            from bm_reports.core.special_pages import draw_appendix_divider_page

            ml = config.margins.left_pt
            mr = config.margins.right_pt
            mt = config.margins.top_pt
            mb = config.margins.bottom_pt
            page_w = config.effective_width_pt
            page_h = config.effective_height_pt

            for appendix in self._appendices:
                num = appendix["number"]
                title = appendix["title"]

                def _make_callback(n, t):
                    def callback(canvas, doc_inner):
                        draw_appendix_divider_page(
                            canvas,
                            doc_inner,
                            config,
                            self._brand,
                            n,
                            t,
                        )

                    return callback

                frame = Frame(
                    ml,
                    mb,
                    page_w - ml - mr,
                    page_h - mt - mb,
                    id=f"appendix_frame_{num}",
                )
                template = PageTemplate(
                    id=f"appendix_{num}",
                    frames=[frame],
                    onPage=_make_callback(num, title),
                )
                doc.addPageTemplates([template])

        # 4. Elements list opbouwen
        elements = self._build_elements()

        # 5. Multi-pass build (ReportLab vult TOC automatisch)
        doc.multiBuild(elements)

        return output

    def _build_elements(self) -> list:
        """Bouw de volledige elements list op voor ReportLab.

        Cover, colofon en backcover worden getekend via PageTemplate onPage callbacks
        in special_pages.py. Hier voegen we alleen de juiste template-wissels en
        PageBreaks toe als trigger voor de canvas rendering.
        """
        elements: list = []
        styles = self._styles

        # Cover: de cover PageTemplate's onPage callback tekent het volledige canvas.
        # We starten in de "cover" template en voegen een lege Spacer toe als trigger.
        if self._has_cover:
            elements.append(NextPageTemplate("cover"))
            # Minimale spacer zodat ReportLab de pagina triggert
            elements.append(Spacer(1, 1))

            # Colofon (pagina 2) — optioneel na cover
            if self._has_colofon:
                elements.append(NextPageTemplate("colofon"))
                elements.append(PageBreak())
                elements.append(Spacer(1, 1))

            # Wissel naar content template voor de inhoud
            elements.append(NextPageTemplate("content"))
            elements.append(PageBreak())
        else:
            # Geen cover: start direct in content template
            elements.append(NextPageTemplate("content"))

        # TOC
        if self._has_toc and self._sections:
            elements.append(Paragraph(self._toc_title, styles["Heading1"]))
            elements.append(self._toc_builder.placeholder())
            elements.append(PageBreak())

        # Secties
        for section in self._sections:
            if section.get("page_break_before"):
                elements.append(PageBreak())

            level = section["level"]
            style_name = f"Heading{level}"
            elements.append(Paragraph(section["title"], styles[style_name]))

            for item in section["content"]:
                if isinstance(item, str):
                    elements.append(Paragraph(item, styles["Normal"]))
                else:
                    # Flowable objecten (components) direct toevoegen
                    elements.append(item)

            elements.append(Spacer(1, 6))

        # Bijlagen
        for appendix in self._appendices:
            elements.append(
                NextPageTemplate(
                    f"appendix_{appendix['number']}",
                )
            )
            elements.append(PageBreak())
            elements.append(Spacer(1, 1))

            # Bijlage-inhoud na de divider
            if appendix["content"]:
                elements.append(NextPageTemplate("content"))
                elements.append(PageBreak())
                for item in appendix["content"]:
                    if isinstance(item, str):
                        elements.append(Paragraph(item, styles["Normal"]))
                    else:
                        elements.append(item)

        # Backcover: de backcover PageTemplate's onPage callback tekent het volledige canvas.
        if self._has_backcover:
            elements.append(NextPageTemplate("backcover"))
            elements.append(PageBreak())
            elements.append(Spacer(1, 1))

        return elements

    @classmethod
    def from_json(
        cls,
        json_path: str | Path,
        *,
        brand: str | BrandConfig | None = None,
    ) -> Report:
        """Maak een Report instantie vanuit een JSON bestand.

        Args:
            json_path: Pad naar JSON bestand conform report.schema.json.
            brand: Optioneel brand naam of BrandConfig.

        Returns:
            Volledig geconfigureerd Report object.
        """
        import json

        path = Path(json_path)
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return cls.from_dict(data, base_dir=path.parent, brand=brand)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        *,
        base_dir: Path | None = None,
        brand: str | BrandConfig | None = None,
    ) -> Report:
        """Maak een Report instantie vanuit een dict (JSON schema).

        Args:
            data: Dict conform report.schema.json.
            base_dir: Basis directory voor relatieve paden (images).
            brand: Optioneel brand naam of BrandConfig.

        Returns:
            Volledig geconfigureerd Report object.
        """
        # Format bepalen
        fmt_name = data.get("format", "A4")
        fmt = A3 if fmt_name == "A3" else A4
        orientation = data.get("orientation", "portrait")

        report = cls(
            format=fmt,
            project=data.get("project", ""),
            project_number=data.get("project_number", ""),
            client=data.get("client", ""),
            author=data.get("author", "3BM Bouwkunde"),
            report_type=data.get("report_type", ""),
            template=data.get("template"),
            brand=brand or data.get("brand"),
        )
        report.document.config.orientation = orientation

        # Extra metadata velden
        report.date = data.get("date")
        report.version = data.get("version", "1.0")
        report.status = data.get("status", "CONCEPT")
        report._metadata = data.get("metadata", {})

        # Cover
        cover = data.get("cover")
        if cover is not None:
            cover_image = cover.get("image")
            if cover_image and isinstance(cover_image, str) and base_dir:
                cover_path = Path(cover_image)
                if not cover_path.is_absolute():
                    cover_image = str(base_dir / cover_image)
            report.add_cover(
                subtitle=cover.get("subtitle", ""),
                image=cover_image,
            )

        # Colofon
        colofon = data.get("colofon")
        if colofon is not None:
            report._colofon = colofon
            if colofon.get("enabled", True):
                report.add_colofon()

        # TOC
        toc = data.get("toc")
        if toc is not None:
            report._has_toc = toc.get("enabled", True)
            report._toc_title = toc.get("title", "Inhoudsopgave")
            report._toc_max_depth = toc.get("max_depth", 3)

        # Tenant identifier voor module registry lookup
        tenant = report._brand.tenant or data.get("tenant")

        # Secties met content blocks
        for section_data in data.get("sections", []):
            content_blocks = []
            for block_data in section_data.get("content", []):
                flowable = create_block(
                    block_data,
                    base_dir=base_dir,
                    styles=report._styles,
                    tenant=tenant,
                )
                content_blocks.append(flowable)

            report.add_section(
                title=section_data["title"],
                content=content_blocks,
                level=section_data.get("level", 1),
                page_break_before=section_data.get("page_break_before", False),
            )

        # Bijlagen
        for appendix_data in data.get("appendices", []):
            appendix_content = []
            for block_data in appendix_data.get("content", []):
                flowable = create_block(
                    block_data,
                    base_dir=base_dir,
                    styles=report._styles,
                    tenant=tenant,
                )
                appendix_content.append(flowable)
            report.add_appendix(
                title=appendix_data.get("title", ""),
                number=appendix_data.get("number"),
                content=appendix_content,
            )

        # Backcover
        backcover = data.get("backcover")
        if backcover is not None and backcover.get("enabled", True):
            report.add_backcover()

        return report

    def __repr__(self) -> str:
        return (
            f"Report({self.document.config.format.name}, "
            f"project={self.document.config.project!r}, "
            f"sections={len(self._sections)})"
        )
