# P8: Brand Config Refactor — Huisstijl als Data, Niet Code

## Context

P6 heeft professionele branding toegevoegd, maar met een architectuurfout: alle huisstijl-waarden (kleuren, bedrijfsnaam, logo) zijn **hardcoded** in Tailwind config, componenten en CSS. Dit is exact het probleem dat in de backend is opgelost met brand YAML — de frontend moet hetzelfde principe volgen.

### Het probleem nu

- `tailwind.config.js` bevat 7 hardcoded hex waarden onder `3bm` namespace
- `AppShell.tsx` bevat hardcoded `"3BM"` en `"Report Editor"` tekst
- `MetadataForm.tsx` bevat `placeholder="3BM Bouwkunde"`
- `index.css` bevat hardcoded `#00B2A9` in focus-visible
- 19 referenties verspreid over 5 bestanden gebruiken `3bm-turquoise`, `3bm-slate` etc.

### Het principe

**Branding = data, niet code.** Als morgen een nieuw bureau wordt opgericht met andere kleuren, mag je **alleen een config bestand wijzigen** — geen Tailwind, geen componenten, geen CSS.

## Scope

1. Brand config bestand als single source of truth
2. CSS custom properties (runtime theming)
3. Tailwind config verwijst naar CSS vars
4. Alle componenten gebruiken generieke `brand-*` classes
5. Alle hardcoded tekst komt uit config
6. Bestaande tests blijven slagen

## Stap 0: Oriëntatie

Lees voordat je begint:
- `tailwind.config.js` — huidige hardcoded kleuren
- `src/index.css` — hardcoded focus kleur
- `src/components/layout/AppShell.tsx` — hardcoded "3BM" tekst en `3bm-*` classes
- `src/components/layout/Sidebar.tsx` — `3bm-*` class referenties
- `src/components/layout/MainPanel.tsx` — `3bm-*` class referenties
- `src/components/editor/BlockToolbox.tsx` — `3bm-*` hover class
- `src/components/forms/MetadataForm.tsx` — hardcoded "3BM Bouwkunde" placeholder
- `src/components/shared/ErrorBoundary.tsx` — check of hier brand refs in zitten
- `src/utils/__tests__/conversion.test.ts` — bestaande tests (moeten blijven slagen)
- `src/stores/__tests__/reportStore.test.ts` — bestaande tests

## Stap 1: Brand Config Bestand

Maak `src/config/brand.ts`:

```ts
/**
 * Brand configuratie — SINGLE SOURCE OF TRUTH voor alle huisstijl.
 *
 * REGEL: Geen hex kleur, bedrijfsnaam, of logo pad mag elders in de
 * codebase hardcoded staan. Alles komt uit dit bestand.
 *
 * Nieuw bureau? Kopieer dit bestand, pas waarden aan, en switch
 * via VITE_BRAND env variable of runtime config.
 */

export interface BrandColors {
  /** Primaire accentkleur (knoppen, links, focus rings, actieve states) */
  primary: string;
  /** Primair donkere variant (hover states) */
  primaryDark: string;
  /** Primair lichte variant (achtergronden, highlights) */
  primaryLight: string;
  /** Secundaire kleur (badges, accenten) */
  secondary: string;
  secondaryDark: string;
  secondaryLight: string;
  /** Header achtergrondkleur */
  headerBg: string;
  /** Header tekstkleur */
  headerText: string;
}

export interface BrandConfig {
  /** Korte naam (header logo) */
  name: string;
  /** Volledige bedrijfsnaam (formulier placeholders, metadata) */
  fullName: string;
  /** Product naam (naast logo in header) */
  productName: string;
  /** Kleurenpalet */
  colors: BrandColors;
  /** Optioneel logo */
  logo?: {
    /** Pad relatief aan public/ */
    src: string;
    /** Weergave breedte in px */
    width: number;
    alt: string;
  };
}

const brand: BrandConfig = {
  name: '3BM',
  fullName: '3BM Coöperatie',
  productName: 'Report Editor',

  colors: {
    primary: '#00B2A9',
    primaryDark: '#009690',
    primaryLight: '#E6F7F6',
    secondary: '#6B2D8B',
    secondaryDark: '#5A2476',
    secondaryLight: '#F3EBF7',
    headerBg: '#2D3748',
    headerText: '#FFFFFF',
  },

  // logo: {
  //   src: '/logo-3bm.svg',
  //   width: 32,
  //   alt: '3BM Logo',
  // },
};

export default brand;
```

## Stap 2: CSS Custom Properties Injectie

Maak `src/config/injectBrandStyles.ts`:

```ts
import brand from './brand';

/**
 * Injecteert brand kleuren als CSS custom properties op :root.
 * Wordt eenmalig aangeroepen bij app startup (main.tsx).
 *
 * Dit maakt het mogelijk om Tailwind classes te gebruiken die
 * verwijzen naar CSS vars — waardoor kleuren runtime configureerbaar zijn.
 */
export function injectBrandStyles(): void {
  const root = document.documentElement;
  const c = brand.colors;

  root.style.setProperty('--brand-primary', c.primary);
  root.style.setProperty('--brand-primary-dark', c.primaryDark);
  root.style.setProperty('--brand-primary-light', c.primaryLight);
  root.style.setProperty('--brand-secondary', c.secondary);
  root.style.setProperty('--brand-secondary-dark', c.secondaryDark);
  root.style.setProperty('--brand-secondary-light', c.secondaryLight);
  root.style.setProperty('--brand-header-bg', c.headerBg);
  root.style.setProperty('--brand-header-text', c.headerText);
}
```

Roep deze functie aan in `src/main.tsx`, **vóór** `ReactDOM.createRoot`:

```ts
import { injectBrandStyles } from './config/injectBrandStyles';

injectBrandStyles();

// ... bestaande ReactDOM.createRoot code
```

## Stap 3: Tailwind Config — CSS Vars

Vervang de hardcoded hex waarden in `tailwind.config.js` door verwijzingen naar CSS custom properties. Hernoem de namespace van `3bm` naar `brand`:

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: 'var(--brand-primary)',
          'primary-dark': 'var(--brand-primary-dark)',
          'primary-light': 'var(--brand-primary-light)',
          secondary: 'var(--brand-secondary)',
          'secondary-dark': 'var(--brand-secondary-dark)',
          'secondary-light': 'var(--brand-secondary-light)',
          'header-bg': 'var(--brand-header-bg)',
          'header-text': 'var(--brand-header-text)',
        },
      },
    },
  },
  plugins: [],
};
```

**Let op Tailwind opacity modifiers:** Classes zoals `bg-brand-primary/20` werken NIET out-of-the-box met CSS vars als raw hex. Tailwind heeft het color format nodig om opacity modifiers toe te passen. Gebruik de Tailwind `color()` helper of definieer kleuren als `rgb()` waarden. 

De eenvoudigste aanpak: gebruik `<alpha-value>` placeholder NIET en werk in plaats daarvan met expliciete opacity classes waar nodig (bijv. `bg-brand-primary bg-opacity-20` in plaats van `bg-brand-primary/20`). 

**Alternatief (beter):** Definieer CSS vars als space-separated RGB:

In `injectBrandStyles.ts`, converteer hex naar RGB:
```ts
function hexToRgb(hex: string): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `${r} ${g} ${b}`;
}

export function injectBrandStyles(): void {
  const root = document.documentElement;
  const c = brand.colors;

  root.style.setProperty('--brand-primary', hexToRgb(c.primary));
  root.style.setProperty('--brand-primary-dark', hexToRgb(c.primaryDark));
  root.style.setProperty('--brand-primary-light', hexToRgb(c.primaryLight));
  root.style.setProperty('--brand-secondary', hexToRgb(c.secondary));
  root.style.setProperty('--brand-secondary-dark', hexToRgb(c.secondaryDark));
  root.style.setProperty('--brand-secondary-light', hexToRgb(c.secondaryLight));
  root.style.setProperty('--brand-header-bg', hexToRgb(c.headerBg));
  root.style.setProperty('--brand-header-text', hexToRgb(c.headerText));
}
```

En in `tailwind.config.js`, gebruik `rgb()` met `<alpha-value>`:
```js
colors: {
  brand: {
    primary: 'rgb(var(--brand-primary) / <alpha-value>)',
    'primary-dark': 'rgb(var(--brand-primary-dark) / <alpha-value>)',
    'primary-light': 'rgb(var(--brand-primary-light) / <alpha-value>)',
    secondary: 'rgb(var(--brand-secondary) / <alpha-value>)',
    'secondary-dark': 'rgb(var(--brand-secondary-dark) / <alpha-value>)',
    'secondary-light': 'rgb(var(--brand-secondary-light) / <alpha-value>)',
    'header-bg': 'rgb(var(--brand-header-bg) / <alpha-value>)',
    'header-text': 'rgb(var(--brand-header-text) / <alpha-value>)',
  },
},
```

**Dit is de aanbevolen aanpak** — hierdoor werken classes zoals `bg-brand-primary/20` correct.

## Stap 4: Hernoem Alle Class References

Doorloop **alle** bestanden en vervang de oude `3bm-*` Tailwind classes door `brand-*`:

| Oud | Nieuw |
|-----|-------|
| `bg-3bm-turquoise` | `bg-brand-primary` |
| `bg-3bm-turquoise-dark` | `bg-brand-primary-dark` |
| `bg-3bm-turquoise-light` | `bg-brand-primary-light` |
| `text-3bm-turquoise` | `text-brand-primary` |
| `text-3bm-turquoise-dark` | `text-brand-primary-dark` |
| `border-3bm-turquoise` | `border-brand-primary` |
| `ring-3bm-turquoise/20` | `ring-brand-primary/20` |
| `hover:border-3bm-turquoise` | `hover:border-brand-primary` |
| `hover:bg-3bm-turquoise-dark` | `hover:bg-brand-primary-dark` |
| `hover:text-3bm-turquoise-dark` | `hover:text-brand-primary-dark` |
| `hover:bg-3bm-turquoise-light` | `hover:bg-brand-primary-light` |
| `bg-3bm-slate` | `bg-brand-header-bg` |

**Bestanden die aangepast moeten worden:**
- `src/components/layout/AppShell.tsx` — header bg, border, knoppen, tekst
- `src/components/layout/Sidebar.tsx` — active states, hover states
- `src/components/layout/MainPanel.tsx` — active block indicator, section headers, knoppen
- `src/components/editor/BlockToolbox.tsx` — hover states
- Eventuele andere bestanden waar `3bm-` voorkomt

**Zoek grondig:** Doe een project-brede zoek naar `3bm-` en `3bm` om niets te missen.

## Stap 5: Hardcoded Tekst Vervangen

### AppShell.tsx
Vervang hardcoded bedrijfsnaam en productnaam:

```tsx
import brand from '@/config/brand';

// In de header:
<span className="text-brand-primary font-bold text-lg tracking-tight">{brand.name}</span>
<span className="text-white/50 text-sm font-medium">{brand.productName}</span>
```

### MetadataForm.tsx
Vervang hardcoded placeholder:

```tsx
import brand from '@/config/brand';

// Bij het bedrijfsnaam veld:
placeholder={brand.fullName}
```

### Overige bestanden
Zoek project-breed naar `"3BM"`, `'3BM'`, `"3bm"` (case-insensitive) en vervang door `brand.*` referenties waar van toepassing.

**Uitzondering:** Tekst in test bestanden hoeft niet per se uit config te komen — tests mogen hardcoded verwachtingen bevatten.

## Stap 6: CSS Focus Ring

Vervang de hardcoded hex in `src/index.css`:

```css
/* Oud: */
*:focus-visible {
  outline: 2px solid #00B2A9;
  outline-offset: 2px;
}

/* Nieuw: */
*:focus-visible {
  outline: 2px solid rgb(var(--brand-primary));
  outline-offset: 2px;
}
```

## Stap 7: Env Variable voor Brand Selectie (Optioneel Setup)

Voeg `VITE_BRAND` toe aan de env types (`src/env.d.ts`):

```ts
interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_BRAND?: string;  // Toekomstig: brand config selectie
}
```

En voeg een comment toe in `brand.ts` dat uitlegt hoe dit in de toekomst kan werken:

```ts
/**
 * TODO: Dynamische brand selectie via VITE_BRAND env variable:
 *
 * const brandId = import.meta.env.VITE_BRAND || '3bm-cooperatie';
 * const brand = await import(`./brands/${brandId}.ts`);
 *
 * Of via een API endpoint: GET /api/brand-config
 */
```

## Stap 8: Verificatie

### 8a: Zoek naar resterende hardcoded waarden

Voer een project-brede zoek uit naar:
- `#00B2A9` (turquoise hex) — mag ALLEEN in `brand.ts` staan
- `#009690` (turquoise dark) — mag ALLEEN in `brand.ts` staan
- `#6B2D8B` (purple hex) — mag ALLEEN in `brand.ts` staan
- `#2D3748` (slate hex) — mag ALLEEN in `brand.ts` staan
- `3bm-` (oude Tailwind namespace) — mag NERGENS meer staan
- `"3BM"` of `'3BM'` (hardcoded naam) — mag ALLEEN in `brand.ts` staan

Als een van deze buiten `brand.ts` voorkomt: fixen.

### 8b: Tests

```bash
npm run test
```

Alle bestaande tests moeten slagen. De brand refactor raakt geen store logica of conversie functies, dus er zou niets mogen breken.

### 8c: Build

```bash
npm run build
```

0 errors, 0 warnings.

### 8d: Visuele check

```bash
npm run dev
```

1. ✅ Header toont correcte branding (naam + kleuren uit config)
2. ✅ Alle turquoise/brand kleuren zijn consistent
3. ✅ Focus rings zijn brand kleur
4. ✅ Hover states, active states werken correct
5. ✅ Opacity modifiers werken (bijv. `bg-brand-primary/20`)
6. ✅ Geen visuele regressie t.o.v. P6

### 8e: Proof of concept — verander brand

Tijdelijke test: verander `primary` in `brand.ts` naar `#FF0000` (rood). Refresh. Controleer dat ALLE accent kleuren in de hele app rood worden — header border, knoppen, focus rings, active states, etc. Als iets nog turquoise is, is er een hardcoded waarde gemist. Zet daarna terug naar `#00B2A9`.

## Regels

1. **Geen hex kleur buiten `brand.ts`** — alle kleuren via CSS custom properties
2. **Geen bedrijfsnaam buiten `brand.ts`** — lees altijd uit config
3. **Backward compatible** — alle functionaliteit identiek, alleen de bron van waarden verandert
4. **Tests moeten slagen** — `npm run test` groen
5. **Geen nieuwe npm packages** — dit is pure refactor
6. **Tailwind opacity modifiers moeten werken** — gebruik RGB + `<alpha-value>` patroon

## Verwachte output

- `src/config/brand.ts` — **NIEUW** (single source of truth)
- `src/config/injectBrandStyles.ts` — **NIEUW** (CSS var injectie)
- `src/main.tsx` — **GEWIJZIGD** (injectBrandStyles aanroep)
- `tailwind.config.js` — **GEWIJZIGD** (`3bm` → `brand` met CSS vars)
- `src/index.css` — **GEWIJZIGD** (focus ring via CSS var)
- `src/env.d.ts` — **GEWIJZIGD** (VITE_BRAND type)
- `src/components/layout/AppShell.tsx` — **GEWIJZIGD** (brand import + generieke classes)
- `src/components/layout/Sidebar.tsx` — **GEWIJZIGD** (generieke classes)
- `src/components/layout/MainPanel.tsx` — **GEWIJZIGD** (generieke classes)
- `src/components/editor/BlockToolbox.tsx` — **GEWIJZIGD** (generieke classes)
- `src/components/forms/MetadataForm.tsx` — **GEWIJZIGD** (brand.fullName placeholder)

## Update na afloop

Werk `TODO.md` bij: P8 item afvinken, noteer dat brand config systeem operationeel is.
