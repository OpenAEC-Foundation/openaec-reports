"""End-to-end test — Template Engine met echte Customer tenant data.

Laadt example JSON, transformeert naar engine formaat, genereert PDF.
Verifiëert bestandsgrootte en paginatelling.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
TENANTS_DIR = PROJECT_ROOT / "tenants"
CUSTOMER_DIR = TENANTS_DIR / "customer"
EXAMPLE_JSON = PROJECT_ROOT / "schemas" / "example_customer_bic_factuur.json"
OUTPUT_DIR = PROJECT_ROOT / "output"

SKIP_NO_TENANT = pytest.mark.skipif(
    not CUSTOMER_DIR.exists(),
    reason="Customer tenant directory niet aanwezig",
)

SKIP_NO_EXAMPLE = pytest.mark.skipif(
    not EXAMPLE_JSON.exists(),
    reason="Example JSON niet aanwezig",
)


def _transform_json_to_engine_data(raw: dict) -> dict:
    """Transformeer de example JSON naar het flat formaat dat de engine verwacht.

    De template engine resolves bind paden via dot-notatie op de data dict.
    Page types verwachten:
    - meta.factuur_kop, meta.datum, meta.factuurnummer
    - project.name, client.name
    - location.name, location.address, location.postcode_plaats, etc.
    - bic_sections (flat list van dicts met label/ref_value/actual_value)
    - detail_items (flat list van dicts)
    - objecten (flat list van dicts)
    """
    # Cover extra fields
    cover = raw.get("cover", {})
    extra = cover.get("extra_fields", {})

    # Location data uit sections
    location_data = {}
    bic_sections_flat: list[dict] = []
    detail_items: list[dict] = []
    objecten: list[dict] = []

    for section in raw.get("sections", []):
        for content_block in section.get("content", []):
            block_type = content_block.get("type", "")

            if block_type == "location_detail":
                loc = content_block.get("location", {})
                location_data = {
                    "name": loc.get("name", ""),
                    "address": loc.get("address", ""),
                    "postcode_plaats": loc.get("city", ""),
                    "code": loc.get("code", ""),
                    "provision": loc.get("provision", ""),
                    "object": loc.get("object", ""),
                    "contact": content_block.get("client", {}).get("name", ""),
                    "telefoon": "",
                }

            elif block_type == "bic_table":
                # Flatten alle sectie rijen naar één lijst
                for bic_section in content_block.get("sections", []):
                    for row in bic_section.get("rows", []):
                        bic_sections_flat.append(row)
                # Voeg summary rijen toe
                summary = content_block.get("summary", {})
                for row in summary.get("rows", []):
                    bic_sections_flat.append(row)
                total = summary.get("total")
                if total:
                    bic_sections_flat.append(total)

            elif block_type == "table":
                title = section.get("title", "")
                headers = content_block.get("headers", [])
                rows = content_block.get("rows", [])

                if "Detail" in title:
                    for row_values in rows:
                        detail_items.append({
                            headers[i] if i < len(headers) else f"col_{i}": v
                            for i, v in enumerate(row_values)
                        })
                elif "objecten" in title.lower() or "Voorziening" in title:
                    for row_values in rows:
                        objecten.append({
                            headers[i] if i < len(headers) else f"col_{i}": v
                            for i, v in enumerate(row_values)
                        })

    return {
        "meta": {
            "factuur_kop": raw.get("report_type", "BIC Factuur"),
            "datum": extra.get("Datum", raw.get("date", "")),
            "factuurnummer": extra.get("Factuurnummer", ""),
        },
        "project": {
            "name": raw.get("project", ""),
        },
        "client": {
            "name": raw.get("client", ""),
        },
        "location": location_data,
        "bic_sections": bic_sections_flat,
        "detail_items": detail_items,
        "objecten": objecten,
    }


@SKIP_NO_TENANT
@SKIP_NO_EXAMPLE
class TestTemplateE2E:
    """End-to-end test: JSON → TemplateEngine → PDF."""

    @pytest.fixture()
    def engine_data(self) -> dict:
        """Laad en transformeer example JSON."""
        with EXAMPLE_JSON.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        return _transform_json_to_engine_data(raw)

    def test_generate_pdf(self, engine_data: dict) -> None:
        """Genereer PDF en verifieer output."""
        from bm_reports.core.template_engine import TemplateEngine

        output_path = OUTPUT_DIR / "test_template_e2e.pdf"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        engine = TemplateEngine(tenants_dir=TENANTS_DIR)
        result = engine.build(
            template_name="bic_factuur",
            tenant="customer",
            data=engine_data,
            output_path=output_path,
        )

        # Verifieer bestand
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
            tenant="customer",
            data=engine_data,
            output_path=output_path,
        )

        # Tel pagina's met PyMuPDF (fitz) of pdfrw
        page_count = _count_pdf_pages(output_path)
        assert page_count is not None, "Kan PDF pagina's niet tellen (PyMuPDF/pdfrw nodig)"
        assert page_count == 6, (
            f"Verwacht 6 pagina's (voorblad, locatie, bic_controles, "
            f"detail, objecten, achterblad), maar kreeg {page_count}"
        )

    def test_data_transformation(self, engine_data: dict) -> None:
        """Verifieer dat de data transformatie correct is."""
        assert engine_data["meta"]["factuur_kop"] == "BIC Factuur"
        assert engine_data["meta"]["factuurnummer"] == "F2026-0283"
        assert engine_data["project"]["name"] == "Jaarlijkse BIC controle 2026"
        assert engine_data["client"]["name"] == "Stichting Woonbron"
        assert engine_data["location"]["name"] == "Woonerf De Mathenesserdijk"
        assert len(engine_data["bic_sections"]) > 0
        assert len(engine_data["detail_items"]) > 0
        assert len(engine_data["objecten"]) > 0


def _count_pdf_pages(path: Path) -> int | None:
    """Tel het aantal pagina's in een PDF bestand."""
    try:
        import fitz  # PyMuPDF

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
