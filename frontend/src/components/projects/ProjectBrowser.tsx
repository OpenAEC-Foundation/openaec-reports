import { useEffect, useState } from "react";
import { useProjectStore } from "@/stores/projectStore";
import { useReportStore } from "@/stores/reportStore";
import brand from "@/config/brand";
import type { Project } from "@/types/project";
import type { ReportDefinition } from "@/types/report";

interface ProjectBrowserProps {
  onOpenReport: () => void;
}

export function ProjectBrowser({ onOpenReport }: ProjectBrowserProps) {
  const projects = useProjectStore((s) => s.projects);
  const reports = useProjectStore((s) => s.reports);
  const selectedProjectId = useProjectStore((s) => s.selectedProjectId);
  const loading = useProjectStore((s) => s.loading);
  const error = useProjectStore((s) => s.error);
  const fetchProjects = useProjectStore((s) => s.fetchProjects);
  const fetchReports = useProjectStore((s) => s.fetchReports);
  const createProject = useProjectStore((s) => s.createProject);
  const deleteProject = useProjectStore((s) => s.deleteProject);
  const selectProject = useProjectStore((s) => s.selectProject);
  const loadReport = useProjectStore((s) => s.loadReport);
  const deleteReport = useProjectStore((s) => s.deleteReport);
  const clearError = useProjectStore((s) => s.clearError);
  const loadReportInEditor = useReportStore((s) => s.loadReport);

  const [newProjectName, setNewProjectName] = useState("");
  const [showNewProject, setShowNewProject] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  useEffect(() => {
    fetchProjects();
    // Laad "losse rapporten" standaard (geen project filter)
    fetchReports(null);
  }, [fetchProjects, fetchReports]);

  async function handleCreateProject() {
    if (!newProjectName.trim()) return;
    await createProject(newProjectName.trim());
    setNewProjectName("");
    setShowNewProject(false);
  }

  async function handleOpenReport(reportId: string) {
    const content = await loadReport(reportId);
    if (content) {
      loadReportInEditor(content as unknown as ReportDefinition);
      // Sla server report ID op zodat we later weer naar dezelfde kunnen saven
      useReportStore.setState({
        serverReportId: reportId,
        serverProjectId: selectedProjectId,
      });
      onOpenReport();
    }
  }

  async function handleDeleteProject(id: string) {
    await deleteProject(id);
    setConfirmDelete(null);
  }

  async function handleDeleteReport(id: string) {
    await deleteReport(id);
    setConfirmDelete(null);
  }

  function formatDate(iso: string): string {
    try {
      return new Date(iso).toLocaleDateString("nl-NL", {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return iso;
    }
  }

  return (
    <div className="flex h-full">
      {/* Links: Projectlijst */}
      <div className="w-72 shrink-0 border-r border-gray-200 bg-gray-50 flex flex-col">
        <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
          <h2 className="text-sm font-semibold text-gray-900">Projecten</h2>
          <button
            onClick={() => setShowNewProject(true)}
            className="rounded-md px-2 py-1 text-xs font-medium text-white transition-colors"
            style={{ backgroundColor: brand.colors.primary }}
          >
            + Nieuw
          </button>
        </div>

        {/* Nieuw project formulier */}
        {showNewProject && (
          <div className="border-b border-gray-200 bg-white p-3">
            <input
              type="text"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreateProject()}
              placeholder="Projectnaam..."
              className="mb-2 w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-1"
              style={
                { "--tw-ring-color": brand.colors.primary } as React.CSSProperties
              }
              autoFocus
            />
            <div className="flex gap-2">
              <button
                onClick={handleCreateProject}
                disabled={!newProjectName.trim()}
                className="rounded px-2 py-1 text-xs font-medium text-white disabled:opacity-50"
                style={{ backgroundColor: brand.colors.primary }}
              >
                Aanmaken
              </button>
              <button
                onClick={() => {
                  setShowNewProject(false);
                  setNewProjectName("");
                }}
                className="rounded px-2 py-1 text-xs text-gray-500 hover:text-gray-700"
              >
                Annuleren
              </button>
            </div>
          </div>
        )}

        {/* Projectlijst */}
        <div className="flex-1 overflow-y-auto">
          {/* "Alle rapporten" item */}
          <button
            onClick={() => {
              selectProject(null);
              fetchReports(null);
            }}
            className={`w-full px-4 py-3 text-left text-sm transition-colors ${
              selectedProjectId === null
                ? "bg-white font-medium border-l-2"
                : "hover:bg-white/50"
            }`}
            style={
              selectedProjectId === null
                ? { borderColor: brand.colors.primary, color: brand.colors.primary }
                : {}
            }
          >
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4 shrink-0 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
              Alle rapporten
            </div>
          </button>

          {projects.map((project) => (
            <ProjectItem
              key={project.id}
              project={project}
              isSelected={selectedProjectId === project.id}
              onSelect={() => selectProject(project.id)}
              onDelete={() => setConfirmDelete(`project:${project.id}`)}
              confirmDelete={confirmDelete === `project:${project.id}`}
              onConfirmDelete={() => handleDeleteProject(project.id)}
              onCancelDelete={() => setConfirmDelete(null)}
            />
          ))}

          {projects.length === 0 && !loading && (
            <p className="px-4 py-6 text-center text-xs text-gray-400">
              Nog geen projecten
            </p>
          )}
        </div>
      </div>

      {/* Rechts: Rapportenlijst */}
      <div className="flex-1 flex flex-col bg-white">
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-3">
          <h2 className="text-sm font-semibold text-gray-900">
            {selectedProjectId
              ? projects.find((p) => p.id === selectedProjectId)?.name ||
                "Rapporten"
              : "Alle rapporten"}
          </h2>
        </div>

        {error && (
          <div className="mx-6 mt-3 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
            <button
              onClick={clearError}
              className="ml-2 text-red-500 hover:text-red-700"
            >
              Sluiten
            </button>
          </div>
        )}

        {loading ? (
          <div className="flex flex-1 items-center justify-center">
            <svg
              className="h-6 w-6 animate-spin text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
          </div>
        ) : reports.length === 0 ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-3 text-center">
            <svg className="h-12 w-12 text-gray-300" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
            <p className="text-sm text-gray-500">Nog geen rapporten</p>
            <p className="text-xs text-gray-400">
              Maak een rapport in de editor en sla het hier op
            </p>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-100 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  <th className="px-6 py-2">Titel</th>
                  <th className="px-6 py-2">Template</th>
                  <th className="px-6 py-2">Laatst gewijzigd</th>
                  <th className="px-6 py-2 w-24"></th>
                </tr>
              </thead>
              <tbody>
                {reports.map((report) => (
                  <tr
                    key={report.id}
                    className="border-b border-gray-50 hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => handleOpenReport(report.id)}
                  >
                    <td className="px-6 py-3 text-sm font-medium text-gray-900">
                      {report.title}
                    </td>
                    <td className="px-6 py-3 text-sm text-gray-500">
                      {report.template || "-"}
                    </td>
                    <td className="px-6 py-3 text-sm text-gray-500">
                      {formatDate(report.updatedAt)}
                    </td>
                    <td className="px-6 py-3">
                      <div className="flex gap-1">
                        {confirmDelete === `report:${report.id}` ? (
                          <>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteReport(report.id);
                              }}
                              className="rounded px-2 py-1 text-xs font-medium text-white bg-red-500 hover:bg-red-600"
                            >
                              Bevestig
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setConfirmDelete(null);
                              }}
                              className="rounded px-2 py-1 text-xs text-gray-500 hover:text-gray-700"
                            >
                              Annuleer
                            </button>
                          </>
                        ) : (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setConfirmDelete(`report:${report.id}`);
                            }}
                            className="rounded p-1 text-gray-400 hover:text-red-500 transition-colors"
                            title="Verwijderen"
                          >
                            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                            </svg>
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================
// Sub-componenten
// ============================================================

function ProjectItem({
  project,
  isSelected,
  onSelect,
  onDelete,
  confirmDelete,
  onConfirmDelete,
  onCancelDelete,
}: {
  project: Project;
  isSelected: boolean;
  onSelect: () => void;
  onDelete: () => void;
  confirmDelete: boolean;
  onConfirmDelete: () => void;
  onCancelDelete: () => void;
}) {
  return (
    <div
      onClick={onSelect}
      className={`group flex cursor-pointer items-center justify-between px-4 py-3 text-sm transition-colors ${
        isSelected
          ? "bg-white font-medium border-l-2"
          : "hover:bg-white/50"
      }`}
      style={
        isSelected
          ? { borderColor: brand.colors.primary, color: brand.colors.primary }
          : {}
      }
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <svg className="h-4 w-4 shrink-0 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
          </svg>
          <span className="truncate">{project.name}</span>
        </div>
        {project.reportCount !== undefined && (
          <span className="ml-6 text-xs text-gray-400">
            {project.reportCount} rapport{project.reportCount !== 1 ? "en" : ""}
          </span>
        )}
      </div>

      {confirmDelete ? (
        <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={onConfirmDelete}
            className="rounded px-1.5 py-0.5 text-xs font-medium text-white bg-red-500 hover:bg-red-600"
          >
            Ja
          </button>
          <button
            onClick={onCancelDelete}
            className="rounded px-1.5 py-0.5 text-xs text-gray-500"
          >
            Nee
          </button>
        </div>
      ) : (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="rounded p-1 text-gray-400 opacity-0 group-hover:opacity-100 hover:text-red-500 transition-all"
          title="Verwijderen"
        >
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  );
}
