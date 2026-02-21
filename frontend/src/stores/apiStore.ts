import { create } from 'zustand';
import {
  api,
  type TemplateInfo,
  type BrandInfo,
  type ValidationError,
  type ApiError,
} from '@/services/api';
import { useReportStore } from './reportStore';
import { toReportDefinition } from '@/utils/conversion';

interface ApiStore {
  // Connection
  connected: boolean;
  backendVersion: string | null;
  checking: boolean;

  // Templates & brands
  templates: TemplateInfo[];
  brands: BrandInfo[];

  // Validation
  validationErrors: ValidationError[];
  isValidating: boolean;

  // Generation
  isGenerating: boolean;
  lastPdfUrl: string | null;
  lastPdfFilename: string | null;

  // Auto-preview
  autoPreview: boolean;
  _previewTimeout: ReturnType<typeof setTimeout> | null;

  // General error
  error: string | null;

  // Actions
  checkHealth: () => Promise<void>;
  loadTemplatesAndBrands: () => Promise<void>;
  loadScaffold: (templateName: string) => Promise<void>;
  validateReport: () => Promise<boolean>;
  generatePdf: () => Promise<void>;
  downloadPdf: () => void;
  clearPdf: () => void;
  clearError: () => void;
  clearValidation: () => void;
  setAutoPreview: (enabled: boolean) => void;
  schedulePreview: () => void;
}

export const useApiStore = create<ApiStore>()((set, get) => ({
  connected: false,
  backendVersion: null,
  checking: false,
  templates: [],
  brands: [],
  validationErrors: [],
  isValidating: false,
  isGenerating: false,
  lastPdfUrl: null,
  lastPdfFilename: null,
  autoPreview: true,
  _previewTimeout: null,
  error: null,

  checkHealth: async () => {
    set({ checking: true });
    try {
      const res = await api.health();
      set({ connected: true, backendVersion: res.version, checking: false, error: null });
    } catch {
      set({ connected: false, backendVersion: null, checking: false });
    }
  },

  loadTemplatesAndBrands: async () => {
    try {
      const [templates, brands] = await Promise.all([api.templates(), api.brands()]);
      set({ templates, brands, error: null });
    } catch (e) {
      const detail = isApiError(e) ? e.detail : 'Kan templates/brands niet laden';
      set({ error: detail });
    }
  },

  loadScaffold: async (templateName) => {
    try {
      const scaffold = await api.scaffold(templateName);
      useReportStore.getState().loadReport(scaffold);
      set({ error: null });
    } catch (e) {
      const detail = isApiError(e) ? e.detail : `Kan template "${templateName}" niet laden`;
      set({ error: detail });
    }
  },

  validateReport: async () => {
    set({ isValidating: true, validationErrors: [] });
    try {
      const report = useReportStore.getState().report;
      const definition = toReportDefinition(report);
      const result = await api.validate(definition);
      set({ validationErrors: result.errors, isValidating: false, error: null });
      return result.valid;
    } catch (e) {
      const detail = isApiError(e) ? e.detail : 'Validatie mislukt';
      set({ isValidating: false, error: detail });
      return false;
    }
  },

  generatePdf: async () => {
    set({ isGenerating: true, error: null });
    try {
      const report = useReportStore.getState().report;
      const definition = toReportDefinition(report);
      const blob = await api.generate(definition);

      // Revoke previous URL if exists
      const prev = get().lastPdfUrl;
      if (prev) URL.revokeObjectURL(prev);

      const url = URL.createObjectURL(blob);
      const parts = [report.project_number, report.project].filter(Boolean);
      const filename = (parts.length > 0 ? parts.join('_') : 'rapport') + '.pdf';

      set({ lastPdfUrl: url, lastPdfFilename: filename, isGenerating: false });

      // Auto-switch to preview (but not if already in split mode)
      const currentMode = useReportStore.getState().viewMode;
      if (currentMode !== 'split') {
        useReportStore.getState().setViewMode('preview');
      }
    } catch (e) {
      const detail = isApiError(e) ? e.detail : 'PDF generatie mislukt';
      set({ isGenerating: false, error: detail });
    }
  },

  downloadPdf: () => {
    const { lastPdfUrl, lastPdfFilename } = get();
    if (!lastPdfUrl) return;
    const a = document.createElement('a');
    a.href = lastPdfUrl;
    a.download = lastPdfFilename ?? 'rapport.pdf';
    a.click();
  },

  clearPdf: () => {
    const prev = get().lastPdfUrl;
    if (prev) URL.revokeObjectURL(prev);
    set({ lastPdfUrl: null, lastPdfFilename: null });
  },

  clearError: () => set({ error: null }),

  clearValidation: () => set({ validationErrors: [] }),

  setAutoPreview: (enabled) => set({ autoPreview: enabled }),

  schedulePreview: () => {
    const state = get();
    if (!state.autoPreview || !state.connected || state.isGenerating) return;

    if (state._previewTimeout) clearTimeout(state._previewTimeout);

    const timeout = setTimeout(() => {
      // Only generate if still enabled and in a mode that shows preview
      const viewMode = useReportStore.getState().viewMode;
      if (viewMode === 'split' || viewMode === 'preview') {
        get().generatePdf();
      }
    }, 1500);

    set({ _previewTimeout: timeout });
  },
}));

function isApiError(e: unknown): e is ApiError {
  return typeof e === 'object' && e !== null && 'status' in e && 'detail' in e;
}
