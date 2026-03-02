"""Integratietests voor Symitech tenant: brand + modules + block_registry.

Test de volledige pipeline:
- Brand laden via BrandLoader
- Modules beschikbaar via ModuleRegistry
- Modules renderen via create_block() met tenant parameter
- Compleet rapport bouwen naar PDF
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Flowable, SimpleDocTemplate, Spacer

from openaec_reports.core.block_registry import create_block
from openaec_reports.core.brand import BrandConfig, BrandLoader
from openaec_reports.modules import ModuleRegistry
from openaec_reports.modules.base import ModuleConfig
from openaec_reports.modules.symitech import register_symitech_modules
from openaec_reports.modules.symitech.bic_table import BicTableModule
from openaec_reports.modules.symitech.location_detail import LocationDetailModule


@pytest.fixture(autouse=True)
def _ensure_symitech_registered():
    """Registreer Symitech modules voor elke test.

    Nodig omdat test_modules_foundation.py ModuleRegistry.reset() aanroept.
    """
    register_symitech_modules()


# ---------------------------------------------------------------------------
# Voorbeeld data
# ---------------------------------------------------------------------------

BIC_TABLE_DATA = {
    "type": "bic_table",
    "location_name": "Amsterdam Noord",
    "sections": [
        {
            "title": "BIC Controles",
            "rows": [
                {
                    "label": "Aantal BIC controles",
                    "ref_value": "12",
                    "actual_value": "14",
                },
                {
                    "label": "Kosten",
                    "ref_value": "\u20ac 3.400,00",
                    "actual_value": "\u20ac 3.966,67",
                },
            ],
        },
    ],
    "summary": {
        "title": "Overzicht samenvatting",
        "rows": [
            {
                "label": "BIC controles",
                "ref_value": "\u20ac 3.400,00",
                "actual_value": "\u20ac 3.966,67",
            },
        ],
        "total": {
            "label": "Totaal",
            "ref_value": "\u20ac 3.400,00",
            "actual_value": "\u20ac 3.966,67",
        },
    },
}

LOCATION_DETAIL_DATA = {
    "type": "location_detail",
    "title": "Locatie",
    "client": {
        "section_title": "Opdrachtgever",
        "name": "Gemeente Amsterdam",
        "address": "Amstel 1",
        "city": "1011 PN Amsterdam",
    },
    "location": {
        "section_title": "Locatie van uitvoer",
        "name": "Depot Noord",
        "address": "Industrieweg 10",
        "city": "1013 AB Amsterdam",
        "code": "LOC-2026-001",
        "provision": "Grondwatermonitoring",
        "object": "Peilbuis PB-01",
    },
    "photo_path": None,
}

COST_SUMMARY_DATA = {
    "type": "cost_summary",
    "title": "Kostenopgave",
    "columns": ["Omschrijving", "Aantal", "Eenheidsprijs", "Totaal"],
    "rows": [
        {
            "description": "BIC controles",
            "quantity": 12,
            "unit_price": 283.33,
            "total": 3400.00,
        },
    ],
    "total": 3400.00,
}

OBJECT_DESCRIPTION_DATA = {
    "type": "object_description",
    "title": "Objectbeschrijving",
    "object_name": "Peilbuis PB-01",
    "fields": [
        {"label": "Type", "value": "Grondwaterpeilbuis"},
        {"label": "Diameter", "value": "50 mm"},
    ],
    "notes": "Geplaatst in 2019.",
    "photo_path": None,
}


# ===================================================================
# Brand + ModuleRegistry integratie
# ===================================================================


class TestBrandModuleIntegration:
    """Test dat brand config en ModuleRegistry samenwerken."""

    def test_load_symitech_brand(self) -> None:
        """BrandLoader kan Symitech brand laden."""
        loader = BrandLoader()
        brand = loader.load("symitech")
        assert isinstance(brand, BrandConfig)
        assert brand.name == "Symitech B.V."
        assert brand.tenant == "symitech"

    def test_brand_lists_tenant_modules(self) -> None:
        """Brand config bevat de 4 tenant module types."""
        loader = BrandLoader()
        brand = loader.load("symitech")
        assert set(brand.tenant_modules) == {
            "bic_table",
            "cost_summary",
            "location_detail",
            "object_description",
        }

    def test_registry_has_all_brand_modules(self) -> None:
        """Alle modules uit brand config zijn geregistreerd in ModuleRegistry."""
        loader = BrandLoader()
        brand = loader.load("symitech")
        for module_type in brand.tenant_modules:
            cls = ModuleRegistry.get(module_type, tenant="symitech")
            assert cls is not None, f"Module {module_type!r} niet geregistreerd"

    def test_brand_module_config_to_module_config(self) -> None:
        """Brand module_config kan worden omgezet naar ModuleConfig."""
        loader = BrandLoader()
        brand = loader.load("symitech")
        mc = brand.module_config
        config = ModuleConfig(
            label_size=mc.get("label_size", 10.0),
            value_size=mc.get("value_size", 10.0),
            heading_size=mc.get("heading_size", 14.0),
            line_color=mc.get("line_color", "#006FAB"),
            line_width=mc.get("line_width", 0.5),
        )
        assert config.label_size == 10.0
        assert config.line_color == "#006FAB"


# ===================================================================
# create_block() met tenant parameter
# ===================================================================


class TestCreateBlockWithTenant:
    """Test dat create_block() tenant modules vindt via ModuleRegistry."""

    def test_bic_table_via_create_block(self) -> None:
        """create_block met type=bic_table en tenant=symitech werkt."""
        block = create_block(BIC_TABLE_DATA, tenant="symitech")
        assert isinstance(block, BicTableModule)
        assert isinstance(block, Flowable)

    def test_location_detail_via_create_block(self) -> None:
        """create_block met type=location_detail en tenant=symitech werkt."""
        block = create_block(LOCATION_DETAIL_DATA, tenant="symitech")
        assert isinstance(block, LocationDetailModule)

    def test_cost_summary_via_create_block(self) -> None:
        """create_block met type=cost_summary en tenant=symitech werkt."""
        block = create_block(COST_SUMMARY_DATA, tenant="symitech")
        assert isinstance(block, Flowable)

    def test_object_description_via_create_block(self) -> None:
        """create_block met type=object_description en tenant=symitech werkt."""
        block = create_block(OBJECT_DESCRIPTION_DATA, tenant="symitech")
        assert isinstance(block, Flowable)

    def test_core_blocks_still_work(self) -> None:
        """Core block types werken nog steeds (regressie)."""
        para = create_block({"type": "paragraph", "text": "Test tekst"})
        assert isinstance(para, Flowable)

        spacer = create_block({"type": "spacer", "height_mm": 10})
        assert isinstance(spacer, Flowable)

    def test_unknown_type_raises(self) -> None:
        """Onbekend type geeft ValueError, ook met tenant."""
        with pytest.raises(ValueError, match="Onbekend content block type"):
            create_block({"type": "nonexistent"}, tenant="symitech")

    def test_without_tenant_unknown_module_raises(self) -> None:
        """Zonder tenant parameter zijn tenant modules onbekend."""
        with pytest.raises(ValueError, match="Onbekend content block type"):
            create_block({"type": "bic_table"})


# ===================================================================
# Volledige PDF rendering
# ===================================================================


class TestSymitechPdfRendering:
    """Test dat alle Symitech modules samen renderen naar een geldige PDF."""

    def test_multi_module_pdf(self) -> None:
        """Render alle 4 modules samen naar een multi-page PDF."""
        modules = [
            create_block(LOCATION_DETAIL_DATA, tenant="symitech"),
            create_block(BIC_TABLE_DATA, tenant="symitech"),
            create_block(COST_SUMMARY_DATA, tenant="symitech"),
            create_block(OBJECT_DESCRIPTION_DATA, tenant="symitech"),
        ]

        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)

        for module in modules:
            w, h = module.wrap(441.3, 700)
            module.canv = c
            c.translate(70, A4[1] - 100 - h)
            module.draw()
            c.showPage()

        c.save()
        pdf_bytes = buf.getvalue()

        # Verifieer geldige PDF
        assert pdf_bytes[:4] == b"%PDF"
        assert len(pdf_bytes) > 2000

    def test_pdf_to_file(self, tmp_path: Path) -> None:
        """Render naar een echt bestand en verifieer het bestaat."""
        output = tmp_path / "symitech_test.pdf"
        modules = [
            create_block(LOCATION_DETAIL_DATA, tenant="symitech"),
            create_block(BIC_TABLE_DATA, tenant="symitech"),
        ]

        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        for module in modules:
            w, h = module.wrap(441.3, 700)
            module.canv = c
            c.translate(70, A4[1] - 100 - h)
            module.draw()
            c.showPage()
        c.save()

        output.write_bytes(buf.getvalue())
        assert output.exists()
        assert output.stat().st_size > 1000

    def test_platypus_integration(self, tmp_path: Path) -> None:
        """Test dat modules werken binnen ReportLab Platypus flow."""
        output = tmp_path / "symitech_platypus.pdf"
        doc = SimpleDocTemplate(str(output), pagesize=A4)

        elements: list[Flowable] = [
            create_block(LOCATION_DETAIL_DATA, tenant="symitech"),
            Spacer(1, 20),
            create_block(OBJECT_DESCRIPTION_DATA, tenant="symitech"),
        ]

        doc.build(elements)

        assert output.exists()
        assert output.stat().st_size > 1000

        with output.open("rb") as f:
            assert f.read(4) == b"%PDF"
