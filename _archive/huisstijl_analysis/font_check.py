"""Quick font diagnostics."""
import sys
sys.path.insert(0, r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src")

from pathlib import Path

# Check font files exist
font_dir = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src\bm_reports\assets\fonts")
print("=== Font Files ===")
for f in sorted(font_dir.iterdir()):
    print(f"  {f.name} ({f.stat().st_size / 1024:.1f} KB)")

print()

# Try registering
from bm_reports.core.fonts import register_fonts, fonts_status, FONTS_DIR
print(f"FONTS_DIR: {FONTS_DIR}")
print(f"FONTS_DIR exists: {FONTS_DIR.exists()}")
print()

result = register_fonts()
print("=== Registration Result ===")
for name, effective in result.items():
    status = "OK (Gotham)" if name == effective else f"FALLBACK -> {effective}"
    print(f"  {name}: {status}")

print()
print("=== Font Status ===")
for name, st in fonts_status().items():
    print(f"  {name}: {st}")

# Also check if ReportLab can actually use the fonts
print()
print("=== ReportLab Font Test ===")
try:
    from reportlab.pdfbase import pdfmetrics
    for name in ["GothamBold", "GothamBook", "GothamMedium", "GothamBookItalic"]:
        try:
            font = pdfmetrics.getFont(name)
            print(f"  {name}: OK - {type(font).__name__}")
        except KeyError:
            print(f"  {name}: NOT REGISTERED")
except Exception as e:
    print(f"  Error: {e}")

# Check logo files
print()
print("=== Logo Files ===")
logo_dir = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src\bm_reports\assets\logos")
for f in sorted(logo_dir.iterdir()):
    if f.is_file():
        print(f"  {f.name} ({f.stat().st_size / 1024:.1f} KB)")

# Compare with original logos
print()
print("=== Original Logo Files ===")
orig_dir = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\logo's\RGB\PNG")
if orig_dir.exists():
    for f in sorted(orig_dir.iterdir()):
        if f.is_file():
            print(f"  {f.name} ({f.stat().st_size / 1024:.1f} KB)")
