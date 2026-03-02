/**
 * Brand configuratie — SINGLE SOURCE OF TRUTH voor alle huisstijl.
 *
 * REGEL: Geen hex kleur, bedrijfsnaam, of logo pad mag elders in de
 * codebase hardcoded staan. Alles komt uit dit bestand.
 *
 * Zie: DESIGN-SYSTEM.md voor het volledige OpenAEC design systeem.
 */

export interface BrandColors {
  /** Primaire accentkleur — Construction Amber (knoppen, links, focus rings) */
  primary: string;
  /** Primair donkere variant — Signal Orange (hover states) */
  primaryDark: string;
  /** Primair lichte variant (achtergronden, highlights) */
  primaryLight: string;
  /** Secundaire kleur — Warm Gold (badges, accenten) */
  secondary: string;
  secondaryDark: string;
  secondaryLight: string;
  /** Header achtergrondkleur — Deep Forge */
  headerBg: string;
  /** Header tekstkleur */
  headerText: string;
}

export interface BrandConfig {
  /** Korte naam prefix (wit deel in header) */
  namePrefix: string;
  /** Korte naam accent (amber deel in header) */
  nameAccent: string;
  /** Volledige organisatienaam (formulier placeholders, metadata) */
  fullName: string;
  /** Product naam (naast logo in header) */
  productName: string;
  /** Tagline */
  tagline: string;
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
  namePrefix: "Open",
  nameAccent: "AEC",
  fullName: "OpenAEC Foundation",
  productName: "Report Editor",
  tagline: "Build free. Build together.",

  colors: {
    primary: "#D97706",     // Construction Amber
    primaryDark: "#EA580C", // Signal Orange (hover)
    primaryLight: "#FEF3C7", // Warm amber tint
    secondary: "#F59E0B",   // Warm Gold
    secondaryDark: "#B45309",
    secondaryLight: "#FFFBEB",
    headerBg: "#36363E",    // Deep Forge
    headerText: "#FAFAF9",  // Blueprint White
  },
};

export default brand;
