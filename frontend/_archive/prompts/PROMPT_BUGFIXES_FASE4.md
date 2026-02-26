# Bugfixes Frontend Fase 4 (Metadata Forms)

Bekijk voor je begint:
- `src/components/forms/MetadataForm.tsx`
- `src/components/forms/CoverForm.tsx`
- `src/components/forms/ColofonForm.tsx`
- `src/components/forms/OptionsPanel.tsx`
- `src/components/forms/MetadataTabs.tsx`
- `src/stores/reportStore.ts`
- `src/utils/conversion.ts`
- `src/types/report.ts`

---

## Bug 1 — Stale local state na import/template load (ALLE FORMS)

**Ernst:** HIGH — formulieren tonen verouderde waarden

**Probleem:**
Alle forms gebruiken `useState(report.someField)` voor locale text inputs die on-blur committen. Het probleem: `useState()` initializer draait alleen bij mount. Als de report extern wijzigt — via `importJson()`, `loadTemplate()`, of `loadReport()` — worden de lokale states niet geüpdatet.

Scenario:
1. Gebruiker vult projectnaam "Brug A" in
2. Gebruiker importeert JSON met project "Kantoor B"
3. Store wordt correct bijgewerkt naar "Kantoor B"
4. MetadataForm toont nog steeds "Brug A" in het inputveld

**Getroffen bestanden:**
- `MetadataForm.tsx` — `local` state (project, project_number, client, author, date, version)
- `CoverForm.tsx` — `subtitle` state
- `ColofonForm.tsx` — `disclaimer` state
- `OptionsPanel.tsx` — `tocTitle` state

**Fix:**
Voeg een `useEffect` sync toe in elk form. Voorbeeld voor MetadataForm:

```tsx
// Na de useState declaratie:
useEffect(() => {
  setLocal({
    project: report.project,
    project_number: report.project_number,
    client: report.client,
    author: report.author,
    date: report.date,
    version: report.version,
  });
}, [report.project, report.project_number, report.client, report.author, report.date, report.version]);
```

Pas hetzelfde patroon toe voor:
- `CoverForm`: `useEffect(() => setSubtitle(cover.subtitle ?? ''), [cover.subtitle]);`
- `ColofonForm`: `useEffect(() => setDisclaimer(colofon.disclaimer ?? ''), [colofon.disclaimer]);`
- `OptionsPanel`: `useEffect(() => setTocTitle(toc.title ?? 'Inhoudsopgave'), [toc.title]);`

Vergeet niet `useEffect` toe te voegen aan de React imports.

Hetzelfde probleem bestaat in `RevisionRow` en `ExtraFieldRow` (sub-componenten). Daar hoeft dit NIET via useEffect — verplaats de `key` prop naar een stabiele identifier (zie Bug 5 hieronder), dan mount React het component opnieuw en wordt useState opnieuw geïnitialiseerd.

---

## Bug 2 — Revisie versie-sortering is string-based (ColofonForm.tsx)

**Ernst:** MEDIUM — sorteervolgorde incorrect bij versie 10+

**Probleem:**
```tsx
const sortedRevisions = [...revisions].sort((a, b) => {
  if (a.version > b.version) return -1;
  if (a.version < b.version) return 1;
  return 0;
});
```
JavaScript `>` en `<` operators op strings doen lexicografische vergelijking. Versie "10.0" wordt als kleiner beschouwd dan "2.0" want "1" < "2". Resultaat: revisie 10.0 verschijnt onderaan in plaats van bovenaan.

**Fix:**
Gebruik numerieke vergelijking:
```tsx
const sortedRevisions = [...revisions].sort((a, b) => {
  const numA = parseFloat(a.version) || 0;
  const numB = parseFloat(b.version) || 0;
  return numB - numA; // Nieuwste (hoogste) eerst
});
```

---

## Bug 3 — Extra field key overwrite bij duplicaat (CoverForm.tsx + ColofonForm.tsx)

**Ernst:** MEDIUM — data loss bij key-rename

**Probleem:**
In `updateExtraFieldKey()`:
```tsx
function updateExtraFieldKey(oldKey: string, newKey: string) {
  if (newKey === oldKey) return;
  const newFields: Record<string, string> = {};
  for (const [k, v] of Object.entries(extraFields)) {
    newFields[k === oldKey ? newKey : k] = v;
  }
  updateExtraFields(newFields);
}
```
Als de gebruiker een key hernoemt naar een key die al bestaat, wordt de bestaande entry stil overschreven. Bijv: key "Kenmerk" → "Opdrachtgever" terwijl "Opdrachtgever" al bestaat → die entry verdwijnt.

**Fix:**
Voorkom de rename als de nieuwe key al bestaat:
```tsx
function updateExtraFieldKey(oldKey: string, newKey: string) {
  if (newKey === oldKey) return;
  if (newKey in extraFields) return; // Duplicaat key — negeer
  const newFields: Record<string, string> = {};
  for (const [k, v] of Object.entries(extraFields)) {
    newFields[k === oldKey ? newKey : k] = v;
  }
  updateExtraFields(newFields);
}
```

Pas dit toe in BEIDE `CoverForm.tsx` en `ColofonForm.tsx`.

---

## Bug 4 — toReportDefinition dropt colofon met alleen disclaimer (conversion.ts)

**Ernst:** MEDIUM — disclaimer gaat verloren bij export

**Probleem:**
```tsx
if (report.colofon.enabled !== undefined || report.colofon.revision_history?.length) {
  def.colofon = report.colofon;
}
```
Deze conditie checkt alleen `enabled` en `revision_history`. Als de gebruiker alleen een disclaimer of extra_fields invult (zonder de enabled toggle te raken, en zonder revisies), wordt het hele colofon object niet geëxporteerd.

**Fix:**
```tsx
const hasColofonContent =
  report.colofon.enabled !== undefined ||
  (report.colofon.revision_history?.length ?? 0) > 0 ||
  !!report.colofon.disclaimer ||
  (report.colofon.extra_fields && Object.keys(report.colofon.extra_fields).length > 0);

if (hasColofonContent) {
  def.colofon = report.colofon;
}
```

---

## Bug 5 — ExtraFieldRow key prop gebaseerd op array index (CoverForm + ColofonForm)

**Ernst:** MEDIUM — stale local state na key-rename

**Probleem:**
```tsx
{entries.map(([key, value], idx) => (
  <ExtraFieldRow key={idx} ... />
))}
```
Wanneer een key wordt hernoemd, verandert `entries` volgorde niet, maar React hergebruikt de component op basis van de index-key. De `useState(fieldKey)` in `ExtraFieldRow` blijft op de oude waarde staan, waardoor het input veld de oude key toont ook al is de store correct bijgewerkt.

**Fix:**
Gebruik een combinatie van key + index als stabiele React key:
```tsx
{entries.map(([key, value], idx) => (
  <ExtraFieldRow key={`${idx}-${key}`} ... />
))}
```
Hierdoor forceert React een remount wanneer de key verandert, en wordt `useState` opnieuw geïnitialiseerd met de correcte waarde.

Pas toe in BEIDE `CoverForm.tsx` en `ColofonForm.tsx`.

Hetzelfde geldt voor `RevisionRow` in `ColofonForm.tsx`:
```tsx
{sortedRevisions.map((rev, sortedIdx) => {
  const origIdx = getOriginalIndex(sortedIdx);
  return (
    <RevisionRow
      key={`${origIdx}-${rev.version}`}
      ...
    />
  );
})}
```

---

## Bug 6 — duplicateBlock gebruikt Date.now() i.p.v. generateId() (reportStore.ts)

**Ernst:** LOW — potentiële ID-collisie, inconsistentie

**Probleem:**
```tsx
const duplicate = { ...rest, id: `${Date.now()}` } as EditorBlock;
```
Alle andere ID-generatie gebruikt `generateId()` (uit `utils/idGenerator.ts`). `Date.now()` heeft milliseconde-resolutie — als twee blocks snel achter elkaar worden gedupliceerd (programmatisch of via toetsenbord-shortcut), krijgen ze hetzelfde ID.

**Fix:**
```tsx
import { generateId } from '@/utils/idGenerator';

// In duplicateBlock:
const duplicate = { ...rest, id: generateId() } as EditorBlock;
```

---

## Refactor — ToggleSwitch en ExtraFieldRow naar shared components

**Ernst:** REFACTOR — geen bug, wel onderhoudslast

**Probleem:**
`ToggleSwitch` is gedupliceerd in `ColofonForm.tsx` en `OptionsPanel.tsx`. `ExtraFieldRow` is gedupliceerd in `CoverForm.tsx` en `ColofonForm.tsx`. Identieke code op twee plekken → divergentie-risico bij toekomstige wijzigingen.

**Fix:**
Maak shared componenten:

1. Maak `src/components/forms/ToggleSwitch.tsx`:
```tsx
interface ToggleSwitchProps {
  checked: boolean;
  onChange: () => void;
  label: string;
}

export function ToggleSwitch({ checked, onChange, label }: ToggleSwitchProps) {
  // Verplaats de bestaande implementatie hierheen
}
```

2. Maak `src/components/forms/ExtraFieldRow.tsx`:
```tsx
interface ExtraFieldRowProps {
  fieldKey: string;
  fieldValue: string;
  onKeyChange: (key: string) => void;
  onValueChange: (value: string) => void;
  onRemove: () => void;
}

export function ExtraFieldRow({ ... }: ExtraFieldRowProps) {
  // Verplaats de bestaande implementatie hierheen
}
```

3. Verwijder de lokale definities uit `ColofonForm.tsx`, `OptionsPanel.tsx`, en `CoverForm.tsx` en importeer vanuit de shared locatie.

---

## Verificatie

```bash
# Typecheck
npx tsc --noEmit

# Handmatige test stappen:
# 1. Vul MetadataForm in → klik "Export JSON" → importeer het JSON bestand → check dat alle velden correct laden (Bug 1)
# 2. Voeg 12 revisies toe (1.0 t/m 12.0) → check sorteervolgorde: 12.0 bovenaan (Bug 2)
# 3. Voeg extra veld "A" toe → hernoem naar bestaand veld "B" → check dat "B" niet overschreven wordt (Bug 3)
# 4. Vul alleen disclaimer in bij colofon → exporteer → check dat colofon in JSON staat (Bug 4)
# 5. Hernoem extra field key → check dat inputveld de nieuwe key toont (Bug 5)
# 6. Dupliceer snel twee blocks achter elkaar → check dat beide unieke IDs hebben (Bug 6)
```

## Samenvatting

| # | Bestand(en) | Bug | Ernst |
|---|-------------|-----|-------|
| 1 | MetadataForm, CoverForm, ColofonForm, OptionsPanel | Stale local state na import/load | HIGH |
| 2 | ColofonForm | Versie sort lexicografisch i.p.v. numeriek | MEDIUM |
| 3 | CoverForm, ColofonForm | Extra field key overwrite bij duplicaat | MEDIUM |
| 4 | conversion.ts | Colofon met alleen disclaimer wordt niet geëxporteerd | MEDIUM |
| 5 | CoverForm, ColofonForm | ExtraFieldRow/RevisionRow key={idx} → stale state | MEDIUM |
| 6 | reportStore.ts | Date.now() i.p.v. generateId() in duplicateBlock | LOW |
| R | CoverForm, ColofonForm, OptionsPanel | ToggleSwitch + ExtraFieldRow refactor naar shared | REFACTOR |
