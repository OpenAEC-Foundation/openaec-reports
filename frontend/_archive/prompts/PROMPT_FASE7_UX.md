# PROMPT: Frontend Fase 7 — UX Essentials

## Context

Dit is de Report Editor frontend (`bm-reports-ui`) — React 18 + TypeScript + Tailwind + Zustand + dnd-kit.
De editor produceert JSON conform `schemas/report.schema.json` en stuurt dat naar de backend API (`POST /api/generate`) voor PDF generatie.

Backend API draait op `http://localhost:8000`. De frontend communiceert via `src/services/api.ts`.

### Huidige staat (Fase 1-6 compleet)

**Wat werkt:**
- Zustand store met volledige CRUD voor secties, blocks, bijlagen
- Sidebar met drag & drop secties + bijlagen
- MainPanel met block editors (paragraph, calculation, check, table, image, map, spacer, page_break)
- MetadataTabs (rapport info, cover, colofon, opties)
- Template selectie + scaffold laden vanuit backend
- JSON export (download .json)
- Handmatige PDF generatie (klik "Genereer PDF" → PDF preview in iframe)
- Validatie tegen JSON schema via backend
- Backend connection indicator

**Wat mist (deze prompt):**
1. **Live PDF preview** — auto-regenerate bij wijzigingen, side-by-side editing
2. **JSON import** — bestaand rapport laden (upload of plakken)
3. **Undo/Redo** — Ctrl+Z / Ctrl+Y
4. **Auto-save naar localStorage** — verlies geen werk bij browser refresh
5. **Keyboard shortcuts** — sneltoetsen voor veelgebruikte acties

---

## Bestandsstructuur (relevant)

```
src/
├── components/
│   ├── blocks/          # ParagraphEditor, CalculationEditor, CheckEditor, TableEditor, ImageEditor, MapEditor, SpacerEditor, PageBreakEditor
│   ├── editor/          # BlockEditor, BlockToolbox, AppendixEditor
│   ├── forms/           # MetadataForm, CoverForm, ColofonForm, OptionsPanel, MetadataTabs, TemplateSelector, ToggleSwitch
│   └── layout/          # AppShell, Sidebar, MainPanel, ValidationBanner
├── services/
│   └── api.ts           # Backend API client (health, templates, brands, validate, generate)
├── stores/
│   ├── reportStore.ts   # Zustand — rapport state + UI state + CRUD actions
│   └── apiStore.ts      # Zustand — backend connection, validation, PDF generation
├── types/
│   └── report.ts        # TypeScript types (ReportDefinition, EditorReport, EditorSection, EditorBlock, etc.)
├── utils/
│   ├── conversion.ts    # toEditorReport() / toReportDefinition() — schema ↔ editor conversie
│   ├── defaults.ts      # createDefaultReport/Section/Appendix/Block
│   └── idGenerator.ts   # nanoid wrapper
├── App.tsx              # Root — laadt example data, checkt backend health
├── main.tsx
└── index.css
```

### Dependencies (package.json)

```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "zustand": "^5.0.3",
    "@dnd-kit/core": "^6.3.1",
    "@dnd-kit/sortable": "^10.0.0",
    "@dnd-kit/utilities": "^3.2.2",
    "nanoid": "^5.1.2"
  }
}
```

Geen extra dependencies nodig — alles kan met Zustand middleware en standaard browser APIs.

---

## Feature 1: Undo/Redo

### 1.1 Zustand temporal middleware

Maak `src/stores/undoMiddleware.ts`:

Implementeer een eenvoudige temporal middleware voor Zustand die snapshots bijhoudt van `report` (NIET van UI state zoals activeSection/activeBlock).

```typescript
interface TemporalState<T> {
  past: T[];
  future: T[];
  canUndo: boolean;
  canRedo: boolean;
}

// Middleware die elke set() call op de store onderschept
// en een snapshot van report pusht naar past[]
```

**Specificaties:**
- Track alleen `report` field (EditorReport), niet UI state
- Max 50 snapshots in past[] (ring buffer)
- Undo: pop past[], push current naar future[]
- Redo: pop future[], push current naar past[]
- Elke `set()` die `report` wijzigt → wis future[], push vorige report naar past[]
- Debounce: als er binnen 300ms meerdere set() calls komen (bijv. typen in een textarea), groepeer ze als één undo stap

**Alternatief (eenvoudiger):** Gebruik `zustand/middleware` met een custom wrapper:

```typescript
import { create } from 'zustand';

// In reportStore.ts — voeg toe aan de store:
interface ReportStore {
  // ... bestaande velden ...
  
  // Undo/redo
  _past: EditorReport[];
  _future: EditorReport[];
  canUndo: boolean;
  canRedo: boolean;
  undo: () => void;
  redo: () => void;
  _pushHistory: () => void;  // intern — roep aan voor elke wijziging
}
```

**Implementatie-aanpak:** Wrap elke bestaande action die `report` wijzigt met een `_pushHistory()` call. Dit is minder elegant maar verreweg het simpelst zonder externe library.

Let op: `_pushHistory()` moet VOOR de state change worden aangeroepen (push huidige `report` naar `_past`).

### 1.2 Keyboard shortcuts

In `AppShell.tsx`, voeg een `useEffect` toe met een global `keydown` listener:

```typescript
useEffect(() => {
  function handleKeyDown(e: KeyboardEvent) {
    const mod = e.metaKey || e.ctrlKey;
    
    if (mod && e.key === 'z' && !e.shiftKey) {
      e.preventDefault();
      useReportStore.getState().undo();
    }
    if (mod && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
      e.preventDefault();
      useReportStore.getState().redo();
    }
    if (mod && e.key === 's') {
      e.preventDefault();
      // Trigger export of save
      handleExport();
    }
  }
  
  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, []);
```

### 1.3 UI indicators

In de `AppShell` header, voeg undo/redo knoppen toe naast de bestaande actieknoppen:

```tsx
{/* Undo/Redo buttons — links van Export JSON */}
<button onClick={undo} disabled={!canUndo} title="Ongedaan maken (Ctrl+Z)" ...>
  ↶
</button>
<button onClick={redo} disabled={!canRedo} title="Opnieuw (Ctrl+Y)" ...>
  ↷
</button>
```

Gebruik dezelfde button styling als de bestaande "Export JSON" en "Valideer" knoppen (border border-gray-200 px-3 py-1.5 text-xs).

---

## Feature 2: Auto-save naar localStorage

### 2.1 Persist middleware

In `reportStore.ts`, voeg localStorage persistentie toe.

**Aanpak:** Gebruik een `subscribe()` handler op de store die bij elke `report` wijziging de staat naar localStorage schrijft.

```typescript
const STORAGE_KEY = 'bm-reports-editor-state';
const SAVE_DEBOUNCE_MS = 1000;

// Na store creatie:
let saveTimeout: ReturnType<typeof setTimeout> | null = null;

useReportStore.subscribe((state, prev) => {
  // Alleen opslaan als report gewijzigd is
  if (state.report !== prev.report) {
    if (saveTimeout) clearTimeout(saveTimeout);
    saveTimeout = setTimeout(() => {
      try {
        const data = {
          report: toReportDefinition(state.report),  // Sla schema-formaat op (zonder IDs)
          savedAt: new Date().toISOString(),
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
      } catch (e) {
        console.warn('Auto-save mislukt:', e);
      }
    }, SAVE_DEBOUNCE_MS);
  }
});
```

### 2.2 Restore bij startup

In `App.tsx`, check localStorage VOOR het laden van example data:

```typescript
useEffect(() => {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) {
    try {
      const { report: savedReport, savedAt } = JSON.parse(saved);
      // Valideer minimaal dat template en project bestaan
      if (savedReport?.template && savedReport?.project) {
        loadReport(savedReport as ReportDefinition);
        console.log(`Rapport hersteld van ${savedAt}`);
        return;  // Skip example data laden
      }
    } catch {
      // Corrupte data — negeer
    }
  }
  // Fallback: laad example data
  loadReport(exampleData as ReportDefinition);
}, [loadReport]);
```

### 2.3 UI feedback

Voeg een subtiele "Opgeslagen" indicator toe in de AppShell header, naast de dirty indicator:

```tsx
{isDirty ? (
  <span className="text-xs text-amber-500 font-medium">Onopgeslagen wijzigingen</span>
) : lastSavedAt ? (
  <span className="text-xs text-gray-400">Opgeslagen {formatTimeAgo(lastSavedAt)}</span>
) : null}
```

Voeg `lastSavedAt: string | null` toe aan de store (of als lokale state in AppShell).

### 2.4 Reset functie

Breid de `reset()` action uit om ook localStorage te wissen:

```typescript
reset: () => {
  localStorage.removeItem(STORAGE_KEY);
  set({ report: createDefaultReport(), /* ... */ });
}
```

Voeg een "Nieuw rapport" knop toe in de sidebar header of in het opties-menu die `reset()` aanroept (met bevestiging).

---

## Feature 3: JSON Import

### 3.1 Import knop in AppShell header

Voeg een "Import JSON" knop toe naast "Export JSON":

```tsx
<button
  onClick={() => fileInputRef.current?.click()}
  className="rounded-md border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors"
>
  Import JSON
</button>
<input
  ref={fileInputRef}
  type="file"
  accept=".json"
  className="hidden"
  onChange={handleFileImport}
/>
```

### 3.2 Import handler

```typescript
function handleFileImport(e: React.ChangeEvent<HTMLInputElement>) {
  const file = e.target.files?.[0];
  if (!file) return;
  
  const reader = new FileReader();
  reader.onload = () => {
    const json = reader.result as string;
    const result = importJson(json);
    if (result.ok) {
      setToast({ message: `Rapport "${file.name}" geladen`, type: 'success' });
    } else {
      setToast({ message: result.errors[0] ?? 'Import mislukt', type: 'error' });
    }
  };
  reader.readAsText(file);
  
  // Reset input zodat hetzelfde bestand opnieuw gekozen kan worden
  e.target.value = '';
}
```

### 3.3 Drag & drop import

Voeg een `onDragOver` + `onDrop` handler toe aan de AppShell root `<div>`:

```typescript
function handleDrop(e: React.DragEvent) {
  e.preventDefault();
  setDragOver(false);
  
  const file = e.dataTransfer.files[0];
  if (!file || !file.name.endsWith('.json')) return;
  
  const reader = new FileReader();
  reader.onload = () => {
    const result = importJson(reader.result as string);
    if (result.ok) {
      setToast({ message: `Rapport "${file.name}" geladen`, type: 'success' });
    } else {
      setToast({ message: result.errors[0] ?? 'Import mislukt', type: 'error' });
    }
  };
  reader.readAsText(file);
}
```

Toon een visuele overlay als een bestand over het venster wordt gesleept:

```tsx
{dragOver && (
  <div className="absolute inset-0 z-50 flex items-center justify-center bg-blue-500/10 border-2 border-dashed border-blue-400 pointer-events-none">
    <div className="rounded-xl bg-white px-8 py-6 shadow-lg text-center">
      <p className="text-lg font-medium text-blue-700">JSON rapport importeren</p>
      <p className="text-sm text-gray-500">Laat los om te laden</p>
    </div>
  </div>
)}
```

### 3.4 JSON plakken in JSON view

In de JSON view mode (`viewMode === 'json'`), maak het JSON venster bewerkbaar:

Vervang de huidige read-only `<pre>` met een `<textarea>`:

```tsx
if (viewMode === 'json') {
  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-gray-900">
      {/* Toolbar */}
      <div className="flex items-center gap-2 border-b border-gray-700 px-4 py-2">
        <button onClick={handleApplyJson} className="...">
          Toepassen
        </button>
        <button onClick={handleFormatJson} className="...">
          Formatteren
        </button>
        {jsonError && <span className="text-xs text-red-400">{jsonError}</span>}
      </div>
      
      <textarea
        value={jsonText}
        onChange={(e) => setJsonText(e.target.value)}
        className="flex-1 bg-gray-900 p-6 text-sm text-green-300 font-mono resize-none outline-none"
        spellCheck={false}
      />
    </div>
  );
}
```

"Toepassen" knop: parse JSON, valideer, en laad in de store via `importJson()`.

---

## Feature 4: Live PDF Preview

### 4.1 Auto-regenerate met debounce

In `apiStore.ts`, voeg een `autoPreview` flag en debounced generate toe:

```typescript
interface ApiStore {
  // ... bestaande velden ...
  autoPreview: boolean;
  setAutoPreview: (enabled: boolean) => void;
  _previewTimeout: ReturnType<typeof setTimeout> | null;
  schedulePreview: () => void;
}
```

**Implementatie:**

```typescript
autoPreview: true,

setAutoPreview: (enabled) => set({ autoPreview: enabled }),

schedulePreview: () => {
  const state = get();
  if (!state.autoPreview || !state.connected || state.isGenerating) return;
  
  // Cancel vorige
  if (state._previewTimeout) clearTimeout(state._previewTimeout);
  
  const timeout = setTimeout(() => {
    get().generatePdf();
  }, 1500);  // 1.5 sec debounce — genoeg tijd om te typen
  
  set({ _previewTimeout: timeout });
},
```

### 4.2 Trigger bij report wijzigingen

In `reportStore.ts`, voeg een subscriber toe die de apiStore triggert:

```typescript
// Na store creatie — auto-preview trigger
useReportStore.subscribe((state, prev) => {
  if (state.report !== prev.report) {
    useApiStore.getState().schedulePreview();
  }
});
```

### 4.3 Split-screen layout

De huidige `MainPanel` heeft een `viewMode` toggle (editor / json / preview) die het hele panel switcht. Wijzig dit naar een split-screen optie:

Voeg een vierde viewMode toe: `'split'`

```typescript
export type ViewMode = 'editor' | 'json' | 'preview' | 'split';
```

Update `VIEW_MODE_TABS` in `AppShell.tsx`:

```typescript
const VIEW_MODE_TABS: { mode: ViewMode; label: string }[] = [
  { mode: 'editor', label: 'Editor' },
  { mode: 'split', label: 'Split' },
  { mode: 'json', label: 'JSON' },
  { mode: 'preview', label: 'Preview' },
];
```

### 4.4 Split view component

Wijzig `MainPanel.tsx` om split view te ondersteunen:

```tsx
// In MainPanel, na de viewMode checks:

if (viewMode === 'split') {
  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Links: editor */}
      <div className="flex-1 overflow-y-auto border-r border-gray-200">
        {activeAppendix ? (
          <AppendixEditor appendixId={activeAppendix} />
        ) : section ? (
          <SectionEditorContent section={section} />
        ) : (
          <MetadataTabs />
        )}
      </div>
      
      {/* Rechts: PDF preview */}
      <div className="flex-1 flex flex-col">
        <PdfPreview />
      </div>
    </div>
  );
}
```

Extraheer de section editor content uit de bestaande MainPanel return naar een `SectionEditorContent` component, zodat die hergebruikt kan worden in zowel full-screen als split view.

### 4.5 Auto-preview toggle

In de preview paneel header (of in OptionsPanel), voeg een toggle toe:

```tsx
<div className="flex items-center gap-2 border-b border-gray-200 px-4 py-2">
  <ToggleSwitch
    checked={autoPreview}
    onChange={setAutoPreview}
    label="Auto-preview"
  />
  {isGenerating && <span className="text-xs text-gray-400">Genereren...</span>}
  {!autoPreview && (
    <button onClick={generatePdf} className="...">
      Vernieuw
    </button>
  )}
</div>
```

`ToggleSwitch` component bestaat al in `forms/ToggleSwitch.tsx`.

---

## Feature 5: Keyboard Shortcuts

### 5.1 Uitgebreide shortcut map

Voeg toe aan de `useEffect` keydown handler in `AppShell.tsx`:

```typescript
const shortcuts: Record<string, () => void> = {
  // Document-level
  'ctrl+s': handleExport,           // Export JSON
  'ctrl+z': () => undo(),           // Undo
  'ctrl+y': () => redo(),           // Redo  
  'ctrl+shift+z': () => redo(),     // Redo (alt)
  
  // View modes
  'ctrl+1': () => setViewMode('editor'),
  'ctrl+2': () => setViewMode('split'),
  'ctrl+3': () => setViewMode('json'),
  'ctrl+4': () => setViewMode('preview'),
  
  // Genereren
  'ctrl+enter': () => generatePdf(),
  
  // Blocks
  'ctrl+shift+p': () => addBlockToActiveSection('paragraph'),
  'ctrl+shift+k': () => addBlockToActiveSection('calculation'),
  'ctrl+shift+t': () => addBlockToActiveSection('table'),
  
  // Navigatie
  'escape': () => setActiveBlock(null),  // Deselect block
};

function handleKeyDown(e: KeyboardEvent) {
  // Niet activeren als focus in textarea/input is (voor typing shortcuts)
  const target = e.target as HTMLElement;
  const isTyping = target.tagName === 'TEXTAREA' || target.tagName === 'INPUT' || target.isContentEditable;
  
  const mod = e.metaKey || e.ctrlKey;
  const shift = e.shiftKey;
  
  let key = '';
  if (mod) key += 'ctrl+';
  if (shift) key += 'shift+';
  key += e.key.toLowerCase();
  
  // Document-level shortcuts werken altijd
  const alwaysActive = ['ctrl+s', 'ctrl+z', 'ctrl+y', 'ctrl+shift+z', 'ctrl+enter'];
  
  if (alwaysActive.includes(key) || !isTyping) {
    const handler = shortcuts[key];
    if (handler) {
      e.preventDefault();
      handler();
    }
  }
}
```

### 5.2 Shortcut help dialog

Maak `src/components/layout/ShortcutHelp.tsx`:

Een simpele modal die alle shortcuts toont. Toon met `Ctrl+/` of `?`.

```tsx
export function ShortcutHelp({ open, onClose }: { open: boolean; onClose: () => void }) {
  if (!open) return null;
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div className="w-[480px] rounded-xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-lg font-semibold mb-4">Sneltoetsen</h2>
        
        <div className="space-y-3 text-sm">
          <ShortcutGroup title="Document">
            <Shortcut keys="Ctrl+S" action="Export JSON" />
            <Shortcut keys="Ctrl+Z" action="Ongedaan maken" />
            <Shortcut keys="Ctrl+Y" action="Opnieuw" />
            <Shortcut keys="Ctrl+Enter" action="Genereer PDF" />
          </ShortcutGroup>
          
          <ShortcutGroup title="Weergave">
            <Shortcut keys="Ctrl+1" action="Editor" />
            <Shortcut keys="Ctrl+2" action="Split (editor + preview)" />
            <Shortcut keys="Ctrl+3" action="JSON" />
            <Shortcut keys="Ctrl+4" action="Preview" />
          </ShortcutGroup>
          
          <ShortcutGroup title="Blocks toevoegen">
            <Shortcut keys="Ctrl+Shift+P" action="Tekst" />
            <Shortcut keys="Ctrl+Shift+K" action="Berekening" />
            <Shortcut keys="Ctrl+Shift+T" action="Tabel" />
          </ShortcutGroup>
          
          <ShortcutGroup title="Navigatie">
            <Shortcut keys="Escape" action="Block deselecteren" />
            <Shortcut keys="?" action="Deze help" />
          </ShortcutGroup>
        </div>
        
        <button onClick={onClose} className="mt-4 w-full rounded-lg bg-gray-100 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200">
          Sluiten
        </button>
      </div>
    </div>
  );
}
```

Voeg een `?` knop toe in de AppShell header (links van de actieknoppen) die de help opent.

---

## Feature 6: Nieuw rapport / Reset

### 6.1 "Nieuw rapport" in sidebar

Voeg een knop toe boven "Rapport instellingen" in de Sidebar:

```tsx
<div className="px-3 pt-3 pb-1 space-y-1">
  <button
    onClick={() => {
      if (isDirty) {
        // Bevestiging
        if (!confirm('Huidig rapport verwijderen? Onopgeslagen wijzigingen gaan verloren.')) return;
      }
      reset();
    }}
    className="w-full flex items-center gap-2 rounded-md px-2 py-2 text-sm text-gray-500 hover:bg-gray-50 hover:text-gray-700 transition-colors"
  >
    <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
    </svg>
    Nieuw rapport
  </button>
  
  {/* Bestaande "Rapport instellingen" knop */}
</div>
```

### 6.2 Template selectie bij nieuw rapport

Als er templates beschikbaar zijn (via backend), toon een template picker modal bij "Nieuw rapport":

```tsx
// In plaats van direct reset(), toon een dialog:
function handleNewReport() {
  if (isDirty && !confirm('...')) return;
  
  if (templates.length > 0) {
    setShowTemplatePicker(true);
  } else {
    reset();
  }
}
```

De `TemplateSelector` component bestaat al in `forms/TemplateSelector.tsx`. Hergebruik die als modal content.

---

## Implementatievolgorde

```
Feature 2 (Import) → Feature 4.3-4.4 (Split view) → Feature 1 (Undo/Redo) → Feature 3 (Auto-save) → Feature 4.1-4.2 (Auto-preview) → Feature 5 (Shortcuts) → Feature 6 (Reset/New)
```

**Waarom deze volgorde:**
1. **Import** is triviaal (store.importJson bestaat al, alleen UI ontbreekt)
2. **Split view** is puur layout, geen state changes
3. **Undo/Redo** raakt de store — doe dit vóór auto-save om ze samen te testen
4. **Auto-save** bouwt voort op de undo-aware store
5. **Auto-preview** bouwt voort op split view + store subscribers
6. **Shortcuts + Reset** zijn finishing touches

---

## Verificatie per feature

### Import JSON
- [ ] "Import JSON" knop in header → file picker opent
- [ ] Selecteer `schemas/example_structural.json` → rapport laadt correct
- [ ] Drag & drop .json bestand op het venster → rapport laadt
- [ ] JSON view is bewerkbaar → "Toepassen" knop werkt
- [ ] Ongeldig JSON → foutmelding, geen crash

### Undo/Redo
- [ ] Wijzig projectnaam → Ctrl+Z → naam hersteld
- [ ] Voeg block toe → Ctrl+Z → block verwijderd
- [ ] Ctrl+Z → Ctrl+Y → block weer terug
- [ ] 50+ wijzigingen → eerste 50 undo stappen beschikbaar
- [ ] Undo knoppen in header enabled/disabled correct

### Auto-save
- [ ] Wijzig rapport → wacht 1 sec → ververs browser → rapport hersteld
- [ ] "Opgeslagen" indicator verschijnt na save
- [ ] "Nieuw rapport" → localStorage gewist → ververs → leeg rapport

### Live Preview
- [ ] Split view: editor links, PDF rechts
- [ ] Wijzig tekst → wacht 1.5 sec → PDF vernieuwt automatisch
- [ ] Auto-preview toggle uit → PDF vernieuwt NIET automatisch
- [ ] "Vernieuw" knop beschikbaar als auto-preview uit staat
- [ ] Ctrl+Enter genereert PDF ongeacht auto-preview setting

### Keyboard Shortcuts
- [ ] Ctrl+S in editor → export JSON
- [ ] Ctrl+Z/Y → undo/redo
- [ ] Ctrl+1/2/3/4 → view mode switch
- [ ] Ctrl+Enter → genereer PDF
- [ ] ? → shortcut help dialog
- [ ] Shortcuts werken NIET als focus in textarea (behalve Ctrl+S/Z/Y)

---

## Aandachtspunten

1. **Performance:** Undo history bewaakt geheugen. Max 50 snapshots, gebruik structureel delen waar mogelijk (Zustand's immer of handmatige shallow copies).

2. **Auto-preview throttling:** 1.5 sec debounce is het minimum. Als de backend langzaam is (>2 sec), queue niet meerdere requests. Gebruik een `isGenerating` guard.

3. **Split view breedte:** Gebruik `flex-1` voor beide panelen (50/50). Overweeg een versleepbare divider later, maar dat is niet nodig voor nu.

4. **JSON view editing:** De textarea aanpak is simpel maar werkt. Monaco Editor zou beter zijn (syntax highlighting, error markers) maar is een zware dependency (~2MB). Doe het met textarea voor nu, overweeg Monaco later.

5. **LocalStorage limiet:** localStorage heeft ~5MB limiet. Een groot rapport met base64 images kan dat bereiken. Catch de `QuotaExceededError` en toon een warning.

6. **Browser tab waarschuwing:** Voeg een `beforeunload` event toe als `isDirty` true is:

```typescript
useEffect(() => {
  function handleBeforeUnload(e: BeforeUnloadEvent) {
    if (useReportStore.getState().isDirty) {
      e.preventDefault();
    }
  }
  window.addEventListener('beforeunload', handleBeforeUnload);
  return () => window.removeEventListener('beforeunload', handleBeforeUnload);
}, []);
```

7. **isDirty na auto-save:** Na een succesvolle auto-save naar localStorage, zet `isDirty` NIET op false. isDirty betekent "niet geëxporteerd als bestand", niet "niet opgeslagen". De gebruiker moet bewust exporteren om isDirty te resetten.
