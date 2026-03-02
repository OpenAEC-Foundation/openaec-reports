"""Tests voor de Report build pipeline."""

from pathlib import Path

from openaec_reports import A4, Report
from openaec_reports.components import CalculationBlock, CheckBlock, ImageBlock, TableBlock


class TestBuildPipeline:
    """Tests voor Report.build() — Fase 1 core engine."""

    def test_build_creates_pdf(self, tmp_path):
        """Report met 1 sectie genereert een PDF bestand."""
        report = Report(
            format=A4,
            project="Testproject",
            project_number="2026-001",
            client="Test BV",
        )
        report.add_section("Uitgangspunten", content=["Dit is een testsectie."])

        output = tmp_path / "test.pdf"
        report.build(output)

        assert output.exists()
        assert output.stat().st_size > 0

    def test_build_empty_report(self, tmp_path):
        """Report zonder secties genereert zonder errors."""
        report = Report(
            format=A4,
            project="Leeg rapport",
            project_number="2026-002",
        )

        output = tmp_path / "empty.pdf"
        report.build(output)

        assert output.exists()

    def test_build_with_toc(self, tmp_path):
        """Report met meerdere secties bevat meer dan 1 pagina."""
        report = Report(format=A4, project="TOC Test", project_number="2026-003")
        report.add_section("Sectie 1", content=["Inhoud sectie 1."])
        report.add_section("Sectie 2", content=["Inhoud sectie 2."])
        report.add_section("Sectie 3", content=["Inhoud sectie 3."])

        output = tmp_path / "toc.pdf"
        report.build(output)

        assert output.exists()
        # Met TOC + 3 secties verwachten we minimaal 2 pagina's
        assert output.stat().st_size > 500

    def test_build_with_cover_and_backcover(self, tmp_path):
        """Report met cover en backcover genereert extra pagina's."""
        report = Report(format=A4, project="Cover Test", project_number="2026-004")
        report.add_cover(subtitle="Constructieve berekening")
        report.add_section("Inhoud", content=["Tekst."])
        report.add_backcover()

        output = tmp_path / "covers.pdf"
        report.build(output)

        assert output.exists()
        assert output.stat().st_size > 500

    def test_build_output_directory_created(self, tmp_path):
        """Output directory wordt automatisch aangemaakt."""
        output = tmp_path / "subdir" / "nested" / "test.pdf"
        assert not output.parent.exists()

        report = Report(format=A4, project="Dir Test")
        report.add_section("Test", content=["Tekst."])
        report.build(output)

        assert output.parent.exists()
        assert output.exists()

    def test_build_returns_path(self, tmp_path):
        """build() retourneert een Path object naar het gegenereerde bestand."""
        report = Report(format=A4, project="Path Test")
        report.add_section("Test", content=["Tekst."])

        output = tmp_path / "result.pdf"
        result = report.build(output)

        assert isinstance(result, Path)
        assert result == output

    def test_build_with_subsections(self, tmp_path):
        """Report met geneste secties (level 1, 2, 3) bouwt correct."""
        report = Report(format=A4, project="Subsections", project_number="2026-005")
        report.add_section("Hoofdstuk 1", level=1, content=["Intro."])
        report.add_section("Paragraaf 1.1", level=2, content=["Detail."])
        report.add_section("Subparagraaf 1.1.1", level=3, content=["Meer detail."])

        output = tmp_path / "subsections.pdf"
        report.build(output)

        assert output.exists()

    def test_build_full_report(self, tmp_path):
        """Volledige report met cover, secties, en backcover."""
        report = Report(
            format=A4,
            project="Volledig Rapport",
            project_number="2026-006",
            client="Opdrachtgever BV",
            author="Ing. Test",
        )
        report.add_cover(subtitle="Constructieve berekening hoofddraagconstructie")
        report.add_section("Uitgangspunten", content=[
            "Dit rapport beschrijft de constructieve berekening.",
            "Alle berekeningen zijn uitgevoerd conform Eurocode.",
        ])
        report.add_section("Belastingen", level=1, content=[
            "Eigen gewicht: 25 kN/m³",
        ])
        report.add_section("Vloerbelasting", level=2, content=[
            "Nuttige belasting: 1.75 kN/m²",
        ])
        report.add_backcover()

        output = tmp_path / "full_report.pdf"
        result = report.build(output)

        assert result.exists()
        assert result.stat().st_size > 1000


class TestConvenienceMethods:
    """Tests voor add_calculation, add_check, add_table, add_image."""

    def test_add_calculation_creates_block(self):
        """add_calculation() voegt een CalculationBlock toe aan de sectie."""
        report = Report(format=A4, project="Test")
        report.add_section("Berekeningen")
        report.add_calculation(
            title="Moment",
            formula="M = q*L²/8",
            substitution="M = 10*6²/8",
            result="M = 45",
            unit="kNm",
            reference="EC3",
        )

        content = report._sections[-1]["content"]
        assert len(content) == 1
        assert isinstance(content[0], CalculationBlock)
        assert content[0].title == "Moment"
        assert content[0].formula == "M = q*L²/8"
        assert content[0].unit == "kNm"

    def test_add_check_creates_block(self):
        """add_check() voegt een CheckBlock toe aan de sectie."""
        report = Report(format=A4, project="Test")
        report.add_section("Toetsing")
        report.add_check(
            description="Buigingscontrole",
            required="UC ≤ 1.0",
            calculated="M_Ed / M_Rd = 0.56",
            unity_check=0.56,
            reference="EC3",
        )

        content = report._sections[-1]["content"]
        assert len(content) == 1
        assert isinstance(content[0], CheckBlock)
        assert content[0].description == "Buigingscontrole"
        assert content[0].unity_check == 0.56
        assert content[0].passes is True

    def test_add_table_creates_block(self):
        """add_table() voegt een TableBlock toe aan de sectie."""
        report = Report(format=A4, project="Test")
        report.add_section("Resultaten")
        report.add_table(
            headers=["Onderdeel", "UC"],
            rows=[["Ligger 1", "0.56"], ["Kolom 1", "0.42"]],
            title="Overzicht",
        )

        content = report._sections[-1]["content"]
        assert len(content) == 1
        assert isinstance(content[0], TableBlock)
        assert content[0].headers == ["Onderdeel", "UC"]
        assert len(content[0].rows) == 2

    def test_add_image_creates_block(self, tmp_path):
        """add_image() voegt een ImageBlock toe aan de sectie."""
        # Maak een test afbeelding
        img_path = tmp_path / "test.png"
        _create_test_png(img_path)

        report = Report(format=A4, project="Test")
        report.add_section("Afbeeldingen")
        report.add_image(path=img_path, caption="Testafbeelding", width_mm=100)

        content = report._sections[-1]["content"]
        assert len(content) == 1
        assert isinstance(content[0], ImageBlock)
        assert content[0].caption == "Testafbeelding"
        assert content[0].width_mm == 100

    def test_add_without_section_creates_implicit(self):
        """Convenience methods zonder bestaande sectie maken een impliciete sectie."""
        report = Report(format=A4, project="Test")
        report.add_calculation(title="Test berekening")

        assert len(report._sections) == 1
        assert isinstance(report._sections[0]["content"][0], CalculationBlock)

    def test_chaining(self):
        """Convenience methods retourneren self voor method chaining."""
        report = Report(format=A4, project="Test")
        result = report.add_section("Test").add_calculation(title="Calc").add_check(
            description="Check", unity_check=0.5
        ).add_table(headers=["A"], rows=[["1"]])

        assert result is report
        assert len(report._sections[-1]["content"]) == 3

    def test_build_with_convenience_methods(self, tmp_path):
        """Report gebouwd met convenience methods genereert geldige PDF."""
        report = Report(format=A4, project="Convenience Test", project_number="T-001")
        report.add_section("Berekeningen")
        report.add_calculation(
            title="Moment",
            formula="M = q*L²/8",
            result="M = 45",
            unit="kNm",
        )
        report.add_check(
            description="UC buiging",
            unity_check=0.45,
        )
        report.add_table(
            headers=["Element", "UC"],
            rows=[["L1", "0.45"]],
        )

        output = tmp_path / "convenience.pdf"
        report.build(output)

        assert output.exists()
        assert output.stat().st_size > 1000


def _create_test_png(path: Path) -> None:
    """Maak een minimale 1x1 PNG voor tests."""
    import struct
    import zlib

    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = _chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    raw = zlib.compress(b"\x00\xff\x00\x00")
    idat = _chunk(b"IDAT", raw)
    iend = _chunk(b"IEND", b"")

    path.write_bytes(sig + ihdr + idat + iend)
