# Opdracht: Fase 4 — Metadata Forms, Cover/Colofon Forms & Template Selectie

## Context

Dit is `bm-reports-ui`, Fase 4. Fase 1-3 zijn compleet: AppShell, Sidebar met drag & drop secties, MainPanel met block editors voor alle 8 block types, JSON export/import. Lees `CLAUDE.md` voor de volledige architectuur.

De Zustand store heeft al alle benodigde actions: `setMetadata()`, `setCover()`, `setColofon()`, `setToc()`, `loadTemplate()`, `reset()`. Deze hoeven NIET aangepast te worden.

## Wat moet er gebouwd worden

### 1. MetadataForm — `src/components/forms/MetadataForm.tsx`

Formulier voor rapport-niveau metadata. Wordt getoond als **geen sectie** geselecteerd is (vervang de huidige "Selecteer een sectie" placeholder in MainPanel).

Velden (allen op basis van `EditorReport` type):

| Veld | Type | Input | Placeholder/opties |
|------|------|-------|--------------------|
| project | string | text input | "Projectnaam" |
| project_number | string | text input | "bijv. 2026-031" |
| client | string | text input | "Opdrachtgever" |
| author | string | text input | "3BM Bouwkunde" (default) |
| date | string | date input | vandaag als default |
| version | string | text input | "1.0" |
| status | Status | select | CONCEPT / DEFINITIEF / REVISIE |
| format | Format | radio buttons | A4 / A3 |
| orientation | Orientation | radio buttons | Portrait / Landscape |

Layout: gebruik een `max-w-2xl mx-auto` container met `space-y-4`. Groepeer gerelateerde velden:
- Rij 1: project (2/3 breedte) + project_number (1/3)
- Rij 2: client (1/2) + author (1/2)
- Rij 3: date (1/3) + version (1/3) + status (1/3)
- Rij 4: format (radio) + orientation (radio)

Gebruik dezelfde `inputClass` en `labelClass` als de block editors. Commit naar store via `setMetadata()` op `onBlur` voor text inputs, direct `onChange` voor selects en radios.

Toon een titel bovenaan: "Rapport instellingen" met een subtiele icoon.

### 2. CoverForm — `src/components/forms/CoverForm.tsx`

Formulier voor cover configuratie. Getoond als **tab of sectie** in het MetadataForm, of als apart panel. Kies voor een tabbed interface in het MetadataForm:

**Tab "Rapport"** = MetadataForm velden
**Tab "Voorblad"** = CoverForm
**Tab "Colofon"** = ColofonForm
**Tab "Opties"** = TOC + backcover toggles

CoverForm velden:

| Veld | Type | Input |
|------|------|-------|
| subtitle | string | text input — "Ondertitel op voorblad" |
| image | ImageSource | File upload zone (hergebruik patroon uit ImageEditor) |
| extra_fields | Record<string, string> | Dynamische key-value lijst |

De **extra_fields** editor:
- Toon bestaande key-value paren als twee inputs naast elkaar (label + waarde)
- "+" knop om een nieuw paar toe te voegen
- "×" knop per rij om te verwijderen
- Commit naar store via `setCover()` op elke blur/change

### 3. ColofonForm — `src/components/forms/ColofonForm.tsx`

Formulier voor colofon configuratie.

Velden:

| Veld | Type | Input |
|------|------|-------|
| enabled | boolean | toggle/checkbox — "Colofon pagina tonen" |
| extra_fields | Record<string, string> | Zelfde dynamische key-value editor als CoverForm |
| revision_history | RevisionEntry[] | Tabel-editor |
| disclaimer | string | textarea |

De **revision_history** editor:
- Tabel met 4 kolommen: Versie, Datum, Auteur, Omschrijving
- Elke rij is bewerkbaar (inline inputs)
- "+" knop onderaan om een nieuwe revisie toe te voegen (default: volgende versienummer, datum vandaag)
- "×" knop per rij om te verwijderen
- Sorteer op versie (nieuwste bovenaan)

Commit naar store via `setColofon()`.

### 4. OptionsPanel — `src/components/forms/OptionsPanel.tsx`

Kleine sectie met toggles:

| Veld | Input |
|------|-------|
| toc.enabled | toggle — "Inhoudsopgave tonen" |
| toc.title | text input — alleen zichtbaar als enabled |
| toc.max_depth | select (1/2/3) — alleen zichtbaar als enabled |
| backcover.enabled | toggle — "Achterblad tonen" |

### 5. MetadataTabs wrapper — `src/components/forms/MetadataTabs.tsx`

Wrapper component dat de 4 forms combineert in een tabbed interface:

```
[ Rapport ] [ Voorblad ] [ Colofon ] [ Opties ]
─────────────────────────────────────────────────
  <ActiveForm />
```

Tab styling: dezelfde stijl als de view mode tabs in AppShell (rounded pills, bg-gray-100 container).

### 6. Integratie in MainPanel.tsx

Vervang het huidige "Selecteer een sectie" lege state blok door `<MetadataTabs />`:

```tsx
// Huidige code:
if (!section) {
  return (
    <div className="flex flex-1 items-center justify-center">
      <div className="text-center">
        <p>Selecteer een sectie</p>
        ...
      </div>
    </div>
  );
}

// Nieuwe code:
if (!section) {
  return <MetadataTabs />;
}
```

### 7. Sidebar navigatie naar metadata

Voeg een klikbaar item toe **boven** de sectielijst in de Sidebar dat naar de metadata view navigeert:

```tsx
<button
  onClick={() => { setActiveSection(null); setActiveBlock(null); }}
  className={`w-full text-left px-2 py-2 rounded-md text-sm ... ${
    activeSection === null ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-50'
  }`}
>
  ⚙ Rapport instellingen
</button>
```

Plaats dit met een scheidingslijn boven "Secties".

### 8. Template Selectie Startscherm (OPTIONEEL — als tijd over)

Als het rapport leeg is (geen project naam, geen secties), toon een startscherm in plaats van MetadataTabs:

- Grid van template kaarten (3 kolommen)
- Templates: Constructief rapport, Daglichtberekening, Bouwbesluit toets, Leeg rapport
- Elke kaart: icoon + titel + korte beschrijving
- Klik → `loadTemplate(templateName)` + vul project naam in via een modal/inline input

Dit is een nice-to-have. Prioriteer de forms boven dit startscherm.

## Technische vereisten

1. **Zustand integratie:** Gebruik de bestaande store actions. GEEN nieuwe actions toevoegen tenzij echt nodig.
2. **TypeScript strict:** Gebruik types uit `@/types/report.ts`. De `Cover`, `Colofon`, `TocConfig` types zijn al gedefinieerd.
3. **Tailwind only:** Geen CSS modules.
4. **Geen nieuwe dependencies.** Gebruik native HTML elements voor toggles (styled checkboxes), date pickers, etc.
5. **Nederlandse labels** overal.
6. **Responsive binnen het main panel.** `max-w-2xl mx-auto` voor forms zodat ze niet te breed worden op grote schermen.

## Design richtlijnen

- Forms moeten **rustig en overzichtelijk** zijn — geen visuele overload
- Gebruik `space-y-4` tussen veldgroepen, `space-y-2` binnen groepen
- Zelfde input styling als block editors: `rounded border border-gray-200 px-2 py-1.5 text-sm focus:border-blue-300 focus:ring-2 focus:ring-blue-100 outline-none`
- Toggle styling: custom checkbox met `w-9 h-5` track, `w-4 h-4` thumb, `bg-blue-500` als aan
- Tab styling: `rounded-lg bg-gray-100 p-0.5` container met `rounded-md px-3 py-1.5 text-xs font-medium` per tab
- Sectie headers in forms: `text-sm font-semibold text-gray-700 mb-2` met optioneel een subtiele border-bottom

## File structuur na implementatie

```
src/components/
├── blocks/          # (bestaand — niet wijzigen)
├── editor/          # (bestaand — niet wijzigen)
├── forms/           # NIEUW
│   ├── MetadataTabs.tsx
│   ├── MetadataForm.tsx
│   ├── CoverForm.tsx
│   ├── ColofonForm.tsx
│   └── OptionsPanel.tsx
└── layout/
    ├── AppShell.tsx  # (niet wijzigen)
    ├── MainPanel.tsx # (kleine aanpassing: lege state → MetadataTabs)
    └── Sidebar.tsx   # (kleine aanpassing: rapport instellingen knop)
```

## Volgorde van implementatie

1. **MetadataForm** — de basis, meest waardevolle form
2. **MetadataTabs** — wrapper met tab navigatie (begin met alleen Rapport tab)
3. **Integratie** — MainPanel + Sidebar aanpassingen
4. **CoverForm** — voorblad configuratie (tweede tab)
5. **ColofonForm** — revisiehistorie tabel is het complexst
6. **OptionsPanel** — simpele toggles

Test na elke stap: `npm run dev`, laad `example_structural.json`, klik weg van secties, en verifieer dat:
- Forms verschijnen in het main panel
- Wijzigingen worden opgeslagen in de store
- JSON export bevat de gewijzigde metadata/cover/colofon
- Sidebar "Rapport instellingen" knop werkt
- Terugnavigeren naar een sectie toont de block editor weer
