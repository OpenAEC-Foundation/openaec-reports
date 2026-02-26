"""Meet echte tekstbreedte van Gotham-Book bij 9.5pt."""
import fitz
from pathlib import Path

FONT = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src\bm_reports\assets\fonts\Gotham-Book.ttf")

# Laad font
font = fitz.Font(fontfile=str(FONT))

# Test regels uit originele pagina 7 - deze passen precies in de marge
test_lines = [
    "Woning type B is met het huidige ontwerp niet te realiseren in de oksel. Op ande",
    "plekken in het gebouw kan dit type wel worden gemaakt.",
    "Bij alle woningen wordt de ventilatie gerealiseerd met centraal gestuurd",
    "mechanische toe- en afvoer (gebalanceerde ventilatie). In de woningen wordt een",
    "Op dit moment zijn er 44 parkeerplekken in het VO ingetekend. Echter deze plekke",
]

print("Gotham-Book 9.5pt tekstbreedtes:")
for line in test_lines:
    w = font.text_length(line, fontsize=9.5)
    print(f"  {w:.1f}pt  \"{line[:60]}...\"" if len(line) > 60 else f"  {w:.1f}pt  \"{line}\"")

# Max breedte voor bullet text (x=143.4) en body (x=125.4)
print(f"\nPagina breedte: 595.3")
print(f"Body text start: 125.4")
print(f"Bullet text start: 143.4")
print(f"Paginanr x: 533.0")

# Bereken juiste rechterrand
# Origineel: tekst stopt rond x=531 (net links van paginanummer)
# Maar body op x=125.4 heeft bredere regels dan bullets op x=143.4
max_body_w = max(font.text_length(l, fontsize=9.5) for l in test_lines if l.startswith("Op"))
max_bullet_w = max(font.text_length(l, fontsize=9.5) for l in test_lines if not l.startswith("Op"))
print(f"\nMax body breedte: {max_body_w:.1f}pt -> rechterrand: {125.4 + max_body_w:.1f}")
print(f"Max bullet breedte: {max_bullet_w:.1f}pt -> rechterrand: {143.4 + max_bullet_w:.1f}")

# Helv vergelijking
print(f"\nHelv 9.5pt vergelijking:")
for line in test_lines[:2]:
    w_helv = fitz.get_text_length(line, fontname="helv", fontsize=9.5)
    w_gotham = font.text_length(line, fontsize=9.5)
    print(f"  Helv={w_helv:.1f} Gotham={w_gotham:.1f} ratio={w_gotham/w_helv:.3f}")
