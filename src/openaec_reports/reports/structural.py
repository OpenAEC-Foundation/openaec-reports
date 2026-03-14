"""Structural report — Constructieve berekening rapport."""

from __future__ import annotations

from typing import Any

from reportlab.platypus import Flowable, Paragraph, Spacer

from openaec_reports.components.calculation import CalculationBlock
from openaec_reports.components.check_block import CheckBlock
from openaec_reports.components.table_block import TableBlock
from openaec_reports.core.document import MM_TO_PT
from openaec_reports.core.styles import BM_STYLES
from openaec_reports.reports.base_report import BaseReport


class StructuralReport(BaseReport):
    """Rapporttype: Constructieve berekening.

    Standaard secties:
    - Uitgangspunten
    - Belastingen & belastingcombinaties
    - Berekeningen per element
    - Unity checks overzicht
    - Conclusie

    Verwachte ``self._data`` structuur::

        {
            "uitgangspunten": {
                "beschrijving": str,
                "normen": [str, ...],
                "materialen": [{"onderdeel": str, "materiaal": str, "sterkteklasse": str}, ...]
            },
            "belastingen": {
                "beschrijving": str,
                "categorieen": [
                    {"titel": str, "level": 2, "beschrijving": str, "items": [...]}
                ]
            },
            "elementen": [
                {
                    "naam": str,
                    "beschrijving": str,
                    "berekeningen": [
                        {"title": str, "formula": str, "substitution": str,
                         "result": str, "unit": str, "reference": str}
                    ],
                    "checks": [
                        {"description": str, "required_value": str, "calculated_value": str,
                         "unity_check": float, "limit": float, "reference": str}
                    ]
                }
            ],
            "conclusie": str
        }
    """

    report_type = "structural"
    default_template = "structural_report"

    def build_sections(self) -> list[dict[str, Any]]:
        """Bouw secties voor constructief rapport."""
        sections: list[dict[str, Any]] = []

        sections.extend(self._build_uitgangspunten())
        sections.extend(self._build_belastingen())
        sections.extend(self._build_elementen())
        sections.extend(self._build_uc_overzicht())
        sections.extend(self._build_conclusie())

        return sections

    def _build_uitgangspunten(self) -> list[dict[str, Any]]:
        """Bouw sectie Uitgangspunten."""
        data = self._data.get("uitgangspunten", {})
        if not data:
            return []

        content: list[Flowable] = []

        beschrijving = data.get("beschrijving", "")
        if beschrijving:
            content.append(Paragraph(beschrijving, BM_STYLES["Normal"]))

        normen = data.get("normen", [])
        if normen:
            normen_text = "Toegepaste normen: " + ", ".join(normen) + "."
            content.append(Paragraph(normen_text, BM_STYLES["Normal"]))

        materialen = data.get("materialen", [])
        if materialen:
            content.append(Spacer(1, 4 * MM_TO_PT))
            headers = ["Onderdeel", "Materiaal", "Sterkteklasse"]
            rows = [
                [m.get("onderdeel", ""), m.get("materiaal", ""), m.get("sterkteklasse", "")]
                for m in materialen
            ]
            content.append(TableBlock(headers=headers, rows=rows, title="Toegepaste materialen"))

        return [{"title": "Uitgangspunten", "content": content, "level": 1}]

    def _build_belastingen(self) -> list[dict[str, Any]]:
        """Bouw sectie Belastingen met optionele subsecties."""
        data = self._data.get("belastingen", {})
        if not data:
            return []

        sections: list[dict[str, Any]] = []

        beschrijving = data.get("beschrijving", "")
        main_content: list[Flowable] = []
        if beschrijving:
            main_content.append(Paragraph(beschrijving, BM_STYLES["Normal"]))
        sections.append({"title": "Belastingen", "content": main_content, "level": 1})

        for cat in data.get("categorieen", []):
            cat_content: list[Flowable] = []
            cat_beschrijving = cat.get("beschrijving", "")
            if cat_beschrijving:
                cat_content.append(Paragraph(cat_beschrijving, BM_STYLES["Normal"]))

            items = cat.get("items", [])
            if items:
                headers = list(items[0].keys()) if items else []
                rows = [list(item.values()) for item in items]
                cat_content.append(TableBlock(headers=headers, rows=rows))

            sections.append({
                "title": cat.get("titel", "Belasting"),
                "content": cat_content,
                "level": cat.get("level", 2),
            })

        return sections

    def _build_elementen(self) -> list[dict[str, Any]]:
        """Bouw secties per constructief element met berekeningen en checks."""
        elementen = self._data.get("elementen", [])
        sections: list[dict[str, Any]] = []

        for element in elementen:
            content: list[Flowable] = []

            beschrijving = element.get("beschrijving", "")
            if beschrijving:
                content.append(Paragraph(beschrijving, BM_STYLES["Normal"]))

            for calc in element.get("berekeningen", []):
                content.append(Spacer(1, 3 * MM_TO_PT))
                content.append(CalculationBlock(
                    title=calc.get("title", ""),
                    formula=calc.get("formula", ""),
                    substitution=calc.get("substitution", ""),
                    result=calc.get("result", ""),
                    unit=calc.get("unit", ""),
                    reference=calc.get("reference", ""),
                ))

            for check in element.get("checks", []):
                content.append(Spacer(1, 3 * MM_TO_PT))
                content.append(CheckBlock(
                    description=check.get("description", ""),
                    required=check.get("required_value", ""),
                    calculated=check.get("calculated_value", ""),
                    unity_check=check.get("unity_check"),
                    limit=check.get("limit", 1.0),
                    reference=check.get("reference", ""),
                ))

            sections.append({
                "title": element.get("naam", "Element"),
                "content": content,
                "level": 1,
                "page_break_before": True,
            })

        return sections

    def _build_uc_overzicht(self) -> list[dict[str, Any]]:
        """Bouw UC overzichtstabel uit alle element checks."""
        elementen = self._data.get("elementen", [])
        if not elementen:
            return []

        headers = ["Element", "Toets", "UC", "Resultaat"]
        rows: list[list[str]] = []

        for element in elementen:
            naam = element.get("naam", "")
            for check in element.get("checks", []):
                uc = check.get("unity_check")
                uc_str = f"{uc:.2f}" if uc is not None else "-"
                passes = uc is not None and uc <= check.get("limit", 1.0)
                rows.append([
                    naam,
                    check.get("description", ""),
                    uc_str,
                    "VOLDOET" if passes else "VOLDOET NIET",
                ])

        if not rows:
            return []

        content: list[Flowable] = [
            TableBlock(headers=headers, rows=rows, title="Unity check overzicht"),
        ]

        return [{"title": "Unity check overzicht", "content": content, "level": 1}]

    def _build_conclusie(self) -> list[dict[str, Any]]:
        """Bouw conclusie sectie."""
        conclusie = self._data.get("conclusie", "")
        if not conclusie:
            return []

        content: list[Flowable] = [Paragraph(conclusie, BM_STYLES["Normal"])]
        return [{"title": "Conclusie", "content": content, "level": 1}]
