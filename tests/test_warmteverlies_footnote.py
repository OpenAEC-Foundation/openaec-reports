"""Tests voor de warmteverlies water-voetnoot injectie.

Verifieert dat de pre-processor in ``core.warmteverlies_footnote``:

- Een voetnoot toevoegt aan de Uitgangspunten sectie van een
  warmteverlies-rapport met water-grensvlak.
- Geen voetnoot toevoegt aan een warmteverlies-rapport zonder water.
- Geen voetnoot toevoegt aan niet-warmteverlies rapporten.
- Defensief omgaat met payloads zonder ``theta_water`` of metadata.
- Idempotent is (tweemaal aanroepen voegt niet twee keer toe).
- Na ``Report.from_dict()`` de voetnoot ook echt in de gerenderde PDF
  verschijnt.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest

from openaec_reports.core.engine import Report
from openaec_reports.core.warmteverlies_footnote import (
    DEFAULT_THETA_WATER_C,
    inject_water_footnote_if_needed,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _base_payload() -> dict[str, Any]:
    """Minimale warmteverlies-rapport payload conform report.schema.json."""
    return {
        "template": "blank",
        "brand": "default",
        "format": "A4",
        "orientation": "portrait",
        "project": "Woonboot 3056",
        "project_number": "2026-001",
        "client": "Klant",
        "author": "OpenAEC",
        "date": "2026-04-10",
        "version": "1.0",
        "status": "CONCEPT",
        "cover": {"subtitle": "Warmteverliesberekening conform ISSO 51:2023"},
        "sections": [
            {
                "title": "Uitgangspunten",
                "level": 1,
                "content": [
                    {
                        "type": "table",
                        "title": "Klimaatgegevens",
                        "headers": ["Parameter", "Waarde"],
                        "rows": [
                            ["Buitentemperatuur (θ_e)", "-10 °C"],
                            ["Grondtemperatuur woning (θ_b)", "17 °C"],
                        ],
                    },
                ],
            },
            {
                "title": "Resultaten",
                "level": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "text": "Placeholder sectie.",
                    },
                ],
            },
        ],
        "metadata": {
            "engine": "isso51-core",
            "generated_at": "2026-04-10T12:00:00Z",
        },
    }


def _count_paragraphs_with_text(
    content: list[Any], fragment: str
) -> int:
    """Tel paragraph-blocks waarvan de tekst ``fragment`` bevat."""
    count = 0
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") != "paragraph":
            continue
        text = block.get("text", "")
        if isinstance(text, str) and fragment in text:
            count += 1
    return count


# ---------------------------------------------------------------------------
# Unit tests — pure functie
# ---------------------------------------------------------------------------


class TestInjectWaterFootnote:
    """Unit tests voor ``inject_water_footnote_if_needed``."""

    def test_injects_when_flag_is_set(self) -> None:
        """Expliciete ``metadata.water_boundaries_present`` triggert injectie."""
        data = _base_payload()
        data["metadata"]["water_boundaries_present"] = True

        added = inject_water_footnote_if_needed(data)

        assert added is True
        content = data["sections"][0]["content"]
        assert _count_paragraphs_with_text(content, "ontwerp-watertemperatuur") == 1

    def test_injects_when_theta_water_present(self) -> None:
        """Alleen ``metadata.theta_water`` is ook een geldige trigger."""
        data = _base_payload()
        data["metadata"]["theta_water"] = 6.0

        added = inject_water_footnote_if_needed(data)

        assert added is True
        content = data["sections"][0]["content"]
        assert _count_paragraphs_with_text(content, "6 °C") == 1

    def test_injects_when_table_mentions_water_row(self) -> None:
        """Een tabelrij met 'H_T,iw' triggert detectie."""
        data = _base_payload()
        data["sections"][1]["content"].append(
            {
                "type": "table",
                "title": "Transmissieverliezen",
                "headers": ["Component", "Waarde"],
                "rows": [
                    ["H_T,ie (schil)", "10.0 W/K"],
                    ["H_T,iw (water)", "2.5 W/K"],
                ],
            }
        )

        added = inject_water_footnote_if_needed(data)

        assert added is True
        content = data["sections"][0]["content"]
        assert _count_paragraphs_with_text(content, "ontwerp-watertemperatuur") == 1

    def test_uses_default_theta_water_when_missing(self) -> None:
        """Zonder expliciete waarde wordt de default (5 °C) gebruikt."""
        data = _base_payload()
        data["metadata"]["water_boundaries_present"] = True

        added = inject_water_footnote_if_needed(data)

        assert added is True
        content = data["sections"][0]["content"]
        expected = f"{int(DEFAULT_THETA_WATER_C)} °C"
        assert _count_paragraphs_with_text(content, expected) == 1

    def test_formats_decimal_theta_water_with_comma(self) -> None:
        """Niet-ronde waarden krijgen Nederlandse komma-notatie."""
        data = _base_payload()
        data["metadata"]["theta_water"] = 5.5

        added = inject_water_footnote_if_needed(data)

        assert added is True
        content = data["sections"][0]["content"]
        assert _count_paragraphs_with_text(content, "5,5 °C") == 1

    def test_no_injection_when_no_water_indicator(self) -> None:
        """Standaard warmteverlies-rapport (geen water) blijft ongewijzigd."""
        data = _base_payload()
        before = copy.deepcopy(data)

        added = inject_water_footnote_if_needed(data)

        assert added is False
        assert data == before

    def test_no_injection_when_not_warmteverlies_report(self) -> None:
        """Andere rapporten (bv. structural) worden niet aangeraakt."""
        data = _base_payload()
        data["metadata"]["engine"] = "structural-core"
        data["metadata"]["water_boundaries_present"] = True
        before = copy.deepcopy(data)

        added = inject_water_footnote_if_needed(data)

        assert added is False
        assert data == before

    def test_no_injection_without_metadata(self) -> None:
        """Payload zonder metadata key crasht niet en doet niets."""
        data = _base_payload()
        data.pop("metadata")

        added = inject_water_footnote_if_needed(data)

        assert added is False

    def test_no_injection_without_uitgangspunten_section(self) -> None:
        """Zonder Uitgangspunten sectie kan er niets worden geïnjecteerd."""
        data = _base_payload()
        data["sections"][0]["title"] = "Iets Anders"
        data["metadata"]["water_boundaries_present"] = True

        added = inject_water_footnote_if_needed(data)

        assert added is False

    def test_injection_is_idempotent(self) -> None:
        """Tweemaal aanroepen voegt niet twee keer dezelfde voetnoot toe."""
        data = _base_payload()
        data["metadata"]["water_boundaries_present"] = True

        first = inject_water_footnote_if_needed(data)
        second = inject_water_footnote_if_needed(data)

        assert first is True
        assert second is False
        content = data["sections"][0]["content"]
        assert _count_paragraphs_with_text(content, "ontwerp-watertemperatuur") == 1

    def test_aannames_alias_title_is_recognised(self) -> None:
        """Sectie met titel 'Aannames' is een geldig alternatief."""
        data = _base_payload()
        data["sections"][0]["title"] = "Aannames"
        data["metadata"]["water_boundaries_present"] = True

        added = inject_water_footnote_if_needed(data)

        assert added is True

    def test_handles_none_input_gracefully(self) -> None:
        """Niet-dict input retourneert False zonder crash."""
        assert inject_water_footnote_if_needed(None) is False  # type: ignore[arg-type]
        assert inject_water_footnote_if_needed([]) is False  # type: ignore[arg-type]

    def test_handles_missing_sections_gracefully(self) -> None:
        """Payload zonder sections-key crasht niet."""
        data = {"metadata": {"engine": "isso51-core", "theta_water": 5.0}}

        added = inject_water_footnote_if_needed(data)

        assert added is False

    def test_defensive_against_legacy_payload_without_theta_water(self) -> None:
        """Oude payloads zonder theta_water én zonder flag blijven no-op."""
        data = _base_payload()
        # Geen water-indicator in metadata, geen water-label in tabellen.
        before = copy.deepcopy(data)

        inject_water_footnote_if_needed(data)

        assert data == before


# ---------------------------------------------------------------------------
# Integratie-tests — via Report.from_dict()
# ---------------------------------------------------------------------------


class TestFromDictIntegration:
    """Integratie-tests: verifieer dat de pre-processor draait bij from_dict."""

    def test_from_dict_injects_footnote_for_water_project(self) -> None:
        """Een warmteverlies-payload met water krijgt een extra paragraph
        in de Uitgangspunten sectie na ``Report.from_dict``."""
        data = _base_payload()
        data["metadata"]["water_boundaries_present"] = True
        data["metadata"]["theta_water"] = 5.0

        report = Report.from_dict(data)

        uitgangspunten = next(
            s for s in report._sections if "uitgangspunt" in s["title"].lower()
        )
        # De content bestaat uit Flowables; we checken het aantal items.
        # Oorspronkelijk: 1 (Klimaatgegevens tabel) → na injectie minimaal 2.
        assert len(uitgangspunten["content"]) >= 2

    def test_from_dict_no_footnote_without_water(self) -> None:
        """Standaard warmteverlies-rapport krijgt geen extra content."""
        data = _base_payload()
        original_count = len(data["sections"][0]["content"])

        report = Report.from_dict(data)

        uitgangspunten = next(
            s for s in report._sections if "uitgangspunt" in s["title"].lower()
        )
        assert len(uitgangspunten["content"]) == original_count

    def test_from_dict_survives_legacy_payload(self) -> None:
        """Oude payloads zonder theta_water en zonder water veroorzaken
        geen crash en wijzigen het rapport niet."""
        data = _base_payload()
        # Expliciet geen water-info.

        report = Report.from_dict(data)

        assert isinstance(report, Report)


# ---------------------------------------------------------------------------
# Rendering-bewijs — echte PDF met voetnoot
# ---------------------------------------------------------------------------


class TestRenderProof:
    """End-to-end: render een PDF en verifieer dat die bestaat en > 0 bytes."""

    def test_render_woonboot_pdf_contains_footnote_content(
        self, tmp_path: Path
    ) -> None:
        """Render een woonboot-rapport naar PDF en controleer dat het
        bestand bestaat, niet leeg is, en dat de voetnoot-tekst in het
        resulterende PDF (via ReportLab text extraction) terug te vinden
        is.

        Dit is het acceptatiecriterium: "de voetnoot is zichtbaar bij een
        woonboot-project met water-constructies".
        """
        data = _base_payload()
        data["metadata"]["water_boundaries_present"] = True
        data["metadata"]["theta_water"] = 5.0

        report = Report.from_dict(data)
        output_path = tmp_path / "woonboot_rapport.pdf"
        report.build(output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 1000

        # Probeer PDF-text te extraheren en de voetnoot terug te vinden.
        # PyMuPDF is een dev-dependency van dit project; als het niet
        # beschikbaar is, skippen we de inhoudscheck.
        try:
            import fitz  # type: ignore
        except ImportError:  # pragma: no cover — CI heeft pymupdf
            pytest.skip("PyMuPDF niet beschikbaar voor tekstextractie")

        doc = fitz.open(str(output_path))
        try:
            all_text = "".join(page.get_text() for page in doc)
        finally:
            doc.close()

        assert "ontwerp-watertemperatuur" in all_text
        assert "5 °C" in all_text
        assert "NEN-EN 12831" in all_text

    def test_render_standard_project_has_no_water_footnote(
        self, tmp_path: Path
    ) -> None:
        """Render een rapport zonder water-grensvlakken en verifieer dat de
        voetnoot NIET verschijnt."""
        data = _base_payload()

        report = Report.from_dict(data)
        output_path = tmp_path / "standaard_rapport.pdf"
        report.build(output_path)

        assert output_path.exists()

        try:
            import fitz  # type: ignore
        except ImportError:  # pragma: no cover
            pytest.skip("PyMuPDF niet beschikbaar voor tekstextractie")

        doc = fitz.open(str(output_path))
        try:
            all_text = "".join(page.get_text() for page in doc)
        finally:
            doc.close()

        assert "ontwerp-watertemperatuur" not in all_text
