"""Stationery extractor — extraheer achtergrondtemplates uit referentie-PDF's."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import fitz
except ImportError:
    fitz = None


class StationeryExtractor:
    """Extraheer stationery-pagina's uit een referentie-PDF.

    Drie extractiemodi:
    - full_page: hele pagina als PDF (vectoren behouden)
    - stripped: pagina met tekst in opgegeven zones verwijderd
    - graphics_only: pagina met ALLE tekst verwijderd
    """

    def __init__(self, source_pdf: Path):
        if fitz is None:
            raise ImportError("PyMuPDF vereist: pip install pymupdf")
        self._source = Path(source_pdf)
        if not self._source.exists():
            raise FileNotFoundError(f"PDF niet gevonden: {self._source}")

    def extract_full_page(self, page_num: int, output_path: Path) -> Path:
        """Extraheer hele pagina als nieuwe single-page PDF.

        page_num: 0-based pagina index.
        Gebruik voor: backcover (100% statisch).
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = fitz.open(str(self._source))
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        new_doc.save(str(output_path))
        new_doc.close()
        doc.close()

        logger.info(f"Stationery geëxtraheerd: pagina {page_num + 1} → {output_path}")
        return output_path

    def extract_stripped_page(
        self, page_num: int, output_path: Path,
        strip_zones: list[tuple[float, float, float, float]],
    ) -> Path:
        """Extraheer pagina met tekst in opgegeven zones verwijderd (wit).

        page_num: 0-based pagina index.
        strip_zones: lijst van (x0, y0, x1, y1) in PyMuPDF coords (top-down).
        Tekst in deze zones wordt wit gemaakt, grafische elementen blijven.

        Gebruik voor: cover (strip titel), colofon (strip labels),
        appendix divider (strip nummer/titel).
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = fitz.open(str(self._source))
        # Werk op kopie
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        doc.close()

        page = new_doc[0]
        for (x0, y0, x1, y1) in strip_zones:
            rect = fitz.Rect(x0, y0, x1, y1)
            # Vind tekst in zone en redact
            text_dict = page.get_text("dict", clip=rect)
            for block in text_dict.get("blocks", []):
                if block.get("type") == 0:  # tekst blok
                    block_rect = fitz.Rect(block["bbox"])
                    page.add_redact_annot(block_rect, fill=(1, 1, 1))
        page.apply_redactions()

        new_doc.save(str(output_path))
        new_doc.close()

        logger.info(f"Stripped stationery: pagina {page_num + 1} → {output_path}")
        return output_path

    def extract_graphics_only(self, page_num: int, output_path: Path) -> Path:
        """Extraheer pagina met ALLE tekst verwijderd.

        Let op: logo-tekst wordt ook verwijderd!
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = fitz.open(str(self._source))
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        doc.close()

        page = new_doc[0]
        # Verwijder alle tekst
        text_dict = page.get_text("dict")
        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:
                block_rect = fitz.Rect(block["bbox"])
                page.add_redact_annot(block_rect, fill=(1, 1, 1))
        page.apply_redactions()

        new_doc.save(str(output_path))
        new_doc.close()

        logger.info(f"Graphics-only stationery: pagina {page_num + 1} → {output_path}")
        return output_path

    def extract_as_png(self, page_num: int, output_path: Path, dpi: int = 300) -> Path:
        """Fallback: extraheer als hoge-resolutie PNG."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = fitz.open(str(self._source))
        page = doc[page_num]
        pix = page.get_pixmap(dpi=dpi)
        pix.save(str(output_path))
        doc.close()

        return output_path
