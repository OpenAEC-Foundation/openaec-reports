/**
 * Brand configuratie — SINGLE SOURCE OF TRUTH voor alle huisstijl.
 *
 * REGEL: Geen hex kleur, bedrijfsnaam, of logo pad mag elders in de
 * codebase hardcoded staan. Alles komt uit dit bestand.
 *
 * Nieuw bureau? Kopieer dit bestand, pas waarden aan, en switch
 * via VITE_BRAND env variable of runtime config.
 *
 * TODO: Dynamische brand selectie via VITE_BRAND env variable:
 *
 * const brandId = import.meta.env.VITE_BRAND || '3bm-cooperatie';
 * const brand = await import(`./brands/${brandId}.ts`);
 *
 * Of via een API endpoint: GET /api/brand-config
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
  fullName: '3BM Bouwkunde',
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
