import type { ReportDefinition } from '@/types/report';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
      body: formData,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw { status: res.status, detail: body.detail ?? 'Upload failed' } as ApiError;
    }
    return res.json();
  },
};
