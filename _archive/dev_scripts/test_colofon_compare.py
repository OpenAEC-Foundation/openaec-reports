"""Quick visual diff: render BBL colofon vs mockup side by side."""
import fitz
from pathlib import Path

OUT = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\test_output")

# Render BBL colofon (pagina 2) als referentie
bbl = fitz.open(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\2707_BBLrapportage_v01.pdf")
pix = bbl[1].get_pixmap(dpi=150)
pix.save(str(OUT / "ref_colofon.png"))
bbl.close()

# Render mockup
mock = fitz.open(str(OUT / "colofon_mockup.pdf"))
pix = mock[0].get_pixmap(dpi=150)
pix.save(str(OUT / "mock_colofon.png"))
mock.close()

# Also render the colofon.pdf template
col = fitz.open(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\paginas\colofon.pdf")
pix = col[0].get_pixmap(dpi=150)
pix.save(str(OUT / "template_colofon.png"))
col.close()

print("Rendered: ref_colofon.png, mock_colofon.png, template_colofon.png")
