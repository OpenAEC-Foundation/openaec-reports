"""Tests voor template_engine.py — data binding, helpers, paginering."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from bm_reports.core.document import A4
from bm_reports.core.template_config import (
    PageType,
    TableConfig,
    TemplateConfig,
)
from bm_reports.core.template_engine import (
    _BuildContext,
    _get_pagesize,
    _paginate_table_data,
    format_value,
    resolve_bind,
)

# ============================================================
# resolve_bind
# ============================================================


class TestResolveBind:
    def test_simple_key(self) -> None:
        assert resolve_bind({"name": "Alice"}, "name") == "Alice"

    def test_nested_key(self) -> None:
        data = {"client": {"name": "Woonbron"}}
        assert resolve_bind(data, "client.name") == "Woonbron"

    def test_empty_path(self) -> None:
        assert resolve_bind({"a": 1}, "") is None

    def test_missing_key(self) -> None:
        assert resolve_bind({"a": 1}, "b") is None

    def test_missing_nested_key(self) -> None:
        assert resolve_bind({"a": {"b": 1}}, "a.c") is None

    def test_none_value(self) -> None:
        """Veld bestaat maar is None."""
        assert resolve_bind({"a": None}, "a") is None

    def test_non_dict_intermediate(self) -> None:
        """Pad gaat door een non-dict → None."""
        assert resolve_bind({"a": "string"}, "a.b") is None


# ============================================================
# format_value
# ============================================================


class TestFormatValue:
    def test_none_returns_empty(self) -> None:
        assert format_value(None) == ""

    def test_plain_text(self) -> None:
        assert format_value("hello") == "hello"

    def test_plain_number(self) -> None:
        assert format_value(42) == "42"

    def test_currency_nl_basic(self) -> None:
        result = format_value(1234.56, "currency_nl")
        assert result == "\u20ac 1.234,56"

    def test_currency_nl_integer(self) -> None:
        result = format_value(1000, "currency_nl")
        assert result == "\u20ac 1.000,00"

    def test_currency_nl_none(self) -> None:
        assert format_value(None, "currency_nl") == ""

    def test_currency_nl_string_number(self) -> None:
        """String die een getal is → currency formattering."""
        result = format_value("2500.50", "currency_nl")
        assert result == "\u20ac 2.500,50"

    def test_currency_nl_non_numeric_string(self) -> None:
        """Niet-numerieke string bij currency_nl → plain string."""
        assert format_value("n/a", "currency_nl") == "n/a"

    def test_no_format(self) -> None:
        assert format_value(123, None) == "123"


# ============================================================
# _get_pagesize
# ============================================================


class TestGetPagesize:
    def test_portrait(self) -> None:
        w, h = _get_pagesize("portrait")
        assert w == A4.width_pt
        assert h == A4.height_pt

    def test_landscape(self) -> None:
        w, h = _get_pagesize("landscape")
        # Landscape = W en H omgedraaid
        assert w == A4.height_pt
        assert h == A4.width_pt

    def test_unknown_defaults_portrait(self) -> None:
        """Onbekende orientatie → portrait (default branch)."""
        w, h = _get_pagesize("unknown")
        assert w == A4.width_pt
        assert h == A4.height_pt


# ============================================================
# _paginate_table_data
# ============================================================


class TestPaginateTableData:
    @staticmethod
    def _make_config(
        origin_y: float = 60.0,
        max_y: float = 260.0,
        row_height: float = 5.6,
    ) -> TableConfig:
        return TableConfig(
            data_bind="items",
            origin_y_mm=origin_y,
            max_y_mm=max_y,
            row_height_mm=row_height,
        )

    def test_empty_rows(self) -> None:
        """Geen rijen → lege lijst."""
        result = _paginate_table_data([], self._make_config())
        assert result == []

    def test_single_row(self) -> None:
        rows = [{"label": "test"}]
        result = _paginate_table_data(rows, self._make_config())
        assert len(result) == 1
        assert result[0] == rows

    def test_exact_fit(self) -> None:
        """Precies passende rijen → 1 chunk."""
        config = self._make_config()
        rows_per_page = int((config.max_y_mm - config.origin_y_mm) / config.row_height_mm)
        rows = [{"i": i} for i in range(rows_per_page)]
        result = _paginate_table_data(rows, config)
        assert len(result) == 1
        assert len(result[0]) == rows_per_page

    def test_overflow(self) -> None:
        """100 rijen bij default config → meerdere chunks."""
        config = self._make_config()
        rows_per_page = int((config.max_y_mm - config.origin_y_mm) / config.row_height_mm)
        total_rows = 100
        rows = [{"i": i} for i in range(total_rows)]
        result = _paginate_table_data(rows, config)

        import math
        expected_chunks = math.ceil(total_rows / rows_per_page)
        assert len(result) == expected_chunks

        # Alle rijen verdeeld
        total = sum(len(c) for c in result)
        assert total == total_rows

    def test_rows_per_page_calculation(self) -> None:
        """Verifieer rows_per_page berekening."""
        config = self._make_config(origin_y=60, max_y=260, row_height=5.6)
        available = 260 - 60  # = 200 mm
        expected_rpp = int(available / 5.6)  # = 35
        assert expected_rpp == 35

        rows = [{"i": i} for i in range(35)]
        result = _paginate_table_data(rows, config)
        assert len(result) == 1

    def test_one_more_than_fit(self) -> None:
        """Eén rij meer dan past → 2 chunks."""
        config = self._make_config(origin_y=60, max_y=260, row_height=5.6)
        rows_per_page = int((260 - 60) / 5.6)
        rows = [{"i": i} for i in range(rows_per_page + 1)]
        result = _paginate_table_data(rows, config)
        assert len(result) == 2
        assert len(result[0]) == rows_per_page
        assert len(result[1]) == 1


# ============================================================
# _BuildContext
# ============================================================


class TestBuildContext:
    def test_instantiation(self) -> None:
        template = TemplateConfig(name="test", tenant="t")
        page_types: dict[str, PageType] = {}
        data: dict[str, Any] = {"key": "val"}
        brand = MagicMock()
        stationery = MagicMock()
        stationery_dir = Path("/tmp/stationery")

        ctx = _BuildContext(
            template=template,
            page_types=page_types,
            data=data,
            brand=brand,
            stationery=stationery,
            stationery_dir=stationery_dir,
        )

        assert ctx.template is template
        assert ctx.page_types is page_types
        assert ctx.data is data
        assert ctx.brand is brand
        assert ctx.stationery is stationery
        assert ctx.stationery_dir == stationery_dir
