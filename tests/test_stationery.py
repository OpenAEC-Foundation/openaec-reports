"""Tests voor StationeryRenderer — achtergrond PDF/PNG op canvas."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from bm_reports.core.stationery import StationeryRenderer


class TestStationeryRendererInit:
    def test_create_without_brand_dir(self):
        renderer = StationeryRenderer()
        assert renderer._brand_dir is None

    def test_create_with_brand_dir(self, tmp_path):
        renderer = StationeryRenderer(brand_dir=tmp_path)
        assert renderer._brand_dir == tmp_path


class TestResolvePath:
    def test_absolute_path_exists(self, tmp_path):
        f = tmp_path / "bg.pdf"
        f.write_bytes(b"dummy")
        renderer = StationeryRenderer()
        assert renderer._resolve_path(str(f)) == f

    def test_absolute_path_not_exists(self):
        renderer = StationeryRenderer()
        assert renderer._resolve_path("/nonexistent/bg.pdf") is None

    def test_relative_path_with_brand_dir(self, tmp_path):
        (tmp_path / "stationery").mkdir()
        f = tmp_path / "stationery" / "cover.pdf"
        f.write_bytes(b"dummy")
        renderer = StationeryRenderer(brand_dir=tmp_path)
        result = renderer._resolve_path("stationery/cover.pdf")
        assert result == f

    def test_relative_path_without_brand_dir(self):
        renderer = StationeryRenderer()
        result = renderer._resolve_path("stationery/cover.pdf")
        assert result is None


class TestDrawFallback:
    def test_draw_none_source(self):
        canvas = MagicMock()
        renderer = StationeryRenderer()
        result = renderer.draw(canvas, None, 595, 842)
        assert result is False

    def test_draw_empty_source(self):
        canvas = MagicMock()
        renderer = StationeryRenderer()
        result = renderer.draw(canvas, "", 595, 842)
        assert result is False

    def test_draw_nonexistent_file(self):
        canvas = MagicMock()
        renderer = StationeryRenderer()
        result = renderer.draw(canvas, "/nonexistent.pdf", 595, 842)
        assert result is False

    def test_draw_unknown_extension(self, tmp_path):
        f = tmp_path / "bg.bmp"
        f.write_bytes(b"dummy")
        canvas = MagicMock()
        renderer = StationeryRenderer(brand_dir=tmp_path)
        result = renderer.draw(canvas, str(f), 595, 842)
        assert result is False


class TestDrawImage:
    def test_draw_png(self, tmp_path):
        """PNG achtergrond wordt gerendered via drawImage."""
        from PIL import Image

        img = Image.new("RGB", (100, 100), (255, 255, 255))
        f = tmp_path / "bg.png"
        img.save(f, "PNG")

        canvas = MagicMock()
        renderer = StationeryRenderer(brand_dir=tmp_path)
        result = renderer.draw(canvas, str(f), 595, 842)

        assert result is True
        canvas.drawImage.assert_called_once()

    def test_draw_jpg(self, tmp_path):
        """JPG achtergrond wordt gerendered via drawImage."""
        from PIL import Image

        img = Image.new("RGB", (100, 100), (255, 255, 255))
        f = tmp_path / "bg.jpg"
        img.save(f, "JPEG")

        canvas = MagicMock()
        renderer = StationeryRenderer(brand_dir=tmp_path)
        result = renderer.draw(canvas, str(f), 595, 842)

        assert result is True
        canvas.drawImage.assert_called_once()


class TestDrawPdf:
    def test_draw_pdf_calls_doForm(self, tmp_path):
        """PDF achtergrond wordt gerendered via pdfrw → doForm."""
        from reportlab.pdfgen import canvas as rl_canvas

        pdf_path = tmp_path / "bg.pdf"
        c = rl_canvas.Canvas(str(pdf_path), pagesize=(595, 842))
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.rect(0, 0, 595, 842, fill=1)
        c.save()

        mock_canvas = MagicMock()
        mock_canvas.transform = MagicMock()
        renderer = StationeryRenderer(brand_dir=tmp_path)
        result = renderer.draw(mock_canvas, str(pdf_path), 595, 842)

        assert result is True
        mock_canvas.saveState.assert_called_once()
        mock_canvas.restoreState.assert_called_once()
        mock_canvas.doForm.assert_called_once()

    def test_pdf_caching(self, tmp_path):
        """Tweede aanroep gebruikt cache (pdfrw leest niet opnieuw)."""
        from reportlab.pdfgen import canvas as rl_canvas

        pdf_path = tmp_path / "bg.pdf"
        c = rl_canvas.Canvas(str(pdf_path), pagesize=(595, 842))
        c.rect(0, 0, 595, 842, fill=1)
        c.save()

        mock_canvas = MagicMock()
        mock_canvas.transform = MagicMock()
        renderer = StationeryRenderer(brand_dir=tmp_path)

        renderer.draw(mock_canvas, str(pdf_path), 595, 842)
        renderer.draw(mock_canvas, str(pdf_path), 595, 842)

        # Cache key moet bestaan
        assert len(renderer._cache) == 1
