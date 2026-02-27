import { create } from "zustand";
import {
  adminApi,
  type AdminUser,
  type TenantInfo,
  type TenantTemplate,
  type TenantAsset,
  type AssetCategory,
  type BrandData,
  type BrandExtractionResult,
  type BrandExtractionData,
  type CreateUserPayload,
  type UpdateUserPayload,
  type CreateTenantPayload,
  type ApiError,
} from "@/services/api";

type AdminTab = "tenants" | "users" | "templates" | "brand" | "brand-wizard";

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
  createTenant: (payload: CreateTenantPayload) => Promise<TenantInfo | null>;
  deleteTenant: (name: string) => Promise<boolean>;
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

  // Assets (stationery, logos, fonts)
  stationeryFiles: TenantAsset[];
  logoFiles: TenantAsset[];
  fontFiles: TenantAsset[];
  assetsLoading: boolean;
  loadAssets: (tenant: string, category: AssetCategory) => Promise<void>;
  loadAllAssets: (tenant: string) => Promise<void>;
  uploadAsset: (
    tenant: string,
    category: AssetCategory,
    file: File
  ) => Promise<boolean>;
  deleteAsset: (
    tenant: string,
    category: AssetCategory,
    filename: string
  ) => Promise<boolean>;

  // Brand Extraction Wizard
  extractionStep: number; // 0=inactive, 1=upload, 2=review, 3=prompt, 4=finalize
  extractionResult: BrandExtractionResult | null;
  editedExtraction: BrandExtractionData | null;
  promptPackage: string | null;
  extractionLoading: boolean;
  setExtractionStep: (step: number) => void;
  startExtraction: (
    tenant: string,
    pdfFile: File,
    brandName: string,
    brandSlug?: string,
    dpi?: number,
    stamkaart?: File
  ) => Promise<boolean>;
  setEditedExtraction: (data: BrandExtractionData) => void;
  generatePrompt: (tenant: string) => Promise<boolean>;
  mergeBrand: (
    tenant: string,
    pagesYaml: string | null,
    brandName: string,
    brandSlug?: string
  ) => Promise<boolean>;
  resetExtraction: () => void;

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
  activeTab: "tenants",
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

  createTenant: async (payload) => {
    try {
      const tenant = await adminApi.createTenant(payload);
      set((s) => ({ tenants: [...s.tenants, tenant], error: null }));
      return tenant;
    } catch (e) {
      set({ error: extractError(e) });
      return null;
    }
  },

  deleteTenant: async (name) => {
    try {
      await adminApi.deleteTenant(name);
      set((s) => ({
        tenants: s.tenants.filter((t) => t.name !== name),
        selectedTenant: s.selectedTenant === name ? null : s.selectedTenant,
        error: null,
      }));
      return true;
    } catch (e) {
      set({ error: extractError(e) });
      return false;
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

  // Assets
  stationeryFiles: [],
  logoFiles: [],
  fontFiles: [],
  assetsLoading: false,

  loadAssets: async (tenant, category) => {
    try {
      const assets = await adminApi.listAssets(tenant, category);
      const key =
        category === "stationery"
          ? "stationeryFiles"
          : category === "logos"
            ? "logoFiles"
            : "fontFiles";
      set({ [key]: assets });
    } catch (e) {
      set({ error: extractError(e) });
    }
  },

  loadAllAssets: async (tenant) => {
    set({ assetsLoading: true });
    try {
      const [stationery, logos, fonts] = await Promise.all([
        adminApi.listAssets(tenant, "stationery"),
        adminApi.listAssets(tenant, "logos"),
        adminApi.listAssets(tenant, "fonts"),
      ]);
      set({
        stationeryFiles: stationery,
        logoFiles: logos,
        fontFiles: fonts,
        assetsLoading: false,
      });
    } catch (e) {
      set({ assetsLoading: false, error: extractError(e) });
    }
  },

  uploadAsset: async (tenant, category, file) => {
    try {
      await adminApi.uploadAsset(tenant, category, file);
      await get().loadAssets(tenant, category);
      // Refresh tenants to update counts
      await get().loadTenants();
      return true;
    } catch (e) {
      set({ error: extractError(e) });
      return false;
    }
  },

  deleteAsset: async (tenant, category, filename) => {
    try {
      await adminApi.deleteAsset(tenant, category, filename);
      await get().loadAssets(tenant, category);
      // Refresh tenants to update counts
      await get().loadTenants();
      return true;
    } catch (e) {
      set({ error: extractError(e) });
      return false;
    }
  },

  // Brand Extraction Wizard
  extractionStep: 0,
  extractionResult: null,
  editedExtraction: null,
  promptPackage: null,
  extractionLoading: false,

  setExtractionStep: (step) => set({ extractionStep: step }),

  startExtraction: async (tenant, pdfFile, brandName, brandSlug, dpi, stamkaart) => {
    set({ extractionLoading: true, error: null });
    try {
      const result = await adminApi.startBrandExtraction(
        tenant, pdfFile, brandName, brandSlug, dpi, stamkaart
      );
      set({
        extractionResult: result,
        editedExtraction: { ...result.extraction },
        extractionLoading: false,
        extractionStep: 2,
      });
      return true;
    } catch (e) {
      set({ extractionLoading: false, error: extractError(e) });
      return false;
    }
  },

  setEditedExtraction: (data) => set({ editedExtraction: data }),

  generatePrompt: async (tenant) => {
    const edited = get().editedExtraction;
    if (!edited) return false;
    set({ extractionLoading: true, error: null });
    try {
      const result = await adminApi.generatePromptPackage(tenant, edited as unknown as Record<string, unknown>);
      set({
        promptPackage: result.prompt,
        extractionLoading: false,
        extractionStep: 3,
      });
      return true;
    } catch (e) {
      set({ extractionLoading: false, error: extractError(e) });
      return false;
    }
  },

  mergeBrand: async (tenant, pagesYaml, brandName, brandSlug) => {
    const edited = get().editedExtraction;
    if (!edited) return false;
    set({ extractionLoading: true, error: null });
    try {
      await adminApi.mergeBrand(
        tenant, edited as unknown as Record<string, unknown>,
        pagesYaml, brandName, brandSlug
      );
      // Herlaad brand data
      await get().loadBrand(tenant);
      set({
        extractionLoading: false,
        extractionStep: 0,
        extractionResult: null,
        editedExtraction: null,
        promptPackage: null,
      });
      return true;
    } catch (e) {
      set({ extractionLoading: false, error: extractError(e) });
      return false;
    }
  },

  resetExtraction: () =>
    set({
      extractionStep: 0,
      extractionResult: null,
      editedExtraction: null,
      promptPackage: null,
      extractionLoading: false,
    }),

  // General
  error: null,
  clearError: () => set({ error: null }),
}));
