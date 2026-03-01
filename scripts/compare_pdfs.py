"""Analyse reference vs generated PDF for pixel-precise comparison."""
import fitz
import json

REF = r"C:\Users\joche\Desktop\336.01-BIC Factuur_BIC.pdf"
GEN = r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\output\test_template_e2e.pdf"

def analyze_page_text(page, page_num):
    """Extract all text blocks with exact positions."""
    blocks = page.get_text("dict")["blocks"]
    result = []
    for b in blocks:
        if b["type"] != 0:  # text blocks only
            continue
        for line in b["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                if not text:
                    continue
                bbox = span["bbox"]
                result.append({
                    "text": text[:60],
                    "x": round(bbox[0], 1),
                    "y": round(bbox[1], 1),
                    "x1": round(bbox[2], 1),
                    "y1": round(bbox[3], 1),
                    "font": span["font"],
                    "size": round(span["size"], 1),
                })
    return result

ref = fitz.open(REF)
gen = fitz.open(GEN)

print(f"=== PAGE COUNT: ref={len(ref)}, gen={len(gen)} ===\n")

for i in range(min(len(ref), len(gen))):
    rp = ref[i]
    gp = gen[i]
    rr = rp.rect
    gr = gp.rect
    orient_r = "L" if rr.width > rr.height else "P"
    orient_g = "L" if gr.width > gr.height else "P"
    
    print(f"{'='*70}")
    print(f"PAGE {i+1}: ref={rr.width:.0f}x{rr.height:.0f}({orient_r}) gen={gr.width:.0f}x{gr.height:.0f}({orient_g})")
    print(f"{'='*70}")
    
    ref_texts = analyze_page_text(rp, i+1)
    gen_texts = analyze_page_text(gp, i+1)
    
    print(f"\n--- REFERENCE ({len(ref_texts)} spans) ---")
    for t in ref_texts:
        print(f"  [{t['x']:6.1f}, {t['y']:6.1f}] {t['size']:5.1f}pt {t['font'][:20]:<20s} | {t['text']}")
    
    print(f"\n--- GENERATED ({len(gen_texts)} spans) ---")
    for t in gen_texts:
        print(f"  [{t['x']:6.1f}, {t['y']:6.1f}] {t['size']:5.1f}pt {t['font'][:20]:<20s} | {t['text']}")
    
    # Find "Pagina" references
    pag_refs = [t for t in ref_texts if "Pagina" in t["text"] or "pagina" in t["text"].lower()]
    if pag_refs:
        print(f"\n>>> PAGE NUMBERING in reference:")
        for p in pag_refs:
            print(f"    '{p['text']}' at [{p['x']}, {p['y']}] font={p['font']} size={p['size']}")
    
    print()

ref.close()
gen.close()
