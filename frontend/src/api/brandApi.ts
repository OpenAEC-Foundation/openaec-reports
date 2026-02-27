const API_BASE = import.meta.env.VITE_API_URL || '';

// ---------- Response types ----------

export interface UploadPair {
  page_type: string;
  has_reference: boolean;
  has_stationery: boolean;
  complete: boolean;
}

export interface UploadResponse {
  session_id: string;
  brand_slug: string;
  pairs: UploadPair[];
}

export interface DetectedField {
  id: string;
  sample_text: string;
  x_pt: number;
  y_pt: number;
  width_pt: number;
  height_pt: number;
  font: string;
  font_size: number;
  color_hex: string;
  suggested_role: string | null;
  role: string | null;
  name: string | null;
}

export interface DetectedColor {
  hex: string;
  count: number;
  usage: string;
}

export interface DetectedFont {
  name: string;
  count: number;
  sizes: number[];
}

export interface DiffResult {
  page_type: string;
  orientation: "portrait" | "landscape";
  page_size: { width_pt: number; height_pt: number };
  diff_image_url: string;
  reference_image_url: string;
  stationery_image_url: string;
  detected_fields: DetectedField[];
  detected_colors: DetectedColor[];
  detected_fonts: DetectedFont[];
}

export interface FieldUpdate {
  id: string;
  role: string;
  name: string;
}

export interface GenerateResponse {
  yaml: string;
  download_url: string;
}

export interface BrandGenerateConfig {
  brand_name: string;
  brand_slug: string;
  colors: Record<string, string>;
  modules: string[];
}

// ---------- API client ----------

export const brandApi = {
  async uploadPairs(files: File[], brandName: string): Promise<UploadResponse> {
    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));
    formData.append("brand_name", brandName);

    const res = await fetch(`${API_BASE}/api/brand/upload-pairs`, {
      method: "POST",
      body: formData,
      credentials: "include",
    });
    if (!res.ok) {
      const detail = await res.text().catch(() => res.statusText);
      throw new Error(`Upload mislukt: ${detail}`);
    }
    return res.json() as Promise<UploadResponse>;
  },

  async runDiff(sessionId: string, pageType: string): Promise<DiffResult> {
    const res = await fetch(
      `${API_BASE}/api/brand/diff/${sessionId}/${pageType}`,
      { method: "POST", credentials: "include" },
    );
    if (!res.ok) {
      const detail = await res.text().catch(() => res.statusText);
      throw new Error(`Diff mislukt: ${detail}`);
    }
    return res.json() as Promise<DiffResult>;
  },

  async updateFields(
    sessionId: string,
    pageType: string,
    fields: FieldUpdate[],
  ): Promise<void> {
    const res = await fetch(
      `${API_BASE}/api/brand/fields/${sessionId}/${pageType}`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fields }),
        credentials: "include",
      },
    );
    if (!res.ok) {
      const detail = await res.text().catch(() => res.statusText);
      throw new Error(`Velden opslaan mislukt: ${detail}`);
    }
  },

  async generateBrand(
    sessionId: string,
    config: BrandGenerateConfig,
  ): Promise<GenerateResponse> {
    const res = await fetch(
      `${API_BASE}/api/brand/generate/${sessionId}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
        credentials: "include",
      },
    );
    if (!res.ok) {
      const detail = await res.text().catch(() => res.statusText);
      throw new Error(`Genereren mislukt: ${detail}`);
    }
    return res.json() as Promise<GenerateResponse>;
  },

  getDiffImageUrl(sessionId: string, pageType: string): string {
    return `${API_BASE}/api/brand/diff-image/${sessionId}/${pageType}`;
  },

  getReferenceImageUrl(sessionId: string, pageType: string): string {
    return `${API_BASE}/api/brand/preview/${sessionId}/${pageType}_reference.png`;
  },

  getStationeryImageUrl(sessionId: string, pageType: string): string {
    return `${API_BASE}/api/brand/preview/${sessionId}/${pageType}_stationery.png`;
  },
};
