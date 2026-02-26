import fitz
import sys
sys.stdout.reconfigure(encoding='utf-8')

pdf_path = r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\2707_BBLrapportage_v01.pdf"
doc = fitz.open(pdf_path)

pages_to_analyze = [0, 1, 2, 3, len(doc)-1]

for page_idx in pages_to_analyze:
    page = doc[page_idx]
    print(f"\n{'='*60}")
    print(f"PAGE {page_idx + 1} (size: {page.rect.width:.0f} x {page.rect.height:.0f} pt)")
    print(f"{'='*60}")
    
    print("\n--- TEXT BLOCKS ---")
    blocks = page.get_text("dict")["blocks"]
    for block in blocks:
        if block["type"] == 0:
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if text:
                        bbox = span["bbox"]
                        print(f"  [{bbox[0]:.0f},{bbox[1]:.0f} -> {bbox[2]:.0f},{bbox[3]:.0f}] "
                              f"font={span['font']}, size={span['size']:.1f}, "
                              f"color=#{span['color']:06x}: \"{text[:80]}\"")
    
    print("\n--- IMAGES ---")
    images = page.get_images()
    for img in images:
        xref = img[0]
        print(f"  Image xref={xref}, size={img[2]}x{img[3]}")
    
    print("\n--- DRAWINGS (first 20) ---")
    drawings = page.get_drawings()
    for d in drawings[:20]:
        items_desc = []
        for item in d["items"]:
            if item[0] == "re":
                rect = item[1]
                items_desc.append(f"rect({rect.x0:.0f},{rect.y0:.0f},{rect.width:.0f}x{rect.height:.0f})")
            elif item[0] == "l":
                items_desc.append(f"line({item[1].x:.0f},{item[1].y:.0f}->{item[2].x:.0f},{item[2].y:.0f})")
            elif item[0] == "c":
                items_desc.append("curve")
        fill = d.get("fill")
        stroke = d.get("color")
        fill_str = f"fill=rgb({fill[0]:.2f},{fill[1]:.2f},{fill[2]:.2f})" if fill else "no-fill"
        stroke_str = f"stroke=rgb({stroke[0]:.2f},{stroke[1]:.2f},{stroke[2]:.2f})" if stroke else "no-stroke"
        if items_desc:
            print(f"  {' | '.join(items_desc)} {fill_str} {stroke_str}")
    if len(drawings) > 20:
        print(f"  ... +{len(drawings)-20} more drawings")

doc.close()
