import { useState } from "react";
import { useAuthStore } from "@/stores/authStore";
import brand from "@/config/brand";

export function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const login = useAuthStore((s) => s.login);
  const error = useAuthStore((s) => s.error);
  const isLoading = useAuthStore((s) => s.isLoading);
  const clearError = useAuthStore((s) => s.clearError);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await login(username, password);
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm">
        {/* Brand header */}
        <div className="mb-8 text-center">
          <h1
            className="text-3xl font-bold tracking-tight"
            style={{ color: brand.colors.secondary }}
          >
            {brand.name}
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
                backgroundColor: brand.colors.primary,
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.backgroundColor = brand.colors.primaryDark)
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.backgroundColor = brand.colors.primary)
              }
            >
              {isLoading ? "Bezig..." : "Inloggen"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
