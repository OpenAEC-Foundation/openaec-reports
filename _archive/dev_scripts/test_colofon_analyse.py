"""Analyseer standaard.pdf achtergrond en extraheer colofon data uit BBL rapport."""
import sys
sys.path.insert(0, r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src")

import fitz
from pathlib import Path

# === 1. Standaard pagina achtergrond ===
print("=" * 60)
print("1. STANDAARD.PDF ANALYSE")
print("=" * 60)
std = fitz.open(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\paginas\standaard.pdf")
p = std[0]
print(f"Paginas: {len(std)}")
print(f"Formaat: {p.rect.width:.1f} x {p.rect.height:.1f} pt")
print(f"Teksten: {len(p.get_text('dict')['blocks'])}")
# Lijst alle tekst
for block in p.get_text("dict")["blocks"]:
    if block.get("type") != 0:
        continue
    for line in block["lines"]:
        for span in line["spans"]:
            t = span["text"].strip()
            if t:
                print(f"  [{span['size']:.1f}pt] [{span['font']}] @ y={span['bbox'][1]:.1f}: \"{t}\"")
std.close()

# === 2. Colofon.pdf (als die er ook is) ===
print()
print("=" * 60)
print("2. COLOFON.PDF ANALYSE")
print("=" * 60)
col = fitz.open(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\paginas\colofon.pdf")
p = col[0]
print(f"Formaat: {p.rect.width:.1f} x {p.rect.height:.1f} pt")
for block in p.get_text("dict")["blocks"]:
    if block.get("type") != 0:
        continue
    for line in block["lines"]:
        for span in line["spans"]:
            t = span["text"].strip()
            if t:
                bbox = span["bbox"]
                print(f"  [{span['size']:.1f}pt] [{span['font']}] [{span['color']}] @ x={bbox[0]:.1f} y={bbox[1]:.1f}: \"{t}\"")
# Check drawings/rects
drawings = p.get_drawings()
print(f"\nDrawings: {len(drawings)}")
for i, d in enumerate(drawings):
    r = d.get("rect")
    fill = d.get("fill")
    if r and fill:
        print(f"  [{i}] rect: ({r.x0:.1f}, {r.y0:.1f}) {r.width:.1f}x{r.height:.1f} fill={fill}")
col.close()

# === 3. BBL rapport colofon (pagina 2) - volledige data ===
print()
print("=" * 60)
print("3. BBL RAPPORT - COLOFON (pagina 2)")
print("=" * 60)
bbl = fitz.open(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\2707_BBLrapportage_v01.pdf")
p = bbl[1]  # pagina 2 = colofon
ph = p.rect.height
print(f"Formaat: {p.rect.width:.1f} x {p.rect.height:.1f} pt")

print("\n--- TEKST (gesorteerd op y-positie) ---")
texts = []
for block in p.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]:
    if block.get("type") != 0:
        continue
    for line in block["lines"]:
        for span in line["spans"]:
            t = span["text"].strip()
            if t:
                bbox = span["bbox"]
                color_int = span["color"]
                r = (color_int >> 16) & 0xFF
                g = (color_int >> 8) & 0xFF
                b = color_int & 0xFF
                texts.append({
                    "text": t,
                    "x": bbox[0],
                    "y": bbox[1],
                    "y_bottom": bbox[3],
                    "x2": bbox[2],
                    "font": span["font"],
                    "size": span["size"],
                    "color": f"#{r:02X}{g:02X}{b:02X}",
                })

# Sorteer op y-positie (top-down)
texts.sort(key=lambda t: t["y"])
for t in texts:
    y_pdf = ph - t["y"]  # PDF-native y (bottom-up)
    print(f"  [{t['size']:.1f}pt] [{t['font']}] [{t['color']}] x={t['x']:.1f} y_td={t['y']:.1f} y_pdf={y_pdf:.1f} w={t['x2']-t['x']:.0f}")
    print(f"    \"{t['text']}\"")

print("\n--- LIJNEN ---")
for d in p.get_drawings():
    r = d.get("rect")
    if r and (abs(r.height) < 2):  # horizontale lijnen
        color = d.get("color")
        print(f"  Lijn: y_td={r.y0:.1f} y_pdf={ph-r.y0:.1f} x={r.x0:.1f}-{r.x1:.1f} color={color}")

bbl.close()
