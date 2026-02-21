"""Compare logos and generate test PDF for comparison."""
import sys
sys.path.insert(0, r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src")

from pathlib import Path
from PIL import Image

out = []

# Compare logo sizes
out.append("=== Logo Vergelijking ===\n")

asset_logos = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src\bm_reports\assets\logos")
orig_logos = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\logo's\RGB\PNG")

out.append("Assets logos:")
for f in sorted(asset_logos.glob("*.png")):
    try:
        img = Image.open(f)
        out.append(f"  {f.name}: {img.size[0]}x{img.size[1]}px, {f.stat().st_size/1024:.1f}KB, mode={img.mode}")
    except Exception as e:
        out.append(f"  {f.name}: ERROR {e}")

out.append("\nOriginal logos:")
for f in sorted(orig_logos.glob("*.png")):
    try:
        img = Image.open(f)
        out.append(f"  {f.name}: {img.size[0]}x{img.size[1]}px, {f.stat().st_size/1024:.1f}KB, mode={img.mode}")
    except Exception as e:
        out.append(f"  {f.name}: ERROR {e}")

# Also check SVG logos
out.append("\nAssets SVG logos:")
for f in sorted(asset_logos.glob("*.svg")):
    out.append(f"  {f.name}: {f.stat().st_size/1024:.1f}KB")

orig_svg = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\logo's\RGB\SVG")
if orig_svg.exists():
    out.append("\nOriginal SVG logos:")
    for f in sorted(orig_svg.glob("*.svg")):
        out.append(f"  {f.name}: {f.stat().st_size/1024:.1f}KB")

# Check what the reference PDF actually has embedded
out.append("\n=== Style Analysis ===\n")

# Check current styles vs spec
from bm_reports.core.fonts import register_fonts, get_font_name
register_fonts()

from bm_reports.core.styles import create_stylesheet, BM_FONTS, BM_COLORS
from bm_reports.core.brand import BrandLoader

brand = BrandLoader().load("3bm_cooperatie")
styles = create_stylesheet(brand=brand)

out.append(f"BM_FONTS.heading = {BM_FONTS.heading}")
out.append(f"BM_FONTS.body = {BM_FONTS.body}")
out.append(f"BM_FONTS.body_size = {BM_FONTS.body_size}")
out.append(f"BM_FONTS.heading1_size = {BM_FONTS.heading1_size}")
out.append(f"BM_FONTS.heading2_size = {BM_FONTS.heading2_size}")

for name in ["Normal", "Heading1", "Heading2", "Heading3", "CoverTitle", "CoverSubtitle"]:
    s = styles[name]
    out.append(f"\n{name}:")
    out.append(f"  fontName: {s.fontName}")
    out.append(f"  fontSize: {s.fontSize}")
    out.append(f"  leading: {s.leading}")
    out.append(f"  textColor: {s.textColor}")

# Check brand config
out.append(f"\n=== Brand Config ===")
out.append(f"fonts: {brand.fonts}")
out.append(f"colors: {brand.colors}")
out.append(f"styles keys: {list(brand.styles.keys())}")

outpath = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\style_diag.txt")
outpath.write_text("\n".join(out), encoding="utf-8")
