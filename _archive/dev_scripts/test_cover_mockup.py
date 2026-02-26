"""Mockup: genereer cover PDF met 3-lagen aanpak.

Laag 1: Projectfoto (achtergrond)
Laag 2: Stationery PNG overlay (met alpha-gat)
Laag 3: Dynamische tekst

Omdat de PNG nog geen alpha heeft, simuleren we met de originele 
PDF pagina als stationery en plaatsen we tekst erover.
"""
import sys
sys.path.insert(0, r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src")

import yaml
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, Color
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

OUT_DIR = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\test_output")
YAML_PATH = OUT_DIR / "cover_template.yaml"
OUTPUT_PDF = OUT_DIR / "cover_mockup_v2.pdf"
STATIONERY_PNG = Path(r"C:\Users\JochemK\Desktop\2707_BBLrapportage_v01_1.png")

# Laad template
with open(YAML_PATH) as f:
    template = yaml.safe_load(f)

# Font registratie
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

font_dir = Path(r"X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator\src\bm_reports\assets\fonts")
font_map = {
    "GothamBold": "Gotham-Bold.ttf",
    "GothamBook": "Gotham-Book.ttf", 
    "GothamMedium": "Gotham-Medium.ttf",
}
for name, filename in font_map.items():
    font_path = font_dir / filename
    if font_path.exists():
        try:
            pdfmetrics.registerFont(TTFont(name, str(font_path)))
            print(f"  Font geladen: {name}")
        except Exception as e:
            print(f"  Font FOUT {name}: {e}")
    else:
        print(f"  Font niet gevonden: {font_path}")

# === PDF genereren ===
print(f"\nGenerating mockup: {OUTPUT_PDF}")

w, h = A4  # 595.27 x 841.89
c = canvas.Canvas(str(OUTPUT_PDF), pagesize=A4)

# --- Laag 1: Placeholder projectfoto ---
photo = template["photo"]
# Teken een placeholder (lichtgrijs vlak met tekst)
c.setFillColor(HexColor("#CCCCCC"))
c.rect(photo["x"], photo["y"], photo["width"], photo["height"], fill=1, stroke=0)
c.setFillColor(HexColor("#999999"))
c.setFont("Helvetica", 14)
c.drawCentredString(
    photo["x"] + photo["width"] / 2,
    photo["y"] + photo["height"] / 2,
    "[ PROJECTFOTO ]"
)

# --- Laag 2: Stationery PNG overlay ---
# De PNG is RGB (geen alpha), dus we plaatsen hem gewoon
# Bij een RGBA PNG zou ReportLab automatisch de alpha respecteren
if STATIONERY_PNG.exists():
    try:
        img = ImageReader(str(STATIONERY_PNG))
        c.drawImage(
            img, 
            0, 0, 
            width=w, height=h,
            mask='auto',  # Respecteert alpha channel als aanwezig
            preserveAspectRatio=False,
        )
        print("  Stationery PNG geplaatst (mask=auto)")
    except Exception as e:
        print(f"  Stationery PNG fout: {e}")
        # Fallback: teken placeholder overlay
        c.setFillColor(Color(0.251, 0.067, 0.275, alpha=0.8))  # paars semi-transparant
        c.rect(0, 0, w, 218, fill=1, stroke=0)
else:
    print(f"  WAARSCHUWING: {STATIONERY_PNG} niet gevonden")
    # Simuleer de overlay met gekleurde vlakken
    c.setFillColor(HexColor("#401146"))
    c.rect(0, 0, w, 218, fill=1, stroke=0)

# --- Laag 3: Dynamische tekst ---
for field_name, field in template["text_fields"].items():
    font = field["font"]
    size = field["size"]
    color = HexColor(field["color"])
    x = field["x"]
    y = field["y"]
    text = field["example"]
    
    try:
        c.setFont(font, size)
    except:
        c.setFont("Helvetica-Bold" if "Bold" in font else "Helvetica", size)
    
    c.setFillColor(color)
    c.drawString(x, y, text)
    print(f"  Tekst geplaatst: \"{text}\" @ ({x:.1f}, {y:.1f})")

# --- Annotaties: teken rode kaders om dynamische zones ---
c.setStrokeColor(HexColor("#FF0000"))
c.setLineWidth(1)
c.setDash(3, 3)

# Foto zone
c.rect(photo["x"], photo["y"], photo["width"], photo["height"], fill=0, stroke=1)
c.setFont("Helvetica", 8)
c.setFillColor(HexColor("#FF0000"))
c.drawString(photo["x"] + 5, photo["y"] + photo["height"] - 12, "FOTO ZONE")

# Tekst zones
for field_name, field in template["text_fields"].items():
    x = field["x"]
    y = field["y"] - 5
    w_box = field.get("max_width", 300)
    h_box = field["size"] + 10
    c.rect(x, y, w_box, h_box, fill=0, stroke=1)
    c.setFont("Helvetica", 6)
    c.drawString(x + 2, y + h_box + 2, f"YAML: {field_name}")

c.save()
print(f"\nDONE: {OUTPUT_PDF}")
