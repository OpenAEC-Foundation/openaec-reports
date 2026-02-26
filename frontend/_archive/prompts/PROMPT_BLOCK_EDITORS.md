# Opdracht: Bouw inline Block Editors voor alle block types

## Context

Dit is `bm-reports-ui`, een React + TypeScript + Tailwind frontend die JSON produceert voor een PDF report generator. De shell staat er: AppShell, Sidebar met drag & drop secties, MainPanel met block-overzicht en BlockToolbox. Blocks zijn momenteel **read-only** (BlockSummary in MainPanel.tsx). De volgende stap is **inline editing** — als je op een block klikt, wordt het bewerkbaar.

Lees eerst `CLAUDE.md` voor de volledige architectuur en conventies.

## Wat moet er gebouwd worden

### 1. Block Editor Components

Maak een `src/components/blocks/` map met een editor component per block type:

| File | Block Type | Editor UI |
|------|-----------|-----------|
| `ParagraphEditor.tsx` | paragraph | `<textarea>` met auto-resize. Toon een kleine toolbar erboven met knoppen voor `<b>`, `<i>`, `<sub>`, `<sup>` die ReportLab XML tags invoegen rond de selectie. |
| `CalculationEditor.tsx` | calculation | Formulier met 6 velden: title (text), formula (monospace input), substitution (monospace input), result (text), unit (text), reference (text). Gebruik een compact 2-kolom grid layout. |
| `CheckEditor.tsx` | check | Formulier met: description (text), required_value (text), calculated_value (text), unity_check (number input, stap 0.01), limit (number input, default 1.0), reference (text). Toon een **live UC-bar** onderaan: horizontale balk die proportioneel vult op basis van unity_check/limit, groen als UC ≤ limit, rood als UC > limit. |
| `TableEditor.tsx` | table | Title input bovenaan. Daaronder een spreadsheet-achtige grid: editable header rij + data rijen. Knoppen: + kolom, + rij, - kolom (laatste), - rij (laatste). `<input>` per cel. Optioneel: style dropdown (default/minimal/striped). |
| `ImageEditor.tsx` | image | File upload zone (drag & drop + klik) die een bestand naar base64 converteert. URL input als alternatief. Preview thumbnail van het huidige beeld. Caption textarea. Width slider (50-210 mm). Alignment radio buttons (left/center/right). |
| `MapEditor.tsx` | map | Lat/lon inputs (number). Radius input (m). Layer checkboxes (percelen, bebouwing, bestemmingsplan, luchtfoto). Caption textarea. Width slider. **Geen kaartweergave nodig voor MVP** — gewoon de inputs. |
| `SpacerEditor.tsx` | spacer | Eén range slider: hoogte 1-50 mm, toont de huidige waarde in mm. |
| `PageBreakEditor.tsx` | page_break | Simpele tekst "Pagina-einde — geen opties". Eventueel een horizontale stippellijn als visuele hint. |

### 2. BlockEditor Wrapper Component

Maak `src/components/editor/BlockEditor.tsx`:

```tsx
// Props: block (EditorBlock), sectionId (string)
// - Rendert het juiste editor component op basis van block.type
// - Gebruikt een switch/map pattern
// - Elke editor ontvangt de block data + een onChange callback
// - onChange roept updateBlock aan op de Zustand store
```

### 3. Integratie in MainPanel.tsx

Wijzig `SortableBlockItem` in MainPanel.tsx:
- Als `isActive === true`: toon het `BlockEditor` component (bewerkbaar)
- Als `isActive === false`: toon het bestaande `BlockSummary` component (read-only)
- De transitie moet smooth zijn — geen layout shift. Gebruik een simpele conditional render.

## Technische vereisten

1. **Zustand integratie:** Elke editor roept `updateBlock(sectionId, blockId, updates)` aan bij wijzigingen. Gebruik `onChange` of `onBlur` — NIET elke keystroke een store update. Debounce of gebruik onBlur.
2. **TypeScript strict:** Geen `any`. Gebruik de discriminated union types uit `@/types/report.ts`. Cast met `as CalculationBlock` etc. waar nodig na type check.
3. **Tailwind only:** Geen CSS modules, geen inline styles behalve voor dynamische waarden (UC-bar breedte, spacer hoogte).
4. **Geen nieuwe dependencies** tenzij echt nodig. Gebruik native `<input>`, `<textarea>`, `<select>`.
5. **Nederlandse labels** voor de UI (formuliervelden, tooltips, placeholders).
6. **File upload (ImageEditor):** Gebruik `FileReader.readAsDataURL()` voor base64 conversie. Sla op als `ImageSourceBase64` object met `data`, `media_type`, en `filename`.

## Design richtlijnen

- Editors moeten **compact** zijn — ze verschijnen inline in de blocklist, niet in een modal.
- Gebruik `text-sm` als basis font size, `text-xs` voor labels.
- Input styling: `rounded border border-gray-200 px-2 py-1.5 text-sm focus:border-blue-300 focus:ring-2 focus:ring-blue-100 outline-none`
- Label styling: `text-xs font-medium text-gray-500 mb-1`
- Groepeer gerelateerde velden met `space-y-3` of een grid.
- De UC-bar in CheckEditor: `h-3 rounded-full bg-gray-100` als achtergrond, gevulde balk met `bg-green-500` of `bg-red-500`, transition-all.

## Volgorde van implementatie

Bouw ze in deze volgorde (simpel → complex), commit na elke editor:
1. SpacerEditor + PageBreakEditor (trivial, valideer de integratie)
2. CalculationEditor (formulier, meest voorkomend)
3. ParagraphEditor (textarea + markup toolbar)
4. CheckEditor (formulier + UC-bar visualisatie)
5. ImageEditor (file upload + preview)
6. TableEditor (grid editor, meest complex)
7. MapEditor (inputs only)

## Test

Na elke editor: start de dev server (`npm run dev`), laad het `example_structural.json` voorbeeld, klik op blocks van dat type, en verifieer dat:
- De editor verschijnt bij klik
- Wijzigingen worden opgeslagen in de store
- JSON export bevat de gewijzigde waarden
- Terugschakelen naar read-only toont de bijgewerkte data
