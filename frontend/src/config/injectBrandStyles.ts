import brand from './brand';

/**
 * Converteert hex kleur (#RRGGBB) naar space-separated RGB string (R G B).
 * Dit formaat is vereist voor Tailwind's alpha-value modifier support:
 * `rgb(var(--brand-primary) / <alpha-value>)`.
 */
function hexToRgb(hex: string): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `${r} ${g} ${b}`;
}

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

  root.style.setProperty('--brand-primary', hexToRgb(c.primary));
  root.style.setProperty('--brand-primary-dark', hexToRgb(c.primaryDark));
  root.style.setProperty('--brand-primary-light', hexToRgb(c.primaryLight));
  root.style.setProperty('--brand-secondary', hexToRgb(c.secondary));
  root.style.setProperty('--brand-secondary-dark', hexToRgb(c.secondaryDark));
  root.style.setProperty('--brand-secondary-light', hexToRgb(c.secondaryLight));
  root.style.setProperty('--brand-header-bg', hexToRgb(c.headerBg));
  root.style.setProperty('--brand-header-text', hexToRgb(c.headerText));
}
