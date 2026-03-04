import { useState } from "react";
import { useAuthStore } from "@/stores/authStore";
import brand from "@/config/brand";

const MIN_PASSWORD_LENGTH = 8;

interface RegisterPageProps {
  onSwitchToLogin: () => void;
}

export function RegisterPage({ onSwitchToLogin }: RegisterPageProps) {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const register = useAuthStore((s) => s.register);
  const error = useAuthStore((s) => s.error);
  const isLoading = useAuthStore((s) => s.isLoading);
  const clearError = useAuthStore((s) => s.clearError);

  const passwordMismatch =
    confirmPassword.length > 0 && password !== confirmPassword;
  const passwordTooShort =
    password.length > 0 && password.length < MIN_PASSWORD_LENGTH;
  const canSubmit =
    username.length >= 3 &&
    email.includes("@") &&
    password.length >= MIN_PASSWORD_LENGTH &&
    password === confirmPassword &&
    !isLoading;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    const ok = await register(username, email, password, displayName);
    if (ok) {
      // Na registratie wordt user automatisch ingelogd via de store
      // App.tsx detecteert user !== null en toont de editor
    }
  }

  function handleFieldChange() {
    clearError();
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm">
        {/* Brand header */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold tracking-tight">
            <span style={{ color: brand.colors.headerBg }}>
              {brand.namePrefix}
            </span>
            <span style={{ color: brand.colors.primary }}>
              {brand.nameAccent}
            </span>
          </h1>
          <p className="mt-1 text-sm text-gray-500">{brand.productName}</p>
        </div>

        {/* Register card */}
        <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
          <h2 className="mb-6 text-lg font-semibold text-gray-900">
            Account aanmaken
          </h2>

          {error && (
            <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="reg-username"
                className="mb-1 block text-sm font-medium text-gray-700"
              >
                Gebruikersnaam *
              </label>
              <input
                id="reg-username"
                type="text"
                autoComplete="username"
                required
                minLength={3}
                value={username}
                onChange={(e) => {
                  setUsername(e.target.value);
                  handleFieldChange();
                }}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-transparent focus:outline-none focus:ring-2"
                onFocus={(e) =>
                  (e.target.style.boxShadow = `0 0 0 2px ${brand.colors.primary}40`)
                }
                onBlur={(e) => (e.target.style.boxShadow = "none")}
                placeholder="min. 3 tekens"
              />
            </div>

            <div>
              <label
                htmlFor="reg-email"
                className="mb-1 block text-sm font-medium text-gray-700"
              >
                E-mailadres *
              </label>
              <input
                id="reg-email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  handleFieldChange();
                }}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-transparent focus:outline-none focus:ring-2"
                onFocus={(e) =>
                  (e.target.style.boxShadow = `0 0 0 2px ${brand.colors.primary}40`)
                }
                onBlur={(e) => (e.target.style.boxShadow = "none")}
              />
            </div>

            <div>
              <label
                htmlFor="reg-displayname"
                className="mb-1 block text-sm font-medium text-gray-700"
              >
                Weergavenaam
              </label>
              <input
                id="reg-displayname"
                type="text"
                autoComplete="name"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-transparent focus:outline-none focus:ring-2"
                onFocus={(e) =>
                  (e.target.style.boxShadow = `0 0 0 2px ${brand.colors.primary}40`)
                }
                onBlur={(e) => (e.target.style.boxShadow = "none")}
                placeholder="Optioneel"
              />
            </div>

            <div>
              <label
                htmlFor="reg-password"
                className="mb-1 block text-sm font-medium text-gray-700"
              >
                Wachtwoord *
              </label>
              <input
                id="reg-password"
                type="password"
                autoComplete="new-password"
                required
                minLength={MIN_PASSWORD_LENGTH}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  handleFieldChange();
                }}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-transparent focus:outline-none focus:ring-2"
                onFocus={(e) =>
                  (e.target.style.boxShadow = `0 0 0 2px ${brand.colors.primary}40`)
                }
                onBlur={(e) => (e.target.style.boxShadow = "none")}
                placeholder={`min. ${MIN_PASSWORD_LENGTH} tekens`}
              />
              {passwordTooShort && (
                <p className="mt-1 text-xs text-amber-600">
                  Minimaal {MIN_PASSWORD_LENGTH} tekens
                </p>
              )}
            </div>

            <div>
              <label
                htmlFor="reg-confirm"
                className="mb-1 block text-sm font-medium text-gray-700"
              >
                Wachtwoord bevestigen *
              </label>
              <input
                id="reg-confirm"
                type="password"
                autoComplete="new-password"
                required
                value={confirmPassword}
                onChange={(e) => {
                  setConfirmPassword(e.target.value);
                  handleFieldChange();
                }}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-transparent focus:outline-none focus:ring-2"
                onFocus={(e) =>
                  (e.target.style.boxShadow = `0 0 0 2px ${brand.colors.primary}40`)
                }
                onBlur={(e) => (e.target.style.boxShadow = "none")}
              />
              {passwordMismatch && (
                <p className="mt-1 text-xs text-red-600">
                  Wachtwoorden komen niet overeen
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={!canSubmit}
              className="w-full rounded-lg px-4 py-2.5 text-sm font-medium text-white transition-colors disabled:cursor-not-allowed disabled:opacity-50"
              style={{ backgroundColor: brand.colors.primary }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.backgroundColor =
                  brand.colors.primaryDark)
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.backgroundColor =
                  brand.colors.primary)
              }
            >
              {isLoading ? "Bezig..." : "Registreren"}
            </button>
          </form>

          <p className="mt-4 text-center text-sm text-gray-500">
            Al een account?{" "}
            <button
              onClick={onSwitchToLogin}
              className="font-medium hover:underline"
              style={{ color: brand.colors.primary }}
            >
              Inloggen
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
