"""Building code report — Bouwbesluit toetsing rapport."""

from __future__ import annotations

from typing import Any

from reportlab.platypus import Flowable, Paragraph, Spacer

from openaec_reports.components.check_block import CheckBlock
from openaec_reports.components.table_block import TableBlock
from openaec_reports.core.document import MM_TO_PT
from openaec_reports.core.styles import BM_STYLES
from openaec_reports.reports.base_report import BaseReport


class BuildingCodeReport(BaseReport):
    """Rapporttype: Bouwbesluit toetsing.

    Generiek toetsingsrapport dat meerdere Bouwbesluit artikelen
    kan bevatten. Elke toets wordt gepresenteerd met:
    - Artikelreferentie
    - Eis
    - Berekende/gemeten waarde
    - Toetsresultaat

    Standaard secties:
    - Projectgegevens en uitgangspunten
    - Toetsingen per hoofdstuk/afdeling
    - Samenvattend overzicht
    - Conclusie

    Verwachte ``self._data`` structuur::

        {
            "uitgangspunten": {
                "beschrijving": str,
                "gebruiksfunctie": str,
                "bouwbesluit_versie": str,
                "nieuwbouw": bool
            },
            "hoofdstukken": [
                {
                    "titel": str,
                    "beschrijving": str,
                    "toetsingen": [
                        {
                            "artikel": str,
                            "beschrijving": str,
                            "eis": str,
                            "berekend": str,
                            "voldoet": bool,
                            "toelichting": str
                        }
                    ]
                }
            ],
            "conclusie": str
        }
    """

    report_type = "building_code"
    default_template = "building_code_report"

    def build_sections(self) -> list[dict[str, Any]]:
        """Bouw secties voor bouwbesluit toetsing."""
        sections: list[dict[str, Any]] = []

        sections.extend(self._build_uitgangspunten())
        sections.extend(self._build_hoofdstukken())
        sections.extend(self._build_overzicht())
        sections.extend(self._build_conclusie())

        return sections

    def _build_uitgangspunten(self) -> list[dict[str, Any]]:
        """Bouw sectie Projectgegevens en uitgangspunten."""
        data = self._data.get("uitgangspunten", {})
        if not data:
            return []

        content: list[Flowable] = []

        beschrijving = data.get("beschrijving", "")
        if beschrijving:
            content.append(Paragraph(beschrijving, BM_STYLES["Normal"]))

        details: list[str] = []
        if data.get("gebruiksfunctie"):
            details.append(f"Gebruiksfunctie: {data['gebruiksfunctie']}")
        if data.get("bouwbesluit_versie"):
            details.append(f"Bouwbesluit: {data['bouwbesluit_versie']}")
        nieuwbouw = data.get("nieuwbouw")
        if nieuwbouw is not None:
            details.append(f"Toetsingsniveau: {'Nieuwbouw' if nieuwbouw else 'Bestaande bouw'}")

        if details:
            content.append(Paragraph("<br/>".join(details), BM_STYLES["Normal"]))

        return [{
            "title": "Projectgegevens en uitgangspunten",
            "content": content,
            "level": 1,
        }]

    def _build_hoofdstukken(self) -> list[dict[str, Any]]:
        """Bouw secties per Bouwbesluit hoofdstuk/afdeling."""
        hoofdstukken = self._data.get("hoofdstukken", [])
        sections: list[dict[str, Any]] = []

        for hoofdstuk in hoofdstukken:
            titel = hoofdstuk.get("titel", "Toetsing")

            # Hoofdstuk intro
            h_content: list[Flowable] = []
            beschrijving = hoofdstuk.get("beschrijving", "")
            if beschrijving:
                h_content.append(Paragraph(beschrijving, BM_STYLES["Normal"]))

            # Elke toetsing als CheckBlock
            for toets in hoofdstuk.get("toetsingen", []):
                h_content.append(Spacer(1, 3 * MM_TO_PT))

                artikel = toets.get("artikel", "")
                beschr = toets.get("beschrijving", "")
                label = f"{artikel} — {beschr}" if artikel and beschr else (artikel or beschr)

                voldoet = toets.get("voldoet", False)
                h_content.append(CheckBlock(
                    description=label,
                    required=toets.get("eis", ""),
                    calculated=toets.get("berekend", ""),
                    result="VOLDOET" if voldoet else "VOLDOET NIET",
                    reference=artikel,
                ))

                toelichting = toets.get("toelichting", "")
                if toelichting:
                    h_content.append(Paragraph(
                        f"<i>{toelichting}</i>", BM_STYLES["Normal"]
                    ))

            sections.append({"title": titel, "content": h_content, "level": 1})

        return sections

    def _build_overzicht(self) -> list[dict[str, Any]]:
        """Bouw samenvattend overzicht van alle toetsingen."""
        hoofdstukken = self._data.get("hoofdstukken", [])
        if not hoofdstukken:
            return []

        headers = ["Artikel", "Omschrijving", "Eis", "Berekend", "Resultaat"]
        rows: list[list[str]] = []

        for hoofdstuk in hoofdstukken:
            for toets in hoofdstuk.get("toetsingen", []):
                voldoet = toets.get("voldoet", False)
                rows.append([
                    toets.get("artikel", ""),
                    toets.get("beschrijving", ""),
                    toets.get("eis", ""),
                    toets.get("berekend", ""),
                    "VOLDOET" if voldoet else "VOLDOET NIET",
                ])

        if not rows:
            return []

        content: list[Flowable] = [
            TableBlock(headers=headers, rows=rows, title="Samenvattend toetsingsoverzicht"),
        ]
        return [{"title": "Samenvattend overzicht", "content": content, "level": 1}]

    def _build_conclusie(self) -> list[dict[str, Any]]:
        """Bouw conclusie sectie."""
        conclusie = self._data.get("conclusie", "")
        if not conclusie:
            return []

        content: list[Flowable] = [Paragraph(conclusie, BM_STYLES["Normal"])]
        return [{"title": "Conclusie", "content": content, "level": 1}]
