"""Tests voor rapporttype implementaties (StructuralReport, DaylightReport, BuildingCodeReport)."""

from __future__ import annotations

from openaec_reports.reports.building_code import BuildingCodeReport
from openaec_reports.reports.daylight import DaylightReport
from openaec_reports.reports.structural import StructuralReport

# ============================================================
# Fixtures
# ============================================================

STRUCTURAL_DATA = {
    "uitgangspunten": {
        "beschrijving": "Constructieve berekening hoofddraagconstructie.",
        "normen": ["NEN-EN 1990", "NEN-EN 1991", "NEN-EN 1993"],
        "materialen": [
            {"onderdeel": "Liggers", "materiaal": "Staal", "sterkteklasse": "S235"},
            {"onderdeel": "Kolommen", "materiaal": "Staal", "sterkteklasse": "S355"},
        ],
    },
    "belastingen": {
        "beschrijving": "Belastingen conform NEN-EN 1991.",
        "categorieen": [
            {
                "titel": "Eigen gewicht",
                "level": 2,
                "beschrijving": "Gewapend beton: 25 kN/m³.",
            },
            {
                "titel": "Veranderlijke belasting",
                "level": 2,
                "beschrijving": "Categorie A: 1.75 kN/m².",
            },
        ],
    },
    "elementen": [
        {
            "naam": "Ligger L1 — HEA 200",
            "beschrijving": "Overspanning 6.0 m, staal S235.",
            "berekeningen": [
                {
                    "title": "Veldmoment",
                    "formula": "M_Ed = q × l² / 8",
                    "substitution": "M_Ed = 8.7 × 6.0² / 8",
                    "result": "39.1",
                    "unit": "kNm",
                    "reference": "NEN-EN 1993-1-1",
                },
            ],
            "checks": [
                {
                    "description": "UC buiging L1",
                    "required_value": "UC ≤ 1.0",
                    "calculated_value": "M_Ed / M_Rd = 39.1 / 100.9",
                    "unity_check": 0.39,
                    "limit": 1.0,
                    "reference": "NEN-EN 1993-1-1 §6.2.5",
                },
            ],
        },
    ],
    "conclusie": "Alle elementen voldoen aan de gestelde eisen.",
}

DAYLIGHT_DATA = {
    "uitgangspunten": {
        "beschrijving": "Daglichtberekening woning.",
        "norm": "NEN 2057 / Bouwbesluit art. 3.74",
        "gebouwtype": "Woning",
        "gebruiksfunctie": "Woonfunctie",
    },
    "situatie": {
        "beschrijving": "Vrijstaande woning op open terrein.",
        "orientatie": "Voorgevel op het zuiden.",
    },
    "ruimtes": [
        {
            "naam": "Woonkamer",
            "verdieping": "BG",
            "vloeroppervlakte_m2": 30.0,
            "eis_percentage": 10.0,
            "ramen": [
                {
                    "naam": "R1",
                    "breedte_m": 1.5,
                    "hoogte_m": 2.0,
                    "orientatie": "Zuid",
                    "reductiefactoren": {
                        "bebouwing": 1.0,
                        "vuil": 0.9,
                        "constructie": 0.85,
                    },
                },
                {
                    "naam": "R2",
                    "breedte_m": 1.0,
                    "hoogte_m": 1.5,
                    "orientatie": "West",
                    "reductiefactoren": {
                        "bebouwing": 0.9,
                        "vuil": 0.9,
                        "constructie": 0.85,
                    },
                },
            ],
        },
    ],
    "conclusie": "Alle verblijfsgebieden voldoen aan de daglichteis.",
}

BUILDING_CODE_DATA = {
    "uitgangspunten": {
        "beschrijving": "Bouwbesluit toetsing nieuwbouw woning.",
        "gebruiksfunctie": "Woonfunctie",
        "bouwbesluit_versie": "Bouwbesluit 2012",
        "nieuwbouw": True,
    },
    "hoofdstukken": [
        {
            "titel": "Hoofdstuk 3 — Gezondheid",
            "beschrijving": "Toetsing gezondheidsvoorschriften.",
            "toetsingen": [
                {
                    "artikel": "Art. 3.74",
                    "beschrijving": "Daglicht",
                    "eis": "A_eq ≥ 10% × A_vloer",
                    "berekend": "A_eq = 3.5 m² ≥ 3.0 m²",
                    "voldoet": True,
                },
                {
                    "artikel": "Art. 3.29",
                    "beschrijving": "Ventilatie",
                    "eis": "q_v ≥ 0.9 dm³/s per m²",
                    "berekend": "q_v = 1.2 dm³/s per m²",
                    "voldoet": True,
                    "toelichting": "Mechanische ventilatie type C.",
                },
            ],
        },
        {
            "titel": "Hoofdstuk 2 — Veiligheid",
            "beschrijving": "Toetsing veiligheidsvoorschriften.",
            "toetsingen": [
                {
                    "artikel": "Art. 2.4",
                    "beschrijving": "Trappen",
                    "eis": "Aantrede ≥ 220 mm, optrede ≤ 188 mm",
                    "berekend": "Aantrede = 250 mm, optrede = 180 mm",
                    "voldoet": True,
                },
            ],
        },
    ],
    "conclusie": "Het ontwerp voldoet aan alle getoetste artikelen.",
}


# ============================================================
# StructuralReport
# ============================================================


class TestStructuralReport:
    """Tests voor StructuralReport.build_sections()."""

    def test_report_type(self) -> None:
        report = StructuralReport()
        assert report.report_type == "structural"
        assert report.default_template == "structural_report"

    def test_empty_data_returns_empty(self) -> None:
        report = StructuralReport()
        report.load_data({})
        assert report.build_sections() == []

    def test_build_sections_returns_list(self) -> None:
        report = StructuralReport()
        report.load_data(STRUCTURAL_DATA)
        sections = report.build_sections()
        assert isinstance(sections, list)
        assert len(sections) > 0

    def test_section_structure(self) -> None:
        report = StructuralReport()
        report.load_data(STRUCTURAL_DATA)
        sections = report.build_sections()
        for section in sections:
            assert "title" in section
            assert "content" in section
            assert "level" in section
            assert isinstance(section["content"], list)

    def test_expected_section_titles(self) -> None:
        report = StructuralReport()
        report.load_data(STRUCTURAL_DATA)
        sections = report.build_sections()
        titles = [s["title"] for s in sections]
        assert "Uitgangspunten" in titles
        assert "Belastingen" in titles
        assert "Unity check overzicht" in titles
        assert "Conclusie" in titles

    def test_elementen_sections_created(self) -> None:
        report = StructuralReport()
        report.load_data(STRUCTURAL_DATA)
        sections = report.build_sections()
        element_sections = [s for s in sections if "HEA 200" in s["title"]]
        assert len(element_sections) == 1
        assert element_sections[0]["page_break_before"] is True

    def test_belasting_subsecties(self) -> None:
        report = StructuralReport()
        report.load_data(STRUCTURAL_DATA)
        sections = report.build_sections()
        level2 = [s for s in sections if s["level"] == 2]
        assert len(level2) == 2  # Eigen gewicht + Veranderlijke belasting

    def test_uc_overzicht_has_content(self) -> None:
        report = StructuralReport()
        report.load_data(STRUCTURAL_DATA)
        sections = report.build_sections()
        uc = [s for s in sections if s["title"] == "Unity check overzicht"]
        assert len(uc) == 1
        assert len(uc[0]["content"]) > 0

    def test_partial_data_uitgangspunten_only(self) -> None:
        report = StructuralReport()
        report.load_data({"uitgangspunten": {"beschrijving": "Test"}})
        sections = report.build_sections()
        assert len(sections) == 1
        assert sections[0]["title"] == "Uitgangspunten"

    def test_generate_pdf(self, tmp_path) -> None:
        """Integratie: StructuralReport → PDF."""
        report = StructuralReport(
            project="Testproject",
            project_number="2026-001",
            client="Testklant",
        )
        report.load_data(STRUCTURAL_DATA)
        output = tmp_path / "structural.pdf"
        result = report.generate(output)
        assert result.exists()
        with open(result, "rb") as f:
            assert f.read(4) == b"%PDF"


# ============================================================
# DaylightReport
# ============================================================


class TestDaylightReport:
    """Tests voor DaylightReport.build_sections()."""

    def test_report_type(self) -> None:
        report = DaylightReport()
        assert report.report_type == "daylight"

    def test_empty_data_returns_empty(self) -> None:
        report = DaylightReport()
        report.load_data({})
        assert report.build_sections() == []

    def test_build_sections_returns_list(self) -> None:
        report = DaylightReport()
        report.load_data(DAYLIGHT_DATA)
        sections = report.build_sections()
        assert isinstance(sections, list)
        assert len(sections) > 0

    def test_expected_section_titles(self) -> None:
        report = DaylightReport()
        report.load_data(DAYLIGHT_DATA)
        sections = report.build_sections()
        titles = [s["title"] for s in sections]
        assert "Uitgangspunten" in titles
        assert "Situatie en oriëntatie" in titles
        assert "Daglichtberekening per ruimte" in titles
        assert "Toetsingsoverzicht" in titles
        assert "Conclusie" in titles

    def test_ruimte_subsecties(self) -> None:
        report = DaylightReport()
        report.load_data(DAYLIGHT_DATA)
        sections = report.build_sections()
        woonkamer = [s for s in sections if s["title"] == "Woonkamer"]
        assert len(woonkamer) == 1
        assert woonkamer[0]["level"] == 2

    def test_ruimte_content_has_check_and_calc(self) -> None:
        """Elke ruimte bevat CalculationBlock en CheckBlock."""
        report = DaylightReport()
        report.load_data(DAYLIGHT_DATA)
        sections = report.build_sections()
        woonkamer = [s for s in sections if s["title"] == "Woonkamer"][0]
        types = [type(c).__name__ for c in woonkamer["content"]]
        assert "CalculationBlock" in types
        assert "CheckBlock" in types

    def test_partial_data_situatie_only(self) -> None:
        report = DaylightReport()
        report.load_data({"situatie": {"beschrijving": "Open terrein"}})
        sections = report.build_sections()
        assert len(sections) == 1
        assert sections[0]["title"] == "Situatie en oriëntatie"

    def test_generate_pdf(self, tmp_path) -> None:
        """Integratie: DaylightReport → PDF."""
        report = DaylightReport(
            project="Daglichtest",
            project_number="2026-002",
            client="Testklant",
        )
        report.load_data(DAYLIGHT_DATA)
        output = tmp_path / "daylight.pdf"
        result = report.generate(output)
        assert result.exists()
        with open(result, "rb") as f:
            assert f.read(4) == b"%PDF"


# ============================================================
# BuildingCodeReport
# ============================================================


class TestBuildingCodeReport:
    """Tests voor BuildingCodeReport.build_sections()."""

    def test_report_type(self) -> None:
        report = BuildingCodeReport()
        assert report.report_type == "building_code"

    def test_empty_data_returns_empty(self) -> None:
        report = BuildingCodeReport()
        report.load_data({})
        assert report.build_sections() == []

    def test_build_sections_returns_list(self) -> None:
        report = BuildingCodeReport()
        report.load_data(BUILDING_CODE_DATA)
        sections = report.build_sections()
        assert isinstance(sections, list)
        assert len(sections) > 0

    def test_expected_section_titles(self) -> None:
        report = BuildingCodeReport()
        report.load_data(BUILDING_CODE_DATA)
        sections = report.build_sections()
        titles = [s["title"] for s in sections]
        assert "Projectgegevens en uitgangspunten" in titles
        assert "Samenvattend overzicht" in titles
        assert "Conclusie" in titles

    def test_hoofdstuk_sections(self) -> None:
        report = BuildingCodeReport()
        report.load_data(BUILDING_CODE_DATA)
        sections = report.build_sections()
        gezondheid = [s for s in sections if "Gezondheid" in s["title"]]
        assert len(gezondheid) == 1
        veiligheid = [s for s in sections if "Veiligheid" in s["title"]]
        assert len(veiligheid) == 1

    def test_check_blocks_in_hoofdstuk(self) -> None:
        """Elke toetsing in een hoofdstuk bevat CheckBlock."""
        from openaec_reports.components.check_block import CheckBlock

        report = BuildingCodeReport()
        report.load_data(BUILDING_CODE_DATA)
        sections = report.build_sections()
        gezondheid = [s for s in sections if "Gezondheid" in s["title"]][0]
        check_blocks = [c for c in gezondheid["content"] if isinstance(c, CheckBlock)]
        assert len(check_blocks) == 2  # Art. 3.74 + Art. 3.29

    def test_overzicht_tabel(self) -> None:
        """Samenvattend overzicht bevat TableBlock."""
        from openaec_reports.components.table_block import TableBlock

        report = BuildingCodeReport()
        report.load_data(BUILDING_CODE_DATA)
        sections = report.build_sections()
        overzicht = [s for s in sections if s["title"] == "Samenvattend overzicht"]
        assert len(overzicht) == 1
        tables = [c for c in overzicht[0]["content"] if isinstance(c, TableBlock)]
        assert len(tables) == 1

    def test_toelichting_rendered(self) -> None:
        """Toetsing met toelichting genereert extra Paragraph."""
        from reportlab.platypus import Paragraph

        report = BuildingCodeReport()
        report.load_data(BUILDING_CODE_DATA)
        sections = report.build_sections()
        gezondheid = [s for s in sections if "Gezondheid" in s["title"]][0]
        paragraphs = [c for c in gezondheid["content"] if isinstance(c, Paragraph)]
        # Minstens 1 toelichting paragraph + 1 beschrijving paragraph
        assert len(paragraphs) >= 1

    def test_nieuwbouw_label(self) -> None:
        report = BuildingCodeReport()
        report.load_data(BUILDING_CODE_DATA)
        sections = report.build_sections()
        uitgangspunten = [s for s in sections if "uitgangspunten" in s["title"].lower()][0]
        # Check dat content Paragraph bevat met "Nieuwbouw"
        from reportlab.platypus import Paragraph
        paras = [c for c in uitgangspunten["content"] if isinstance(c, Paragraph)]
        texts = [p.text for p in paras]
        assert any("Nieuwbouw" in t for t in texts)

    def test_generate_pdf(self, tmp_path) -> None:
        """Integratie: BuildingCodeReport → PDF."""
        report = BuildingCodeReport(
            project="BB Toets",
            project_number="2026-003",
            client="Testklant",
        )
        report.load_data(BUILDING_CODE_DATA)
        output = tmp_path / "building_code.pdf"
        result = report.generate(output)
        assert result.exists()
        with open(result, "rb") as f:
            assert f.read(4) == b"%PDF"
