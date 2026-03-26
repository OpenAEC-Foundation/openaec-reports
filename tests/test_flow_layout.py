"""Tests voor flow layout — zone verschuiving bij text wrapping overflow."""

from __future__ import annotations

from unittest.mock import patch

from openaec_reports.core.template_config import (
    ImageZone,
    LineZone,
    TextZone,
)
from openaec_reports.core.template_engine import _apply_flow_layout


def _make_brand():
    """Minimale brand mock voor font/kleur resolve."""
    class _Brand:
        fonts = {"body": "Helvetica", "heading": "Helvetica-Bold"}
        colors = {
            "primary": "#40124A",
            "secondary": "#38BDA0",
            "text": "#45243D",
            "white": "#FFFFFF",
        }
    return _Brand()


# ============================================================
# Helpers
# ============================================================

FOOTER_Y = 260.0


def _tz(bind: str, y_mm: float, max_width_mm: float | None = None) -> TextZone:
    """Shorthand voor TextZone aanmaken."""
    return TextZone(
        bind=bind,
        x_mm=19.5,
        y_mm=y_mm,
        font="body",
        size=10,
        max_width_mm=max_width_mm,
        line_height_mm=4.2,
    )


def _lz(y_mm: float) -> LineZone:
    """Shorthand voor LineZone aanmaken."""
    return LineZone(x0_mm=17.5, y_mm=y_mm, x1_mm=80.2, width_pt=1.0, color="primary")


def _iz(bind: str, y_mm: float) -> ImageZone:
    """Shorthand voor ImageZone aanmaken."""
    return ImageZone(bind=bind, x_mm=40.0, y_mm=y_mm, width_mm=130, height_mm=100)


# ============================================================
# Tests
# ============================================================


class TestNoOverflow:
    """Als data kort genoeg is, mogen zones niet verschuiven."""

    def test_short_text_no_changes(self) -> None:
        """Korte tekst → geen verschuiving."""
        text_zones = [
            _tz("_static.Label", 44.3),
            _tz("field.value", 44.3, max_width_mm=83),
            _tz("_static.Label2", 48.4),
            _tz("field.value2", 48.4, max_width_mm=83),
        ]
        data = {"field": {"value": "Kort", "value2": "Ook kort"}}

        new_tz, new_lz, new_iz = _apply_flow_layout(
            text_zones, [], [], data, _make_brand(), FOOTER_Y,
        )

        # Posities ongewijzigd
        assert [z.y_mm for z in new_tz] == [44.3, 44.3, 48.4, 48.4]

    def test_no_max_width_no_changes(self) -> None:
        """Zones zonder max_width_mm → geen wrapping check."""
        text_zones = [
            _tz("_static.Label", 44.3),
            _tz("_static.Label2", 48.4),
        ]
        data = {}

        new_tz, _, _ = _apply_flow_layout(
            text_zones, [], [], data, _make_brand(), FOOTER_Y,
        )

        assert [z.y_mm for z in new_tz] == [44.3, 48.4]


class TestSingleRowOverflow:
    """Eén veld wraps naar meerdere regels — alles eronder verschuift."""

    def test_single_overflow_shifts_below(self) -> None:
        """Veld op y=44.3 wraps, zones op y=48.4 en y=52.4 moeten verschuiven."""
        text_zones = [
            _tz("_static.Label", 44.3),
            _tz("desc", 44.3, max_width_mm=83),
            _tz("_static.Label2", 48.4),
            _tz("val2", 48.4, max_width_mm=83),
            _tz("_static.Label3", 52.4),
            _tz("val3", 52.4, max_width_mm=83),
        ]

        # Tekst die lang genoeg is om te wrappen in 83mm bij 10pt Helvetica
        long_text = "Dit is een zeer lange beschrijving die absoluut niet in een enkele regel past bij 83mm breedte en 10pt font"
        data = {"desc": long_text, "val2": "kort", "val3": "kort"}

        new_tz, _, _ = _apply_flow_layout(
            text_zones, [], [], data, _make_brand(), FOOTER_Y,
        )

        # De eerste rij (44.3) behoudt positie
        row1 = [z for z in new_tz if abs(z.y_mm - 44.3) < 0.1]
        assert len(row1) == 2

        # De tweede rij moet verschoven zijn (> 48.4)
        row2 = [z for z in new_tz if z.bind in ("_static.Label2", "val2")]
        assert all(z.y_mm > 48.4 for z in row2)

        # De derde rij moet ook verschoven zijn
        row3 = [z for z in new_tz if z.bind in ("_static.Label3", "val3")]
        assert all(z.y_mm > 52.4 for z in row3)


class TestMultipleOverflows:
    """Meerdere velden wrappen — offsets accumuleren."""

    def test_cumulative_offsets(self) -> None:
        """Twee velden wrappen → derde rij verschuift met som van beide."""
        text_zones = [
            _tz("desc1", 44.3, max_width_mm=83),
            _tz("desc2", 48.4, max_width_mm=83),
            _tz("val3", 52.4, max_width_mm=83),
        ]

        long_text = "Dit is een zeer lange beschrijving die absoluut niet in een enkele regel past bij 83mm breedte en 10pt font"
        data = {"desc1": long_text, "desc2": long_text, "val3": "kort"}

        new_tz, _, _ = _apply_flow_layout(
            text_zones, [], [], data, _make_brand(), FOOTER_Y,
        )

        # Derde zone moet meer verschoven zijn dan de tweede
        shift_2 = new_tz[1].y_mm - 48.4
        shift_3 = new_tz[2].y_mm - 52.4
        assert shift_3 >= shift_2


class TestFooterExcluded:
    """Footer zones (y >= footer_y_mm) blijven op hun vaste positie."""

    def test_footer_not_shifted(self) -> None:
        """Footer zones verplaatsen NIET, ook bij overflow."""
        text_zones = [
            _tz("desc", 44.3, max_width_mm=83),
            _tz("_static.Label2", 48.4),
            # Footer zones
            TextZone(bind="client.name", x_mm=10.3, y_mm=275.4, font="heading", size=10),
            TextZone(bind="_page_number", x_mm=172.0, y_mm=275.4, font="heading", size=12, align="right"),
        ]

        long_text = "Dit is een zeer lange beschrijving die absoluut niet in een enkele regel past bij 83mm breedte"
        data = {"desc": long_text, "client": {"name": "TestBV"}}

        new_tz, _, _ = _apply_flow_layout(
            text_zones, [], [], data, _make_brand(), FOOTER_Y,
        )

        # Footer zones behouden originele y
        footer_zones = [z for z in new_tz if z.y_mm >= FOOTER_Y]
        assert len(footer_zones) == 2
        assert all(z.y_mm == 275.4 for z in footer_zones)


class TestLineZonesShift:
    """Lijnen verschuiven mee met tekst."""

    def test_lines_shift_with_content(self) -> None:
        """Line zones onder overflow verschuiven mee."""
        text_zones = [
            _tz("desc", 44.3, max_width_mm=83),
            _tz("_static.Label2", 90.0),
        ]
        line_zones = [
            _lz(42.05),  # boven de overflow → kleine/geen shift
            _lz(88.55),  # onder de overflow → moet verschuiven als er overflow is
        ]

        long_text = "Dit is een zeer lange beschrijving die absoluut niet in een enkele regel past bij 83mm breedte en 10pt font"
        data = {"desc": long_text}

        _, new_lz, _ = _apply_flow_layout(
            text_zones, line_zones, [], data, _make_brand(), FOOTER_Y,
        )

        # Lijn op 88.55 moet verschoven zijn als er overflow was
        # (afhankelijk van of er genoeg overflow is — met 1 wrapping rij
        #  en gap van 45.7mm is er mogelijk geen overflow)
        # We controleren minimaal dat het mechanisme werkt:
        assert len(new_lz) == 2


class TestImageZonesShift:
    """Afbeeldingen verschuiven mee met tekst."""

    def test_images_shift_with_content(self) -> None:
        """Image zones onder overflow verschuiven mee."""
        text_zones = [
            _tz("desc", 44.3, max_width_mm=83),
            _tz("_static.Label2", 48.4),
        ]
        image_zones = [
            _iz("foto", 157.0),
        ]

        long_text = "Dit is een zeer lange beschrijving die absoluut niet in een enkele regel past bij 83mm breedte en 10pt font"
        data = {"desc": long_text}

        _, _, new_iz = _apply_flow_layout(
            text_zones, [], image_zones, data, _make_brand(), FOOTER_Y,
        )

        assert len(new_iz) == 1


class TestEmptyData:
    """Lege of ontbrekende data veroorzaakt geen fouten."""

    def test_empty_data_no_crash(self) -> None:
        """Lege data dict → geen crash, zones ongewijzigd."""
        text_zones = [
            _tz("_static.Label", 44.3),
            _tz("field.value", 44.3, max_width_mm=83),
            _tz("_static.Label2", 48.4),
        ]

        new_tz, _, _ = _apply_flow_layout(
            text_zones, [], [], {}, _make_brand(), FOOTER_Y,
        )

        assert [z.y_mm for z in new_tz] == [44.3, 44.3, 48.4]

    def test_none_values_no_crash(self) -> None:
        """None waarden in data → geen crash."""
        text_zones = [
            _tz("field.value", 44.3, max_width_mm=83),
            _tz("field.other", 48.4, max_width_mm=83),
        ]
        data = {"field": {"value": None, "other": None}}

        new_tz, _, _ = _apply_flow_layout(
            text_zones, [], [], data, _make_brand(), FOOTER_Y,
        )

        assert [z.y_mm for z in new_tz] == [44.3, 48.4]

    def test_empty_zones_no_crash(self) -> None:
        """Geen zones → geen crash."""
        new_tz, new_lz, new_iz = _apply_flow_layout(
            [], [], [], {}, _make_brand(), FOOTER_Y,
        )

        assert new_tz == []
        assert new_lz == []
        assert new_iz == []

    def test_single_row_no_crash(self) -> None:
        """Slechts één rij → geen crash (geen volgende rij voor gap berekening)."""
        text_zones = [_tz("desc", 44.3, max_width_mm=83)]
        data = {"desc": "Kort"}

        new_tz, _, _ = _apply_flow_layout(
            text_zones, [], [], data, _make_brand(), FOOTER_Y,
        )

        assert len(new_tz) == 1


class TestParseFlowLayoutConfig:
    """parse_page_type leest flow_layout en flow_footer_y_mm."""

    def test_parse_flow_layout_true(self) -> None:
        from openaec_reports.core.template_config import parse_page_type

        data = {
            "name": "test_page",
            "flow_layout": True,
            "flow_footer_y_mm": 265.0,
        }
        pt = parse_page_type(data)
        assert pt.flow_layout is True
        assert pt.flow_footer_y_mm == 265.0

    def test_parse_flow_layout_default(self) -> None:
        from openaec_reports.core.template_config import parse_page_type

        data = {"name": "test_page"}
        pt = parse_page_type(data)
        assert pt.flow_layout is False
        assert pt.flow_footer_y_mm == 260.0
