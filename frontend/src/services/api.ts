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
  has_stationery: boolean;
  has_fonts: boolean;
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
