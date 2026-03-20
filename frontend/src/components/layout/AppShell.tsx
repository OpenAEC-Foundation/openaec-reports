import { useState, useEffect, useRef, useCallback } from "react";
import { useReportStore } from "@/stores/reportStore";
import { useApiStore } from "@/stores/apiStore";
import { useProjectStore } from "@/stores/projectStore";
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";
import { getSetting, setSetting } from "@/utils/settingsStore";
import { ErrorBoundary } from "@/components/shared/ErrorBoundary";
import TitleBar from "@/components/chrome/TitleBar";
import Ribbon from "@/components/chrome/ribbon/Ribbon";
import StatusBar from "@/components/chrome/StatusBar";
import Backstage from "@/components/chrome/backstage/Backstage";
import { SaveAsDialog } from "@/components/chrome/backstage/SaveAsDialog";
import { OpenDialog } from "@/components/chrome/backstage/OpenDialog";
import SettingsDialog, { applyTheme } from "@/components/chrome/settings/SettingsDialog";
import { Sidebar } from "./Sidebar";
import { MainPanel } from "./MainPanel";
import { ValidationBanner } from "./ValidationBanner";
import { ShortcutHelp } from "./ShortcutHelp";
import { AdminPanel } from "@/components/admin/AdminPanel";
import { ProjectBrowser } from "@/components/projects/ProjectBrowser";

const SIDEBAR_VISIBLE_KEY = "openaec-sidebar-visible";

export function AppShell() {
  const viewMode = useReportStore((s) => s.viewMode);
  const setViewMode = useReportStore((s) => s.setViewMode);
  const exportJson = useReportStore((s) => s.exportJson);
  const importJson = useReportStore((s) => s.importJson);
  const report = useReportStore((s) => s.report);

  const error = useApiStore((s) => s.error);
  const validateReport = useApiStore((s) => s.validateReport);
  const clearError = useApiStore((s) => s.clearError);

  const saveReport = useProjectStore((s) => s.saveReport);
  const [isSaving, setIsSaving] = useState(false);

  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [backstageOpen, setBackstageOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [saveAsOpen, setSaveAsOpen] = useState(false);
  const [openDialogOpen, setOpenDialogOpen] = useState(false);
  const [theme, setTheme] = useState(() => getSetting("theme", "light"));
  const [sidebarVisible, setSidebarVisible] = useState(() => {
    try {
      const stored = localStorage.getItem(SIDEBAR_VISIBLE_KEY);
      return stored !== "false";
    } catch {
      return true;
    }
  });
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragCountRef = useRef(0);

  // Persist sidebar visibility
  const toggleSidebar = useCallback(() => {
    setSidebarVisible((prev) => {
      const next = !prev;
      try { localStorage.setItem(SIDEBAR_VISIBLE_KEY, String(next)); } catch { /* noop */ }
      return next;
    });
  }, []);

  // Auto-dismiss toast
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 3000);
    return () => clearTimeout(timer);
  }, [toast]);

  // Show API errors as toast
  useEffect(() => {
    if (error) {
      setToast({ message: error, type: "error" });
      clearError();
    }
  }, [error, clearError]);

  // Save to server
  const handleSaveToServer = useCallback(async () => {
    if (isSaving) return;
    setIsSaving(true);
    try {
      const state = useReportStore.getState();
      const reportId = await saveReport(state.report, {
        id: state.serverReportId ?? undefined,
        title: state.report.project || "Naamloos rapport",
        projectId: state.serverProjectId,
      });
      if (reportId) {
        useReportStore.setState({
          serverReportId: reportId,
          isDirty: false,
        });
        setToast({ message: "Rapport opgeslagen op server", type: "success" });
      }
    } finally {
      setIsSaving(false);
    }
  }, [isSaving, saveReport]);

  // Keyboard shortcuts
  useKeyboardShortcuts({
    onSave: handleSaveToServer,
    onToggleShortcuts: () => setShowShortcuts((v) => !v),
  });

  // Export JSON
  function handleExport() {
    const json = exportJson();
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${report.project_number || "rapport"}_${report.template}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // Validate
  async function handleValidate() {
    const valid = await validateReport();
    if (valid) {
      setToast({ message: "Rapport is geldig", type: "success" });
    }
  }

  // Import
  function handleImportFile(json: string, filename: string) {
    const result = importJson(json);
    if (result.ok) {
      setToast({ message: `Rapport "${filename}" geladen`, type: "success" });
    } else {
      setToast({ message: result.errors[0] ?? "Import mislukt", type: "error" });
    }
  }

  function handleImportClick() {
    fileInputRef.current?.click();
  }

  function handleFileInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => handleImportFile(reader.result as string, file.name);
    reader.readAsText(file);
    e.target.value = "";
  }

  // Drag-drop
  function handleDragEnter(e: React.DragEvent) {
    e.preventDefault();
    dragCountRef.current++;
    if (dragCountRef.current === 1) setDragOver(true);
  }

  function handleDragLeave(e: React.DragEvent) {
    e.preventDefault();
    dragCountRef.current--;
    if (dragCountRef.current === 0) setDragOver(false);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    dragCountRef.current = 0;
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (!file || !file.name.endsWith(".json")) return;
    const reader = new FileReader();
    reader.onload = () => handleImportFile(reader.result as string, file.name);
    reader.readAsText(file);
  }

  // Theme change handler
  function handleThemeChange(newTheme: string) {
    setTheme(newTheme);
    applyTheme(newTheme);
    setSetting("theme", newTheme);
  }

  return (
    <div
      className="flex h-screen flex-col relative"
      data-theme={theme}
      onDragEnter={handleDragEnter}
      onDragOver={(e) => e.preventDefault()}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Drag overlay */}
      {dragOver && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-brand-primary/10 border-2 border-dashed border-brand-primary pointer-events-none">
          <div className="rounded-xl bg-white px-8 py-6 shadow-lg text-center">
            <p className="text-lg font-medium text-brand-primary-dark">JSON rapport importeren</p>
            <p className="text-sm text-gray-500">Laat los om te laden</p>
          </div>
        </div>
      )}

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        className="hidden"
        onChange={handleFileInputChange}
      />

      {/* Title bar */}
      <TitleBar
        onSave={handleSaveToServer}
        onSettingsClick={() => setSettingsOpen(true)}
        onHelpClick={() => setShowShortcuts(true)}
        isSaving={isSaving}
      />

      {/* Ribbon */}
      <Ribbon
        onFileTabClick={() => setBackstageOpen(true)}
        onValidate={handleValidate}
        sidebarVisible={sidebarVisible}
        onToggleSidebar={toggleSidebar}
      />

      {/* Validation banner */}
      <ValidationBanner />

      {/* Floating toast notifications */}
      {toast && (
        <div className="fixed top-36 right-4 z-50 animate-slide-in-right">
          <div className={`rounded-lg shadow-lg px-4 py-3 flex items-center gap-2 ${
            toast.type === "success"
              ? "bg-green-600 text-white"
              : "bg-red-600 text-white"
          }`}>
            {toast.type === "success" ? (
              <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
            ) : (
              <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            )}
            <span className="text-sm font-medium">{toast.message}</span>
          </div>
        </div>
      )}

      {/* Main content */}
      {viewMode === "projects" ? (
        <div className="flex-1 overflow-hidden">
          <ProjectBrowser onOpenReport={() => setViewMode("editor")} />
        </div>
      ) : viewMode === "admin" ? (
        <div className="flex-1 overflow-auto">
          <AdminPanel />
        </div>
      ) : (
        <div className="flex flex-1 overflow-hidden">
          {sidebarVisible && <Sidebar />}
          <ErrorBoundary context="MainPanel" fallback={<AppCrashFallback />}>
            <MainPanel />
          </ErrorBoundary>
        </div>
      )}

      {/* Status bar */}
      <StatusBar />

      {/* Backstage */}
      <Backstage
        open={backstageOpen}
        onClose={() => setBackstageOpen(false)}
        onOpenSettings={() => setSettingsOpen(true)}
        onSave={handleSaveToServer}
        onSaveAs={() => setSaveAsOpen(true)}
        onOpenDialog={() => setOpenDialogOpen(true)}
        onOpenProjects={() => setViewMode("projects")}
      />

      {/* Save As dialog */}
      <SaveAsDialog
        open={saveAsOpen}
        onClose={() => setSaveAsOpen(false)}
        onSaveServer={handleSaveToServer}
        onSaveLocal={handleExport}
      />

      {/* Open dialog */}
      <OpenDialog
        open={openDialogOpen}
        onClose={() => setOpenDialogOpen(false)}
        onOpenServer={() => setViewMode("projects")}
        onOpenLocal={handleImportClick}
      />

      {/* Settings dialog */}
      <SettingsDialog
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        theme={theme}
        onThemeChange={handleThemeChange}
      />

      {/* Shortcut help dialog */}
      <ShortcutHelp open={showShortcuts} onClose={() => setShowShortcuts(false)} />
    </div>
  );
}

function AppCrashFallback() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8 text-center">
      <div className="rounded-full bg-red-100 p-4">
        <svg className="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
        </svg>
      </div>
      <p className="text-sm font-medium text-gray-700">Er is een fout opgetreden in de editor</p>
      <p className="text-xs text-gray-500">Probeer het rapport te resetten of herlaad de pagina</p>
      <div className="flex gap-3">
        <button
          onClick={() => useReportStore.getState().reset()}
          className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 transition-colors"
        >
          Reset rapport
        </button>
        <button
          onClick={() => window.location.reload()}
          className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
        >
          Herlaad pagina
        </button>
      </div>
    </div>
  );
}
