import { create } from "zustand";

const API_BASE = import.meta.env.VITE_API_URL || "";

export interface AuthUser {
  id: string;
  username: string;
  email: string;
  display_name: string;
  role: string;
  tenant: string;
  is_active: boolean;
}

interface AuthState {
  user: AuthUser | null;
  isLoading: boolean;
  error: string | null;
  checkSession: () => Promise<void>;
  login: (username: string, password: string) => Promise<boolean>;
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
}));
