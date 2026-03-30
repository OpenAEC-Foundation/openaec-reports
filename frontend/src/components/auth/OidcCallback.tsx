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

      // Haal redirect_uri op (moet matchen met wat we bij de authorize stuurden)
      const config = await getOidcConfig();
      if (!config.enabled) {
        setError("OIDC is niet geconfigureerd");
        return;
      }

      // Server-side code exchange — backend doet de token request naar de IdP
      // (voorkomt CORS issues met het IdP token endpoint)
      const exchangeRes = await fetch(`${API_BASE}/api/auth/oidc/code-exchange`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          code,
          code_verifier: codeVerifier,
          redirect_uri: config.redirectUri,
        }),
      });

      if (!exchangeRes.ok) {
        const errBody = await exchangeRes.json().catch(() => ({}));
        setError(`SSO login mislukt: ${errBody.detail || exchangeRes.statusText}`);
        return;
      }

      // Verwijder query params VOOR checkSession — checkSession triggert een
      // synchrone React re-render (via useSyncExternalStore). Als pathname
      // dan nog /auth/callback is, rendert App opnieuw OidcCallback.
      window.history.replaceState({}, "", "/");

      // Sessie herladen — triggert re-render, App ziet pathname "/" + user → AppShell
      await checkSession();
    } catch (err) {
      setError(`Onverwachte fout: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-oaec-bg">
        <div className="w-full max-w-md">
          <div className="rounded-xl border border-oaec-border bg-oaec-bg-lighter p-8 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold text-oaec-danger">
              Inloggen mislukt
            </h2>
            <p className="mb-6 text-sm text-oaec-text-secondary">{error}</p>
            <button
              onClick={() => {
                window.history.replaceState({}, "", "/");
                window.location.reload();
              }}
              className="w-full rounded-lg bg-oaec-hover px-4 py-2 text-sm font-medium text-oaec-text-secondary hover:bg-oaec-hover-strong transition-colors"
            >
              Terug naar inlogpagina
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-oaec-bg">
      <div className="text-center">
        <svg
          className="mx-auto h-8 w-8 animate-spin text-oaec-text-faint"
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
        <p className="mt-3 text-sm text-oaec-text-muted">Inloggen via SSO...</p>
      </div>
    </div>
  );
}
