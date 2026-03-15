# PLAN — Rust Implementation (openaec-layout + openaec-core)

> Status: MVP COMPLEET
> Deadline: dinsdag 17 maart 2026
> Laatst bijgewerkt: 2026-03-15

---

## Doel

1. **openaec-layout** — Eigen Rust "ReportLab" library (herbruikbaar)
2. **openaec-core uitbreiden** — Python libs nabouwen in Rust
3. **openaec-server** — Axum API met dezelfde endpoints
4. **Werkende PDF output** — JSON in → PDF uit, zelfde schema

---

## Wat al klaar is (Phase 0) ✅

| Module | Lines | Tests |
|--------|-------|-------|
| `schema.rs` — Alle JSON block types | 1,084 | 30 |
| `brand.rs` — Brand YAML loading | 601 | 8 |
| `tenant.rs` — Multi-tenant asset paden | 255 | 5 |
| `font_manager.rs` — Font discovery + fallback | 315 | 9 |
| **Totaal** | **2,255** | **40** |

---

## Phase 1 — openaec-layout (eigen ReportLab)

Nieuwe crate: `crates/openaec-layout/`

Fundament crates: `pdf-writer`, `ab_glyph`, `image`, `fontdb`, `ttf-parser`

### 1.1 — Basis types + Font registry

**Bestand:** `src/lib.rs`, `src/types.rs`, `src/fonts.rs`

```rust
// types.rs
pub struct Pt(pub f32);          // Points (1/72 inch)
pub struct Mm(pub f32);          // Millimeters
impl From<Mm> for Pt { ... }    // mm * 2.8346 = pt

pub struct Size { width: Pt, height: Pt }
pub struct Rect { x: Pt, y: Pt, width: Pt, height: Pt }
pub struct Color { r: u8, g: u8, b: u8, a: u8 }

pub const A4: Size = Size { width: Pt(595.28), height: Pt(841.89) };
pub const A3: Size = Size { width: Pt(841.89), height: Pt(1190.55) };
```

```rust
// fonts.rs
pub struct FontRegistry {
    db: fontdb::Database,
    registered: HashMap<String, FontId>,
}

impl FontRegistry {
    pub fn new() -> Self;
    pub fn register_ttf(&mut self, name: &str, path: &Path) -> Result<FontId>;
    pub fn register_dir(&mut self, dir: &Path) -> usize;
    pub fn get(&self, name: &str) -> Option<FontId>;
    pub fn font_data(&self, id: FontId) -> &[u8];  // Voor PDF embedding
}
```

### 1.2 — Canvas

**Bestand:** `src/canvas.rs`

Low-level tekenen op een PDF pagina. Bouwt intern een `Vec<DrawOp>` op.

```rust
pub struct Canvas {
    ops: Vec<DrawOp>,
    page_size: Size,
    font_registry: Arc<FontRegistry>,
}

impl Canvas {
    pub fn new(page_size: Size, fonts: Arc<FontRegistry>) -> Self;

    // Tekst
    pub fn set_font(&mut self, name: &str, size: Pt);
    pub fn draw_string(&mut self, x: Pt, y: Pt, text: &str);
    pub fn draw_right_string(&mut self, x: Pt, y: Pt, text: &str);
    pub fn draw_centered_string(&mut self, x: Pt, y: Pt, text: &str);

    // Vormen
    pub fn set_fill_color(&mut self, color: Color);
    pub fn set_stroke_color(&mut self, color: Color);
    pub fn set_line_width(&mut self, width: Pt);
    pub fn rect(&mut self, x: Pt, y: Pt, w: Pt, h: Pt, fill: bool, stroke: bool);
    pub fn line(&mut self, x1: Pt, y1: Pt, x2: Pt, y2: Pt);

    // Images
    pub fn draw_image(&mut self, path: &Path, x: Pt, y: Pt, w: Pt, h: Pt);
    pub fn draw_image_bytes(&mut self, data: &[u8], x: Pt, y: Pt, w: Pt, h: Pt);

    // Text metrics
    pub fn string_width(&self, text: &str, font: &str, size: Pt) -> Pt;

    // State
    pub fn save_state(&mut self);
    pub fn restore_state(&mut self);
}
```

### 1.3 — Flowable trait

**Bestand:** `src/flowable.rs`

```rust
pub trait Flowable: std::fmt::Debug {
    /// Bereken grootte gegeven beschikbare ruimte.
    fn wrap(&mut self, available_width: Pt, available_height: Pt) -> Size;

    /// Teken op canvas op positie (x, y).
    fn draw(&self, canvas: &mut Canvas, x: Pt, y: Pt);

    /// Splits over pagina-grens. Returns (past_op_pagina, rest).
    fn split(&self, available_width: Pt, available_height: Pt) -> SplitResult {
        SplitResult::CannotSplit  // default: niet splitsbaar
    }
}

pub enum SplitResult {
    /// Past volledig
    Fits,
    /// Splits in twee delen
    Split(Box<dyn Flowable>, Box<dyn Flowable>),
    /// Kan niet gesplitst worden, naar volgende pagina
    CannotSplit,
}
```

### 1.4 — Simpele flowables: Spacer, PageBreak

**Bestand:** `src/spacer.rs`

```rust
pub struct Spacer { height: Pt }
pub struct PageBreak;

impl Flowable for Spacer { ... }  // wrap → (0, height), draw → noop
impl Flowable for PageBreak { ... }  // signaleert page break aan Frame
```

### 1.5 — Paragraph

**Bestand:** `src/paragraph.rs`

Gestylde tekst met word-wrapping. Ondersteunt:
- Bold, italic, bold-italic
- Inline `<b>`, `<i>` tags (subset van ReportLab XML)
- Word-wrap op beschikbare breedte
- Leading (regelafstand)

```rust
pub struct ParagraphStyle {
    pub font_name: String,
    pub font_size: Pt,
    pub leading: Pt,
    pub text_color: Color,
    pub alignment: Alignment,
    pub space_before: Pt,
    pub space_after: Pt,
    pub first_line_indent: Pt,
    pub left_indent: Pt,
    pub right_indent: Pt,
}

pub struct Paragraph {
    text: String,
    style: ParagraphStyle,
    // Cached na wrap():
    lines: Vec<TextLine>,
    wrapped_height: Pt,
}

impl Flowable for Paragraph { ... }
```

### 1.6 — Table

**Bestand:** `src/table.rs`

```rust
pub struct Table {
    data: Vec<Vec<CellContent>>,  // rijen × kolommen
    col_widths: Option<Vec<Pt>>,
    style: TableStyle,
    repeat_rows: usize,           // header herhaling bij split
}

pub enum CellContent {
    Text(String),
    Styled(Paragraph),
    Empty,
}

pub struct TableStyle {
    pub grid: Option<(Pt, Color)>,        // lijndikte + kleur
    pub row_backgrounds: Vec<Option<Color>>, // zebra-striping
    pub header_background: Option<Color>,
    pub padding: Pt,
}

impl Flowable for Table {
    fn split(...) -> SplitResult { ... }  // Split met header herhaling
}
```

### 1.7 — Image flowable

**Bestand:** `src/image.rs`

```rust
pub struct ImageFlowable {
    data: ImageData,
    width: Pt,
    height: Pt,
    alignment: Alignment,
    caption: Option<String>,
}

pub enum ImageData {
    Path(PathBuf),
    Bytes(Vec<u8>),
}

impl Flowable for ImageFlowable { ... }
```

### 1.8 — Frame

**Bestand:** `src/frame.rs`

Container die flowables top-to-bottom plaatst. Signaleert wanneer pagina vol is.

```rust
pub struct Frame {
    rect: Rect,               // positie + grootte op pagina
    padding: Padding,
}

impl Frame {
    pub fn new(rect: Rect) -> Self;

    /// Vul frame met flowables. Returns index van eerste flowable die niet paste.
    pub fn add_flowables(
        &self,
        flowables: &mut Vec<Box<dyn Flowable>>,
        canvas: &mut Canvas,
    ) -> FrameResult;
}

pub enum FrameResult {
    /// Alles paste
    Complete,
    /// Overflow: index van eerste niet-geplaatste flowable
    Overflow(usize),
}
```

### 1.9 — PageTemplate

**Bestand:** `src/page_template.rs`

```rust
pub trait PageCallback: Send + Sync {
    fn on_page(&self, canvas: &mut Canvas, page_num: usize, total_pages: usize);
}

pub struct PageTemplate {
    pub name: String,
    pub page_size: Size,
    pub frames: Vec<Frame>,
    pub on_page: Option<Box<dyn PageCallback>>,       // header/footer
    pub on_page_end: Option<Box<dyn PageCallback>>,
}
```

### 1.10 — DocTemplate (PDF assembly)

**Bestand:** `src/doc_template.rs`

```rust
pub struct DocTemplate {
    page_templates: Vec<PageTemplate>,
    font_registry: Arc<FontRegistry>,
}

impl DocTemplate {
    pub fn new(fonts: Arc<FontRegistry>) -> Self;
    pub fn add_page_template(&mut self, template: PageTemplate);

    /// Bouw PDF vanuit flowables.
    pub fn build(
        &self,
        flowables: Vec<Box<dyn Flowable>>,
        output: &Path,
    ) -> Result<(), LayoutError>;
}
```

### 1.11 — PDF writer backend

**Bestand:** `src/pdf_backend.rs`

Vertaalt `Canvas` draw ops naar `pdf-writer` calls. Handelt font embedding, image embedding, pagina's.

```rust
pub struct PdfBackend {
    font_registry: Arc<FontRegistry>,
}

impl PdfBackend {
    /// Canvas per pagina → PDF bytes
    pub fn render(&self, pages: Vec<Canvas>) -> Result<Vec<u8>>;
}
```

---

## Phase 2 — Python libs porten naar openaec-core

Uitbreiden van `crates/openaec-core/` met de data/logica laag.

### 2.1 — Schema sync: Spreadsheet block

Voeg `ContentBlock::Spreadsheet` variant toe (mist sinds Python #9).

### 2.2 — document.rs

Port van `core/document.py` — A4/A3 paginaformaten, marges, oriëntatie.

### 2.3 — styles.rs

Port van `core/styles.py` — FontConfig, font rollen (heading/body/mono), kleuren, paragraph styles.

### 2.4 — template_config.rs

Port van `core/template_config.py` — PageType, TextZone, ImageZone, LineZone, ContentFrame dataclasses.

### 2.5 — template_loader.rs

Port van `core/template_loader.py` — YAML template discovery, scaffold generatie, template merging.

### 2.6 — block_registry.rs

Port van `core/block_registry.py` — Block factory (`create_block()`), image source resolution (pad/URL/base64).

### 2.7 — data_transform.rs

Port van `core/data_transform.py` — JSON → flat dict transformatie voor template engine.

### 2.8 — stationery.rs

Port van `core/stationery.py` — Stationery PDF/PNG pad resolutie, lopdf merge.

### 2.9 — toc.rs

Port van `core/toc.py` — TOC data structuur, sectie nummering.

### 2.10 — kadaster.rs

Port van `data/kadaster.py` — RD↔WGS84 coordinaat transformatie, PDOK WMS URL builder.

### 2.11 — json_adapter.rs

Port van `data/json_adapter.py` — JSON schema validatie met `jsonschema` crate of custom.

### 2.12 — report_types.rs

Port van `reports/*.py` — StructuralReport, DaylightReport, BuildingCodeReport section builders.

---

## Phase 3 — Rendering pipeline (openaec-core → openaec-layout)

Verbind de data laag met de layout engine.

### 3.1 — block_renderers.rs

Vertaal ContentBlock → Flowable:
- `Paragraph` → `layout::Paragraph`
- `Calculation` → `layout::Table` (2-kolom)
- `Check` → custom flowable (icoon + tekst + UC bar)
- `Table` → `layout::Table`
- `Image` → `layout::ImageFlowable`
- `Spacer` → `layout::Spacer`
- `PageBreak` → `layout::PageBreak`
- `BulletList` → meerdere `layout::Paragraph` met bullet prefix
- `Heading2` → `layout::Paragraph` met heading style

### 3.2 — special_pages.rs

Port van `core/special_pages.py`:
- Cover page (canvas drawing)
- Colofon page (tabel met project/adviseur info)
- TOC page (genummerde lijst)
- Backcover page

### 3.3 — engine.rs

Hoofd-engine: `ReportData` → `Vec<Flowable>` → `DocTemplate.build()` → PDF.

```rust
pub fn generate(data: &ReportData, output: &Path) -> Result<()> {
    let tenant = TenantConfig::from_env();
    let brand = BrandLoader::new(&tenant).load(&data.brand)?;
    let fonts = setup_fonts(&tenant, &brand)?;
    let flowables = render_sections(&data.sections, &brand, &fonts)?;
    let doc = build_document(&data, &brand, &fonts, flowables)?;
    doc.build(output)?;
    Ok(())
}
```

---

## Phase 4 — Server + CLI

### 4.1 — CLI wiring

`openaec-cli`:
- `generate` — JSON → PDF
- `validate` — JSON schema check
- `serve` — Start Axum server

### 4.2 — Axum API server

`openaec-server` met endpoints:
- `GET /api/health`
- `GET /api/templates`
- `GET /api/templates/{name}/scaffold`
- `GET /api/brands`
- `POST /api/validate`
- `POST /api/generate`

Auth (JWT + API keys) en storage later — eerst PDF generatie werkend.

### 4.3 — Dockerfile

```dockerfile
FROM rust:1.85 AS builder
WORKDIR /app
COPY rust/ .
RUN cargo build --release -p openaec-server

FROM debian:bookworm-slim
COPY --from=builder /app/target/release/openaec-server /usr/local/bin/
EXPOSE 8001
CMD ["openaec-server"]
```

Deploy als `report-rs.3bm.co.nl` op poort 8001.

---

## Prioriteit voor dinsdag 17 maart

**Must have (MVP):**
- [ ] Phase 1.1–1.6: Layout engine basics (types, fonts, canvas, flowable, spacer, paragraph)
- [ ] Phase 1.8–1.10: Frame + PageTemplate + DocTemplate
- [ ] Phase 1.11: PDF writer backend
- [ ] Phase 2.1: Spreadsheet block sync
- [ ] Phase 3.1: Block renderers (paragraph, table, spacer, pagebreak)
- [ ] Phase 3.3: Engine (JSON → PDF)
- [ ] Phase 4.1: CLI generate commando

**Should have:**
- [ ] Phase 1.6: Table met splitting
- [ ] Phase 1.7: Image flowable
- [ ] Phase 3.2: Cover + colofon
- [ ] Phase 4.2: Axum API (health + generate)

**Nice to have:**
- [ ] Phase 2.10: Kadaster
- [ ] Phase 2.12: Report types
- [ ] Phase 4.3: Dockerfile + deploy
- [ ] Stationery PDF merge

---

## Verificatie

```bash
# Build
cd rust && cargo build

# Tests
cargo test

# Clippy
cargo clippy -- -D warnings

# Genereer test PDF
cargo run -p openaec-cli -- generate \
  --data ../schemas/example_structural.json \
  --output test_output.pdf

# Vergelijk met Python output
python -c "
import fitz
doc = fitz.open('test_output.pdf')
print(f'Pages: {len(doc)}')
for i, page in enumerate(doc):
    fonts = page.get_fonts()
    for f in fonts:
        print(f'Page {i}: {f[3]} (type={f[2]})')
"
```

---

## Risico's

- **Text layout:** Word-wrapping correct krijgen met proportionele fonts is fiddly
- **Table splitting:** Complexste deel van de layout engine
- **PDF compliance:** pdf-writer is low-level, moeten zelf font subsetting doen
- **Stationery merge:** lopdf kan fragiel zijn met complexe PDF's
- **Timeline:** 3 dagen is krap — focus op werkende PDF output, niet perfectie
