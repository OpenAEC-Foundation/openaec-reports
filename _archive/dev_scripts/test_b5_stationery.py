"""Stationery generator — maak schone achtergronden van speciale pagina's.

Neemt de PDF pagina-render en maskeert dynamische content (tekst, foto's)
zodat er een bruikbare stationery/achtergrond overblijft.
"""
import sys
sys.path.insert(0, r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src")

from pathlib import Path
import fitz  # PyMuPDF

from bm_reports.tools.pdf_extractor import extract_pdf
from bm_reports.tools.page_classifier import classify_pages, PageType
from bm_reports.tools.layout_extractor import extract_page_layouts

PDF = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\2707_BBLrapportage_v01.pdf")
OUT = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\test_output\b5_stationery")
OUT.mkdir(parents=True, exist_ok=True)

# ============================================================
# Configuratie per pagina-type: welke zones moeten gemaskeerd?
# ============================================================
# Elke zone is (x, y_top, width, height) in PDF-native coords (bottom-up)
# + de kleur waarmee gemaskeerd wordt

DYNAMIC_ZONES = {
    PageType.COVER: {
        "mask_color": (0.251, 0.067, 0.275),  # #401146 paars
        "zones": [
            # Titel "BBL-toetsingsrapportage" — bovenaan
            {"rect": (40, 698, 520, 50), "color": (0.251, 0.067, 0.275)},
            # Subtitle "Projecten die inspireren" 
            # -> STATISCH, niet maskeren
            # Foto — het grote beeld
            {"rect": (50, 118, 500, 570), "color": (0.251, 0.067, 0.275)},
        ],
        "remove_images": True,  # Verwijder alle embedded images
        "remove_texts": [
            # Teksten die dynamisch zijn (titel)
            {"min_size": 25, "max_y": 750},  # Grote titel tekst bovenaan
        ],
    },
    PageType.COLOFON: {
        "mask_color": (1, 1, 1),  # wit
        "zones": [
            # Rapport type titel bovenaan
            {"rect": (60, 760, 400, 40), "color": (1, 1, 1)},
            # Subtitel eronder
            {"rect": (60, 725, 400, 30), "color": (1, 1, 1)},
            # Alle colofon waarden (rechterkolom)
            {"rect": (220, 180, 210, 360), "color": (1, 1, 1)},
            # Paginanummer rechtsonder
            {"rect": (520, 38, 50, 20), "color": (1, 1, 1)},
        ],
        "remove_images": False,
        "remove_texts": [],
    },
    PageType.TOC: {
        "mask_color": (1, 1, 1),
        "zones": [
            # Hele inhoudsopgave tekst
            {"rect": (80, 120, 460, 700), "color": (1, 1, 1)},
            # Paginanummer
            {"rect": (520, 38, 50, 20), "color": (1, 1, 1)},
        ],
        "remove_images": False,
        "remove_texts": [],
    },
    PageType.APPENDIX_DIVIDER: {
        "mask_color": (0.216, 0.737, 0.671),  # #37BCAB teal
        "zones": [
            # Bijlage nummer "A"
            {"rect": (90, 140, 200, 60), "color": (0.216, 0.737, 0.671)},
            # Bijlage titel (twee regels)
            {"rect": (90, 200, 400, 120), "color": (0.216, 0.737, 0.671)},
        ],
        "remove_images": False,
        "remove_texts": [],
    },
    PageType.BACKCOVER: {
        # Backcover is volledig statisch — geen masking nodig
        "mask_color": None,
        "zones": [],
        "remove_images": False,
        "remove_texts": [],
    },
}


def create_stationery(pdf_path: Path, output_dir: Path, dpi: int = 300):
    """Maak schone stationery achtergronden."""
    
    print("=" * 60)
    print("STATIONERY GENERATOR")
    print("=" * 60)
    
    # Stap 1: Classificeer pagina's
    print("\n[1/3] Extracting & classifying...")
    pages = extract_pdf(pdf_path)
    classified = classify_pages(pages)
    layouts = extract_page_layouts(classified)
    
    # Stap 2: Open PDF voor manipulatie
    print("[2/3] Generating stationery pages...")
    doc = fitz.open(str(pdf_path))
    
    for cp in classified:
        if cp.page_type == PageType.CONTENT:
            continue
            
        config = DYNAMIC_ZONES.get(cp.page_type)
        if not config or not config["zones"]:
            # Geen masking nodig (bijv. backcover) — gewoon renderen
            page = doc[cp.page.page_number - 1]
            pix = page.get_pixmap(dpi=dpi)
            out_path = output_dir / f"stationery_{cp.page_type.value}.png"
            pix.save(str(out_path))
            print(f"  {cp.page_type.value}: direct gerenderd -> {out_path.name}")
            continue
        
        # Maak een kopie van de pagina om te bewerken
        # We werken op een nieuwe doc om het origineel niet aan te passen
        tmp_doc = fitz.open(str(pdf_path))
        page = tmp_doc[cp.page.page_number - 1]
        
        # Optie 1: Verwijder images
        if config.get("remove_images"):
            for img_info in page.get_images(full=True):
                xref = img_info[0]
                try:
                    rects = page.get_image_rects(xref)
                    for r in rects:
                        # Teken rechthoek over image
                        color = config["mask_color"]
                        shape = page.new_shape()
                        shape.draw_rect(r)
                        shape.finish(fill=color, color=color)
                        shape.commit()
                except:
                    pass
        
        # Optie 2: Mask dynamische zones
        for zone in config["zones"]:
            x, y, w, h = zone["rect"]
            color = zone["color"]
            rect = fitz.Rect(x, y, x + w, y + h)
            shape = page.new_shape()
            shape.draw_rect(rect)
            shape.finish(fill=color, color=color)
            shape.commit()
        
        # Render naar PNG
        pix = page.get_pixmap(dpi=dpi)
        out_path = output_dir / f"stationery_{cp.page_type.value}.png"
        pix.save(str(out_path))
        print(f"  {cp.page_type.value}: masked & gerenderd -> {out_path.name}")
        
        tmp_doc.close()
    
    doc.close()
    
    # Stap 3: Maak ook een content pagina stationery (header/footer template)
    print("[3/3] Generating content page stationery...")
    # Pak een typische content pagina (bijv. pagina 4)
    tmp_doc = fitz.open(str(pdf_path))
    content_page_idx = 3  # pagina 4 (0-based)
    page = tmp_doc[content_page_idx]
    
    # Mask alles behalve header en footer
    shape = page.new_shape()
    # Wis het content-gebied (midden van de pagina)
    content_rect = fitz.Rect(0, 70, 595, 800)  # alles behalve header/footer
    shape.draw_rect(content_rect)
    shape.finish(fill=(1, 1, 1), color=(1, 1, 1))
    shape.commit()
    
    pix = page.get_pixmap(dpi=dpi)
    out_path = output_dir / "stationery_content.png"
    pix.save(str(out_path))
    print(f"  content: masked & gerenderd -> {out_path.name}")
    tmp_doc.close()
    
    print(f"\n{'=' * 60}")
    print(f"DONE - {len(list(output_dir.glob('*.png')))} stationery bestanden in:")
    print(f"  {output_dir}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    create_stationery(PDF, OUT)
