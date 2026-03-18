"""Tests voor SpreadsheetBlock — Excel-achtige tabellen."""

from __future__ import annotations

from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate

from openaec_reports.components.spreadsheet_block import SpreadsheetBlock
from openaec_reports.core.block_registry import create_block


class TestBasicRendering:
    """Basis rendering tests."""

    def test_simple_spreadsheet(self) -> None:
        block = SpreadsheetBlock(
            headers=["A", "B"],
            rows=[["1", "2"], ["3", "4"]],
        )
        w, h = block.wrap(400, 1000)
        assert w > 0
        assert h > 0

    def test_with_title(self) -> None:
        block = SpreadsheetBlock(
            headers=["X"],
            rows=[["val"]],
            title="Test Titel",
        )
        w, h = block.wrap(400, 1000)
        assert h > 0

    def test_empty_rows(self) -> None:
        block = SpreadsheetBlock(
            headers=["A", "B", "C"],
            rows=[["", "", ""]],
        )
        w, h = block.wrap(400, 1000)
        assert h > 0

    def test_col_widths_mm(self) -> None:
        block = SpreadsheetBlock(
            headers=["A", "B"],
            rows=[["1", "2"]],
            col_widths_mm=[50, 80],
        )
        w, h = block.wrap(500, 1000)
        assert w > 0


class TestMergedCells:
    """Merged cells tests."""

    def test_horizontal_merge(self) -> None:
        block = SpreadsheetBlock(
            headers=["A", "B", "C"],
            rows=[["merged", "", ""], ["a", "b", "c"]],
            merged_cells=[{"row": 0, "col": 0, "rowspan": 1, "colspan": 2}],
        )
        w, h = block.wrap(400, 1000)
        assert h > 0

    def test_vertical_merge(self) -> None:
        block = SpreadsheetBlock(
            headers=["A", "B"],
            rows=[["merged", "x"], ["", "y"], ["a", "b"]],
            merged_cells=[{"row": 0, "col": 0, "rowspan": 2, "colspan": 1}],
        )
        w, h = block.wrap(400, 1000)
        assert h > 0

    def test_block_merge(self) -> None:
        """2x2 merge."""
        block = SpreadsheetBlock(
            headers=["A", "B", "C"],
            rows=[["big", "", "x"], ["", "", "y"], ["a", "b", "c"]],
            merged_cells=[{"row": 0, "col": 0, "rowspan": 2, "colspan": 2}],
        )
        w, h = block.wrap(400, 1000)
        assert h > 0


class TestCellStyles:
    """Per-cel styling tests."""

    def test_bold_cell(self) -> None:
        block = SpreadsheetBlock(
            headers=["A"],
            rows=[["vet"]],
            cell_styles={"0,0": {"bold": True}},
        )
        w, h = block.wrap(400, 1000)
        assert h > 0

    def test_italic_cell(self) -> None:
        block = SpreadsheetBlock(
            headers=["A"],
            rows=[["cursief"]],
            cell_styles={"0,0": {"italic": True}},
        )
        w, h = block.wrap(400, 1000)
        assert h > 0

    def test_bg_color(self) -> None:
        block = SpreadsheetBlock(
            headers=["A"],
            rows=[["kleur"]],
            cell_styles={"0,0": {"bg_color": "#fef3c7"}},
        )
        w, h = block.wrap(400, 1000)
        assert h > 0

    def test_alignment(self) -> None:
        block = SpreadsheetBlock(
            headers=["A"],
            rows=[["rechts"]],
            cell_styles={"0,0": {"align": "right"}},
        )
        w, h = block.wrap(400, 1000)
        assert h > 0

    def test_font_size(self) -> None:
        block = SpreadsheetBlock(
            headers=["A"],
            rows=[["groot"]],
            cell_styles={"0,0": {"font_size": 14}},
        )
        w, h = block.wrap(400, 1000)
        assert h > 0

    def test_combined_styles(self) -> None:
        block = SpreadsheetBlock(
            headers=["A", "B"],
            rows=[["vet", "normaal"], ["kleur", "cursief"]],
            cell_styles={
                "0,0": {"bold": True, "bg_color": "#d1fae5"},
                "1,0": {"bg_color": "#dbeafe"},
                "1,1": {"italic": True, "align": "center"},
            },
        )
        w, h = block.wrap(400, 1000)
        assert h > 0

    def test_no_style_override(self) -> None:
        """Cel zonder style entry gebruikt standaard stijl."""
        block = SpreadsheetBlock(
            headers=["A"],
            rows=[["normaal"]],
            cell_styles={},
        )
        w, h = block.wrap(400, 1000)
        assert h > 0


class TestRowHeights:
    """Rijhoogte tests."""

    def test_custom_row_heights(self) -> None:
        block = SpreadsheetBlock(
            headers=["A"],
            rows=[["r1"], ["r2"], ["r3"]],
            row_heights_mm=[10, 15, 10],
        )
        w, h = block.wrap(400, 1000)
        assert h > 0

    def test_partial_row_heights(self) -> None:
        """Minder heights dan rijen → padding met default."""
        block = SpreadsheetBlock(
            headers=["A"],
            rows=[["r1"], ["r2"], ["r3"]],
            row_heights_mm=[12],
            default_row_height_mm=8,
        )
        w, h = block.wrap(400, 1000)
        assert h > 0


class TestBlockRegistry:
    """Block registry integratie."""

    def test_create_block_basic(self) -> None:
        data = {
            "type": "spreadsheet",
            "headers": ["X", "Y"],
            "rows": [["1", "2"]],
        }
        block = create_block(data)
        assert isinstance(block, SpreadsheetBlock)

    def test_create_block_with_new_fields(self) -> None:
        data = {
            "type": "spreadsheet",
            "headers": ["A", "B", "C"],
            "rows": [["a", "b", "c"], ["d", "e", "f"]],
            "column_widths": [40, 40, 40],
            "row_heights": [8, 10],
            "merged_cells": [
                {"row": 0, "col": 0, "rowspan": 1, "colspan": 2},
            ],
            "cell_styles": {
                "0,0": {"bold": True},
                "1,2": {"bg_color": "#fef3c7", "align": "right"},
            },
        }
        block = create_block(data)
        assert isinstance(block, SpreadsheetBlock)
        assert len(block.merged_cells) == 1
        assert len(block.cell_styles) == 2
        assert block.row_heights_mm == [8, 10]

    def test_backward_compatible(self) -> None:
        """Oude JSON zonder nieuwe velden werkt nog steeds."""
        data = {
            "type": "spreadsheet",
            "headers": ["A"],
            "rows": [["1"]],
            "show_row_numbers": True,
            "note": "test",
        }
        block = create_block(data)
        assert isinstance(block, SpreadsheetBlock)
        assert block.merged_cells == []
        assert block.cell_styles == {}
        assert block.row_heights_mm is None


class TestPdfOutput:
    """PDF output tests."""

    def test_generate_pdf_with_all_features(self) -> None:
        """PDF generatie met merges, styles en row heights."""
        block = SpreadsheetBlock(
            headers=["Omschrijving", "Aantal", "Prijs", "Totaal"],
            rows=[
                ["Beton C30/37", "12 m3", "€ 120", "€ 1.440"],
                ["Wapening B500", "850 kg", "€ 1,80", "€ 1.530"],
                [{"value": "Totaal", "style": "total"}, "", "", "€ 2.970"],
            ],
            col_widths_mm=[60, 30, 30, 30],
            row_heights_mm=[8, 8, 10],
            merged_cells=[
                {"row": 2, "col": 0, "rowspan": 1, "colspan": 3},
            ],
            cell_styles={
                "2,3": {"bold": True, "bg_color": "#d1fae5"},
            },
        )

        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        doc.build([block])
        pdf_bytes = buf.getvalue()
        assert len(pdf_bytes) > 500
        assert pdf_bytes[:5] == b"%PDF-"
