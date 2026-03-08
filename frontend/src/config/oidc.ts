/**
 * OIDC configuratie voor Authentik SSO.
 *
 * Haalt alle OIDC info op via de backend (/api/auth/oidc/config),
 * inclusief het authorization_endpoint (server-side discovery).
 * Fallback naar Vite env vars voor lokale dev.
 */

const API_BASE = import.meta.env.VITE_API_URL || "";

export interface OidcConfig {
  enabled: boolean;
  authority: string;
  clientId: string;
  redirectUri: string;
  scopes: string;
  authorizationEndpoint: string;
}

const DISABLED_CONFIG: OidcConfig = {
  enabled: false,
  authority: "",
  clientId: "",
  redirectUri: "",
  scopes: "",
  authorizationEndpoint: "",
};

/** Cached config na discovery */
let _cachedConfig: OidcConfig | null = null;
let _discoveryDone = false;

/**
 * Haal OIDC config op via de backend (die server-side discovery doet).
 * Fallback naar Vite env vars voor lokale dev zonder backend.
 */
export async function getOidcConfig(): Promise<OidcConfig> {
  // Cache hit
  if (_discoveryDone && _cachedConfig) {
    return _cachedConfig;
  }

  // Backend discovery (inclusief authorization_endpoint)
  try {
    const res = await fetch(`${API_BASE}/api/auth/oidc/config`);
    if (res.ok) {
      const data = await res.json();
      if (data.enabled) {
        _cachedConfig = {
          enabled: true,
          authority: (data.issuer as string).replace(/\/$/, ""),
          clientId: data.client_id,
          redirectUri: `${window.location.origin}/auth/callback`,
          scopes: "openid profile email openaec_profile",
          authorizationEndpoint: data.authorization_endpoint || "",
        };
        _discoveryDone = true;
        return _cachedConfig;
      }
    }
  } catch {
    // Backend niet bereikbaar — probeer statische fallback
  }

  // Statische fallback (Vite env vars, lokale dev)
  const authority = import.meta.env.VITE_OIDC_AUTHORITY;
  const clientId = import.meta.env.VITE_OIDC_CLIENT_ID;
  if (authority && clientId) {
    _cachedConfig = {
      enabled: true,
      authority: authority.replace(/\/$/, ""),
      clientId,
      redirectUri: `${window.location.origin}/auth/callback`,
      scopes: "openid profile email openaec_profile",
      authorizationEndpoint: "",  // Niet beschikbaar zonder discovery
    };
    _discoveryDone = true;
    return _cachedConfig;
  }

  _discoveryDone = true;
  return DISABLED_CONFIG;
}

/**
 * Check snel of OIDC mogelijk enabled is (zonder async fetch).
 * Gebruikt cached discovery resultaat.
 */
export function isOidcPossiblyEnabled(): boolean {
  if (_cachedConfig) return _cachedConfig.enabled;
  // Statische fallback check
  return !!(import.meta.env.VITE_OIDC_AUTHORITY && import.meta.env.VITE_OIDC_CLIENT_ID);
}
