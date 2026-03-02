"""Logo preparation — Verwerk ruwe logo's naar rapport-klare PNG's.

Verwijdert witte achtergronden, behoudt bestaande transparantie,
en kopieert SVG's ongewijzigd.
"""

from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path

from PIL import Image, ImageChops

logger = logging.getLogger(__name__)

LOGOS_DIR = Path(__file__).parent.parent / "assets" / "logos"
DEFAULT_MAX_SIZE = 800  # pixels
RASTER_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}
SVG_EXTENSIONS = {".svg"}
SUPPORTED_EXTENSIONS = RASTER_EXTENSIONS | SVG_EXTENSIONS


def prepare_logos(
    source: str | Path,
    output_dir: str | Path | None = None,
    *,
    max_size: int = DEFAULT_MAX_SIZE,
    tolerance: int = 30,
    skip_existing: bool = False,
) -> list[Path]:
    """Verwerk logo's uit bronmap of -bestand naar rapport-klare PNG's.

    Scant recursief voor PNG, JPG, SVG bestanden.
    Raster -> witte achtergrond verwijderen -> PNG met alpha.
    SVG -> ongewijzigd kopiëren.

    Args:
        source: Pad naar bronmap of enkel bestand.
        output_dir: Doelmap voor verwerkte logo's. Default: assets/logos/.
        max_size: Maximale breedte/hoogte in pixels.
        tolerance: Drempelwaarde voor wit-detectie (0-255).
        skip_existing: Sla bestanden over die al bestaan in output_dir.

    Returns:
        Lijst van paden naar verwerkte bestanden.

    Raises:
        FileNotFoundError: Als source niet bestaat.
        ValueError: Als source een lege map is (geen ondersteunde bestanden).
    """
    source = Path(source)
    if not source.exists():
        msg = f"Bronpad bestaat niet: {source}"
        raise FileNotFoundError(msg)

    output = Path(output_dir) if output_dir else LOGOS_DIR
    output.mkdir(parents=True, exist_ok=True)

    # Verzamel bronbestanden
    if source.is_file():
        files = [source]
    else:
        files = sorted(f for f in source.rglob("*") if f.suffix.lower() in SUPPORTED_EXTENSIONS)

    if not files:
        msg = f"Geen ondersteunde bestanden gevonden in: {source}"
        raise ValueError(msg)

    results: list[Path] = []
    for file_path in files:
        suffix = file_path.suffix.lower()
        slug = slugify(file_path.stem)

        if suffix in SVG_EXTENSIONS:
            out_path = output / f"{slug}.svg"
        else:
            out_path = output / f"{slug}.png"

        if skip_existing and out_path.exists():
            logger.info("Overgeslagen (bestaat al): %s", out_path.name)
            results.append(out_path)
            continue

        if suffix in SVG_EXTENSIONS:
            copy_svg(file_path, out_path)
        else:
            process_raster(
                file_path,
                out_path,
                max_size=max_size,
                tolerance=tolerance,
            )

        results.append(out_path)
        logger.info("Verwerkt: %s -> %s", file_path.name, out_path.name)

    return results


def process_raster(
    source_path: Path,
    output_path: Path,
    *,
    max_size: int = DEFAULT_MAX_SIZE,
    tolerance: int = 30,
) -> Path:
    """Verwerk één rasterafbeelding: transparantie + resize -> PNG.

    Args:
        source_path: Pad naar bronafbeelding.
        output_path: Pad voor output PNG.
        max_size: Maximale breedte/hoogte in pixels.
        tolerance: Drempelwaarde voor wit-detectie (0-255).

    Returns:
        Pad naar de verwerkte PNG.
    """
    image = Image.open(source_path)
    image = remove_white_background(image, tolerance=tolerance)

    # Resize als nodig (behoud aspect ratio)
    if image.width > max_size or image.height > max_size:
        image.thumbnail((max_size, max_size), Image.LANCZOS)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, "PNG")
    return output_path


def remove_white_background(
    image: Image.Image,
    tolerance: int = 30,
) -> Image.Image:
    """Verwijder witte achtergrond via per-kanaal thresholding (pure Pillow).

    Algoritme:
        1. Converteer naar RGBA
        2. Check of afbeelding al transparantie heeft -> zo ja, retourneer
        3. Split in R, G, B, A kanalen
        4. Per kanaal: point() met threshold (255 - tolerance) -> masker
        5. Combineer kanalen met ImageChops.multiply() -> wit-masker
        6. Inverteer -> alpha masker
        7. Pas toe op alpha kanaal

    Args:
        image: Pillow Image object.
        tolerance: Drempelwaarde (0-255). Pixels waar R, G én B >= 255-tolerance
            worden als wit beschouwd.

    Returns:
        RGBA Image met transparante achtergrond.
    """
    image = image.convert("RGBA")

    # Check bestaande transparantie
    r, g, b, a = image.split()
    if a.getextrema()[0] < 255:
        # Afbeelding heeft al transparantie, niet aanpassen
        return image

    # Per kanaal: markeer pixels die "wit" zijn (>= 255 - tolerance)
    threshold = 255 - tolerance

    def _is_white_channel(channel: Image.Image) -> Image.Image:
        """Retourneer masker: 255 waar pixel >= threshold, 0 elders."""
        return channel.point(lambda v: 255 if v >= threshold else 0)

    white_r = _is_white_channel(r)
    white_g = _is_white_channel(g)
    white_b = _is_white_channel(b)

    # Pixel is wit als ALLE kanalen boven threshold liggen
    white_mask = ImageChops.multiply(ImageChops.multiply(white_r, white_g), white_b)

    # Inverteer: witte pixels -> transparant (alpha=0), rest -> opaque (alpha=255)
    alpha_mask = ImageChops.invert(white_mask)

    # Pas toe
    image.putalpha(alpha_mask)
    return image


def copy_svg(source_path: Path, output_path: Path) -> Path:
    """Kopieer SVG ongewijzigd.

    Args:
        source_path: Pad naar bron SVG.
        output_path: Pad voor output SVG.

    Returns:
        Pad naar de gekopieerde SVG.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, output_path)
    return output_path


def slugify(name: str) -> str:
    """Maak een bestandsnaam-veilige slug van een naam.

    Args:
        name: Originele naam, bijv. '3BM-Logo (Full)'.

    Returns:
        Slug, bijv. '3bm-logo-full'.
    """
    # Lowercase
    slug = name.lower()
    # Vervang niet-alfanumeriek door hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    # Strip leading/trailing hyphens
    slug = slug.strip("-")
    return slug
