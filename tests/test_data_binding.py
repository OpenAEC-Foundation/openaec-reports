"""Extended tests voor data binding — resolve_bind + format_value edge cases."""

from __future__ import annotations

from bm_reports.core.template_engine import format_value, resolve_bind

# ============================================================
# resolve_bind — diep nested + arrays + mixed types
# ============================================================


class TestResolveBindDeep:
    def test_three_levels(self) -> None:
        data = {"a": {"b": {"c": "deep"}}}
        assert resolve_bind(data, "a.b.c") == "deep"

    def test_four_levels(self) -> None:
        data = {"level1": {"level2": {"level3": {"level4": 42}}}}
        assert resolve_bind(data, "level1.level2.level3.level4") == 42

    def test_array_value(self) -> None:
        """Pad resolves naar een list → retourneert de list."""
        data = {"items": [1, 2, 3]}
        result = resolve_bind(data, "items")
        assert result == [1, 2, 3]

    def test_dict_value(self) -> None:
        """Pad resolves naar een dict → retourneert de dict."""
        data = {"meta": {"info": {"a": 1, "b": 2}}}
        result = resolve_bind(data, "meta.info")
        assert result == {"a": 1, "b": 2}

    def test_mixed_types(self) -> None:
        """Nested data met mixed types."""
        data = {
            "project": {
                "name": "Test",
                "cost": 1500.0,
                "active": True,
                "tags": ["bic", "inspection"],
            },
        }
        assert resolve_bind(data, "project.name") == "Test"
        assert resolve_bind(data, "project.cost") == 1500.0
        assert resolve_bind(data, "project.active") is True
        assert resolve_bind(data, "project.tags") == ["bic", "inspection"]

    def test_empty_dict(self) -> None:
        assert resolve_bind({}, "any.path") is None

    def test_single_part_missing(self) -> None:
        assert resolve_bind({"a": 1}, "b") is None

    def test_path_through_none(self) -> None:
        """Pad gaat door een None waarde."""
        data = {"a": {"b": None}}
        assert resolve_bind(data, "a.b.c") is None

    def test_path_through_list(self) -> None:
        """Pad gaat door een list (geen dict) → None."""
        data = {"a": [1, 2, 3]}
        assert resolve_bind(data, "a.0") is None

    def test_path_through_string(self) -> None:
        data = {"a": "hello"}
        assert resolve_bind(data, "a.b") is None

    def test_path_through_int(self) -> None:
        data = {"a": 42}
        assert resolve_bind(data, "a.b") is None

    def test_boolean_value(self) -> None:
        data = {"enabled": False}
        assert resolve_bind(data, "enabled") is False

    def test_zero_value(self) -> None:
        data = {"count": 0}
        assert resolve_bind(data, "count") == 0

    def test_empty_string_value(self) -> None:
        data = {"name": ""}
        assert resolve_bind(data, "name") == ""


# ============================================================
# format_value — extended edge cases
# ============================================================


class TestFormatValueExtended:
    def test_negative_currency(self) -> None:
        result = format_value(-1234.56, "currency_nl")
        assert result == "\u20ac -1.234,56"

    def test_zero_currency(self) -> None:
        result = format_value(0, "currency_nl")
        assert result == "\u20ac 0,00"

    def test_zero_float_currency(self) -> None:
        result = format_value(0.0, "currency_nl")
        assert result == "\u20ac 0,00"

    def test_small_amount_currency(self) -> None:
        result = format_value(0.99, "currency_nl")
        assert result == "\u20ac 0,99"

    def test_large_amount_currency(self) -> None:
        result = format_value(1234567.89, "currency_nl")
        assert result == "\u20ac 1.234.567,89"

    def test_string_integer_currency(self) -> None:
        result = format_value("1000", "currency_nl")
        assert result == "\u20ac 1.000,00"

    def test_bool_true(self) -> None:
        assert format_value(True) == "True"

    def test_bool_false(self) -> None:
        assert format_value(False) == "False"

    def test_integer(self) -> None:
        assert format_value(42) == "42"

    def test_float(self) -> None:
        assert format_value(3.14) == "3.14"

    def test_list_value(self) -> None:
        """Lijst als waarde → str representatie."""
        assert format_value([1, 2]) == "[1, 2]"

    def test_empty_format(self) -> None:
        """format=None (geen format) → str()."""
        assert format_value(42, None) == "42"

    def test_unknown_format(self) -> None:
        """Onbekend format → str()."""
        assert format_value(42, "unknown_format") == "42"

    def test_negative_zero_currency(self) -> None:
        result = format_value(-0.0, "currency_nl")
        # Accepteer zowel "€ -0,00" als "€ 0,00"
        assert "\u20ac" in result
        assert "0,00" in result
