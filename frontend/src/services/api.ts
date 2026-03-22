import type { ReportDefinition } from '@/types/report';

// Leeg = relatieve URLs, werkt achter reverse proxy (Caddy)
// Voor lokale dev: stel VITE_API_URL=http://localhost:8000 in .env.development
const API_BASE = import.meta.env.VITE_API_URL || '';

export interface ApiError {
  status: number;
  detail: string;
  type?: string;
}

export interface TemplateInfo {
  name: string;
  report_type: string;
  /** Engine type: 'v2' (ReportLab/PyMuPDF) of 'template' (TemplateEngine YAML-driven) */
  engine?: 'v2' | 'template';
}

export interface BrandInfo {
  name: string;
  slug: string;
  complete?: boolean;
}

export interface ValidationError {
  path: string;
  message: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
}

export interface HealthResponse {
  status: string;
  version: string;
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    const err: ApiError = {
      status: res.status,
      detail: body.detail ?? res.statusText,
      type: body.type,
    };
    throw err;
  }
  return res.json();
}

// ---------- Admin types ----------


export interface AdminUser {
  id: string;
  username: string;
  email: string;
  display_name: string;
  role: string;
  tenant: string;
  is_active: boolean;
}

export interface CreateUserPayload {
  username: string;
  email?: string;
  display_name?: string;
  password: string;
  role?: string;
  tenant?: string;
}

export interface UpdateUserPayload {
  email?: string;
  display_name?: string;
  role?: string;
  tenant?: string;
  is_active?: boolean;
}

export interface TenantInfo {
  name: string;
  has_brand: boolean;
  template_count: number;
  page_type_count: number;
  module_count: number;
  stationery_count: number;
  logo_count: number;
  font_count: number;
}

export interface CreateTenantPayload {
  name: string;
  display_name?: string;
}

export type AssetCategory = "stationery" | "logos" | "fonts";

export type YamlCategory = "templates" | "page-types" | "modules";

export interface TenantAsset {
  filename: string;
  size: number;
}

export interface TenantTemplate {
  filename: string;
  size: number;
}

export interface BrandData {
  exists: boolean;
  parsed: Record<string, unknown> | null;
  raw: string;
}

export interface YamlContentResponse {
  filename: string;
  parsed: Record<string, unknown> | null;
  raw: string;
}

// ---------- API Key types ----------

export interface ApiKeyInfo {
  id: string;
  name: string;
  key_prefix: string;
  user_id: string;
  is_active: boolean;
  created_at: string;
  expires_at: string | null;
}

export interface CreateApiKeyPayload {
  name: string;
  user_id: string;
  expires_at?: string;
}

export interface CreateApiKeyResponse {
  api_key: ApiKeyInfo;
  plaintext_key: string;
}

// ---------- Brand Extraction types ----------

export interface BrandExtractionData {
  brand: { name: string; slug: string };
  colors: Record<string, string>;
  fonts: Record<string, string>;
  margins_mm: Record<string, number>;
  header: { height: number; elements: Record<string, unknown>[] };
  footer: { height: number; elements: Record<string, unknown>[] };
  styles: Record<string, {
    fontName: string;
    fontSize: number;
    leading: number;
    textColor: string;
  }>;
  table_style: Record<string, string>;
  page_classifications: { page_number: number; type: string; confidence: number }[];
  page_layouts: Record<string, unknown>;
}

export interface BrandExtractionResult {
  extraction: BrandExtractionData;
  page_images: Record<string, string>;
  draft_yaml: string;
}

export interface PromptPackageResult {
  prompt: string;
  page_images: Record<string, string>;
  pages_dir: string;
}

export interface BrandMergeResult {
  detail: string;
  yaml: string;
  path: string;
}

// ---------- Admin API ----------

export const adminApi = {
  // Users
  listUsers: () =>
    apiFetch<{ users: AdminUser[] }>("/api/admin/users").then((r) => r.users),

  createUser: (payload: CreateUserPayload) =>
    apiFetch<{ user: AdminUser }>("/api/admin/users", {
      method: "POST",
      body: JSON.stringify(payload),
    }).then((r) => r.user),

  getUser: (id: string) =>
    apiFetch<{ user: AdminUser }>(`/api/admin/users/${id}`).then((r) => r.user),

  updateUser: (id: string, payload: UpdateUserPayload) =>
    apiFetch<{ user: AdminUser }>(`/api/admin/users/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }).then((r) => r.user),

  resetPassword: (id: string, newPassword: string) =>
    apiFetch<{ detail: string }>(`/api/admin/users/${id}/reset-password`, {
      method: "POST",
      body: JSON.stringify({ new_password: newPassword }),
    }),

  deleteUser: (id: string) =>
    apiFetch<{ detail: string }>(`/api/admin/users/${id}`, {
      method: "DELETE",
    }),

  // Tenants
  listTenants: () =>
    apiFetch<{ tenants: TenantInfo[] }>("/api/admin/tenants").then((r) => r.tenants),

  createTenant: (payload: CreateTenantPayload) =>
    apiFetch<{ tenant: TenantInfo }>("/api/admin/tenants", {
      method: "POST",
      body: JSON.stringify(payload),
    }).then((r) => r.tenant),

  deleteTenant: (name: string) =>
    apiFetch<{ detail: string }>(`/api/admin/tenants/${encodeURIComponent(name)}`, {
      method: "DELETE",
    }),

  // Templates
  listTemplates: (tenant: string) =>
    apiFetch<{ templates: TenantTemplate[] }>(
      `/api/admin/tenants/${encodeURIComponent(tenant)}/templates`
    ).then((r) => r.templates),

  uploadTemplate: async (tenant: string, file: File): Promise<{ filename: string; size: number }> => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(
      `${API_BASE}/api/admin/tenants/${encodeURIComponent(tenant)}/templates`,
      { method: "POST", credentials: "include", body: formData }
    );
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw { status: res.status, detail: body.detail ?? "Upload mislukt" } as ApiError;
    }
    return res.json();
  },

  deleteTemplate: (tenant: string, filename: string) =>
    apiFetch<{ detail: string }>(
      `/api/admin/tenants/${encodeURIComponent(tenant)}/templates/${encodeURIComponent(filename)}`,
      { method: "DELETE" }
    ),

  // Page Types
  listPageTypes: (tenant: string) =>
    apiFetch<{ page_types: TenantTemplate[] }>(
      `/api/admin/tenants/${encodeURIComponent(tenant)}/page-types`
    ).then((r) => r.page_types),

  uploadPageType: async (tenant: string, file: File): Promise<{ filename: string; size: number }> => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(
      `${API_BASE}/api/admin/tenants/${encodeURIComponent(tenant)}/page-types`,
      { method: "POST", credentials: "include", body: formData }
    );
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw { status: res.status, detail: body.detail ?? "Upload mislukt" } as ApiError;
    }
    return res.json();
  },

  deletePageType: (tenant: string, filename: string) =>
    apiFetch<{ detail: string }>(
      `/api/admin/tenants/${encodeURIComponent(tenant)}/page-types/${encodeURIComponent(filename)}`,
      { method: "DELETE" }
    ),

  // Modules
  listModules: (tenant: string) =>
    apiFetch<{ modules: TenantTemplate[] }>(
      `/api/admin/tenants/${encodeURIComponent(tenant)}/modules`
    ).then((r) => r.modules),

  uploadModule: async (tenant: string, file: File): Promise<{ filename: string; size: number }> => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(
      `${API_BASE}/api/admin/tenants/${encodeURIComponent(tenant)}/modules`,
      { method: "POST", credentials: "include", body: formData }
    );
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw { status: res.status, detail: body.detail ?? "Upload mislukt" } as ApiError;
    }
    return res.json();
  },

  deleteModule: (tenant: string, filename: string) =>
    apiFetch<{ detail: string }>(
      `/api/admin/tenants/${encodeURIComponent(tenant)}/modules/${encodeURIComponent(filename)}`,
      { method: "DELETE" }
    ),

  // YAML download URL helper
  getYamlDownloadUrl: (tenant: string, category: YamlCategory, filename: string): string =>
    `${API_BASE}/api/admin/tenants/${encodeURIComponent(tenant)}/${category}/${encodeURIComponent(filename)}/download`,

  // YAML inline editor
  getYamlContent: (tenant: string, category: YamlCategory, filename: string) =>
    apiFetch<YamlContentResponse>(
      `/api/admin/tenants/${encodeURIComponent(tenant)}/${category}/${encodeURIComponent(filename)}/content`
    ),

  updateYamlContent: (tenant: string, category: YamlCategory, filename: string, content: string) =>
    apiFetch<{ filename: string; size: number }>(
      `/api/admin/tenants/${encodeURIComponent(tenant)}/${category}/${encodeURIComponent(filename)}/content`,
      {
        method: "PUT",
        body: JSON.stringify({ content }),
      }
    ),

  // Brand
  getBrand: (tenant: string) =>
    apiFetch<BrandData>(`/api/admin/tenants/${encodeURIComponent(tenant)}/brand`),

  uploadBrand: async (tenant: string, file: File): Promise<{ detail: string }> => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(
      `${API_BASE}/api/admin/tenants/${encodeURIComponent(tenant)}/brand`,
      { method: "POST", credentials: "include", body: formData }
    );
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw { status: res.status, detail: body.detail ?? "Upload mislukt" } as ApiError;
    }
    return res.json();
  },

  // Assets (stationery, logos, fonts)
  listAssets: (tenant: string, category: AssetCategory) =>
    apiFetch<{ assets: TenantAsset[] }>(
      `/api/admin/tenants/${encodeURIComponent(tenant)}/assets/${category}`
    ).then((r) => r.assets),

  uploadAsset: async (
    tenant: string,
    category: AssetCategory,
    file: File
  ): Promise<{ filename: string; size: number }> => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(
      `${API_BASE}/api/admin/tenants/${encodeURIComponent(tenant)}/assets/${category}`,
      { method: "POST", credentials: "include", body: formData }
    );
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw { status: res.status, detail: body.detail ?? "Upload mislukt" } as ApiError;
    }
    return res.json();
  },

  deleteAsset: (tenant: string, category: AssetCategory, filename: string) =>
    apiFetch<{ detail: string }>(
      `/api/admin/tenants/${encodeURIComponent(tenant)}/assets/${category}/${encodeURIComponent(filename)}`,
      { method: "DELETE" }
    ),

  // API Keys
  listApiKeys: () =>
    apiFetch<{ api_keys: ApiKeyInfo[] }>("/api/admin/api-keys").then((r) => r.api_keys),

  createApiKey: (payload: CreateApiKeyPayload) =>
    apiFetch<CreateApiKeyResponse>("/api/admin/api-keys", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  revokeApiKey: (keyId: string) =>
    apiFetch<{ detail: string }>(`/api/admin/api-keys/${keyId}/revoke`, {
      method: "POST",
    }),

  deleteApiKey: (keyId: string) =>
    apiFetch<{ detail: string }>(`/api/admin/api-keys/${keyId}`, {
      method: "DELETE",
    }),

  // Page-type preview
  previewPageType: (
    tenant: string,
    yamlContent: string,
    sampleData?: Record<string, unknown>,
    dpi?: number,
    signal?: AbortSignal
  ) =>
    apiFetch<{ image: string; width: number; height: number }>(
      `/api/admin/tenants/${encodeURIComponent(tenant)}/preview/page-type`,
      {
        method: "POST",
        body: JSON.stringify({
          yaml_content: yamlContent,
          sample_data: sampleData ?? null,
          dpi: dpi ?? 150,
        }),
        signal,
      }
    ),

  // Brand Extraction
  startBrandExtraction: async (
    tenant: string,
    pdfFile: File,
    brandName: string,
    brandSlug?: string,
    dpi?: number,
    stamkaart?: File
  ): Promise<BrandExtractionResult> => {
    const formData = new FormData();
    formData.append("pdf_file", pdfFile);
    formData.append("brand_name", brandName);
    if (brandSlug) formData.append("brand_slug", brandSlug);
    if (dpi) formData.append("dpi", String(dpi));
    if (stamkaart) formData.append("stamkaart", stamkaart);
    const res = await fetch(
      `${API_BASE}/api/admin/tenants/${encodeURIComponent(tenant)}/brand-extract`,
      { method: "POST", credentials: "include", body: formData }
    );
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw { status: res.status, detail: body.detail ?? "Extractie mislukt" } as ApiError;
    }
    return res.json();
  },

  getAnalysisPageUrl: (tenant: string, filename: string): string =>
    `${API_BASE}/api/admin/tenants/${encodeURIComponent(tenant)}/analysis/pages/${encodeURIComponent(filename)}`,

  generatePromptPackage: (tenant: string, editedExtraction: Record<string, unknown>) =>
    apiFetch<PromptPackageResult>(
      `/api/admin/tenants/${encodeURIComponent(tenant)}/brand-extract/prompt-package`,
      {
        method: "POST",
        body: JSON.stringify({ edited_extraction: editedExtraction }),
      }
    ),

  mergeBrand: (
    tenant: string,
    editedExtraction: Record<string, unknown>,
    pagesYaml: string | null,
    brandName: string,
    brandSlug?: string
  ) =>
    apiFetch<BrandMergeResult>(
      `/api/admin/tenants/${encodeURIComponent(tenant)}/brand-merge`,
      {
        method: "POST",
        body: JSON.stringify({
          edited_extraction: editedExtraction,
          pages_yaml: pagesYaml,
          brand_name: brandName,
          brand_slug: brandSlug || tenant,
        }),
      }
    ),

};

// ---------- Report API ----------

export const api = {
  health: () => apiFetch<HealthResponse>('/api/health'),

  templates: () =>
    apiFetch<{ templates: TemplateInfo[] }>('/api/templates').then((r) => r.templates),

  scaffold: (name: string) =>
    apiFetch<ReportDefinition>(`/api/templates/${encodeURIComponent(name)}/scaffold`),

  brands: () =>
    apiFetch<{ brands: BrandInfo[] }>('/api/brands').then((r) => r.brands),

  stationery: () =>
    apiFetch<{ brands: BrandInfo[] }>('/api/stationery'),

  validate: (data: ReportDefinition) =>
    apiFetch<ValidationResult>('/api/validate', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  generate: async (data: ReportDefinition): Promise<Blob> => {
    const res = await fetch(`${API_BASE}/api/generate/v2`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      const err: ApiError = {
        status: res.status,
        detail: body.detail ?? res.statusText,
        type: body.type,
      };
      throw err;
    }
    return res.blob();
  },

  generateTemplate: async (data: ReportDefinition): Promise<Blob> => {
    const res = await fetch(`${API_BASE}/api/generate/template`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      const err: ApiError = {
        status: res.status,
        detail: body.detail ?? res.statusText,
        type: body.type,
      };
      throw err;
    }
    return res.blob();
  },

  upload: async (file: File): Promise<{ path: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/api/upload`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw { status: res.status, detail: body.detail ?? 'Upload failed' } as ApiError;
    }
    return res.json();
  },
};
