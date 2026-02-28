"""End-to-end test — Template Engine met echte Symitech tenant data.

Laadt example JSON, transformeert naar engine formaat, genereert PDF.
Verifiëert bestandsgrootte en paginatelling.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bm_reports.core.data_transform import transform_json_to_engine_data

PROJECT_ROOT = Path(__file__).parent.parent
TENANTS_DIR = PROJECT_ROOT / "tenants"
SYMITECH_DIR = TENANTS_DIR / "symitech"
EXAMPLE_JSON = PROJECT_ROOT / "schemas" / "example_symitech_bic_factuur.json"
TEST_JSON = PROJECT_ROOT / "schemas" / "test_336_bic_factuur.json"
OUTPUT_DIR = PROJECT_ROOT / "output"

SKIP_NO_TENANT = pytest.mark.skipif(
    not SYMITECH_DIR.exists(),
    reason="Symitech tenant directory niet aanwezig",
)

SKIP_NO_EXAMPLE = pytest.mark.skipif(
    not EXAMPLE_JSON.exists(),
    reason="Example JSON niet aanwezig",
)


@SKIP_NO_TENANT
@SKIP_NO_EXAMPLE
class TestTemplateE2E:
    """End-to-end test: JSON → TemplateEngine → PDF."""

    @pytest.fixture()
    def engine_data(self) -> dict:
        """Laad en transformeer example JSON."""
        with EXAMPLE_JSON.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        return transform_json_to_engine_data(raw)

    def test_generate_pdf(self, engine_data: dict) -> None:
        """Genereer PDF en verifieer output."""
        from bm_reports.core.template_engine import TemplateEngine

        output_path = OUTPUT_DIR / "test_template_e2e.pdf"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        engine = TemplateEngine(tenants_dir=TENANTS_DIR)
        result = engine.build(
            template_name="bic_factuur",
            tenant="symitech",
            data=engine_data,
            output_path=output_path,
        )

        assert result.exists(), f"PDF niet aangemaakt: {result}"
        assert result.stat().st_size > 0, "PDF is leeg (0 bytes)"

    def test_page_count(self, engine_data: dict) -> None:
        """Verifieer het aantal pagina's (verwacht: 6)."""
        from bm_reports.core.template_engine import TemplateEngine

        output_path = OUTPUT_DIR / "test_template_e2e_pagecount.pdf"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        engine = TemplateEngine(tenants_dir=TENANTS_DIR)
        engine.build(
            template_name="bic_factuur",
            tenant="symitech",
            data=engine_data,
            output_path=output_path,
        )

        page_count = _count_pdf_pages(output_path)
        assert page_count is not None, "Kan PDF pagina's niet tellen"
        assert page_count == 6, (
            f"Verwacht 6 pagina's, maar kreeg {page_count}"
        )

    def test_data_transformation(self, engine_data: dict) -> None:
        """Verifieer dat de data transformatie correct is."""
        assert engine_data["meta"]["factuur_kop"] == "BIC Factuur"
        assert engine_data["meta"]["factuurnummer"] == "F2026-0283"
        assert engine_data["meta"]["type_offerte"] == "BIC Controle:"
        assert "336.01" in engine_data["meta"]["offerte_regel"]
        assert "WB-RTD-0047" in engine_data["meta"]["rapportkop_locatie"]
        assert engine_data["project"]["name"] == "Jaarlijkse BIC controle 2026"
        assert engine_data["client"]["name"] == "Stichting Woonbron"
        assert engine_data["client"]["address"] == "Schiedamseweg 46"
        assert engine_data["client"]["postcode_plaats"] == "3025 AE Rotterdam"
        assert engine_data["location"]["name"] == "Woonerf De Mathenesserdijk"
        assert engine_data["location"]["provision"] == "Droge blusleiding / BMI"
        assert len(engine_data["bic_sections"]) > 0
        assert len(engine_data["detail_items"]) > 0
        assert len(engine_data["objecten"]) > 0
        # Verify objecten has Type2 for duplicate header
        assert "Type2" in engine_data["objecten"][0]


class TestDataTransformationStandalone:
    """Transformatie tests die geen tenant dir nodig hebben."""

    def test_transform_336_json(self) -> None:
        """Test transformatie van de 336 test JSON."""
        json_path = PROJECT_ROOT / "schemas" / "test_336_bic_factuur.json"
        if not json_path.exists():
            pytest.skip("test_336_bic_factuur.json niet aanwezig")

        with json_path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        data = transform_json_to_engine_data(raw)

        # Meta
        assert data["meta"]["factuur_kop"] == "BIC Factuur"
        assert data["meta"]["factuurnummer"] == "F2025-1247"
        assert data["meta"]["datum"] == "15 december 2025"
        assert data["meta"]["type_offerte"] == "BIC Controle:"
        assert "336.01" in data["meta"]["offerte_regel"]
        assert "Strandbaak Kijkduin" in data["meta"]["offerte_regel"]
        assert "HW-DH-0336" in data["meta"]["rapportkop_locatie"]

        # Client
        assert data["client"]["name"] == "Haagwonen"
        assert data["client"]["address"] == "Wielingenstraat 22"
        assert data["client"]["postcode_plaats"] == "2584 XZ Den Haag"

        # Location
        assert data["location"]["name"] == "Strandbaak Kijkduin"
        assert data["location"]["code"] == "HW-DH-0336"
        assert "Sprinkler" in data["location"]["provision"]

        # BIC sections
        assert len(data["bic_sections"]) == 14  # 6 + 2 + 2 + 1 + 3 summary
        assert data["bic_sections"][-1]["label"] == "Totaal"
        assert data["bic_sections"][-1]["actual_value"] == "€ 4.274,00"

        # Detail items
        assert len(data["detail_items"]) == 6
        assert data["detail_items"][0]["BIC Controle nummer"] == "BIC-2025-0336-001"

        # Objecten
        assert len(data["objecten"]) == 12
        assert "Type2" in data["objecten"][0]  # Duplicate "Type" header → Type2
        assert data["objecten"][0]["Type2"] == "Stijgleiding"


def _count_pdf_pages(path: Path) -> int | None:
    """Tel het aantal pagina's in een PDF bestand."""
    try:
        import fitz

        doc = fitz.open(str(path))
        count = len(doc)
        doc.close()
        return count
    except ImportError:
        pass

    try:
        from pdfrw import PdfReader

        reader = PdfReader(str(path))
        return len(reader.pages)
    except ImportError:
        pass

    return None
