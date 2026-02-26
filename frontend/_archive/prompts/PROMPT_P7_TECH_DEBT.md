# P7: Technische Schuld — Tests, Error Boundaries, Hardening

## Context

De frontend is functioneel compleet maar mist drie dingen voor productie-waardigheid:
1. **Geen tests** — geen enkele unit of integration test
2. **Geen error boundaries** — een crash in een block editor breekt de hele app
3. **Hardcoded API URL** — `http://localhost:8000` staat hardcoded in `services/api.ts`

TypeScript strict mode staat al aan (`tsconfig.json`), dat is goed. Focus nu op runtime veiligheid en testbare correctheid.

## Scope

1. Vitest + React Testing Library opzetten
2. Core unit tests schrijven (conversion round-trip, store actions, block editors)
3. Error boundary component rond block editors
4. API URL via environment variable (`VITE_API_URL`)
5. Build warnings oplossen

## Stap 0: Oriëntatie

Lees voordat je begint:
- `package.json` — huidige dependencies (geen test framework aanwezig)
- `tsconfig.json` — strict mode al aan ✅
- `vite.config.ts` — huidige Vite configuratie
- `src/utils/conversion.ts` — de kritieke round-trip logica
- `src/stores/reportStore.ts` — store met alle actions
- `src/services/api.ts` — hardcoded API_BASE
- `src/components/editor/BlockEditor.tsx` — switch statement over block types

## Stap 1: Vitest + React Testing Library Installeren

```bash
cd "X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator_frontend"
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

### Vitest configuratie

Voeg toe aan `vite.config.ts`:

```ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': '/src',
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
    css: false,  // Skip CSS parsing in tests
  },
});
```

### Test setup

Maak `src/test/setup.ts`:

```ts
import '@testing-library/jest-dom';
```

### Scripts

Voeg toe aan `package.json`:

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage"
  }
}
```

### TypeScript config voor tests

Maak `tsconfig.test.json` (optioneel, als nodig voor test globals):

```json
{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "types": ["vitest/globals", "@testing-library/jest-dom"]
  }
}
```

Of voeg `"types": ["vitest/globals"]` toe aan de hoofdconfiguratie.

## Stap 2: Conversion Round-trip Test (KRITIEK)

Dit is de **belangrijkste test** — als de conversie stuk gaat, worden rapporten corrupt.

Maak `src/utils/__tests__/conversion.test.ts`:

```ts
import { describe, it, expect } from 'vitest';
import { toEditorReport, toReportDefinition } from '../conversion';
import type { ReportDefinition } from '@/types/report';

// Minimaal rapport
const MINIMAL: ReportDefinition = {
  template: '3bm-bbl',
  project: 'Test Project',
};

// Volledig rapport met alle velden
const FULL: ReportDefinition = {
  template: '3bm-bbl',
  project: 'Test Project',
  project_number: '2503.30',
  client: 'Opdrachtgever BV',
  author: 'Ir. J. Test',
  date: '2025-03-01',
  version: '2.0',
  status: 'DEFINITIEF',
  format: 'A4',
  orientation: 'portrait',
  cover: {
    subtitle: 'Constructief rapport',
    extra_fields: { 'Kenmerk': 'ABC-123' },
  },
  colofon: {
    enabled: true,
    disclaimer: 'Standaard disclaimer',
    revision_history: [
      { version: '1.0', date: '2025-01-01', description: 'Eerste versie' },
      { version: '2.0', date: '2025-03-01', author: 'JT', description: 'Revisie' },
    ],
  },
  toc: { enabled: true, title: 'Inhoudsopgave', max_depth: 3 },
  sections: [
    {
      title: 'Inleiding',
      level: 1,
      content: [
        { type: 'paragraph', text: 'Dit is een <b>test</b> paragraaf.' },
        { type: 'calculation', title: 'Calc 1', formula: 'F = m * a', result: '100', unit: 'kN' },
      ],
    },
    {
      title: 'Toetsing',
      level: 1,
      page_break_before: true,
      content: [
        { type: 'check', description: 'UC toets', unity_check: 0.85, limit: 1.0, result: 'VOLDOET' },
        { type: 'table', headers: ['Kolom A', 'Kolom B'], rows: [[1, 'x'], [2, 'y']] },
        { type: 'spacer', height_mm: 10 },
        { type: 'page_break' },
        { type: 'image', src: 'test.png', caption: 'Figuur 1' },
      ],
    },
  ],
  appendices: [
    { title: 'Bijlage A', number: 1, content: [{ type: 'paragraph', text: 'Bijlage inhoud' }] },
  ],
  backcover: { enabled: true },
};

describe('conversion round-trip', () => {
  it('round-trips a minimal report', () => {
    const editor = toEditorReport(MINIMAL);
    const output = toReportDefinition(editor);
    expect(output.template).toBe(MINIMAL.template);
    expect(output.project).toBe(MINIMAL.project);
  });

  it('round-trips a full report preserving all data', () => {
    const editor = toEditorReport(FULL);
    const output = toReportDefinition(editor);

    // Top-level fields
    expect(output.template).toBe(FULL.template);
    expect(output.project).toBe(FULL.project);
    expect(output.project_number).toBe(FULL.project_number);
    expect(output.client).toBe(FULL.client);
    expect(output.status).toBe(FULL.status);

    // Cover
    expect(output.cover?.subtitle).toBe(FULL.cover?.subtitle);
    expect(output.cover?.extra_fields).toEqual(FULL.cover?.extra_fields);

    // Colofon
    expect(output.colofon?.revision_history).toHaveLength(2);
    expect(output.colofon?.disclaimer).toBe(FULL.colofon?.disclaimer);

    // Sections
    expect(output.sections).toHaveLength(2);
    expect(output.sections![0]!.title).toBe('Inleiding');
    expect(output.sections![0]!.content).toHaveLength(2);
    expect(output.sections![1]!.page_break_before).toBe(true);

    // Block content preserved
    const para = output.sections![0]!.content![0]!;
    expect(para.type).toBe('paragraph');
    if (para.type === 'paragraph') {
      expect(para.text).toBe('Dit is een <b>test</b> paragraaf.');
    }

    // Appendices
    expect(output.appendices).toHaveLength(1);
    expect(output.appendices![0]!.title).toBe('Bijlage A');

    // Backcover
    expect(output.backcover?.enabled).toBe(true);
  });

  it('strips editor IDs from output', () => {
    const editor = toEditorReport(FULL);
    const output = toReportDefinition(editor);
    const json = JSON.stringify(output);
    // Editor IDs should not appear in output
    for (const section of editor.sections) {
      expect(json).not.toContain(`"id":"${section.id}"`);
      for (const block of section.content) {
        expect(json).not.toContain(`"id":"${block.id}"`);
      }
    }
  });

  it('assigns unique IDs to editor sections and blocks', () => {
    const editor = toEditorReport(FULL);
    const allIds = new Set<string>();
    for (const section of editor.sections) {
      expect(allIds.has(section.id)).toBe(false);
      allIds.add(section.id);
      for (const block of section.content) {
        expect(allIds.has(block.id)).toBe(false);
        allIds.add(block.id);
      }
    }
    for (const appendix of editor.appendices) {
      expect(allIds.has(appendix.id)).toBe(false);
      allIds.add(appendix.id);
    }
  });
});
```

## Stap 3: Store Unit Tests

Maak `src/stores/__tests__/reportStore.test.ts`:

```ts
import { describe, it, expect, beforeEach } from 'vitest';
import { useReportStore } from '../reportStore';

describe('reportStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useReportStore.getState().reset();
  });

  describe('sections', () => {
    it('adds a new section', () => {
      useReportStore.getState().addNewSection();
      expect(useReportStore.getState().report.sections).toHaveLength(1);
    });

    it('removes a section', () => {
      useReportStore.getState().addNewSection();
      const id = useReportStore.getState().report.sections[0]!.id;
      useReportStore.getState().removeSection(id);
      expect(useReportStore.getState().report.sections).toHaveLength(0);
    });

    it('reorders sections', () => {
      useReportStore.getState().addNewSection();
      useReportStore.getState().addNewSection();
      const [a, b] = useReportStore.getState().report.sections;
      useReportStore.getState().reorderSections(0, 1);
      const reordered = useReportStore.getState().report.sections;
      expect(reordered[0]!.id).toBe(b!.id);
      expect(reordered[1]!.id).toBe(a!.id);
    });

    it('updates section title', () => {
      useReportStore.getState().addNewSection();
      const id = useReportStore.getState().report.sections[0]!.id;
      useReportStore.getState().updateSection(id, { title: 'Nieuwe titel' });
      expect(useReportStore.getState().report.sections[0]!.title).toBe('Nieuwe titel');
    });
  });

  describe('blocks', () => {
    let sectionId: string;

    beforeEach(() => {
      useReportStore.getState().addNewSection();
      sectionId = useReportStore.getState().report.sections[0]!.id;
    });

    it('adds a paragraph block', () => {
      useReportStore.getState().addNewBlock(sectionId, 'paragraph');
      const section = useReportStore.getState().report.sections[0]!;
      expect(section.content).toHaveLength(1);
      expect(section.content[0]!.type).toBe('paragraph');
    });

    it('adds a calculation block', () => {
      useReportStore.getState().addNewBlock(sectionId, 'calculation');
      const section = useReportStore.getState().report.sections[0]!;
      expect(section.content[0]!.type).toBe('calculation');
    });

    it('removes a block', () => {
      useReportStore.getState().addNewBlock(sectionId, 'paragraph');
      const blockId = useReportStore.getState().report.sections[0]!.content[0]!.id;
      useReportStore.getState().removeBlock(sectionId, blockId);
      expect(useReportStore.getState().report.sections[0]!.content).toHaveLength(0);
    });

    it('duplicates a block with new ID', () => {
      useReportStore.getState().addNewBlock(sectionId, 'paragraph');
      const originalId = useReportStore.getState().report.sections[0]!.content[0]!.id;
      useReportStore.getState().duplicateBlock(sectionId, originalId);
      const content = useReportStore.getState().report.sections[0]!.content;
      expect(content).toHaveLength(2);
      expect(content[0]!.id).not.toBe(content[1]!.id);
      expect(content[0]!.type).toBe(content[1]!.type);
    });

    it('reorders blocks', () => {
      useReportStore.getState().addNewBlock(sectionId, 'paragraph');
      useReportStore.getState().addNewBlock(sectionId, 'calculation');
      const content = useReportStore.getState().report.sections[0]!.content;
      const [a, b] = content;
      useReportStore.getState().reorderBlocks(sectionId, 0, 1);
      const reordered = useReportStore.getState().report.sections[0]!.content;
      expect(reordered[0]!.id).toBe(b!.id);
      expect(reordered[1]!.id).toBe(a!.id);
    });
  });

  describe('appendices', () => {
    it('adds and renumbers appendices', () => {
      useReportStore.getState().addNewAppendix();
      useReportStore.getState().addNewAppendix();
      const appendices = useReportStore.getState().report.appendices;
      expect(appendices).toHaveLength(2);
      expect(appendices[0]!.number).toBe(1);
      expect(appendices[1]!.number).toBe(2);
    });

    it('renumbers after removal', () => {
      useReportStore.getState().addNewAppendix();
      useReportStore.getState().addNewAppendix();
      useReportStore.getState().addNewAppendix();
      const firstId = useReportStore.getState().report.appendices[0]!.id;
      useReportStore.getState().removeAppendix(firstId);
      const appendices = useReportStore.getState().report.appendices;
      expect(appendices).toHaveLength(2);
      expect(appendices[0]!.number).toBe(1);
      expect(appendices[1]!.number).toBe(2);
    });
  });

  describe('undo/redo', () => {
    it('undoes a section add', () => {
      useReportStore.getState().addNewSection();
      expect(useReportStore.getState().report.sections).toHaveLength(1);
      useReportStore.getState().undo();
      expect(useReportStore.getState().report.sections).toHaveLength(0);
    });

    it('redoes after undo', () => {
      useReportStore.getState().addNewSection();
      useReportStore.getState().undo();
      useReportStore.getState().redo();
      expect(useReportStore.getState().report.sections).toHaveLength(1);
    });
  });

  describe('metadata', () => {
    it('sets metadata fields', () => {
      useReportStore.getState().setMetadata({
        project: 'Nieuw Project',
        project_number: '2503.30',
        status: 'DEFINITIEF',
      });
      const report = useReportStore.getState().report;
      expect(report.project).toBe('Nieuw Project');
      expect(report.project_number).toBe('2503.30');
      expect(report.status).toBe('DEFINITIEF');
    });
  });

  describe('import/export', () => {
    it('exports and re-imports without data loss', () => {
      useReportStore.getState().setMetadata({ project: 'Round Trip Test', client: 'Klant BV' });
      useReportStore.getState().addNewSection();
      const sectionId = useReportStore.getState().report.sections[0]!.id;
      useReportStore.getState().addNewBlock(sectionId, 'paragraph');

      const json = useReportStore.getState().exportJson();
      useReportStore.getState().reset();

      const result = useReportStore.getState().importJson(json);
      expect(result.ok).toBe(true);
      expect(useReportStore.getState().report.project).toBe('Round Trip Test');
      expect(useReportStore.getState().report.sections).toHaveLength(1);
    });

    it('rejects invalid JSON', () => {
      const result = useReportStore.getState().importJson('not json');
      expect(result.ok).toBe(false);
    });

    it('rejects JSON without required fields', () => {
      const result = useReportStore.getState().importJson('{"foo": "bar"}');
      expect(result.ok).toBe(false);
    });
  });
});
```

## Stap 4: Error Boundary Component

Maak `src/components/shared/ErrorBoundary.tsx`:

```tsx
import { Component, type ReactNode, type ErrorInfo } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  context?: string;   // Bijv. "ParagraphEditor", "TableEditor"
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error(`[ErrorBoundary${this.props.context ? `: ${this.props.context}` : ''}]`, error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm font-medium text-red-700">
            Er ging iets mis{this.props.context ? ` in ${this.props.context}` : ''}
          </p>
          <p className="mt-1 text-xs text-red-500 font-mono">
            {this.state.error?.message}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-2 rounded bg-red-600 px-3 py-1 text-xs text-white hover:bg-red-700"
          >
            Opnieuw proberen
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
```

### Integreren in BlockEditor

Wrap elke block editor in een ErrorBoundary in `src/components/editor/BlockEditor.tsx`:

```tsx
import { ErrorBoundary } from '@/components/shared/ErrorBoundary';

export function BlockEditor({ block, sectionId }: BlockEditorProps) {
  const editor = renderBlockEditor(block, sectionId);
  return (
    <ErrorBoundary context={`${block.type} block`}>
      {editor}
    </ErrorBoundary>
  );
}
```

### Integreren op app niveau

Wrap `<MainPanel />` in `AppShell.tsx` met een top-level ErrorBoundary:

```tsx
<ErrorBoundary context="MainPanel" fallback={<AppCrashFallback />}>
  <MainPanel />
</ErrorBoundary>
```

Waar `AppCrashFallback` een "Reset rapport" knop toont die `useReportStore.getState().reset()` aanroept.

## Stap 5: API URL via Environment Variable

### Aanpassing in `src/services/api.ts`

```ts
// Voorheen: const API_BASE = 'http://localhost:8000';
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

### `.env` bestand

Maak `.env` (voor development):
```
VITE_API_URL=http://localhost:8000
```

Maak `.env.example` (voor documentatie):
```
# Backend API URL
VITE_API_URL=http://localhost:8000
```

### Vite env types

Maak `src/env.d.ts`:
```ts
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

### .gitignore

Voeg `.env` toe aan `.gitignore` (behoud `.env.example`).

## Stap 6: Build Warnings Oplossen

Run:
```bash
npm run build 2>&1
```

Bekijk alle warnings en los op:
- Unused imports → verwijderen
- Unused variables → verwijderen of prefixen met `_`
- Missing return types → toevoegen waar nodig
- Any implicit `any` → expliciet typen

**Doel:** `npm run build` produceert 0 warnings.

## Stap 7: Run Tests

```bash
npm run test
```

**Verwacht:** Alle tests slagen. Noteer het aantal tests en coverage percentage.

Optioneel:
```bash
npx vitest run --coverage
```

Genereer een coverage rapport en noteer de getallen.

## Regels

1. **Geen regressies** — bestaande functionaliteit moet identiek blijven
2. **Tests zijn isolated** — elke test reset de store (geen test-volgorde afhankelijkheid)
3. **Geen mocking van Zustand** — gebruik de echte store in tests (Zustand werkt prima in node)
4. **Error boundary vangt alleen** — het logt, toont fallback, maar gooit niet opnieuw
5. **API URL fallback** — als `VITE_API_URL` niet gezet is, gebruik `http://localhost:8000`
6. **Geen test voor API calls** — die vereisen een mock server, dat is voor later

## Verwachte output

### Nieuwe bestanden
- `src/test/setup.ts`
- `src/env.d.ts`
- `.env`
- `.env.example`
- `src/components/shared/ErrorBoundary.tsx`
- `src/utils/__tests__/conversion.test.ts`
- `src/stores/__tests__/reportStore.test.ts`

### Gewijzigde bestanden
- `package.json` — test dependencies + scripts
- `vite.config.ts` — test configuratie
- `src/services/api.ts` — VITE_API_URL
- `src/components/editor/BlockEditor.tsx` — ErrorBoundary wrapper
- `src/components/layout/AppShell.tsx` — top-level ErrorBoundary
- `.gitignore` — `.env` toevoegen

## Update na afloop

Werk `TODO.md` bij: P7 items afvinken.
Noteer in `TODO.md` het testresultaat:
```
## Test resultaten
- Tests: XX passing
- Coverage: XX%
```
