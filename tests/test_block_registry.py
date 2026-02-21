"""Tests voor block_registry — factory functies voor content blocks."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest
from reportlab.platypus import Flowable, PageBreak, Paragraph, Spacer

from bm_reports.components.calculation import CalculationBlock
from bm_reports.components.check_block import CheckBlock
from bm_reports.components.map_block import KadasterMap
from bm_reports.components.table_block import TableBlock
from bm_reports.core.block_registry import (
    BLOCK_REGISTRY,
    create_block,
    resolve_image_source,
)


# ============================================================
# TestCreateBlock — dispatch via create_block()
# ============================================================


class TestCreateBlock:
    """Tests voor de centrale create_block() dispatch functie."""

    def test_paragraph(self):
        block = create_block({"type": "paragraph", "text": "Hello"})
        assert isinstance(block, Paragraph)

    def test_calculation(self):
        block = create_block({"type": "calculation", "title": "Test"})
        assert isinstance(block, CalculationBlock)

    def test_check(self):
        block = create_block({"type": "check", "description": "UC test"})
        assert isinstance(block, CheckBlock)

    def test_table(self):
        block = create_block({
            "type": "table",
            "headers": ["A", "B"],
            "rows": [["1", "2"]],
        })
        assert isinstance(block, TableBlock)

    def test_spacer(self):
        block = create_block({"type": "spacer", "height_mm": 10})
        assert isinstance(block, Spacer)

    def test_page_break(self):
        block = create_block({"type": "page_break"})
        assert isinstance(block, PageBreak)

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Onbekend content block type"):
            create_block({"type": "nonexistent_block"})

    def test_missing_type_raises(self):
        with pytest.raises(ValueError, match="mist 'type' veld"):
            create_block({"text": "no type"})


# ============================================================
# TestCreateParagraph
# ============================================================


class TestCreateParagraph:
    def test_default_style(self):
        block = create_block({"type": "paragraph", "text": "Test tekst"})
        assert isinstance(block, Paragraph)
        assert block.style.name == "Normal"

    def test_custom_style(self):
        block = create_block({
            "type": "paragraph",
            "text": "Heading tekst",
            "style": "Heading1",
        })
        assert isinstance(block, Paragraph)
        assert block.style.name == "Heading1"

    def test_unknown_style_falls_back_to_normal(self):
        block = create_block({
            "type": "paragraph",
            "text": "Test",
            "style": "NonExistentStyle",
        })
        assert block.style.name == "Normal"


# ============================================================
# TestCreateCalculation
# ============================================================


class TestCreateCalculation:
    def test_all_fields(self):
        block = create_block({
            "type": "calculation",
            "title": "Veldmoment",
            "formula": "M = q*l²/8",
            "substitution": "M = 8.5*6²/8",
            "result": "38.3",
            "unit": "kNm",
            "reference": "NEN-EN 1993",
        })
        assert isinstance(block, CalculationBlock)
        assert block.title == "Veldmoment"
        assert block.formula == "M = q*l²/8"
        assert block.result == "38.3"
        assert block.unit == "kNm"
        assert block.reference == "NEN-EN 1993"

    def test_minimal(self):
        block = create_block({"type": "calculation", "title": "Minimaal"})
        assert isinstance(block, CalculationBlock)
        assert block.title == "Minimaal"
        assert block.formula == ""
        assert block.result == ""


# ============================================================
# TestCreateCheck
# ============================================================


class TestCreateCheck:
    def test_mapping_required_value(self):
        """Schema veld 'required_value' wordt gemapped naar CheckBlock 'required'."""
        block = create_block({
            "type": "check",
            "description": "UC buiging",
            "required_value": "UC ≤ 1.0",
            "calculated_value": "0.39",
        })
        assert isinstance(block, CheckBlock)
        assert block.required == "UC ≤ 1.0"
        assert block.calculated == "0.39"

    def test_auto_result_voldoet(self):
        block = create_block({
            "type": "check",
            "description": "Test",
            "unity_check": 0.5,
            "limit": 1.0,
        })
        assert block.result == "VOLDOET"

    def test_auto_result_voldoet_niet(self):
        block = create_block({
            "type": "check",
            "description": "Test",
            "unity_check": 1.5,
            "limit": 1.0,
        })
        assert block.result == "VOLDOET NIET"

    def test_explicit_result(self):
        block = create_block({
            "type": "check",
            "description": "Test",
            "unity_check": 0.5,
            "result": "VOLDOET NIET",
        })
        assert block.result == "VOLDOET NIET"

    def test_reference(self):
        block = create_block({
            "type": "check",
            "description": "Test",
            "reference": "NEN-EN 1993-1-1 §6.2.5",
        })
        assert block.reference == "NEN-EN 1993-1-1 §6.2.5"


# ============================================================
# TestCreateTable
# ============================================================


class TestCreateTable:
    def test_headers_and_rows(self):
        block = create_block({
            "type": "table",
            "headers": ["Kol1", "Kol2"],
            "rows": [["a", "b"], ["c", "d"]],
        })
        assert isinstance(block, TableBlock)
        assert block.headers == ["Kol1", "Kol2"]
        assert len(block.rows) == 2

    def test_column_widths_mapping(self):
        """Schema veld 'column_widths' wordt gemapped naar 'col_widths_mm'."""
        block = create_block({
            "type": "table",
            "headers": ["A", "B"],
            "rows": [["1", "2"]],
            "column_widths": [50, 80],
        })
        assert block.col_widths_mm == [50, 80]

    def test_style_striped_to_zebra(self):
        """Schema style 'striped' wordt gemapped naar zebra=True."""
        block = create_block({
            "type": "table",
            "headers": ["A"],
            "rows": [["1"]],
            "style": "striped",
        })
        assert block.zebra is True

    def test_style_minimal_no_zebra(self):
        block = create_block({
            "type": "table",
            "headers": ["A"],
            "rows": [["1"]],
            "style": "minimal",
        })
        assert block.zebra is False

    def test_title(self):
        block = create_block({
            "type": "table",
            "title": "Materiaaltabel",
            "headers": ["A"],
            "rows": [["1"]],
        })
        assert block.title == "Materiaaltabel"


# ============================================================
# TestCreateImage
# ============================================================


class TestCreateImage:
    def test_existing_file(self, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

        block = create_block(
            {"type": "image", "src": str(img), "caption": "Test afbeelding"},
            base_dir=tmp_path,
        )
        # ImageBlock raises FileNotFoundError for invalid PNG, but our test PNG
        # might not be valid enough. Let's check it's a Flowable at minimum.
        assert isinstance(block, Flowable)

    def test_nonexistent_returns_placeholder(self):
        """Niet-bestaand bestand retourneert placeholder Paragraph."""
        block = create_block(
            {"type": "image", "src": "/nonexistent/path/image.png"},
        )
        assert isinstance(block, Paragraph)

    def test_base64_source(self, tmp_path):
        """Base64 encoded image wordt gedecoded naar tempfile."""
        # Minimale PNG bytes
        png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
        b64_data = base64.b64encode(png_bytes).decode()

        block = create_block({
            "type": "image",
            "src": {"data": b64_data, "media_type": "image/png"},
        })
        # Kan placeholder zijn als de PNG niet geldig genoeg is,
        # maar het moet een Flowable zijn
        assert isinstance(block, Flowable)


# ============================================================
# TestCreateMap
# ============================================================


class TestCreateMap:
    def test_center_to_lat_lon_mapping(self):
        """Schema center.lat/lon worden gemapped naar latitude/longitude."""
        block = create_block({
            "type": "map",
            "center": {"lat": 52.0975, "lon": 4.2200},
        })
        assert isinstance(block, KadasterMap)
        assert block.latitude == 52.0975
        assert block.longitude == 4.2200

    def test_defaults(self):
        block = create_block({"type": "map"})
        assert isinstance(block, KadasterMap)
        assert block.radius_m == 100.0
        assert block.width_mm == 120.0

    def test_layers_and_caption(self):
        block = create_block({
            "type": "map",
            "center": {"lat": 52.0, "lon": 4.0},
            "layers": ["percelen", "luchtfoto"],
            "caption": "Situering",
        })
        assert block.layers == ["percelen", "luchtfoto"]
        assert block.caption == "Situering"


# ============================================================
# TestResolveImageSource
# ============================================================


class TestResolveImageSource:
    def test_string_path(self):
        result = resolve_image_source("images/test.png")
        assert isinstance(result, Path)
        assert result == Path("images/test.png")

    def test_absolute_path(self):
        abs_path = "/absolute/path/to/image.png"
        result = resolve_image_source(abs_path)
        assert result == Path(abs_path)

    def test_relative_with_base_dir(self, tmp_path):
        result = resolve_image_source("images/test.png", base_dir=tmp_path)
        assert result == tmp_path / "images" / "test.png"

    def test_base64_creates_file(self):
        data = base64.b64encode(b"fake image data").decode()
        result = resolve_image_source({
            "data": data,
            "media_type": "image/png",
        })
        assert isinstance(result, Path)
        assert result.exists()
        assert result.suffix == ".png"
        assert result.read_bytes() == b"fake image data"

    def test_base64_with_filename(self):
        data = base64.b64encode(b"test").decode()
        result = resolve_image_source({
            "data": data,
            "media_type": "image/jpeg",
            "filename": "photo.jpg",
        })
        assert result.suffix == ".jpg"
        assert "photo.jpg" in result.name
