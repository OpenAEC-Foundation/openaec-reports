import { useState, useEffect, useRef, useCallback } from 'react';
import { useReportStore } from '@/stores/reportStore';
import { useApiStore } from '@/stores/apiStore';
import { useAuthStore } from '@/stores/authStore';
import { ErrorBoundary } from '@/components/shared/ErrorBoundary';
import brand from '@/config/brand';
import { Sidebar } from './Sidebar';
import { MainPanel } from './MainPanel';
import { ValidationBanner } from './ValidationBanner';
import { ShortcutHelp } from './ShortcutHelp';
import { AdminPanel } from '@/components/admin/AdminPanel';
import type { ViewMode } from '@/stores/reportStore';

const EDITOR_TABS: { mode: ViewMode; label: string }[] = [
  { mode: 'editor', label: 'Editor' },
  { mode: 'split', label: 'Split' },
  { mode: 'json', label: 'JSON' },
  { mode: 'preview', label: 'Preview' },
];

export function AppShell() {
  const viewMode = useReportStore((s) => s.viewMode);
  const setViewMode = useReportStore((s) => s.setViewMode);
  const isDirty = useReportStore((s) => s.isDirty);
  const lastSavedAt = useReportStore((s) => s.lastSavedAt);
  const exportJson = useReportStore((s) => s.exportJson);
  const importJson = useReportStore((s) => s.importJson);
  const report = useReportStore((s) => s.report);

  const canUndo = useReportStore((s) => s.canUndo);
  const canRedo = useReportStore((s) => s.canRedo);
  const undo = useReportStore((s) => s.undo);
  const redo = useReportStore((s) => s.redo);

  const authUser = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const connected = useApiStore((s) => s.connected);
  const isValidating = useApiStore((s) => s.isValidating);
  const isGenerating = useApiStore((s) => s.isGenerating);
  const lastPdfUrl = useApiStore((s) => s.lastPdfUrl);
  const error = useApiStore((s) => s.error);
  const validateReport = useApiStore((s) => s.validateReport);
  const generatePdf = useApiStore((s) => s.generatePdf);
  const downloadPdf = useApiStore((s) => s.downloadPdf);
  const clearError = useApiStore((s) => s.clearError);

  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragCountRef = useRef(0);

  // Auto-dismiss toast
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 3000);
    return () => clearTimeout(timer);
  }, [toast]);

  // Show API errors as toast
  useEffect(() => {
    if (error) {
      setToast({ message: error, type: 'error' });
      clearError();
    }
  }, [error, clearError]);

  // Helper to add block to active section
  const addBlockToActiveSection = useCallback((blockType: 'paragraph' | 'calculation' | 'table') => {
    const state = useReportStore.getState();
    if (state.activeSection) {
      state.addNewBlock(state.activeSection, blockType);
    } else if (state.activeAppendix) {
      state.addNewAppendixBlock(state.activeAppendix, blockType);
    }
  }, []);

  // Global keyboard shortcuts
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      const target = e.target as HTMLElement;
      const isTyping = target.tagName === 'TEXTAREA' || target.tagName === 'INPUT' || target.isContentEditable;

      const mod = e.metaKey || e.ctrlKey;
      const shift = e.shiftKey;

      let key = '';
      if (mod) key += 'ctrl+';
      if (shift) key += 'shift+';
      key += e.key.toLowerCase();

      // Shortcuts that always work (even when typing)
      const alwaysActive: Record<string, () => void> = {
        'ctrl+s': () => handleExport(),
        'ctrl+z': () => useReportStore.getState().undo(),
        'ctrl+y': () => useReportStore.getState().redo(),
        'ctrl+shift+z': () => useReportStore.getState().redo(),
        'ctrl+enter': () => useApiStore.getState().generatePdf(),
      };

      const alwaysHandler = alwaysActive[key];
      if (alwaysHandler) {
        e.preventDefault();
        alwaysHandler();
        return;
      }

      // Shortcuts that only work when NOT typing
      if (!isTyping) {
        const contextual: Record<string, () => void> = {
          'ctrl+1': () => useReportStore.getState().setViewMode('editor'),
          'ctrl+2': () => useReportStore.getState().setViewMode('split'),
          'ctrl+3': () => useReportStore.getState().setViewMode('json'),
          'ctrl+4': () => useReportStore.getState().setViewMode('preview'),
          'ctrl+shift+p': () => addBlockToActiveSection('paragraph'),
          'ctrl+shift+k': () => addBlockToActiveSection('calculation'),
          'ctrl+shift+t': () => addBlockToActiveSection('table'),
          'escape': () => useReportStore.getState().setActiveBlock(null),
        };

        const contextHandler = contextual[key];
        if (contextHandler) {
          e.preventDefault();
          contextHandler();
          return;
        }

        // ? key for help (no modifier)
        if (e.key === '?' && !mod && !e.altKey) {
          e.preventDefault();
          setShowShortcuts((v) => !v);
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [addBlockToActiveSection]);

  function handleExport() {
    const json = exportJson();
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${report.project_number || 'rapport'}_${report.template}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function handleValidate() {
    const valid = await validateReport();
    if (valid) {
      setToast({ message: 'Rapport is geldig', type: 'success' });
    }
  }

  function handleImportFile(json: string, filename: string) {
    const result = importJson(json);
    if (result.ok) {
      setToast({ message: `Rapport "${filename}" geladen`, type: 'success' });
    } else {
      setToast({ message: result.errors[0] ?? 'Import mislukt', type: 'error' });
    }
  }

  function handleFileInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => handleImportFile(reader.result as string, file.name);
    reader.readAsText(file);
    e.target.value = '';
  }

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
    if (!file || !file.name.endsWith('.json')) return;
    const reader = new FileReader();
    reader.onload = () => handleImportFile(reader.result as string, file.name);
    reader.readAsText(file);
  }

  return (
    <div
      className="flex h-screen flex-col relative"
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

      {/* Branded header */}
      <header className="flex h-12 shrink-0 items-center justify-between bg-brand-header-bg px-4 border-b-2 border-brand-primary">
        {/* Left: logo + view mode tabs */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="font-bold text-lg tracking-tight">
              <span className="text-white">{brand.namePrefix}</span>
              <span className="text-brand-primary">{brand.nameAccent}</span>
            </span>
            <span className="text-white/50 text-sm font-medium">{brand.productName}</span>
          </div>

          <div className="flex rounded-lg bg-white/10 p-0.5">
            {EDITOR_TABS.map((tab) => (
              <button
                key={tab.mode}
                onClick={() => setViewMode(tab.mode)}
                className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                  viewMode === tab.mode
                    ? 'bg-white/15 text-white'
                    : 'text-white/50 hover:text-white/80'
                }`}
              >
                {tab.label}
              </button>
            ))}
            {authUser?.role === 'admin' && (
              <button
                onClick={() => setViewMode('admin')}
                className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ml-1 border-l border-white/10 pl-2 ${
                  viewMode === 'admin'
                    ? 'bg-white/15 text-white'
                    : 'text-white/50 hover:text-white/80'
                }`}
              >
                Admin
              </button>
            )}
          </div>

          {isDirty ? (
            <span className="text-xs text-amber-400 font-medium">Onopgeslagen wijzigingen</span>
          ) : lastSavedAt ? (
            <span className="text-xs text-white/30">Opgeslagen</span>
          ) : null}
        </div>

        {/* Right: action buttons */}
        <div className="flex items-center gap-2">
          {/* Help */}
          <button
            onClick={() => setShowShortcuts(true)}
            title="Sneltoetsen (?)"
            className="rounded-md px-2 py-1.5 text-xs text-white/40 hover:text-white/70 hover:bg-white/10 transition-colors"
          >
            ?
          </button>

          {/* Undo/Redo */}
          <div className="flex items-center border-r border-white/10 pr-2 mr-1">
            <button
              onClick={undo}
              disabled={!canUndo}
              title="Ongedaan maken (Ctrl+Z)"
              className="rounded-md px-2 py-1.5 text-white/40 hover:text-white/70 hover:bg-white/10 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 15L3 9m0 0l6-6M3 9h12a6 6 0 010 12h-3" />
              </svg>
            </button>
            <button
              onClick={redo}
              disabled={!canRedo}
              title="Opnieuw (Ctrl+Y)"
              className="rounded-md px-2 py-1.5 text-white/40 hover:text-white/70 hover:bg-white/10 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 15l6-6m0 0l-6-6m6 6H9a6 6 0 000 12h3" />
              </svg>
            </button>
          </div>

          {/* Import JSON */}
          <button
            onClick={() => fileInputRef.current?.click()}
            className="rounded-md border border-white/20 px-3 py-1.5 text-xs font-medium text-white/70 hover:bg-white/10 transition-colors"
          >
            Import JSON
          </button>

          {/* Export JSON */}
          <button
            onClick={handleExport}
            className="rounded-md border border-white/20 px-3 py-1.5 text-xs font-medium text-white/70 hover:bg-white/10 transition-colors"
          >
            Export JSON
          </button>

          {/* Validate */}
          <button
            onClick={handleValidate}
            disabled={!connected || isValidating}
            className="rounded-md border border-white/20 px-3 py-1.5 text-xs font-medium text-white/70 hover:bg-white/10 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isValidating ? (
              <span className="flex items-center gap-1.5">
                <Spinner light /> Valideren...
              </span>
            ) : (
              'Valideer'
            )}
          </button>

          {/* Generate PDF */}
          <button
            onClick={generatePdf}
            disabled={!connected || isGenerating}
            className="rounded-md bg-brand-primary px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-primary-dark transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isGenerating ? (
              <span className="flex items-center gap-1.5">
                <Spinner light /> Genereren...
              </span>
            ) : (
              'Genereer PDF'
            )}
          </button>

          {/* Download PDF */}
          {lastPdfUrl && (
            <button
              onClick={downloadPdf}
              className="rounded-md bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700 transition-colors"
            >
              Download PDF
            </button>
          )}

          {/* User + Logout */}
          {authUser && (
            <div className="flex items-center gap-2 border-l border-white/10 pl-3 ml-1">
              <span className="text-xs text-white/50">
                {authUser.display_name || authUser.username}
              </span>
              <button
                onClick={logout}
                className="rounded-md px-2 py-1.5 text-xs text-white/40 hover:text-white/70 hover:bg-white/10 transition-colors"
              >
                Uitloggen
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Validation banner */}
      <ValidationBanner />

      {/* Floating toast notifications */}
      {toast && (
        <div className="fixed top-14 right-4 z-50 animate-slide-in-right">
          <div className={`rounded-lg shadow-lg px-4 py-3 flex items-center gap-2 ${
            toast.type === 'success'
              ? 'bg-green-600 text-white'
              : 'bg-red-600 text-white'
          }`}>
            {toast.type === 'success' ? (
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
      {viewMode === 'admin' ? (
        <div className="flex-1 overflow-auto">
          <AdminPanel />
        </div>
      ) : (
        <div className="flex flex-1 overflow-hidden">
          <Sidebar />
          <ErrorBoundary context="MainPanel" fallback={<AppCrashFallback />}>
            <MainPanel />
          </ErrorBoundary>
        </div>
      )}

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

function Spinner({ light }: { light?: boolean }) {
  return (
    <svg
      className={`h-3 w-3 animate-spin ${light ? 'text-white/70' : 'text-gray-500'}`}
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}
