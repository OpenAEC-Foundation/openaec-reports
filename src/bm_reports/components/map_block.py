"""Map block — Kadaster/situatiekaartjes via PDOK WMS."""

from __future__ import annotations

import hashlib
import logging
import tempfile
import time
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Flowable, Paragraph, Table, TableStyle

from bm_reports.core.document import MM_TO_PT
from bm_reports.core.styles import BM_COLORS, BM_FONTS, BM_STYLES
from bm_reports.data.kadaster import KadasterClient

logger = logging.getLogger(__name__)

# Maximum cache leeftijd in seconden (24 uur)
_CACHE_MAX_AGE = 24 * 60 * 60

# Module-level styles (voorkom naam-conflicten bij multi-pass builds)
_STYLE_MAP_SCALE = ParagraphStyle(
    "_map_scale",
    parent=BM_STYLES["Caption"],
    fontSize=BM_FONTS.caption_size,
    textColor=HexColor(BM_COLORS.text_light),
)

_STYLE_MAP_PLACEHOLDER = ParagraphStyle(
    "_map_placeholder",
    parent=BM_STYLES["Normal"],
    fontName=BM_FONTS.body,
    fontSize=BM_FONTS.body_size,
    textColor=HexColor(BM_COLORS.text_light),
)


class KadasterMap(Flowable):
    """Kadaster kaartje flowable via PDOK WMS.

    Haalt kaartuitsnedes op van PDOK WMS services en rendert ze
    als gestapelde lagen op het ReportLab canvas. Gebruikt
    KadasterClient voor de WMS communicatie.

    Beschikbare lagen:
    - percelen (kadastrale grenzen + straatnamen)
    - bebouwing (BAG panden)
    - luchtfoto (actuele luchtfoto)
    - bestemmingsplan (placeholder — nog niet beschikbaar)

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

    LAYER_CONFIG: dict[str, dict[str, str]] = {
        "percelen": {
            "service": "kadaster",
            "layers": "Perceel,OpenbareRuimteNaam",
        },
        "bebouwing": {
            "service": "bag",
            "layers": "pand",
        },
        "bestemmingsplan": {
            "service": "kadaster",
            "layers": "Perceel",
        },
        "luchtfoto": {
            "service": "luchtfoto",
            "layers": "Actueel_orthoHR",
        },
    }

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
        self.layers = layers or list(self.DEFAULT_LAYERS)
        self.caption = caption

        default_cache = Path(tempfile.gettempdir()) / "bm_maps"
        self._cache_dir = Path(cache_dir) if cache_dir else default_cache
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        self._client = KadasterClient(cache_dir=self._cache_dir)

        # Bereken pixel dimensies (150 DPI equivalent)
        self._width_px = max(int(self.width_mm * 150 / 25.4), 100)
        self._height_px = max(int(self.height_mm * 150 / 25.4), 100)

        # Layer images worden gevuld tijdens wrap()
        self._layer_paths: list[Path] = []
        self._fetch_failed = False

    def _cache_key(self) -> str:
        """Genereer deterministische cache key op basis van parameters."""
        raw = (
            f"{self.latitude}:{self.longitude}:{self.radius_m}"
            f":{sorted(self.layers)}:{self._width_px}:{self._height_px}"
        )
        return hashlib.md5(raw.encode()).hexdigest()

    def _get_cached(self, layer_name: str) -> Path | None:
        """Check of een gecachte laag bestaat en niet verlopen is.

        Args:
            layer_name: Naam van de laag.

        Returns:
            Path naar cached bestand, of None als niet beschikbaar.
        """
        key = self._cache_key()
        cache_path = self._cache_dir / f"map_{key}_{layer_name}.png"
        if cache_path.exists():
            age = time.time() - cache_path.stat().st_mtime
            if age < _CACHE_MAX_AGE:
                return cache_path
        return None

    def _fetch_layers(self) -> list[Path]:
        """Haal per laag een PNG op van PDOK (met caching).

        Returns:
            Lijst van Paths naar PNG bestanden, in laagvolgorde.
        """
        paths: list[Path] = []
        key = self._cache_key()

        # Sorteer lagen: luchtfoto eerst (achtergrond), dan overlays
        ordered = []
        if "luchtfoto" in self.layers:
            ordered.append("luchtfoto")
        for layer in self.layers:
            if layer != "luchtfoto":
                ordered.append(layer)

        for layer_name in ordered:
            config = self.LAYER_CONFIG.get(layer_name)
            if config is None:
                logger.warning("Onbekende kaartlaag: %s — overgeslagen", layer_name)
                continue

            # Check cache
            cached = self._get_cached(layer_name)
            if cached is not None:
                paths.append(cached)
                continue

            # Fetch van PDOK
            cache_path = self._cache_dir / f"map_{key}_{layer_name}.png"
            try:
                image_data = self._client.get_map(
                    lat=self.latitude,
                    lon=self.longitude,
                    radius_m=self.radius_m,
                    width_px=self._width_px,
                    height_px=self._height_px,
                    service=config["service"],
                    layers=config["layers"],
                    image_format="image/png",
                )
                cache_path.write_bytes(image_data)
                paths.append(cache_path)
            except Exception as e:
                logger.warning(
                    "Kon kaartlaag '%s' niet ophalen van PDOK: %s", layer_name, e
                )

        return paths

    def _build_content(self, available_width: float) -> Table:
        """Bouw intern Table object met kaart en optioneel caption/schaalbalk.

        Args:
            available_width: Beschikbare breedte in points.
        """
        pad = 6
        target_w = min(self.width_mm * MM_TO_PT, available_width - 2 * pad)
        target_h = self.height_mm * MM_TO_PT

        data = []

        if self._fetch_failed or not self._layer_paths:
            # Placeholder bij fout
            placeholder = self._make_placeholder(target_w, target_h)
            data.append([placeholder])
        else:
            # Kaartafbeelding — gebruik eerste laag als representatie in Table
            # Extra lagen worden in draw() als overlay getekend
            from reportlab.platypus import Image

            img = Image(
                str(self._layer_paths[0]),
                width=target_w,
                height=target_h,
            )
            data.append([img])

        # Caption
        if self.caption:
            data.append([Paragraph(self.caption, BM_STYLES["Caption"])])

        # Schaalbalk tekst
        diameter = self.radius_m * 2
        if diameter >= 1000:
            scale_text = f"~{diameter / 1000:.1f} km"
        else:
            scale_text = f"~{int(diameter)} m"
        data.append([Paragraph(scale_text, _STYLE_MAP_SCALE)])

        table = Table(data, colWidths=[available_width])

        style_cmds = [
            ("ALIGN", (0, 0), (0, 0), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), pad),
            ("RIGHTPADDING", (0, 0), (-1, -1), pad),
            # Turquoise linker accent-lijn
            ("LINEBEFORE", (0, 0), (0, -1), 2.5, HexColor(BM_COLORS.secondary)),
        ]
        # Caption padding
        if self.caption:
            style_cmds.append(("TOPPADDING", (0, 1), (0, 1), 4))
            style_cmds.append(("ALIGN", (0, 1), (0, 1), "CENTER"))
        # Schaalbalk padding
        scale_row = len(data) - 1
        style_cmds.append(("TOPPADDING", (0, scale_row), (0, scale_row), 2))
        style_cmds.append(("ALIGN", (0, scale_row), (0, scale_row), "CENTER"))

        table.setStyle(TableStyle(style_cmds))
        return table

    def _make_placeholder(self, width_pt: float, height_pt: float) -> Flowable:
        """Maak placeholder tabel voor wanneer de kaart niet beschikbaar is.

        Args:
            width_pt: Breedte in points.
            height_pt: Hoogte in points.
        """
        lines = [
            "Kaart niet beschikbaar",
            f"Locatie: {self.latitude:.6f}, {self.longitude:.6f}",
            f"Lagen: {', '.join(self.layers)}",
        ]
        text = "<br/>".join(lines)
        para = Paragraph(text, _STYLE_MAP_PLACEHOLDER)

        inner = Table([[para]], colWidths=[width_pt - 12])
        inner.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BACKGROUND", (0, 0), (-1, -1), HexColor("#F0F0F0")),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("BOX", (0, 0), (-1, -1), 0.5, HexColor(BM_COLORS.rule)),
        ]))

        # Wrapper tabel met vaste hoogte
        wrapper = Table([[inner]], colWidths=[width_pt], rowHeights=[height_pt])
        wrapper.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        return wrapper

    def wrap(self, available_width, available_height):
        """Bereken afmetingen en haal kaartdata op."""
        # Fetch layers als dat nog niet gebeurd is
        if not self._layer_paths and not self._fetch_failed:
            try:
                self._layer_paths = self._fetch_layers()
                if not self._layer_paths:
                    self._fetch_failed = True
            except Exception as e:
                logger.warning("Fout bij ophalen kaartlagen: %s", e)
                self._fetch_failed = True

        self._content = self._build_content(available_width)
        w, h = self._content.wrap(available_width, available_height)
        self.width = w
        self.height = h
        return (self.width, self.height)

    def draw(self):
        """Render de kaart met overlay lagen, caption en schaalbalk.

        Extra lagen (index 1+) worden als transparante PNG overlays
        op het canvas getekend boven de eerste laag.
        """
        if not hasattr(self, "_content"):
            return

        # Teken de basis content (eerste laag + caption + schaalbalk)
        self._content.drawOn(self.canv, 0, 0)

        # Teken extra lagen als overlay op de kaartafbeelding
        if len(self._layer_paths) > 1:
            pad = 6  # moet overeenkomen met _build_content pad
            target_w = min(self.width_mm * MM_TO_PT, self.width - 2 * pad)
            target_h = self.height_mm * MM_TO_PT

            img_y = self.height - target_h
            img_x = pad

            for layer_path in self._layer_paths[1:]:
                try:
                    self.canv.drawImage(
                        str(layer_path),
                        img_x,
                        img_y,
                        width=target_w,
                        height=target_h,
                        preserveAspectRatio=True,
                        mask="auto",
                    )
                except Exception as e:
                    logger.warning("Kon overlay laag niet tekenen: %s", e)
