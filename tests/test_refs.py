"""Tests voor de $colors./$fonts.-ref resolver (core/refs.py).

Zie ook tests/test_renderer_v2.py voor de integratie met TemplateSet.
"""

from __future__ import annotations

import pytest

from openaec_reports.core.brand import BrandConfig
from openaec_reports.core.refs import resolve_refs


@pytest.fixture
def brand() -> BrandConfig:
    return BrandConfig(
        name="Test",
        slug="test",
        tenant="test-tenant",
        colors={"primary": "#40124A", "secondary": "#38BDA0"},
        fonts={"heading": "GothamBold", "body": "GothamBook"},
    )


class TestResolveRefsScalars:
    def test_literal_hex_unchanged(self, brand):
        assert resolve_refs("#40124A", brand) == "#40124A"

    def test_colors_ref_resolves(self, brand):
        assert resolve_refs("$colors.primary", brand) == "#40124A"

    def test_fonts_ref_resolves(self, brand):
        assert resolve_refs("$fonts.heading", brand) == "GothamBold"

    def test_plain_string_unchanged(self, brand):
        assert resolve_refs("GothamBook", brand) == "GothamBook"

    def test_non_string_scalars_unchanged(self, brand):
        assert resolve_refs(42, brand) == 42
        assert resolve_refs(3.14, brand) == 3.14
        assert resolve_refs(True, brand) is True
        assert resolve_refs(None, brand) is None

    def test_unknown_color_key_raises_value_error_with_context(self, brand):
        with pytest.raises(ValueError) as exc_info:
            resolve_refs("$colors.does_not_exist", brand, tenant="acme", source="cover.yaml")
        message = str(exc_info.value)
        assert "acme" in message
        assert "cover.yaml" in message
        assert "does_not_exist" in message

    def test_unknown_font_key_raises_value_error(self, brand):
        with pytest.raises(ValueError, match="fonts.does_not_exist"):
            resolve_refs("$fonts.does_not_exist", brand, tenant="acme", source="colofon.yaml")

    def test_ref_with_trailing_space_is_treated_as_literal(self, brand):
        """Een ref die niet EXACT matcht (hier: trailing space) wordt niet
        herkend als ref en dus ook niet als fout gerapporteerd — hij komt
        ongewijzigd terug als gewone string. Zie de docstring van
        ``resolve_refs`` voor de motivatie van dit gedrag."""
        value = "$colors.primary "
        assert resolve_refs(value, brand) == value

    def test_ref_embedded_in_larger_string_is_treated_as_literal(self, brand):
        value = "zie $colors.primary voor de kleur"
        assert resolve_refs(value, brand) == value


class TestResolveRefsNested:
    def test_dict_is_resolved_recursively(self, brand):
        data = {"color": "$colors.primary", "size": 9.5}
        assert resolve_refs(data, brand) == {"color": "#40124A", "size": 9.5}

    def test_list_is_resolved_recursively(self, brand):
        data = ["$colors.primary", "$colors.secondary", "#FFFFFF"]
        assert resolve_refs(data, brand) == ["#40124A", "#38BDA0", "#FFFFFF"]

    def test_dict_in_list_in_dict_is_fully_resolved(self, brand):
        data = {
            "blocks": {
                "table": {
                    "rows": [
                        {"color": "$colors.primary", "label": "Row 1"},
                        {"color": "$colors.secondary", "label": "Row 2"},
                    ],
                },
                "fonts": ["$fonts.heading", "$fonts.body"],
            },
        }
        result = resolve_refs(data, brand)
        assert result["blocks"]["table"]["rows"][0]["color"] == "#40124A"
        assert result["blocks"]["table"]["rows"][1]["color"] == "#38BDA0"
        assert result["blocks"]["fonts"] == ["GothamBold", "GothamBook"]
        # labels (plain strings) blijven ongewijzigd
        assert result["blocks"]["table"]["rows"][0]["label"] == "Row 1"

    def test_unknown_key_deep_in_structure_still_raises(self, brand):
        data = {"a": [{"b": {"color": "$colors.nope"}}]}
        with pytest.raises(ValueError, match="nope"):
            resolve_refs(data, brand, tenant="acme", source="deep.yaml")

    def test_empty_dict_and_list_unchanged(self, brand):
        assert resolve_refs({}, brand) == {}
        assert resolve_refs([], brand) == []
