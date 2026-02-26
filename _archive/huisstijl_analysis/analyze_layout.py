"""Extract text blocks, images, and drawing elements with exact coordinates from PDF.
Focus on key pages: cover(1), colofon(2), TOC(3), content(4-5), backcover(36)."""
import fitz
import json
from pathlib import Path

pdf_path = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\2707_BBLrapportage_v01.pdf")
doc = fitz.open(str(pdf_path))

# Pages to analyze in detail
key_pages = [0, 1, 2, 3, 4, 5, 6, 20, 35]  # 0-indexed

results = {}

for page_idx in key_pages:
    if page_idx >= len(doc):
        continue
    page = doc[page_idx]
    pw = page.rect.width
    ph = page.rect.height
    
    page_data = {
        "page_number": page_idx + 1,
        "width_pt": round(pw, 2),
        "height_pt": round(ph, 2),
        "width_mm": round(pw / 2.8346, 1),
        "height_mm": round(ph / 2.8346, 1),
    }
    
    # Extract text blocks with positions
    text_blocks = []
    blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
    for block in blocks.get("blocks", []):
        if block.get("type") == 0:  # text block
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue
                    bbox = span.get("bbox", [0,0,0,0])
                    text_blocks.append({
                        "text": text[:80],
                        "x": round(bbox[0], 1),
                        "y_top": round(bbox[1], 1),
                        "x2": round(bbox[2], 1),
                        "y_bottom": round(bbox[3], 1),
                        "font": span.get("font", ""),
                        "size": round(span.get("size", 0), 1),
                        "color": span.get("color", 0),
                        # Convert color int to hex
                        "color_hex": "#{:06x}".format(span.get("color", 0)),
                    })
    
    page_data["text_blocks"] = text_blocks
    
    # Extract images
    images = []
    for img in page.get_images(full=True):
        xref = img[0]
        images.append({
            "xref": xref,
            "width": img[2],
            "height": img[3],
        })
    page_data["images_count"] = len(images)
    
    # Extract drawings (paths, rects, lines)
    drawings = []
    for d in page.get_drawings():
        draw_info = {
            "type": d.get("type", ""),
            "rect": [round(x, 1) for x in d.get("rect", fitz.Rect()).irect],
            "fill": d.get("fill"),
            "stroke_opacity": d.get("stroke_opacity"),
            "fill_opacity": d.get("fill_opacity"),
            "color": d.get("color"),
            "width": d.get("width"),
        }
        # Convert fill color tuple to hex if present
        if d.get("fill"):
            try:
                r, g, b = d["fill"]
                draw_info["fill_hex"] = "#{:02x}{:02x}{:02x}".format(int(r*255), int(g*255), int(b*255))
            except:
                pass
        if d.get("color"):
            try:
                r, g, b = d["color"]
                draw_info["color_hex"] = "#{:02x}{:02x}{:02x}".format(int(r*255), int(g*255), int(b*255))
            except:
                pass
        drawings.append(draw_info)
    
    page_data["drawings_count"] = len(drawings)
    # Only include first 30 drawings to keep output manageable
    page_data["drawings"] = drawings[:30]
    
    results[f"page_{page_idx+1}"] = page_data

doc.close()

out_path = pdf_path.parent / "layout_analysis.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"Analysis saved to {out_path}")
print(f"Analyzed {len(results)} pages")
