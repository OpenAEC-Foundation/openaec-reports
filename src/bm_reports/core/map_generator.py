"""
Map Generator — fetches map images from PDOK WMS services.

Supports:
- Address geocoding via PDOK Locatieserver
- Multiple map layers: topografie, luchtfoto, kadastrale kaart
- Configurable zoom, size, and bounding box
- Returns PIL Image or saves to file

Usage:
    gen = MapGenerator()
    # From address
    images = gen.generate_maps("Kijkduin 1, Den Haag", layers=["brt", "luchtfoto"])
    # From coordinates
    images = gen.generate_maps_from_coords(52.06, 4.22, layers=["brt"])
"""
from __future__ import annotations

import logging
import math
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any

import requests
from PIL import Image

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PDOK WMS endpoints
# ---------------------------------------------------------------------------
PDOK_SERVICES = {
    "brt": {
        "name": "BRT Achtergrondkaart",
        "url": "https://service.pdok.nl/brt/achtergrondkaart/wms/v2_0",
        "layers": "standaard",
        "caption": "Topografische kaart (PDOK BRT)",
    },
    "brt_grijs": {
        "name": "BRT Achtergrondkaart Grijs",
        "url": "https://service.pdok.nl/brt/achtergrondkaart/wms/v2_0",
        "layers": "grijs",
        "caption": "Topografische kaart grijs (PDOK BRT)",
    },
    "luchtfoto": {
        "name": "Luchtfoto (meest recent)",
        "url": "https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0",
        "layers": "Actueel_orthoHR",
        "caption": "Luchtfoto (PDOK)",
    },
    "kadastraal": {
        "name": "Kadastrale kaart",
        "url": "https://service.pdok.nl/kadaster/kadastralekaart/wms/v5_0",
        "layers": "Kadastralekaart",
        "caption": "Kadastrale kaart (PDOK Kadaster)",
    },
}

# PDOK Locatieserver for geocoding
PDOK_GEOCODER_URL = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free"

# Default map settings
DEFAULT_ZOOM = 16  # ~1:5000 neighborhood level
DEFAULT_WIDTH_PX = 1200
DEFAULT_HEIGHT_PX = 800
DEFAULT_LAYERS = ["brt"]

# EPSG:28992 (Rijksdriehoek) is used by PDOK, but WMS supports EPSG:4326 too
WMS_CRS = "EPSG:4326"


def _lat_lon_to_bbox(
    lat: float, lon: float, zoom: int = DEFAULT_ZOOM,
    width_px: int = DEFAULT_WIDTH_PX, height_px: int = DEFAULT_HEIGHT_PX,
) -> tuple[float, float, float, float]:
    """Calculate WMS bounding box from center lat/lon and zoom level.

    Returns (minlon, minlat, maxlon, maxlat) in EPSG:4326.
    """
    # Approximate meters per pixel at given zoom and latitude
    meters_per_px = 156543.03 * math.cos(math.radians(lat)) / (2 ** zoom)
    half_w = (width_px / 2) * meters_per_px
    half_h = (height_px / 2) * meters_per_px

    # Convert meters to degrees (approximate)
    dlat = half_h / 111320.0
    dlon = half_w / (111320.0 * math.cos(math.radians(lat)))

    return (lon - dlon, lat - dlat, lon + dlon, lat + dlat)


class MapGenerator:
    """Generates map images from PDOK WMS services."""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "3BM-ReportGenerator/1.0",
        })

    def geocode(self, address: str) -> dict[str, Any] | None:
        """Geocode a Dutch address using PDOK Locatieserver.

        Returns dict with lat, lon, display_name or None.
        """
        try:
            resp = self.session.get(
                PDOK_GEOCODER_URL,
                params={"q": address, "rows": 1, "fl": "*"},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            docs = data.get("response", {}).get("docs", [])
            if not docs:
                logger.warning("Geocoding: no results for '%s'", address)
                return None

            doc = docs[0]
            # PDOK returns centroide_ll as "POINT(lon lat)"
            centroid = doc.get("centroide_ll", "")
            if centroid.startswith("POINT("):
                coords = centroid[6:-1].split()
                lon, lat = float(coords[0]), float(coords[1])
            else:
                logger.warning("Geocoding: unexpected centroid format: %s", centroid)
                return None

            return {
                "lat": lat,
                "lon": lon,
                "display_name": doc.get("weergavenaam", address),
                "type": doc.get("type", ""),
                "score": doc.get("score", 0),
            }
        except Exception as e:
            logger.error("Geocoding failed for '%s': %s", address, e)
            return None

    def fetch_wms_image(
        self,
        service_key: str,
        bbox: tuple[float, float, float, float],
        width_px: int = DEFAULT_WIDTH_PX,
        height_px: int = DEFAULT_HEIGHT_PX,
    ) -> Image.Image | None:
        """Fetch a single WMS map image.

        Args:
            service_key: Key from PDOK_SERVICES (e.g. "brt", "luchtfoto")
            bbox: (minlon, minlat, maxlon, maxlat) in EPSG:4326
            width_px: Image width in pixels
            height_px: Image height in pixels

        Returns:
            PIL Image or None on failure.
        """
        service = PDOK_SERVICES.get(service_key)
        if not service:
            logger.error("Unknown map service: %s", service_key)
            return None

        params = {
            "SERVICE": "WMS",
            "VERSION": "1.3.0",
            "REQUEST": "GetMap",
            "LAYERS": service["layers"],
            "CRS": WMS_CRS,
            "BBOX": f"{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}",  # WMS 1.3.0: lat,lon order
            "WIDTH": width_px,
            "HEIGHT": height_px,
            "FORMAT": "image/png",
            "STYLES": "",
        }

        try:
            resp = self.session.get(
                service["url"], params=params, timeout=self.timeout,
            )
            resp.raise_for_status()

            content_type = resp.headers.get("Content-Type", "")
            if "image" not in content_type:
                logger.error("WMS returned non-image: %s — %s", content_type, resp.text[:200])
                return None

            img = Image.open(BytesIO(resp.content))
            return img.convert("RGB")
        except Exception as e:
            logger.error("WMS fetch failed for %s: %s", service_key, e)
            return None

    def generate_maps(
        self,
        address: str,
        layers: list[str] | None = None,
        zoom: int = DEFAULT_ZOOM,
        width_px: int = DEFAULT_WIDTH_PX,
        height_px: int = DEFAULT_HEIGHT_PX,
    ) -> list[dict[str, Any]]:
        """Generate map images from address.

        Returns list of dicts: {image: PIL.Image, caption: str, path: Path}
        """
        geo = self.geocode(address)
        if not geo:
            logger.warning("Could not geocode address: %s", address)
            return []

        return self.generate_maps_from_coords(
            geo["lat"], geo["lon"],
            layers=layers, zoom=zoom,
            width_px=width_px, height_px=height_px,
            location_name=geo.get("display_name", address),
        )

    def generate_maps_from_coords(
        self,
        lat: float, lon: float,
        layers: list[str] | None = None,
        zoom: int = DEFAULT_ZOOM,
        width_px: int = DEFAULT_WIDTH_PX,
        height_px: int = DEFAULT_HEIGHT_PX,
        location_name: str = "",
    ) -> list[dict[str, Any]]:
        """Generate map images from coordinates.

        Returns list of dicts: {image: PIL.Image, caption: str, path: Path}
        """
        if not layers:
            layers = DEFAULT_LAYERS

        bbox = _lat_lon_to_bbox(lat, lon, zoom, width_px, height_px)
        results = []

        for layer_key in layers:
            service = PDOK_SERVICES.get(layer_key)
            if not service:
                logger.warning("Unknown layer: %s, skipping", layer_key)
                continue

            img = self.fetch_wms_image(layer_key, bbox, width_px, height_px)
            if not img:
                continue

            # Save to temp file
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            img.save(tmp, format="PNG")
            tmp.close()

            caption = service["caption"]
            if location_name:
                caption = f"{caption} — {location_name}"

            results.append({
                "image": img,
                "caption": caption,
                "path": Path(tmp.name),
                "layer": layer_key,
                "lat": lat,
                "lon": lon,
                "zoom": zoom,
            })

        return results
