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
import type { ReportDefinition } from '@/types/report';

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
  previewPage: number;

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
  setPreviewPage: (page: number) => void;
  schedulePreview: () => void;
}

/**
 * Detecteer of een rapport via de TemplateEngine moet worden gegenereerd.
 *
 * Heuristiek (in volgorde):
 * 1. Template naam bevat bekende Customer prefixen
 * 2. Brand is 'customer'
 * 3. Report type bevat 'BIC'
 *
 * Alle andere rapporten gaan via renderer_v2.
 */
function _isTemplateEngineReport(def: ReportDefinition): boolean {
  const template = (def.template ?? '').toLowerCase();
  const brand = (def.brand ?? '').toLowerCase();
  const reportType = (def.report_type ?? '').toLowerCase();

  // Customer templates → TemplateEngine
  if (template.includes('bic_factuur') || template.includes('bic_rapport') || template.includes('sanering')) {
    return true;
  }

  // Customer brand → TemplateEngine
  if (brand === 'customer') {
    return true;
  }

  // BIC report types → TemplateEngine
  if (reportType.includes('bic')) {
    return true;
  }

  return false;
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
  previewPage: 1,
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
      // Smart endpoint routing: TemplateEngine voor YAML-driven templates
      const isTemplateEngine = _isTemplateEngineReport(definition);
      const blob = isTemplateEngine
        ? await api.generateTemplate(definition)
        : await api.generate(definition);

      // Revoke previous URL if exists
      const prev = get().lastPdfUrl;
      if (prev) URL.revokeObjectURL(prev.replace(/#.*$/, ''));

      const blobUrl = URL.createObjectURL(blob);
      const page = get().previewPage;
      const url = page > 1 ? `${blobUrl}#page=${page}` : blobUrl;
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
    a.href = lastPdfUrl.replace(/#.*$/, '');
    a.download = lastPdfFilename ?? 'rapport.pdf';
    a.click();
  },

  clearPdf: () => {
    const prev = get().lastPdfUrl;
    if (prev) URL.revokeObjectURL(prev.replace(/#.*$/, ''));
    set({ lastPdfUrl: null, lastPdfFilename: null, previewPage: 1 });
  },

  clearError: () => set({ error: null }),

  clearValidation: () => set({ validationErrors: [] }),

  setAutoPreview: (enabled) => set({ autoPreview: enabled }),

  setPreviewPage: (page) => {
    const p = Math.max(1, Math.round(page));
    set({ previewPage: p });
  },

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
