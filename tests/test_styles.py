"""Tests voor create_stylesheet met brand overrides."""

from reportlab.lib.colors import HexColor

from bm_reports.core.brand import BrandConfig
from bm_reports.core.styles import create_stylesheet


class TestCreateStylesheet:
    """Tests voor create_stylesheet()."""

    def test_default_without_brand(self):
        styles = create_stylesheet()
        assert "Normal" in styles
        assert "Heading1" in styles
        assert "Heading2" in styles
        assert "Heading3" in styles
        assert styles["Normal"].fontSize == 9.5  # default body_size

    def test_with_brand_font_override(self):
        brand = BrandConfig(styles={
            "Heading1": {"fontName": "Inter-Regular", "fontSize": 18.0},
        })
        styles = create_stylesheet(brand=brand)
        assert styles["Heading1"].fontSize == 18.0

    def test_with_brand_color_override(self):
        brand = BrandConfig(styles={
            "Normal": {"textColor": "#45243D"},
        })
        styles = create_stylesheet(brand=brand)
        expected = HexColor("#45243D")
        assert styles["Normal"].textColor == expected

    def test_with_brand_leading_override(self):
        brand = BrandConfig(styles={
            "Normal": {"fontSize": 9.5, "leading": 12.0},
        })
        styles = create_stylesheet(brand=brand)
        assert styles["Normal"].fontSize == 9.5
        assert styles["Normal"].leading == 12.0

    def test_unknown_style_ignored(self):
        brand = BrandConfig(styles={
            "NonexistentStyle": {"fontSize": 99.0},
        })
        styles = create_stylesheet(brand=brand)
        assert "NonexistentStyle" not in styles

    def test_none_brand_same_as_default(self):
        default = create_stylesheet()
        none_brand = create_stylesheet(brand=None)
        assert default["Normal"].fontSize == none_brand["Normal"].fontSize

    def test_openaec_brand_overrides(self):
        brand = BrandConfig(styles={
            "Normal": {"fontName": "Inter-Regular", "fontSize": 9.5, "textColor": "#45243D"},
            "Heading1": {"fontName": "Inter-Regular", "fontSize": 18.0, "textColor": "#45243D"},
            "Heading2": {"fontName": "Inter-Regular", "fontSize": 13.0, "textColor": "#56B49B"},
        })
        styles = create_stylesheet(brand=brand)
        assert styles["Normal"].fontSize == 9.5
        assert styles["Heading1"].fontSize == 18.0
        assert styles["Heading2"].fontSize == 13.0
        assert styles["Heading2"].textColor == HexColor("#56B49B")
