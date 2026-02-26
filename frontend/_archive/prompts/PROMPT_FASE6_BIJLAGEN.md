# Fase 6: Bijlagen (Appendices) in de Frontend Editor

## Context

Je werkt in het `Report_generator_frontend` project (Vite + React + TypeScript + Tailwind + Zustand).
De editor heeft al secties met drag & drop, block editors, metadata forms, en API integratie (PDF genereren + preview).

De backend (apart project) krijgt in Fase B ondersteuning voor bijlagen:
- `appendices[]` array op het root ReportDefinition object
- Elke bijlage heeft: `title`, `number` (auto-increment), en optioneel `content[]` (zelfde ContentBlock types als secties)
- De backend rendert per bijlage een turquoise divider-pagina gevolgd door eventuele content

Nu moet de frontend bijlagen kunnen aanmaken, bewerken, herordenen en meesturen naar de API.

## Referentiebestanden — lees EERST

- `src/types/report.ts` — Alle TypeScript types (ReportDefinition, EditorReport, etc.)
- `src/stores/reportStore.ts` — Zustand store met alle actions
- `src/utils/defaults.ts` — Default factories voor report, section, block
- `src/utils/conversion.ts` — Conversie editor ↔ schema (toEditorReport / toReportDefinition)
- `src/components/layout/Sidebar.tsx` — Sidebar met sectie-navigatie + drag & drop
- `src/components/layout/MainPanel.tsx` — Hoofd editor panel met block editing
- `src/components/editor/BlockEditor.tsx` — Block type dispatcher
- `src/components/editor/BlockToolbox.tsx` — "+ Block toevoegen" knoppen

---

## Stap 1: Types uitbreiden — `src/types/report.ts`

### Schema types (zonder IDs)

Voeg toe na `BackcoverConfig`:

```typescript
// ---------- Appendix ----------

export interface Appendix {
  title: string;
  number?: number;
  content?: ContentBlock[];
}
```

### ReportDefinition uitbreiden

Voeg `appendices` toe tussen `sections` en `backcover`:

```typescript
export interface ReportDefinition {
  // ... bestaande velden ...
  sections?: Section[];
  appendices?: Appendix[];        // NIEUW
  backcover?: BackcoverConfig;
  metadata?: Record<string, unknown>;
}
```

### Editor types (met IDs)

Voeg toe na `EditorSection`:

```typescript
/** Bijlage met uniek ID en editor blocks */
export interface EditorAppendix {
  id: string;
  title: string;
  number: number;
  content: EditorBlock[];
}
```

### EditorReport uitbreiden

```typescript
export interface EditorReport {
  // ... bestaande velden ...
  sections: EditorSection[];
  appendices: EditorAppendix[];    // NIEUW
  backcover: BackcoverConfig;
  metadata: Record<string, unknown>;
}
```

---

## Stap 2: Defaults — `src/utils/defaults.ts`

### `createDefaultReport()`

Voeg `appendices: []` toe aan het return object, tussen `sections` en `backcover`.

### Nieuwe factory

```typescript
export function createDefaultAppendix(overrides?: Partial<EditorAppendix>): EditorAppendix {
  return {
    id: generateId(),
    title: 'Nieuwe bijlage',
    number: 0,  // wordt berekend door de store
    content: [],
    ...overrides,
  };
}
```

Importeer `EditorAppendix` in de imports bovenaan.

---

## Stap 3: Conversie — `src/utils/conversion.ts`

### `toEditorReport()`

Voeg appendix conversie toe:

```typescript
function toEditorAppendix(appendix: Appendix, index: number): EditorAppendix {
  return {
    id: generateId(),
    title: appendix.title,
    number: appendix.number ?? index + 1,
    content: (appendix.content ?? []).map(toEditorBlock),
  };
}
```

In `toEditorReport()`:
```typescript
appendices: (def.appendices ?? []).map(toEditorAppendix),
```

### `toReportDefinition()`

Voeg toe:

```typescript
function toSchemaAppendix(appendix: EditorAppendix): Appendix {
  const result: Appendix = { title: appendix.title };
  if (appendix.number > 0) result.number = appendix.number;
  if (appendix.content.length > 0) result.content = appendix.content.map(toSchemaBlock);
  return result;
}
```

In `toReportDefinition()`, na de sections block:
```typescript
if (report.appendices.length > 0) {
  def.appendices = report.appendices.map(toSchemaAppendix);
}
```

---

## Stap 4: Store uitbreiden — `src/stores/reportStore.ts`

### Store interface

Voeg toe in `ReportStore`:

```typescript
// State
activeAppendix: string | null;

// Actions — bijlagen
addAppendix: (appendix: EditorAppendix, index?: number) => void;
addNewAppendix: (index?: number) => void;
updateAppendix: (id: string, updates: Partial<Pick<EditorAppendix, 'title'>>) => void;
removeAppendix: (id: string) => void;
reorderAppendices: (fromIndex: number, toIndex: number) => void;

// Actions — blocks in bijlagen
addAppendixBlock: (appendixId: string, block: EditorBlock, index?: number) => void;
addNewAppendixBlock: (appendixId: string, blockType: EditableBlockType, index?: number) => void;
updateAppendixBlock: (appendixId: string, blockId: string, updates: Partial<ContentBlock>) => void;
removeAppendixBlock: (appendixId: string, blockId: string) => void;
reorderAppendixBlocks: (appendixId: string, fromIndex: number, toIndex: number) => void;
duplicateAppendixBlock: (appendixId: string, blockId: string) => void;

// UI
setActiveAppendix: (id: string | null) => void;
```

### Helper

```typescript
function updateAppendices(
  appendices: EditorAppendix[],
  appendixId: string,
  updater: (appendix: EditorAppendix) => EditorAppendix,
): EditorAppendix[] {
  return appendices.map((a) => (a.id === appendixId ? updater(a) : a));
}
```

### Auto-nummering helper

```typescript
function renumberAppendices(appendices: EditorAppendix[]): EditorAppendix[] {
  return appendices.map((a, i) => ({ ...a, number: i + 1 }));
}
```

### Implementatie

De appendix actions volgen exact hetzelfde patroon als de section actions. Het belangrijkste verschil:

1. **`addAppendix`**: Na toevoegen → `renumberAppendices()` aanroepen
2. **`removeAppendix`**: Na verwijderen → `renumberAppendices()` aanroepen  
3. **`reorderAppendices`**: Na herordenen → `renumberAppendices()` aanroepen
4. **`addNewAppendix`**: Roept `addAppendix(createDefaultAppendix())` aan
5. **Block actions**: Identiek aan section block actions, maar op `report.appendices` i.p.v. `report.sections`

**UI state logica:**
- `setActiveAppendix(id)` moet ook `activeSection` op `null` zetten (en vice versa)
- `setActiveSection(id)` moet ook `activeAppendix` op `null` zetten
- Bij klikken op "Rapport instellingen": zet beide op `null`

Pas `setActiveSection` aan:
```typescript
setActiveSection: (id) => set({ activeSection: id, activeAppendix: null, activeBlock: null }),
setActiveAppendix: (id) => set({ activeAppendix: id, activeSection: null, activeBlock: null }),
```

### Initial state

```typescript
activeAppendix: null,
```

En in `reset()` en `importJson()` en `loadReport()`: voeg `activeAppendix: null` toe.

---

## Stap 5: Sidebar bijlagen sectie — `src/components/layout/Sidebar.tsx`

Voeg onder de bestaande secties-lijst een **"Bijlagen"** sectie toe met dezelfde UX:

### Structuur

```
┌─────────────────────────┐
│ ⚙ Rapport instellingen  │
├─────────────────────────┤
│ SECTIES          + Toev. │
│  ≡ H1 Inleiding         │
│  ≡ H1 Resultaten         │
│  ≡ H1 Conclusie          │
├─────────────────────────┤  ← scheidingslijn
│ BIJLAGEN         + Toev. │
│  ≡ 1. Kadastrale kaart   │
│  ≡ 2. Fotoreportage      │
│  ≡ 3. Berekeningen       │
├─────────────────────────┤
│ 3 secties · 2 bijlagen   │  ← footer update
└─────────────────────────┘
```

### Implementatie

- Haal `appendices`, `activeAppendix`, `setActiveAppendix`, `addNewAppendix`, `removeAppendix`, `reorderAppendices` uit de store
- Maak een `SortableAppendixItem` component (vergelijkbaar met `SortableSectionItem`)
  - Toon: nummer + titel + block count
  - Active state: highlight als `activeAppendix === appendix.id`
  - Drag handle + delete knop (zelfde UX als secties)
- Wrap in eigen `<DndContext>` met eigen `<SortableContext>` (gescheiden van secties DnD)
- Klik op appendix → `setActiveAppendix(id)` (zet automatisch `activeSection` op null)

### Visueel onderscheid

Bijlagen zijn visueel net iets anders dan secties:
- In plaats van `H1`/`H2` badge → toon het bijlage **nummer** (`1`, `2`, `3`)
- Badge kleur: turquoise achtergrond (`bg-teal-100 text-teal-600`) i.p.v. blauw
- Block count + type iconen: zelfde als bij secties

---

## Stap 6: MainPanel bijlage-editor — `src/components/layout/MainPanel.tsx`

### Routing logica

Het MainPanel moet nu drie scenarios kennen:

```typescript
const activeSection = useReportStore((s) => s.activeSection);
const activeAppendix = useReportStore((s) => s.activeAppendix);

// In de render:
if (viewMode === 'json') return <JsonView />;
if (viewMode === 'preview') return <PdfPreview />;

if (activeAppendix) {
  return <AppendixEditor appendixId={activeAppendix} />;
}

if (activeSection) {
  return <SectionEditor sectionId={activeSection} />;
}

return <MetadataTabs />;
```

### Refactor: Extract SectionEditor

De huidige sectie-editing logica in MainPanel (DndContext + SortableBlockItems + BlockToolbox) moet geëxtraheerd worden naar een `<SectionEditor sectionId={...} />` component. Dit voorkomt code duplicatie.

### AppendixEditor component

Maak `src/components/editor/AppendixEditor.tsx`:

```typescript
interface AppendixEditorProps {
  appendixId: string;
}

export function AppendixEditor({ appendixId }: AppendixEditorProps) {
  const appendices = useReportStore((s) => s.report.appendices);
  const appendix = appendices.find((a) => a.id === appendixId);
  // ... store actions voor appendix blocks ...

  if (!appendix) return null;

  return (
    <div className="flex-1 overflow-y-auto">
      {/* Header met titel editor */}
      <div className="sticky top-0 z-10 border-b border-gray-200 bg-white/95 backdrop-blur px-6 py-4">
        <AppendixHeader appendix={appendix} />
      </div>

      {/* Divider preview hint */}
      <div className="mx-6 mt-4 rounded-lg border border-dashed border-teal-300 bg-teal-50 p-4 text-center">
        <p className="text-sm text-teal-700 font-medium">
          Bijlage {appendix.number} — Scheidingspagina
        </p>
        <p className="text-xs text-teal-500 mt-1">
          Turquoise divider wordt automatisch gegenereerd in de PDF
        </p>
      </div>

      {/* Content blocks (optioneel) */}
      <div className="px-6 py-4 space-y-3">
        {appendix.content.length === 0 && (
          <p className="py-4 text-center text-sm text-gray-400 italic">
            Optioneel: voeg content toe die na de divider komt
          </p>
        )}

        {/* DndContext + SortableContext + blocks — zelfde als SectionEditor */}
        {/* Gebruik appendixBlock actions i.p.v. section block actions */}

        <div className="pt-2">
          <BlockToolbox
            onAdd={(blockType) => addNewAppendixBlock(appendixId, blockType)}
          />
        </div>
      </div>
    </div>
  );
}
```

### AppendixHeader

Vergelijkbaar met `SectionHeader` maar met:
- Turquoise badge met bijlage nummer (niet editable, auto-genummerd)
- Bewerkbare titel (klik om te bewerken, zelfde UX als secties)
- Geen level selector (bijlagen hebben geen heading level)

```typescript
function AppendixHeader({ appendix }: { appendix: EditorAppendix }) {
  const updateAppendix = useReportStore((s) => s.updateAppendix);
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(appendix.title);
  // ... zelfde edit logica als SectionHeader ...

  return (
    <div className="flex items-center gap-3">
      <span className="flex h-7 w-7 items-center justify-center rounded bg-teal-100 text-xs font-semibold text-teal-600">
        B{appendix.number}
      </span>
      {editing ? (
        <input ... />
      ) : (
        <h2 className="flex-1 text-lg font-semibold text-gray-900 cursor-pointer hover:text-teal-700 transition-colors"
            onClick={() => setEditing(true)}>
          {appendix.title}
        </h2>
      )}
    </div>
  );
}
```

---

## Stap 7: BlockToolbox aanpassen

De huidige `BlockToolbox` accepteert een `sectionId` prop en roept `addNewBlock(sectionId, type)` aan. Dit moet generiek worden zodat het ook voor bijlagen werkt.

**Optie A (eenvoudigst):** Voeg een `onAdd` callback prop toe:

```typescript
interface BlockToolboxProps {
  sectionId?: string;                           // legacy, voor secties
  onAdd?: (blockType: EditableBlockType) => void; // generiek
}

export function BlockToolbox({ sectionId, onAdd }: BlockToolboxProps) {
  const addNewBlock = useReportStore((s) => s.addNewBlock);

  function handleAdd(type: EditableBlockType) {
    if (onAdd) {
      onAdd(type);
    } else if (sectionId) {
      addNewBlock(sectionId, type);
    }
  }
  // ... rest blijft gelijk, maar gebruik handleAdd(type) bij klik ...
}
```

---

## Stap 8: ColofonForm — bijlage-specifieke velden

De `ColofonForm.tsx` heeft momenteel al extra_fields. Controleer of de colofon data die de backend verwacht (zoals `norms`, `phase`, `status`, `document_code`, `document_description`) beschikbaar is via het formulier.

De nieuwe backend colofon (Fase B) leest deze velden uit `colofon_data`. Voeg de volgende velden toe aan ColofonForm als ze er nog niet zijn:

- **Toegepaste Normen** (`norms`) — textarea
- **Documentgegevens** (`document_description`) — text input
- **Fase in bouwproces** (`phase`) — text input of select
- **Rapportstatus** — leest al uit `report.status`, hoeft niet dubbel
- **Documentkenmerk** (`document_code`) — text input

Deze worden opgeslagen in `colofon.extra_fields` als key-value pairs. De backend leest ze via `colofon_data.get("norms")` etc.

**Let op:** Check of de huidige `extra_fields` implementatie al key-value pairs gebruikt (`Record<string, string>`). Zo ja, dan kunnen deze velden gewoon als vaste velden boven de dynamische extra_fields staan.

---

## Stap 9: Footer update in Sidebar

Update de footer van de Sidebar:

```typescript
<p className="text-xs text-gray-400">
  {sections.length} sectie{sections.length !== 1 ? 's' : ''} &middot;{' '}
  {appendices.length > 0 && (
    <>{appendices.length} bijlage{appendices.length !== 1 ? 'n' : ''} &middot; </>
  )}
  {sections.reduce((sum, s) => sum + s.content.length, 0) +
   appendices.reduce((sum, a) => sum + a.content.length, 0)} blocks
</p>
```

---

## Samenvatting wijzigingen

| Bestand | Wijziging |
|---------|-----------|
| `src/types/report.ts` | +`Appendix`, `EditorAppendix` types, +`appendices` op ReportDefinition en EditorReport |
| `src/utils/defaults.ts` | +`createDefaultAppendix()`, +`appendices: []` in default report |
| `src/utils/conversion.ts` | +`toEditorAppendix()`, +`toSchemaAppendix()`, appendix conversie in beide richtingen |
| `src/stores/reportStore.ts` | +`activeAppendix`, +appendix CRUD actions, +appendix block actions, renumbering, UI state logica |
| `src/components/layout/Sidebar.tsx` | +Bijlagen sectie met drag & drop, `SortableAppendixItem`, footer update |
| `src/components/layout/MainPanel.tsx` | Routing: section / appendix / metadata, extract `SectionEditor` |
| `src/components/editor/AppendixEditor.tsx` | **Nieuw**: Bijlage editor met header, divider hint, block editing |
| `src/components/editor/BlockToolbox.tsx` | +`onAdd` callback prop (generiek gebruik) |
| `src/components/forms/ColofonForm.tsx` | +Vaste velden: norms, phase, document_description, document_code |

## Niet wijzigen

- `src/services/api.ts` — Geen API changes nodig (appendices gaan mee in het ReportDefinition JSON object)
- `src/stores/apiStore.ts` — Geen changes
- Block editors (`CheckEditor`, `TableEditor`, etc.) — Werken al generiek via `updateBlock`
- `src/components/forms/MetadataForm.tsx` — Geen changes
- `src/components/forms/CoverForm.tsx` — Geen changes

## Prioriteit

Als je tijd tekort komt:
1. **Types + Store + Conversie** (stappen 1-4) — Zonder dit werkt niets
2. **Sidebar bijlagen sectie** (stap 5) — Navigatie
3. **AppendixEditor + MainPanel routing** (stap 6) — Editing
4. **BlockToolbox generiek** (stap 7) — Block toevoegen aan bijlagen
5. **ColofonForm velden** (stap 8) — Nice to have
