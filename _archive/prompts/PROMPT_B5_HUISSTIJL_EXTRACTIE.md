# PROMPT B5 — Huisstijl Extractie Tool (Brand Setup Wizard)

## Context

De bm-reports library genereert PDF-rapporten op basis van een brand YAML die de volledige visuele layout beschrijft. De huidige YAML voor 3BM Coöperatie bevat 200+ regels handmatig geschreven coördinaten die niet kloppen — de gegenereerde PDF's wijken sterk af van het referentiedocument.

**Oorzaak:** De bestaande extractie-tools (`tools/pdf_extractor.py`, `tools/pattern_detector.py`, `tools/config_generator.py`) extraheren wél kleuren, fonts, marges en tekststijlen, maar missen:
1. **Drawing paths** — polygonen, clip-paths, bezier curves (PyMuPDF kan dit via `page.get_drawings()` maar de huidige code haalt alleen rects eruit)
2. **Per-pagina layout specificatie** — de volledige `pages:` sectie wordt niet gegenereerd
3. **Element-relaties** — welke tekst in welke rect zit (badges), welke image een logo is vs een projectfoto
4. **Visuele verificatie** — geen manier om gegenereerde output te vergelijken met het origineel

## Doel

Bouw een **complete huisstijl-extractietool** die vanuit een referentie-PDF een volledige, accurate brand YAML genereert. Dit is een eenmalige setup-tool per bureau (niet dagelijks gebruik).

De tool wordt later via de frontend aanroepbaar als "Brand Setup Wizard" maar werkt nu als CLI.

## Architectuur

```
tools/
├── pdf_extractor.py          ← UITBREIDEN: drawing paths toevoegen
├── page_classifier.py         ← ONGEWIJZIGD (werkt goed)
├── pattern_detector.py        ← ONGEWIJZIGD voor content analyse
├── layout_extractor.py        ← NIEUW: per-pagina layout extractie
├── config_generator.py        ← UITBREIDEN: pages-sectie genereren
├── visual_diff.py             ← NIEUW: verificatie tool
└── brand_builder.py           ← UPDATEN: nieuwe tools integreren
```

## Stap 1: Extend pdf_extractor.py — Drawing Path Extractie

PyMuPDF's `page.get_drawings()` retourneert alle vector graphics inclusief paths. De huidige code haalt hier alleen rects uit. Voeg toe:

### 1a. PathElement dataclass

```python
@dataclass
class PathElement:
    """Vector path uit een PDF pagina (polygon, clip-path, bezier)."""
    
    path_type: str  # "polygon" | "bezier" | "clip_path"
    points: list[tuple[float, float]]  # Lijst van (x, y) punten
    fill_hex: str | None = None
    stroke_hex: str | None = None
    stroke_width: float = 0.0
    is_closed: bool = True
    # Bounding box
    bbox_x: float = 0.0
    bbox_y: float = 0.0  
    bbox_width: float = 0.0
    bbox_height: float = 0.0
```

### 1b. RawPageData uitbreiden

```python
@dataclass
class RawPageData:
    page_number: int
    width_pt: float
    height_pt: float
    texts: list[TextElement] = field(default_factory=list)
    rects: list[RectElement] = field(default_factory=list)
    images: list[ImageElement] = field(default_factory=list)
    paths: list[PathElement] = field(default_factory=list)  # ← NIEUW
    page_image_path: str | None = None
```

### 1c. _extract_paths() functie

Gebruik `page.get_drawings()` maar extraheer nu de volledige path data:

```python
def _extract_paths(page) -> list[PathElement]:
    """Extraheer vector paths (polygonen, clip-paths) uit een pagina."""
    paths = []
    for drawing in page.get_drawings():
        items = drawing.get("items", [])
        if not items:
            continue
        
        # Verzamel alle punten uit de path items
        points = []
        for item in items:
            # item[0] = type: "l" (line), "c" (curve), "re" (rect), "qu" (quad)
            item_type = item[0]
            if item_type == "l":  # line to
                points.append((item[1].x, item[1].y))
                points.append((item[2].x, item[2].y))
            elif item_type == "c":  # cubic bezier
                points.append((item[1].x, item[1].y))
                points.append((item[4].x, item[4].y))  # eindpunt
            elif item_type == "re":  # rectangle — skip, al in rects
                continue
            elif item_type == "qu":  # quad
                q = item[1]
                points.extend([(q.x, q.y) for q in [item[1], item[2], item[3], item[4]]])
        
        if len(points) < 3:  # Geen zinvol polygon
            continue
        
        # Deduplicate opeenvolgende identieke punten
        deduped = [points[0]]
        for p in points[1:]:
            if abs(p[0] - deduped[-1][0]) > 0.1 or abs(p[1] - deduped[-1][1]) > 0.1:
                deduped.append(p)
        
        if len(deduped) < 3:
            continue
        
        fill = drawing.get("fill")
        stroke = drawing.get("color")
        
        # Bereken bounding box
        xs = [p[0] for p in deduped]
        ys = [p[1] for p in deduped]
        
        paths.append(PathElement(
            path_type="polygon",
            points=[(round(p[0], 1), round(p[1], 1)) for p in deduped],
            fill_hex=_color_to_hex(fill),
            stroke_hex=_color_to_hex(stroke),
            stroke_width=drawing.get("width", 0),
            is_closed=drawing.get("closePath", False),
            bbox_x=min(xs),
            bbox_y=min(ys),
            bbox_width=max(xs) - min(xs),
            bbox_height=max(ys) - min(ys),
        ))
    
    return paths
```

### 1d. RectElement uitbreiden met rounded rect detectie

```python
@dataclass
class RectElement:
    x: float
    y: float
    width: float
    height: float
    fill_hex: str | None = None
    stroke_hex: str | None = None
    stroke_width: float = 0.0
    element_type: str = "rect"
    corner_radius: float = 0.0  # ← NIEUW: voor rounded rects (badges)
```

Detecteer rounded rects: als een drawing "re" items heeft met aangrenzende "c" (curve) items, is het een rounded rect. Bereken de radius uit de curve control points.

## Stap 2: Nieuw bestand — layout_extractor.py

Dit is de kern: extraheer per pagina-type de volledige layout specificatie.

### 2a. Interface

```python
"""Layout extractor — extraheer per-pagina layout specificaties uit geëxtraheerde data."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from .pdf_extractor import RawPageData, TextElement, RectElement, ImageElement, PathElement
from .page_classifier import ClassifiedPage, PageType

logger = logging.getLogger(__name__)


@dataclass
class TextZone:
    """Dynamisch tekstveld op een pagina."""
    name: str           # "title", "subtitle", "project", etc.
    x_pt: float
    y_pt: float         # Top-down referentie (vanuit bovenkant pagina)
    font: str
    size: float
    color: str
    align: str = "left"  # "left" | "right" | "center"
    max_width_pt: float | None = None
    is_dynamic: bool = True  # True = wordt ingevuld bij generatie


@dataclass  
class StaticElement:
    """Statisch visueel element (rect, path, image)."""
    element_type: str   # "rect" | "polygon" | "image" | "rounded_rect" | "line"
    # Positie
    x_pt: float = 0
    y_pt: float = 0     # Top-down referentie
    width_pt: float = 0
    height_pt: float = 0
    # Visueel
    fill_color: str | None = None
    stroke_color: str | None = None
    stroke_width: float = 0
    corner_radius: float = 0
    # Voor polygonen
    points: list[tuple[float, float]] | None = None
    # Voor images
    image_role: str | None = None  # "logo" | "photo" | "decorative"


@dataclass
class BadgeSpec:
    """Badge/pill element (rounded rect met tekst)."""
    label: str
    bg_color: str
    text_color: str
    x_pt: float
    y_pt: float
    width_pt: float
    height_pt: float
    corner_radius: float
    font_size: float


@dataclass
class PageLayout:
    """Volledige layout specificatie voor één pagina-type."""
    page_type: PageType
    page_number: int
    width_pt: float
    height_pt: float
    static_elements: list[StaticElement] = field(default_factory=list)
    text_zones: list[TextZone] = field(default_factory=list)
    badges: list[BadgeSpec] = field(default_factory=list)
    # Specifiek voor cover
    clip_polygon: list[tuple[float, float]] | None = None
    photo_rect: tuple[float, float, float, float] | None = None
```

### 2b. Extractie functies

```python
def extract_page_layouts(classified_pages: list[ClassifiedPage]) -> dict[PageType, PageLayout]:
    """Extraheer layout voor alle speciale pagina-types.
    
    Returns:
        Dict van PageType → PageLayout.
    """
    layouts = {}
    for cp in classified_pages:
        if cp.page_type == PageType.CONTENT:
            continue  # Content heeft geen speciale layout
        
        layout = _extract_single_page_layout(cp)
        layouts[cp.page_type] = layout
    
    return layouts


def _extract_single_page_layout(cp: ClassifiedPage) -> PageLayout:
    """Extraheer layout voor één pagina."""
    page = cp.page
    ph = page.height_pt
    
    layout = PageLayout(
        page_type=cp.page_type,
        page_number=page.page_number,
        width_pt=page.width_pt,
        height_pt=page.height_pt,
    )
    
    # 1. Converteer alle rects naar StaticElements (y → top-down)
    for r in page.rects:
        layout.static_elements.append(StaticElement(
            element_type=r.element_type,
            x_pt=round(r.x, 1),
            y_pt=round(ph - r.y - r.height, 1),  # PDF bottom-up → top-down
            width_pt=round(r.width, 1),
            height_pt=round(r.height, 1),
            fill_color=r.fill_hex,
            stroke_color=r.stroke_hex,
            stroke_width=r.stroke_width,
            corner_radius=getattr(r, 'corner_radius', 0),
        ))
    
    # 2. Converteer alle paths naar StaticElements
    for p in page.paths:
        # Converteer punten naar top-down
        td_points = [(round(x, 1), round(ph - y, 1)) for x, y in p.points]
        layout.static_elements.append(StaticElement(
            element_type="polygon",
            x_pt=round(p.bbox_x, 1),
            y_pt=round(ph - p.bbox_y - p.bbox_height, 1),
            width_pt=round(p.bbox_width, 1),
            height_pt=round(p.bbox_height, 1),
            fill_color=p.fill_hex,
            stroke_color=p.stroke_hex,
            points=td_points,
        ))
    
    # 3. Converteer images
    for img in page.images:
        role = _classify_image_role(img, page)
        layout.static_elements.append(StaticElement(
            element_type="image",
            x_pt=round(img.x, 1),
            y_pt=round(ph - img.y - img.height, 1),
            width_pt=round(img.width, 1),
            height_pt=round(img.height, 1),
            image_role=role,
        ))
    
    # 4. Classificeer tekstelementen
    for t in page.texts:
        y_td = round(ph - t.y_top, 1)  # top-down
        
        # Heuristiek: is dit dynamische tekst?
        is_dynamic = _is_dynamic_text(t, cp.page_type)
        
        layout.text_zones.append(TextZone(
            name=_guess_text_role(t, cp.page_type),
            x_pt=round(t.x, 1),
            y_pt=y_td,
            font=t.font,
            size=t.size,
            color=t.color_hex,
            is_dynamic=is_dynamic,
        ))
    
    # 5. Detecteer badges (rounded rects met tekst erin)
    layout.badges = _detect_badges(page)
    
    # 6. Detecteer clip-path voor cover foto
    if cp.page_type == PageType.COVER:
        layout.clip_polygon = _find_clip_polygon(page)
        layout.photo_rect = _find_photo_rect(page)
    
    return layout
```

### 2c. Helper functies

```python
def _classify_image_role(img: ImageElement, page: RawPageData) -> str:
    """Classificeer een image als logo, foto of decoratief."""
    page_area = page.width_pt * page.height_pt
    img_area = img.width * img.height
    
    # Klein beeld in hoek → waarschijnlijk logo
    if img_area < page_area * 0.05 and (img.x < 150 or img.y < 150):
        return "logo"
    
    # Groot beeld → projectfoto
    if img_area > page_area * 0.15:
        return "photo"
    
    return "decorative"


def _is_dynamic_text(text: TextElement, page_type: PageType) -> bool:
    """Bepaal of tekst dynamisch is (ingevuld bij generatie) of statisch."""
    static_texts = {
        "ontdek ons", "3bm.co.nl", "meedenken", "praktisch", "betrouwbaar",
        "projecten die inspireren", "coöperatie", "bijlage",
        "betrouwbaar | praktisch | meedenken",
    }
    
    text_lower = text.text.strip().lower()
    
    # Bekende statische teksten
    for st in static_texts:
        if st in text_lower:
            return False
    
    # Op cover: grote tekst is waarschijnlijk de titel (dynamisch)
    if page_type == PageType.COVER and text.size > 20:
        return True
    
    # Op colofon: tekst naast labels is dynamisch
    if page_type == PageType.COLOFON:
        # Labels zelf zijn statisch, waarden zijn dynamisch
        colofon_labels = {"project", "in opdracht van", "adviseur", "datum", 
                         "fase", "status", "normen", "documentgegevens", "documentkenmerk"}
        if text_lower in colofon_labels:
            return False
        return True  # Waarden zijn dynamisch
    
    return False


def _guess_text_role(text: TextElement, page_type: PageType) -> str:
    """Geef een semantische naam aan een tekstelement."""
    if page_type == PageType.COVER:
        if text.size > 25:
            return "title"
        if text.size > 15:
            return "subtitle"
        if "ontdek" in text.text.lower():
            return "ontdek_text"
    
    if page_type == PageType.COLOFON:
        if text.size > 18:
            return "report_type"
        if text.size > 12:
            return "colofon_subtitle"
    
    if page_type == PageType.APPENDIX_DIVIDER:
        if text.size > 30 and "bijlage" in text.text.lower():
            return "appendix_number"
        if text.size > 30:
            return "appendix_title"
    
    return f"text_{round(text.y_top)}"


def _detect_badges(page: RawPageData) -> list[BadgeSpec]:
    """Detecteer badges: rounded rects met gecentreerde tekst."""
    badges = []
    ph = page.height_pt
    
    for r in page.rects:
        if r.corner_radius <= 0:
            continue
        if r.width < 50 or r.height < 15 or r.height > 50:
            continue
        
        # Zoek tekst die in deze rect zit
        for t in page.texts:
            if (t.x >= r.x - 2 and t.x2 <= r.x + r.width + 2 and
                t.y_top >= r.y - 2 and t.y_bottom <= r.y + r.height + 2):
                badges.append(BadgeSpec(
                    label=t.text.strip(),
                    bg_color=r.fill_hex or "#808080",
                    text_color=t.color_hex,
                    x_pt=round(r.x, 1),
                    y_pt=round(ph - r.y - r.height, 1),  # top-down
                    width_pt=round(r.width, 1),
                    height_pt=round(r.height, 1),
                    corner_radius=r.corner_radius,
                    font_size=t.size,
                ))
                break
    
    return badges


def _find_clip_polygon(page: RawPageData) -> list[tuple[float, float]] | None:
    """Zoek het clip-path polygon voor de cover foto."""
    # Het clip polygon is typisch het grootste niet-rechthoekige path
    best = None
    best_area = 0
    
    for p in page.paths:
        if len(p.points) < 5:  # Clip paths hebben typisch 5+ punten
            continue
        area = p.bbox_width * p.bbox_height
        if area > best_area:
            best_area = area
            best = p
    
    if best and best_area > page.width_pt * page.height_pt * 0.1:
        return best.points  # Al in PDF coördinaten (bottom-up) voor ReportLab
    
    return None


def _find_photo_rect(page: RawPageData) -> tuple[float, float, float, float] | None:
    """Zoek de foto-rechthoek op de cover."""
    for img in page.images:
        img_area = img.width * img.height
        if img_area > page.width_pt * page.height_pt * 0.15:
            return (round(img.x, 1), round(img.y, 1), 
                    round(img.width, 1), round(img.height, 1))
    return None
```

## Stap 3: Extend config_generator.py — Volledige YAML generatie

Voeg een functie toe die PageLayout objecten omzet naar de `pages:` YAML sectie:

```python
def generate_pages_yaml(layouts: dict[PageType, PageLayout]) -> dict:
    """Genereer de pages-sectie van de brand YAML.
    
    Args:
        layouts: Dict van PageType → PageLayout uit layout_extractor.
    
    Returns:
        Dict klaar voor YAML serialisatie.
    """
    pages = {}
    
    for page_type, layout in layouts.items():
        key = page_type.value  # "cover", "colofon", etc.
        page_data = {}
        
        # Static elements → gegroepeerd op type
        rects = [e for e in layout.static_elements if e.element_type == "rect"]
        polygons = [e for e in layout.static_elements if e.element_type == "polygon"]
        lines = [e for e in layout.static_elements if e.element_type == "line"]
        images = [e for e in layout.static_elements if e.element_type == "image"]
        
        # Grootste rect = achtergrond vlak
        if rects:
            biggest = max(rects, key=lambda r: r.width_pt * r.height_pt)
            if biggest.fill_color:
                page_data["bg_rect"] = {
                    "x": biggest.x_pt,
                    "y_ref": biggest.y_pt,
                    "width": biggest.width_pt,
                    "height": biggest.height_pt,
                    "color": biggest.fill_color,
                }
        
        # Clip polygon (cover)
        if layout.clip_polygon:
            page_data["clip_polygon"] = [list(p) for p in layout.clip_polygon]
        
        # Photo rect (cover)
        if layout.photo_rect:
            page_data["photo_rect"] = list(layout.photo_rect)
        
        # Badges
        if layout.badges:
            page_data["badges"] = [
                {
                    "label": b.label,
                    "bg_color": b.bg_color,
                    "text_color": b.text_color,
                    "x_ref": b.x_pt,
                    "y_ref": b.y_pt,
                    "w_ref": b.width_pt,
                    "h_ref": b.height_pt,
                }
                for b in layout.badges
            ]
            # Badge gemeenschappelijke properties
            if layout.badges:
                page_data["badge_radius_ref"] = layout.badges[0].corner_radius
                page_data["badge_font_size_ref"] = layout.badges[0].font_size
        
        # Text zones → gescheiden in statisch en dynamisch
        dynamic_zones = [z for z in layout.text_zones if z.is_dynamic]
        static_zones = [z for z in layout.text_zones if not z.is_dynamic]
        
        # Dynamische zones: mapping naam → positie
        for zone in dynamic_zones:
            key_name = zone.name
            page_data[f"{key_name}_x_ref"] = zone.x_pt
            page_data[f"{key_name}_y_ref"] = zone.y_pt
            page_data[f"{key_name}_size_ref"] = zone.size
            # Font en kleur als $-referenties waar mogelijk
        
        # Logo's
        logos = [e for e in images if e.image_role == "logo"]
        if logos:
            logo = logos[0]
            page_data["logo_x_ref"] = logo.x_pt
            page_data["logo_y_ref"] = logo.y_pt
            page_data["logo_w_ref"] = logo.width_pt
        
        # Polygonen (backcover geometrie, etc.)
        for i, poly in enumerate(polygons):
            if poly.points:
                suffix = "" if i == 0 else f"_{i}"
                name = _guess_polygon_name(poly, layout)
                page_data[name] = [list(p) for p in poly.points]
        
        pages[key] = page_data
    
    return pages
```

Integreer dit in `generate_brand_yaml()` zodat de volledige YAML gegenereerd wordt inclusief pages-sectie.

## Stap 4: Nieuw bestand — visual_diff.py

Verificatie tool die gegenereerde PDF vergelijkt met referentie.

```python
"""Visual diff — vergelijk gegenereerde PDF met referentie."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import fitz
    from PIL import Image, ImageChops, ImageDraw
    import numpy as np
except ImportError:
    fitz = None


@dataclass
class PageDiff:
    """Verschilanalyse voor één pagina."""
    page_number: int
    similarity_pct: float  # 0-100
    diff_image_path: str | None = None  # Pad naar verschil-overlay
    notes: list[str] = None  # Waarnemingen


def compare_pdfs(
    generated: Path,
    reference: Path,
    output_dir: Path | None = None,
    dpi: int = 150,
    pages: list[int] | None = None,
) -> list[PageDiff]:
    """Vergelijk twee PDF's pagina-voor-pagina.
    
    Args:
        generated: Pad naar gegenereerde PDF.
        reference: Pad naar referentie PDF.
        output_dir: Map voor verschil-afbeeldingen.
        dpi: Render DPI.
        pages: Specifieke pagina's om te vergelijken (1-based), None = alle.
    
    Returns:
        Lijst van PageDiff per vergeleken pagina.
    """
    if fitz is None:
        raise ImportError("PyMuPDF en Pillow nodig: pip install PyMuPDF Pillow numpy")
    
    gen_doc = fitz.open(str(generated))
    ref_doc = fitz.open(str(reference))
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    page_indices = range(min(len(gen_doc), len(ref_doc)))
    if pages:
        page_indices = [p - 1 for p in pages if 0 < p <= min(len(gen_doc), len(ref_doc))]
    
    for idx in page_indices:
        gen_pix = gen_doc[idx].get_pixmap(dpi=dpi)
        ref_pix = ref_doc[idx].get_pixmap(dpi=dpi)
        
        gen_img = Image.frombytes("RGB", (gen_pix.width, gen_pix.height), gen_pix.samples)
        ref_img = Image.frombytes("RGB", (ref_pix.width, ref_pix.height), ref_pix.samples)
        
        # Resize naar zelfde formaat als ze iets afwijken
        if gen_img.size != ref_img.size:
            ref_img = ref_img.resize(gen_img.size, Image.LANCZOS)
        
        # Bereken verschil
        gen_arr = np.array(gen_img, dtype=float)
        ref_arr = np.array(ref_img, dtype=float)
        diff_arr = np.abs(gen_arr - ref_arr)
        
        # Similarity: percentage pixels dat <threshold verschil heeft
        threshold = 30  # tolerantie per kanaal
        similar_pixels = np.all(diff_arr < threshold, axis=2).sum()
        total_pixels = diff_arr.shape[0] * diff_arr.shape[1]
        similarity = (similar_pixels / total_pixels) * 100
        
        # Diff image
        diff_path = None
        if output_dir:
            # Maak een overlay: rood waar verschil groot is
            diff_mask = np.any(diff_arr > threshold, axis=2)
            overlay = gen_arr.copy().astype(np.uint8)
            overlay[diff_mask] = [255, 0, 0]  # Rood voor afwijkingen
            
            diff_img = Image.fromarray(overlay)
            diff_path = str(output_dir / f"diff_page_{idx + 1:03d}.png")
            diff_img.save(diff_path)
        
        results.append(PageDiff(
            page_number=idx + 1,
            similarity_pct=round(similarity, 1),
            diff_image_path=diff_path,
            notes=[],
        ))
    
    gen_doc.close()
    ref_doc.close()
    
    return results


def print_diff_report(diffs: list[PageDiff]) -> None:
    """Print een leesbaar diff rapport naar stdout."""
    print("\n=== Visual Diff Report ===\n")
    for d in diffs:
        status = "✅" if d.similarity_pct > 95 else "⚠️" if d.similarity_pct > 80 else "❌"
        print(f"  Pagina {d.page_number}: {d.similarity_pct:.1f}% match {status}")
        if d.diff_image_path:
            print(f"    Diff: {d.diff_image_path}")
    
    avg = sum(d.similarity_pct for d in diffs) / len(diffs) if diffs else 0
    print(f"\n  Gemiddeld: {avg:.1f}%")
    print(f"  Pagina's: {len(diffs)}")
```

## Stap 5: Update brand_builder.py

Integreer de nieuwe tools in de build pipeline:

```python
def build(self, referentie_rapport, ...):
    # ... bestaande stappen 1-6 ...
    
    # NIEUW: Stap 7a — Extraheer per-pagina layouts
    from .layout_extractor import extract_page_layouts
    layouts = extract_page_layouts(classified)
    
    # NIEUW: Stap 7b — Genereer volledige brand.yaml inclusief pages
    yaml_str = generate_brand_yaml(
        analysis, self.brand_name, self.brand_slug,
        page_layouts=layouts,  # ← nieuw argument
    )
    
    # NIEUW: Stap 8 — Visuele verificatie (optioneel)
    if verify:
        from .visual_diff import compare_pdfs, print_diff_report
        # Genereer test PDF met de nieuwe config
        # Vergelijk met origineel
        diffs = compare_pdfs(test_pdf, referentie_rapport, analysis_dir / "diffs")
        print_diff_report(diffs)
```

## Stap 6: CLI commando's

Voeg toe aan `cli.py`:

```python
# Extractie commando
@app.command()
def extract_layout(
    pdf: Path = typer.Argument(..., help="Pad naar referentie PDF"),
    output: Path = typer.Option("./extracted", help="Output directory"),
):
    """Extraheer volledige layout uit een referentie-PDF."""
    from bm_reports.tools.pdf_extractor import extract_pdf
    from bm_reports.tools.page_classifier import classify_pages
    from bm_reports.tools.layout_extractor import extract_page_layouts
    
    pages = extract_pdf(pdf, output / "pages", dpi=150)
    classified = classify_pages(pages)
    layouts = extract_page_layouts(classified)
    
    # Print layout samenvatting
    for page_type, layout in layouts.items():
        print(f"\n{page_type.value.upper()} (pagina {layout.page_number}):")
        print(f"  Statische elementen: {len(layout.static_elements)}")
        print(f"  Tekst zones: {len(layout.text_zones)}")
        print(f"  Badges: {len(layout.badges)}")
        if layout.clip_polygon:
            print(f"  Clip polygon: {len(layout.clip_polygon)} punten")

# Diff commando
@app.command()
def visual_diff(
    generated: Path = typer.Argument(...),
    reference: Path = typer.Argument(...),
    output: Path = typer.Option("./diffs"),
):
    """Vergelijk gegenereerde PDF met referentie."""
    from bm_reports.tools.visual_diff import compare_pdfs, print_diff_report
    diffs = compare_pdfs(generated, reference, output)
    print_diff_report(diffs)
```

## Coördinatensysteem — KRITIEK

**Eén duidelijk systeem door de hele pipeline:**

- `pdf_extractor.py` levert coördinaten in **PDF-native** (y=0 onderaan, y omhoog)
- `layout_extractor.py` converteert naar **top-down referentie** (y=0 bovenaan) voor de YAML
- `special_pages.py` (renderer) converteert terug naar **PDF-native** bij het tekenen

**In de YAML staan alle y-coördinaten in top-down referentie.** Dit is intuïtief (y=0 = bovenkant pagina) en consistent met hoe mensen over layouts denken.

De renderer doet: `y_pdf = page_height - y_yaml`

## Verificatie checklist

- [ ] `extract_pdf()` retourneert nu ook `paths` met polygonen
- [ ] `RectElement` heeft `corner_radius` voor rounded rects  
- [ ] `layout_extractor.py` genereert PageLayout voor cover, colofon, backcover, appendix_divider
- [ ] `config_generator.py` genereert volledige YAML inclusief `pages:` sectie
- [ ] `visual_diff.py` vergelijkt twee PDF's en geeft similarity score
- [ ] CLI commando's `extract-layout` en `visual-diff` werken
- [ ] Gegenereerde YAML voor 3BM Coöperatie is completer dan de huidige handgeschreven versie
- [ ] Test: extraheer layout uit `huisstijl/2707_BBLrapportage_v01.pdf`, genereer PDF, diff > 90%

## Dependencies

Voeg toe aan `pyproject.toml` onder `[project.optional-dependencies]`:
```toml
brand-tools = ["PyMuPDF>=1.23", "Pillow>=10.0", "numpy>=1.24"]
```

## Bestanden die aangemaakt/gewijzigd worden

| Bestand | Actie |
|---------|-------|
| `tools/pdf_extractor.py` | WIJZIG: PathElement + _extract_paths() + corner_radius |
| `tools/layout_extractor.py` | NIEUW: per-pagina layout extractie |
| `tools/config_generator.py` | WIJZIG: pages-sectie generatie |
| `tools/visual_diff.py` | NIEUW: PDF vergelijking |
| `tools/brand_builder.py` | WIJZIG: nieuwe tools integreren |
| `cli.py` | WIJZIG: extract-layout en visual-diff commando's |
| `pyproject.toml` | WIJZIG: brand-tools dependencies |
