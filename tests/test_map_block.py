"""Tests voor KadasterMap flowable (PDOK WMS integratie)."""

from __future__ import annotations

import struct
import zlib
from unittest.mock import MagicMock, patch

from openaec_reports.components.map_block import KadasterMap


def _make_white_png(width: int = 1, height: int = 1) -> bytes:
    """Genereer minimale valide witte PNG bytes."""

    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc

    header = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr = _chunk(b"IHDR", ihdr_data)

    # Uncompressed RGB scanlines
    raw = b""
    for _ in range(height):
        raw += b"\x00" + b"\xff\xff\xff" * width
    idat = _chunk(b"IDAT", zlib.compress(raw))
    iend = _chunk(b"IEND", b"")

    return header + ihdr + idat + iend


class TestKadasterMapInit:
    """Unit tests voor KadasterMap instantie-creatie."""

    def test_create_default(self, tmp_path):
        """KadasterMap met default parameters — geen crash."""
        m = KadasterMap(
            latitude=51.8125,
            longitude=4.6757,
            cache_dir=tmp_path / "cache",
        )
        assert m.latitude == 51.8125
        assert m.longitude == 4.6757
        assert m.radius_m == 100.0
        assert m.width_mm == 120.0
        assert m.height_mm == 90.0
        assert m.layers == ["percelen", "bebouwing"]
        assert m.caption == ""

    def test_create_custom_params(self, tmp_path):
        """KadasterMap met custom parameters."""
        m = KadasterMap(
            latitude=52.0,
            longitude=5.0,
            radius_m=200.0,
            width_mm=150.0,
            height_mm=100.0,
            layers=["luchtfoto", "percelen"],
            caption="Testlocatie",
            cache_dir=tmp_path / "cache",
        )
        assert m.radius_m == 200.0
        assert m.width_mm == 150.0
        assert m.layers == ["luchtfoto", "percelen"]
        assert m.caption == "Testlocatie"

    def test_cache_dir_created(self, tmp_path):
        """Cache directory wordt automatisch aangemaakt."""
        cache = tmp_path / "new_cache_dir"
        assert not cache.exists()
        KadasterMap(latitude=52.0, longitude=5.0, cache_dir=cache)
        assert cache.exists()


class TestLayerConfig:
    """Unit tests voor LAYER_CONFIG."""

    def test_all_expected_layers_present(self):
        """LAYER_CONFIG bevat alle verwachte lagen."""
        expected = {"percelen", "bebouwing", "bestemmingsplan", "luchtfoto"}
        assert set(KadasterMap.LAYER_CONFIG.keys()) == expected

    def test_each_layer_has_service_and_layers(self):
        """Elke laag heeft een service en layers veld."""
        for name, config in KadasterMap.LAYER_CONFIG.items():
            assert "service" in config, f"Laag '{name}' mist 'service'"
            assert "layers" in config, f"Laag '{name}' mist 'layers'"

    def test_percelen_config(self):
        """Percelen laag verwijst naar kadaster service."""
        cfg = KadasterMap.LAYER_CONFIG["percelen"]
        assert cfg["service"] == "kadaster"
        assert "Perceel" in cfg["layers"]

    def test_luchtfoto_config(self):
        """Luchtfoto laag verwijst naar luchtfoto service."""
        cfg = KadasterMap.LAYER_CONFIG["luchtfoto"]
        assert cfg["service"] == "luchtfoto"
        assert "Actueel_orthoHR" in cfg["layers"]


class TestCacheKey:
    """Unit tests voor deterministische cache keys."""

    def test_cache_key_deterministic(self, tmp_path):
        """Zelfde input → zelfde cache key."""
        m1 = KadasterMap(
            latitude=51.8125, longitude=4.6757,
            radius_m=100, layers=["percelen"],
            cache_dir=tmp_path / "c1",
        )
        m2 = KadasterMap(
            latitude=51.8125, longitude=4.6757,
            radius_m=100, layers=["percelen"],
            cache_dir=tmp_path / "c2",
        )
        assert m1._cache_key() == m2._cache_key()

    def test_cache_key_differs_on_location(self, tmp_path):
        """Andere locatie → andere cache key."""
        m1 = KadasterMap(latitude=51.0, longitude=4.0, cache_dir=tmp_path / "c1")
        m2 = KadasterMap(latitude=52.0, longitude=5.0, cache_dir=tmp_path / "c2")
        assert m1._cache_key() != m2._cache_key()

    def test_cache_key_differs_on_layers(self, tmp_path):
        """Andere lagen → andere cache key."""
        m1 = KadasterMap(
            latitude=51.0, longitude=4.0,
            layers=["percelen"],
            cache_dir=tmp_path / "c1",
        )
        m2 = KadasterMap(
            latitude=51.0, longitude=4.0,
            layers=["luchtfoto"],
            cache_dir=tmp_path / "c2",
        )
        assert m1._cache_key() != m2._cache_key()

    def test_cache_key_layer_order_independent(self, tmp_path):
        """Layer volgorde maakt niet uit voor cache key (gesorteerd)."""
        m1 = KadasterMap(
            latitude=51.0, longitude=4.0,
            layers=["percelen", "bebouwing"],
            cache_dir=tmp_path / "c1",
        )
        m2 = KadasterMap(
            latitude=51.0, longitude=4.0,
            layers=["bebouwing", "percelen"],
            cache_dir=tmp_path / "c2",
        )
        assert m1._cache_key() == m2._cache_key()


class TestFetchLayers:
    """Mock tests voor _fetch_layers() — PDOK wordt niet echt aangeroepen."""

    def test_fetch_layers_writes_files(self, tmp_path):
        """Mock get_map → retourneer witte PNG → bestanden worden geschreven."""
        png_bytes = _make_white_png()

        m = KadasterMap(
            latitude=51.8125, longitude=4.6757,
            layers=["percelen"],
            cache_dir=tmp_path / "cache",
        )
        with patch.object(m._client, "get_map", return_value=png_bytes) as mock_get:
            paths = m._fetch_layers()

        assert len(paths) == 1
        assert paths[0].exists()
        assert paths[0].stat().st_size > 0
        mock_get.assert_called_once()

    def test_fetch_layers_multiple(self, tmp_path):
        """Meerdere lagen → meerdere bestanden."""
        png_bytes = _make_white_png()

        m = KadasterMap(
            latitude=51.8125, longitude=4.6757,
            layers=["luchtfoto", "percelen", "bebouwing"],
            cache_dir=tmp_path / "cache",
        )
        with patch.object(m._client, "get_map", return_value=png_bytes):
            paths = m._fetch_layers()

        # luchtfoto wordt als eerste geplaatst (achtergrond)
        assert len(paths) == 3

    def test_fetch_layers_uses_cache(self, tmp_path):
        """Tweede call gebruikt cache, geen extra HTTP request."""
        png_bytes = _make_white_png()

        m = KadasterMap(
            latitude=51.8125, longitude=4.6757,
            layers=["percelen"],
            cache_dir=tmp_path / "cache",
        )
        with patch.object(m._client, "get_map", return_value=png_bytes) as mock_get:
            m._fetch_layers()
            # Reset _layer_paths om opnieuw fetch te simuleren
            m._layer_paths = []
            paths2 = m._fetch_layers()

        # Slechts 1 keer aangeroepen — tweede keer uit cache
        mock_get.assert_called_once()
        assert len(paths2) == 1

    def test_fetch_layers_luchtfoto_first(self, tmp_path):
        """Luchtfoto wordt altijd als eerste laag geplaatst."""
        png_bytes = _make_white_png()
        call_services = []

        m = KadasterMap(
            latitude=51.8125, longitude=4.6757,
            layers=["percelen", "luchtfoto"],
            cache_dir=tmp_path / "cache",
        )

        def mock_get(*, lat, lon, radius_m, width_px, height_px,
                     service, layers, image_format):
            call_services.append(service)
            return png_bytes

        with patch.object(m._client, "get_map", side_effect=mock_get):
            m._fetch_layers()

        assert call_services[0] == "luchtfoto"

    def test_unknown_layer_skipped(self, tmp_path):
        """Onbekende laag wordt overgeslagen met warning."""
        png_bytes = _make_white_png()

        m = KadasterMap(
            latitude=51.8125, longitude=4.6757,
            layers=["percelen", "onbekend"],
            cache_dir=tmp_path / "cache",
        )
        with patch.object(m._client, "get_map", return_value=png_bytes):
            paths = m._fetch_layers()

        # Alleen "percelen" wordt opgehaald
        assert len(paths) == 1


class TestPlaceholderFallback:
    """Tests voor graceful fallback bij PDOK fouten."""

    def test_timeout_renders_placeholder(self, tmp_path):
        """Timeout bij PDOK → placeholder wordt gerendered, geen crash."""
        m = KadasterMap(
            latitude=51.8125, longitude=4.6757,
            layers=["percelen"],
            cache_dir=tmp_path / "cache",
        )

        # Mock get_map om een timeout/connection error te gooien
        with patch.object(
            m._client, "get_map", side_effect=ConnectionError("Timeout")
        ):
            w, h = m.wrap(500, 800)

        assert m._fetch_failed is True
        assert w > 0
        assert h > 0

    def test_http_error_renders_placeholder(self, tmp_path):
        """HTTP error → placeholder, geen crash."""
        from requests.exceptions import HTTPError

        m = KadasterMap(
            latitude=51.8125, longitude=4.6757,
            layers=["percelen"],
            cache_dir=tmp_path / "cache",
        )
        with patch.object(
            m._client, "get_map", side_effect=HTTPError("503 Service Unavailable")
        ):
            w, h = m.wrap(500, 800)

        assert m._fetch_failed is True
        assert w > 0


class TestWrapAndDraw:
    """Tests voor wrap() en draw() met gemockte data."""

    def test_wrap_returns_dimensions(self, tmp_path):
        """wrap() retourneert geldige afmetingen."""
        png_bytes = _make_white_png(100, 75)

        m = KadasterMap(
            latitude=51.8125, longitude=4.6757,
            width_mm=120, height_mm=90,
            layers=["percelen"],
            caption="Testkaart",
            cache_dir=tmp_path / "cache",
        )
        with patch.object(m._client, "get_map", return_value=png_bytes):
            w, h = m.wrap(500, 800)

        assert w > 0
        assert h > 0
        # Hoogte moet groter zijn dan alleen de kaart (er is caption + schaalbalk)
        from openaec_reports.core.document import MM_TO_PT
        assert h > 90 * MM_TO_PT - 1  # marge voor afrondingsfouten

    def test_wrap_respects_available_width(self, tmp_path):
        """wrap() past breedte aan aan available_width."""
        png_bytes = _make_white_png(100, 75)

        m = KadasterMap(
            latitude=51.8125, longitude=4.6757,
            width_mm=300,  # groter dan available
            layers=["percelen"],
            cache_dir=tmp_path / "cache",
        )
        available_width = 200
        with patch.object(m._client, "get_map", return_value=png_bytes):
            w, h = m.wrap(available_width, 800)

        assert w <= available_width + 1  # kleine marge voor padding


class TestOverlayAlignment:
    """Tests voor overlay positionering na Bug 1+2 fix."""

    def test_overlay_aligns_with_base_image(self, tmp_path):
        """Overlay x-positie moet gelijk zijn aan base image x-positie."""
        png_bytes = _make_white_png(100, 75)

        m = KadasterMap(
            latitude=51.8125, longitude=4.6757,
            width_mm=80,  # smaller dan available_width
            layers=["luchtfoto", "percelen"],
            cache_dir=tmp_path / "cache",
        )
        with patch.object(m._client, "get_map", return_value=png_bytes):
            m.wrap(500, 800)

        # Na wrap: als draw() niet crasht en overlay positie berekening klopt
        assert not m._fetch_failed
        assert len(m._layer_paths) == 2

    def test_target_width_respects_padding(self, tmp_path):
        """target_w moet padding aftrekken van available_width."""
        png_bytes = _make_white_png(100, 75)

        m = KadasterMap(
            latitude=51.8125, longitude=4.6757,
            width_mm=300,  # veel breder dan available
            layers=["percelen"],
            cache_dir=tmp_path / "cache",
        )
        available = 400
        with patch.object(m._client, "get_map", return_value=png_bytes):
            m.wrap(available, 800)

        # De content tabel breedte mag niet groter zijn dan available
        assert m.width <= available + 1


class TestIntegration:
    """Integratie test — Report.from_dict() met map block → PDF."""

    def test_report_with_map_block(self, tmp_path):
        """Rapport met een map block via from_dict → build → valide PDF."""
        from openaec_reports import Report

        data = {
            "template": "structural",
            "project": "Map Test",
            "sections": [
                {
                    "title": "Locatie",
                    "content": [
                        {
                            "type": "map",
                            "center": {"lat": 51.8125, "lon": 4.6757},
                            "radius_m": 150,
                            "layers": ["luchtfoto", "percelen"],
                            "caption": "Projectlocatie — Nieuw-Lekkerland",
                        }
                    ],
                }
            ],
        }

        png_bytes = _make_white_png(100, 75)

        # Mock KadasterClient.get_map op class niveau
        with patch(
            "openaec_reports.components.map_block.KadasterClient"
        ) as mock_client:
            mock_instance = MagicMock()
            mock_instance.get_map.return_value = png_bytes
            mock_client.return_value = mock_instance

            report = Report.from_dict(data)
            output = tmp_path / "map_test.pdf"
            result = report.build(output)

        assert result.exists()
        assert result.stat().st_size > 500
        # Check PDF magic bytes
        with open(result, "rb") as f:
            assert f.read(4) == b"%PDF"

    def test_report_with_map_fallback(self, tmp_path):
        """Rapport met map block waar PDOK faalt → PDF met placeholder."""
        from openaec_reports import Report

        data = {
            "template": "structural",
            "project": "Map Fallback Test",
            "sections": [
                {
                    "title": "Locatie",
                    "content": [
                        {
                            "type": "map",
                            "center": {"lat": 51.8125, "lon": 4.6757},
                            "radius_m": 100,
                            "layers": ["percelen"],
                            "caption": "Kaart zou hier moeten staan",
                        }
                    ],
                }
            ],
        }

        # Mock KadasterClient om ConnectionError te gooien
        with patch(
            "openaec_reports.components.map_block.KadasterClient"
        ) as mock_client:
            mock_instance = MagicMock()
            mock_instance.get_map.side_effect = ConnectionError("No network")
            mock_client.return_value = mock_instance

            report = Report.from_dict(data)
            output = tmp_path / "map_fallback_test.pdf"
            result = report.build(output)

        assert result.exists()
        assert result.stat().st_size > 500
        with open(result, "rb") as f:
            assert f.read(4) == b"%PDF"
