import { create } from 'zustand';
import type {
  EditorReport,
  EditorSection,
  EditorAppendix,
  EditorBlock,
  ContentBlock,
  Cover,
  Colofon,
  TocConfig,
  BackcoverConfig,
  ReportDefinition,
  EditableBlockType,
} from '@/types/report';
import { createDefaultReport, createDefaultSection, createDefaultAppendix, createDefaultBlock } from '@/utils/defaults';
import { toEditorReport, toReportDefinition } from '@/utils/conversion';
import { generateId } from '@/utils/idGenerator';
import { useAuthStore } from '@/stores/authStore';

// ---------- Validation result ----------

export interface ValidationResult {
  ok: boolean;
  errors: string[];
}

// ---------- View mode ----------

export type ViewMode = 'editor' | 'split' | 'json' | 'preview' | 'admin' | 'projects';

export type MetadataPanel = 'rapport' | 'voorblad' | 'colofon' | 'opties';

// ---------- Undo/redo constants ----------

const MAX_UNDO_HISTORY = 50;
const UNDO_DEBOUNCE_MS = 300;

// ---------- Store interface ----------

export interface ReportStore {
  // Rapport data
  report: EditorReport;

  // UI state
  activeSection: string | null;
  activeAppendix: string | null;
  activeBlock: string | null;
  activePanel: MetadataPanel;
  viewMode: ViewMode;
  isDirty: boolean;

  // Undo/redo
  _past: EditorReport[];
  _future: EditorReport[];
  _lastPushTime: number;
  canUndo: boolean;
  canRedo: boolean;
  undo: () => void;
  redo: () => void;
  _pushHistory: () => void;

  // Auto-save
  lastSavedAt: string | null;

  // Server-side opslag referenties
  serverReportId: string | null;
  serverProjectId: string | null;

  // Actions — rapport niveau
  setMetadata: (fields: Partial<Pick<EditorReport, 'project' | 'project_number' | 'client' | 'author' | 'report_type' | 'date' | 'version' | 'status' | 'format' | 'orientation'>>) => void;
  setCover: (cover: Cover) => void;
  setColofon: (colofon: Colofon) => void;
  setToc: (toc: TocConfig) => void;
  setBackcover: (backcover: BackcoverConfig) => void;

  // Actions — secties
  addSection: (section: EditorSection, index?: number) => void;
  addNewSection: (index?: number) => void;
  updateSection: (id: string, updates: Partial<Pick<EditorSection, 'title' | 'level' | 'page_break_before'>>) => void;
  removeSection: (id: string) => void;
  reorderSections: (fromIndex: number, toIndex: number) => void;

  // Actions — blocks
  addBlock: (sectionId: string, block: EditorBlock, index?: number) => void;
  addNewBlock: (sectionId: string, blockType: EditableBlockType, index?: number) => void;
  updateBlock: (sectionId: string, blockId: string, updates: Partial<ContentBlock>) => void;
  removeBlock: (sectionId: string, blockId: string) => void;
  reorderBlocks: (sectionId: string, fromIndex: number, toIndex: number) => void;
  duplicateBlock: (sectionId: string, blockId: string) => void;

  // Actions — bijlagen
  addAppendix: (appendix: EditorAppendix, index?: number) => void;
  addNewAppendix: (index?: number) => void;
  updateAppendix: (id: string, updates: Partial<Pick<EditorAppendix, 'title'>>) => void;
  removeAppendix: (id: string) => void;
  reorderAppendices: (fromIndex: number, toIndex: number) => void;

  // Actions — blocks in bijlagen
  addAppendixBlock: (appendixId: string, block: EditorBlock, index?: number) => void;
  addNewAppendixBlock: (appendixId: string, blockType: EditableBlockType, index?: number) => void;
  updateAppendixBlock: (appendixId: string, blockId: string, updates: Partial<ContentBlock>) => void;
  removeAppendixBlock: (appendixId: string, blockId: string) => void;
  reorderAppendixBlocks: (appendixId: string, fromIndex: number, toIndex: number) => void;
  duplicateAppendixBlock: (appendixId: string, blockId: string) => void;

  // Actions — UI
  setActiveSection: (id: string | null) => void;
  setActiveAppendix: (id: string | null) => void;
  setActiveBlock: (id: string | null) => void;
  setActivePanel: (panel: MetadataPanel) => void;
  setViewMode: (mode: ViewMode) => void;

  // Actions — I/O
  importJson: (json: string) => ValidationResult;
  exportJson: () => string;
  loadReport: (definition: ReportDefinition) => void;
  loadTemplate: (templateName: string) => void;
  reset: () => void;
}

// ---------- Helper: immutable section update ----------

function updateSections(
  sections: EditorSection[],
  sectionId: string,
  updater: (section: EditorSection) => EditorSection,
): EditorSection[] {
  return sections.map((s) => (s.id === sectionId ? updater(s) : s));
}

function updateAppendices(
  appendices: EditorAppendix[],
  appendixId: string,
  updater: (appendix: EditorAppendix) => EditorAppendix,
): EditorAppendix[] {
  return appendices.map((a) => (a.id === appendixId ? updater(a) : a));
}

function renumberAppendices(appendices: EditorAppendix[]): EditorAppendix[] {
  return appendices.map((a, i) => ({ ...a, number: i + 1 }));
}

// ---------- Content check helper ----------

export function reportHasContent(report: EditorReport): boolean {
  const hasBlocks = report.sections.some(s => s.content.length > 0);
  const hasAppendices = report.appendices.length > 0;
  const hasMetadata = !!(report.project || report.client || report.project_number);
  return hasBlocks || hasAppendices || hasMetadata;
}

// ---------- Store ----------

export const useReportStore = create<ReportStore>()((set, get) => ({
  // Initial state
  report: createDefaultReport(),
  activeSection: null,
  activeAppendix: null,
  activeBlock: null,
  activePanel: 'rapport',
  viewMode: 'editor',
  isDirty: false,

  // Undo/redo state
  _past: [],
  _future: [],
  _lastPushTime: 0,
  canUndo: false,
  canRedo: false,

  // Auto-save
  lastSavedAt: null,

  // Server-side opslag referenties
  serverReportId: null,
  serverProjectId: null,

  _pushHistory: () => {
    const state = get();
    const now = Date.now();
    // Debounce: if last push was recent, replace the last snapshot instead of adding
    if (now - state._lastPushTime < UNDO_DEBOUNCE_MS && state._past.length > 0) {
      // Don't push a new entry — the previous snapshot is close enough
      set({ _future: [], canRedo: false, _lastPushTime: now });
      return;
    }
    const past = [...state._past, state.report];
    if (past.length > MAX_UNDO_HISTORY) past.shift();
    set({ _past: past, _future: [], canUndo: true, canRedo: false, _lastPushTime: now });
  },

  undo: () => {
    const state = get();
    if (state._past.length === 0) return;
    const past = [...state._past];
    const previous = past.pop()!;
    set({
      _past: past,
      _future: [state.report, ...state._future],
      report: previous,
      canUndo: past.length > 0,
      canRedo: true,
      isDirty: true,
    });
  },

  redo: () => {
    const state = get();
    if (state._future.length === 0) return;
    const future = [...state._future];
    const next = future.shift()!;
    set({
      _past: [...state._past, state.report],
      _future: future,
      report: next,
      canUndo: true,
      canRedo: future.length > 0,
      isDirty: true,
    });
  },

  // --- Metadata ---
  setMetadata: (fields) => {
    get()._pushHistory();
    set((state) => ({
      report: { ...state.report, ...fields },
      isDirty: true,
    }));
  },

  setCover: (cover) => {
    get()._pushHistory();
    set((state) => ({
      report: { ...state.report, cover },
      isDirty: true,
    }));
  },

  setColofon: (colofon) => {
    get()._pushHistory();
    set((state) => ({
      report: { ...state.report, colofon },
      isDirty: true,
    }));
  },

  setToc: (toc) => {
    get()._pushHistory();
    set((state) => ({
      report: { ...state.report, toc },
      isDirty: true,
    }));
  },

  setBackcover: (backcover) => {
    get()._pushHistory();
    set((state) => ({
      report: { ...state.report, backcover },
      isDirty: true,
    }));
  },

  // --- Sections ---
  addSection: (section, index) => {
    get()._pushHistory();
    set((state) => {
      const sections = [...state.report.sections];
      if (index !== undefined && index >= 0 && index <= sections.length) {
        sections.splice(index, 0, section);
      } else {
        sections.push(section);
      }
      return {
        report: { ...state.report, sections },
        activeSection: section.id,
        isDirty: true,
      };
    });
  },

  addNewSection: (index) => {
    const section = createDefaultSection();
    get().addSection(section, index);
  },

  updateSection: (id, updates) => {
    get()._pushHistory();
    set((state) => ({
      report: {
        ...state.report,
        sections: updateSections(state.report.sections, id, (s) => ({
          ...s,
          ...updates,
        })),
      },
      isDirty: true,
    }));
  },

  removeSection: (id) => {
    get()._pushHistory();
    set((state) => ({
      report: {
        ...state.report,
        sections: state.report.sections.filter((s) => s.id !== id),
      },
      activeSection: state.activeSection === id ? null : state.activeSection,
      isDirty: true,
    }));
  },

  reorderSections: (fromIndex, toIndex) => {
    get()._pushHistory();
    set((state) => {
      const sections = [...state.report.sections];
      const [moved] = sections.splice(fromIndex, 1);
      if (moved) {
        sections.splice(toIndex, 0, moved);
      }
      return {
        report: { ...state.report, sections },
        isDirty: true,
      };
    });
  },

  // --- Blocks ---
  addBlock: (sectionId, block, index) => {
    get()._pushHistory();
    set((state) => ({
      report: {
        ...state.report,
        sections: updateSections(state.report.sections, sectionId, (s) => {
          const content = [...s.content];
          if (index !== undefined && index >= 0 && index <= content.length) {
            content.splice(index, 0, block);
          } else {
            content.push(block);
          }
          return { ...s, content };
        }),
      },
      activeBlock: block.id,
      isDirty: true,
    }));
  },

  addNewBlock: (sectionId, blockType, index) => {
    const block = createDefaultBlock(blockType);
    get().addBlock(sectionId, block, index);
  },

  updateBlock: (sectionId, blockId, updates) => {
    get()._pushHistory();
    set((state) => ({
      report: {
        ...state.report,
        sections: updateSections(state.report.sections, sectionId, (s) => ({
          ...s,
          content: s.content.map((b) =>
            b.id === blockId ? ({ ...b, ...updates } as EditorBlock) : b,
          ),
        })),
      },
      isDirty: true,
    }));
  },

  removeBlock: (sectionId, blockId) => {
    get()._pushHistory();
    set((state) => ({
      report: {
        ...state.report,
        sections: updateSections(state.report.sections, sectionId, (s) => ({
          ...s,
          content: s.content.filter((b) => b.id !== blockId),
        })),
      },
      activeBlock: state.activeBlock === blockId ? null : state.activeBlock,
      isDirty: true,
    }));
  },

  reorderBlocks: (sectionId, fromIndex, toIndex) => {
    get()._pushHistory();
    set((state) => ({
      report: {
        ...state.report,
        sections: updateSections(state.report.sections, sectionId, (s) => {
          const content = [...s.content];
          const [moved] = content.splice(fromIndex, 1);
          if (moved) {
            content.splice(toIndex, 0, moved);
          }
          return { ...s, content };
        }),
      },
      isDirty: true,
    }));
  },

  duplicateBlock: (sectionId, blockId) => {
    get()._pushHistory();
    set((state) => ({
      report: {
        ...state.report,
        sections: updateSections(state.report.sections, sectionId, (s) => {
          const idx = s.content.findIndex((b) => b.id === blockId);
          if (idx === -1) return s;
          const original = s.content[idx]!;
          const { id: _id, ...rest } = original;
          const duplicate = { ...rest, id: generateId() } as EditorBlock;
          const content = [...s.content];
          content.splice(idx + 1, 0, duplicate);
          return { ...s, content };
        }),
      },
      isDirty: true,
    }));
  },

  // --- Appendices ---
  addAppendix: (appendix, index) => {
    get()._pushHistory();
    set((state) => {
      const appendices = [...state.report.appendices];
      if (index !== undefined && index >= 0 && index <= appendices.length) {
        appendices.splice(index, 0, appendix);
      } else {
        appendices.push(appendix);
      }
      return {
        report: { ...state.report, appendices: renumberAppendices(appendices) },
        activeAppendix: appendix.id,
        activeSection: null,
        activeBlock: null,
        isDirty: true,
      };
    });
  },

  addNewAppendix: (index) => {
    const appendix = createDefaultAppendix();
    get().addAppendix(appendix, index);
  },

  updateAppendix: (id, updates) => {
    get()._pushHistory();
    set((state) => ({
      report: {
        ...state.report,
        appendices: updateAppendices(state.report.appendices, id, (a) => ({
          ...a,
          ...updates,
        })),
      },
      isDirty: true,
    }));
  },

  removeAppendix: (id) => {
    get()._pushHistory();
    set((state) => ({
      report: {
        ...state.report,
        appendices: renumberAppendices(state.report.appendices.filter((a) => a.id !== id)),
      },
      activeAppendix: state.activeAppendix === id ? null : state.activeAppendix,
      isDirty: true,
    }));
  },

  reorderAppendices: (fromIndex, toIndex) => {
    get()._pushHistory();
    set((state) => {
      const appendices = [...state.report.appendices];
      const [moved] = appendices.splice(fromIndex, 1);
      if (moved) {
        appendices.splice(toIndex, 0, moved);
      }
      return {
        report: { ...state.report, appendices: renumberAppendices(appendices) },
        isDirty: true,
      };
    });
  },

  // --- Appendix blocks ---
  addAppendixBlock: (appendixId, block, index) => {
    get()._pushHistory();
    set((state) => ({
      report: {
        ...state.report,
        appendices: updateAppendices(state.report.appendices, appendixId, (a) => {
          const content = [...a.content];
          if (index !== undefined && index >= 0 && index <= content.length) {
            content.splice(index, 0, block);
          } else {
            content.push(block);
          }
          return { ...a, content };
        }),
      },
      activeBlock: block.id,
      isDirty: true,
    }));
  },

  addNewAppendixBlock: (appendixId, blockType, index) => {
    const block = createDefaultBlock(blockType);
    get().addAppendixBlock(appendixId, block, index);
  },

  updateAppendixBlock: (appendixId, blockId, updates) => {
    get()._pushHistory();
    set((state) => ({
      report: {
        ...state.report,
        appendices: updateAppendices(state.report.appendices, appendixId, (a) => ({
          ...a,
          content: a.content.map((b) =>
            b.id === blockId ? ({ ...b, ...updates } as EditorBlock) : b,
          ),
        })),
      },
      isDirty: true,
    }));
  },

  removeAppendixBlock: (appendixId, blockId) => {
    get()._pushHistory();
    set((state) => ({
      report: {
        ...state.report,
        appendices: updateAppendices(state.report.appendices, appendixId, (a) => ({
          ...a,
          content: a.content.filter((b) => b.id !== blockId),
        })),
      },
      activeBlock: state.activeBlock === blockId ? null : state.activeBlock,
      isDirty: true,
    }));
  },

  reorderAppendixBlocks: (appendixId, fromIndex, toIndex) => {
    get()._pushHistory();
    set((state) => ({
      report: {
        ...state.report,
        appendices: updateAppendices(state.report.appendices, appendixId, (a) => {
          const content = [...a.content];
          const [moved] = content.splice(fromIndex, 1);
          if (moved) {
            content.splice(toIndex, 0, moved);
          }
          return { ...a, content };
        }),
      },
      isDirty: true,
    }));
  },

  duplicateAppendixBlock: (appendixId, blockId) => {
    get()._pushHistory();
    set((state) => ({
      report: {
        ...state.report,
        appendices: updateAppendices(state.report.appendices, appendixId, (a) => {
          const idx = a.content.findIndex((b) => b.id === blockId);
          if (idx === -1) return a;
          const original = a.content[idx]!;
          const { id: _id, ...rest } = original;
          const duplicate = { ...rest, id: generateId() } as EditorBlock;
          const content = [...a.content];
          content.splice(idx + 1, 0, duplicate);
          return { ...a, content };
        }),
      },
      isDirty: true,
    }));
  },

  // --- UI ---
  setActiveSection: (id) => set({ activeSection: id, activeAppendix: null, activeBlock: null }),
  setActiveAppendix: (id) => set({ activeAppendix: id, activeSection: null, activeBlock: null }),
  setActiveBlock: (id) => set({ activeBlock: id }),
  setActivePanel: (panel) => set({ activePanel: panel, activeSection: null, activeAppendix: null, activeBlock: null }),
  setViewMode: (mode) => set({ viewMode: mode }),

  // --- I/O ---
  importJson: (json) => {
    try {
      const parsed = JSON.parse(json) as ReportDefinition;
      if (!parsed.template || !parsed.project) {
        return {
          ok: false,
          errors: ['JSON moet "template" en "project" velden bevatten.'],
        };
      }
      const editorReport = toEditorReport(parsed);
      set({
        report: editorReport,
        activeSection: null,
        activeAppendix: null,
        activeBlock: null,
        activePanel: 'rapport',
        isDirty: false,
        _past: [],
        _future: [],
        canUndo: false,
        canRedo: false,
      });
      return { ok: true, errors: [] };
    } catch (e) {
      return {
        ok: false,
        errors: [e instanceof Error ? e.message : 'Onbekende parse fout'],
      };
    }
  },

  exportJson: () => {
    const definition = toReportDefinition(get().report);
    return JSON.stringify(definition, null, 2);
  },

  loadReport: (definition) => {
    const editorReport = toEditorReport(definition);
    set({
      report: editorReport,
      activeSection: null,
      activeAppendix: null,
      activeBlock: null,
      activePanel: 'rapport',
      isDirty: false,
      _past: [],
      _future: [],
      canUndo: false,
      canRedo: false,
      serverReportId: null,
      serverProjectId: null,
    });
  },

  loadTemplate: (templateName) => {
    const report = createDefaultReport();
    report.template = templateName;
    set({
      report,
      activeSection: null,
      activeAppendix: null,
      activeBlock: null,
      activePanel: 'rapport',
      isDirty: false,
      _past: [],
      _future: [],
      canUndo: false,
      canRedo: false,
      serverReportId: null,
      serverProjectId: null,
    });
  },

  reset: () => {
    localStorage.removeItem(STORAGE_KEY);
    set({
      report: createDefaultReport(),
      activeSection: null,
      activeAppendix: null,
      activeBlock: null,
      activePanel: 'rapport',
      viewMode: 'editor',
      isDirty: false,
      _past: [],
      _future: [],
      canUndo: false,
      canRedo: false,
      lastSavedAt: null,
      serverReportId: null,
      serverProjectId: null,
    });
  },
}));

// ---------- Auto-save to localStorage ----------

export const STORAGE_KEY = 'openaec-report-editor-state';
const SAVE_DEBOUNCE_MS = 1000;

let saveTimeout: ReturnType<typeof setTimeout> | null = null;

useReportStore.subscribe((state, prev) => {
  const reportChanged = state.report !== prev.report;
  const serverIdChanged = state.serverReportId !== prev.serverReportId
    || state.serverProjectId !== prev.serverProjectId;

  if (reportChanged || serverIdChanged) {
    // Auto-save to localStorage
    if (saveTimeout) clearTimeout(saveTimeout);
    saveTimeout = setTimeout(() => {
      try {
        const data = {
          report: toReportDefinition(state.report),
          savedAt: new Date().toISOString(),
          serverReportId: state.serverReportId,
          serverProjectId: state.serverProjectId,
          userId: useAuthStore.getState().user?.id ?? null,
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
        useReportStore.setState({ lastSavedAt: data.savedAt });
      } catch (e) {
        console.warn('Auto-save mislukt:', e);
      }
    }, SAVE_DEBOUNCE_MS);
  }

  if (reportChanged) {
    // Auto-preview trigger (lazy import to avoid circular dependency)
    import('./apiStore').then(({ useApiStore }) => {
      useApiStore.getState().schedulePreview();
    });
  }
});
