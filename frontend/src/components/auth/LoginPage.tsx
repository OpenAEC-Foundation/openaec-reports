import { useEffect } from "react";
import { useAuthStore } from "@/stores/authStore";
import brand from "@/config/brand";

/**
 * SSO splash screen — wordt alleen kort getoond als er een 401 vanuit
 * de API komt (bijv. lokale dev zonder ingelogde Authentik sessie).
 *
 * In productie zorgt Caddy + Authentik forward_auth ervoor dat
 * anonieme verzoeken al voor het laden van de SPA worden doorgestuurd
 * naar de Authentik login flow. Deze pagina is dus voornamelijk een
 * fallback voor lokale dev en cosmetische "log opnieuw in" knop.
 */
export function LoginPage() {
  const loginWithSso = useAuthStore((s) => s.loginWithSso);
  const error = useAuthStore((s) => s.error);

  // Auto-redirect naar Authentik wanneer er geen sessie is — dit is
  // praktisch instant in productie omdat Caddy al de outpost-redirect
  // doet, maar nuttig in lokale dev wanneer de SPA via Vite is gestart.
  useEffect(() => {
    const timer = window.setTimeout(() => {
      loginWithSso();
    }, 600);
    return () => window.clearTimeout(timer);
  }, [loginWithSso]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-oaec-bg">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold tracking-tight">
            <span className="text-oaec-text">{brand.namePrefix}</span>
            <span className="text-oaec-accent">{brand.nameAccent}</span>
          </h1>
          <p className="mt-1 text-sm text-oaec-text-secondary">{brand.productName}</p>
        </div>

        <div className="rounded-xl border border-oaec-border bg-oaec-bg-lighter p-8 shadow-sm">
          <h2 className="mb-6 text-lg font-semibold text-oaec-text">Doorsturen naar SSO…</h2>

          {error && (
            <div
              className="mb-4 rounded-lg px-4 py-3 text-sm"
              style={{ background: "var(--oaec-danger-soft)", color: "var(--oaec-danger)" }}
            >
              {error}
            </div>
          )}

          <p className="mb-4 text-sm text-oaec-text-secondary">
            Je wordt automatisch doorgestuurd naar de Authentik inlogpagina. Werkt dat niet?
          </p>

          <button
            onClick={loginWithSso}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-oaec-accent px-4 py-2.5 text-sm font-medium text-oaec-accent-text transition-colors hover:bg-oaec-accent-hover"
          >
            <svg
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15.75 5.25a3 3 0 013 3m3 0a6 6 0 01-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1121.75 8.25z"
              />
            </svg>
            Inloggen via SSO
          </button>
        </div>
      </div>
    </div>
  );
}
