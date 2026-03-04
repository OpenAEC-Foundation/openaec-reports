import { create } from "zustand";
import { getOidcConfig } from "@/config/oidc";
import {
  generatePkceChallenge,
  storePkceVerifier,
  generateState,
} from "@/utils/pkce";

const API_BASE = import.meta.env.VITE_API_URL || "";

export interface AuthUser {
  id: string;
  username: string;
  email: string;
  display_name: string;
  role: string;
  tenant: string;
  is_active: boolean;
  phone: string;
  job_title: string;
  registration_number: string;
  company: string;
  auth_provider: string;
}

interface AuthState {
  user: AuthUser | null;
  isLoading: boolean;
  error: string | null;
  oidcEnabled: boolean | null;
  registrationEnabled: boolean | null;
  checkSession: () => Promise<void>;
  login: (username: string, password: string) => Promise<boolean>;
  register: (
    username: string,
    email: string,
    password: string,
    displayName?: string,
  ) => Promise<boolean>;
  loginWithOidc: () => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
  checkOidcEnabled: () => Promise<void>;
  checkRegistrationEnabled: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  error: null,
  oidcEnabled: null,
  registrationEnabled: null,

  checkSession: async () => {
    set({ isLoading: true, error: null });
    try {
      const res = await fetch(`${API_BASE}/api/auth/me`, {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        set({ user: data.user, isLoading: false });
      } else {
        set({ user: null, isLoading: false });
      }
    } catch {
      set({ user: null, isLoading: false });
    }
  },

  login: async (username: string, password: string) => {
    set({ error: null, isLoading: true });
    try {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ username, password }),
      });
      if (res.ok) {
        const data = await res.json();
        set({ user: data.user, isLoading: false, error: null });
        return true;
      }
      const body = await res.json().catch(() => ({ detail: "Login mislukt" }));
      set({ error: body.detail, isLoading: false });
      return false;
    } catch {
      set({ error: "Kan geen verbinding maken met de server", isLoading: false });
      return false;
    }
  },

  register: async (
    username: string,
    email: string,
    password: string,
    displayName?: string,
  ) => {
    set({ error: null, isLoading: true });
    try {
      const res = await fetch(`${API_BASE}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          username,
          email,
          password,
          display_name: displayName || "",
        }),
      });
      if (res.ok) {
        const data = await res.json();
        set({ user: data.user, isLoading: false, error: null });
        return true;
      }
      const body = await res
        .json()
        .catch(() => ({ detail: "Registratie mislukt" }));
      const detail = Array.isArray(body.detail)
        ? body.detail.join(", ")
        : body.detail;
      set({ error: detail, isLoading: false });
      return false;
    } catch {
      set({
        error: "Kan geen verbinding maken met de server",
        isLoading: false,
      });
      return false;
    }
  },

  loginWithOidc: async () => {
    try {
      const config = await getOidcConfig();
      if (!config.enabled) {
        set({ error: "SSO is niet geconfigureerd" });
        return;
      }

      // PKCE challenge genereren
      const pkce = await generatePkceChallenge();
      storePkceVerifier(pkce.codeVerifier);

      // State parameter voor CSRF protection
      const state = generateState();

      // Haal authorization endpoint uit discovery
      const discoveryRes = await fetch(
        `${config.authority}/.well-known/openid-configuration`
      );
      if (!discoveryRes.ok) {
        set({ error: "Kan OIDC discovery niet laden" });
        return;
      }
      const discovery = await discoveryRes.json();
      const authEndpoint = discovery.authorization_endpoint;

      // Redirect naar Authentik
      const params = new URLSearchParams({
        response_type: "code",
        client_id: config.clientId,
        redirect_uri: config.redirectUri,
        scope: config.scopes,
        state,
        code_challenge: pkce.codeChallenge,
        code_challenge_method: pkce.codeChallengeMethod,
      });

      window.location.href = `${authEndpoint}?${params.toString()}`;
    } catch {
      set({ error: "Kan SSO login niet starten" });
    }
  },

  logout: async () => {
    try {
      await fetch(`${API_BASE}/api/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
    } catch {
      // Altijd uitloggen, ook bij netwerk fout
    }
    set({ user: null, error: null });
  },

  clearError: () => set({ error: null }),

  checkOidcEnabled: async () => {
    try {
      const config = await getOidcConfig();
      set({ oidcEnabled: config.enabled });
    } catch {
      set({ oidcEnabled: false });
    }
  },

  checkRegistrationEnabled: async () => {
    try {
      const res = await fetch(
        `${API_BASE}/api/auth/registration-enabled`,
      );
      if (res.ok) {
        const data = await res.json();
        set({ registrationEnabled: data.enabled });
      } else {
        set({ registrationEnabled: false });
      }
    } catch {
      set({ registrationEnabled: false });
    }
  },
}));
