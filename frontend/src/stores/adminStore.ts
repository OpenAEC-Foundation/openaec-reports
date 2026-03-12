import { create } from "zustand";
import {
  adminApi,
  type AdminUser,
  type TenantInfo,
  type TenantTemplate,
  type TenantAsset,
  type AssetCategory,
  type YamlCategory,
  type BrandData,
  type BrandExtractionResult,
  type BrandExtractionData,
  type CreateUserPayload,
  type UpdateUserPayload,
  type CreateTenantPayload,
  type ApiKeyInfo,
  type CreateApiKeyPayload,
  type ApiError,
  type Organisation,
  type CreateOrganisationPayload,
} from "@/services/api";

type AdminTab = "tenants" | "users" | "api-keys" | "templates" | "brand" | "organisations" | "help";

interface AdminStore {
  // UI
  activeTab: AdminTab;
  setActiveTab: (tab: AdminTab) => void;

  // Users
  users: AdminUser[];
  usersLoading: boolean;
  loadUsers: () => Promise<void>;
  createUser: (payload: CreateUserPayload) => Promise<AdminUser | null>;
  updateUser: (id: string, payload: UpdateUserPayload) => Promise<AdminUser | null>;
  resetPassword: (id: string, newPassword: string) => Promise<boolean>;
  deleteUser: (id: string) => Promise<boolean>;

  // API Keys
  apiKeys: ApiKeyInfo[];
  apiKeysLoading: boolean;
  loadApiKeys: (force?: boolean) => Promise<void>;
  createApiKey: (payload: CreateApiKeyPayload) => Promise<string | null>;
  revokeApiKey: (keyId: string) => Promise<boolean>;
  deleteApiKey: (keyId: string) => Promise<boolean>;

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

  // Page Types
  pageTypes: TenantTemplate[];
  pageTypesLoading: boolean;
  loadPageTypes: (tenant: string) => Promise<void>;
  uploadPageType: (tenant: string, file: File) => Promise<boolean>;
  deletePageType: (tenant: string, filename: string) => Promise<boolean>;

  // Modules
  modules: TenantTemplate[];
  modulesLoading: boolean;
  loadModules: (tenant: string) => Promise<void>;
  uploadModule: (tenant: string, file: File) => Promise<boolean>;
  deleteModule: (tenant: string, filename: string) => Promise<boolean>;

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

  // YAML Editor
  editorFile: { tenant: string; category: YamlCategory; filename: string } | null;
  editorContent: string;
  editorOriginal: string;
  editorLoading: boolean;
  editorSaving: boolean;
  editorMode: "raw" | "form";
  openEditor: (tenant: string, category: YamlCategory, filename: string) => Promise<void>;
  closeEditor: () => void;
  setEditorContent: (content: string) => void;
  setEditorMode: (mode: "raw" | "form") => void;
  saveEditorContent: () => Promise<boolean>;

  // Preview
  previewImage: string | null;
  previewWidth: number;
  previewHeight: number;
  previewLoading: boolean;
  previewError: string | null;
  requestPreview: (signal?: AbortSignal) => Promise<void>;
  clearPreview: () => void;

  // Brand Colors
  brandColors: Record<string, string> | null;
  loadBrandColors: (tenant: string) => Promise<void>;

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

  // Organisations
  organisations: Organisation[];
  organisationsLoading: boolean;
  loadOrganisations: () => Promise<void>;
  createOrganisation: (data: CreateOrganisationPayload) => Promise<Organisation | null>;
  updateOrganisation: (id: string, data: Partial<Organisation>) => Promise<Organisation | null>;
  deleteOrganisation: (id: string) => Promise<boolean>;

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

  loadUsers: async () => {
    set({ usersLoading: true });
    try {
      const users = await adminApi.listUsers();
      set({ users, usersLoading: false });
    } catch (e) {
      set({ usersLoading: false, error: extractError(e) });
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

  // API Keys
  apiKeys: [],
  apiKeysLoading: false,

  loadApiKeys: async (force = false) => {
    if (!force && get().apiKeys.length > 0) return;
    set({ apiKeysLoading: true });
    try {
      const apiKeys = await adminApi.listApiKeys();
      set({ apiKeys, apiKeysLoading: false });
    } catch (e) {
      set({ apiKeysLoading: false, error: extractError(e) });
    }
  },

  createApiKey: async (payload) => {
    try {
      const result = await adminApi.createApiKey(payload);
      set((s) => ({
        apiKeys: [result.api_key, ...s.apiKeys],
        error: null,
      }));
      return result.plaintext_key;
    } catch (e) {
      set({ error: extractError(e) });
      return null;
    }
  },

  revokeApiKey: async (keyId) => {
    try {
      await adminApi.revokeApiKey(keyId);
      set((s) => ({
        apiKeys: s.apiKeys.map((k) =>
          k.id === keyId ? { ...k, is_active: false } : k
        ),
        error: null,
      }));
      return true;
    } catch (e) {
      set({ error: extractError(e) });
      return false;
    }
  },

  deleteApiKey: async (keyId) => {
    try {
      await adminApi.deleteApiKey(keyId);
      set((s) => ({
        apiKeys: s.apiKeys.filter((k) => k.id !== keyId),
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

  // Page Types
  pageTypes: [],
  pageTypesLoading: false,

  loadPageTypes: async (tenant) => {
    set({ pageTypesLoading: true });
    try {
      const pageTypes = await adminApi.listPageTypes(tenant);
      set({ pageTypes, pageTypesLoading: false });
    } catch (e) {
      set({ pageTypesLoading: false, error: extractError(e) });
    }
  },

  uploadPageType: async (tenant, file) => {
    try {
      await adminApi.uploadPageType(tenant, file);
      await get().loadPageTypes(tenant);
      return true;
    } catch (e) {
      set({ error: extractError(e) });
      return false;
    }
  },

  deletePageType: async (tenant, filename) => {
    try {
      await adminApi.deletePageType(tenant, filename);
      set((s) => ({
        pageTypes: s.pageTypes.filter((t) => t.filename !== filename),
      }));
      return true;
    } catch (e) {
      set({ error: extractError(e) });
      return false;
    }
  },

  // Modules
  modules: [],
  modulesLoading: false,

  loadModules: async (tenant) => {
    set({ modulesLoading: true });
    try {
      const modules = await adminApi.listModules(tenant);
      set({ modules, modulesLoading: false });
    } catch (e) {
      set({ modulesLoading: false, error: extractError(e) });
    }
  },

  uploadModule: async (tenant, file) => {
    try {
      await adminApi.uploadModule(tenant, file);
      await get().loadModules(tenant);
      return true;
    } catch (e) {
      set({ error: extractError(e) });
      return false;
    }
  },

  deleteModule: async (tenant, filename) => {
    try {
      await adminApi.deleteModule(tenant, filename);
      set((s) => ({
        modules: s.modules.filter((t) => t.filename !== filename),
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

  // YAML Editor
  editorFile: null,
  editorContent: "",
  editorOriginal: "",
  editorLoading: false,
  editorSaving: false,
  editorMode: "raw",

  openEditor: async (tenant, category, filename) => {
    set({ editorLoading: true, error: null });
    try {
      const result = await adminApi.getYamlContent(tenant, category, filename);
      set({
        editorFile: { tenant, category, filename },
        editorContent: result.raw,
        editorOriginal: result.raw,
        editorLoading: false,
        editorMode: "raw",
      });
    } catch (e) {
      set({ editorLoading: false, error: extractError(e) });
    }
  },

  closeEditor: () =>
    set({
      editorFile: null,
      editorContent: "",
      editorOriginal: "",
      editorLoading: false,
      editorSaving: false,
      editorMode: "raw",
      previewImage: null,
      previewWidth: 0,
      previewHeight: 0,
      previewLoading: false,
      previewError: null,
    }),

  setEditorContent: (content) => set({ editorContent: content }),

  setEditorMode: (mode) => set({ editorMode: mode }),

  saveEditorContent: async () => {
    const { editorFile, editorContent } = get();
    if (!editorFile) return false;
    set({ editorSaving: true, error: null });
    try {
      await adminApi.updateYamlContent(
        editorFile.tenant,
        editorFile.category,
        editorFile.filename,
        editorContent
      );
      set({ editorOriginal: editorContent, editorSaving: false });
      return true;
    } catch (e) {
      set({ editorSaving: false, error: extractError(e) });
      return false;
    }
  },

  // Preview
  previewImage: null,
  previewWidth: 0,
  previewHeight: 0,
  previewLoading: false,
  previewError: null,

  requestPreview: async (signal) => {
    const { editorFile, editorContent } = get();
    if (!editorFile || editorFile.category !== "page-types") return;
    set({ previewLoading: true, previewError: null });
    try {
      const result = await adminApi.previewPageType(
        editorFile.tenant,
        editorContent,
        undefined,
        undefined,
        signal,
      );
      // Controleer of request niet geannuleerd is
      if (signal?.aborted) return;
      set({
        previewImage: result.image,
        previewWidth: result.width,
        previewHeight: result.height,
        previewLoading: false,
      });
    } catch (e) {
      if (signal?.aborted) return;
      set({
        previewLoading: false,
        previewError: extractError(e),
      });
    }
  },

  clearPreview: () =>
    set({
      previewImage: null,
      previewWidth: 0,
      previewHeight: 0,
      previewLoading: false,
      previewError: null,
    }),

  // Brand Colors
  brandColors: null,

  loadBrandColors: async (tenant) => {
    try {
      const brand = await adminApi.getBrand(tenant);
      if (brand.parsed && typeof brand.parsed.colors === "object") {
        set({ brandColors: brand.parsed.colors as Record<string, string> });
      } else {
        set({ brandColors: null });
      }
    } catch {
      set({ brandColors: null });
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

  // Organisations
  organisations: [],
  organisationsLoading: false,

  loadOrganisations: async () => {
    set({ organisationsLoading: true });
    try {
      const result = await adminApi.listOrganisations();
      set({ organisations: result.organisations, organisationsLoading: false });
    } catch (e) {
      set({ organisationsLoading: false, error: extractError(e) });
    }
  },

  createOrganisation: async (data) => {
    try {
      const result = await adminApi.createOrganisation(data);
      set((s) => ({ organisations: [...s.organisations, result.organisation], error: null }));
      return result.organisation;
    } catch (e) {
      set({ error: extractError(e) });
      return null;
    }
  },

  updateOrganisation: async (id, data) => {
    try {
      const result = await adminApi.updateOrganisation(id, data);
      set((s) => ({
        organisations: s.organisations.map((o) => (o.id === id ? result.organisation : o)),
        error: null,
      }));
      return result.organisation;
    } catch (e) {
      set({ error: extractError(e) });
      return null;
    }
  },

  deleteOrganisation: async (id) => {
    try {
      await adminApi.deleteOrganisation(id);
      set((s) => ({
        organisations: s.organisations.filter((o) => o.id !== id),
        error: null,
      }));
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
