"""Test B5 huisstijl extractie pipeline."""
import sys
sys.path.insert(0, r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src")

from pathlib import Path
from bm_reports.tools.pdf_extractor import extract_pdf
from bm_reports.tools.page_classifier import classify_pages
from bm_reports.tools.layout_extractor import extract_page_layouts

PDF = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\2707_BBLrapportage_v01.pdf")
OUT = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\test_output\b5_test")

print("=" * 60)
print("B5 HUISSTIJL EXTRACTIE TEST")
print("=" * 60)

# Stap 1: Extract PDF
print("\n[1/3] Extracting PDF elements...")
pages = extract_pdf(PDF, OUT / "pages", dpi=150)
print(f"  Pagina's: {len(pages)}")
for p in pages:
    print(f"  Pagina {p.page_number}: {len(p.texts)} teksten, {len(p.rects)} rects, {len(p.images)} images, {len(p.paths)} paths")

# Stap 2: Classify pages
print("\n[2/3] Classifying pages...")
classified = classify_pages(pages)
for cp in classified:
    print(f"  Pagina {cp.page.page_number}: {cp.page_type.value} (confidence: {cp.confidence:.2f})")

# Stap 3: Extract layouts
print("\n[3/3] Extracting page layouts...")
layouts = extract_page_layouts(classified)
for page_type, layout in layouts.items():
    print(f"\n  === {page_type.value.upper()} (pagina {layout.page_number}) ===")
    print(f"  Formaat: {layout.width_pt:.0f} x {layout.height_pt:.0f} pt")
    print(f"  Statische elementen: {len(layout.static_elements)}")
    for se in layout.static_elements:
        detail = f"    {se.element_type}: ({se.x_pt:.0f}, {se.y_pt:.0f}) {se.width_pt:.0f}x{se.height_pt:.0f}"
        if se.fill_color:
            detail += f" fill={se.fill_color}"
        if se.image_role:
            detail += f" role={se.image_role}"
        if se.points:
            detail += f" {len(se.points)} points"
        print(detail)
    
    print(f"  Tekst zones: {len(layout.text_zones)}")
    for tz in layout.text_zones:
        dyn = "DYNAMIC" if tz.is_dynamic else "static"
        print(f"    {tz.name}: \"{tz.font}\" {tz.size}pt @ ({tz.x_pt:.0f}, {tz.y_pt:.0f}) [{dyn}]")
    
    print(f"  Badges: {len(layout.badges)}")
    for b in layout.badges:
        print(f"    \"{b.label}\" bg={b.bg_color} @ ({b.x_pt:.0f}, {b.y_pt:.0f})")
    
    if layout.clip_polygon:
        print(f"  Clip polygon: {len(layout.clip_polygon)} punten")
    if layout.photo_rect:
        print(f"  Photo rect: {layout.photo_rect}")

print("\n" + "=" * 60)
print("DONE — Output in:", OUT)
print("=" * 60)
