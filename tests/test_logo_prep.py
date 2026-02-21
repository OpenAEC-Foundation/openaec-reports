"""Tests voor bm_reports.utils.logo_prep — Logo preparation module."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from bm_reports.utils.logo_prep import (
    copy_svg,
    prepare_logos,
    process_raster,
    remove_white_background,
    slugify,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rgb_image(
    width: int = 100,
    height: int = 100,
    color: tuple[int, int, int] = (255, 255, 255),
) -> Image.Image:
    """Maak een effen RGB afbeelding."""
    return Image.new("RGB", (width, height), color)


def _make_rgba_image(
    width: int = 100,
    height: int = 100,
    color: tuple[int, int, int, int] = (255, 0, 0, 255),
) -> Image.Image:
    """Maak een effen RGBA afbeelding."""
    return Image.new("RGBA", (width, height), color)


def _save_rgb(path: Path, color: tuple[int, int, int] = (255, 255, 255),
              size: tuple[int, int] = (100, 100)) -> None:
    """Sla een effen RGB afbeelding op."""
    _make_rgb_image(size[0], size[1], color).save(path)


def _save_rgba(path: Path, color: tuple[int, int, int, int] = (255, 0, 0, 128),
               size: tuple[int, int] = (100, 100)) -> None:
    """Sla een RGBA afbeelding op met transparantie."""
    _make_rgba_image(size[0], size[1], color).save(path)


SAMPLE_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50"><circle cx="25" cy="25" r="20"/></svg>'


# ===========================================================================
# TestSlugify
# ===========================================================================

class TestSlugify:
    """Tests voor slugify()."""

    def test_basic(self) -> None:
        assert slugify("logo") == "logo"

    def test_spaces(self) -> None:
        assert slugify("My Logo") == "my-logo"

    def test_special_characters(self) -> None:
        assert slugify("OpenAEC-Logo (Full)") == "openaec-logo-full"

    def test_underscores(self) -> None:
        assert slugify("logo_variant_2") == "logo-variant-2"

    def test_multiple_hyphens(self) -> None:
        assert slugify("logo---test") == "logo-test"

    def test_leading_trailing_special(self) -> None:
        assert slugify("(logo)") == "logo"

    def test_uppercase(self) -> None:
        assert slugify("BRAND") == "brand"


# ===========================================================================
# TestRemoveWhiteBackground
# ===========================================================================

class TestRemoveWhiteBackground:
    """Tests voor remove_white_background()."""

    def test_pure_white_becomes_transparent(self) -> None:
        """Puur witte afbeelding -> volledig transparant."""
        img = _make_rgb_image(50, 50, (255, 255, 255))
        result = remove_white_background(img)

        assert result.mode == "RGBA"
        # Alle pixels moeten alpha=0 hebben
        r, g, b, a = result.split()
        assert a.getextrema() == (0, 0)

    def test_non_white_preserved(self) -> None:
        """Niet-witte pixels blijven opaque."""
        img = _make_rgb_image(50, 50, (255, 0, 0))
        result = remove_white_background(img)

        r, g, b, a = result.split()
        assert a.getextrema() == (255, 255)

    def test_tolerance(self) -> None:
        """Bijna-wit (binnen tolerance) wordt ook transparant."""
        img = _make_rgb_image(50, 50, (230, 230, 230))
        result = remove_white_background(img, tolerance=30)

        r, g, b, a = result.split()
        assert a.getextrema() == (0, 0)

    def test_existing_transparency_preserved(self) -> None:
        """Afbeelding met bestaande transparantie wordt niet aangepast."""
        img = _make_rgba_image(50, 50, (255, 255, 255, 128))
        result = remove_white_background(img)

        # Alpha moet ongewijzigd zijn (niet naar 0 omgezet)
        r, g, b, a = result.split()
        assert a.getextrema() == (128, 128)

    def test_zero_tolerance(self) -> None:
        """Met tolerance=0, alleen exact wit wordt transparant."""
        # 254,254,254 is niet exact wit
        img = _make_rgb_image(50, 50, (254, 254, 254))
        result = remove_white_background(img, tolerance=0)

        r, g, b, a = result.split()
        assert a.getextrema() == (255, 255)

    def test_colored_image_unchanged(self) -> None:
        """Gekleurde afbeelding (blauw) blijft volledig opaque."""
        img = _make_rgb_image(50, 50, (0, 0, 200))
        result = remove_white_background(img)

        r, g, b, a = result.split()
        assert a.getextrema() == (255, 255)

    def test_mixed_image(self) -> None:
        """Afbeelding met witte en gekleurde pixels."""
        img = Image.new("RGB", (2, 1))
        img.putpixel((0, 0), (255, 255, 255))  # wit
        img.putpixel((1, 0), (255, 0, 0))  # rood

        result = remove_white_background(img)
        pixels = list(result.getdata())
        # Witte pixel → transparant
        assert pixels[0][3] == 0
        # Rode pixel → opaque
        assert pixels[1][3] == 255


# ===========================================================================
# TestProcessRaster
# ===========================================================================

class TestProcessRaster:
    """Tests voor process_raster()."""

    def test_png_background_removed(self, tmp_path: Path) -> None:
        """PNG met witte achtergrond → transparante PNG."""
        src = tmp_path / "logo.png"
        out = tmp_path / "output.png"
        _save_rgb(src, (255, 255, 255))

        result = process_raster(src, out)
        assert result == out
        assert out.exists()

        img = Image.open(out)
        assert img.mode == "RGBA"

    def test_jpg_to_png(self, tmp_path: Path) -> None:
        """JPG wordt omgezet naar PNG."""
        src = tmp_path / "logo.jpg"
        out = tmp_path / "output.png"
        _make_rgb_image(80, 80, (200, 0, 0)).save(src, "JPEG")

        process_raster(src, out)
        assert out.exists()
        assert out.suffix == ".png"

    def test_resize_large_image(self, tmp_path: Path) -> None:
        """Te groot beeld wordt geresized."""
        src = tmp_path / "big.png"
        out = tmp_path / "output.png"
        _save_rgb(src, (100, 100, 100), size=(2000, 1000))

        process_raster(src, out, max_size=800)
        img = Image.open(out)
        assert img.width <= 800
        assert img.height <= 800

    def test_aspect_ratio_preserved(self, tmp_path: Path) -> None:
        """Aspect ratio blijft behouden bij resize."""
        src = tmp_path / "wide.png"
        out = tmp_path / "output.png"
        _save_rgb(src, (100, 100, 100), size=(2000, 1000))

        process_raster(src, out, max_size=800)
        img = Image.open(out)
        ratio = img.width / img.height
        assert abs(ratio - 2.0) < 0.01

    def test_no_resize_if_small(self, tmp_path: Path) -> None:
        """Klein beeld wordt niet geresized."""
        src = tmp_path / "small.png"
        out = tmp_path / "output.png"
        _save_rgb(src, (100, 100, 100), size=(200, 150))

        process_raster(src, out, max_size=800)
        img = Image.open(out)
        assert img.width == 200
        assert img.height == 150

    def test_existing_transparency_kept(self, tmp_path: Path) -> None:
        """Afbeelding met bestaande transparantie wordt niet aangepast."""
        src = tmp_path / "alpha.png"
        out = tmp_path / "output.png"
        _save_rgba(src, (255, 0, 0, 128))

        process_raster(src, out)
        img = Image.open(out)
        r, g, b, a = img.split()
        assert a.getextrema() == (128, 128)


# ===========================================================================
# TestCopySvg
# ===========================================================================

class TestCopySvg:
    """Tests voor copy_svg()."""

    def test_content_identical(self, tmp_path: Path) -> None:
        """SVG inhoud moet identiek zijn na kopiëren."""
        src = tmp_path / "source.svg"
        out = tmp_path / "output" / "logo.svg"
        src.write_text(SAMPLE_SVG, encoding="utf-8")

        result = copy_svg(src, out)
        assert result == out
        assert out.exists()
        assert out.read_text(encoding="utf-8") == SAMPLE_SVG

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Maakt outputmap aan als die niet bestaat."""
        src = tmp_path / "source.svg"
        out = tmp_path / "deep" / "nested" / "logo.svg"
        src.write_text(SAMPLE_SVG, encoding="utf-8")

        copy_svg(src, out)
        assert out.exists()


# ===========================================================================
# TestPrepareLogos
# ===========================================================================

class TestPrepareLogos:
    """Tests voor prepare_logos()."""

    def test_single_file(self, tmp_path: Path) -> None:
        """Enkel bestand als bron."""
        src = tmp_path / "source" / "logo.png"
        src.parent.mkdir()
        _save_rgb(src, (255, 0, 0))
        out = tmp_path / "output"

        results = prepare_logos(src, out)
        assert len(results) == 1
        assert results[0].exists()

    def test_directory_recursive(self, tmp_path: Path) -> None:
        """Map met subdirectory's wordt recursief gescand."""
        src = tmp_path / "source"
        sub = src / "subdir"
        sub.mkdir(parents=True)
        _save_rgb(src / "logo1.png", (255, 0, 0))
        _save_rgb(sub / "logo2.png", (0, 255, 0))
        out = tmp_path / "output"

        results = prepare_logos(src, out)
        assert len(results) == 2

    def test_mixed_formats(self, tmp_path: Path) -> None:
        """Verwerkt PNG, JPG en SVG in één run."""
        src = tmp_path / "source"
        src.mkdir()
        _save_rgb(src / "logo.png", (255, 0, 0))
        _make_rgb_image(80, 80, (0, 255, 0)).save(src / "logo.jpg", "JPEG")
        (src / "logo.svg").write_text(SAMPLE_SVG, encoding="utf-8")
        out = tmp_path / "output"

        results = prepare_logos(src, out)
        assert len(results) == 3
        extensions = {p.suffix for p in results}
        assert ".png" in extensions
        assert ".svg" in extensions

    def test_empty_directory_raises(self, tmp_path: Path) -> None:
        """Lege map geeft ValueError."""
        src = tmp_path / "empty"
        src.mkdir()

        with pytest.raises(ValueError, match="Geen ondersteunde bestanden"):
            prepare_logos(src, tmp_path / "output")

    def test_nonexistent_path_raises(self, tmp_path: Path) -> None:
        """Niet-bestaand pad geeft FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Bronpad bestaat niet"):
            prepare_logos(tmp_path / "does_not_exist")

    def test_skip_existing(self, tmp_path: Path) -> None:
        """skip_existing=True slaat bestanden over die al bestaan."""
        src = tmp_path / "source"
        src.mkdir()
        _save_rgb(src / "logo.png", (255, 0, 0))
        out = tmp_path / "output"
        out.mkdir()

        # Eerste keer verwerken
        results1 = prepare_logos(src, out)
        assert len(results1) == 1

        # Wijzig de output om te verifiëren dat deze niet overschreven wordt
        first_output = results1[0]
        mtime_before = first_output.stat().st_mtime

        # Tweede keer met skip_existing
        results2 = prepare_logos(src, out, skip_existing=True)
        assert len(results2) == 1
        mtime_after = results2[0].stat().st_mtime
        assert mtime_after == mtime_before

    def test_return_values(self, tmp_path: Path) -> None:
        """Return waarden zijn Path objecten naar bestaande bestanden."""
        src = tmp_path / "source"
        src.mkdir()
        _save_rgb(src / "logo.png", (255, 0, 0))
        out = tmp_path / "output"

        results = prepare_logos(src, out)
        for p in results:
            assert isinstance(p, Path)
            assert p.exists()

    def test_default_output_dir(self, tmp_path: Path) -> None:
        """Zonder output_dir wordt assets/logos/ gebruikt."""
        src = tmp_path / "logo.png"
        _save_rgb(src, (255, 0, 0))

        results = prepare_logos(src)
        assert len(results) == 1
        # Output moet in de assets/logos/ map staan
        assert "logos" in str(results[0].parent)
        # Cleanup
        results[0].unlink()

    def test_slugified_output_names(self, tmp_path: Path) -> None:
        """Output bestandsnamen worden geslugged."""
        src = tmp_path / "source"
        src.mkdir()
        _save_rgb(src / "My Logo (Full).png", (255, 0, 0))
        out = tmp_path / "output"

        results = prepare_logos(src, out)
        assert results[0].stem == "my-logo-full"
