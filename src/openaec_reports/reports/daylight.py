"""Daylight report — Daglichtberekening rapport."""

from __future__ import annotations

from typing import Any

from reportlab.platypus import Flowable, Paragraph, Spacer

from openaec_reports.components.calculation import CalculationBlock
from openaec_reports.components.check_block import CheckBlock
from openaec_reports.components.table_block import TableBlock
from openaec_reports.core.document import MM_TO_PT
from openaec_reports.core.styles import BM_STYLES
from openaec_reports.reports.base_report import BaseReport


class DaylightReport(BaseReport):
    """Rapporttype: Daglichtberekening (Bouwbesluit Art. 3.74 / NEN 2057).

    Standaard secties:
    - Uitgangspunten
    - Situatie en oriëntatie
    - Berekening equivalente daglichtoppervlakte per verblijfsgebied
    - Toetsing aan Bouwbesluit eisen
    - Conclusie

    Verwachte ``self._data`` structuur::

        {
            "uitgangspunten": {
                "beschrijving": str,
                "norm": str,
                "gebouwtype": str,
                "gebruiksfunctie": str
            },
            "situatie": {
                "beschrijving": str,
                "orientatie": str
            },
            "ruimtes": [
                {
                    "naam": str,
                    "verdieping": str,
                    "vloeroppervlakte_m2": float,
                    "ramen": [
                        {"naam": str, "breedte_m": float, "hoogte_m": float,
                         "borstwering_m": float, "orientatie": str,
                         "reductiefactoren": {"bebouwing": float, ...}}
                    ],
                    "eis_percentage": float
                }
            ],
            "conclusie": str
        }
    """

    report_type = "daylight"
    default_template = "daylight_report"

    def build_sections(self) -> list[dict[str, Any]]:
        """Bouw secties voor daglichtrapport."""
        sections: list[dict[str, Any]] = []

        sections.extend(self._build_uitgangspunten())
        sections.extend(self._build_situatie())
        sections.extend(self._build_ruimtes())
        sections.extend(self._build_toetsing())
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

        details: list[str] = []
        if data.get("norm"):
            details.append(f"Norm: {data['norm']}")
        if data.get("gebouwtype"):
            details.append(f"Gebouwtype: {data['gebouwtype']}")
        if data.get("gebruiksfunctie"):
            details.append(f"Gebruiksfunctie: {data['gebruiksfunctie']}")

        if details:
            content.append(Paragraph("<br/>".join(details), BM_STYLES["Normal"]))

        return [{"title": "Uitgangspunten", "content": content, "level": 1}]

    def _build_situatie(self) -> list[dict[str, Any]]:
        """Bouw sectie Situatie en oriëntatie."""
        data = self._data.get("situatie", {})
        if not data:
            return []

        content: list[Flowable] = []

        beschrijving = data.get("beschrijving", "")
        if beschrijving:
            content.append(Paragraph(beschrijving, BM_STYLES["Normal"]))

        orientatie = data.get("orientatie", "")
        if orientatie:
            content.append(Paragraph(f"Oriëntatie: {orientatie}", BM_STYLES["Normal"]))

        return [{"title": "Situatie en oriëntatie", "content": content, "level": 1}]

    def _build_ruimtes(self) -> list[dict[str, Any]]:
        """Bouw secties per ruimte met daglichtberekening."""
        ruimtes = self._data.get("ruimtes", [])
        if not ruimtes:
            return []

        sections: list[dict[str, Any]] = []

        # Hoofdsectie
        sections.append({
            "title": "Daglichtberekening per ruimte",
            "content": [Paragraph(
                "Per verblijfsgebied wordt de equivalente daglichtoppervlakte "
                "berekend conform NEN 2057.",
                BM_STYLES["Normal"],
            )],
            "level": 1,
        })

        for ruimte in ruimtes:
            content: list[Flowable] = []
            naam = ruimte.get("naam", "Ruimte")
            vloer = ruimte.get("vloeroppervlakte_m2", 0.0)
            eis_pct = ruimte.get("eis_percentage", 10.0)

            info = f"Vloeroppervlakte: {vloer:.1f} m²"
            verdieping = ruimte.get("verdieping", "")
            if verdieping:
                info += f" | Verdieping: {verdieping}"
            content.append(Paragraph(info, BM_STYLES["Normal"]))

            # Ramen tabel
            ramen = ruimte.get("ramen", [])
            if ramen:
                content.append(Spacer(1, 3 * MM_TO_PT))
                headers = ["Raam", "B×H (m)", "Oriëntatie", "A_glas (m²)", "A_eq (m²)"]
                rows: list[list[str]] = []
                totaal_eq = 0.0

                for raam in ramen:
                    b = raam.get("breedte_m", 0.0)
                    h = raam.get("hoogte_m", 0.0)
                    a_glas = b * h
                    # Reductiefactoren
                    red = raam.get("reductiefactoren", {})
                    factor = (
                        red.get("bebouwing", 1.0)
                        * red.get("vuil", 1.0)
                        * red.get("constructie", 1.0)
                    )
                    a_eq = a_glas * factor
                    totaal_eq += a_eq

                    rows.append([
                        raam.get("naam", ""),
                        f"{b:.2f} × {h:.2f}",
                        raam.get("orientatie", ""),
                        f"{a_glas:.2f}",
                        f"{a_eq:.2f}",
                    ])

                content.append(TableBlock(headers=headers, rows=rows, title="Raamopeningen"))

                # Berekening
                content.append(Spacer(1, 3 * MM_TO_PT))
                eis_abs = vloer * eis_pct / 100.0
                content.append(CalculationBlock(
                    title=f"Equivalente daglichtoppervlakte — {naam}",
                    formula="A_eq,totaal = Σ (A_glas × f_bebouwing × f_vuil × f_constructie)",
                    result=f"{totaal_eq:.2f}",
                    unit="m²",
                    reference="NEN 2057",
                ))

                # Check
                content.append(Spacer(1, 3 * MM_TO_PT))
                uc = totaal_eq / eis_abs if eis_abs > 0 else 0.0
                content.append(CheckBlock(
                    description=f"Daglichttoetreding {naam}",
                    required=f"A_eq ≥ {eis_pct}% × {vloer:.1f} = {eis_abs:.2f} m²",
                    calculated=f"A_eq = {totaal_eq:.2f} m²",
                    unity_check=1.0 / uc if uc > 0 else 999.0,
                    limit=1.0,
                    reference="Bouwbesluit art. 3.74",
                ))

            sections.append({"title": naam, "content": content, "level": 2})

        return sections

    def _build_toetsing(self) -> list[dict[str, Any]]:
        """Bouw samenvattend toetsingsoverzicht."""
        ruimtes = self._data.get("ruimtes", [])
        if not ruimtes:
            return []

        headers = ["Ruimte", "A_vloer (m²)", "Eis (m²)", "A_eq (m²)", "Resultaat"]
        rows: list[list[str]] = []

        for ruimte in ruimtes:
            naam = ruimte.get("naam", "")
            vloer = ruimte.get("vloeroppervlakte_m2", 0.0)
            eis_pct = ruimte.get("eis_percentage", 10.0)
            eis_abs = vloer * eis_pct / 100.0

            totaal_eq = 0.0
            for raam in ruimte.get("ramen", []):
                b = raam.get("breedte_m", 0.0)
                h = raam.get("hoogte_m", 0.0)
                red = raam.get("reductiefactoren", {})
                factor = (
                    red.get("bebouwing", 1.0)
                    * red.get("vuil", 1.0)
                    * red.get("constructie", 1.0)
                )
                totaal_eq += b * h * factor

            voldoet = totaal_eq >= eis_abs
            rows.append([
                naam,
                f"{vloer:.1f}",
                f"{eis_abs:.2f}",
                f"{totaal_eq:.2f}",
                "VOLDOET" if voldoet else "VOLDOET NIET",
            ])

        content: list[Flowable] = [
            TableBlock(
                headers=headers, rows=rows,
                title="Samenvattend overzicht daglichttoetreding",
            ),
        ]
        return [{"title": "Toetsingsoverzicht", "content": content, "level": 1}]

    def _build_conclusie(self) -> list[dict[str, Any]]:
        """Bouw conclusie sectie."""
        conclusie = self._data.get("conclusie", "")
        if not conclusie:
            return []

        content: list[Flowable] = [Paragraph(conclusie, BM_STYLES["Normal"])]
        return [{"title": "Conclusie", "content": content, "level": 1}]
