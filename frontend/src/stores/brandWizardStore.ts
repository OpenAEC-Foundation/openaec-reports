import { create } from "zustand";
import {
  brandApi,
  type DiffResult,
  type FieldUpdate,
} from "@/api/brandApi";

// ---------- Types ----------

export interface PagePair {
  page_type: string;
  has_reference: boolean;
  has_stationery: boolean;
  complete: boolean;
}

export type WizardStep = 1 | 2 | 3;

export interface BrandWizardState {
  // Step tracking
  currentStep: WizardStep;

  // Step 1: Upload
  sessionId: string | null;
  brandName: string;
  brandSlug: string;
  pairs: PagePair[];
  uploading: boolean;
  uploadError: string | null;

  // Step 2: Diff review
  activePageType: string | null;
  diffResults: Record<string, DiffResult>;
  diffLoading: boolean;
  diffError: string | null;
  activeFieldId: string | null;

  // Step 3: Config
  colors: Record<string, string>;
  modules: string[];
  generatedYaml: string | null;
  downloadUrl: string | null;
  generating: boolean;
  generateError: string | null;

  // Actions
  setStep: (step: WizardStep) => void;
  setBrandName: (name: string) => void;
  uploadFiles: (files: File[], brandName: string) => Promise<void>;
  runDiff: (pageType: string) => Promise<void>;
  runAllDiffs: () => Promise<void>;
  setActivePageType: (pageType: string | null) => void;
  setActiveFieldId: (fieldId: string | null) => void;
  updateFieldRole: (
    pageType: string,
    fieldId: string,
    role: string,
    name: string,
  ) => void;
  saveFieldRoles: (pageType: string) => Promise<void>;
  setColors: (colors: Record<string, string>) => void;
  setColor: (key: string, value: string) => void;
  setModules: (modules: string[]) => void;
  toggleModule: (module: string) => void;
  generateBrand: () => Promise<void>;
  reset: () => void;
}

// ---------- Helpers ----------

function toSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

// ---------- Initial state ----------

const INITIAL_STATE = {
  currentStep: 1 as WizardStep,
  sessionId: null,
  brandName: "",
  brandSlug: "",
  pairs: [],
  uploading: false,
  uploadError: null,
  activePageType: null,
  diffResults: {},
  diffLoading: false,
  diffError: null,
  activeFieldId: null,
  colors: {},
  modules: [],
  generatedYaml: null,
  downloadUrl: null,
  generating: false,
  generateError: null,
};

// ---------- Store ----------

export const useBrandWizardStore = create<BrandWizardState>((set, get) => ({
  ...INITIAL_STATE,

  setStep: (step) => set({ currentStep: step }),

  setBrandName: (name) => set({ brandName: name, brandSlug: toSlug(name) }),

  uploadFiles: async (files, brandName) => {
    set({ uploading: true, uploadError: null });
    try {
      const result = await brandApi.uploadPairs(files, brandName);
      set({
        sessionId: result.session_id,
        brandSlug: result.brand_slug,
        pairs: result.pairs,
        uploading: false,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Upload mislukt";
      set({ uploading: false, uploadError: message });
    }
  },

  runDiff: async (pageType) => {
    const { sessionId } = get();
    if (!sessionId) return;

    set({ diffLoading: true, diffError: null, activePageType: pageType });
    try {
      const result = await brandApi.runDiff(sessionId, pageType);
      set((state) => ({
        diffResults: { ...state.diffResults, [pageType]: result },
        diffLoading: false,
      }));
    } catch (err) {
      const message = err instanceof Error ? err.message : "Diff mislukt";
      set({ diffLoading: false, diffError: message });
    }
  },

  runAllDiffs: async () => {
    const { pairs } = get();
    const completePairs = pairs.filter((p) => p.complete);
    for (const pair of completePairs) {
      await get().runDiff(pair.page_type);
    }
  },

  setActivePageType: (pageType) => set({ activePageType: pageType }),

  setActiveFieldId: (fieldId) => set({ activeFieldId: fieldId }),

  updateFieldRole: (pageType, fieldId, role, name) => {
    set((state) => {
      const existing = state.diffResults[pageType];
      if (!existing) return state;

      const updatedFields = existing.detected_fields.map((f) =>
        f.id === fieldId ? { ...f, role, name } : f,
      );
      return {
        diffResults: {
          ...state.diffResults,
          [pageType]: { ...existing, detected_fields: updatedFields },
        },
      };
    });
  },

  saveFieldRoles: async (pageType) => {
    const { sessionId, diffResults } = get();
    if (!sessionId) return;

    const diff = diffResults[pageType];
    if (!diff) return;

    const fieldUpdates: FieldUpdate[] = diff.detected_fields
      .filter((f) => f.role)
      .map((f) => ({
        id: f.id,
        role: f.role ?? "",
        name: f.name ?? "",
      }));

    await brandApi.updateFields(sessionId, pageType, fieldUpdates);
  },

  setColors: (colors) => set({ colors }),

  setColor: (key, value) =>
    set((state) => ({ colors: { ...state.colors, [key]: value } })),

  setModules: (modules) => set({ modules }),

  toggleModule: (module) =>
    set((state) => ({
      modules: state.modules.includes(module)
        ? state.modules.filter((m) => m !== module)
        : [...state.modules, module],
    })),

  generateBrand: async () => {
    const { sessionId, brandName, brandSlug, colors, modules } = get();
    if (!sessionId) return;

    set({ generating: true, generateError: null });
    try {
      const result = await brandApi.generateBrand(sessionId, {
        brand_name: brandName,
        brand_slug: brandSlug,
        colors,
        modules,
      });
      set({
        generatedYaml: result.yaml,
        downloadUrl: result.download_url,
        generating: false,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Genereren mislukt";
      set({ generating: false, generateError: message });
    }
  },

  reset: () => set(INITIAL_STATE),
}));
