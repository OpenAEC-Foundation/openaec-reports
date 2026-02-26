"""Genereer een voorbeeld rapport PDF."""
import sys
sys.path.insert(0, r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src")

from pathlib import Path
from bm_reports.core.engine import Report

json_path = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\voorbeeld_rapport.json")
output_path = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\voorbeeld_rapport.pdf")

try:
    report = Report.from_json(json_path, brand="3bm_cooperatie")
    result = report.build(output_path)
    print(f"OK: {result} ({result.stat().st_size / 1024:.0f} KB)")
except Exception as e:
    print(f"FOUT: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
