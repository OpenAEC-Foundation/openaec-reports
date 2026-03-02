"""Stationery renderer — tekent PDF/PNG achtergronden op ReportLab canvas."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class StationeryRenderer:
    """Tekent stationery (achtergrond PDF/PNG) als laag 1 op een pagina.

    Gebruikt pdfrw om PDF pagina's als vector XObject te embedden.
    Fallback naar Pillow voor PNG achtergronden.
    """

    def __init__(self, brand_dir: Path | None = None):
        self._brand_dir = brand_dir
        self._cache: dict[str, Any] = {}

    def draw(
        self,
        canvas,
        source_path: str | Path | None,
        page_w: float,
        page_h: float,
    ) -> bool:
        """Teken stationery achtergrond op het canvas.

        source_path: pad naar PDF of PNG (relatief t.o.v. brand_dir, of absoluut).
        Returns True als getekend, False als niet beschikbaar.
        """
        if not source_path:
            return False

        path = self._resolve_path(source_path)
        if path is None or not path.exists():
            logger.warning(f"Stationery niet gevonden: {source_path}")
            return False

        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return self._draw_pdf(canvas, path, page_w, page_h)
        elif suffix in (".png", ".jpg", ".jpeg"):
            return self._draw_image(canvas, path, page_w, page_h)
        else:
            logger.warning(f"Onbekend stationery formaat: {suffix}")
            return False

    def _resolve_path(self, source: str | Path) -> Path | None:
        """Resolve relatief pad t.o.v. brand_dir."""
        path = Path(source)
        if path.is_absolute() and path.exists():
            return path
        if self._brand_dir:
            resolved = self._brand_dir / path
            if resolved.exists():
                return resolved
        return None

    def _draw_pdf(self, canvas, pdf_path: Path, page_w: float, page_h: float) -> bool:
        """Render PDF als achtergrond via pdfrw → ReportLab XObject."""
        try:
            from pdfrw import PdfReader
            from pdfrw.buildxobj import pagexobj
            from pdfrw.toreportlab import makerl
        except ImportError:
            logger.error("pdfrw niet geïnstalleerd: pip install pdfrw")
            return False

        cache_key = str(pdf_path)
        if cache_key not in self._cache:
            reader = PdfReader(str(pdf_path))
            if not reader.pages:
                return False
            self._cache[cache_key] = pagexobj(reader.pages[0])

        xobj = self._cache[cache_key]

        canvas.saveState()
        # Schaal stationery naar pagina-afmetingen
        xobj_w = float(xobj.BBox[2]) - float(xobj.BBox[0])
        xobj_h = float(xobj.BBox[3]) - float(xobj.BBox[1])
        if xobj_w > 0 and xobj_h > 0:
            sx = page_w / xobj_w
            sy = page_h / xobj_h
            canvas.transform(sx, 0, 0, sy, 0, 0)

        rl_obj = makerl(canvas, xobj)
        canvas.doForm(rl_obj)
        canvas.restoreState()

        return True

    def _draw_image(self, canvas, img_path: Path, page_w: float, page_h: float) -> bool:
        """Render PNG/JPG als full-page achtergrond."""
        try:
            canvas.drawImage(
                str(img_path),
                0,
                0,
                page_w,
                page_h,
                preserveAspectRatio=False,
                mask="auto",
            )
            return True
        except (OSError, ValueError) as e:
            logger.error("Stationery image fout: %s", e)
            return False
