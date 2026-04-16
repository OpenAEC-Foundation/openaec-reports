/**
 * Authentik helpers — overgebleven na migratie naar forward_auth.
 *
 * De Caddy + Authentik proxy outpost regelt sinds april 2026 alle
 * browser-authenticatie. Deze module bevat enkel nog UI-helpers
 * (account-link en logout-redirect) zodat de frontend niets meer
 * weet van OIDC discovery, PKCE of token-exchange.
 */

const API_BASE = import.meta.env.VITE_API_URL || "";

/**
 * Genereer de Authentik outpost start-URL voor een (her)login.
 *
 * Caddy stuurt anonieme requests al automatisch door, maar deze helper
 * is bruikbaar voor expliciete "log opnieuw in" knoppen of het opvangen
 * van een 401 vanuit de API.
 */
export function getAuthentikLoginUrl(returnTo?: string): string {
  const target = returnTo || window.location.href;
  return `/outpost.goauthentik.io/start?rd=${encodeURIComponent(target)}`;
}

/**
 * Authentik sign-out endpoint — wist de outpost-cookie en redirect
 * doorgaans terug naar de Authentik login flow.
 */
export function getAuthentikLogoutUrl(): string {
  return "/outpost.goauthentik.io/sign_out";
}

/**
 * Probeer de Authentik instance-URL af te leiden uit ``VITE_AUTHENTIK_URL``
 * (compile-time). Productie deployments zetten deze env var tijdens de
 * Vite build (zie ``frontend/.env.production``).
 *
 * Returns:
 *   "https://auth.open-aec.com/if/user/" indien geconfigureerd, anders null.
 */
export function getAuthentikUserUrl(): string | null {
  const raw = import.meta.env.VITE_AUTHENTIK_URL || "";
  if (!raw) return null;
  try {
    const url = new URL(raw);
    return `${url.origin}/if/user/`;
  } catch {
    return null;
  }
}

/**
 * Vraag het backend ``/api/auth/me`` endpoint zodat de frontend snel
 * kan checken of de Authentik headers aankwamen. Returnt ``null`` bij
 * een 401 — caller kan dan ``getAuthentikLoginUrl()`` aanroepen.
 */
export async function fetchSession(): Promise<unknown | null> {
  try {
    const res = await fetch(`${API_BASE}/api/auth/me`, {
      credentials: "include",
    });
    if (!res.ok) return null;
    const body = await res.json();
    return body.user ?? null;
  } catch {
    return null;
  }
}
