"""Report engine — Hoofdklasse voor het genereren van PDF rapporten."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from bm_reports.core.document import A4, Document, DocumentConfig, PageFormat


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
        self._sections: list[dict[str, Any]] = []
        self._has_cover = False
        self._has_backcover = False
        self._has_toc = True  # TOC standaard aan

    def add_cover(
        self,
        subtitle: str = "",
        image: str | Path | None = None,
        **kwargs,
    ) -> Report:
        """Voeg een voorblad toe.

        Args:
            subtitle: Ondertitel op het voorblad.
            image: Pad naar een cover afbeelding.
        """
        self._has_cover = True
        self.document.config.subtitle = subtitle
        # TODO: Implementeer cover page rendering
        return self

    def add_colofon(self, **kwargs) -> Report:
        """Voeg een colofon/informatiepagina toe (pagina 2)."""
        # TODO: Implementeer colofon
        return self

    def add_section(
        self,
        title: str,
        content: list[Any] | None = None,
        level: int = 1,
    ) -> Report:
        """Voeg een sectie toe aan het rapport.

        Args:
            title: Sectietitel (wordt opgenomen in TOC).
            content: Lijst van content elementen.
            level: Heading level (1-3) voor TOC hiërarchie.
        """
        self._sections.append({
            "title": title,
            "content": content or [],
            "level": level,
        })
        return self

    def add_calculation(
        self,
        title: str,
        formula: str = "",
        result: str = "",
        unit: str = "",
        **kwargs,
    ) -> Report:
        """Voeg een berekeningsblok toe.

        Args:
            title: Naam van de berekening.
            formula: Wiskundige formule (tekst representatie).
            result: Berekend resultaat.
            unit: Eenheid.
        """
        # TODO: Implementeer calculation block
        return self

    def add_check(
        self,
        description: str,
        unity_check: float | None = None,
        limit: float = 1.0,
        result: str | None = None,
        **kwargs,
    ) -> Report:
        """Voeg een toetsingsblok toe (voldoet/voldoet niet).

        Args:
            description: Omschrijving van de toets.
            unity_check: Unity check waarde (optioneel).
            limit: Grenswaarde.
            result: Expliciet resultaat ("VOLDOET" / "VOLDOET NIET").
        """
        # TODO: Implementeer check block
        return self

    def add_table(
        self,
        headers: list[str],
        rows: list[list[Any]],
        title: str = "",
        **kwargs,
    ) -> Report:
        """Voeg een tabel toe.

        Args:
            headers: Kolomnamen.
            rows: Data rijen.
            title: Optionele tabeltitel.
        """
        # TODO: Implementeer table block
        return self

    def add_image(
        self,
        path: str | Path,
        caption: str = "",
        width_mm: float | None = None,
        **kwargs,
    ) -> Report:
        """Voeg een afbeelding toe.

        Args:
            path: Pad naar afbeelding (PNG, JPG, SVG).
            caption: Bijschrift.
            width_mm: Breedte in mm (auto-scaled als None).
        """
        # TODO: Implementeer image block
        return self

    def add_backcover(self, **kwargs) -> Report:
        """Voeg een achterblad toe."""
        self._has_backcover = True
        # TODO: Implementeer backcover
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

        # TODO: Implementeer volledige build pipeline:
        # 1. Laad template (YAML) indien opgegeven
        # 2. Initialiseer ReportLab document
        # 3. Registreer page templates (cover, content, backcover)
        # 4. Render cover page
        # 5. Render colofon
        # 6. Render TOC (placeholder, gevuld in tweede pass)
        # 7. Render secties met content
        # 8. Render backcover
        # 9. Bouw PDF (multi-pass voor TOC paginanummers)

        raise NotImplementedError(
            "Build pipeline nog niet geïmplementeerd. Zie Fase 1 planning."
        )

    @classmethod
    def from_json(cls, json_path: str | Path, template: str | None = None) -> Report:
        """Maak een Report instantie vanuit een JSON configuratie.

        Args:
            json_path: Pad naar JSON bestand met project data.
            template: Optioneel template naam.

        Returns:
            Geconfigureerd Report object.
        """
        import json

        path = Path(json_path)
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return cls(
            project=data.get("project", ""),
            project_number=data.get("project_number", ""),
            client=data.get("client", ""),
            author=data.get("author", "3BM Bouwkunde"),
            report_type=data.get("report_type", ""),
            template=template or data.get("template"),
        )

    def __repr__(self) -> str:
        return (
            f"Report({self.document.config.format.name}, "
            f"project={self.document.config.project!r}, "
            f"sections={len(self._sections)})"
        )
