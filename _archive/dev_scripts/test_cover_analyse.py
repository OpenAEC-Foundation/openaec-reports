"""Analyseer cover PNG (alpha channel) en haal tekst-posities uit PDF."""
import sys
sys.path.insert(0, r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src")

from PIL import Image
import numpy as np
import fitz
from pathlib import Path

# === 1. PNG alpha analyse ===
print("=" * 60)
print("1. PNG ALPHA ANALYSE")
print("=" * 60)
img = Image.open(r'C:\Users\JochemK\Desktop\2707_BBLrapportage_v01_1.png')
print(f"Size: {img.size}")
print(f"Mode: {img.mode}")

if img.mode == 'RGBA':
    arr = np.array(img)
    alpha = arr[:,:,3]
    transparent = np.where(alpha < 128)
    if len(transparent[0]) > 0:
        y_min, y_max = transparent[0].min(), transparent[0].max()
        x_min, x_max = transparent[1].min(), transparent[1].max()
        print(f"Transparent area (px): x={x_min}-{x_max}, y={y_min}-{y_max}")
        print(f"Transparent area size: {x_max-x_min}x{y_max-y_min} px")
        # Converteer naar PDF pts (A4 = 595x842pt)
        scale_x = 595.0 / img.size[0]
        scale_y = 842.0 / img.size[1]
        pt_x = x_min * scale_x
        pt_y = y_min * scale_y
        pt_w = (x_max - x_min) * scale_x
        pt_h = (y_max - y_min) * scale_y
        print(f"Transparent area (pt): x={pt_x:.1f}, y={pt_y:.1f}, w={pt_w:.1f}, h={pt_h:.1f}")
    else:
        print("Geen transparante pixels gevonden!")

# === 2. PDF tekst-posities cover (pagina 1) ===
print()
print("=" * 60)
print("2. PDF TEKST-POSITIES COVER (pagina 1)")
print("=" * 60)
pdf_path = r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\huisstijl\2707_BBLrapportage_v01.pdf"
doc = fitz.open(pdf_path)
page = doc[0]  # Cover = pagina 1
ph = page.rect.height

text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
for block in text_dict.get("blocks", []):
    if block.get("type") != 0:
        continue
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            text = span.get("text", "").strip()
            if not text:
                continue
            bbox = span.get("bbox", (0,0,0,0))
            font = span.get("font", "")
            size = span.get("size", 0)
            color_int = span.get("color", 0)
            r = (color_int >> 16) & 0xFF
            g = (color_int >> 8) & 0xFF
            b = color_int & 0xFF
            color_hex = f"#{r:02X}{g:02X}{b:02X}"
            
            # y_top_down = y vanuit bovenkant pagina
            y_td = bbox[1]
            
            print(f"  [{size:.1f}pt] [{font}] [{color_hex}] @ x={bbox[0]:.1f}, y_td={y_td:.1f} (pdf_y={bbox[1]:.1f})")
            print(f"    text: \"{text}\"")

doc.close()
