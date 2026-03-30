import { useEffect } from "react";
import { useAuthStore } from "@/stores/authStore";
import brand from "@/config/brand";

export function LoginPage() {
  const loginWithOidc = useAuthStore((s) => s.loginWithOidc);
  const error = useAuthStore((s) => s.error);
  const isLoading = useAuthStore((s) => s.isLoading);
  const oidcEnabled = useAuthStore((s) => s.oidcEnabled);
  const checkOidcEnabled = useAuthStore((s) => s.checkOidcEnabled);

  useEffect(() => {
    checkOidcEnabled();
  }, [checkOidcEnabled]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-oaec-bg">
      <div className="w-full max-w-sm">
        {/* Brand header */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold tracking-tight">
            <span className="text-oaec-text">{brand.namePrefix}</span>
            <span className="text-oaec-accent">{brand.nameAccent}</span>
          </h1>
          <p className="mt-1 text-sm text-oaec-text-secondary">{brand.productName}</p>
        </div>

        {/* Login card */}
        <div className="rounded-xl border border-oaec-border bg-oaec-bg-lighter p-8 shadow-sm">
          <h2 className="mb-6 text-lg font-semibold text-oaec-text">Inloggen</h2>

          {error && (
            <div className="mb-4 rounded-lg px-4 py-3 text-sm" style={{ background: 'var(--oaec-danger-soft)', color: 'var(--oaec-danger)' }}>
              {error}
            </div>
          )}

          {oidcEnabled === false && (
            <div className="rounded-lg px-4 py-3 text-sm" style={{ background: 'var(--oaec-warning-soft)', color: 'var(--oaec-warning)' }}>
              SSO is niet geconfigureerd. Neem contact op met de beheerder.
            </div>
          )}

          {oidcEnabled !== false && (
            <button
              onClick={loginWithOidc}
              disabled={isLoading || !oidcEnabled}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-oaec-accent px-4 py-2.5 text-sm font-medium text-oaec-accent-text transition-colors hover:bg-oaec-accent-hover disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 5.25a3 3 0 013 3m3 0a6 6 0 01-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1121.75 8.25z" />
              </svg>
              {isLoading ? "Bezig..." : "Inloggen via SSO"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
