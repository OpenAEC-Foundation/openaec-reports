"""Kadaster client — PDOK API integratie voor kadastraal kaartmateriaal."""

from __future__ import annotations

from pathlib import Path

import requests
from pyproj import Transformer


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
    Rijksdriehoek (EPSG:28992) via pyproj (nauwkeurigheid <1mm).
    """

    WMS_SERVICES = {
        "kadaster": "https://service.pdok.nl/kadaster/kadastralekaart/wms/v5_0",
        "bgt": "https://service.pdok.nl/lv/bgt/wms/v1_0",
        "luchtfoto": "https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0",
        "bag": "https://service.pdok.nl/lv/bag/wms/v2_0",
    }

    # Transformers worden eenmalig aangemaakt (thread-safe singletons)
    _wgs84_to_rd: Transformer = Transformer.from_crs("EPSG:4326", "EPSG:28992", always_xy=True)
    _rd_to_wgs84: Transformer = Transformer.from_crs("EPSG:28992", "EPSG:4326", always_xy=True)

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

        Gebruikt pyproj Transformer (EPSG:4326 → EPSG:28992).
        Nauwkeurigheid: <1mm (geodetische standaard).

        Args:
            lat: Breedtegraad (WGS84).
            lon: Lengtegraad (WGS84).

        Returns:
            Tuple (x, y) in RD coördinaten (meters).
        """
        # pyproj met always_xy=True verwacht (lon, lat)
        x, y = self._wgs84_to_rd.transform(lon, lat)
        return (x, y)

    def rd_to_wgs84(self, x: float, y: float) -> tuple[float, float]:
        """Converteer Rijksdriehoekscoördinaten naar WGS84.

        Args:
            x: RD x-coördinaat (meters).
            y: RD y-coördinaat (meters).

        Returns:
            Tuple (lat, lon) in WGS84 graden.
        """
        lon, lat = self._rd_to_wgs84.transform(x, y)
        return (lat, lon)

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
