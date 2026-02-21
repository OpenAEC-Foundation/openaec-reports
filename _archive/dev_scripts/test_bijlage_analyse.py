"""Analyseer bijlagen.pdf template + BBL rapport bijlagenpagina (pagina 21)."""
import fitz

# === 1. bijlagen.pdf template ===
print("=" * 60)
print("1. BIJLAGEN.PDF TEMPLATE")
print("=" * 60)
doc = fitz.open(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\paginas\bijlagen.pdf")
p = doc[0]
print(f"Formaat: {p.rect.width:.1f} x {p.rect.height:.1f} pt")

for block in p.get_text("dict")["blocks"]:
    if block.get("type") != 0:
        continue
    for line in block["lines"]:
        for span in line["spans"]:
            t = span["text"].strip()
            if t:
                bbox = span["bbox"]
                c = span["color"]
                r = (c >> 16) & 0xFF; g = (c >> 8) & 0xFF; b = c & 0xFF
                print(f"  [{span['size']:.1f}pt] [{span['font']}] [#{r:02X}{g:02X}{b:02X}] x={bbox[0]:.1f} y_td={bbox[1]:.1f}: \"{t}\"")

drawings = p.get_drawings()
print(f"\nDrawings: {len(drawings)}")
for i, d in enumerate(drawings):
    r = d.get("rect")
    fill = d.get("fill")
    if r and fill and r.width > 10:
        print(f"  [{i}] rect: ({r.x0:.1f}, {r.y0:.1f}) {r.width:.1f}x{r.height:.1f} fill={fill}")
doc.close()

# === 2. BBL rapport bijlagenpagina (pagina 21) ===
print()
print("=" * 60)
print("2. BBL RAPPORT - BIJLAGE DIVIDER (pagina 21)")
print("=" * 60)
bbl = fitz.open(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\2707_BBLrapportage_v01.pdf")
p = bbl[20]  # pagina 21 = bijlage divider
print(f"Formaat: {p.rect.width:.1f} x {p.rect.height:.1f} pt")

texts = []
for block in p.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]:
    if block.get("type") != 0:
        continue
    for line in block["lines"]:
        for span in line["spans"]:
            t = span["text"].strip()
            if t:
                bbox = span["bbox"]
                c = span["color"]
                r = (c >> 16) & 0xFF; g = (c >> 8) & 0xFF; b = c & 0xFF
                texts.append({
                    "text": t, "x": bbox[0], "y_td": bbox[1],
                    "font": span["font"], "size": span["size"],
                    "color": f"#{r:02X}{g:02X}{b:02X}"
                })

texts.sort(key=lambda t: t["y_td"])
for t in texts:
    print(f"  [{t['size']:.1f}pt] [{t['font']}] [{t['color']}] x={t['x']:.1f} y_td={t['y_td']:.1f}: \"{t['text']}\"")

# Check for large colored rectangles
print(f"\nDrawings: {len(p.get_drawings())}")
for i, d in enumerate(p.get_drawings()):
    r = d.get("rect")
    fill = d.get("fill")
    if r and fill and r.width > 50:
        print(f"  [{i}] rect: ({r.x0:.1f}, {r.y0:.1f}) {r.width:.1f}x{r.height:.1f} fill={fill}")

bbl.close()
