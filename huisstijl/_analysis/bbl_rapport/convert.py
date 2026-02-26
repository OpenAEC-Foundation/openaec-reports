import fitz
import os

pdf_path = r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\2707_BBLrapportage_v01.pdf"
out_dir = r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\_analysis\bbl_rapport"

doc = fitz.open(pdf_path)
print(f"Pages: {len(doc)}")
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=200)
    out_path = os.path.join(out_dir, f"page_{i+1}.png")
    pix.save(out_path)
    print(f"Saved page {i+1}: {pix.width}x{pix.height}")
doc.close()
