# PROMPT F-FINAL: Frontend Afstemming op renderer_v2 Backend

## Context

Je werkt in `X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator_frontend`.

Er is een **werkende React/TypeScript frontend** (Fase 1-7 + P5-P7 afgerond) met:
- Zustand store, drag & drop, block editors, metadata forms, API client
- TypeScript types afgeleid uit `schemas/report.schema.json`
- Tech stack: React 18, Vite, Tailwind, Tiptap, dnd-kit, Zustand

Het probleem: de frontend produceert JSON conform het **oude** schema, maar de backend is herschreven naar **renderer_v2** die een ander JSON formaat verwacht. De JSON die de frontend exporteert verschilt op cruciale punten van wat de backend consumeert.

## Doel

Breng de frontend in lijn met het renderer_v2 JSON formaat zodat de volledige pipeline werkt:
**Frontend → JSON → POST /api/generate/v2 → PDF**

---

## STAP 1: TypeScript types uitbreiden

### 1a. Nieuwe block types toevoegen aan `src/types/report.ts`

De renderer_v2 backend ondersteunt block types die de frontend niet kent:

```typescript
// TOEVOEGEN aan report.ts:

export interface BulletListBlock {
  type: 'bullet_list';
  items: string[];
}

export interface Heading2Block {
  type: 'heading_2';
  number: string;    // bijv. "2.1"
  title: string;
}
```

Update de `ContentBlock` union:
```typescript
export type ContentBlock =
  | ParagraphBlock
  | CalculationBlock
  | CheckBlock
  | TableBlock
  | ImageBlock
  | MapBlock
  | SpacerBlock
  | PageBreakBlock
  | BulletListBlock     // NIEUW
  | Heading2Block       // NIEUW
  | RawFlowableBlock;
```

Update `EditableBlockType` om `raw_flowable` uit te sluiten maar de nieuwe types wel toe te voegen.

### 1b. Colofon type uitbreiden

De renderer_v2 verwacht specifieke colofon-velden, niet alleen `extra_fields`:

```typescript
export interface Colofon {
  enabled?: boolean;
  // Specifieke renderer_v2 velden:
  opdrachtgever_contact?: string;
  opdrachtgever_naam?: string;
  opdrachtgever_adres?: string;
  adviseur_bedrijf?: string;
  adviseur_naam?: string;
  normen?: string;
  documentgegevens?: string;
  datum?: string;
  fase?: string;
  status_colofon?: string;
  kenmerk?: string;
  // Legacy:
  extra_fields?: Record<string, string>;
  revision_history?: RevisionEntry[];
  disclaimer?: string;
}
```

### 1c. Appendix type uitbreiden

De renderer_v2 verwacht een ander formaat:

```typescript
export interface Appendix {
  number: number;
  label?: string;       // bijv. "Bijlage 1"
  title: string;        // bijv. "Sonderingsgegevens en\nfunderingsadvies"
  content_sections?: AppendixSection[];  // NIEUW: sub-secties
  content?: ContentBlock[];              // legacy flat content
}

export interface AppendixSection {
  number: string;
  title: string;
  level: number;
  content: ContentBlock[];
}
```

### 1d. Report root velden

Voeg `report_type` toe:
```typescript
export interface ReportDefinition {
  // ... bestaande velden ...
  report_type?: string;  // NIEUW: "BBL-toetsingsrapportage", "Constructief adviesrapport", etc.
}
```

### 1e. Section nummering

Voeg `number` toe aan Section:
```typescript
export interface Section {
  number?: string;  // NIEUW: "1", "2", etc. — wordt automatisch berekend bij export
  title: string;
  level?: number;
  content?: ContentBlock[];
  page_break_before?: boolean;
}
```

---

## STAP 2: Block editors toevoegen

### 2a. BulletListEditor — `src/components/blocks/BulletListEditor.tsx`

- Lijst van string items
- Elke bullet is een input field
- "+" knop om bullet toe te voegen
- "×" knop per bullet om te verwijderen
- Drag & drop reorder van bullets
- Minimaal 1 bullet altijd aanwezig

```tsx
interface BulletListEditorProps {
  items: string[];
  onChange: (items: string[]) => void;
}
```

### 2b. Heading2Editor — `src/components/blocks/Heading2Editor.tsx`

- Twee velden: nummer (kort text input) + titel (text input)
- Inline layout: nummer links, titel rechts
- Nummer wordt automatisch gesuggereerd op basis van parent section nummer

```tsx
interface Heading2EditorProps {
  number: string;
  title: string;
  onChange: (updates: { number?: string; title?: string }) => void;
}
```

### 2c. Block toolbox updaten

Voeg `bullet_list` en `heading_2` toe aan de block toolbox in `src/components/editor/BlockToolbox.tsx`:
- Bullet List icoon: een lijst-icoon
- Heading 2 icoon: "H2" tekst

### 2d. Defaults updaten

In `src/utils/defaults.ts`, voeg defaults toe:
```typescript
case 'bullet_list':
  return { id: generateId(), type: 'bullet_list', items: [''] };
case 'heading_2':
  return { id: generateId(), type: 'heading_2', number: '', title: '' };
```

---

## STAP 3: Colofon form updaten

### 3a. ColofonForm herschrijven — `src/components/forms/ColofonForm.tsx`

Vervang de generieke `extra_fields` editor met specifieke velden die matchen met de renderer_v2 colofon layout:

**Sectie "Opdrachtgever":**
- Contact persoon (`opdrachtgever_contact`)
- Bedrijfsnaam (`opdrachtgever_naam`)
- Adres (`opdrachtgever_adres`) — textarea (multiline)

**Sectie "Adviseur":**
- Bedrijf (`adviseur_bedrijf`) — default "3BM Coöperatie"
- Uitvoerend adviseur (`adviseur_naam`)

**Sectie "Document":**
- Normen (`normen`) — bijv. "Eurocode, NEN-EN 1990"
- Documentgegevens (`documentgegevens`) — bijv. "Constructief advies, pg 1-14"
- Datum (`datum`) — date picker, default vandaag
- Fase (`fase`) — dropdown: Haalbaarheid / Voorlopig Ontwerp / Definitief Ontwerp / Uitvoering
- Status (`status_colofon`) — dropdown: Concept / Definitief / Revisie
- Kenmerk (`kenmerk`) — text, bijv. "2801-CA-01"

**Sectie "Overig":**
- Disclaimer — textarea met default tekst
- Revisiegeschiedenis — behoud bestaande dynamic rows

### 3b. MetadataForm updaten

Voeg `report_type` veld toe:
- Label: "Rapporttype"
- Input: text field met suggesties (dropdown/combobox)
- Suggesties: "BBL-toetsingsrapportage", "Constructief adviesrapport", "Daglichttoetreding", "Ventilatieberekening", "Geluidsberekening"
- Waarde wordt ook gebruikt als cover subtitle default

---

## STAP 4: Conversie layer updaten

### 4a. `src/utils/conversion.ts` — toReportDefinition()

De export functie moet JSON produceren die **exact** matcht met het renderer_v2 formaat. Cruciale wijzigingen:

**Section nummering:**
```typescript
function toSchemaSection(section: EditorSection, index: number): Section {
  return {
    number: String(index + 1),  // Auto-nummering
    title: section.title,
    level: section.level,
    content: section.content.map(toSchemaBlock),
  };
}
```

**Heading_2 nummering in content:**
De renderer_v2 verwacht `heading_2` blocks als inline content blocks, NIET als aparte secties. De conversie moet heading_2 blocks met correcte nummering exporteren.

**Appendix conversie:**
```typescript
function toSchemaAppendix(appendix: EditorAppendix): Appendix {
  return {
    number: appendix.number,
    label: `Bijlage ${appendix.number}`,
    title: appendix.title,
    content_sections: convertToContentSections(appendix.content),
  };
}
```

**Colofon conversie:**
De nieuwe specifieke colofon-velden moeten direct mee in de export JSON, NIET in `extra_fields`.

### 4b. `src/utils/conversion.ts` — toEditorReport()

De import functie moet renderer_v2 JSON correct kunnen inlezen:
- `bullet_list` blocks → BulletListBlock
- `heading_2` blocks → Heading2Block
- Specifieke colofon velden → Colofon interface
- `content_sections` in appendices → flat content met heading blocks
- `report_type` → store

---

## STAP 5: API client updaten

### 5a. `src/services/api.ts`

Update het `generate` endpoint:
```typescript
generate: async (data: ReportDefinition): Promise<Blob> => {
  const res = await fetch(`${API_BASE}/api/generate/v2`, {  // /v2 endpoint!
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  // ...
},
```

Voeg nieuw endpoint toe:
```typescript
stationery: () =>
  apiFetch<{ brands: { name: string; slug: string; complete: boolean }[] }>('/api/stationery'),

upload: async (file: File): Promise<{ path: string }> => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/api/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Upload failed');
  return res.json();
},
```

### 5b. ImageEditor updaten

De huidige ImageEditor stuurt base64. Voeg optie toe om via `/api/upload` te uploaden en het pad te gebruiken — efficiënter voor grote bestanden.

---

## STAP 6: Build & Test

### 6a. TypeScript compilatie
```bash
npx tsc --noEmit
```
Alle type errors moeten opgelost zijn.

### 6b. Vitest tests updaten
Update bestaande tests in `src/stores/__tests__/` en `src/utils/__tests__/`:
- Test bullet_list en heading_2 block creation
- Test conversie round-trip met nieuwe block types
- Test colofon specifieke velden conversie

### 6c. Build
```bash
npm run build
```
Moet succesvol builden naar `dist/`.

### 6d. Import test
Na build: importeer `tests/test_data/sample_report.json` (uit het backend project) via de JSON import functie en verifieer dat alle blocks correct worden weergegeven.

---

## Referentie: renderer_v2 JSON formaat

Dit is het **exacte** JSON formaat dat de backend verwacht (uit `tests/test_data/sample_report.json`):

```json
{
  "template": "3bm_cooperatie",
  "format": "A4",
  "project": "Projectnaam",
  "project_number": "2801",
  "client": "Opdrachtgever B.V.",
  "author": "3BM Coöperatie",
  "report_type": "Constructief adviesrapport",
  "date": "20-02-2026",
  "version": "1.0",
  "status": "Concept",
  "cover": {
    "subtitle": "Constructief adviesrapport",
    "image": null
  },
  "colofon": {
    "enabled": true,
    "opdrachtgever_contact": "Dhr. P. van der Berg",
    "opdrachtgever_naam": "Bedrijfsnaam B.V.",
    "opdrachtgever_adres": "Straat 12,\n1234 AB Stad",
    "adviseur_bedrijf": "3BM Coöperatie",
    "adviseur_naam": "Ir. S. de Vries",
    "normen": "Eurocode, NEN-EN 1990",
    "documentgegevens": "Constructief advies, pg 1-14",
    "fase": "Definitief Ontwerp",
    "kenmerk": "2801-CA-01"
  },
  "toc": { "enabled": true, "title": "Inhoud", "max_depth": 2 },
  "sections": [
    {
      "number": "1",
      "title": "Inleiding",
      "level": 1,
      "content": [
        { "type": "paragraph", "text": "Tekst hier..." },
        { "type": "bullet_list", "items": ["Item 1", "Item 2"] },
        { "type": "heading_2", "number": "1.1", "title": "Subtitel" }
      ]
    }
  ],
  "appendices": [
    {
      "number": 1,
      "label": "Bijlage 1",
      "title": "Sonderingsgegevens",
      "content_sections": [
        {
          "number": "B1",
          "title": "Sonderingsgegevens",
          "level": 1,
          "content": [
            { "type": "paragraph", "text": "..." }
          ]
        }
      ]
    }
  ],
  "backcover": { "enabled": true }
}
```

---

## NIET doen

- Raak de backend NIET aan (apart project)
- Verwijder GEEN bestaande functionaliteit
- Herschrijf NIET de Zustand store architectuur — voeg alleen toe
- Wijzig NIET de drag & drop logica (dnd-kit) — die werkt
- Maak GEEN nieuwe dependencies behalve als absoluut nodig
- Raak de Tiptap rich text editor NIET aan — die werkt

## Volgorde van uitvoering

1. Update `src/types/report.ts` met nieuwe types
2. Update `src/utils/defaults.ts` met defaults voor nieuwe types  
3. Maak `BulletListEditor.tsx` en `Heading2Editor.tsx`
4. Update `BlockToolbox` met nieuwe block types
5. Update `BlockEditor` dispatch voor nieuwe types
6. Herschrijf `ColofonForm` met specifieke velden
7. Update `MetadataForm` met `report_type`
8. Update `src/utils/conversion.ts` (import + export)
9. Update `src/services/api.ts` endpoints
10. Update/schrijf tests
11. Build en verifieer

## Verificatie

Na afloop moet dit werken:
```bash
cd X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator_frontend
npx tsc --noEmit                    # 0 errors
npm run test                         # Alle tests groen
npm run build                        # Succesvolle build
npm run dev                          # Start op localhost:5173
```

En in de UI:
- JSON import van `sample_report.json` → alle blocks inclusief bullet_list en heading_2 zichtbaar
- Colofon form toont specifieke velden (opdrachtgever, adviseur, etc.)
- JSON export produceert formaat dat de backend accepteert
- Nieuwe bullet_list en heading_2 blocks aanmaken via toolbox werkt
