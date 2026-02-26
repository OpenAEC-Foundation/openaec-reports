"""Minimal font diagnostics."""
import sys
from pathlib import Path

outpath = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\font_diag.txt")

try:
    out = ["=== Start ==="]
    
    # Font files
    font_dir = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src\bm_reports\assets\fonts")
    out.append(f"Font dir exists: {font_dir.exists()}")
    if font_dir.exists():
        for f in sorted(font_dir.iterdir()):
            out.append(f"  {f.name} ({f.stat().st_size / 1024:.1f} KB)")
    
    # Try import
    sys.path.insert(0, r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src")
    out.append(f"\nPython: {sys.version}")
    
    try:
        import reportlab
        out.append(f"ReportLab: {reportlab.Version}")
    except ImportError as e:
        out.append(f"ReportLab NOT INSTALLED: {e}")
    
    try:
        from bm_reports.core.fonts import register_fonts, fonts_status
        result = register_fonts()
        out.append("\n=== Registration ===")
        for name, effective in result.items():
            out.append(f"  {name}: {effective}")
    except Exception as e:
        import traceback
        out.append(f"\nFont import error: {e}")
        out.append(traceback.format_exc())
    
    # Logo files
    out.append("\n=== Logos ===")
    logo_dir = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src\bm_reports\assets\logos")
    for f in sorted(logo_dir.iterdir()):
        if f.is_file():
            out.append(f"  {f.name} ({f.stat().st_size / 1024:.1f} KB)")
    
    outpath.write_text("\n".join(out), encoding="utf-8")

except Exception as e:
    outpath.write_text(f"FATAL: {e}\n{sys.exc_info()}", encoding="utf-8")
