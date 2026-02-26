"""Meet bijlage titel breedtes bij verschillende fontsizes."""
import fitz
from pathlib import Path

font = fitz.Font(fontfile=str(Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src\bm_reports\assets\fonts\Gotham-Book.ttf")))

titles = ["Bouwbesluittoets en", "Sonderingsgegevens en", "funderingsadvies", "daglichttoetsing"]
available_width = 595.3 - 136.1  # = 459.2pt

print(f"Beschikbare breedte: {available_width:.1f}pt")
print()
for size in [41.4, 36.0, 32.0, 28.0]:
    print(f"--- {size}pt ---")
    for t in titles:
        w = font.text_length(t, fontsize=size)
        ok = "OK" if w < available_width else "OVERFLOW"
        print(f"  {w:6.1f}pt  {ok}  \"{t}\"")
    print()
