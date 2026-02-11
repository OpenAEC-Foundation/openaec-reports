"""Kadaster client — PDOK API integratie voor kadastraal kaartmateriaal."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import requests


class KadasterClient:
    """Client voor PDOK WMS services.

    Haalt kadastraal kaartmateriaal op via de gratis PDOK API.
    Geen API key vereist.

    Beschikbare services:
    - Kadastrale kaart (perceelgrenzen, nummers)
    - BAG (bebouwing)
    - Luchtfoto
    - BGT (Basisregistratie Grootschalige Topografie)

    Coördinaten worden intern geconverteerd van WGS84 naar
    Rijksdriehoek (EPSG:28992) voor de WMS requests.
    """

    WMS_SERVICES = {
        "kadaster": "https://service.pdok.nl/kadaster/kadastralekaart/wms/v5_0",
        "bgt": "https://service.pdok.nl/lv/bgt/wms/v1_0",
        "luchtfoto": "https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0",
        "bag": "https://service.pdok.nl/lv/bag/wms/v2_0",
    }

    def __init__(self, cache_dir: str | Path | None = None):
        """Initialiseer Kadaster client.

        Args:
            cache_dir: Map voor gecachte kaartafbeeldingen.
                       None = geen caching.
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()

    def wgs84_to_rd(self, lat: float, lon: float) -> tuple[float, float]:
        """Converteer WGS84 naar Rijksdriehoekscoördinaten.

        Gebruikt benaderende transformatie.
        Nauwkeurigheid: ~1m (voldoende voor kaartjes).

        Args:
            lat: Breedtegraad (WGS84).
            lon: Lengtegraad (WGS84).

        Returns:
            Tuple (x, y) in RD coördinaten (meters).
        """
        # Benadering op basis van 2 referentiepunten
        # Bron: https://www.kadaster.nl/zakelijk/registraties/basisregistraties/rijksdriehoeksmeting
        # TODO: Implementeer nauwkeuriger met pyproj of RDNAPTRANS
        d_lat = 0.36 * (lat - 52.15517440)
        d_lon = 0.36 * (lon - 5.38720621)

        x = 155000 + (190094.945 * d_lon) + (-11832.228 * d_lat * d_lon)
        y = 463000 + (309056.544 * d_lat) + (3638.893 * d_lon * d_lon)

        return (x, y)

    def get_map(
        self,
        lat: float,
        lon: float,
        radius_m: float = 100.0,
        width_px: int = 800,
        height_px: int = 600,
        service: str = "kadaster",
        layers: str = "Perceel,OpenbareRuimteNaam",
        image_format: str = "image/png",
    ) -> bytes:
        """Haal kaartafbeelding op via WMS GetMap.

        Args:
            lat: Breedtegraad (WGS84).
            lon: Lengtegraad (WGS84).
            radius_m: Straal rondom punt in meters.
            width_px: Breedte in pixels.
            height_px: Hoogte in pixels.
            service: WMS service naam (kadaster, bgt, luchtfoto, bag).
            layers: Komma-gescheiden laagnamen.
            image_format: Output formaat.

        Returns:
            PNG image bytes.
        """
        x, y = self.wgs84_to_rd(lat, lon)
        bbox = f"{x - radius_m},{y - radius_m},{x + radius_m},{y + radius_m}"

        params = {
            "service": "WMS",
            "version": "1.3.0",
            "request": "GetMap",
            "layers": layers,
            "crs": "EPSG:28992",
            "bbox": bbox,
            "width": width_px,
            "height": height_px,
            "format": image_format,
            "transparent": "true",
        }

        url = self.WMS_SERVICES.get(service, service)
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()

        return response.content

    def save_map(
        self,
        lat: float,
        lon: float,
        output_path: str | Path,
        **kwargs,
    ) -> Path:
        """Haal kaart op en sla op als bestand.

        Args:
            lat: Breedtegraad.
            lon: Lengtegraad.
            output_path: Pad voor output PNG.
            **kwargs: Doorgeven aan get_map().

        Returns:
            Path naar opgeslagen bestand.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        image_data = self.get_map(lat, lon, **kwargs)
        path.write_bytes(image_data)

        return path
