import { create } from "zustand";
import { getAuthentikLoginUrl, getAuthentikLogoutUrl } from "@/config/oidc";

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
  /**
   * Vraag de huidige sessie op via /api/auth/me.
   * Caddy + Authentik forward_auth zorgt dat de backend de juiste
   * X-Authentik-Meta-* headers ontvangt voor browser-traffic.
   */
  checkSession: () => Promise<void>;
  /**
   * Start een nieuwe Authentik login door de browser naar de outpost
   * start-URL te sturen. Caddy fangt de callback op en zet de cookie.
   */
  loginWithSso: () => void;
  /**
   * Logout: roep eerst het backend ``/api/auth/logout`` aan om legacy
   * cookies (lokale dev) op te ruimen, en stuur de browser daarna naar
   * de Authentik sign-out endpoint zodat ook de outpost-cookie weg is.
   */
  logout: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  error: null,

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

  loginWithSso: () => {
    window.location.href = getAuthentikLoginUrl();
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
    // Hard redirect zodat ook de Authentik outpost cookie wordt gewist
    window.location.href = getAuthentikLogoutUrl();
  },

  clearError: () => set({ error: null }),
}));
