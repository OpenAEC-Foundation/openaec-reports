"""
Map Generator — fetches map images from PDOK services.

Uses:
- WMTS tiles for BRT Achtergrondkaart (standaard, grijs, pastel, water)
- WMS for Luchtfoto and Kadastrale kaart

Supports:
- Address geocoding via PDOK Locatieserver
- Multiple map layers
- Configurable zoom, size
- Returns PIL Image or saves to file
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
# Service configuration
# ---------------------------------------------------------------------------
PDOK_SERVICES: dict[str, dict[str, Any]] = {
    "brt": {
        "name": "BRT Achtergrondkaart",
        "type": "wmts",
        "url_template": "https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:3857/{z}/{x}/{y}.png",
        "caption": "Topografische kaart (PDOK BRT)",
    },
    "brt_grijs": {
        "name": "BRT Achtergrondkaart Grijs",
        "type": "wmts",
        "url_template": "https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/grijs/EPSG:3857/{z}/{x}/{y}.png",
        "caption": "Topografische kaart grijs (PDOK BRT)",
    },
    "brt_pastel": {
        "name": "BRT Achtergrondkaart Pastel",
        "type": "wmts",
        "url_template": "https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/pastel/EPSG:3857/{z}/{x}/{y}.png",
        "caption": "Topografische kaart pastel (PDOK BRT)",
    },
    "brt_water": {
        "name": "BRT Achtergrondkaart Water",
        "type": "wmts",
        "url_template": "https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/water/EPSG:3857/{z}/{x}/{y}.png",
        "caption": "Topografische kaart water (PDOK BRT)",
    },
    "luchtfoto": {
        "name": "Luchtfoto (meest recent)",
        "type": "wms",
        "url": "https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0",
        "layers": "Actueel_orthoHR",
        "caption": "Luchtfoto (PDOK)",
    },
    "kadastraal": {
        "name": "Kadastrale kaart",
        "type": "wms",
        "url": "https://service.pdok.nl/kadaster/kadastralekaart/wms/v5_0",
        "layers": "Kadastralekaart",
        "caption": "Kadastrale kaart (PDOK Kadaster)",
    },
}

PDOK_GEOCODER_URL = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free"

DEFAULT_ZOOM = 16
DEFAULT_WIDTH_PX = 1200
DEFAULT_HEIGHT_PX = 800
DEFAULT_LAYERS = ["brt"]
TILE_SIZE = 256  # WMTS standard tile size


# ---------------------------------------------------------------------------
# Coordinate math
# ---------------------------------------------------------------------------

def _lat_lon_to_tile(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    """Convert lat/lon to Web Mercator tile x, y at given zoom."""
    n = 2 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


def _tile_to_lat_lon(x: int, y: int, zoom: int) -> tuple[float, float]:
    """Convert tile x, y to lat/lon of tile's NW corner."""
    n = 2 ** zoom
    lon = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat = math.degrees(lat_rad)
    return lat, lon


def _lat_lon_to_pixel(lat: float, lon: float, zoom: int) -> tuple[float, float]:
    """Convert lat/lon to global pixel coordinates at given zoom."""
    n = 2 ** zoom
    px_x = (lon + 180.0) / 360.0 * n * TILE_SIZE
    lat_rad = math.radians(lat)
    px_y = (1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n * TILE_SIZE
    return px_x, px_y


def _lat_lon_to_bbox_wms(
    lat: float, lon: float, zoom: int,
    width_px: int, height_px: int,
) -> tuple[float, float, float, float]:
    """Calculate WMS bounding box from center lat/lon and zoom level.
    Returns (minlon, minlat, maxlon, maxlat) in EPSG:4326.
    """
    meters_per_px = 156543.03 * math.cos(math.radians(lat)) / (2 ** zoom)
    half_w = (width_px / 2) * meters_per_px
    half_h = (height_px / 2) * meters_per_px
    dlat = half_h / 111320.0
    dlon = half_w / (111320.0 * math.cos(math.radians(lat)))
    return (lon - dlon, lat - dlat, lon + dlon, lat + dlat)


# ---------------------------------------------------------------------------
# MapGenerator
# ---------------------------------------------------------------------------

class MapGenerator:
    """Generates map images from PDOK services."""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "3BM-ReportGenerator/1.0",
        })

    def geocode(self, address: str) -> dict[str, Any] | None:
        """Geocode a Dutch address using PDOK Locatieserver."""
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
            centroid = doc.get("centroide_ll", "")
            if centroid.startswith("POINT("):
                coords = centroid[6:-1].split()
                lon, lat = float(coords[0]), float(coords[1])
            else:
                return None

            return {
                "lat": lat,
                "lon": lon,
                "display_name": doc.get("weergavenaam", address),
                "type": doc.get("type", ""),
            }
        except Exception as e:
            logger.error("Geocoding failed for '%s': %s", address, e)
            return None

    # --- WMTS tile stitching ---

    def fetch_wmts_image(
        self,
        service_key: str,
        lat: float, lon: float,
        zoom: int = DEFAULT_ZOOM,
        width_px: int = DEFAULT_WIDTH_PX,
        height_px: int = DEFAULT_HEIGHT_PX,
    ) -> Image.Image | None:
        """Fetch and stitch WMTS tiles into a single image centered on lat/lon."""
        service = PDOK_SERVICES.get(service_key)
        if not service or service["type"] != "wmts":
            return None

        url_template = service["url_template"]

        # Calculate center pixel
        center_px, center_py = _lat_lon_to_pixel(lat, lon, zoom)

        # Calculate tile range needed
        left_px = center_px - width_px / 2
        top_px = center_py - height_px / 2
        right_px = center_px + width_px / 2
        bottom_px = center_py + height_px / 2

        tile_x_min = int(left_px // TILE_SIZE)
        tile_y_min = int(top_px // TILE_SIZE)
        tile_x_max = int(right_px // TILE_SIZE)
        tile_y_max = int(bottom_px // TILE_SIZE)

        # Create canvas for all tiles
        canvas_w = (tile_x_max - tile_x_min + 1) * TILE_SIZE
        canvas_h = (tile_y_max - tile_y_min + 1) * TILE_SIZE
        canvas = Image.new("RGB", (canvas_w, canvas_h), (240, 240, 240))

        # Fetch and paste each tile
        for tx in range(tile_x_min, tile_x_max + 1):
            for ty in range(tile_y_min, tile_y_max + 1):
                url = url_template.format(z=zoom, x=tx, y=ty)
                try:
                    resp = self.session.get(url, timeout=self.timeout)
                    if resp.status_code == 200 and "image" in resp.headers.get("Content-Type", ""):
                        tile_img = Image.open(BytesIO(resp.content))
                        paste_x = (tx - tile_x_min) * TILE_SIZE
                        paste_y = (ty - tile_y_min) * TILE_SIZE
                        canvas.paste(tile_img, (paste_x, paste_y))
                except Exception as e:
                    logger.warning("Tile fetch failed %s: %s", url, e)

        # Crop to exact desired area
        offset_x = int(left_px - tile_x_min * TILE_SIZE)
        offset_y = int(top_px - tile_y_min * TILE_SIZE)
        cropped = canvas.crop((offset_x, offset_y, offset_x + width_px, offset_y + height_px))

        return cropped

    # --- WMS fetch ---

    def fetch_wms_image(
        self,
        service_key: str,
        bbox: tuple[float, float, float, float],
        width_px: int = DEFAULT_WIDTH_PX,
        height_px: int = DEFAULT_HEIGHT_PX,
    ) -> Image.Image | None:
        """Fetch a WMS map image."""
        service = PDOK_SERVICES.get(service_key)
        if not service or service["type"] != "wms":
            return None

        params = {
            "SERVICE": "WMS",
            "VERSION": "1.3.0",
            "REQUEST": "GetMap",
            "LAYERS": service["layers"],
            "CRS": "EPSG:4326",
            "BBOX": f"{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}",  # WMS 1.3.0: lat,lon order
            "WIDTH": width_px,
            "HEIGHT": height_px,
            "FORMAT": "image/png",
            "STYLES": "",
        }

        try:
            resp = self.session.get(service["url"], params=params, timeout=self.timeout)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            if "image" not in content_type:
                logger.error("WMS returned non-image: %s", content_type)
                return None
            img = Image.open(BytesIO(resp.content))
            return img.convert("RGB")
        except Exception as e:
            logger.error("WMS fetch failed for %s: %s", service_key, e)
            return None

    # --- Unified fetch ---

    def fetch_map_image(
        self,
        service_key: str,
        lat: float, lon: float,
        zoom: int = DEFAULT_ZOOM,
        width_px: int = DEFAULT_WIDTH_PX,
        height_px: int = DEFAULT_HEIGHT_PX,
    ) -> Image.Image | None:
        """Fetch a map image using the appropriate method (WMTS or WMS)."""
        service = PDOK_SERVICES.get(service_key)
        if not service:
            logger.error("Unknown map service: %s", service_key)
            return None

        if service["type"] == "wmts":
            return self.fetch_wmts_image(service_key, lat, lon, zoom, width_px, height_px)
        else:
            bbox = _lat_lon_to_bbox_wms(lat, lon, zoom, width_px, height_px)
            return self.fetch_wms_image(service_key, bbox, width_px, height_px)

    # --- Public API ---

    def generate_maps(
        self,
        address: str,
        layers: list[str] | None = None,
        zoom: int = DEFAULT_ZOOM,
        width_px: int = DEFAULT_WIDTH_PX,
        height_px: int = DEFAULT_HEIGHT_PX,
    ) -> list[dict[str, Any]]:
        """Generate map images from address."""
        geo = self.geocode(address)
        if not geo:
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
        """Generate map images from coordinates."""
        if not layers:
            layers = DEFAULT_LAYERS

        results = []

        for layer_key in layers:
            service = PDOK_SERVICES.get(layer_key)
            if not service:
                logger.warning("Unknown layer: %s, skipping", layer_key)
                continue

            img = self.fetch_map_image(layer_key, lat, lon, zoom, width_px, height_px)
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
