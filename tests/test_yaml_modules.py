"""Tests voor YAML-driven content modules.

Vergelijkt de YAML-versies van de Symitech modules met de originele
Python modules qua:
- Instantiatie en height berekening
- Rendering zonder crashes
- Hoogtevergelijking met de originele modules
- YAML loading vanuit directory
- Factory functie
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
import yaml
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from openaec_reports.modules.base import ContentModule

# Originele Python modules (voor vergelijking)
from openaec_reports.modules.symitech.bic_table import BicTableModule
from openaec_reports.modules.symitech.cost_summary import CostSummaryModule
from openaec_reports.modules.symitech.location_detail import LocationDetailModule
from openaec_reports.modules.symitech.object_description import ObjectDescriptionModule
from openaec_reports.modules.yaml_module import (
    YamlModule,
    create_yaml_module_class,
    load_yaml_modules_from_dir,
)

# ---------------------------------------------------------------------------
# Constants en helpers
# ---------------------------------------------------------------------------

DEFAULT_WIDTH = 441.3
YAML_DEFS_DIR = (
    Path(__file__).parent.parent / "tenants" / "symitech" / "modules"
)


def render_module_to_pdf(module: ContentModule) -> bytes:
    """Render een module naar een in-memory test PDF."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = module.wrap(DEFAULT_WIDTH, 700)
    module.canv = c
    c.translate(70, A4[1] - 100 - h)
    module.draw()
    c.showPage()
    c.save()
    return buf.getvalue()


def load_yaml_config(name: str) -> dict:
    """Laad een YAML module config uit de yaml_defs directory."""
    path = YAML_DEFS_DIR / f"{name}.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Fixtures — voorbeeld data (zelfde als test_symitech_modules.py)
# ---------------------------------------------------------------------------

@pytest.fixture()
def bic_table_data() -> dict:
    """Volledig voorbeeld voor bic_table."""
    return {
        "type": "bic_table",
        "location_name": "Amsterdam Noord",
        "sections": [
            {
                "title": "BIC Controles",
                "rows": [
                    {"label": "Aantal BIC controles", "ref_value": "12", "actual_value": "14"},
                    {
                        "label": "Kosten",
                        "ref_value": "\u20ac 3.400,00",
                        "actual_value": "\u20ac 3.966,67",
                    },
                ],
            },
            {
                "title": "Reinigen tijdens BIC",
                "rows": [
                    {"label": "Aantal reinigingen", "ref_value": "3", "actual_value": "4"},
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
                    "label": "Reinigen",
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
    """Volledig voorbeeld voor cost_summary."""
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
            {"description": "Reinigingen", "quantity": 3, "unit_price": 300.00, "total": 900.00},
        ],
        "total": 4550.00,
    }


@pytest.fixture()
def location_detail_data() -> dict:
    """Volledig voorbeeld voor location_detail."""
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
    """Volledig voorbeeld voor object_description."""
    return {
        "type": "object_description",
        "title": "Objectbeschrijving",
        "object_name": "Peilbuis PB-01",
        "fields": [
            {"label": "Type", "value": "Grondwaterpeilbuis"},
            {"label": "Diameter", "value": "50 mm"},
            {"label": "Diepte", "value": "12,5 m-mv"},
        ],
        "notes": "Geplaatst in 2019, jaarlijkse controle.",
        "photo_path": None,
    }


# ===================================================================
# Factory tests
# ===================================================================

class TestCreateYamlModuleClass:
    """Tests voor create_yaml_module_class factory."""

    def test_creates_class(self) -> None:
        """Factory retourneert een type (class)."""
        config = {"name": "test_module", "elements": []}
        cls = create_yaml_module_class(config)
        assert isinstance(cls, type)
        assert issubclass(cls, YamlModule)
        assert issubclass(cls, ContentModule)

    def test_class_name(self) -> None:
        """Class naam wordt afgeleid van module naam."""
        config = {"name": "bic_table", "elements": []}
        cls = create_yaml_module_class(config)
        assert cls.__name__ == "BicTableYamlModule"

    def test_layout_bound(self) -> None:
        """Layout config is gebonden aan de class."""
        config = {"name": "test", "elements": [{"type": "title", "default": "Test"}]}
        cls = create_yaml_module_class(config)
        assert cls._layout is config

    def test_different_classes_independent(self) -> None:
        """Twee classes met dezelfde factory zijn onafhankelijk."""
        config_a = {"name": "a", "elements": []}
        config_b = {"name": "b", "elements": []}
        cls_a = create_yaml_module_class(config_a)
        cls_b = create_yaml_module_class(config_b)
        assert cls_a is not cls_b
        assert cls_a._layout is not cls_b._layout


# ===================================================================
# YAML loading tests
# ===================================================================

class TestLoadYamlModules:
    """Tests voor load_yaml_modules_from_dir."""

    def test_load_from_symitech_dir(self) -> None:
        """Alle 4 YAML definities worden geladen."""
        modules = load_yaml_modules_from_dir(YAML_DEFS_DIR)
        assert "location_detail" in modules
        assert "bic_table" in modules
        assert "cost_summary" in modules
        assert "object_description" in modules

    def test_loaded_classes_are_yaml_modules(self) -> None:
        """Geladen classes zijn YamlModule subclasses."""
        modules = load_yaml_modules_from_dir(YAML_DEFS_DIR)
        for name, cls in modules.items():
            assert issubclass(cls, YamlModule), f"{name} is geen YamlModule"
            assert issubclass(cls, ContentModule), f"{name} is geen ContentModule"

    def test_nonexistent_dir(self) -> None:
        """Niet-bestaande directory retourneert leeg dict."""
        modules = load_yaml_modules_from_dir(Path("/nonexistent"))
        assert modules == {}


# ===================================================================
# YAML location_detail tests
# ===================================================================

class TestYamlLocationDetail:
    """Tests voor YAML-versie van location_detail."""

    @pytest.fixture()
    def yaml_cls(self) -> type[YamlModule]:
        config = load_yaml_config("location_detail")
        return create_yaml_module_class(config)

    def test_instantiate(self, yaml_cls: type, location_detail_data: dict) -> None:
        """YAML module kan geinstantieerd worden."""
        module = yaml_cls(location_detail_data)
        assert isinstance(module, ContentModule)

    def test_height_positive(self, yaml_cls: type, location_detail_data: dict) -> None:
        """Height is positief."""
        module = yaml_cls(location_detail_data)
        assert module.height > 0

    def test_draw_no_crash(self, yaml_cls: type, location_detail_data: dict) -> None:
        """Draw crasht niet."""
        module = yaml_cls(location_detail_data)
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0

    def test_height_close_to_python(
        self, yaml_cls: type, location_detail_data: dict,
    ) -> None:
        """YAML hoogte komt overeen met Python module hoogte."""
        yaml_module = yaml_cls(location_detail_data)
        python_module = LocationDetailModule(location_detail_data)
        # Tolerantie: YAML kan licht afwijken door andere section_header spacing
        assert abs(yaml_module.height - python_module.height) < 20.0, (
            f"YAML={yaml_module.height:.1f}, Python={python_module.height:.1f}"
        )

    def test_empty_data(self, yaml_cls: type) -> None:
        """Lege data leidt niet tot crash."""
        module = yaml_cls({})
        assert module.height > 0
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0

    def test_only_client(self, yaml_cls: type) -> None:
        """Werkt met alleen client sectie."""
        data = {
            "title": "Locatie",
            "client": {"section_title": "Opdrachtgever", "name": "Test BV"},
        }
        module = yaml_cls(data)
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0


# ===================================================================
# YAML bic_table tests
# ===================================================================

class TestYamlBicTable:
    """Tests voor YAML-versie van bic_table."""

    @pytest.fixture()
    def yaml_cls(self) -> type[YamlModule]:
        config = load_yaml_config("bic_table")
        return create_yaml_module_class(config)

    def test_instantiate(self, yaml_cls: type, bic_table_data: dict) -> None:
        """YAML module kan geinstantieerd worden."""
        module = yaml_cls(bic_table_data)
        assert isinstance(module, ContentModule)

    def test_height_positive(self, yaml_cls: type, bic_table_data: dict) -> None:
        """Height is positief."""
        module = yaml_cls(bic_table_data)
        assert module.height > 0

    def test_draw_no_crash(self, yaml_cls: type, bic_table_data: dict) -> None:
        """Draw crasht niet."""
        module = yaml_cls(bic_table_data)
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0

    def test_height_close_to_python(
        self, yaml_cls: type, bic_table_data: dict,
    ) -> None:
        """YAML hoogte komt overeen met Python module hoogte."""
        yaml_module = yaml_cls(bic_table_data)
        python_module = BicTableModule(bic_table_data)
        assert abs(yaml_module.height - python_module.height) < 20.0, (
            f"YAML={yaml_module.height:.1f}, Python={python_module.height:.1f}"
        )

    def test_empty_data(self, yaml_cls: type) -> None:
        """Lege data leidt niet tot crash."""
        module = yaml_cls({})
        assert module.height > 0
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0

    def test_no_summary(self, yaml_cls: type) -> None:
        """Werkt zonder summary sectie."""
        data = {
            "location_name": "Test",
            "sections": [
                {"title": "Test", "rows": [{"label": "A", "ref_value": "1", "actual_value": "2"}]},
            ],
        }
        module = yaml_cls(data)
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0


# ===================================================================
# YAML cost_summary tests
# ===================================================================

class TestYamlCostSummary:
    """Tests voor YAML-versie van cost_summary."""

    @pytest.fixture()
    def yaml_cls(self) -> type[YamlModule]:
        config = load_yaml_config("cost_summary")
        return create_yaml_module_class(config)

    def test_instantiate(self, yaml_cls: type, cost_summary_data: dict) -> None:
        """YAML module kan geinstantieerd worden."""
        module = yaml_cls(cost_summary_data)
        assert isinstance(module, ContentModule)

    def test_height_positive(self, yaml_cls: type, cost_summary_data: dict) -> None:
        """Height is positief."""
        module = yaml_cls(cost_summary_data)
        assert module.height > 0

    def test_draw_no_crash(self, yaml_cls: type, cost_summary_data: dict) -> None:
        """Draw crasht niet."""
        module = yaml_cls(cost_summary_data)
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0

    def test_height_close_to_python(
        self, yaml_cls: type, cost_summary_data: dict,
    ) -> None:
        """YAML hoogte komt overeen met Python module hoogte."""
        yaml_module = yaml_cls(cost_summary_data)
        python_module = CostSummaryModule(cost_summary_data)
        assert abs(yaml_module.height - python_module.height) < 20.0, (
            f"YAML={yaml_module.height:.1f}, Python={python_module.height:.1f}"
        )

    def test_currency_formatting(self, yaml_cls: type) -> None:
        """Nederlands valutaformaat werkt in YAML module."""
        assert YamlModule._format_value(1234.56, "currency_nl") == "\u20ac 1.234,56"
        assert YamlModule._format_value(0.0, "currency_nl") == "\u20ac 0,00"
        assert YamlModule._format_value(None, "currency_nl") == ""

    def test_empty_data(self, yaml_cls: type) -> None:
        """Lege data leidt niet tot crash."""
        module = yaml_cls({})
        assert module.height > 0
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0


# ===================================================================
# YAML object_description tests
# ===================================================================

class TestYamlObjectDescription:
    """Tests voor YAML-versie van object_description."""

    @pytest.fixture()
    def yaml_cls(self) -> type[YamlModule]:
        config = load_yaml_config("object_description")
        return create_yaml_module_class(config)

    def test_instantiate(self, yaml_cls: type, object_description_data: dict) -> None:
        """YAML module kan geinstantieerd worden."""
        module = yaml_cls(object_description_data)
        assert isinstance(module, ContentModule)

    def test_height_positive(self, yaml_cls: type, object_description_data: dict) -> None:
        """Height is positief."""
        module = yaml_cls(object_description_data)
        assert module.height > 0

    def test_draw_no_crash(self, yaml_cls: type, object_description_data: dict) -> None:
        """Draw crasht niet."""
        module = yaml_cls(object_description_data)
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0

    def test_height_close_to_python(
        self, yaml_cls: type, object_description_data: dict,
    ) -> None:
        """YAML hoogte komt overeen met Python module hoogte."""
        yaml_module = yaml_cls(object_description_data)
        python_module = ObjectDescriptionModule(object_description_data)
        assert abs(yaml_module.height - python_module.height) < 20.0, (
            f"YAML={yaml_module.height:.1f}, Python={python_module.height:.1f}"
        )

    def test_empty_data(self, yaml_cls: type) -> None:
        """Lege data leidt niet tot crash."""
        module = yaml_cls({})
        assert module.height > 0
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0

    def test_field_list_dynamic(self, yaml_cls: type) -> None:
        """Dynamische field list werkt met willekeurige velden."""
        data = {
            "title": "Object",
            "object_name": "Test",
            "fields": [
                {"label": "A", "value": "1"},
                {"label": "B", "value": "2"},
                {"label": "C", "value": "3"},
            ],
        }
        module = yaml_cls(data)
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0

    def test_notes_wrapping(self, yaml_cls: type) -> None:
        """Lange notities worden gewrapped."""
        data = {
            "object_name": "Test",
            "fields": [],
            "notes": "Korte tekst " * 20,
        }
        module = yaml_cls(data)
        assert module.height > 0
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0


# ===================================================================
# Element-specifieke tests
# ===================================================================

class TestYamlElements:
    """Tests voor individuele YAML element types."""

    def _make_module(self, elements: list[dict], data: dict) -> YamlModule:
        """Maak een YamlModule met custom elements."""
        config = {"name": "test", "elements": elements, "style": {}}
        cls = create_yaml_module_class(config)
        return cls(data)

    def test_title_element(self) -> None:
        """Title element werkt."""
        module = self._make_module(
            [{"type": "title", "field": "title", "default": "Fallback"}],
            {"title": "Mijn Titel"},
        )
        assert module.height > 0
        render_module_to_pdf(module)

    def test_title_with_separator(self) -> None:
        """Title met double_line separator."""
        module = self._make_module(
            [{"type": "title", "default": "Test", "separator": "double_line"}],
            {},
        )
        render_module_to_pdf(module)

    def test_subtitle_shown_when_data(self) -> None:
        """Subtitle wordt getoond als data aanwezig is."""
        module = self._make_module(
            [{"type": "subtitle", "field": "name"}],
            {"name": "Test Object"},
        )
        assert module.height > 20.0

    def test_subtitle_hidden_when_empty(self) -> None:
        """Subtitle wordt verborgen als data leeg is."""
        module = self._make_module(
            [{"type": "subtitle", "field": "name"}],
            {},
        )
        # Alleen bottom_padding
        assert module.height < 15.0

    def test_right_header(self) -> None:
        """Right header element werkt."""
        module = self._make_module(
            [{"type": "right_header", "field": "location"}],
            {"location": "Amsterdam"},
        )
        assert module.height > 0
        render_module_to_pdf(module)

    def test_field_list_element(self) -> None:
        """field_list element rendert key-value paren."""
        module = self._make_module(
            [{"type": "field_list", "data_key": "fields"}],
            {"fields": [{"label": "A", "value": "1"}, {"label": "B", "value": "2"}]},
        )
        assert module.height > 40.0
        render_module_to_pdf(module)

    def test_field_list_empty(self) -> None:
        """Leeg field_list geeft geen hoogte."""
        module = self._make_module(
            [{"type": "field_list", "data_key": "fields"}],
            {"fields": []},
        )
        # Alleen bottom_padding
        assert module.height < 15.0

    def test_data_rows_element(self) -> None:
        """data_rows element werkt."""
        module = self._make_module(
            [{
                "type": "data_rows",
                "data_key": "rows",
                "columns": [
                    {"key": "name", "x_frac": 0.0, "offset": 4},
                    {"key": "amount", "x_frac": 1.0, "align": "right", "format": "currency_nl"},
                ],
            }],
            {"rows": [
                {"name": "Item 1", "amount": 100.0},
                {"name": "Item 2", "amount": 200.0},
            ]},
        )
        assert module.height > 30.0
        render_module_to_pdf(module)

    def test_total_row_element(self) -> None:
        """total_row element werkt."""
        module = self._make_module(
            [{
                "type": "total_row",
                "data_key": "total",
                "label": "Totaal",
                "format": "currency_nl",
            }],
            {"total": 4550.00},
        )
        assert module.height > 20.0
        render_module_to_pdf(module)

    def test_total_row_absent(self) -> None:
        """total_row zonder data geeft geen hoogte."""
        module = self._make_module(
            [{"type": "total_row", "data_key": "total"}],
            {},
        )
        assert module.height < 15.0

    def test_photo_placeholder(self) -> None:
        """Photo zonder geldig pad toont placeholder."""
        module = self._make_module(
            [{"type": "photo", "field": "photo", "placeholder_text": "[TEST]"}],
            {"photo": None},
        )
        assert module.height > 60.0
        render_module_to_pdf(module)

    def test_notes_element(self) -> None:
        """Notes element rendert tekst."""
        module = self._make_module(
            [{"type": "notes", "field": "notes"}],
            {"notes": "Dit is een notitie."},
        )
        assert module.height > 20.0
        render_module_to_pdf(module)

    def test_notes_empty(self) -> None:
        """Lege notes geeft geen hoogte."""
        module = self._make_module(
            [{"type": "notes", "field": "notes"}],
            {},
        )
        assert module.height < 15.0

    def test_unknown_element_skipped(self) -> None:
        """Onbekend element type wordt overgeslagen."""
        module = self._make_module(
            [{"type": "nonexistent_element"}],
            {},
        )
        render_module_to_pdf(module)


# ===================================================================
# Symitech registratie met YAML modules
# ===================================================================

class TestSymitechYamlRegistration:
    """Tests voor YAML module registratie in Symitech."""

    def test_register_yaml_only(self) -> None:
        """register_symitech_yaml_modules registreert YAML versies."""
        from openaec_reports.modules import ModuleRegistry
        from openaec_reports.modules.symitech import register_symitech_yaml_modules

        ModuleRegistry.reset()
        register_symitech_yaml_modules(modules_dir=YAML_DEFS_DIR)

        # Alle 4 modules moeten beschikbaar zijn
        for name in ["bic_table", "cost_summary", "location_detail", "object_description"]:
            cls = ModuleRegistry.get(name, tenant="symitech")
            assert issubclass(cls, YamlModule), f"{name} is geen YamlModule"

    def test_python_modules_have_priority(self) -> None:
        """Bij register_symitech_modules() hebben Python modules prioriteit."""
        from openaec_reports.modules import ModuleRegistry
        from openaec_reports.modules.symitech import register_symitech_modules

        ModuleRegistry.reset()
        register_symitech_modules(modules_dir=YAML_DEFS_DIR)

        # Python modules moeten de originele classes zijn
        assert ModuleRegistry.get("bic_table", tenant="symitech") is BicTableModule
        assert ModuleRegistry.get("location_detail", tenant="symitech") is LocationDetailModule
