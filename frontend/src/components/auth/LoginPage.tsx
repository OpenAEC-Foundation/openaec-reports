import { useState, useEffect } from "react";
import { useAuthStore } from "@/stores/authStore";
import brand from "@/config/brand";

interface LoginPageProps {
  onSwitchToRegister?: () => void;
}

export function LoginPage({ onSwitchToRegister }: LoginPageProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showLocalLogin, setShowLocalLogin] = useState(false);
  const login = useAuthStore((s) => s.login);
  const loginWithOidc = useAuthStore((s) => s.loginWithOidc);
  const error = useAuthStore((s) => s.error);
  const isLoading = useAuthStore((s) => s.isLoading);
  const clearError = useAuthStore((s) => s.clearError);
  const oidcEnabled = useAuthStore((s) => s.oidcEnabled);
  const checkOidcEnabled = useAuthStore((s) => s.checkOidcEnabled);

  useEffect(() => {
    checkOidcEnabled();
  }, [checkOidcEnabled]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await login(username, password);
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm">
        {/* Brand header */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold tracking-tight">
            <span style={{ color: brand.colors.headerBg }}>{brand.namePrefix}</span>
            <span style={{ color: brand.colors.primary }}>{brand.nameAccent}</span>
          </h1>
          <p className="mt-1 text-sm text-gray-500">{brand.productName}</p>
        </div>

        {/* Login card */}
        <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
          <h2 className="mb-6 text-lg font-semibold text-gray-900">Inloggen</h2>

          {error && (
            <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* SSO Login — primaire knop wanneer OIDC enabled */}
          {oidcEnabled && (
            <>
              <button
                onClick={loginWithOidc}
                disabled={isLoading}
                className="mb-4 flex w-full items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                style={{ backgroundColor: brand.colors.primary }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.backgroundColor = brand.colors.primaryDark)
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.backgroundColor = brand.colors.primary)
                }
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 5.25a3 3 0 013 3m3 0a6 6 0 01-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1121.75 8.25z" />
                </svg>
                {isLoading ? "Bezig..." : "Inloggen via SSO"}
              </button>

              {!showLocalLogin && (
                <button
                  onClick={() => setShowLocalLogin(true)}
                  className="w-full text-center text-xs text-gray-400 hover:text-gray-600 transition-colors"
                >
                  Of inloggen met gebruikersnaam
                </button>
              )}

              {showLocalLogin && (
                <div className="relative my-4">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-200" />
                  </div>
                  <div className="relative flex justify-center text-xs">
                    <span className="bg-white px-2 text-gray-400">of</span>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Lokale login — altijd tonen als OIDC niet enabled, anders achter toggle */}
          {(!oidcEnabled || showLocalLogin) && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label
                  htmlFor="username"
                  className="mb-1 block text-sm font-medium text-gray-700"
                >
                  Gebruikersnaam
                </label>
                <input
                  id="username"
                  type="text"
                  autoComplete="username"
                  required
                  value={username}
                  onChange={(e) => {
                    setUsername(e.target.value);
                    clearError();
                  }}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-transparent focus:outline-none focus:ring-2"
                  style={
                    {
                      "--tw-ring-color": brand.colors.primary,
                    } as React.CSSProperties
                  }
                  onFocus={(e) =>
                    (e.target.style.boxShadow = `0 0 0 2px ${brand.colors.primary}40`)
                  }
                  onBlur={(e) => (e.target.style.boxShadow = "none")}
                />
              </div>

              <div>
                <label
                  htmlFor="password"
                  className="mb-1 block text-sm font-medium text-gray-700"
                >
                  Wachtwoord
                </label>
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    clearError();
                  }}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-transparent focus:outline-none focus:ring-2"
                  onFocus={(e) =>
                    (e.target.style.boxShadow = `0 0 0 2px ${brand.colors.primary}40`)
                  }
                  onBlur={(e) => (e.target.style.boxShadow = "none")}
                />
              </div>

              <button
                type="submit"
                disabled={isLoading || !username || !password}
                className="w-full rounded-lg px-4 py-2.5 text-sm font-medium text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                style={{
                  backgroundColor: oidcEnabled ? brand.colors.headerBg : brand.colors.primary,
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.backgroundColor = brand.colors.primaryDark)
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.backgroundColor = oidcEnabled ? brand.colors.headerBg : brand.colors.primary)
                }
              >
                {isLoading ? "Bezig..." : "Inloggen"}
              </button>
            </form>
          )}

          {onSwitchToRegister && (
            <p className="mt-4 text-center text-sm text-gray-500">
              Nog geen account?{" "}
              <button
                onClick={onSwitchToRegister}
                className="font-medium hover:underline"
                style={{ color: brand.colors.primary }}
              >
                Registreer hier
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
