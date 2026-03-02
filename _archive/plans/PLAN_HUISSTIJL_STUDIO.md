# Plan: Huisstijl Studio — Automatische brand extractie uit designdocumenten

## Visie

Een CLI-tool + toekomstige frontend die van een **set huisstijl-documenten** een complete, 
productie-klare brand configuratie genereert. Input = wat de huisstijl-specialist aanlevert. 
Output = alles wat de report generator nodig heeft.

---

## Input: wat levert de designer aan?

Typische set documenten per bureau:

| Document | Bevat | Voorbeeld |
|----------|-------|-----------|
| **Stamkaart** | Kleurenpalet (PMS/CMYK/RGB), fonts, grid, beeldmerk | `3BM-Stamkaart.pdf` (6 pag) |
| **Briefpapier** | Kant-en-klare stationery met header/footer/logo | `3BM-Briefpapier-Digitaal.pdf` (1 pag) |
| **Referentie-rapport** | Alle paginatypes in context (cover, colofon, content, bijlagen, backcover) | `2707_BBLrapportage_v01.pdf` (36 pag) |
| **Logo's** | SVG/PDF/PNG in kleur, wit, grijswaarden | `logo's/RGB/SVG/3BM-Logo.svg` |
| **Tone of voice** | Schrijfstijl richtlijnen (niet voor tool, maar goed om te hebben) | `3BM-Tone-of-voice.pdf` |

De tool moet per rapport-type (BBL, constructie, brandveiligheid) een **variant** kunnen genereren 
met dezelfde basiskleuren/fonts maar ander referentie-rapport.

---

## Output: wat produceren we?

```
assets/brands/{slug}/
├── brand.yaml              # Volledige brand config (kleuren, fonts, styles, text zones)
├── stationery/
│   ├── cover.pdf           # Cover achtergrond (zonder projectfoto/titel)
│   ├── colofon.pdf         # Colofon achtergrond (zonder dynamische tekst)
│   ├── content.pdf         # Content pagina achtergrond (header/footer)
│   ├── toc.pdf             # TOC achtergrond
│   ├── appendix_divider.pdf # Bijlage-scheidingspagina (zonder nummer/titel)
│   ├── backcover.pdf       # Achterpagina (100% statisch)
│   └── briefpapier.pdf     # Briefpapier stationery
├── logos/
│   ├── main.svg            # Hoofdlogo (kleur)
│   ├── wit.svg             # Wit logo (voor op donkere vlakken)
│   └── grijswaarden.svg    # Grijswaarden variant
└── analysis/
    ├── report.md           # Uitgebreid analyserapport
    ├── colors.json         # Geëxtraheerd kleurenpalet met bronnen
    ├── fonts.json           # Font mapping met sizes per context
    └── pages/              # Preview PNG's per pagina
        ├── page_001.png
        └── ...
```

---

## Architectuur: 5 stappen pipeline

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  1. COLLECT   │────>│  2. ANALYZE  │────>│  3. EXTRACT   │
│  Documenten   │     │  Per pagina  │     │  Stationery   │
│  inventariseer│     │  classificeer│     │  + logo's     │
└──────────────┘     └──────────────┘     └──────────────┘
                                                │
                     ┌──────────────┐     ┌─────▼────────┐
                     │  5. OUTPUT   │<────│  4. MAP       │
                     │  YAML + dirs │     │  Text zones   │
                     └──────────────┘     └──────────────┘
```

### Stap 1: COLLECT — Document inventarisatie

```python
class DocumentSet:
    """Verzameling van input documenten voor brand extractie."""
    
    stamkaart: Path | None       # Kleurenpalet, fonts, grid
    briefpapier: Path | None     # Briefpapier stationery
    referentie_rapport: Path     # Hoofd-referentiedocument (VERPLICHT)
    logo_dir: Path | None        # Map met logo bestanden
    extra_rapporten: list[Path]  # Optioneel: andere rapporttypen ter vergelijking
```

**Logica:**
- `referentie_rapport` is verplicht — hieruit worden paginatypes geclassificeerd
- `stamkaart` is optioneel maar sterk aanbevolen — levert exacte kleurcodes
- `briefpapier` is optioneel — wordt direct als stationery overgenomen
- `logo_dir` is optioneel — kopieert SVG/PNG naar output

### Stap 2: ANALYZE — Gecombineerde analyse

Breidt de bestaande `analyze_brand()` pipeline uit met:

#### 2a. Stamkaart kleur-extractie (NIEUW)

De stamkaart bevat typisch:
- Pagina met kleurvlakken + PMS/CMYK/RGB codes als tekst
- Font voorbeelden met namen en sizes

```python
def extract_colors_from_stamkaart(stamkaart_pages: list[RawPageData]) -> dict[str, str]:
    """Extraheer kleurenpalet uit stamkaart PDF.
    
    Zoekt naar patronen als:
    - RGB tekst "R123 G45 B67" of "123/45/67" naast kleurvlakken
    - Hex codes "#401246" 
    - PMS referenties "PMS 5195" 
    - CMYK "C76 M100 Y36 K43"
    
    Matcht kleurtekst aan het dichtstbijzijnde kleurvlak op dezelfde pagina.
    """
```

**Waarom stamkaart > referentie-rapport voor kleuren:**
De referentie-rapport levert kleuren via pixel-sampling (onnauwkeurig door antialiasing, 
JPEG-compressie, kleurprofielen). De stamkaart heeft de EXACTE RGB/PMS waarden als tekst.

#### 2b. Font detectie verbetering

Huidige font detectie pakt embedded font-namen op (bijv. "Gotham-Book"). 
Verbeter met:
- Koppeling aan font-bestanden in `logo_dir` of een `fonts/` map
- Stamkaart: zoek tekst als "Gotham Book" / "Gotham Bold" bij font-voorbeelden
- Rapport: bevestig door te matchen welke fonts op welke sizes voorkomen

#### 2c. Paginatype analyse (bestaand, uitbreiden)

De bestaande `page_classifier.py` werkt al. Uitbreiden met:
- **Betere cover detectie**: check voor projectfoto clip-path (niet alleen grote rects)
- **Colofon**: detecteer het 2-kolom label-waarde patroon preciezer
- **Meerdere bijlage-dividers**: classificeer ze allemaal (niet alleen de eerste)

### Stap 3: EXTRACT — Stationery generatie (NIEUW, kernfunctionaliteit)

```python
class StationeryExtractor:
    """Extraheer stationery-achtergronden uit referentie-PDF."""
    
    def extract_page_as_pdf(self, page_num: int) -> Path:
        """Extraheer hele pagina als vectoriële PDF (voor 100% statische pagina's)."""
    
    def extract_page_stripped(self, page_num: int, strip_zones: list[Rect]) -> Path:
        """Extraheer pagina met specifieke zones leeggemaakt (wit gemaakt).
        
        Gebruik voor pagina's waar je dynamische tekst wilt plaatsen:
        - Cover: strip projecttitel en ondertitel zones
        - Colofon: strip alle label-waarde tekst + rapport-titel
        - Appendix divider: strip "Bijlage N" en titel
        - Content: strip alles behalve header/footer (= briefpapier stationery)
        """
    
    def extract_page_graphics_only(self, page_num: int) -> Path:
        """Extraheer pagina met ALLE tekst verwijderd.
        
        Behoudt: kleurvlakken, lijnen, afbeeldingen, geometrie.
        Verwijdert: alle tekst (inclusief logo-tekst — let op!).
        """
    
    def extract_content_stationery(self, content_pages: list[int]) -> Path:
        """Genereer stationery voor content pagina's.
        
        Neemt de herhalende elementen (header/footer) van content pagina's
        en maakt daar één schone stationery-pagina van.
        
        Als er geen header/footer is (zoals bij 3BM BBL rapporten):
        → Output is een blanco pagina (of None).
        """
```

**Implementatie detail: tekst verwijderen uit PDF**

PyMuPDF's `page.add_redact_annot()` + `page.apply_redactions()` kan tekst verwijderen 
terwijl de onderliggende grafische elementen behouden blijven. Dit is de kern van de 
stationery-extractie.

```python
def strip_text_zones(page, zones: list[fitz.Rect]) -> None:
    """Verwijder tekst in specifieke zones, behoud grafische elementen."""
    for zone in zones:
        # Vind tekst in deze zone
        text_instances = page.get_text("dict", clip=zone)
        for block in text_instances["blocks"]:
            if block["type"] == 0:  # tekst
                rect = fitz.Rect(block["bbox"])
                page.add_redact_annot(rect, fill=(1, 1, 1))  # wit invullen
    page.apply_redactions()
```

**Per paginatype:**

| Type | Extractie methode | Strip zones |
|------|-------------------|-------------|
| Cover | `extract_page_stripped` | Titel zone (onder), ondertitel zone, projectfoto |
| Colofon | `extract_page_stripped` | Rapporttitel, subtitel, alle label-waarde paren |
| TOC | Niet extraheren | Volledig programmatisch (alleen tekst) |
| Content | `extract_content_stationery` | Alles behalve paginanummer |
| Appendix divider | `extract_page_stripped` | "Bijlage N" tekst, titel regels |
| Backcover | `extract_page_as_pdf` | NIETS — 100% statisch |
| Briefpapier | Direct kopiëren | Input briefpapier PDF = stationery |

### Stap 4: MAP — Text zone definitie (NIEUW)

Na extractie weten we WAT er is verwijderd. Nu moeten we definiëren WAAR dynamische tekst 
komt. Dit wordt opgeslagen in de brand YAML.

```yaml
stationery:
  cover:
    source: "stationery/cover.pdf"
    text_zones:
      # Waar komt de projectfoto?
      - role: hero_image
        type: clipped_image
        clip_polygon: [[350.8, 159.8], [383.7, 192.7], ...]  # uit analyse
      # Waar komt de titel?
      - role: title
        x_pt: 54.28
        y_pt: 93.47      # PDF y-up coords
        font: "$fonts.heading"
        size: 28.9
        color: "$colors.primary"
        max_width_pt: 490
      # Ondertitel
      - role: subtitle
        x_pt: 55.0
        y_pt: 63.0
        font: "$fonts.body"
        size: 17.8
        color: "$colors.secondary"
        max_width_pt: 490

  colofon:
    source: "stationery/colofon.pdf"
    text_zones:
      - role: report_type
        x_pt: 70.9
        y_pt: 57.3       # top-down!
        font: "$fonts.heading"
        size: 22.0
        color: "$colors.primary"
      - role: subtitle
        x_pt: 70.9
        y_pt: 86.8
        font: "$fonts.body"
        size: 14.0
        color: "$colors.secondary"
      - role: field_table
        type: key_value_table
        label_x_pt: 103
        value_x_pt: 229
        fields: [...]

  content:
    source: "stationery/content.pdf"  # Kan null zijn als er geen header/footer is
    content_frame:
      x_pt: 56.69
      y_pt: 48.0
      width_pt: 481.89
      height_pt: 746.0
    text_zones:
      - role: page_number
        x_pt: 541.6
        y_pt: 35.7
        font: "$fonts.body"
        size: 9.5
        color: "$colors.text"
        align: right
  
  backcover:
    source: "stationery/backcover.pdf"
    # Geen text_zones — 100% statisch
  
  briefpapier:
    source: "stationery/briefpapier.pdf"
    content_frame:
      x_pt: 70
      y_pt: 100
      width_pt: 455
      height_pt: 620
```

**Hoe text zones worden bepaald:**
1. Classificeer de pagina (bestaande code)
2. Groepeer tekstelementen per "rol" (titel, labels, body, paginanummer)
3. Bereken bounding boxes per groep
4. Die bounding boxes = text zones
5. Font, size, color per zone = mediaan van tekst in die zone

### Stap 5: OUTPUT — Alles samenvoegen

```python
class BrandBuilder:
    """Orchestreert de volledige brand-extractie pipeline."""
    
    def build(self, doc_set: DocumentSet, output_dir: Path, brand_name: str, brand_slug: str):
        """Voer de complete pipeline uit."""
        
        # 1. Analyseer referentie-rapport (bestaande pipeline)
        rapport_pages = extract_pdf(doc_set.referentie_rapport, ...)
        classified = classify_pages(rapport_pages)
        analysis = analyze_brand(classified, ...)
        
        # 2. Verrijk met stamkaart (kleuren)
        if doc_set.stamkaart:
            stamkaart_pages = extract_pdf(doc_set.stamkaart, ...)
            stamkaart_colors = extract_colors_from_stamkaart(stamkaart_pages)
            analysis.colors.update(stamkaart_colors)  # Stamkaart overschrijft
        
        # 3. Extraheer stationery per paginatype
        extractor = StationeryExtractor(doc_set.referentie_rapport)
        for page_type, page_num in self._get_type_pages(classified):
            stationery_path = extractor.extract(page_type, page_num, output_dir)
        
        # 4. Kopieer briefpapier als stationery
        if doc_set.briefpapier:
            shutil.copy(doc_set.briefpapier, output_dir / "stationery/briefpapier.pdf")
        
        # 5. Kopieer logo's
        if doc_set.logo_dir:
            self._copy_logos(doc_set.logo_dir, output_dir / "logos")
        
        # 6. Map text zones per stationery pagina
        text_zones = self._map_text_zones(classified, analysis)
        
        # 7. Genereer brand YAML
        yaml_str = generate_brand_yaml_v2(analysis, text_zones, brand_name, brand_slug)
        (output_dir / "brand.yaml").write_text(yaml_str)
        
        # 8. Genereer analyserapport
        report = generate_analysis_report(analysis)
        (output_dir / "analysis/report.md").write_text(report)
```

---

## CLI interface

```bash
# Volledige brand extractie (aanbevolen)
openaec-report build-brand \
  --rapport huisstijl/2707_BBLrapportage_v01.pdf \
  --stamkaart huisstijl/3BM-Stamkaart.pdf \
  --briefpapier huisstijl/3BM-Briefpapier-Digitaal.pdf \
  --logos huisstijl/logo\'s/RGB/SVG/ \
  --name "3BM Coöperatie" \
  --slug "3bm-cooperatie" \
  --output src/openaec_reports/assets/brands/3bm-cooperatie/

# Minimaal (alleen referentie-rapport)
openaec-report build-brand \
  --rapport huisstijl/2707_BBLrapportage_v01.pdf \
  --name "3BM BBL" \
  --slug "3bm-bbl" \
  --output brands/3bm-bbl/

# Variant voor ander rapporttype (hergebruikt base brand)
openaec-report build-brand \
  --rapport huisstijl/3BM-250206-Constructierapport.pdf \
  --base-brand src/openaec_reports/assets/brands/3bm-cooperatie/ \
  --name "3BM Constructie" \
  --slug "3bm-constructie" \
  --output brands/3bm-constructie/
```

De `--base-brand` optie is krachtig: het hergebruikt kleuren, fonts en logo's van een 
bestaande brand, maar extraheert nieuwe stationery en text zones uit het andere rapport.

---

## Renderer aanpassing

De huidige `special_pages.py` moet de stationery-first aanpak ondersteunen:

```python
def draw_page(canvas, doc, page_type, config, brand, stationery_renderer, **kwargs):
    """Universele pagina-renderer met stationery-first strategie.
    
    1. Als stationery beschikbaar → teken achtergrond PDF/PNG
    2. Teken dynamische content in text zones
    3. Als GEEN stationery → fallback naar programmatische rendering
    """
    # Laag 1: Stationery achtergrond
    has_stationery = stationery_renderer.draw(canvas, page_type, pw, ph)
    
    if has_stationery:
        # Laag 2: Dynamische tekst in gedefinieerde zones
        text_zones = brand.stationery[page_type].text_zones
        for zone in text_zones:
            _draw_text_zone(canvas, zone, config, kwargs)
    else:
        # Fallback: bestaande programmatische rendering
        _FALLBACK_RENDERERS[page_type](canvas, doc, config, brand, **kwargs)
```

---

## Prioriteit en fasering

### Fase 1: StationeryExtractor + backcover fix (hoogste impact)
- `tools/stationery_extractor.py` — extract_page_as_pdf(), extract_page_stripped()  
- Extraheer backcover uit referentie-PDF
- StationeryRenderer in special_pages.py
- **Resultaat:** Backcover is pixel-perfect

### Fase 2: Stamkaart kleur-extractie
- `tools/stamkaart_parser.py` — extract_colors_from_stamkaart()
- Pattern matching op RGB/PMS/CMYK tekst naast kleurvlakken  
- Integreer in analyze_brand pipeline
- **Resultaat:** Exacte kleuren uit designdocument

### Fase 3: Text zone mapping
- Automatische text zone detectie per paginatype
- YAML stationery sectie met text_zones
- Generieke renderer die text zones uitleest
- **Resultaat:** Cover, colofon, appendix divider via stationery + zones

### Fase 4: Brand Builder CLI
- `build-brand` CLI command
- DocumentSet input, volledige pipeline
- `--base-brand` voor varianten
- Briefpapier + logo kopiëren
- **Resultaat:** End-to-end automatisering

### Fase 5: Brand Builder Frontend (toekomst)
- Visuele tool in de frontend
- Upload documenten
- Preview stationery met text zone overlays
- Handmatig corrigeren van auto-detectie
- Live YAML preview
- Export naar assets/brands/

---

## Relatie tot bestaande code

| Bestaand | Actie |
|----------|-------|
| `tools/pdf_extractor.py` | Behouden, uitbreiden met image export per pagina |
| `tools/page_classifier.py` | Behouden, verfijnen classificatie |
| `tools/pattern_detector.py` | Behouden, uitbreiden met text zone mapping |
| `tools/config_generator.py` | Herschrijven → `brand_builder.py` met stationery support |
| `core/special_pages.py` | Uitbreiden met stationery-first rendering |
| `core/brand.py` | Uitbreiden met `StationeryConfig` en `TextZone` |
| `core/brand_renderer.py` | Uitbreiden met `StationeryRenderer` |
| `cli.py` | `build-brand` command toevoegen |

---

## Open vragen

1. **PDF-als-achtergrond: pdfrw of PyMuPDF?**
   - `pdfrw` kan PDF pagina's als XObject embedden in ReportLab (vector kwaliteit)
   - `PyMuPDF` kan PDF pagina's renderen als raster (PNG)
   - Aanbeveling: `pdfrw` voor maximale kwaliteit, PNG als fallback

2. **Tekst strippen: redact vs. content stream editing?**
   - Redact: simpel maar laat soms witte vlakken achter over grafische elementen
   - Content stream editing: complexer maar chirurgischer
   - Aanbeveling: Start met redact, switch naar content stream als nodig

3. **Briefpapier als content stationery?**
   - Het briefpapier heeft al header/footer/logo → perfect als content stationery
   - Maar het heeft een ander content frame dan het rapport (andere marges)
   - Aanbeveling: Briefpapier = apart stationery type, niet hergebruiken voor rapporten

4. **Meerdere rapporttypen per bureau**
   - BBL rapport vs. constructierapport vs. brandveiligheidsrapport
   - Zelfde kleuren/fonts, maar mogelijk andere cover-layout of stationery
   - Oplossing: `--base-brand` flag die kleuren/fonts/logos overerft maar stationery per rapport-type extraheert
