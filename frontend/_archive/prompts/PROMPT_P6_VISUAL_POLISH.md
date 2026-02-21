# P6: Visuele Polish — Professionele Look & Feel

## Context

De editor is functioneel compleet (fasen 1-7) maar ziet er nog uit als een prototype. Voor productiegebruik bij 3BM moet de UI professioneel aanvoelen: herkenbare branding, betere visuele hiërarchie, en gepolijste micro-interacties.

De huidige pijnpunten:
- **Header** is kaal wit — geen branding, geen herkenning als 3BM tool
- **Sidebar** heeft tekst-abbreviaties als block type indicators (`Aa`, `#`, `||`) — onduidelijk
- **Secties** zijn niet inklapbaar — bij grote rapporten raak je het overzicht kwijt
- **Empty states** zijn tekst-only — geen visuele hints
- **Toast notificaties** zijn inline banners die de layout verschuiven

## Scope

1. Branded header met 3BM kleuren en logo
2. SVG iconen voor block types (sidebar + toolbox)
3. Inklapbare secties in sidebar
4. Verbeterde empty states met illustraties
5. Floating toast notificaties (positie fixed, geen layout shift)
6. Subtiele verbeteringen (hover states, transitions, focus rings)

## Stap 0: Oriëntatie

Lees voordat je begint:
- `src/components/layout/AppShell.tsx` — huidige header + toast logica
- `src/components/layout/Sidebar.tsx` — sectie-items, block type indicators
- `src/components/layout/MainPanel.tsx` — empty states, BlockSummary
- `src/components/editor/BlockToolbox.tsx` — block type knoppen
- `tailwind.config.js` — huidige Tailwind configuratie

## Stap 1: Tailwind Extend — 3BM Kleuren

Voeg de 3BM huisstijlkleuren toe aan `tailwind.config.js`:

```js
module.exports = {
  theme: {
    extend: {
      colors: {
        '3bm': {
          turquoise: '#00B2A9',    // Primaire brandkleur
          'turquoise-dark': '#009690',
          'turquoise-light': '#E6F7F6',
          purple: '#6B2D8B',       // Secundaire brandkleur
          'purple-dark': '#5A2476',
          'purple-light': '#F3EBF7',
          slate: '#2D3748',        // Tekst/header achtergrond
        },
      },
    },
  },
};
```

## Stap 2: Branded Header

Vervang de kale witte header in `AppShell.tsx` met een donkere branded header:

**Design:**
- Achtergrond: donker slate (`bg-3bm-slate`) met turquoise accent lijn onderaan
- Links: "3BM" tekst-logo in turquoise + "Report Editor" in wit
- Midden: view mode tabs (witte tekst, actieve tab met turquoise indicator)
- Rechts: actieknoppen (gedempte witte tekst, primary button in turquoise)
- Connectie-indicator verhuist naar linksonder in sidebar footer

**Implementatie richting:**
```tsx
<header className="flex h-12 shrink-0 items-center justify-between bg-3bm-slate px-4 border-b-2 border-3bm-turquoise">
  {/* Logo */}
  <div className="flex items-center gap-3">
    <span className="text-3bm-turquoise font-bold text-lg tracking-tight">3BM</span>
    <span className="text-white/60 text-sm font-medium">Report Editor</span>
  </div>
  {/* ... tabs en knoppen in witte/turquoise styling ... */}
</header>
```

**Pas de view mode tabs aan:** Gebruik `text-white/60` voor inactief, `text-white bg-white/10` voor actief.

**Pas de actieknoppen aan:**
- "Import JSON" en "Export JSON": `border-white/20 text-white/70 hover:bg-white/10`
- "Valideer": `border-white/20 text-white/70`
- "Genereer PDF": `bg-3bm-turquoise text-white hover:bg-3bm-turquoise-dark`
- "Download PDF": `bg-green-500 text-white`

**Undo/Redo knoppen:** `text-white/40 hover:text-white/70`

## Stap 3: Block Type Iconen

Maak `src/components/shared/BlockIcons.tsx` met inline SVG iconen voor alle block types. Gebruik simpele, herkenbare 16x16 iconen:

| Block type | Icoon concept |
|------------|--------------|
| `paragraph` | Horizontale tekstregels (≡) |
| `calculation` | Functie fx symbool |
| `check` | Vinkje in vierkant (☑) |
| `table` | Grid/raster (田) |
| `image` | Landschap met zon (🖼) |
| `map` | Pin/marker (📍) |
| `spacer` | Verticale pijlen uit elkaar (↕) |
| `page_break` | Horizontale stippellijn met pijl (⤓) |
| `raw_flowable` | Code haakjes (</>) |

**Implementatie:**
```tsx
interface BlockIconProps {
  type: string;
  className?: string;
}

export function BlockIcon({ type, className = 'h-4 w-4' }: BlockIconProps) {
  switch (type) {
    case 'paragraph':
      return (
        <svg className={className} viewBox="0 0 16 16" fill="currentColor">
          <rect x="1" y="2" width="14" height="1.5" rx="0.5" />
          <rect x="1" y="6" width="14" height="1.5" rx="0.5" />
          <rect x="1" y="10" width="10" height="1.5" rx="0.5" />
        </svg>
      );
    // ... andere types
  }
}
```

**Vervang** de tekst-abbreviaties in `Sidebar.tsx` (de `BLOCK_TYPE_ICONS` map) en `BlockToolbox.tsx` door `<BlockIcon type={...} />`.

## Stap 4: Inklapbare Secties in Sidebar

Voeg een collapse/expand functie toe aan secties in de sidebar:

**Gedrag:**
- Standaard: secties zijn ingeklapt (tonen alleen titel + block count)
- Klik op sectie: selecteer en klap uit
- Klik op chevron: toggle collapse zonder te selecteren
- Actieve sectie is altijd uitgeklapt

**UI:**
- Voeg een chevron icoon (▸/▾) toe vóór de drag handle
- Ingeklapt: toon block count badge naast titel
- Uitgeklapt: toon individuele block type iconen (zoals nu)

**State:** Gebruik lokale `collapsedSections: Set<string>` state in `Sidebar.tsx` (niet in store — dit is pure UI state).

```tsx
const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

function toggleCollapse(id: string) {
  setCollapsed(prev => {
    const next = new Set(prev);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    return next;
  });
}
```

**Automatisch uitklappen:** wanneer `activeSection` wijzigt, verwijder die sectie uit `collapsed`.

## Stap 5: Empty States Verbeteren

Vervang de tekst-only empty states door visuele hints:

### Sectie zonder blocks (`MainPanel.tsx`)
```tsx
<div className="flex flex-col items-center justify-center py-16 text-center">
  <div className="rounded-full bg-gray-100 p-4 mb-4">
    <svg className="h-8 w-8 text-gray-400" ...> {/* document icon */} </svg>
  </div>
  <p className="text-sm font-medium text-gray-500">Geen content blocks</p>
  <p className="text-xs text-gray-400 mt-1">
    Gebruik de toolbar hieronder om tekst, berekeningen of tabellen toe te voegen
  </p>
</div>
```

### Geen secties (`Sidebar.tsx`)
Vergelijkbaar patroon met een plus-icoon in een cirkel.

### Preview zonder PDF
Al goed, maar voeg een subtiele pulserende animatie toe aan de "Genereer PDF" knop:
```tsx
className="... animate-pulse"
```
(Alleen als er content is maar nog geen PDF gegenereerd.)

## Stap 6: Floating Toast Notificaties

Verplaats de toast notificaties van inline (layout-shifting) naar fixed positie.

**Huidige situatie:** Toast is een `<div>` in de header flow die de layout verschuift.

**Nieuwe situatie:** Toast wordt absoluut gepositioneerd rechtsboven:

```tsx
{/* In AppShell.tsx, buiten de header flow */}
{toast && (
  <div className="fixed top-14 right-4 z-50 animate-slide-in-right">
    <div className={`rounded-lg shadow-lg px-4 py-3 flex items-center gap-2 ${
      toast.type === 'success'
        ? 'bg-green-600 text-white'
        : 'bg-red-600 text-white'
    }`}>
      {toast.type === 'success' ? '✓' : '✕'}
      <span className="text-sm font-medium">{toast.message}</span>
    </div>
  </div>
)}
```

Voeg de slide-in animatie toe aan `index.css`:
```css
@keyframes slide-in-right {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
.animate-slide-in-right {
  animation: slide-in-right 0.3s ease-out;
}
```

Verwijder de oude inline toast en error banners uit de header flow.

## Stap 7: Micro-verbeteringen

### Focus rings
Voeg een consistente focus ring toe aan alle interactieve elementen:
```css
/* In index.css */
*:focus-visible {
  outline: 2px solid #00B2A9;
  outline-offset: 2px;
}
```

### Block hover states
Voeg een subtiele schaduw-verhoging toe bij hover op blocks in `MainPanel.tsx`:
```tsx
className="... hover:shadow-md transition-shadow"
```

### Active block indicator
Maak de actieve block indicator prominenter met turquoise in plaats van blauw:
```tsx
// Van: 'border-blue-300 ring-2 ring-blue-100'
// Naar: 'border-3bm-turquoise ring-2 ring-3bm-turquoise/20'
```

### Sidebar width
De sidebar is nu `w-72` (288px). Dit is goed voor de meeste gevallen.
Voeg een resize handle toe (optioneel — alleen als tijd over):

```tsx
<div className="w-1 cursor-col-resize hover:bg-3bm-turquoise/30 transition-colors" />
```

## Stap 8: Build + Visuele Check

```bash
npm run build
```

**Verwacht:** 0 errors, 0 warnings.

Open `npm run dev` en controleer visueel:
1. ✅ Header toont 3BM branding in turquoise op donkere achtergrond
2. ✅ View mode tabs zijn wit op donker, actieve tab heeft turquoise indicator
3. ✅ Actieknoppen passen bij het donkere kleurenschema
4. ✅ Block iconen zijn SVG, herkenbaar en consistent
5. ✅ Secties in sidebar zijn inklapbaar
6. ✅ Empty states hebben visuele hints (icoon + beschrijving)
7. ✅ Toasts verschijnen rechts bovenin zonder layout shift
8. ✅ Focus rings zijn turquoise
9. ✅ Geen visuele regressies in bestaande functionaliteit

## Regels

1. **Alleen Tailwind** — geen CSS modules, geen styled-components, geen inline style objects
2. **Geen externe UI libraries** — geen Headless UI, Radix, of andere component libraries. Alles custom.
3. **Geen nieuwe npm packages** voor iconen — alle iconen zijn inline SVG
4. **Backward compatible** — alle bestaande functionaliteit moet identiek blijven werken
5. **Geen wijzigingen aan store of API** — dit is een pure UI/CSS taak
6. **3BM kleurenpalet:** turquoise (#00B2A9), paars (#6B2D8B), donker slate (#2D3748)

## Verwachte output

- `tailwind.config.js` — GEWIJZIGD (3BM kleuren)
- `src/index.css` — UITGEBREID (animaties, focus ring)
- `src/components/shared/BlockIcons.tsx` — NIEUW
- `src/components/layout/AppShell.tsx` — GEWIJZIGD (branded header, floating toast)
- `src/components/layout/Sidebar.tsx` — GEWIJZIGD (SVG iconen, collapsible secties)
- `src/components/layout/MainPanel.tsx` — GEWIJZIGD (SVG iconen, empty states, hover)
- `src/components/editor/BlockToolbox.tsx` — GEWIJZIGD (SVG iconen)

## Update na afloop

Werk `TODO.md` bij: P6 items afvinken.
