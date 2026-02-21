"""Convert PDF pages to PNG images for visual analysis."""
import fitz  # PyMuPDF
import sys
from pathlib import Path

pdf_path = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\2707_BBLrapportage_v01.pdf")
out_dir = pdf_path.parent / "pages"
out_dir.mkdir(exist_ok=True)

doc = fitz.open(str(pdf_path))
print(f"Pages: {len(doc)}")

for i, page in enumerate(doc):
    # Render at 150 DPI for good quality
    pix = page.get_pixmap(dpi=150)
    out_path = out_dir / f"page_{i+1:02d}.png"
    pix.save(str(out_path))
    print(f"  Page {i+1}: {page.rect.width:.1f} x {page.rect.height:.1f} pt -> {out_path.name}")

doc.close()
print("Done!")
