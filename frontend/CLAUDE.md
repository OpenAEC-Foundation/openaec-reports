# OpenAEC Report Editor — `openaec-reports-ui`

Web-based editor voor het samenstellen van professionele engineering rapporten. Produceert JSON conform `schemas/report.schema.json` — de backend library (`openaec-reports`) consumeert dit en genereert de PDF.

---

## Quick Start

```bash
npm install
npm run dev          # Dev server op http://localhost:5173
npm run build        # Productie build naar dist/
```

**Vereist:** Backend API op http://localhost:8000 (zie Report_generator)

---

## Context

Dit project is **Layer 3** van een drielaags platform, nu een **monorepo** (`openaec-reports`):

```
Layer 1: LIBRARY (openaec-reports)         ← ../src/openaec_reports/ (zelfde repo)
         Consumeert JSON → genereert PDF

Layer 2: API SERVER (openaec-reports-api)  ← ../src/openaec_reports/api.py
         POST JSON → ontvang PDF

Layer 3: FRONTEND (openaec-reports-ui)     ← DIT DIRECTORY (frontend/)
         Visuele editor → produceert JSON
```

**Kernprincipe:** De frontend produceert JSON, NIET PDF's. Het JSON schema is het contract. De frontend hoeft niets te weten over ReportLab, Python, of PDF rendering.

---

## Tech Stack

- **React 18** + **TypeScript**
- **Vite** — bundler
- **Zustand** — state management
- **Tailwind CSS** — styling
- **dnd-kit** — drag & drop
- Backend API: `http://localhost:8000`

---

## Status

Zie **`STATUS.md`** voor de volledige component-status en fasen.
Zie **`TODO.md`** voor openstaande taken en prioriteiten.

**Samenvatting:** Alle 7 fasen afgerond. Editor volledig werkend met API integratie, drag & drop, undo/redo, live preview.

---

## Architectuur

```
src/
├── components/
│   ├── blocks/        # 8 block editors (paragraph, calc, check, table, image, map, spacer, page_break)
│   ├── editor/        # BlockEditor, BlockToolbox, AppendixEditor
│   ├── forms/         # MetadataTabs, CoverForm, ColofonForm, OptionsPanel, TemplateSelector
│   └── layout/        # AppShell, Sidebar, MainPanel, ShortcutHelp, ValidationBanner
├── services/
│   └── api.ts         # Backend API client (localhost:8000)
├── stores/
│   ├── reportStore.ts # Zustand — rapport state (secties, metadata, bijlagen)
│   └── apiStore.ts    # Zustand — API state (preview, generation, templates, brands)
├── types/
│   └── report.ts      # TypeScript types (Report, Section, Block, Cover, Colofon, etc.)
└── utils/
    ├── conversion.ts  # Store → API JSON conversie
    ├── defaults.ts    # Default block waarden
    └── idGenerator.ts # Unieke ID generator
```

---

## Data Flow

```
User interactie
      |
Block component (React)
      |
Zustand store (reportStore)    <- Single source of truth
      |                |
JSON export       PDF preview
(.json file)      (via API → pdf.js)
```

---

## JSON Schema als Contract

Het bestand `schemas/report.schema.json` is **gekopieerd uit het library project** en is het single source of truth.

**REGELS:**
1. **NOOIT dit bestand wijzigen.** Wijzigingen gaan via het library project.
2. TypeScript types in `types/report.ts` worden gegenereerd/afgeleid uit dit schema.
3. Bij twijfel over een veld: kijk in het schema, niet in de frontend code.

### Content Block Types (uit schema)

| Type | Editor Component | Complexiteit |
|------|-----------------|--------------|
| `paragraph` | Rich text editor (bold, italic, sub, sup) | Medium |
| `calculation` | Formulier met 6 velden | Laag |
| `check` | Formulier met UC visualisatie | Medium |
| `table` | Spreadsheet-achtige grid editor | Hoog |
| `image` | Upload + preview + caption | Medium |
| `map` | Lat/lon picker + layer checkboxen | Hoog |
| `spacer` | Hoogte slider | Triviaal |
| `page_break` | Geen editor nodig (icoon only) | Triviaal |

---

## API Contract

Frontend communiceert met backend via:

```
GET  /api/health              → { status, version }
GET  /api/templates           → { templates: [...] }
GET  /api/brands              → { brands: [...] }
GET  /api/templates/{n}/scaffold → { template, project, sections, cover, ... }
POST /api/validate            → { valid, errors }
POST /api/generate            → application/pdf (binary)
```

Conversie: `reportStore` state → API JSON via `utils/conversion.ts`

---

## Conventies

1. **TypeScript strict mode** — geen `any` types
2. **Functionele components** met hooks, geen class components
3. **Tailwind** voor alle styling, geen CSS modules of styled-components
4. **Colocatie:** Block-specifieke logica bij de block component, niet in utils
5. **Naming:** PascalCase voor components, camelCase voor hooks/utils, kebab-case voor bestanden
6. **Tests:** Vitest + React Testing Library voor unit tests
7. **Schema first:** Types en validatie altijd afgeleid uit `report.schema.json`

---

## Relatie met Backend (Monorepo)

```
openaec-reports/                     <- Monorepo
├── schemas/
│   ├── report.schema.json          <- BRON — schema wordt hier beheerd
│   └── example_structural.json     <- Testdata
├── src/openaec_reports/                 <- Python library + API
├── frontend/                       <- DIT DIRECTORY
│   ├── schemas/
│   │   └── report.schema.json      <- KOPIE — niet wijzigen
│   └── src/                        <- React/TypeScript code
└── Dockerfile                      <- Multi-stage: node build + python runtime
```

---

## Notities

- De library ondersteunt `raw_flowable` blocks maar die zijn library-only (directe ReportLab class instanties). De frontend moet dit type negeren / niet aanbieden in de toolbox.
- Image sources kunnen pad, URL, of base64 zijn. De frontend stuurt base64 (file upload) of URL. Paden zijn alleen relevant voor library-direct gebruik.
- De `map` block vereist PDOK integratie in de library. De frontend hoeft alleen lat/lon + layers op te slaan.
- ReportLab XML markup in paragraph text (`<b>`, `<i>`, `<sub>`, `<sup>`) — de paragraph editor moet dit ondersteunen.
