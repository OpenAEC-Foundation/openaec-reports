"""Map block — Kadaster/situatiekaartjes via PDOK API."""

from __future__ import annotations

from pathlib import Path
from reportlab.platypus import Flowable

from bm_reports.core.document import MM_TO_PT


class KadasterMap(Flowable):
    """Kadaster kaartje flowable via PDOK WMS.

    Haalt een kaartuitsnede op van de PDOK WMS service
    en plaatst deze als afbeelding in het rapport.

    Beschikbare lagen:
    - kadastrale grenzen (perceelgrenzen)
    - perceelnummers
    - bebouwing (BAG)
    - luchtfoto (PDOK achtergrondkaart)

    Args:
        latitude: Breedtegraad (WGS84).
        longitude: Lengtegraad (WGS84).
        radius_m: Straal rondom coördinaat in meters.
        width_mm: Breedte in rapport in mm.
        height_mm: Hoogte in rapport in mm.
        layers: Lijst van gewenste lagen.
        caption: Bijschrift.
        cache_dir: Map voor gecachte kaartafbeeldingen.
    """

    PDOK_WMS_BASE = "https://service.pdok.nl/kadaster/kadastralekaart/wms/v5_0"
    PDOK_BGT_BASE = "https://service.pdok.nl/lv/bgt/wms/v1_0"
    PDOK_LUFO_BASE = "https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0"

    DEFAULT_LAYERS = ["percelen", "bebouwing"]

    def __init__(
        self,
        latitude: float,
        longitude: float,
        radius_m: float = 100.0,
        width_mm: float = 120.0,
        height_mm: float = 90.0,
        layers: list[str] | None = None,
        caption: str = "",
        cache_dir: str | Path | None = None,
    ):
        super().__init__()
        self.latitude = latitude
        self.longitude = longitude
        self.radius_m = radius_m
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.layers = layers or self.DEFAULT_LAYERS
        self.caption = caption
        self.cache_dir = Path(cache_dir) if cache_dir else None

    def _wgs84_to_rd(self, lat: float, lon: float) -> tuple[float, float]:
        """Converteer WGS84 naar Rijksdriehoekscoördinaten (EPSG:28992).

        Gebruikt een benaderende transformatie.
        Voor exacte conversie: pyproj of RDNAPTRANS™2018.
        """
        # TODO: Implementeer WGS84 → RD conversie
        # Benaderingsformule of pyproj
        raise NotImplementedError("WGS84 → RD conversie nog niet geïmplementeerd")

    def _build_wms_url(self, bbox_rd: tuple[float, float, float, float]) -> str:
        """Bouw WMS GetMap URL voor PDOK."""
        # TODO: Implementeer WMS URL builder
        raise NotImplementedError("WMS URL builder nog niet geïmplementeerd")

    def _fetch_map(self) -> Path:
        """Haal kaartafbeelding op van PDOK (met caching)."""
        # TODO: Implementeer map fetching
        # 1. Converteer lat/lon naar RD
        # 2. Bereken bbox
        # 3. Check cache
        # 4. WMS GetMap request
        # 5. Sla op als PNG
        raise NotImplementedError("Map fetching nog niet geïmplementeerd")

    def wrap(self, available_width, available_height):
        self.width = min(self.width_mm * MM_TO_PT, available_width)
        self.height = self.height_mm * MM_TO_PT
        return (self.width, self.height)

    def draw(self):
        """Render de kaart met optioneel bijschrift."""
        # TODO: Implementeer kaart rendering
        # - Fetch/cache map image
        # - Render image centered
        # - Render caption
        # - Render schaalbalkt en noordpijl
        pass
