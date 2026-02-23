import { create } from "zustand";
import {
  adminApi,
  type AdminUser,
  type TenantInfo,
  type TenantTemplate,
  type BrandData,
  type CreateUserPayload,
  type UpdateUserPayload,
  type ApiError,
} from "@/services/api";

type AdminTab = "users" | "templates" | "brand";

interface AdminStore {
  // UI
  activeTab: AdminTab;
  setActiveTab: (tab: AdminTab) => void;

  // Users
  users: AdminUser[];
  usersLoading: boolean;
  usersError: string | null;
  loadUsers: () => Promise<void>;
  createUser: (payload: CreateUserPayload) => Promise<AdminUser | null>;
  updateUser: (id: string, payload: UpdateUserPayload) => Promise<AdminUser | null>;
  resetPassword: (id: string, newPassword: string) => Promise<boolean>;
  deleteUser: (id: string) => Promise<boolean>;

  // Tenants
  tenants: TenantInfo[];
  tenantsLoading: boolean;
  selectedTenant: string | null;
  loadTenants: () => Promise<void>;
  selectTenant: (tenant: string | null) => void;

  // Templates
  templates: TenantTemplate[];
  templatesLoading: boolean;
  loadTemplates: (tenant: string) => Promise<void>;
  uploadTemplate: (tenant: string, file: File) => Promise<boolean>;
  deleteTemplate: (tenant: string, filename: string) => Promise<boolean>;

  // Brand
  brandData: BrandData | null;
  brandLoading: boolean;
  loadBrand: (tenant: string) => Promise<void>;
  uploadBrand: (tenant: string, file: File) => Promise<boolean>;

  // General
  error: string | null;
  clearError: () => void;
}

function extractError(e: unknown): string {
  if (typeof e === "object" && e !== null && "detail" in e) {
    return (e as ApiError).detail;
  }
  return "Onbekende fout";
}

export const useAdminStore = create<AdminStore>()((set, get) => ({
  // UI
  activeTab: "users",
  setActiveTab: (tab) => set({ activeTab: tab }),

  // Users
  users: [],
  usersLoading: false,
  usersError: null,

  loadUsers: async () => {
    set({ usersLoading: true, usersError: null });
    try {
      const users = await adminApi.listUsers();
      set({ users, usersLoading: false });
    } catch (e) {
      set({ usersLoading: false, usersError: extractError(e) });
    }
  },

  createUser: async (payload) => {
    try {
      const user = await adminApi.createUser(payload);
      set((s) => ({ users: [...s.users, user], error: null }));
      return user;
    } catch (e) {
      set({ error: extractError(e) });
      return null;
    }
  },

  updateUser: async (id, payload) => {
    try {
      const user = await adminApi.updateUser(id, payload);
      set((s) => ({
        users: s.users.map((u) => (u.id === id ? user : u)),
        error: null,
      }));
      return user;
    } catch (e) {
      set({ error: extractError(e) });
      return null;
    }
  },

  resetPassword: async (id, newPassword) => {
    try {
      await adminApi.resetPassword(id, newPassword);
      set({ error: null });
      return true;
    } catch (e) {
      set({ error: extractError(e) });
      return false;
    }
  },

  deleteUser: async (id) => {
    try {
      await adminApi.deleteUser(id);
      set((s) => ({
        users: s.users.filter((u) => u.id !== id),
        error: null,
      }));
      return true;
    } catch (e) {
      set({ error: extractError(e) });
      return false;
    }
  },

  // Tenants
  tenants: [],
  tenantsLoading: false,
  selectedTenant: null,

  loadTenants: async () => {
    set({ tenantsLoading: true });
    try {
      const tenants = await adminApi.listTenants();
      set({ tenants, tenantsLoading: false });
    } catch (e) {
      set({ tenantsLoading: false, error: extractError(e) });
    }
  },

  selectTenant: (tenant) => set({ selectedTenant: tenant }),

  // Templates
  templates: [],
  templatesLoading: false,

  loadTemplates: async (tenant) => {
    set({ templatesLoading: true });
    try {
      const templates = await adminApi.listTemplates(tenant);
      set({ templates, templatesLoading: false });
    } catch (e) {
      set({ templatesLoading: false, error: extractError(e) });
    }
  },

  uploadTemplate: async (tenant, file) => {
    try {
      await adminApi.uploadTemplate(tenant, file);
      await get().loadTemplates(tenant);
      return true;
    } catch (e) {
      set({ error: extractError(e) });
      return false;
    }
  },

  deleteTemplate: async (tenant, filename) => {
    try {
      await adminApi.deleteTemplate(tenant, filename);
      set((s) => ({
        templates: s.templates.filter((t) => t.filename !== filename),
      }));
      return true;
    } catch (e) {
      set({ error: extractError(e) });
      return false;
    }
  },

  // Brand
  brandData: null,
  brandLoading: false,

  loadBrand: async (tenant) => {
    set({ brandLoading: true });
    try {
      const brandData = await adminApi.getBrand(tenant);
      set({ brandData, brandLoading: false });
    } catch (e) {
      set({ brandLoading: false, error: extractError(e) });
    }
  },

  uploadBrand: async (tenant, file) => {
    try {
      await adminApi.uploadBrand(tenant, file);
      await get().loadBrand(tenant);
      return true;
    } catch (e) {
      set({ error: extractError(e) });
      return false;
    }
  },

  // General
  error: null,
  clearError: () => set({ error: null }),
}));
