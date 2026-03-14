"""Tests voor KadasterClient coördinaat-conversie (pyproj)."""

from __future__ import annotations

import pytest

from openaec_reports.data.kadaster import KadasterClient


@pytest.fixture()
def client() -> KadasterClient:
    """KadasterClient zonder cache."""
    return KadasterClient()


class TestWgs84ToRd:
    """WGS84 → RD conversie met bekende referentiepunten."""

    def test_amersfoort_origin(self, client: KadasterClient) -> None:
        """Amersfoort (RD oorsprong) → ~(155000, 463000)."""
        x, y = client.wgs84_to_rd(52.15517, 5.38721)
        assert abs(x - 155000) < 5
        assert abs(y - 463000) < 5

    def test_amsterdam_dam(self, client: KadasterClient) -> None:
        """Amsterdam Dam → ~(121000, 487000)."""
        x, y = client.wgs84_to_rd(52.3730, 4.8932)
        assert abs(x - 121000) < 1500
        assert abs(y - 487000) < 1500

    def test_rotterdam_erasmusbrug(self, client: KadasterClient) -> None:
        """Rotterdam Erasmusbrug → ~(92000, 437000)."""
        x, y = client.wgs84_to_rd(51.9093, 4.4864)
        assert abs(x - 92000) < 1500
        assert abs(y - 437000) < 1500

    def test_maastricht_vrijthof(self, client: KadasterClient) -> None:
        """Maastricht Vrijthof → ~(176000, 318000)."""
        x, y = client.wgs84_to_rd(50.8492, 5.6885)
        assert abs(x - 176000) < 1500
        assert abs(y - 318000) < 1500

    def test_groningen_martinitoren(self, client: KadasterClient) -> None:
        """Groningen Martinitoren → ~(233000, 582000)."""
        x, y = client.wgs84_to_rd(53.2194, 6.5665)
        assert abs(x - 233000) < 1500
        assert abs(y - 582000) < 1500

    def test_return_type_is_float_tuple(self, client: KadasterClient) -> None:
        """Resultaat is tuple van floats."""
        result = client.wgs84_to_rd(52.0, 5.0)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], float)
        assert isinstance(result[1], float)


class TestRdToWgs84:
    """RD → WGS84 conversie met bekende referentiepunten."""

    def test_amersfoort_origin(self, client: KadasterClient) -> None:
        """RD oorsprong (155000, 463000) → ~(52.155, 5.387)."""
        lat, lon = client.rd_to_wgs84(155000, 463000)
        assert abs(lat - 52.155) < 0.01
        assert abs(lon - 5.387) < 0.01

    def test_amsterdam(self, client: KadasterClient) -> None:
        """RD (121000, 487000) → ~Amsterdam."""
        lat, lon = client.rd_to_wgs84(121000, 487000)
        assert 52.3 < lat < 52.5
        assert 4.8 < lon < 5.0

    def test_return_type_is_float_tuple(self, client: KadasterClient) -> None:
        """Resultaat is tuple van (lat, lon) floats."""
        result = client.rd_to_wgs84(155000, 463000)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], float)
        assert isinstance(result[1], float)


class TestRoundTrip:
    """Heen-en-terug conversie nauwkeurigheid."""

    @pytest.mark.parametrize(
        "lat,lon",
        [
            (52.3730, 4.8932),   # Amsterdam
            (51.9093, 4.4864),   # Rotterdam
            (52.0975, 4.2200),   # Kijkduin
            (50.8492, 5.6885),   # Maastricht
            (53.2194, 6.5665),   # Groningen
        ],
    )
    def test_wgs84_rd_wgs84_roundtrip(
        self, client: KadasterClient, lat: float, lon: float
    ) -> None:
        """WGS84 → RD → WGS84 roundtrip nauwkeurigheid <0.0001°."""
        x, y = client.wgs84_to_rd(lat, lon)
        lat2, lon2 = client.rd_to_wgs84(x, y)
        assert abs(lat2 - lat) < 0.0001
        assert abs(lon2 - lon) < 0.0001

    @pytest.mark.parametrize(
        "x,y",
        [
            (155000, 463000),   # Amersfoort
            (121000, 487000),   # Amsterdam
            (92000, 437000),    # Rotterdam
        ],
    )
    def test_rd_wgs84_rd_roundtrip(
        self, client: KadasterClient, x: float, y: float
    ) -> None:
        """RD → WGS84 → RD roundtrip nauwkeurigheid <0.01m."""
        lat, lon = client.rd_to_wgs84(x, y)
        x2, y2 = client.wgs84_to_rd(lat, lon)
        assert abs(x2 - x) < 0.01
        assert abs(y2 - y) < 0.01
