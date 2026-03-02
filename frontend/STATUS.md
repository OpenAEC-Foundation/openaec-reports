# Frontend Status — Report Generator UI

> Laatst bijgewerkt: 2026-02-20

## Deployment

| Component | URL | Status |
|-----------|-----|--------|
| **Productie** | https://report.3bm.co.nl/ | ⏳ Build klaar, upload pending |
| **Backend API** | https://report.3bm.co.nl/api/* | ✅ Live |
| **Lokaal dev** | http://localhost:5173 → http://localhost:8000 | ✅ |

### Deploy stappen (morgen)
1. `npm run build` (met `.env.production` → `VITE_API_URL=https://report.3bm.co.nl`)
2. Upload `dist/` naar server: `/opt/3bm/openaec-reports-ui/dist/`
3. Caddy serveert static files automatisch

## Architectuur

```
src/
├── components/
│   ├── blocks/        # 10 block editors + RichTextEditor (Tiptap)
│   ├── editor/        # BlockEditor (met ErrorBoundary), BlockToolbox, AppendixEditor
│   ├── forms/         # MetadataTabs, CoverForm, ColofonForm, OptionsPanel, TemplateSelector
│   ├── layout/        # AppShell (met ErrorBoundary), Sidebar, MainPanel, ShortcutHelp, ValidationBanner
│   └── shared/        # ErrorBoundary, BlockIcons
├── services/
│   └── api.ts         # Backend API client (VITE_API_URL env var)
├── stores/
│   ├── reportStore.ts # Zustand — rapport state (secties, metadata, bijlagen)
│   ├── apiStore.ts    # Zustand — API state (preview, generation, templates, brands)
│   └── __tests__/     # Store unit tests (19 tests)
├── test/
│   └── setup.ts       # Vitest setup (@testing-library/jest-dom)
├── types/
│   └── report.ts      # TypeScript types (Report, Section, Block, Cover, Colofon, etc.)
└── utils/
    ├── conversion.ts  # Store → API JSON conversie
    ├── defaults.ts    # Default block waarden
    ├── idGenerator.ts # Unieke ID generator
    └── __tests__/     # Conversion round-trip tests (6 tests)
```

## Tech Stack

- **React 18** + **TypeScript**
- **Vite** — bundler
- **Zustand** — state management
- **Tailwind CSS** — styling (brand config + CSS custom properties)
- **Tiptap** — rich text editor (paragraph blocks)
- **dnd-kit** — drag & drop
- **Vitest** + **React Testing Library** — tests
- Backend API: `import.meta.env.VITE_API_URL` (default: `http://localhost:8000`)

## Fasen — Afgerond

| Fase | Wat | Status |
|------|-----|--------|
| **1** | Project setup, Zustand store, TypeScript types, drag & drop | ✅ |
| **2** | Sidebar met secties, block toolbox, section CRUD | ✅ |
| **3** | Block editors: Paragraph, Calculation, Check, Table, Image, Spacer, PageBreak | ✅ |
| **3+** | MapEditor (PDOK layers, lat/lon, radius) | ✅ |
| **4** | Metadata forms: MetadataTabs, CoverForm, ColofonForm, OptionsPanel, TemplateSelector | ✅ |
| **4fix** | Bugfixes: section reordering, block deletion, form state sync | ✅ |
| **5** | API integratie: preview, generate, download, template/brand loading, validation | ✅ |
| **6** | Bijlagen: AppendixEditor, appendix CRUD, drag & drop reorder | ✅ |
| **7** | UX: JSON import/export, split view, undo/redo, auto-save, live preview, shortcuts | ✅ |
| **P5** | Rich text: Tiptap WYSIWYG editor in ParagraphEditor | ✅ |
| **P6** | Visual polish: 3BM branding, SVG iconen, inklapbare secties, floating toasts | ✅ |
| **P7** | Tech debt: Vitest tests, ErrorBoundary, env variables | ✅ |
| **P8** | Brand config: huisstijl als data, CSS custom properties, generieke Tailwind classes | ✅ |
| **F-FINAL** | renderer_v2 alignment: bullet_list, heading_2, colofon, content_sections, API v2 | ✅ |

## Componenten — Detail

### Block Editors (`components/blocks/`)

| Component | Props | Features |
|-----------|-------|----------|
| `ParagraphEditor` | text, style | Tiptap WYSIWYG (B/I/U/Sub/Sup/Lists), style selector |
| `CalculationEditor` | title, formula, substitution, result, unit, reference | 6 velden, alle optioneel behalve title |
| `CheckEditor` | description, required_value, calculated_value, unity_check, limit, result, reference | Auto UC berekening |
| `TableEditor` | title, headers, rows, column_widths, style | Dynamic rows/columns, striped/minimal toggle |
| `ImageEditor` | src, caption, width_mm, alignment | File upload → base64, preview thumbnail |
| `MapEditor` | center.lat/lon, radius_m, layers, caption, width_mm, height_mm | PDOK layer checkboxes |
| `SpacerEditor` | height_mm | Slider 5-50mm |
| `PageBreakEditor` | — | Display only, no config |
| `BulletListEditor` | items | Dynamic input list, Enter/Backspace shortcuts |
| `Heading2Editor` | number, title | Inline number + titel velden |

### Forms (`components/forms/`)

| Component | Functie |
|-----------|---------|
| `MetadataTabs` | Tab container: Metadata / Cover / Colofon / Opties |
| `MetadataForm` | project, project_number, client, author, report_type, date, version, status |
| `CoverForm` | subtitle, image upload |
| `ColofonForm` | Opdrachtgever (contact, naam, adres), Adviseur (bedrijf, naam), Document (normen, kenmerk, fase, status), revisiehistorie, disclaimer |
| `OptionsPanel` | TOC enable/title/depth, backcover enable, format (A4/A3), orientation |
| `TemplateSelector` | Dropdown met templates van API, laadt scaffold |

### Layout (`components/layout/`)

| Component | Functie |
|-----------|---------|
| `AppShell` | Root layout, keyboard shortcuts handler |
| `Sidebar` | Sections list, drag & drop reorder, block toolbox per section |
| `MainPanel` | Block editors, metadata tabs, PDF preview, JSON view |
| `ShortcutHelp` | Keyboard shortcuts dialog (Ctrl+?) |
| `ValidationBanner` | Toon API validatie errors |

### Stores

| Store | Slices |
|-------|--------|
| `reportStore` | sections, metadata, cover, colofon, toc, backcover, appendices, activeSection, activeBlock |
| `apiStore` | previewUrl, isGenerating, templates, brands, selectedTemplate, selectedBrand, validationErrors |

## API Contract

Frontend communiceert met backend via:

```
GET  /api/health              → { status, version }
GET  /api/templates           → { templates: [...] }
GET  /api/brands              → { brands: [...] }
GET  /api/stationery          → { brands: [...] }
GET  /api/templates/{n}/scaffold → { template, project, sections, cover, ... }
POST /api/validate            → { valid, errors }
POST /api/generate/v2         → application/pdf (binary)
POST /api/upload              → { path: string }
```

Conversie: `reportStore` state → API JSON via `utils/conversion.ts`
