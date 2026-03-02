"""Tests voor Symitech content modules.

Test elke module op:
- Instantiatie met voorbeeld-data
- _calculate_height() retourneert positief getal
- wrap() retourneert (width, height) tuple
- draw() crasht niet (render naar test canvas)
- Lege data handelt graceful af
"""

from __future__ import annotations

from io import BytesIO

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from openaec_reports.modules.base import ContentModule, ModuleConfig
from openaec_reports.modules.symitech.bic_table import BicTableModule
from openaec_reports.modules.symitech.cost_summary import (
    CostSummaryModule,
    _format_currency_nl,
)
from openaec_reports.modules.symitech.location_detail import LocationDetailModule
from openaec_reports.modules.symitech.object_description import ObjectDescriptionModule

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

DEFAULT_WIDTH = 441.3


def render_module_to_pdf(module: ContentModule) -> bytes:
    """Render een module naar een in-memory test PDF.

    Args:
        module: De ContentModule om te renderen.

    Returns:
        PDF content als bytes.
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = module.wrap(DEFAULT_WIDTH, 700)
    module.canv = c
    c.translate(70, A4[1] - 100 - h)
    module.draw()
    c.showPage()
    c.save()
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Voorbeeld data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def bic_table_data() -> dict:
    """Volledig voorbeeld voor BicTableModule."""
    return {
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
                        "is_currency": True,
                    },
                ],
            },
            {
                "title": "Reinigen tijdens BIC",
                "rows": [
                    {
                        "label": "Aantal reinigingen",
                        "ref_value": "3",
                        "actual_value": "4",
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
                {
                    "label": "Reinigen tijdens BIC",
                    "ref_value": "\u20ac 900,00",
                    "actual_value": "\u20ac 1.200,00",
                },
            ],
            "total": {
                "label": "Totaal",
                "ref_value": "\u20ac 4.300,00",
                "actual_value": "\u20ac 5.166,67",
            },
        },
    }


@pytest.fixture()
def cost_summary_data() -> dict:
    """Volledig voorbeeld voor CostSummaryModule."""
    return {
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
            {
                "description": "Reinigingen",
                "quantity": 3,
                "unit_price": 300.00,
                "total": 900.00,
            },
        ],
        "total": 4550.00,
    }


@pytest.fixture()
def location_detail_data() -> dict:
    """Volledig voorbeeld voor LocationDetailModule."""
    return {
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


@pytest.fixture()
def object_description_data() -> dict:
    """Volledig voorbeeld voor ObjectDescriptionModule."""
    return {
        "type": "object_description",
        "title": "Objectbeschrijving",
        "object_name": "Peilbuis PB-01",
        "fields": [
            {"label": "Type", "value": "Grondwaterpeilbuis"},
            {"label": "Diameter", "value": "50 mm"},
            {"label": "Diepte", "value": "12,5 m-mv"},
            {"label": "Filterdiepte", "value": "10,0 - 12,0 m-mv"},
            {"label": "Materiaal", "value": "PVC"},
            {"label": "Status", "value": "Actief"},
        ],
        "notes": "Geplaatst in 2019, jaarlijkse controle.",
        "photo_path": None,
    }


# ===================================================================
# BicTableModule tests
# ===================================================================

class TestBicTableModule:
    """Tests voor BicTableModule."""

    def test_instantiate(self, bic_table_data: dict) -> None:
        """Module kan geinstantieerd worden met voorbeeld-data."""
        module = BicTableModule(bic_table_data)
        assert isinstance(module, ContentModule)

    def test_height_positive(self, bic_table_data: dict) -> None:
        """_calculate_height retourneert een positief getal."""
        module = BicTableModule(bic_table_data)
        assert module.height > 0

    def test_wrap_returns_tuple(self, bic_table_data: dict) -> None:
        """wrap() retourneert (width, height) tuple."""
        module = BicTableModule(bic_table_data)
        result = module.wrap(DEFAULT_WIDTH, 700)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == DEFAULT_WIDTH
        assert result[1] > 0

    def test_draw_no_crash(self, bic_table_data: dict) -> None:
        """draw() crasht niet bij rendering naar PDF."""
        module = BicTableModule(bic_table_data)
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0

    def test_empty_data(self) -> None:
        """Lege data leidt niet tot crash."""
        module = BicTableModule({})
        assert module.height > 0
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0

    def test_no_summary(self) -> None:
        """Module werkt zonder summary sectie."""
        data = {
            "location_name": "Test",
            "sections": [
                {"title": "Test", "rows": [{"label": "A", "ref_value": "1", "actual_value": "2"}]},
            ],
        }
        module = BicTableModule(data)
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0

    def test_custom_config(self, bic_table_data: dict) -> None:
        """Module accepteert custom ModuleConfig."""
        config = ModuleConfig(
            heading_size=16.0,
            label_size=11.0,
        )
        module = BicTableModule(bic_table_data, config=config)
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0


# ===================================================================
# CostSummaryModule tests
# ===================================================================

class TestCostSummaryModule:
    """Tests voor CostSummaryModule."""

    def test_instantiate(self, cost_summary_data: dict) -> None:
        """Module kan geinstantieerd worden met voorbeeld-data."""
        module = CostSummaryModule(cost_summary_data)
        assert isinstance(module, ContentModule)

    def test_height_positive(self, cost_summary_data: dict) -> None:
        """_calculate_height retourneert een positief getal."""
        module = CostSummaryModule(cost_summary_data)
        assert module.height > 0

    def test_wrap_returns_tuple(self, cost_summary_data: dict) -> None:
        """wrap() retourneert (width, height) tuple."""
        module = CostSummaryModule(cost_summary_data)
        result = module.wrap(DEFAULT_WIDTH, 700)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_draw_no_crash(self, cost_summary_data: dict) -> None:
        """draw() crasht niet bij rendering naar PDF."""
        module = CostSummaryModule(cost_summary_data)
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0

    def test_empty_data(self) -> None:
        """Lege data leidt niet tot crash."""
        module = CostSummaryModule({})
        assert module.height > 0
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0

    def test_no_total(self) -> None:
        """Module werkt zonder totaalregel."""
        data = {
            "title": "Test",
            "rows": [{"description": "Item", "quantity": 1, "unit_price": 100.0, "total": 100.0}],
        }
        module = CostSummaryModule(data)
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0

    def test_currency_formatting(self) -> None:
        """Nederlands valutaformaat werkt correct."""
        assert _format_currency_nl(1234.56) == "\u20ac 1.234,56"
        assert _format_currency_nl(0.0) == "\u20ac 0,00"
        assert _format_currency_nl(1000000.01) == "\u20ac 1.000.000,01"
        assert _format_currency_nl(99.90) == "\u20ac 99,90"


# ===================================================================
# LocationDetailModule tests
# ===================================================================

class TestLocationDetailModule:
    """Tests voor LocationDetailModule."""

    def test_instantiate(self, location_detail_data: dict) -> None:
        """Module kan geinstantieerd worden met voorbeeld-data."""
        module = LocationDetailModule(location_detail_data)
        assert isinstance(module, ContentModule)

    def test_height_positive(self, location_detail_data: dict) -> None:
        """_calculate_height retourneert een positief getal."""
        module = LocationDetailModule(location_detail_data)
        assert module.height > 0

    def test_wrap_returns_tuple(self, location_detail_data: dict) -> None:
        """wrap() retourneert (width, height) tuple."""
        module = LocationDetailModule(location_detail_data)
        result = module.wrap(DEFAULT_WIDTH, 700)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_draw_no_crash(self, location_detail_data: dict) -> None:
        """draw() crasht niet bij rendering naar PDF."""
        module = LocationDetailModule(location_detail_data)
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0

    def test_empty_data(self) -> None:
        """Lege data leidt niet tot crash."""
        module = LocationDetailModule({})
        assert module.height > 0
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0

    def test_only_client(self) -> None:
        """Module werkt met alleen client sectie."""
        data = {
            "title": "Locatie",
            "client": {
                "section_title": "Opdrachtgever",
                "name": "Test BV",
            },
        }
        module = LocationDetailModule(data)
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0

    def test_only_location(self) -> None:
        """Module werkt met alleen location sectie."""
        data = {
            "title": "Locatie",
            "location": {
                "section_title": "Locatie van uitvoer",
                "name": "Test Depot",
                "code": "LOC-001",
            },
        }
        module = LocationDetailModule(data)
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0


# ===================================================================
# ObjectDescriptionModule tests
# ===================================================================

class TestObjectDescriptionModule:
    """Tests voor ObjectDescriptionModule."""

    def test_instantiate(self, object_description_data: dict) -> None:
        """Module kan geinstantieerd worden met voorbeeld-data."""
        module = ObjectDescriptionModule(object_description_data)
        assert isinstance(module, ContentModule)

    def test_height_positive(self, object_description_data: dict) -> None:
        """_calculate_height retourneert een positief getal."""
        module = ObjectDescriptionModule(object_description_data)
        assert module.height > 0

    def test_wrap_returns_tuple(self, object_description_data: dict) -> None:
        """wrap() retourneert (width, height) tuple."""
        module = ObjectDescriptionModule(object_description_data)
        result = module.wrap(DEFAULT_WIDTH, 700)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_draw_no_crash(self, object_description_data: dict) -> None:
        """draw() crasht niet bij rendering naar PDF."""
        module = ObjectDescriptionModule(object_description_data)
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0

    def test_empty_data(self) -> None:
        """Lege data leidt niet tot crash."""
        module = ObjectDescriptionModule({})
        assert module.height > 0
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0

    def test_no_notes(self) -> None:
        """Module werkt zonder notities."""
        data = {
            "title": "Object",
            "object_name": "Test PB-01",
            "fields": [{"label": "Type", "value": "Peilbuis"}],
        }
        module = ObjectDescriptionModule(data)
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0

    def test_long_notes_wrapping(self) -> None:
        """Lange notities worden correct gewrapped."""
        data = {
            "object_name": "Test",
            "fields": [],
            "notes": "Dit is een hele lange notitie die over meerdere regels "
                     "zou moeten worden gewrapped zodat de tekst netjes "
                     "binnen de beschikbare breedte past. " * 3,
        }
        module = ObjectDescriptionModule(data)
        assert module.height > 0
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0

    def test_text_wrapping_utility(self) -> None:
        """_wrap_text splitst correct op woordgrenzen."""
        short = "Korte tekst"
        assert ObjectDescriptionModule._wrap_text(short) == ["Korte tekst"]

        long_text = "woord " * 20
        lines = ObjectDescriptionModule._wrap_text(long_text.strip(), max_chars=40)
        assert len(lines) > 1
        for line in lines:
            assert len(line) <= 45  # kleine marge voor laatste woord

    def test_empty_text_wrapping(self) -> None:
        """_wrap_text handelt lege string af."""
        assert ObjectDescriptionModule._wrap_text("") == [""]


# ===================================================================
# ModuleRegistry registratie tests
# ===================================================================

class TestSymitechRegistration:
    """Tests voor Symitech module registratie."""

    def test_register_all_modules(self) -> None:
        """register_symitech_modules registreert alle 4 modules."""
        from openaec_reports.modules import ModuleRegistry
        from openaec_reports.modules.symitech import register_symitech_modules

        register_symitech_modules()

        assert ModuleRegistry.get("bic_table", tenant="symitech") is BicTableModule
        assert ModuleRegistry.get("cost_summary", tenant="symitech") is CostSummaryModule
        assert ModuleRegistry.get("location_detail", tenant="symitech") is LocationDetailModule
        result = ModuleRegistry.get("object_description", tenant="symitech")
        assert result is ObjectDescriptionModule

    def test_list_symitech_modules(self) -> None:
        """Symitech modules zijn vindbaar via list_modules."""
        from openaec_reports.modules import ModuleRegistry
        from openaec_reports.modules.symitech import register_symitech_modules

        register_symitech_modules()
        modules = ModuleRegistry.available(tenant="symitech")

        assert "bic_table" in modules
        assert "cost_summary" in modules
        assert "location_detail" in modules
        assert "object_description" in modules
