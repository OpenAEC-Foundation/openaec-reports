"""Tests voor image_block.py — edge cases en coverage gaps."""

from __future__ import annotations

import base64
import io
from pathlib import Path

import pytest
from PIL import Image as PILImage

from openaec_reports.components.image_block import ImageBlock
from openaec_reports.core.block_registry import create_block, resolve_image_source


def _make_png(tmp_path: Path, name: str = "test.png", size: tuple = (100, 100)) -> Path:
    """Maak een tijdelijke PNG afbeelding."""
    img = PILImage.new("RGB", size, (255, 0, 0))
    path = tmp_path / name
    img.save(path, "PNG")
    return path


def _make_base64_png(size: tuple = (50, 50)) -> str:
    """Maak een base64 encoded PNG string."""
    img = PILImage.new("RGB", size, (0, 128, 255))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


class TestImageBlockInit:
    def test_create_with_valid_png(self, tmp_path):
        """ImageBlock met bestaande PNG."""
        path = _make_png(tmp_path)
        block = ImageBlock(path=path)
        assert block.path == path
        assert block.align == "center"

    def test_create_with_width_mm(self, tmp_path):
        """ImageBlock met expliciete breedte."""
        path = _make_png(tmp_path)
        block = ImageBlock(path=path, width_mm=80)
        assert block.width_mm == 80

    def test_create_with_caption(self, tmp_path):
        """ImageBlock met caption."""
        path = _make_png(tmp_path)
        block = ImageBlock(path=path, caption="Test caption")
        assert block.caption == "Test caption"

    def test_create_with_align_left(self, tmp_path):
        """ImageBlock met left alignment."""
        path = _make_png(tmp_path)
        block = ImageBlock(path=path, align="left")
        assert block.align == "left"

    def test_missing_file_raises(self):
        """Niet-bestaand bestand geeft FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            ImageBlock(path="/nonexistent/image.png")

    def test_unsupported_format_raises(self, tmp_path):
        """Niet-ondersteund formaat geeft ValueError."""
        path = tmp_path / "test.xyz"
        path.write_text("not an image")
        with pytest.raises(ValueError, match="Niet-ondersteund formaat"):
            ImageBlock(path=path)


class TestImageBlockRendering:
    def test_wrap_returns_dimensions(self, tmp_path):
        """wrap() retourneert breedte en hoogte."""
        path = _make_png(tmp_path, size=(200, 100))
        block = ImageBlock(path=path)
        w, h = block.wrap(400, 800)
        assert w > 0
        assert h > 0

    def test_wrap_respects_available_width(self, tmp_path):
        """wrap() respecteert de beschikbare breedte."""
        path = _make_png(tmp_path, size=(1000, 500))
        block = ImageBlock(path=path)
        w, h = block.wrap(300, 800)
        assert w <= 300

    def test_wrap_with_width_mm(self, tmp_path):
        """wrap() met expliciete width_mm."""
        path = _make_png(tmp_path)
        block = ImageBlock(path=path, width_mm=50)
        w, h = block.wrap(400, 800)
        assert w > 0

    def test_wrap_with_height_mm_constraint(self, tmp_path):
        """wrap() met height_mm beperkt de hoogte."""
        path = _make_png(tmp_path, size=(100, 500))
        block = ImageBlock(path=path, height_mm=20)
        w, h = block.wrap(400, 800)
        assert h > 0

    def test_wrap_with_caption(self, tmp_path):
        """wrap() met caption voegt hoogte toe."""
        path = _make_png(tmp_path)
        block_no_caption = ImageBlock(path=path)
        block_with_caption = ImageBlock(path=path, caption="Test bijschrift")

        _, h_no = block_no_caption.wrap(400, 800)
        _, h_with = block_with_caption.wrap(400, 800)

        # Met caption is hoger
        assert h_with > h_no


class TestResolveImageSource:
    def test_resolve_file_path(self, tmp_path):
        """resolve_image_source met bestandspad."""
        path = _make_png(tmp_path)
        resolved = resolve_image_source(str(path))
        assert Path(resolved).exists()

    def test_resolve_relative_path(self, tmp_path):
        """resolve_image_source met relatief pad + base_dir."""
        _make_png(tmp_path, "photo.png")
        resolved = resolve_image_source("photo.png", base_dir=tmp_path)
        assert Path(resolved).exists()

    def test_resolve_base64_dict(self):
        """resolve_image_source met base64 dict."""
        b64 = _make_base64_png()
        resolved = resolve_image_source({
            "data": b64,
            "media_type": "image/png",
        })
        assert Path(resolved).exists()
        assert Path(resolved).stat().st_size > 0

    def test_resolve_base64_with_filename(self):
        """resolve_image_source met base64 dict + filename."""
        b64 = _make_base64_png()
        resolved = resolve_image_source({
            "data": b64,
            "media_type": "image/jpeg",
            "filename": "foto",
        })
        assert Path(resolved).exists()
        assert ".jpg" in str(resolved)


class TestCreateImageBlock:
    def test_create_block_image(self, tmp_path):
        """create_block met type 'image' en bestaand bestand."""
        path = _make_png(tmp_path)
        block = create_block(
            {"type": "image", "src": str(path), "caption": "Test"},
            base_dir=tmp_path,
        )
        assert block is not None

    def test_create_block_missing_file_placeholder(self):
        """create_block met ontbrekend bestand retourneert placeholder."""
        block = create_block(
            {"type": "image", "src": "/nonexistent/img.png"},
        )
        # Zou een Paragraph placeholder moeten retourneren (niet crashen)
        assert block is not None

    def test_create_block_with_alignment(self, tmp_path):
        """create_block met alignment parameter."""
        path = _make_png(tmp_path)
        block = create_block(
            {"type": "image", "src": str(path), "alignment": "left"},
            base_dir=tmp_path,
        )
        assert block is not None

    def test_create_block_with_width(self, tmp_path):
        """create_block met width_mm parameter."""
        path = _make_png(tmp_path)
        block = create_block(
            {"type": "image", "src": str(path), "width_mm": 120},
            base_dir=tmp_path,
        )
        assert block is not None

    def test_create_block_base64(self):
        """create_block met base64 src."""
        b64 = _make_base64_png()
        block = create_block(
            {"type": "image", "src": {"data": b64, "media_type": "image/png"}},
        )
        assert block is not None
