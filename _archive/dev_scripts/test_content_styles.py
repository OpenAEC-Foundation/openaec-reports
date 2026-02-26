"""Analyseer pagina 7 van BBL rapport voor content block styling."""
import fitz

bbl = fitz.open(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\2707_BBLrapportage_v01.pdf")
p = bbl[6]  # pagina 7
ph = p.rect.height

print(f"Pagina 7 - Formaat: {p.rect.width:.1f} x {ph:.1f} pt")
print()

# Alle tekst met volledige metadata
print("--- ALLE TEKST (gesorteerd top-down) ---")
texts = []
for block in p.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]:
    if block.get("type") != 0:
        continue
    for line in block["lines"]:
        for span in line["spans"]:
            t = span["text"]
            t_stripped = t.strip()
            if not t_stripped:
                continue
            bbox = span["bbox"]
            c = span["color"]
            r = (c >> 16) & 0xFF; g = (c >> 8) & 0xFF; b = c & 0xFF
            texts.append({
                "text": t_stripped,
                "raw": t,
                "x": bbox[0], "x2": bbox[2],
                "y_td": bbox[1], "y_bottom": bbox[3],
                "font": span["font"],
                "size": span["size"],
                "color": f"#{r:02X}{g:02X}{b:02X}",
                "flags": span.get("flags", 0),
            })

texts.sort(key=lambda t: (t["y_td"], t["x"]))

# Groepeer per unieke stijl
styles = {}
for t in texts:
    key = f"{t['font']}_{t['size']:.1f}_{t['color']}"
    if key not in styles:
        styles[key] = {"font": t["font"], "size": t["size"], "color": t["color"], "x_positions": set(), "count": 0, "examples": []}
    styles[key]["x_positions"].add(round(t["x"], 1))
    styles[key]["count"] += 1
    if len(styles[key]["examples"]) < 3:
        styles[key]["examples"].append(t["text"][:60])

print("--- STIJL OVERZICHT ---")
for key, s in sorted(styles.items(), key=lambda x: -x[1]["size"]):
    print(f"\n  [{s['size']:.1f}pt] [{s['font']}] [{s['color']}]")
    print(f"    x-posities: {sorted(s['x_positions'])}")
    print(f"    Aantal spans: {s['count']}")
    for ex in s["examples"]:
        print(f"    > \"{ex}\"")

print()
print("--- VOLLEDIGE TEKST MET POSITIES ---")
prev_y = 0
for t in texts:
    gap = t["y_td"] - prev_y if prev_y > 0 else 0
    marker = "  GAP={:.1f}".format(gap) if gap > 15 else ""
    print(f"  [{t['size']:.1f}pt] [{t['font']}] [{t['color']}] x={t['x']:.1f} y={t['y_td']:.1f}{marker}")
    print(f"    \"{t['text'][:80]}\"")
    prev_y = t["y_td"]

# Check ook pagina 5 en 8 voor meer block types
print()
print("=" * 60)
print("EXTRA: pagina 5 (inleiding) en 8 (tabellen?)")
print("=" * 60)
for pg_idx in [4, 7]:
    p2 = bbl[pg_idx]
    print(f"\n--- Pagina {pg_idx+1} stijlen ---")
    pstyles = {}
    for block in p2.get_text("dict")["blocks"]:
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
                key = f"{span['font']}_{span['size']:.1f}_#{r:02X}{g:02X}{b:02X}"
                if key not in pstyles:
                    pstyles[key] = {"x_pos": set(), "examples": []}
                pstyles[key]["x_pos"].add(round(bbox[0], 1))
                if len(pstyles[key]["examples"]) < 2:
                    pstyles[key]["examples"].append(f"x={bbox[0]:.1f} y={bbox[1]:.1f}: \"{t[:50]}\"")
    for key, s in pstyles.items():
        print(f"  {key}  x={sorted(s['x_pos'])}")
        for ex in s["examples"]:
            print(f"    {ex}")

bbl.close()
