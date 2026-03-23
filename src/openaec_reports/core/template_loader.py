"""Template loader — YAML rapport templates inlezen en parsen."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yaml

# Standaard locatie van templates binnen het package
TEMPLATES_DIR = Path(__file__).parent.parent / "assets" / "templates"


@dataclass
class TemplateConfig:
    """Geparseerde template configuratie.

    Attrs:
        name: Template bestandsnaam (zonder extensie).
        report_type: Type rapport (bijv. 'structural', 'daylight').
        format: Paginaformaat ('A4' of 'A3').
        orientation: Oriëntatie ('portrait' of 'landscape').
        margins: Marges in mm (dict met top, bottom, left, right).
        header: Header configuratie.
        footer: Footer configuratie.
        cover: Voorblad configuratie.
        colofon: Colofon configuratie.
        toc: Inhoudsopgave configuratie.
        backcover: Achterblad configuratie.
        structure: Volgorde van secties.
        raw: Volledige ongeparseerde YAML data.
    """

    name: str = ""
    report_type: str = ""
    tenant: str = ""
    format: str = "A4"
    orientation: str = "portrait"
    margins: dict[str, float] = field(
        default_factory=lambda: {
            "top": 25.0,
            "bottom": 20.0,
            "left": 20.0,
            "right": 15.0,
        }
    )
    header: dict[str, Any] = field(default_factory=dict)
    footer: dict[str, Any] = field(default_factory=dict)
    cover: dict[str, Any] = field(default_factory=dict)
    colofon: dict[str, Any] = field(default_factory=dict)
    toc: dict[str, Any] = field(default_factory=dict)
    backcover: dict[str, Any] = field(default_factory=dict)
    structure: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


class TemplateLoader:
    """Laad en parseer YAML rapport templates.

    Zoekt templates in de standaard assets/templates/ directory,
    of in een custom directory. Ondersteunt meerdere directories
    (tenant-specifiek + package defaults).

    Usage:
        loader = TemplateLoader()
        config = loader.load("structural_report")
        available = loader.list_templates()

        # Multi-tenant: meerdere directories
        loader = TemplateLoader(templates_dirs=[tenant_dir, package_dir])
    """

    def __init__(
        self,
        templates_dir: Path | None = None,
        templates_dirs: list[Path] | None = None,
        tenant_slug: str = "",
    ):
        if templates_dirs:
            self._templates_dirs = templates_dirs
        else:
            self._templates_dirs = [templates_dir or TEMPLATES_DIR]
        # Backward compat: eerste directory is de "primaire"
        self.templates_dir = self._templates_dirs[0]
        self._tenant_slug = tenant_slug

    def load(self, name: str) -> TemplateConfig:
        """Laad een template op naam.

        Zoekt in alle geconfigureerde directories (tenant eerst, dan package).

        Args:
            name: Template naam (zonder .yaml extensie).

        Returns:
            TemplateConfig met de geparseerde template data.

        Raises:
            FileNotFoundError: Als het template niet gevonden wordt.
            yaml.YAMLError: Als het YAML bestand ongeldig is.
        """
        path = self._resolve_path(name)
        if not path.exists():
            raise FileNotFoundError(f"Template '{name}' niet gevonden in {self._templates_dirs}")

        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data is None:
            data = {}

        return TemplateConfig(
            name=name,
            report_type=data.get("report_type", ""),
            tenant=data.get("tenant", ""),
            format=data.get("format", "A4"),
            orientation=data.get("orientation", "portrait"),
            margins=data.get(
                "margins",
                {
                    "top": 25.0,
                    "bottom": 20.0,
                    "left": 20.0,
                    "right": 15.0,
                },
            ),
            header=data.get("header", {}),
            footer=data.get("footer", {}),
            cover=data.get("cover", {}),
            colofon=data.get("colofon", {}),
            toc=data.get("toc", {}),
            backcover=data.get("backcover", {}),
            structure=data.get("structure", []),
            raw=data,
        )

    def list_templates(self) -> list[dict[str, str]]:
        """Lijst beschikbare templates, strikt per tenant.

        Als een tenant_slug is ingesteld, worden ALLEEN templates uit de
        tenant-directory getoond (eerste dir in ``_templates_dirs``).
        Fallback-directories worden niet gescand — een tenant ziet
        uitsluitend eigen templates.

        Zonder tenant_slug worden alle directories gescand (backward compat).

        Returns:
            Lijst van dicts met 'name' en 'report_type' per template.
        """
        seen: set[str] = set()
        templates = []

        # Met tenant: alleen eerste directory (= tenant templates)
        dirs_to_scan = self._templates_dirs
        if self._tenant_slug and len(self._templates_dirs) > 1:
            dirs_to_scan = self._templates_dirs[:1]

        for tdir in dirs_to_scan:
            if not tdir.exists():
                continue
            for path in sorted(tdir.glob("*.yaml")):
                if path.stem in seen:
                    continue
                seen.add(path.stem)
                try:
                    with path.open("r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    templates.append(
                        {
                            "name": path.stem,
                            "report_type": data.get("report_type", "") if data else "",
                        }
                    )
                except yaml.YAMLError:
                    templates.append(
                        {
                            "name": path.stem,
                            "report_type": "(ongeldig YAML)",
                        }
                    )

        return templates

    def to_scaffold(self, name: str) -> dict[str, Any]:
        """Genereer een leeg JSON scaffold vanuit een template.

        Het scaffold bevat alle metadata velden met defaults uit het template,
        cover/colofon/toc/backcover configuratie, en een lege sections array.
        Geschikt als startpunt voor de frontend.

        Args:
            name: Template naam.

        Returns:
            Dict conform report.schema.json, klaar voor de frontend.

        Raises:
            FileNotFoundError: Als het template niet gevonden wordt.
        """
        config = self.load(name)
        today = date.today().isoformat()

        default_disclaimer = (
            "Dit rapport is opgesteld door OpenAEC en is uitsluitend "
            "bedoeld voor de opdrachtgever. Verspreiding aan derden is niet "
            "toegestaan zonder schriftelijke toestemming."
        )

        # Colofon
        colofon_raw = config.colofon
        colofon_enabled = colofon_raw.get("enabled", True) if colofon_raw else False
        disclaimer = colofon_raw.get("disclaimer", "").strip() if colofon_raw else ""
        if not disclaimer:
            disclaimer = default_disclaimer

        colofon: dict[str, Any] = {
            "enabled": colofon_enabled,
            "opdrachtgever_naam": "",
            "opdrachtgever_contact": "",
            "opdrachtgever_adres": "",
            "adviseur_bedrijf": "",
            "adviseur_naam": "",
            "adviseur_email": "",
            "adviseur_telefoon": "",
            "adviseur_functie": "",
            "adviseur_registratie": "",
            "normen": "",
            "documentgegevens": "",
            "datum": today,
            "fase": "",
            "status_colofon": "CONCEPT",
            "kenmerk": "",
            "extra_fields": {},
            "revision_history": [
                {
                    "version": "0.1",
                    "date": today,
                    "author": "",
                    "description": "Eerste opzet",
                },
            ],
            "disclaimer": disclaimer,
        }

        # TOC
        toc_raw = config.toc
        toc: dict[str, Any] = {
            "enabled": toc_raw.get("enabled", True) if toc_raw else False,
            "title": toc_raw.get("title", "Inhoudsopgave") if toc_raw else "Inhoudsopgave",
            "max_depth": toc_raw.get("max_depth", 3) if toc_raw else 3,
        }

        # Cover
        cover_raw = config.cover
        cover: dict[str, Any] = {
            "subtitle": cover_raw.get("subtitle_hint", "") if cover_raw else "",
        }

        # Backcover
        backcover_raw = config.backcover
        backcover: dict[str, Any] = {
            "enabled": backcover_raw.get("enabled", True) if backcover_raw else False,
        }

        sections = self._build_scaffold_sections(config)

        scaffold: dict[str, Any] = {
            "template": name,
            "format": config.format,
            "orientation": config.orientation,
            "project": "",
            "project_number": "",
            "client": "",
            "author": "OpenAEC",
            "brand": config.tenant if config.tenant else "default",
            "date": today,
            "version": "1.0",
            "status": "CONCEPT",
            "report_type": config.report_type,
            "cover": cover,
            "colofon": colofon,
            "toc": toc,
            "sections": sections,
            "backcover": backcover,
            "metadata": {},
        }

        # BIC Rapport: voeg flat data-dicts toe voor fixed page_types
        if config.report_type == "bic_rapport":
            scaffold.update(self._build_bic_flat_data())

        return scaffold

    def _build_scaffold_sections(
        self, config: TemplateConfig
    ) -> list[dict[str, Any]]:
        """Genereer default secties op basis van het template type.

        BIC Rapport templates krijgen vaste secties die corresponderen met
        de page_types in de YAML. Overige templates retourneren een lege
        lijst (gebruiker voegt zelf secties toe).
        """
        if config.report_type != "bic_rapport":
            return []

        return [
            {
                "title": "Locatie",
                "content": [
                    {
                        "type": "location_detail",
                        "client": {
                            "section_title": "Opdrachtgever",
                            "name": "",
                            "address": "",
                            "city": "",
                        },
                        "location": {
                            "section_title": "Locatie van uitvoer",
                            "name": "",
                            "address": "",
                            "city": "",
                            "code": "",
                            "provision": "",
                            "object": "",
                        },
                    }
                ],
            },
            {
                "title": "BIC Controles",
                "content": [
                    {
                        "type": "bic_table",
                        "location_name": "",
                        "sections": [
                            {
                                "title": "BIC Controles",
                                "rows": [],
                            },
                            {
                                "title": "Reinigen tijdens BIC",
                                "rows": [],
                            },
                            {
                                "title": "Additioneel tijdens BIC",
                                "rows": [],
                            },
                        ],
                        "summary": {
                            "title": "Overzicht samenvatting",
                            "rows": [],
                            "total": {
                                "label": "Totaal excl. BTW",
                                "ref_value": "",
                                "actual_value": "",
                            },
                        },
                    }
                ],
            },
            {
                "title": "Herstelwerkzaamheden",
                "content": [],
            },
            {
                "title": "Tekeningen",
                "content": [],
            },
            {
                "title": "Onderhoudsdossier",
                "content": [],
            },
            {
                "title": "Bijlagen",
                "content": [],
            },
        ]

    @staticmethod
    def _build_bic_flat_data() -> dict[str, Any]:
        """Lege flat data-dicts voor BIC Rapport fixed page_types."""
        return {
            "voorziening": {
                "code": "",
                "beschrijving": "",
                "vereiste_status": "",
                "huidige_status": "",
                "notitie": "",
                "foto": "",
            },
            "object": {
                "code": "",
                "beschrijving": "",
                "ruimte": "",
                "type": "",
            },
            "vvv": {
                "geldigheid": "",
                "nummer": "",
                "instantie": "",
                "opmerkingen": "",
                "onderhoudsdossier_ref": "",
                "bijlage_ref": "",
            },
        }

    def _resolve_path(self, name: str) -> Path:
        """Resolve template naam naar bestandspad.

        Met tenant_slug: zoekt ALLEEN in de eerste directory (tenant dir).
        Zonder tenant_slug: zoekt in alle directories (backward compat).

        Bij niet gevonden, retourneer het pad in de eerste directory
        (voor foutmelding).
        """
        filename = name if name.endswith(".yaml") else f"{name}.yaml"

        # Met tenant: alleen eigen tenant directory (= eerste dir)
        dirs_to_search = self._templates_dirs
        if self._tenant_slug and len(self._templates_dirs) > 1:
            dirs_to_search = self._templates_dirs[:1]

        for tdir in dirs_to_search:
            candidate = tdir / filename
            if candidate.exists():
                return candidate
        # Niet gevonden — retourneer pad in eerste dir voor foutmelding
        return self._templates_dirs[0] / filename
