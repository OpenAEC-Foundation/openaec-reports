# Frontend Fase 5 — API Integratie

## Context

De backend draait op `http://localhost:8000` (FastAPI) en biedt deze endpoints:

| Endpoint | Methode | Request | Response |
|----------|---------|---------|----------|
| `/api/health` | GET | — | `{ status: "ok", version: "0.1.0" }` |
| `/api/templates` | GET | — | `{ templates: [{ name, report_type }] }` |
| `/api/templates/{name}/scaffold` | GET | — | ReportDefinition JSON (volledig scaffold) |
| `/api/brands` | GET | — | `{ brands: [{ name, slug }] }` |
| `/api/validate` | POST | ReportDefinition JSON | `{ valid: boolean, errors: [{ path, message }] }` |
| `/api/generate` | POST | ReportDefinition JSON | PDF binary (application/pdf) |

CORS is geconfigureerd voor `localhost:5173` en `localhost:5174`.

De frontend exporteert al JSON via `exportJson()` in reportStore → `toReportDefinition()` in conversion.ts.

## Scope

Deze fase voegt **5 onderdelen** toe:

1. API client service
2. API store (connectie-state, loading, errors)
3. Template selector met scaffold loading
4. Validate + Generate toolbar
5. PDF preview tab

---

## 1. API Client — `src/services/api.ts`

Maak een typed API client met foutafhandeling.

```typescript
// src/services/api.ts

const API_BASE = 'http://localhost:8000';

export interface ApiError {
  status: number;
  detail: string;
  type?: string;
}

export interface TemplateInfo {
  name: string;
  report_type: string;
}

export interface BrandInfo {
  name: string;
  slug: string;
}

export interface ValidationError {
  path: string;
  message: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
}

export interface HealthResponse {
  status: string;
  version: string;
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    const err: ApiError = { status: res.status, detail: body.detail ?? res.statusText, type: body.type };
    throw err;
  }
  return res.json();
}

export const api = {
  health: () => apiFetch<HealthResponse>('/api/health'),

  templates: () => apiFetch<{ templates: TemplateInfo[] }>('/api/templates').then(r => r.templates),

  scaffold: (name: string) => apiFetch<import('@/types/report').ReportDefinition>(`/api/templates/${encodeURIComponent(name)}/scaffold`),

  brands: () => apiFetch<{ brands: BrandInfo[] }>('/api/brands').then(r => r.brands),

  validate: (data: import('@/types/report').ReportDefinition) =>
    apiFetch<ValidationResult>('/api/validate', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  generate: async (data: import('@/types/report').ReportDefinition): Promise<Blob> => {
    const res = await fetch(`${API_BASE}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      const err: ApiError = { status: res.status, detail: body.detail ?? res.statusText, type: body.type };
      throw err;
    }
    return res.blob();
  },
};
```

### Vereisten

- `apiFetch` is generiek — gooit `ApiError` bij niet-200 responses
- `generate` retourneert een `Blob` (geen JSON parse!) — dit is een PDF binary
- `scaffold` retourneert een `ReportDefinition` direct (de backend retourneert dit al in correct schema formaat)
- Gebruik `encodeURIComponent` op template namen
- **Geen** axios dependency — gebruik native fetch

---

## 2. API Store — `src/stores/apiStore.ts`

Maak een Zustand store voor API-state, los van de report data.

```typescript
// src/stores/apiStore.ts

import { create } from 'zustand';
import { api, type TemplateInfo, type BrandInfo, type ValidationError, type ApiError } from '@/services/api';
import { useReportStore } from './reportStore';
import { toReportDefinition } from '@/utils/conversion';

interface ApiStore {
  // Connection
  connected: boolean;
  backendVersion: string | null;
  checking: boolean;

  // Templates & brands (geladen bij startup)
  templates: TemplateInfo[];
  brands: BrandInfo[];

  // Validation
  validationErrors: ValidationError[];
  isValidating: boolean;

  // Generation
  isGenerating: boolean;
  lastPdfUrl: string | null;      // Object URL voor preview/download
  lastPdfFilename: string | null;

  // General error
  error: string | null;

  // Actions
  checkHealth: () => Promise<void>;
  loadTemplatesAndBrands: () => Promise<void>;
  loadScaffold: (templateName: string) => Promise<void>;
  validateReport: () => Promise<boolean>;
  generatePdf: () => Promise<void>;
  downloadPdf: () => void;
  clearPdf: () => void;
  clearError: () => void;
}
```

### Implementatie-details

**`checkHealth()`**:
- Zet `checking: true` → call `api.health()` → zet `connected: true` + `backendVersion` → bij fout: `connected: false`
- Aanroepen bij app-startup (zie punt 5)

**`loadTemplatesAndBrands()`**:
- Call `api.templates()` en `api.brands()` parallel via `Promise.all()`
- Sla op in store
- Alleen aanroepen als `connected === true`

**`loadScaffold(templateName)`**:
- Call `api.scaffold(templateName)`
- Roep `useReportStore.getState().loadReport(scaffold)` aan om de editor te vullen
- Dit overschrijft het huidige rapport — toon later een bevestiging (niet in scope)

**`validateReport()`**:
- Haal JSON op: `toReportDefinition(useReportStore.getState().report)`
- Call `api.validate(json)`
- Sla `validationErrors` op
- Return `valid` boolean

**`generatePdf()`**:
- Zet `isGenerating: true`
- Haal JSON op: `toReportDefinition(useReportStore.getState().report)`
- Call `api.generate(json)` → ontvangt Blob
- Maak Object URL: `URL.createObjectURL(blob)`
- Als er een vorige `lastPdfUrl` bestaat: `URL.revokeObjectURL(lastPdfUrl)` eerst!
- Sla `lastPdfUrl` en `lastPdfFilename` op (filename uit report.project_number + project)
- Zet `isGenerating: false`

**`downloadPdf()`**:
- Guard: als `lastPdfUrl === null` → return
- Maak `<a>` element met `href=lastPdfUrl`, `download=lastPdfFilename`
- Trigger click

**`clearPdf()`**:
- `URL.revokeObjectURL(lastPdfUrl)` als niet null
- Reset `lastPdfUrl` en `lastPdfFilename` naar null

---

## 3. Template Selector — `src/components/forms/TemplateSelector.tsx`

Voeg een template dropdown toe aan MetadataForm.tsx, bovenaan het formulier (vóór de "Project" rij).

### Component: `TemplateSelector`

```tsx
// src/components/forms/TemplateSelector.tsx

// Props: geen (leest uit apiStore + reportStore)

// Gedrag:
// - Toont een <select> met alle templates uit apiStore.templates
// - Huidige waarde = report.template uit reportStore
// - Bij wijziging: roep apiStore.loadScaffold(newValue) aan
// - Toon een loading spinner als scaffold wordt geladen
// - Als apiStore.connected === false → toon "Backend niet beschikbaar" hint
//   en maak het veld een gewone text input (fallback)
```

### Integratie in MetadataForm

Voeg `<TemplateSelector />` toe als eerste element in de MetadataForm return, vóór de grid rows. Voeg een horizontale lijn toe (`<hr>`) eronder als visuele scheiding.

### Gedrag bij template wissel

- `loadScaffold()` laadt een volledig scaffold → `loadReport()` overschrijft alle velden
- De `useEffect` syncs in de forms (Bug 1 fix uit Fase 4) zorgen dat alle local state meteen bijwerkt
- Template wissel reset `isDirty` naar `false`

---

## 4. Toolbar Acties — Aanpassing `AppShell.tsx`

Pas de header in AppShell.tsx aan:

### Links: bestaande view mode tabs (ongewijzigd)

### Midden: connectie indicator

```tsx
// Klein bolletje + tekst
// connected === true  → groen bolletje + "Backend v{version}"
// connected === false → rood bolletje + "Offline"
// checking === true   → geel bolletje + "Verbinden..."
```

### Rechts: actie-knoppen (vervang huidige "Export JSON" knop)

Maak een groep van 4 knoppen:

| Knop | Label | Actie | Voorwaarde | Stijl |
|------|-------|-------|------------|-------|
| 1 | Export JSON | bestaande `handleExport()` | altijd | ghost (outline) |
| 2 | Valideer | `apiStore.validateReport()` | `connected` | ghost |
| 3 | Genereer PDF | `apiStore.generatePdf()` | `connected` | primary (blauw filled) |
| 4 | Download PDF | `apiStore.downloadPdf()` | `lastPdfUrl !== null` | success (groen filled) |

### Loading states

- "Valideer" knop: toon spinner + "Valideren..." wanneer `isValidating`
- "Genereer PDF" knop: toon spinner + "Genereren..." wanneer `isGenerating`
- Disable beide knoppen tijdens hun actie

### Validatie feedback

Na `validateReport()`:
- Als `valid === true`: toon kort een groene toast/melding "✓ Rapport is geldig" (3 sec auto-dismiss)
- Als `valid === false`: toon rode banner onder de toolbar met errors

Maak een eenvoudig `ValidationBanner` component:

```tsx
// Toont onder de header, enkel als validationErrors.length > 0
// Rode achtergrond, lijst van errors met path + message
// "✕ Sluiten" knop die validationErrors leegt
```

---

## 5. Preview Tab — Aanpassing `MainPanel.tsx`

De `viewMode === 'preview'` case is nu leeg. Vul deze in:

### Als `lastPdfUrl` bestaat:

Toon de PDF in een `<iframe>`:

```tsx
<iframe
  src={lastPdfUrl}
  className="w-full h-full border-0"
  title="PDF Preview"
/>
```

### Als `lastPdfUrl` niet bestaat:

Toon een placeholder:

```tsx
<div className="flex-1 flex flex-col items-center justify-center text-gray-400 gap-4">
  <svg ...> {/* document icon */} </svg>
  <p>Nog geen PDF gegenereerd</p>
  <button onClick={() => apiStore.generatePdf()}>
    Genereer PDF
  </button>
</div>
```

### Auto-switch naar preview

Na een succesvolle `generatePdf()` in de apiStore: roep `useReportStore.getState().setViewMode('preview')` aan. Dan ziet de gebruiker meteen het resultaat.

---

## 6. App Startup — Aanpassing `App.tsx`

Voeg een `useEffect` toe in `App.tsx` die bij mount:

1. `apiStore.checkHealth()` aanroept
2. Als connected: `apiStore.loadTemplatesAndBrands()` aanroept

```tsx
// In App.tsx
useEffect(() => {
  const init = async () => {
    await useApiStore.getState().checkHealth();
    if (useApiStore.getState().connected) {
      await useApiStore.getState().loadTemplatesAndBrands();
    }
  };
  init();
}, []);
```

---

## Bestandsoverzicht

| Bestand | Actie |
|---------|-------|
| `src/services/api.ts` | **NIEUW** — API client |
| `src/stores/apiStore.ts` | **NIEUW** — API state store |
| `src/components/forms/TemplateSelector.tsx` | **NIEUW** — Template dropdown |
| `src/components/layout/ValidationBanner.tsx` | **NIEUW** — Validatie foutmelding |
| `src/components/forms/MetadataForm.tsx` | **WIJZIG** — Voeg TemplateSelector toe bovenaan |
| `src/components/layout/AppShell.tsx` | **WIJZIG** — Toolbar met validate/generate/download + connectie indicator |
| `src/components/layout/MainPanel.tsx` | **WIJZIG** — Preview tab met iframe |
| `src/App.tsx` | **WIJZIG** — Startup health check |

## Niet in scope

- Bevestigingsdialoog bij template wissel (komt later)
- Real-time PDF preview bij elke wijziging (te zwaar)
- WebSocket live reload
- Authenticatie
- Error retry/backoff

## Test-checklist (handmatig)

1. **Startup**: App start → groen bolletje "Backend v0.1.0" (of rood "Offline" als backend niet draait)
2. **Template laden**: Selecteer "daylight" → formulier vult zich met scaffold defaults (subtitle = "Daglichtberekening")
3. **Valideer**: Klik "Valideer" → groen toast als geldig, rode banner met errors als ongeldig
4. **Genereer PDF**: Vul project + template in → klik "Genereer PDF" → spinner → switch naar Preview tab → PDF zichtbaar in iframe
5. **Download**: Klik "Download PDF" → browser download dialoog met juiste bestandsnaam
6. **Offline**: Stop backend → rood bolletje → "Genereer PDF" en "Valideer" knoppen disabled
7. **JSON export**: Bestaande export knop werkt nog steeds onafhankelijk van backend status
