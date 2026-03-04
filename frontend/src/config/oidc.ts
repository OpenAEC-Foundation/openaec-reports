/**
 * OIDC configuratie voor Authentik SSO.
 *
 * Gebruikt VITE_OIDC_AUTHORITY en VITE_OIDC_CLIENT_ID als primaire bron,
 * met fallback naar backend discovery via /api/auth/oidc/config.
 */

const API_BASE = import.meta.env.VITE_API_URL || "";

export interface OidcConfig {
  enabled: boolean;
  authority: string;
  clientId: string;
  redirectUri: string;
  scopes: string;
}

/** Statische config uit Vite environment variables */
function getStaticConfig(): OidcConfig | null {
  const authority = import.meta.env.VITE_OIDC_AUTHORITY;
  const clientId = import.meta.env.VITE_OIDC_CLIENT_ID;

  if (!authority || !clientId) {
    return null;
  }

  return {
    enabled: true,
    authority: authority.replace(/\/$/, ""),
    clientId,
    redirectUri: `${window.location.origin}/auth/callback`,
    scopes: "openid profile email openaec_profile",
  };
}

/** Cached config na discovery */
let _cachedConfig: OidcConfig | null = null;
let _discoveryDone = false;

/**
 * Haal OIDC config op — eerst statisch (env vars), daarna backend discovery.
 */
export async function getOidcConfig(): Promise<OidcConfig> {
  // Statische config heeft voorrang
  const staticCfg = getStaticConfig();
  if (staticCfg) {
    return staticCfg;
  }

  // Cache hit
  if (_discoveryDone && _cachedConfig) {
    return _cachedConfig;
  }

  // Backend discovery
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
        };
        _discoveryDone = true;
        return _cachedConfig;
      }
    }
  } catch {
    // Backend niet bereikbaar — OIDC disabled
  }

  _discoveryDone = true;
  return { enabled: false, authority: "", clientId: "", redirectUri: "", scopes: "" };
}

/**
 * Check snel of OIDC mogelijk enabled is (zonder async fetch).
 * Gebruikt env vars of cached discovery resultaat.
 */
export function isOidcPossiblyEnabled(): boolean {
  const staticCfg = getStaticConfig();
  if (staticCfg) return true;
  if (_cachedConfig) return _cachedConfig.enabled;
  return false;
}
