"""Visual diff — vergelijk gegenereerde PDF met referentie."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import fitz
except ImportError:
    fitz = None

try:
    from PIL import Image
    import numpy as np
except ImportError:
    Image = None
    np = None


@dataclass
class PageDiff:
    """Verschilanalyse voor één pagina."""

    page_number: int
    similarity_pct: float  # 0-100
    diff_image_path: str | None = None
    notes: list[str] = field(default_factory=list)


def compare_pdfs(
    generated: Path,
    reference: Path,
    output_dir: Path | None = None,
    dpi: int = 150,
    pages: list[int] | None = None,
) -> list[PageDiff]:
    """Vergelijk twee PDF's pagina-voor-pagina.

    Args:
        generated: Pad naar gegenereerde PDF.
        reference: Pad naar referentie PDF.
        output_dir: Map voor verschil-afbeeldingen.
        dpi: Render DPI.
        pages: Specifieke pagina's om te vergelijken (1-based), None = alle.

    Returns:
        Lijst van PageDiff per vergeleken pagina.

    Raises:
        ImportError: Als PyMuPDF, Pillow of numpy niet geinstalleerd zijn.
        FileNotFoundError: Als een PDF bestand niet bestaat.
    """
    if fitz is None:
        raise ImportError("PyMuPDF nodig: pip install PyMuPDF")
    if Image is None or np is None:
        raise ImportError("Pillow en numpy nodig: pip install Pillow numpy")

    generated = Path(generated)
    reference = Path(reference)

    if not generated.exists():
        raise FileNotFoundError(f"Gegenereerde PDF niet gevonden: {generated}")
    if not reference.exists():
        raise FileNotFoundError(f"Referentie PDF niet gevonden: {reference}")

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    gen_doc = fitz.open(str(generated))
    ref_doc = fitz.open(str(reference))

    results: list[PageDiff] = []
    max_pages = min(len(gen_doc), len(ref_doc))
    page_indices: range | list[int] = range(max_pages)

    if pages:
        page_indices = [p - 1 for p in pages if 0 < p <= max_pages]

    for idx in page_indices:
        gen_pix = gen_doc[idx].get_pixmap(dpi=dpi)
        ref_pix = ref_doc[idx].get_pixmap(dpi=dpi)

        gen_img = Image.frombytes("RGB", (gen_pix.width, gen_pix.height), gen_pix.samples)
        ref_img = Image.frombytes("RGB", (ref_pix.width, ref_pix.height), ref_pix.samples)

        # Resize naar zelfde formaat
        if gen_img.size != ref_img.size:
            ref_img = ref_img.resize(gen_img.size, Image.LANCZOS)

        gen_arr = np.array(gen_img, dtype=float)
        ref_arr = np.array(ref_img, dtype=float)
        diff_arr = np.abs(gen_arr - ref_arr)

        # Similarity: percentage pixels met <threshold verschil
        threshold = 30
        similar_pixels = np.all(diff_arr < threshold, axis=2).sum()
        total_pixels = diff_arr.shape[0] * diff_arr.shape[1]
        similarity = (similar_pixels / total_pixels) * 100

        diff_path = None
        if output_dir:
            diff_mask = np.any(diff_arr > threshold, axis=2)
            overlay = gen_arr.copy().astype(np.uint8)
            overlay[diff_mask] = [255, 0, 0]

            diff_img = Image.fromarray(overlay)
            diff_path = str(output_dir / f"diff_page_{idx + 1:03d}.png")
            diff_img.save(diff_path)

        results.append(PageDiff(
            page_number=idx + 1,
            similarity_pct=round(similarity, 1),
            diff_image_path=diff_path,
        ))

    gen_doc.close()
    ref_doc.close()

    return results


def print_diff_report(diffs: list[PageDiff]) -> None:
    """Print een leesbaar diff rapport naar stdout."""
    print("\n=== Visual Diff Report ===\n")
    for d in diffs:
        status = "OK" if d.similarity_pct > 95 else "WARN" if d.similarity_pct > 80 else "FAIL"
        print(f"  Pagina {d.page_number}: {d.similarity_pct:.1f}% match [{status}]")
        if d.diff_image_path:
            print(f"    Diff: {d.diff_image_path}")

    avg = sum(d.similarity_pct for d in diffs) / len(diffs) if diffs else 0
    print(f"\n  Gemiddeld: {avg:.1f}%")
    print(f"  Pagina's: {len(diffs)}")
