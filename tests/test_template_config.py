"""Tests voor template_config.py — dataclasses + parse helpers."""

from __future__ import annotations

import pytest

from openaec_reports.core.template_config import (
    ContentFrame,
    PageDef,
    PageType,
    TableColumn,
    TableConfig,
    TemplateConfig,
    TextZone,
    parse_content_frame,
    parse_page_def,
    parse_page_type,
    parse_table_column,
    parse_table_config,
    parse_template_config,
    parse_text_zone,
)

# ============================================================
# TextZone
# ============================================================


class TestParseTextZone:
    def test_full_fields(self) -> None:
        data = {
            "bind": "client.name",
            "x_mm": 20,
            "y_mm": 99,
            "font": "heading",
            "size": 14,
            "color": "primary",
            "align": "right",
        }
        tz = parse_text_zone(data)
        assert isinstance(tz, TextZone)
        assert tz.bind == "client.name"
        assert tz.x_mm == 20.0
        assert tz.y_mm == 99.0
        assert tz.font == "heading"
        assert tz.size == 14.0
        assert tz.color == "primary"
        assert tz.align == "right"

    def test_minimal_input(self) -> None:
        """Alleen verplicht veld 'bind' → rest defaults."""
        tz = parse_text_zone({"bind": "meta.datum"})
        assert tz.bind == "meta.datum"
        assert tz.x_mm == 0.0
        assert tz.y_mm == 0.0
        assert tz.font == "body"
        assert tz.size == 10.0
        assert tz.color == "text"
        assert tz.align == "left"

    def test_missing_bind_raises(self) -> None:
        with pytest.raises(KeyError):
            parse_text_zone({})


# ============================================================
# TableColumn
# ============================================================


class TestParseTableColumn:
    def test_full_fields(self) -> None:
        data = {
            "field": "label",
            "width_mm": 85,
            "align": "right",
            "format": "currency_nl",
            "font": "heading",
            "size": 12,
            "color": "primary",
        }
        col = parse_table_column(data)
        assert isinstance(col, TableColumn)
        assert col.field == "label"
        assert col.width_mm == 85.0
        assert col.align == "right"
        assert col.format == "currency_nl"
        assert col.font == "heading"
        assert col.size == 12.0
        assert col.color == "primary"

    def test_minimal_input(self) -> None:
        col = parse_table_column({"field": "cost"})
        assert col.field == "cost"
        assert col.width_mm == 40.0
        assert col.align == "left"
        assert col.format is None
        assert col.font == "body"
        assert col.size == 9.0
        assert col.color == "text"
        assert col.header is None

    def test_header_field(self) -> None:
        """Column with explicit header display name."""
        col = parse_table_column({"field": "ref_value", "header": "Conform opdracht"})
        assert col.field == "ref_value"
        assert col.header == "Conform opdracht"

    def test_missing_field_raises(self) -> None:
        with pytest.raises(KeyError):
            parse_table_column({})


# ============================================================
# TableConfig
# ============================================================


class TestParseTableConfig:
    def test_full_config(self) -> None:
        data = {
            "data_bind": "bic_sections",
            "origin": {"x_mm": 25, "y_mm": 80},
            "row_height_mm": 6.0,
            "max_y_mm": 250,
            "header_font": "body",
            "header_size": 10,
            "header_color": "primary",
            "show_header": True,
            "columns": [
                {"field": "label", "width_mm": 85},
                {"field": "value", "width_mm": 42, "align": "right"},
            ],
        }
        tc = parse_table_config(data)
        assert isinstance(tc, TableConfig)
        assert tc.data_bind == "bic_sections"
        assert tc.origin_x_mm == 25.0
        assert tc.origin_y_mm == 80.0
        assert tc.row_height_mm == 6.0
        assert tc.max_y_mm == 250.0
        assert tc.header_font == "body"
        assert tc.header_size == 10.0
        assert tc.header_color == "primary"
        assert tc.show_header is True
        assert len(tc.columns) == 2
        assert tc.columns[0].field == "label"
        assert tc.columns[1].align == "right"

    def test_minimal_input(self) -> None:
        tc = parse_table_config({"data_bind": "items"})
        assert tc.data_bind == "items"
        assert tc.origin_x_mm == 20.0
        assert tc.origin_y_mm == 60.0
        assert tc.row_height_mm == 5.6
        assert tc.max_y_mm == 260.0
        assert tc.show_header is False
        assert tc.columns == []
        # New styling fields default to None
        assert tc.header_bg is None
        assert tc.body_font is None
        assert tc.body_size is None
        assert tc.body_color is None
        assert tc.alt_row_bg is None
        assert tc.grid_color is None

    def test_styling_fields(self) -> None:
        """TableConfig with all styling overrides."""
        data = {
            "data_bind": "items",
            "header_bg": "#006FAB",
            "body_font": "Helvetica",
            "body_size": 9.0,
            "body_color": "#333333",
            "alt_row_bg": "#F5F5F5",
            "grid_color": "#CCCCCC",
        }
        tc = parse_table_config(data)
        assert tc.header_bg == "#006FAB"
        assert tc.body_font == "Helvetica"
        assert tc.body_size == 9.0
        assert tc.body_color == "#333333"
        assert tc.alt_row_bg == "#F5F5F5"
        assert tc.grid_color == "#CCCCCC"

    def test_empty_columns_list(self) -> None:
        tc = parse_table_config({"data_bind": "x", "columns": []})
        assert tc.columns == []

    def test_missing_data_bind_raises(self) -> None:
        with pytest.raises(KeyError):
            parse_table_config({"columns": []})


# ============================================================
# ContentFrame
# ============================================================


class TestParseContentFrame:
    def test_full_fields(self) -> None:
        data = {"x_mm": 30, "y_mm": 40, "width_mm": 150, "height_mm": 200}
        cf = parse_content_frame(data)
        assert isinstance(cf, ContentFrame)
        assert cf.x_mm == 30.0
        assert cf.y_mm == 40.0
        assert cf.width_mm == 150.0
        assert cf.height_mm == 200.0

    def test_defaults(self) -> None:
        cf = parse_content_frame({})
        assert cf.x_mm == 20.0
        assert cf.y_mm == 25.0
        assert cf.width_mm == 175.0
        assert cf.height_mm == 247.0


# ============================================================
# PageType
# ============================================================


class TestParsePageType:
    def test_full_page_type(self) -> None:
        data = {
            "name": "voorblad_bic",
            "stationery": "cover.pdf",
            "text_zones": [
                {"bind": "meta.titel", "x_mm": 20, "y_mm": 99},
            ],
            "table": {
                "data_bind": "items",
                "columns": [{"field": "label"}],
            },
            "content_frame": {"x_mm": 10, "y_mm": 20, "width_mm": 180, "height_mm": 250},
        }
        pt = parse_page_type(data)
        assert isinstance(pt, PageType)
        assert pt.name == "voorblad_bic"
        assert pt.stationery == "cover.pdf"
        assert len(pt.text_zones) == 1
        assert pt.text_zones[0].bind == "meta.titel"
        assert pt.table is not None
        assert pt.table.data_bind == "items"
        assert pt.content_frame is not None
        assert pt.content_frame.x_mm == 10.0

    def test_minimal_page_type(self) -> None:
        """Zonder optionele velden → defaults."""
        pt = parse_page_type({})
        assert pt.name == "unknown"
        assert pt.stationery is None
        assert pt.text_zones == []
        assert pt.table is None
        assert pt.content_frame is None

    def test_only_stationery(self) -> None:
        """Achterblad: alleen stationery, geen content."""
        pt = parse_page_type({"name": "achterblad", "stationery": "back.pdf"})
        assert pt.name == "achterblad"
        assert pt.stationery == "back.pdf"
        assert pt.text_zones == []
        assert pt.table is None

    def test_empty_text_zones(self) -> None:
        pt = parse_page_type({"name": "test", "text_zones": []})
        assert pt.text_zones == []


# ============================================================
# PageDef
# ============================================================


class TestParsePageDef:
    def test_full_page_def(self) -> None:
        data = {
            "type": "fixed",
            "page_type": "bic_controles",
            "orientation": "landscape",
            "repeat": "auto",
        }
        pd = parse_page_def(data)
        assert isinstance(pd, PageDef)
        assert pd.type == "fixed"
        assert pd.page_type == "bic_controles"
        assert pd.orientation == "landscape"
        assert pd.repeat == "auto"

    def test_defaults(self) -> None:
        pd = parse_page_def({"type": "special", "page_type": "voorblad"})
        assert pd.orientation == "portrait"
        assert pd.repeat == "none"

    def test_missing_type_raises(self) -> None:
        with pytest.raises(KeyError):
            parse_page_def({"page_type": "test"})

    def test_missing_page_type_raises(self) -> None:
        with pytest.raises(KeyError):
            parse_page_def({"type": "special"})


# ============================================================
# TemplateConfig
# ============================================================


class TestParseTemplateConfig:
    def test_full_template(self) -> None:
        data = {
            "name": "bic_factuur",
            "tenant": "symitech",
            "pages": [
                {"type": "special", "page_type": "voorblad"},
                {"type": "fixed", "page_type": "locatie"},
                {"type": "fixed", "page_type": "bic_controles", "repeat": "auto"},
            ],
        }
        tc = parse_template_config(data)
        assert isinstance(tc, TemplateConfig)
        assert tc.name == "bic_factuur"
        assert tc.tenant == "symitech"
        assert len(tc.pages) == 3
        assert tc.pages[0].type == "special"
        assert tc.pages[2].repeat == "auto"

    def test_minimal_template(self) -> None:
        tc = parse_template_config({})
        assert tc.name == "unknown"
        assert tc.tenant == ""
        assert tc.pages == []

    def test_empty_pages(self) -> None:
        tc = parse_template_config({"name": "test", "tenant": "t", "pages": []})
        assert tc.pages == []
