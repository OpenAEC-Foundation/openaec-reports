# Architectuurplan: Template-Driven Report Engine
## Datum: 2026-02-28
## Status: GOEDGEKEURD

---

## 1. Kernprincipe

```
TEMPLATE  = documentstructuur (volgorde + type pagina's)
PAGE_TYPE = wat er op een pagina komt (stationery + text zones + optioneel tabel)
DATA      = JSON met feitelijke inhoud
ENGINE    = generiek, nul tenant-specifieke code
```

---

## 2. Drie pagina-modes

| Mode | Gedrag | Gebruik |
|------|--------|---------|
| `special` | Stationery + text zones, geen content | Voorblad, colofon, achterblad |
| `flow` | Stationery + header/footer, ReportLab flowables stromen door | Inhoudspagina's, berekeningen |
| `fixed` | Stationery + text zones + optioneel tabel op vaste positie | BIC controles, detail tabellen |

Paginering:
- **flow**: ReportLab paginateert automatisch (flowables → overflow → nieuwe pagina)
- **fixed** met `repeat: auto`: Engine paginateert tabeldata (rijen > max_y → volgende pagina, zelfde stationery)

---

## 3. Tenant directory structuur

```
tenants/
├── 3bm_cooperatie/
│   ├── brand.yaml                    # kleuren, fonts, contact
│   ├── stationery/                   # achtergrond PDFs
│   │   ├── voorblad.pdf
│   │   ├── colofon.pdf
│   │   ├── standaard.pdf             # content pagina met header/footer
│   │   ├── bijlage.pdf
│   │   └── achterblad.pdf
│   ├── templates/                    # documentstructuur
│   │   ├── rapport.yaml
│   │   ├── berekening.yaml
│   │   └── offerte.yaml
│   └── page_types/                   # pagina-inhoud definities
│       ├── voorblad.yaml
│       ├── colofon.yaml
│       ├── inhoud.yaml               # content_frame voor flow
│       └── achterblad.yaml
│
├── symitech/
│   ├── brand.yaml
│   ├── stationery/
│   │   ├── voorblad_bic.pdf
│   │   ├── locatie.pdf               # bevat blauwe lijnen, sectie-headers
│   │   ├── bic_controles.pdf         # bevat kolomkoppen, lijnen
│   │   ├── detail_landscape.pdf
│   │   ├── objecten_landscape.pdf
│   │   ├── standaard.pdf             # voor simpel rapport flow
│   │   └── achterblad.pdf
│   ├── templates/
│   │   ├── bic_factuur.yaml
│   │   └── rapport.yaml
│   └── page_types/
│       ├── voorblad_bic.yaml
│       ├── locatie.yaml
│       ├── bic_controles.yaml
│       ├── detail_weergave.yaml
│       ├── objecten.yaml
│       ├── inhoud.yaml
│       └── achterblad.yaml
```

---

## 4. YAML Schema's

### 4.1 Template (documentstructuur)

```yaml
# tenants/symitech/templates/bic_factuur.yaml
name: symitech_bic_factuur
tenant: symitech

pages:
  - type: special
    page_type: voorblad_bic
    orientation: portrait

  - type: fixed
    page_type: locatie
    orientation: portrait

  - type: fixed
    page_type: bic_controles
    orientation: portrait
    repeat: auto

  - type: fixed
    page_type: detail_weergave
    orientation: landscape
    repeat: auto

  - type: fixed
    page_type: objecten
    orientation: landscape
    repeat: auto

  - type: special
    page_type: achterblad
    orientation: portrait
```

```yaml
# tenants/3bm_cooperatie/templates/rapport.yaml
name: 3bm_rapport
tenant: 3bm_cooperatie

pages:
  - type: special
    page_type: voorblad
    orientation: portrait

  - type: special
    page_type: colofon
    orientation: portrait

  - type: toc
    page_type: inhoud           # gebruikt dezelfde stationery als inhoud
    orientation: portrait

  - type: flow
    page_type: inhoud
    orientation: portrait

  - type: special
    page_type: achterblad
    orientation: portrait

  # bijlagen optioneel, toegevoegd via JSON data
```

```yaml
# tenants/3bm_cooperatie/templates/berekening.yaml
name: 3bm_berekening
tenant: 3bm_cooperatie

pages:
  - type: flow
    page_type: inhoud
    orientation: portrait
```

```yaml
# tenants/3bm_cooperatie/templates/offerte.yaml
name: 3bm_offerte
tenant: 3bm_cooperatie

pages:
  - type: special
    page_type: voorblad
    orientation: portrait

  - type: flow
    page_type: inhoud
    orientation: portrait
```

### 4.2 Page Type (pagina-inhoud)

#### Special page — alleen text zones
```yaml
# tenants/symitech/page_types/voorblad_bic.yaml
name: voorblad_bic
stationery: voorblad_bic.pdf

text_zones:
  - bind: meta.factuur_kop
    x_mm: 20
    y_mm: 99
    font: heading
    size: 14
    color: primary
  - bind: meta.datum
    x_mm: 20
    y_mm: 110
    font: body
    size: 10
  - bind: meta.factuurnummer
    x_mm: 20
    y_mm: 120
    font: body
    size: 10
  - bind: project
    x_mm: 20
    y_mm: 135
    font: heading
    size: 12
    color: primary
```

#### Fixed page — text zones + tabel
```yaml
# tenants/symitech/page_types/bic_controles.yaml
name: bic_controles
stationery: bic_controles.pdf

text_zones:
  - bind: location.name
    x_mm: 185
    y_mm: 30
    align: right
    font: heading
    size: 14
    color: primary

table:
  data_bind: bic_sections
  origin:
    x_mm: 20
    y_mm: 80
  row_height_mm: 5.6
  max_y_mm: 260
  columns:
    - { field: label, width_mm: 85, align: left }
    - { field: ref_value, width_mm: 42, align: right }
    - { field: actual_value, width_mm: 42, align: right }
```

#### Fixed page — alleen tabel (landscape)
```yaml
# tenants/symitech/page_types/detail_weergave.yaml
name: detail_weergave
stationery: detail_landscape.pdf

table:
  data_bind: detail_items
  origin:
    x_mm: 20
    y_mm: 60
  row_height_mm: 5.6
  max_y_mm: 170
  columns:
    - { field: code, width_mm: 30, align: left }
    - { field: description, width_mm: 120, align: left }
    - { field: status, width_mm: 25, align: center }
    - { field: remark, width_mm: 60, align: left }
    - { field: cost, width_mm: 30, align: right, format: currency_nl }
```

#### Flow page — content frame voor flowables
```yaml
# tenants/3bm_cooperatie/page_types/inhoud.yaml
name: inhoud
stationery: standaard.pdf

content_frame:
  x_mm: 20
  y_mm: 25
  width_mm: 175
  height_mm: 247
```

#### Special page — leeg (alleen stationery)
```yaml
# tenants/symitech/page_types/achterblad.yaml
name: achterblad
stationery: achterblad.pdf
```

### 4.3 Brand (ongewijzigd, werkt al)
```yaml
# tenants/symitech/brand.yaml
tenant: symitech
name: "Symitech Milieutechniek"
colors:
  primary: "#006FAB"
  secondary: "#94571E"
  text: "#000000"
fonts:
  heading: "Helvetica-Bold"
  body: "Helvetica"
# ...
```

---

## 5. Engine design

### 5.1 Hoofdloop (pseudo-code)

```python
class ReportEngine:
    def build(self, template_path, data, brand, output_path):
        template = load_template(template_path)
        brand = load_brand(brand)
        stationery = StationeryRenderer(brand.stationery_dir)
        
        canvas = Canvas(output_path)
        
        for page_def in template.pages:
            page_type = load_page_type(page_def.page_type)
            
            if page_def.type == "special":
                self._render_special(canvas, page_def, page_type, data, brand)
                
            elif page_def.type == "toc":
                self._render_toc(canvas, page_def, page_type, data, brand)
                
            elif page_def.type == "flow":
                self._render_flow(canvas, page_def, page_type, data, brand)
                
            elif page_def.type == "fixed":
                self._render_fixed(canvas, page_def, page_type, data, brand)
        
        canvas.save()
```

### 5.2 Special renderer
```python
def _render_special(self, canvas, page_def, page_type, data, brand):
    pagesize = self._get_pagesize(page_def.orientation)
    canvas.setPageSize(pagesize)
    
    # 1. Stationery achtergrond
    self._draw_stationery(canvas, page_type.stationery, pagesize)
    
    # 2. Text zones invullen
    self._fill_text_zones(canvas, page_type.text_zones, data, brand)
    
    canvas.showPage()
```

### 5.3 Fixed renderer (met auto-paginering)
```python
def _render_fixed(self, canvas, page_def, page_type, data, brand):
    pagesize = self._get_pagesize(page_def.orientation)
    
    if page_type.table and page_def.repeat == "auto":
        # Haal alle tabeldata op
        table_data = resolve_data_bind(data, page_type.table.data_bind)
        
        # Pagineer over meerdere pagina's
        for chunk in self._paginate_rows(table_data, page_type.table):
            canvas.setPageSize(pagesize)
            self._draw_stationery(canvas, page_type.stationery, pagesize)
            self._fill_text_zones(canvas, page_type.text_zones, data, brand)
            self._draw_table(canvas, page_type.table, chunk)
            canvas.showPage()
    else:
        # Enkele pagina
        canvas.setPageSize(pagesize)
        self._draw_stationery(canvas, page_type.stationery, pagesize)
        self._fill_text_zones(canvas, page_type.text_zones, data, brand)
        if page_type.table:
            table_data = resolve_data_bind(data, page_type.table.data_bind)
            self._draw_table(canvas, page_type.table, table_data)
        canvas.showPage()
```

### 5.4 Flow renderer (bestaande ReportLab logica)
```python
def _render_flow(self, canvas, page_def, page_type, data, brand):
    # Delegeer naar ReportLab's BaseDocTemplate/flowable engine
    # Dit is grotendeels de BESTAANDE engine.py logica:
    # - Maak PageTemplate met content_frame uit page_type
    # - Registreer stationery als onPage callback
    # - Bouw flowables uit JSON sections/content blocks
    # - ReportLab paginateert automatisch
    pass
```

### 5.5 Tabel renderer (nieuw, simpel)
```python
def _draw_table(self, canvas, table_config, rows):
    """Teken een transparante tabel met vaste kolommen op canvas."""
    x_origin = table_config.origin.x_mm * MM_TO_PT
    y_start = table_config.origin.y_mm * MM_TO_PT  # top-down
    row_h = table_config.row_height_mm * MM_TO_PT
    
    y = y_start
    for row in rows:
        x = x_origin
        for col in table_config.columns:
            value = format_value(row.get(col.field, ""), col.format)
            col_w = col.width_mm * MM_TO_PT
            
            if col.align == "right":
                canvas.drawRightString(x + col_w, y, value)
            elif col.align == "center":
                canvas.drawCentredString(x + col_w / 2, y, value)
            else:
                canvas.drawString(x, y, value)
            
            x += col_w
        y += row_h
```

### 5.6 Text zone renderer (bestaand, uitbreiden)
```python
def _fill_text_zones(self, canvas, text_zones, data, brand):
    """Vul text zones in met data uit JSON."""
    for zone in text_zones:
        value = resolve_data_bind(data, zone.bind)
        if not value:
            continue
        
        font = brand.resolve_font(zone.font)
        color = brand.resolve_color(zone.color)
        
        canvas.setFont(font, zone.size)
        canvas.setFillColor(color)
        
        x = zone.x_mm * MM_TO_PT
        y = page_height - zone.y_mm * MM_TO_PT  # top-down → bottom-up
        
        if zone.align == "right":
            canvas.drawRightString(x, y, str(value))
        elif zone.align == "center":
            canvas.drawCentredString(x, y, str(value))
        else:
            canvas.drawString(x, y, str(value))
```

---

## 6. Data binding

Text zones en tabellen verwijzen naar data via een dot-notatie `bind` pad:

```yaml
bind: client.name          → data["client"]["name"]
bind: meta.datum           → data["meta"]["datum"]
bind: location.name        → data["location"]["name"]
bind: project              → data["project"]
```

Tabel data_bind verwijst naar een array in de JSON:

```yaml
data_bind: bic_sections    → data["bic_sections"]  (list of dicts)
data_bind: detail_items    → data["detail_items"]   (list of dicts)
```

Resolver:
```python
def resolve_data_bind(data: dict, path: str):
    """Resolve dot-notatie pad naar waarde in data dict."""
    parts = path.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current
```

---

## 7. Wat wordt VERWIJDERD

### Uit src/bm_reports/ (engine package)
- `modules/symitech/` — volledig (4 Python modules + __init__.py)
- `modules/yaml_module.py` — niet meer nodig voor fixed pages
- `modules/base.py` — ContentModule base class niet meer nodig voor fixed
- `assets/templates/symitech_*.yaml` — verplaatst naar tenant dir
- `assets/brands/symitech/` — verplaatst naar tenant dir
- `core/special_pages.py` — vervangen door stationery + text zones
- `reports/` — report subclasses niet meer nodig

### Behouden (nodig voor flow mode / 3BM)
- `modules/__init__.py` — ModuleRegistry (voor flow mode blocks)
- `modules/yaml_module.py` — mogelijk nog nodig als flow blocks YAML-driven worden
- `components/` — TableBlock, CalculationBlock etc. (voor flow mode)
- `core/engine.py` — herschreven met drie modes
- `core/stationery.py` — ongewijzigd, werkt
- `core/brand.py` — ongewijzigd, werkt
- `core/page_templates.py` — vereenvoudigd voor flow mode
- `core/styles.py` — voor flow mode paragraphs
- `core/toc.py` — voor flow mode TOC
- `core/fonts.py` — ongewijzigd

---

## 8. Implementatieplan

### Fase 1: Engine refactor — fixed + special mode
1. Dataclasses voor TemplateConfig, PageDef, PageType, TableConfig, TextZone
2. Template loader: lees template YAML → resolve page_type YAML's
3. `_render_special()` — stationery + text zones
4. `_render_fixed()` — stationery + text zones + tabel met auto-paginering
5. Simpele tabel renderer (transparant, vaste kolommen, direct op canvas)
6. Text zone renderer (resolve bind, draw op x,y)

### Fase 2: Symitech stationery PDFs
1. Extract per pagina-type een stationery PDF uit referentie-PDF
   - Optie A: Referentie-PDF splitsen, dynamische tekst verwijderen
   - Optie B: Vanuit bron opnieuw exporteren zonder data
2. Test: stationery + text zones + tabel = visueel identiek aan referentie

### Fase 3: Flow mode integratie
1. `_render_flow()` — wrapper rond bestaande ReportLab engine
2. page_type.content_frame → ReportLab Frame
3. page_type.stationery → onPage callback
4. Bestaande 3BM rapporten werken ongewijzigd

### Fase 4: Cleanup
1. Verwijder `src/bm_reports/modules/symitech/`
2. Verwijder `src/bm_reports/assets/templates/symitech_*.yaml`
3. Verplaats 3BM templates naar tenant dir
4. Update tests + CI

---

## 9. Risico's

| Risico | Mitigatie |
|--------|-----------|
| Stationery PDFs extraheren is lastig | Optie B: vanuit bron opnieuw maken, of handmatig in InDesign/Illustrator |
| Flow mode regressie bij 3BM | Flow mode = grotendeels bestaande code, minimale wijziging |
| Tabel paginering edge cases | Unit tests met 0, 1, exact-fit, en overflow scenario's |
| ReportLab canvas vs DocTemplate mixing | Special/fixed = pure canvas, flow = DocTemplate. Niet mixen in één render pass |

---

## 10. Open vraag: mixed canvas + DocTemplate

Special en fixed modes gebruiken directe canvas operaties.
Flow mode gebruikt ReportLab's DocTemplate met flowables.

Twee opties:
A. **Twee-pass**: Eerst flow-pagina's via DocTemplate → temp PDF, 
   dan merge met special/fixed pagina's via PyMuPDF
B. **Canvas-only**: Ook flow mode direct op canvas tekenen 
   (eigen flowable layout engine)
C. **DocTemplate-only**: Alles via DocTemplate, special/fixed als 
   PageTemplates met onPage callbacks die alles tekenen

Aanbeveling: **Optie C** — DocTemplate is al bewezen voor 3BM.
Special/fixed pagina's worden PageTemplates waarbij de onPage callback
de stationery + text zones + tabel tekent. De "content" is een
minimale Spacer (trigger). Dit is hoe het NU al werkt voor cover/backcover.

Dit vermijdt PDF merging en houdt één output pipeline.
