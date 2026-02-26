"""Analyseer TOC pagina (pagina 3) uit BBL rapport voor layout/marges."""
import fitz

bbl = fitz.open(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\2707_BBLrapportage_v01.pdf")
p = bbl[2]  # pagina 3 = TOC
ph = p.rect.height

print(f"Pagina formaat: {p.rect.width:.1f} x {ph:.1f} pt")
print()

# Alle tekst met posities
texts = []
for block in p.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]:
    if block.get("type") != 0:
        continue
    for line in block["lines"]:
        for span in line["spans"]:
            t = span["text"].strip()
            if not t:
                continue
            bbox = span["bbox"]
            c = span["color"]
            r = (c >> 16) & 0xFF; g = (c >> 8) & 0xFF; b = c & 0xFF
            texts.append({
                "text": t,
                "x": bbox[0], "x2": bbox[2],
                "y_td": bbox[1], "y_td_bottom": bbox[3],
                "font": span["font"],
                "size": span["size"],
                "color": f"#{r:02X}{g:02X}{b:02X}",
            })

texts.sort(key=lambda t: t["y_td"])

print("--- ALLE TEKST (gesorteerd top-down) ---")
for t in texts:
    print(f"  [{t['size']:.1f}pt] [{t['font']}] [{t['color']}] x={t['x']:.1f}-{t['x2']:.1f} y_td={t['y_td']:.1f}")
    print(f"    \"{t['text']}\"")

# Bereken marges
print()
print("--- AFGELEIDE MARGES ---")
x_vals = [t["x"] for t in texts if t["text"] != "3"]  # exclude paginanummer
x2_vals = [t["x2"] for t in texts if t["text"] != "3"]
y_vals = [t["y_td"] for t in texts if t["text"] != "3"]
y2_vals = [t["y_td_bottom"] for t in texts if t["text"] != "3"]

if x_vals:
    print(f"  Links (min x):    {min(x_vals):.1f} pt")
    print(f"  Rechts (max x2):  {max(x2_vals):.1f} pt  -> marge rechts = {p.rect.width - max(x2_vals):.1f} pt")
    print(f"  Boven (min y_td): {min(y_vals):.1f} pt")
    print(f"  Onder (max y_td): {max(y2_vals):.1f} pt  -> marge onder = {ph - max(y2_vals):.1f} pt")

# Ook content pagina's (4,5) voor vergelijking
print()
print("--- CONTENT PAGINA MARGES (pagina 4-5) ---")
for pg_idx in [3, 4]:
    p2 = bbl[pg_idx]
    ctexts = []
    for block in p2.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                t = span["text"].strip()
                if t and not t.isdigit():
                    bbox = span["bbox"]
                    ctexts.append({"x": bbox[0], "x2": bbox[2], "y_td": bbox[1], "y_td_bottom": bbox[3], "text": t})
    if ctexts:
        print(f"  Pagina {pg_idx+1}: x={min(t['x'] for t in ctexts):.1f}-{max(t['x2'] for t in ctexts):.1f}  y={min(t['y_td'] for t in ctexts):.1f}-{max(t['y_td_bottom'] for t in ctexts):.1f}")

bbl.close()
