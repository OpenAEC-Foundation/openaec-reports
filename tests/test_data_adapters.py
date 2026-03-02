"""Tests voor data adapters — kadaster.py en revit_adapter.py."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from openaec_reports.data.kadaster import KadasterClient
from openaec_reports.data.revit_adapter import RevitAdapter


class TestKadasterClient:
    def test_init_without_cache(self):
        """KadasterClient zonder cache directory."""
        client = KadasterClient()
        assert client.cache_dir is None

    def test_init_with_cache(self, tmp_path):
        """KadasterClient met cache directory."""
        cache_dir = tmp_path / "cache"
        client = KadasterClient(cache_dir=cache_dir)
        assert client.cache_dir == cache_dir
        assert cache_dir.exists()

    def test_wgs84_to_rd_amsterdam(self):
        """WGS84 → RD conversie voor Amsterdam (Centraal Station)."""
        client = KadasterClient()
        x, y = client.wgs84_to_rd(52.3791, 4.9003)
        # Amsterdam CS is rond x=121000, y=487000 in RD
        assert 118000 < x < 125000
        assert 484000 < y < 490000

    def test_wgs84_to_rd_zwijndrecht(self):
        """WGS84 → RD conversie voor Zwijndrecht (OpenAEC)."""
        client = KadasterClient()
        x, y = client.wgs84_to_rd(51.8123, 4.6407)
        # Zwijndrecht is rond x=100000, y=425000 in RD
        assert 95000 < x < 105000
        assert 420000 < y < 430000

    def test_wms_services_defined(self):
        """Alle WMS services zijn gedefinieerd."""
        assert "kadaster" in KadasterClient.WMS_SERVICES
        assert "bgt" in KadasterClient.WMS_SERVICES
        assert "luchtfoto" in KadasterClient.WMS_SERVICES
        assert "bag" in KadasterClient.WMS_SERVICES

    @patch("openaec_reports.data.kadaster.requests.Session")
    def test_get_map_builds_correct_params(self, mock_session_cls):
        """get_map() bouwt correcte WMS parameters."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.content = b"PNG_DATA"
        mock_session.get.return_value = mock_response
        mock_session_cls.return_value = mock_session

        client = KadasterClient()
        client.session = mock_session

        result = client.get_map(52.0, 4.5, radius_m=200)

        mock_session.get.assert_called_once()
        call_kwargs = mock_session.get.call_args
        params = call_kwargs[1]["params"]
        assert params["service"] == "WMS"
        assert params["request"] == "GetMap"
        assert params["crs"] == "EPSG:28992"
        assert result == b"PNG_DATA"

    @patch("openaec_reports.data.kadaster.requests.Session")
    def test_save_map(self, mock_session_cls, tmp_path):
        """save_map() slaat PNG op als bestand."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.content = b"\x89PNG_FAKE_DATA"
        mock_session.get.return_value = mock_response
        mock_session_cls.return_value = mock_session

        client = KadasterClient()
        client.session = mock_session

        output = tmp_path / "kaart.png"
        result = client.save_map(52.0, 4.5, output)

        assert result == output
        assert output.exists()
        assert output.read_bytes() == b"\x89PNG_FAKE_DATA"


class TestRevitAdapter:
    def test_init_without_doc(self):
        """RevitAdapter zonder Revit document."""
        adapter = RevitAdapter()
        assert adapter.doc is None

    def test_get_project_info_without_doc_raises(self):
        """get_project_info() zonder doc geeft RuntimeError."""
        adapter = RevitAdapter()
        with pytest.raises(RuntimeError, match="Geen Revit document"):
            adapter.get_project_info()

    def test_get_structural_elements_not_implemented(self):
        """get_structural_elements() is niet geimplementeerd."""
        adapter = RevitAdapter()
        with pytest.raises(NotImplementedError):
            adapter.get_structural_elements()

    def test_get_rooms_not_implemented(self):
        """get_rooms() is niet geimplementeerd."""
        adapter = RevitAdapter()
        with pytest.raises(NotImplementedError):
            adapter.get_rooms()

    def test_from_json(self, tmp_path):
        """from_json() laadt data uit JSON bestand."""
        data = {"source": "revit", "project_info": {"project": "Test"}}
        f = tmp_path / "revit_export.json"
        f.write_text(json.dumps(data))

        adapter = RevitAdapter.from_json(f)
        assert adapter._data["source"] == "revit"
        assert adapter.doc is None

    def test_export_to_json_without_doc_raises(self, tmp_path):
        """export_to_json() zonder doc geeft error (via get_project_info)."""
        adapter = RevitAdapter()
        output = tmp_path / "export.json"
        with pytest.raises(RuntimeError):
            adapter.export_to_json(output)
