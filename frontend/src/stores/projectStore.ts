import { create } from "zustand";
import type {
  Project,
  ReportSummary,
} from "@/types/project";
import { mapProject, mapReportSummary } from "@/types/project";
import type { EditorReport } from "@/types/report";
import { toReportDefinition } from "@/utils/conversion";

const API_BASE = import.meta.env.VITE_API_URL || "";

interface ProjectStore {
  projects: Project[];
  reports: ReportSummary[];
  selectedProjectId: string | null;
  loading: boolean;
  error: string | null;

  // Projecten
  fetchProjects: () => Promise<void>;
  createProject: (
    name: string,
    description?: string,
  ) => Promise<Project | null>;
  updateProject: (
    id: string,
    fields: { name?: string; description?: string },
  ) => Promise<void>;
  deleteProject: (id: string) => Promise<void>;
  selectProject: (id: string | null) => void;

  // Rapporten
  fetchReports: (projectId?: string | null) => Promise<void>;
  saveReport: (
    report: EditorReport,
    options?: {
      id?: string;
      title?: string;
      projectId?: string | null;
    },
  ) => Promise<string | null>;
  loadReport: (
    id: string,
  ) => Promise<Record<string, unknown> | null>;
  deleteReport: (id: string) => Promise<void>;
  moveReport: (
    id: string,
    projectId: string | null,
  ) => Promise<void>;

  clearError: () => void;
}

async function apiFetch(
  path: string,
  options?: RequestInit,
): Promise<Response> {
  return fetch(`${API_BASE}${path}`, {
    credentials: "include",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
}

export const useProjectStore = create<ProjectStore>((set, get) => ({
  projects: [],
  reports: [],
  selectedProjectId: null,
  loading: false,
  error: null,

  // ============================================================
  // Projecten
  // ============================================================

  fetchProjects: async () => {
    set({ loading: true, error: null });
    try {
      const res = await apiFetch("/api/projects");
      if (res.ok) {
        const data = await res.json();
        const projects = (
          data.projects as Record<string, unknown>[]
        ).map(mapProject);
        set({ projects, loading: false });
      } else {
        set({ error: "Kan projecten niet laden", loading: false });
      }
    } catch {
      set({
        error: "Kan geen verbinding maken met de server",
        loading: false,
      });
    }
  },

  createProject: async (name, description) => {
    set({ error: null });
    try {
      const res = await apiFetch("/api/projects", {
        method: "POST",
        body: JSON.stringify({ name, description: description || "" }),
      });
      if (res.ok) {
        const raw = await res.json();
        const project = mapProject(raw);
        set((s) => ({ projects: [project, ...s.projects] }));
        return project;
      }
      const body = await res.json().catch(() => ({}));
      set({
        error:
          (body as Record<string, string>).detail ||
          "Project aanmaken mislukt",
      });
      return null;
    } catch {
      set({ error: "Kan geen verbinding maken met de server" });
      return null;
    }
  },

  updateProject: async (id, fields) => {
    set({ error: null });
    try {
      const res = await apiFetch(`/api/projects/${id}`, {
        method: "PUT",
        body: JSON.stringify(fields),
      });
      if (res.ok) {
        const raw = await res.json();
        const updated = mapProject(raw);
        set((s) => ({
          projects: s.projects.map((p) =>
            p.id === id ? { ...updated, reportCount: p.reportCount } : p,
          ),
        }));
      }
    } catch {
      set({ error: "Project bijwerken mislukt" });
    }
  },

  deleteProject: async (id) => {
    set({ error: null });
    try {
      const res = await apiFetch(`/api/projects/${id}`, {
        method: "DELETE",
      });
      if (res.ok) {
        set((s) => ({
          projects: s.projects.filter((p) => p.id !== id),
          selectedProjectId:
            s.selectedProjectId === id ? null : s.selectedProjectId,
          reports:
            s.selectedProjectId === id ? [] : s.reports,
        }));
      }
    } catch {
      set({ error: "Project verwijderen mislukt" });
    }
  },

  selectProject: (id) => {
    set({ selectedProjectId: id });
    get().fetchReports(id);
  },

  // ============================================================
  // Rapporten
  // ============================================================

  fetchReports: async (projectId) => {
    set({ loading: true, error: null });
    try {
      const query = projectId ? `?project_id=${projectId}` : "";
      const res = await apiFetch(`/api/reports${query}`);
      if (res.ok) {
        const data = await res.json();
        const reports = (
          data.reports as Record<string, unknown>[]
        ).map(mapReportSummary);
        set({ reports, loading: false });
      } else {
        set({ error: "Kan rapporten niet laden", loading: false });
      }
    } catch {
      set({
        error: "Kan geen verbinding maken met de server",
        loading: false,
      });
    }
  },

  saveReport: async (report, options) => {
    set({ error: null });
    try {
      const content = toReportDefinition(report);
      const body = {
        id: options?.id || "",
        title:
          options?.title || report.project || "Naamloos rapport",
        template: report.template,
        project_id: options?.projectId ?? null,
        content,
      };
      const res = await apiFetch("/api/reports", {
        method: "POST",
        body: JSON.stringify(body),
      });
      if (res.ok) {
        const data = await res.json();
        // Refresh lijst als we in een project zitten
        const state = get();
        if (state.selectedProjectId !== undefined) {
          get().fetchReports(state.selectedProjectId);
        }
        return data.id as string;
      }
      const errBody = await res.json().catch(() => ({}));
      set({
        error:
          (errBody as Record<string, string>).detail ||
          "Rapport opslaan mislukt",
      });
      return null;
    } catch {
      set({ error: "Kan geen verbinding maken met de server" });
      return null;
    }
  },

  loadReport: async (id) => {
    set({ loading: true, error: null });
    try {
      const res = await apiFetch(`/api/reports/${id}`);
      if (res.ok) {
        const data = await res.json();
        set({ loading: false });
        return data.content as Record<string, unknown>;
      }
      set({ error: "Rapport niet gevonden", loading: false });
      return null;
    } catch {
      set({
        error: "Kan geen verbinding maken met de server",
        loading: false,
      });
      return null;
    }
  },

  deleteReport: async (id) => {
    set({ error: null });
    try {
      const res = await apiFetch(`/api/reports/${id}`, {
        method: "DELETE",
      });
      if (res.ok) {
        set((s) => ({
          reports: s.reports.filter((r) => r.id !== id),
        }));
      }
    } catch {
      set({ error: "Rapport verwijderen mislukt" });
    }
  },

  moveReport: async (id, projectId) => {
    set({ error: null });
    try {
      const res = await apiFetch(`/api/reports/${id}/move`, {
        method: "PUT",
        body: JSON.stringify({ project_id: projectId }),
      });
      if (res.ok) {
        // Refresh huidige lijst
        const state = get();
        get().fetchReports(state.selectedProjectId);
        get().fetchProjects();
      }
    } catch {
      set({ error: "Rapport verplaatsen mislukt" });
    }
  },

  clearError: () => set({ error: null }),
}));
