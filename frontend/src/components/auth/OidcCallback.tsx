import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/authStore";
import { getOidcConfig } from "@/config/oidc";
import { consumePkceVerifier, validateState } from "@/utils/pkce";

const API_BASE = import.meta.env.VITE_API_URL || "";

/**
 * OIDC Callback handler.
 *
 * Wordt getoond op /auth/callback nadat Authentik redirect terug.
 * Exchange de authorization code voor tokens via de IdP token endpoint,
 * stuurt de tokens naar de backend voor user sync, en redirect naar de app.
 */
export function OidcCallback() {
  const [error, setError] = useState<string | null>(null);
  const checkSession = useAuthStore((s) => s.checkSession);

  useEffect(() => {
    handleCallback();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleCallback() {
    try {
      const params = new URLSearchParams(window.location.search);
      const code = params.get("code");
      const state = params.get("state");
      const errorParam = params.get("error");

      if (errorParam) {
        setError(`Authentik fout: ${errorParam} — ${params.get("error_description") || ""}`);
        return;
      }

      if (!code) {
        setError("Geen authorization code ontvangen");
        return;
      }

      // Valideer state parameter (CSRF protection)
      if (state && !validateState(state)) {
        setError("State parameter mismatch — mogelijke CSRF aanval");
        return;
      }

      // Haal PKCE verifier op
      const codeVerifier = consumePkceVerifier();
      if (!codeVerifier) {
        setError("PKCE verifier niet gevonden — probeer opnieuw in te loggen");
        return;
      }

      // Exchange code voor tokens bij de IdP
      const config = await getOidcConfig();
      if (!config.enabled) {
        setError("OIDC is niet geconfigureerd");
        return;
      }

      // Haal token endpoint uit discovery
      const discoveryRes = await fetch(
        `${config.authority}/.well-known/openid-configuration`
      );
      if (!discoveryRes.ok) {
        setError("Kan OIDC discovery niet laden");
        return;
      }
      const discovery = await discoveryRes.json();
      const tokenEndpoint = discovery.token_endpoint;

      // Token request
      const tokenRes = await fetch(tokenEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          grant_type: "authorization_code",
          code,
          redirect_uri: config.redirectUri,
          client_id: config.clientId,
          code_verifier: codeVerifier,
        }),
      });

      if (!tokenRes.ok) {
        const errBody = await tokenRes.json().catch(() => ({}));
        setError(`Token exchange mislukt: ${errBody.error_description || tokenRes.statusText}`);
        return;
      }

      const tokens = await tokenRes.json();

      // Stuur tokens naar backend voor user sync + cookie
      const exchangeRes = await fetch(`${API_BASE}/api/auth/oidc/token-exchange`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          access_token: tokens.access_token,
          id_token: tokens.id_token,
        }),
      });

      if (!exchangeRes.ok) {
        const errBody = await exchangeRes.json().catch(() => ({}));
        setError(`Backend token exchange mislukt: ${errBody.detail || exchangeRes.statusText}`);
        return;
      }

      // Sessie herladen en redirect naar app
      await checkSession();

      // Verwijder query params en redirect naar root
      window.history.replaceState({}, "", "/");
    } catch (err) {
      setError(`Onverwachte fout: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="w-full max-w-md">
          <div className="rounded-xl border border-red-200 bg-white p-8 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold text-red-700">
              Inloggen mislukt
            </h2>
            <p className="mb-6 text-sm text-gray-600">{error}</p>
            <button
              onClick={() => {
                window.history.replaceState({}, "", "/");
                window.location.reload();
              }}
              className="w-full rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200 transition-colors"
            >
              Terug naar inlogpagina
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="text-center">
        <svg
          className="mx-auto h-8 w-8 animate-spin text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
        <p className="mt-3 text-sm text-gray-500">Inloggen via SSO...</p>
      </div>
    </div>
  );
}
