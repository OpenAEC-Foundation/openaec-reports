# PROMPT: Stationery-architectuur + Huisstijl fixes

## Lees eerst

Lees voor je begint deze bestanden:
- `SPEC_PAGINA_ARCHITECTUUR.md` — 3-lagenmodel per paginatype, volledige brand config spec
- `huisstijl/HUISSTIJL_SPEC.md` — Exacte fonts, kleuren, posities
- `PLAN_STATIONERY_ARCHITECTUUR.md` — Stationery concept

## Doel

Twee dingen tegelijk:
1. **Fix alle font/kleur bugs** — direct visueel resultaat
2. **Bouw stationery-systeem** — achtergrond-PDF's als eerste laag, programmatisch als fallback

Na afloop: genereer een test-PDF en vergelijk visueel met `huisstijl/pages/page_01.png` t/m `page_36.png`.

---

## Deel A: Font/kleur fixes

### A1. `src/bm_reports/core/styles.py` — Colors dataclass

Wijzig de defaults:

```python
@dataclass(frozen=True)
class Colors:
    primary: str = "#401246"          # Was: "#40124A"
    secondary: str = "#38BDAB"        # Was: "#38BDA0"
    accent: str = "#2ECC71"           # Ongewijzigd
    warning: str = "#E74C3C"          # Ongewijzigd
    text: str = "#45243D"             # Ongewijzigd
    text_light: str = "#7F8C8D"       # Ongewijzigd
    text_accent: str = "#56B49B"      # NIEUW — H2/H3 headings, TOC level 1
    background: str = "#FFFFFF"       # Ongewijzigd
    background_alt: str = "#F8F9FA"   # Ongewijzigd
    rule: str = "#BDC3C7"             # Ongewijzigd
    table_header_bg: str = "#45233C"  # NIEUW — tabel header achtergrond
    table_header_text: str = "#FFFFFF" # NIEUW — tabel header tekst
    table_footer_bg: str = "#55B49B"  # NIEUW — tabel footer/totaal rij
    separator: str = "#E0D0E8"        # NIEUW — scheidingslijnen
```

### A2. `src/bm_reports/core/styles.py` — FontConfig

Wijzig de size defaults:

```python
@dataclass(frozen=True)
class FontConfig:
    heading: str = "GothamBold"
    body: str = "GothamBook"
    medium: str = "GothamMedium"
    italic: str = "GothamBookItalic"
    mono: str = "Courier"
    body_size: float = 9.5            # Was: 9.0
    heading1_size: float = 18.0       # Was: 16.0
    heading2_size: float = 13.0       # Ongewijzigd
    heading3_size: float = 11.0       # Ongewijzigd
    caption_size: float = 8.0         # Ongewijzigd
    footer_size: float = 7.5          # Ongewijzigd
```

### A3. `src/bm_reports/core/styles.py` — create_stylesheet()

Wijzig de Heading styles:

```python
# Heading1: GothamBook (NIET Bold!), kleur = text (niet primary)
styles.add(ParagraphStyle(
    name="Heading1",
    parent=styles["Normal"],
    fontName=BM_FONTS.body,           # Was: BM_FONTS.heading
    fontSize=BM_FONTS.heading1_size,
    leading=BM_FONTS.heading1_size * 1.3,
    textColor=HexColor(BM_COLORS.text),  # Was: BM_COLORS.primary
    spaceBefore=12,
    spaceAfter=6,
))

# Heading2: kleur = text_accent (turquoise)
styles.add(ParagraphStyle(
    name="Heading2",
    parent=styles["Normal"],
    fontName=BM_FONTS.body,           # Was: BM_FONTS.heading
    fontSize=BM_FONTS.heading2_size,
    leading=BM_FONTS.heading2_size * 1.3,
    textColor=HexColor(BM_COLORS.text_accent),  # Was: BM_COLORS.primary
    spaceBefore=10,
    spaceAfter=4,
))

# Heading3: kleur = text_accent
styles.add(ParagraphStyle(
    name="Heading3",
    parent=styles["Normal"],
    fontName=BM_FONTS.body,           # Was: BM_FONTS.heading
    fontSize=BM_FONTS.heading3_size,
    leading=BM_FONTS.heading3_size * 1.3,
    textColor=HexColor(BM_COLORS.text_accent),  # Was: BM_COLORS.secondary
    spaceBefore=8,
    spaceAfter=3,
))
```

Rebuild `BM_STYLES` en `BM_COLORS` onderaan het bestand na de fixes.

### A4. `src/bm_reports/assets/brands/3bm_cooperatie.yaml`

Zorg dat de fonts sectie naar Gotham verwijst (niet Helvetica):

```yaml
fonts:
  heading: "GothamBold"
  body: "GothamBook"
  medium: "GothamMedium"
  italic: "GothamBookItalic"
```

Voeg toe onder `colors:`:
```yaml
colors:
  primary: "#401246"
  secondary: "#38BDAB"
  text: "#45243D"
  text_accent: "#56B49B"
  table_header_bg: "#45233C"
  table_header_text: "#FFFFFF"
  table_footer_bg: "#55B49B"
  separator: "#E0D0E8"
```

### A5. `src/bm_reports/core/special_pages.py`

Zoek ALLE hardcoded kleurwaarden bovenaan het bestand en vervang ze:

```python
# Vervang:
_COLOR_PRIMARY = HexColor("#40124A")    # → "#401246"
_COLOR_SECONDARY = HexColor("#38BDA0")  # → "#38BDAB"
```

Beter: verwijder de module-level constanten en lees kleuren uit de `brand` parameter die al aan elke `draw_*` functie wordt meegegeven:

```python
def _brand_primary(brand) -> HexColor:
    return HexColor(brand.colors.get("primary", "#401246"))

def _brand_secondary(brand) -> HexColor:
    return HexColor(brand.colors.get("secondary", "#38BDAB"))

def _brand_text(brand) -> HexColor:
    return HexColor(brand.colors.get("text", "#45243D"))
```

Vervang alle `_COLOR_PRIMARY` / `_COLOR_SECONDARY` door `_brand_primary(brand)` / `_brand_secondary(brand)` calls in draw_cover_page, draw_colofon_page, draw_backcover_page, draw_appendix_divider_page, en _draw_badges.

### A6. Module styling — `components/table_block.py`

Als `table_block.py` hardcoded kleuren gebruikt voor tabel headers/footers, vervang die met `BM_COLORS.table_header_bg`, `BM_COLORS.table_header_text`, `BM_COLORS.table_footer_bg`.

Check ook `calculation.py` en `check_block.py` voor hardcoded kleuren.

---

## Deel B: Stationery systeem

### B1. Dependency toevoegen — `pyproject.toml`

Voeg `pdfrw>=0.4` toe aan de hoofd-dependencies:

```toml
dependencies = [
    "reportlab>=4.0",
    "PyYAML>=6.0",
    "Pillow>=10.0",
    "svglib>=0.9",
    "pdfrw>=0.4",       # NIEUW — PDF-als-achtergrond in ReportLab
]
```

Installeer: `pip install pdfrw`

### B2. Stationery extractor — `src/bm_reports/tools/stationery_extractor.py`

Nieuw bestand. Extraheert achtergrond-pagina's uit een referentie-PDF met PyMuPDF.

```python
"""Stationery extractor — extraheer achtergrondtemplates uit referentie-PDF's."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import fitz
except ImportError:
    fitz = None


class StationeryExtractor:
    """Extraheer stationery-pagina's uit een referentie-PDF.
    
    Drie extractiemodi:
    - full_page: hele pagina als PDF (vectoren behouden)
    - stripped: pagina met tekst in opgegeven zones verwijderd
    - graphics_only: pagina met ALLE tekst verwijderd
    """
    
    def __init__(self, source_pdf: Path):
        if fitz is None:
            raise ImportError("PyMuPDF vereist: pip install pymupdf")
        self._source = Path(source_pdf)
        if not self._source.exists():
            raise FileNotFoundError(f"PDF niet gevonden: {self._source}")
    
    def extract_full_page(self, page_num: int, output_path: Path) -> Path:
        """Extraheer hele pagina als nieuwe single-page PDF.
        
        page_num: 0-based pagina index.
        Gebruik voor: backcover (100% statisch).
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        doc = fitz.open(str(self._source))
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        new_doc.save(str(output_path))
        new_doc.close()
        doc.close()
        
        logger.info(f"Stationery geëxtraheerd: pagina {page_num + 1} → {output_path}")
        return output_path
    
    def extract_stripped_page(
        self, page_num: int, output_path: Path,
        strip_zones: list[tuple[float, float, float, float]],
    ) -> Path:
        """Extraheer pagina met tekst in opgegeven zones verwijderd (wit).
        
        page_num: 0-based pagina index.
        strip_zones: lijst van (x0, y0, x1, y1) in PyMuPDF coords (top-down).
        Tekst in deze zones wordt wit gemaakt, grafische elementen blijven.
        
        Gebruik voor: cover (strip titel), colofon (strip labels), 
        appendix divider (strip nummer/titel).
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        doc = fitz.open(str(self._source))
        # Werk op kopie
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        doc.close()
        
        page = new_doc[0]
        for (x0, y0, x1, y1) in strip_zones:
            rect = fitz.Rect(x0, y0, x1, y1)
            # Vind tekst in zone en redact
            text_dict = page.get_text("dict", clip=rect)
            for block in text_dict.get("blocks", []):
                if block.get("type") == 0:  # tekst blok
                    block_rect = fitz.Rect(block["bbox"])
                    page.add_redact_annot(block_rect, fill=(1, 1, 1))
        page.apply_redactions()
        
        new_doc.save(str(output_path))
        new_doc.close()
        
        logger.info(f"Stripped stationery: pagina {page_num + 1} → {output_path}")
        return output_path
    
    def extract_graphics_only(self, page_num: int, output_path: Path) -> Path:
        """Extraheer pagina met ALLE tekst verwijderd.
        
        Let op: logo-tekst wordt ook verwijderd!
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        doc = fitz.open(str(self._source))
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        doc.close()
        
        page = new_doc[0]
        # Verwijder alle tekst
        text_dict = page.get_text("dict")
        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:
                block_rect = fitz.Rect(block["bbox"])
                page.add_redact_annot(block_rect, fill=(1, 1, 1))
        page.apply_redactions()
        
        new_doc.save(str(output_path))
        new_doc.close()
        
        logger.info(f"Graphics-only stationery: pagina {page_num + 1} → {output_path}")
        return output_path
    
    def extract_as_png(self, page_num: int, output_path: Path, dpi: int = 300) -> Path:
        """Fallback: extraheer als hoge-resolutie PNG."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        doc = fitz.open(str(self._source))
        page = doc[page_num]
        pix = page.get_pixmap(dpi=dpi)
        pix.save(str(output_path))
        doc.close()
        
        return output_path
```

### B3. Stationery renderer — `src/bm_reports/core/stationery.py`

Nieuw bestand. Tekent stationery PDF's als achtergrond op het ReportLab canvas.

```python
"""Stationery renderer — tekent PDF/PNG achtergronden op ReportLab canvas."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class StationeryRenderer:
    """Tekent stationery (achtergrond PDF/PNG) als laag 1 op een pagina.
    
    Gebruikt pdfrw om PDF pagina's als vector XObject te embedden.
    Fallback naar Pillow voor PNG achtergronden.
    """
    
    def __init__(self, brand_dir: Path | None = None):
        self._brand_dir = brand_dir
        self._cache: dict[str, Any] = {}
    
    def draw(
        self, canvas, source_path: str | Path | None, 
        page_w: float, page_h: float,
    ) -> bool:
        """Teken stationery achtergrond op het canvas.
        
        source_path: pad naar PDF of PNG (relatief t.o.v. brand_dir, of absoluut).
        Returns True als getekend, False als niet beschikbaar.
        """
        if not source_path:
            return False
        
        path = self._resolve_path(source_path)
        if path is None or not path.exists():
            logger.warning(f"Stationery niet gevonden: {source_path}")
            return False
        
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return self._draw_pdf(canvas, path, page_w, page_h)
        elif suffix in (".png", ".jpg", ".jpeg"):
            return self._draw_image(canvas, path, page_w, page_h)
        else:
            logger.warning(f"Onbekend stationery formaat: {suffix}")
            return False
    
    def _resolve_path(self, source: str | Path) -> Path | None:
        """Resolve relatief pad t.o.v. brand_dir."""
        path = Path(source)
        if path.is_absolute() and path.exists():
            return path
        if self._brand_dir:
            resolved = self._brand_dir / path
            if resolved.exists():
                return resolved
        return None
    
    def _draw_pdf(self, canvas, pdf_path: Path, page_w: float, page_h: float) -> bool:
        """Render PDF als achtergrond via pdfrw → ReportLab XObject."""
        try:
            from pdfrw import PdfReader
            from pdfrw.buildxobj import pagexobj
            from pdfrw.toreportlab import makerl
        except ImportError:
            logger.error("pdfrw niet geïnstalleerd: pip install pdfrw")
            return False
        
        cache_key = str(pdf_path)
        if cache_key not in self._cache:
            reader = PdfReader(str(pdf_path))
            if not reader.pages:
                return False
            self._cache[cache_key] = pagexobj(reader.pages[0])
        
        xobj = self._cache[cache_key]
        
        canvas.saveState()
        # Schaal stationery naar pagina-afmetingen
        xobj_w = float(xobj.BBox[2]) - float(xobj.BBox[0])
        xobj_h = float(xobj.BBox[3]) - float(xobj.BBox[1])
        if xobj_w > 0 and xobj_h > 0:
            sx = page_w / xobj_w
            sy = page_h / xobj_h
            canvas.transform(sx, 0, 0, sy, 0, 0)
        
        rl_obj = makerl(canvas, xobj)
        canvas.doForm(rl_obj)
        canvas.restoreState()
        
        return True
    
    def _draw_image(self, canvas, img_path: Path, page_w: float, page_h: float) -> bool:
        """Render PNG/JPG als full-page achtergrond."""
        try:
            canvas.drawImage(
                str(img_path), 0, 0, page_w, page_h,
                preserveAspectRatio=False, mask='auto',
            )
            return True
        except Exception as e:
            logger.error(f"Stationery image fout: {e}")
            return False
```

### B4. Brand config uitbreiden — `src/bm_reports/core/brand.py`

Voeg stationery configuratie toe aan BrandConfig:

```python
@dataclass
class StationeryPageConfig:
    """Stationery configuratie per paginatype."""
    source: str = ""                        # Pad naar PDF/PNG (relatief aan brand_dir)
    header_footer: str | None = None        # Kop/voettekst variant ("content", "colofon", None)
    text_zones: list[dict] = field(default_factory=list)
    content_frame: dict | None = None       # Voor content pagina's: {x_pt, y_pt, width_pt, height_pt}

@dataclass
class BrandConfig:
    # Bestaande velden — NIET WIJZIGEN (backward compatible)
    name: str = "Default"
    slug: str = "default"
    colors: dict[str, str] = field(default_factory=dict)
    fonts: dict[str, str] = field(default_factory=dict)
    header: ZoneConfig = field(default_factory=ZoneConfig)
    footer: ZoneConfig = field(default_factory=ZoneConfig)
    logos: dict[str, str] = field(default_factory=dict)
    contact: dict[str, str] = field(default_factory=dict)
    styles: dict[str, dict] = field(default_factory=dict)
    pages: dict[str, dict] = field(default_factory=dict)
    
    # NIEUW
    stationery: dict[str, StationeryPageConfig] = field(default_factory=dict)
    modules: dict[str, dict] = field(default_factory=dict)
    brand_dir: Path | None = None
```

Breid `BrandLoader.load()` uit om `stationery:` sectie te parsen:

```python
def load(self, name: str) -> BrandConfig:
    # ... bestaande code ...
    
    # Stationery parsen
    stationery = {}
    for page_type, spec in data.get("stationery", {}).items():
        stationery[page_type] = StationeryPageConfig(
            source=spec.get("source", ""),
            header_footer=spec.get("header_footer"),
            text_zones=spec.get("text_zones", []),
            content_frame=spec.get("content_frame"),
        )
    
    return BrandConfig(
        # ... bestaande velden ...
        stationery=stationery,
        modules=data.get("modules", {}),
        brand_dir=path.parent,  # Directory van het YAML bestand
    )
```

**BrandLoader directory support**: De BrandLoader moet zowel `brands/3bm_cooperatie.yaml` (single file, legacy) als `brands/3bm-cooperatie/brand.yaml` (directory, v2) kunnen laden. Pas `_resolve_path` aan:

```python
def _resolve_path(self, name: str) -> Path:
    if name.endswith(".yaml"):
        return self.brands_dir / name
    # Probeer eerst directory
    dir_path = self.brands_dir / name / "brand.yaml"
    if dir_path.exists():
        return dir_path
    # Fallback naar single file
    return self.brands_dir / f"{name}.yaml"
```

### B5. Stationery integratie in page rendering — `src/bm_reports/core/page_templates.py`

Wijzig `create_page_templates()` zodat elke onPage callback stationery-first werkt:

```python
from bm_reports.core.stationery import StationeryRenderer

def create_page_templates(config, brand=None, colofon_data=None, cover_image=None):
    if brand is None:
        brand = BrandLoader().load_default()
    
    renderer = BrandRenderer(brand, assets_dir=ASSETS_DIR)
    stationery = StationeryRenderer(brand_dir=brand.brand_dir)
    
    # ... frame definities ongewijzigd ...
    
    # Cover
    cover_template = PageTemplate(
        id="cover",
        frames=[cover_frame],
        onPage=lambda c, d: _on_page_cover(c, d, config, brand, stationery, cover_image),
    )
    
    # Content — stationery-aware
    content_template = PageTemplate(
        id="content",
        frames=[content_frame],
        onPage=lambda c, d: _on_page_content(c, d, config, brand, renderer, stationery),
    )
    
    # Backcover — stationery-first (dit is de grote winst!)
    backcover_template = PageTemplate(
        id="backcover",
        frames=[backcover_frame],
        onPage=lambda c, d: _on_page_backcover(c, d, config, brand, stationery),
    )
    
    # ... colofon, appendix idem ...
    
    return [cover_template, colofon_template, content_template, appendix_template, backcover_template]


def _on_page_backcover(canvas, doc, config, brand, stationery):
    """Backcover: stationery-first, fallback naar programmatisch."""
    pw = config.effective_width_pt
    ph = config.effective_height_pt
    
    spec = brand.stationery.get("backcover")
    if spec and stationery.draw(canvas, spec.source, pw, ph):
        # Stationery getekend — teken eventuele text zones (contactgegevens)
        _draw_text_zones(canvas, spec.text_zones, config, brand, pw, ph)
    else:
        # Fallback: bestaande programmatische rendering
        draw_backcover_page(canvas, doc, config, brand)


def _on_page_cover(canvas, doc, config, brand, stationery, cover_image):
    """Cover: stationery-first, fallback naar programmatisch."""
    pw = config.effective_width_pt
    ph = config.effective_height_pt
    
    spec = brand.stationery.get("cover")
    if spec and stationery.draw(canvas, spec.source, pw, ph):
        _draw_text_zones(canvas, spec.text_zones, config, brand, pw, ph)
    else:
        draw_cover_page(canvas, doc, config, brand, cover_image)


def _on_page_content(canvas, doc, config, brand, renderer, stationery):
    """Content: stationery achtergrond (optioneel) + header/footer."""
    pw = config.effective_width_pt
    ph = config.effective_height_pt
    
    spec = brand.stationery.get("content")
    if spec and spec.source:
        stationery.draw(canvas, spec.source, pw, ph)
    
    # Header/footer altijd tekenen (via BrandRenderer)
    renderer.draw_page(canvas, doc, config)


def _draw_text_zones(canvas, text_zones, config, brand, pw, ph):
    """Teken dynamische tekst in text zones op de stationery.
    
    Text zones zijn gedefinieerd met y_pt in top-down coördinaten.
    ReportLab canvas gebruikt bottom-up. Converteer: rl_y = ph - y_pt
    """
    from bm_reports.core.fonts import get_font_name
    
    for zone in text_zones:
        role = zone.get("role", "")
        zone_type = zone.get("type", "text")
        
        if zone_type != "text":
            continue  # clipped_image en key_value_table later implementeren
        
        # Resolve font
        font_ref = zone.get("font", "$fonts.body")
        if font_ref.startswith("$fonts."):
            font_key = font_ref.replace("$fonts.", "")
            font_name = brand.fonts.get(font_key, "GothamBook")
        else:
            font_name = font_ref
        font_name = get_font_name(font_name)
        
        # Resolve kleur
        color_ref = zone.get("color", "$colors.text")
        if color_ref.startswith("$colors."):
            color_key = color_ref.replace("$colors.", "")
            color_hex = brand.colors.get(color_key, "#45243D")
        else:
            color_hex = color_ref
        
        # Resolve tekst via data binding
        bind = zone.get("bind", role)
        text = _resolve_binding(bind, config, brand)
        if not text:
            continue
        
        size = zone.get("size", 10.0)
        x_pt = zone.get("x_pt", 0)
        y_pt = zone.get("y_pt", 0)
        align = zone.get("align", "left")
        
        # Converteer top-down y naar bottom-up
        rl_y = ph - y_pt
        
        canvas.saveState()
        canvas.setFont(font_name, size)
        canvas.setFillColor(HexColor(color_hex))
        
        if align == "right":
            canvas.drawRightString(x_pt, rl_y, text)
        elif align == "center":
            canvas.drawCentredString(x_pt, rl_y, text)
        else:
            canvas.drawString(x_pt, rl_y, text)
        
        canvas.restoreState()


def _resolve_binding(bind, config, brand):
    """Resolve data binding naar tekst waarde."""
    # Config velden
    bindings = {
        "project": config.project,
        "project_number": config.project_number,
        "client": config.client,
        "author": config.author,
        "report_type": config.report_type,
        "subtitle": config.subtitle,
    }
    # Contact velden
    if bind.startswith("contact."):
        key = bind.replace("contact.", "")
        return brand.contact.get(key, "")
    
    return bindings.get(bind, "")
```

### B6. Content frame uit brand config

In `page_templates.py` → `create_page_templates()`, lees content frame uit stationery config als die er is:

```python
# Content frame: gebruik brand stationery config als beschikbaar
content_spec = brand.stationery.get("content")
if content_spec and content_spec.content_frame:
    cf = content_spec.content_frame
    content_frame = Frame(
        cf["x_pt"],
        cf.get("y_pt", mb),  # y_pt is bottom-up in ReportLab!
        cf["width_pt"],
        cf["height_pt"],
        id="content_frame",
    )
else:
    # Fallback: bestaande marge-gebaseerde berekening
    content_frame = Frame(
        ml, mb + footer_h,
        page_w - ml - mr,
        page_h - mt - mb - header_h - footer_h,
        id="content_frame",
    )
```

---

## Deel C: Brand YAML met stationery configuratie

### C1. `assets/brands/3bm_cooperatie.yaml` — volledig herschrijven

Herschrijf het brand YAML bestand met de complete structuur. Neem de exacte waarden uit `HUISSTIJL_SPEC.md` en `SPEC_PAGINA_ARCHITECTUUR.md`.

Voeg minimaal toe:

```yaml
stationery:
  cover:
    source: ""  # Voorlopig leeg — wordt via build-brand gevuld
    text_zones: []
  colofon:
    source: ""
    header_footer: "colofon"
    text_zones: []
  content:
    source: ""  # Kan leeg blijven als er geen achtergrond is
    header_footer: "content"
    content_frame:
      x_pt: 90.0
      y_pt: 38.9       # bottom margin in ReportLab coords
      width_pt: 451.6   # 595.28 - 90.0 - 53.7
      height_pt: 746.0
  toc:
    source: ""
    header_footer: "content"
  appendix_divider:
    source: ""
    header_footer: null
    text_zones: []
  backcover:
    source: ""
    header_footer: null
    text_zones: []
```

### C2. Stationery bestanden extraheren

Maak een helper script `scripts/extract_3bm_stationery.py` dat de StationeryExtractor gebruikt om stationery uit `huisstijl/2707_BBLrapportage_v01.pdf` te extraheren:

```python
"""Eenmalig script: extraheer stationery voor 3BM Coöperatie."""
from pathlib import Path
from bm_reports.tools.stationery_extractor import StationeryExtractor

SOURCE = Path("huisstijl/2707_BBLrapportage_v01.pdf")
OUTPUT = Path("src/bm_reports/assets/graphics")

ext = StationeryExtractor(SOURCE)

# Backcover (pagina 36 = index 35) — volledig, geen tekst strippen
ext.extract_full_page(35, OUTPUT / "3bm-backcover.pdf")

# Appendix divider (pagina 21 = index 20) — strip "Bijlage" + titel tekst
# Bepaal strip zones door eerst de pagina te analyseren
ext.extract_stripped_page(20, OUTPUT / "3bm-appendix-divider.pdf", strip_zones=[
    # Pas deze coördinaten aan na visuele inspectie:
    (80, 170, 500, 220),    # "Bijlage N" zone (schatting)
    (80, 240, 500, 340),    # Titel zone (schatting)
])

# Cover (pagina 1 = index 0) — strip titel + subtitel
ext.extract_stripped_page(0, OUTPUT / "3bm-cover.pdf", strip_zones=[
    (40, 700, 540, 780),    # Titel zone (schatting)
    (40, 780, 540, 820),    # Subtitel zone (schatting)
])

# Briefpapier — kopieer direct
import shutil
shutil.copy("huisstijl/3BM-Briefpapier-Digitaal.pdf", OUTPUT / "3bm-briefpapier.pdf")

print("Stationery bestanden geëxtraheerd naar:", OUTPUT)
print("CONTROLEER visueel of de juiste zones geript zijn!")
print("Pas strip_zones aan als tekst nog zichtbaar is.")
```

**BELANGRIJK:** De strip_zones coördinaten hierboven zijn schattingen. Na het runnen van het script:
1. Open elk geëxtraheerd PDF bestand
2. Controleer of alle dynamische tekst verwijderd is
3. Controleer of grafische elementen intact zijn
4. Pas strip_zones aan en run opnieuw indien nodig

Update daarna `3bm_cooperatie.yaml` met de juiste `source:` paden:

```yaml
stationery:
  backcover:
    source: "graphics/3bm-backcover.pdf"
  cover:
    source: "graphics/3bm-cover.pdf"
  # etc.
```

---

## Deel D: Brand Builder CLI

### D1. `tools/brand_builder.py` — Orchestrator

Nieuw bestand dat de complete pipeline uitvoert:

```python
"""Brand Builder — genereer complete brand config uit huisstijl-documenten."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from bm_reports.tools.pdf_extractor import extract_pdf
from bm_reports.tools.page_classifier import classify_pages, PageType
from bm_reports.tools.pattern_detector import analyze_brand
from bm_reports.tools.config_generator import generate_brand_yaml, generate_analysis_report
from bm_reports.tools.stationery_extractor import StationeryExtractor

logger = logging.getLogger(__name__)


class BrandBuilder:
    """Genereert een volledige brand directory uit huisstijl-documenten."""
    
    def __init__(self, output_dir: Path, brand_name: str, brand_slug: str):
        self.output_dir = Path(output_dir)
        self.brand_name = brand_name
        self.brand_slug = brand_slug
    
    def build(
        self,
        referentie_rapport: Path,
        stamkaart: Path | None = None,
        briefpapier: Path | None = None,
        logo_dir: Path | None = None,
        font_dir: Path | None = None,
        base_brand: Path | None = None,
        dpi: int = 150,
    ) -> Path:
        """Voer de volledige pipeline uit.
        
        Returns pad naar output directory.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        stationery_dir = self.output_dir / "stationery"
        stationery_dir.mkdir(exist_ok=True)
        analysis_dir = self.output_dir / "analysis"
        analysis_dir.mkdir(exist_ok=True)
        logos_dir = self.output_dir / "logos"
        logos_dir.mkdir(exist_ok=True)
        
        # --- Stap 1: Analyseer referentie-rapport ---
        logger.info(f"[1/7] Analyseer {referentie_rapport.name}...")
        pages_dir = analysis_dir / "pages"
        raw_pages = extract_pdf(referentie_rapport, pages_dir, dpi=dpi)
        classified = classify_pages(raw_pages)
        page_images = [p.page_image_path for p in raw_pages if p.page_image_path]
        analysis = analyze_brand(classified, str(referentie_rapport), page_images)
        
        # --- Stap 2: Verrijk kleuren uit stamkaart ---
        if stamkaart:
            logger.info(f"[2/7] Verrijk kleuren uit {stamkaart.name}...")
            stamkaart_pages = extract_pdf(stamkaart)
            stamkaart_colors = self._extract_stamkaart_colors(stamkaart_pages)
            if stamkaart_colors:
                analysis.colors.update(stamkaart_colors)
                logger.info(f"  Stamkaart kleuren: {stamkaart_colors}")
        else:
            logger.info("[2/7] Geen stamkaart — skip")
        
        # --- Stap 3: Extraheer stationery ---
        logger.info("[3/7] Extraheer stationery...")
        extractor = StationeryExtractor(referentie_rapport)
        stationery_config = self._extract_stationery(extractor, classified, stationery_dir)
        
        # --- Stap 4: Kopieer briefpapier ---
        if briefpapier and briefpapier.exists():
            logger.info(f"[4/7] Kopieer briefpapier: {briefpapier.name}")
            shutil.copy(briefpapier, stationery_dir / "briefpapier.pdf")
            stationery_config["briefpapier"] = {"source": "stationery/briefpapier.pdf"}
        else:
            logger.info("[4/7] Geen briefpapier — skip")
        
        # --- Stap 5: Kopieer logo's ---
        if logo_dir and logo_dir.exists():
            logger.info(f"[5/7] Kopieer logo's uit {logo_dir}")
            for logo_file in logo_dir.iterdir():
                if logo_file.suffix.lower() in (".svg", ".png", ".pdf", ".eps"):
                    shutil.copy(logo_file, logos_dir / logo_file.name)
        else:
            logger.info("[5/7] Geen logo directory — skip")
        
        # --- Stap 6: Kopieer fonts ---
        if font_dir and font_dir.exists():
            fonts_dir = self.output_dir / "fonts"
            fonts_dir.mkdir(exist_ok=True)
            logger.info(f"[6/7] Kopieer fonts uit {font_dir}")
            for font_file in font_dir.iterdir():
                if font_file.suffix.lower() in (".ttf", ".otf", ".woff", ".woff2"):
                    shutil.copy(font_file, fonts_dir / font_file.name)
        else:
            logger.info("[6/7] Geen font directory — skip")
        
        # --- Stap 7: Genereer brand.yaml + rapport ---
        logger.info("[7/7] Genereer brand.yaml...")
        
        # Merge stationery config in analysis voor YAML generatie
        # TODO: generate_brand_yaml_v2 met stationery support
        yaml_str = generate_brand_yaml(analysis, self.brand_name, self.brand_slug)
        (self.output_dir / "brand.yaml").write_text(yaml_str, encoding="utf-8")
        
        report_str = generate_analysis_report(analysis)
        (analysis_dir / "report.md").write_text(report_str, encoding="utf-8")
        
        logger.info(f"Brand directory gereed: {self.output_dir}")
        return self.output_dir
    
    def _extract_stationery(self, extractor, classified, stationery_dir):
        """Extraheer stationery per paginatype."""
        config = {}
        
        for cp in classified:
            page_idx = cp.page.page_number - 1  # 0-based
            
            if cp.page_type == PageType.BACKCOVER:
                path = extractor.extract_full_page(page_idx, stationery_dir / "backcover.pdf")
                config["backcover"] = {"source": f"stationery/backcover.pdf"}
                logger.info(f"  Backcover: pagina {cp.page.page_number} → {path.name}")
            
            elif cp.page_type == PageType.APPENDIX_DIVIDER:
                # Strip bijlage nummer en titel
                strip_zones = self._detect_appendix_strip_zones(cp.page)
                path = extractor.extract_stripped_page(
                    page_idx, stationery_dir / "appendix_divider.pdf", strip_zones,
                )
                config["appendix_divider"] = {"source": f"stationery/appendix_divider.pdf"}
                logger.info(f"  Appendix divider: pagina {cp.page.page_number} → {path.name}")
            
            elif cp.page_type == PageType.COVER:
                # Strip titel en subtitel zones
                strip_zones = self._detect_cover_strip_zones(cp.page)
                path = extractor.extract_stripped_page(
                    page_idx, stationery_dir / "cover.pdf", strip_zones,
                )
                config["cover"] = {"source": f"stationery/cover.pdf"}
                logger.info(f"  Cover: pagina {cp.page.page_number} → {path.name}")
        
        return config
    
    def _detect_cover_strip_zones(self, page):
        """Bepaal welke tekst-zones op de cover geript moeten worden.
        
        Strategie: de grootste tekst (titel) en op-één-na-grootste (subtitel)
        worden geript. Logo en badges blijven staan.
        """
        if not page.texts:
            return []
        
        sorted_texts = sorted(page.texts, key=lambda t: t.size, reverse=True)
        zones = []
        
        # Grootste tekst = titel
        if sorted_texts:
            t = sorted_texts[0]
            # Maak zone iets groter dan de tekst zelf
            zones.append((t.x - 5, t.y_top - 5, t.x2 + 5, t.y_bottom + 5))
        
        # Op-één-na-grootste = subtitel (als significant kleiner dan titel)
        if len(sorted_texts) > 1:
            t = sorted_texts[1]
            if t.size > 12:  # Alleen als het echt een subtitel is
                zones.append((t.x - 5, t.y_top - 5, t.x2 + 5, t.y_bottom + 5))
        
        return zones
    
    def _detect_appendix_strip_zones(self, page):
        """Bepaal welke tekst-zones op de appendix divider geript moeten worden."""
        if not page.texts:
            return []
        
        zones = []
        for t in page.texts:
            # Strip alle grote tekst (bijlagenummer + titel)
            if t.size > 20:
                zones.append((t.x - 5, t.y_top - 5, t.x2 + 5, t.y_bottom + 5))
        
        return zones
    
    def _extract_stamkaart_colors(self, pages):
        """Extraheer kleuren uit stamkaart (best effort).
        
        Zoekt naar RGB-patronen in tekst naast kleurvlakken.
        """
        import re
        
        colors = {}
        for page_data in pages:
            for t in page_data.texts:
                text = t.text.strip()
                
                # Patroon: "R123 G45 B67" of "123 / 45 / 67"
                rgb_match = re.match(
                    r'R?\s*(\d{1,3})\s*[/\s]+G?\s*(\d{1,3})\s*[/\s]+B?\s*(\d{1,3})', text
                )
                if rgb_match:
                    r, g, b = int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3))
                    if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                        hex_color = f"#{r:02X}{g:02X}{b:02X}"
                        # Zoek dichtstbijzijnde rect op dezelfde pagina
                        label = self._find_color_label(t, page_data.texts)
                        if label:
                            colors[label] = hex_color
                
                # Patroon: "#401246" (direct hex)
                hex_match = re.match(r'#([0-9A-Fa-f]{6})', text)
                if hex_match:
                    hex_color = f"#{hex_match.group(1).upper()}"
                    label = self._find_color_label(t, page_data.texts)
                    if label:
                        colors[label] = hex_color
        
        return colors
    
    def _find_color_label(self, color_text, all_texts):
        """Zoek een label-tekst dichtbij de kleurcode-tekst."""
        # Zoek tekst binnen 50pt boven de kleurcode
        for t in all_texts:
            if t is color_text:
                continue
            if (abs(t.x - color_text.x) < 50 and 
                0 < (color_text.y_top - t.y_bottom) < 50):
                label = t.text.strip().lower().replace(" ", "_")
                if label and not any(c.isdigit() for c in label):
                    return label
        return None
```

### D2. CLI command — `src/bm_reports/cli.py`

Voeg `build-brand` toe onder de bestaande `analyze-brand`:

```python
# In main():
bb_parser = subparsers.add_parser("build-brand", help="Genereer complete brand directory")
bb_parser.add_argument("--rapport", "-r", required=True, help="Pad naar referentie-rapport PDF")
bb_parser.add_argument("--stamkaart", "-s", help="Pad naar stamkaart PDF")
bb_parser.add_argument("--briefpapier", "-b", help="Pad naar briefpapier PDF")
bb_parser.add_argument("--logos", "-l", help="Pad naar logo directory")
bb_parser.add_argument("--fonts", help="Pad naar fonts directory")
bb_parser.add_argument("--base-brand", help="Pad naar bestaande brand directory (voor varianten)")
bb_parser.add_argument("--name", required=True, help="Brand weergavenaam")
bb_parser.add_argument("--slug", required=True, help="Brand slug (machine-leesbaar)")
bb_parser.add_argument("--output", "-o", required=True, help="Output directory")
bb_parser.add_argument("--dpi", type=int, default=150, help="DPI voor pagina renders")

# In command dispatch:
elif args.command == "build-brand":
    _cmd_build_brand(args)


def _cmd_build_brand(args):
    """Genereer complete brand directory."""
    from bm_reports.tools.brand_builder import BrandBuilder
    
    builder = BrandBuilder(
        output_dir=Path(args.output),
        brand_name=args.name,
        brand_slug=args.slug,
    )
    
    result = builder.build(
        referentie_rapport=Path(args.rapport),
        stamkaart=Path(args.stamkaart) if args.stamkaart else None,
        briefpapier=Path(args.briefpapier) if args.briefpapier else None,
        logo_dir=Path(args.logos) if args.logos else None,
        font_dir=Path(args.fonts) if args.fonts else None,
        base_brand=Path(args.base_brand) if args.base_brand else None,
        dpi=args.dpi,
    )
    
    print(f"✓ Brand directory gegenereerd: {result}")
```

---

## Deel E: Registreer tools exports

### E1. `src/bm_reports/tools/__init__.py`

Voeg de nieuwe exports toe:

```python
from bm_reports.tools.pdf_extractor import extract_pdf, RawPageData, TextElement, RectElement, ImageElement
from bm_reports.tools.page_classifier import classify_pages, ClassifiedPage, PageType
from bm_reports.tools.pattern_detector import analyze_brand, BrandAnalysis
from bm_reports.tools.config_generator import generate_brand_yaml, generate_analysis_report
from bm_reports.tools.stationery_extractor import StationeryExtractor
from bm_reports.tools.brand_builder import BrandBuilder

__all__ = [
    "extract_pdf", "RawPageData", "TextElement", "RectElement", "ImageElement",
    "classify_pages", "ClassifiedPage", "PageType",
    "analyze_brand", "BrandAnalysis",
    "generate_brand_yaml", "generate_analysis_report",
    "StationeryExtractor",
    "BrandBuilder",
]
```

---

## Verificatie

### Test 1: Font/kleur fixes

```bash
cd src/bm_reports
python -c "
from core.styles import BM_COLORS, BM_FONTS, BM_STYLES
print('Colors:')
print(f'  primary:  {BM_COLORS.primary}')     # Moet: #401246
print(f'  secondary: {BM_COLORS.secondary}')   # Moet: #38BDAB
print(f'  text_accent: {BM_COLORS.text_accent}')# Moet: #56B49B
print()
print('Fonts:')
print(f'  heading: {BM_FONTS.heading}')   # Moet: GothamBold (of Helvetica-Bold als fallback)
print(f'  body:    {BM_FONTS.body}')      # Moet: GothamBook (of Helvetica als fallback)
print(f'  body_size: {BM_FONTS.body_size}')   # Moet: 9.5
print(f'  h1_size: {BM_FONTS.heading1_size}') # Moet: 18.0
print()
print('Styles:')
h1 = BM_STYLES['Heading1']
print(f'  H1 font: {h1.fontName}')   # Moet: GothamBook (NIET GothamBold!)
print(f'  H1 color: {h1.textColor}') # Moet: #45243d (text, NIET primary)
h2 = BM_STYLES['Heading2']
print(f'  H2 color: {h2.textColor}') # Moet: #56b49b (text_accent)
"
```

### Test 2: Stationery extractor

```bash
python -c "
from pathlib import Path
from bm_reports.tools.stationery_extractor import StationeryExtractor

ext = StationeryExtractor(Path('huisstijl/2707_BBLrapportage_v01.pdf'))
ext.extract_full_page(35, Path('test_backcover.pdf'))
print('Backcover geëxtraheerd → test_backcover.pdf')
print('Open en vergelijk met huisstijl/pages/page_36.png')
"
```

### Test 3: Stationery renderer

```bash
python -c "
from pathlib import Path
from bm_reports.core.stationery import StationeryRenderer

renderer = StationeryRenderer()
# Gebruik het briefpapier als test
from reportlab.pdfgen import canvas
c = canvas.Canvas('test_stationery.pdf', pagesize=(595.28, 841.89))
result = renderer.draw(c, Path('huisstijl/3BM-Briefpapier-Digitaal.pdf'), 595.28, 841.89)
c.showPage()
c.save()
print(f'Stationery render: {result}')
print('Open test_stationery.pdf — moet briefpapier tonen')
"
```

### Test 4: Volledig rapport

```bash
python -c "
from bm_reports import Report, A4
report = Report(format=A4, project='Stationery Test', project_number='2026-TEST', 
                client='Test Client', brand='3bm_cooperatie')
report.add_cover(subtitle='Test rapport stationery-architectuur')
report.add_colofon()
report.add_section('Hoofdstuk 1', content=['Test paragraaf met correct font en kleur.'])
report.add_section('Subsectie', level=2, content=['Turquoise heading verwacht.'])
report.add_backcover()
report.build('test_huisstijl_output.pdf')
print('Rapport gegenereerd → test_huisstijl_output.pdf')
print('Vergelijk met huisstijl/pages/')
"
```

### Test 5: Brand Builder CLI

```bash
bm-report build-brand \
  --rapport huisstijl/2707_BBLrapportage_v01.pdf \
  --stamkaart huisstijl/3BM-Stamkaart.pdf \
  --briefpapier huisstijl/3BM-Briefpapier-Digitaal.pdf \
  --fonts src/bm_reports/assets/fonts/ \
  --name "3BM Coöperatie" \
  --slug "3bm-cooperatie" \
  --output test_brand_output/
```

Controleer daarna:
- `test_brand_output/brand.yaml` — bevat kleuren, fonts, stationery paden
- `test_brand_output/stationery/backcover.pdf` — pixel-perfect backcover
- `test_brand_output/stationery/cover.pdf` — cover zonder titel/subtitel
- `test_brand_output/analysis/report.md` — leesbaar analyserapport

---

## Samenvatting bestanden

### Nieuw
| Bestand | Doel |
|---------|------|
| `tools/stationery_extractor.py` | PDF pagina's extraheren als stationery |
| `tools/brand_builder.py` | Complete brand directory generatie pipeline |
| `core/stationery.py` | PDF/PNG achtergrond rendering op ReportLab canvas |
| `scripts/extract_3bm_stationery.py` | Eenmalig script voor 3BM stationery |

### Gewijzigd
| Bestand | Wijziging |
|---------|-----------|
| `core/styles.py` | Colors: fix hex waarden + nieuwe velden. FontConfig: fix sizes. Headings: fix font/kleur |
| `core/special_pages.py` | Hardcoded kleuren → brand.colors. Helper functies _brand_primary/secondary/text |
| `core/brand.py` | +StationeryPageConfig, +brand_dir, BrandLoader directory support |
| `core/page_templates.py` | Stationery-first onPage callbacks, content_frame uit brand |
| `assets/brands/3bm_cooperatie.yaml` | Fix fonts, fix colors, +stationery sectie |
| `tools/__init__.py` | +StationeryExtractor, +BrandBuilder exports |
| `cli.py` | +build-brand command |
| `pyproject.toml` | +pdfrw dependency |
| `components/table_block.py` | Gebruik BM_COLORS.table_header_bg i.p.v. hardcoded |
