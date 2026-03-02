"""Eenmalig script: extraheer stationery voor 3BM Cooperatie."""

from pathlib import Path

from openaec_reports.tools.stationery_extractor import StationeryExtractor

SOURCE = Path("huisstijl/2707_BBLrapportage_v01.pdf")
OUTPUT = Path("src/openaec_reports/assets/graphics")

if not SOURCE.exists():
    print(f"FOUT: Referentie-PDF niet gevonden: {SOURCE}")
    raise SystemExit(1)

ext = StationeryExtractor(SOURCE)

# Backcover (pagina 36 = index 35) — volledig, geen tekst strippen
ext.extract_full_page(35, OUTPUT / "3bm-backcover.pdf")
print(f"  Backcover → {OUTPUT / '3bm-backcover.pdf'}")

# Appendix divider (pagina 21 = index 20) — strip bijlage nummer + titel
ext.extract_stripped_page(20, OUTPUT / "3bm-appendix-divider.pdf", strip_zones=[
    (80, 170, 500, 220),    # "Bijlage N" zone
    (80, 240, 500, 340),    # Titel zone
])
print(f"  Appendix divider → {OUTPUT / '3bm-appendix-divider.pdf'}")

# Cover (pagina 1 = index 0) — strip titel + subtitel
ext.extract_stripped_page(0, OUTPUT / "3bm-cover.pdf", strip_zones=[
    (40, 700, 540, 780),    # Titel zone
    (40, 780, 540, 820),    # Subtitel zone
])
print(f"  Cover → {OUTPUT / '3bm-cover.pdf'}")

# Briefpapier — kopieer als het bestaat
import shutil
briefpapier = Path("huisstijl/3BM-Briefpapier-Digitaal.pdf")
if briefpapier.exists():
    shutil.copy(briefpapier, OUTPUT / "3bm-briefpapier.pdf")
    print(f"  Briefpapier → {OUTPUT / '3bm-briefpapier.pdf'}")
else:
    print(f"  Briefpapier niet gevonden: {briefpapier} (skip)")

print()
print(f"Stationery bestanden geextraheerd naar: {OUTPUT}")
print("CONTROLEER visueel of de juiste zones geript zijn!")
print("Pas strip_zones aan en run opnieuw indien nodig.")
