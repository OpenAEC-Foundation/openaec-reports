import { useCallback, useEffect, useRef, useState } from "react";
import jsYaml from "js-yaml";
import { useAdminStore } from "@/stores/adminStore";
import { adminApi, type TenantTemplate, type YamlCategory } from "@/services/api";

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

interface YamlFileSectionProps {
  title: string;
  category: YamlCategory;
  files: TenantTemplate[];
  loading: boolean;
  tenant: string;
  onUpload: (tenant: string, file: File) => Promise<boolean>;
  onDelete: (tenant: string, filename: string) => Promise<boolean>;
  onEdit: (filename: string) => void;
}

function YamlFileSection({
  title,
  category,
  files,
  loading,
  tenant,
  onUpload,
  onDelete,
  onEdit,
}: YamlFileSectionProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    await onUpload(tenant, file);
    e.target.value = "";
  }

  async function handleDelete(filename: string) {
    if (!confirm(`"${filename}" verwijderen?`)) return;
    await onDelete(tenant, filename);
  }

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-800">{title}</h3>
        <button
          onClick={() => fileInputRef.current?.click()}
          className="rounded-md bg-purple-600 px-3 py-1 text-xs font-medium text-white hover:bg-purple-700 transition-colors"
        >
          Upload
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".yaml,.yml"
          className="hidden"
          onChange={handleUpload}
        />
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-sm text-gray-500 py-4">
          <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Laden...
        </div>
      ) : files.length === 0 ? (
        <div className="rounded-lg border-2 border-dashed border-gray-300 py-6 text-center">
          <p className="text-sm text-gray-500">Geen bestanden</p>
          <p className="text-xs text-gray-400 mt-1">Upload een .yaml bestand</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Bestandsnaam
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Grootte
                </th>
                <th className="px-4 py-2 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                  Acties
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {files.map((f) => (
                <tr key={f.filename}>
                  <td className="px-4 py-2 text-sm font-medium text-gray-700">
                    {f.filename}
                  </td>
                  <td className="px-4 py-2 text-sm text-gray-500">
                    {formatSize(f.size)}
                  </td>
                  <td className="px-4 py-2 text-right space-x-2">
                    <button
                      onClick={() => onEdit(f.filename)}
                      className="rounded px-2 py-1 text-xs text-purple-600 hover:bg-purple-50"
                    >
                      Bewerken
                    </button>
                    <a
                      href={adminApi.getYamlDownloadUrl(tenant, category, f.filename)}
                      className="rounded px-2 py-1 text-xs text-blue-600 hover:bg-blue-50"
                      download
                    >
                      Download
                    </a>
                    <button
                      onClick={() => handleDelete(f.filename)}
                      className="rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50"
                    >
                      Verwijderen
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function YamlEditorPanel() {
  const editorFile = useAdminStore((s) => s.editorFile);
  const editorContent = useAdminStore((s) => s.editorContent);
  const editorOriginal = useAdminStore((s) => s.editorOriginal);
  const editorLoading = useAdminStore((s) => s.editorLoading);
  const editorSaving = useAdminStore((s) => s.editorSaving);
  const setEditorContent = useAdminStore((s) => s.setEditorContent);
  const saveEditorContent = useAdminStore((s) => s.saveEditorContent);
  const closeEditor = useAdminStore((s) => s.closeEditor);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [yamlError, setYamlError] = useState<string | null>(null);

  const isDirty = editorContent !== editorOriginal;

  // Client-side YAML validation
  const validateYaml = useCallback((content: string) => {
    try {
      jsYaml.load(content);
      setYamlError(null);
    } catch (e) {
      if (e instanceof jsYaml.YAMLException) {
        setYamlError(e.message);
      }
    }
  }, []);

  function handleChange(value: string) {
    setEditorContent(value);
    validateYaml(value);
  }

  async function handleSave() {
    if (yamlError) return;
    const ok = await saveEditorContent();
    if (ok) {
      setYamlError(null);
    }
  }

  function handleClose() {
    if (isDirty && !confirm("Je hebt onopgeslagen wijzigingen. Sluiten zonder opslaan?")) {
      return;
    }
    closeEditor();
  }

  // Ctrl+S shortcut
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key === "s" && editorFile) {
        e.preventDefault();
        if (!yamlError && isDirty) {
          void saveEditorContent();
        }
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [editorFile, yamlError, isDirty, saveEditorContent]);

  // Tab key inserts 2 spaces
  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Tab") {
      e.preventDefault();
      const ta = e.currentTarget;
      const start = ta.selectionStart;
      const end = ta.selectionEnd;
      const value = ta.value;
      const newValue = value.substring(0, start) + "  " + value.substring(end);
      setEditorContent(newValue);
      validateYaml(newValue);
      // Restore cursor position after React re-render
      requestAnimationFrame(() => {
        ta.selectionStart = ta.selectionEnd = start + 2;
      });
    }
  }

  if (!editorFile) return null;

  return (
    <div className="mb-8 rounded-lg border border-purple-200 bg-purple-50 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-purple-800">
            {editorFile.filename}
          </h3>
          {isDirty && (
            <span className="inline-block h-2 w-2 rounded-full bg-orange-400" title="Onopgeslagen wijzigingen" />
          )}
          <span className="text-xs text-gray-500">
            ({editorFile.category})
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleSave}
            disabled={!isDirty || !!yamlError || editorSaving}
            className="rounded-md bg-purple-600 px-3 py-1 text-xs font-medium text-white hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {editorSaving ? "Opslaan..." : "Opslaan"}
          </button>
          <button
            onClick={handleClose}
            className="rounded-md border border-gray-300 bg-white px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Sluiten
          </button>
        </div>
      </div>

      {editorLoading ? (
        <div className="flex items-center gap-2 text-sm text-gray-500 py-8 justify-center">
          <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Laden...
        </div>
      ) : (
        <>
          <textarea
            ref={textareaRef}
            value={editorContent}
            onChange={(e) => handleChange(e.target.value)}
            onKeyDown={handleKeyDown}
            spellCheck={false}
            className={`w-full rounded-md border p-3 font-mono text-sm leading-relaxed focus:outline-none focus:ring-2 ${
              yamlError
                ? "border-red-300 focus:ring-red-400"
                : "border-gray-300 focus:ring-purple-400"
            }`}
            rows={20}
          />
          {yamlError && (
            <p className="mt-1 text-xs text-red-600 font-mono">{yamlError}</p>
          )}
          <p className="mt-1 text-xs text-gray-400">
            Ctrl+S om op te slaan &middot; Tab voegt 2 spaties in
          </p>
        </>
      )}
    </div>
  );
}

export function TemplateManagement() {
  const tenants = useAdminStore((s) => s.tenants);
  const selectedTenant = useAdminStore((s) => s.selectedTenant);
  const selectTenant = useAdminStore((s) => s.selectTenant);

  const templates = useAdminStore((s) => s.templates);
  const templatesLoading = useAdminStore((s) => s.templatesLoading);
  const loadTemplates = useAdminStore((s) => s.loadTemplates);
  const uploadTemplate = useAdminStore((s) => s.uploadTemplate);
  const deleteTemplate = useAdminStore((s) => s.deleteTemplate);

  const pageTypes = useAdminStore((s) => s.pageTypes);
  const pageTypesLoading = useAdminStore((s) => s.pageTypesLoading);
  const loadPageTypes = useAdminStore((s) => s.loadPageTypes);
  const uploadPageType = useAdminStore((s) => s.uploadPageType);
  const deletePageType = useAdminStore((s) => s.deletePageType);

  const modules = useAdminStore((s) => s.modules);
  const modulesLoading = useAdminStore((s) => s.modulesLoading);
  const loadModules = useAdminStore((s) => s.loadModules);
  const uploadModule = useAdminStore((s) => s.uploadModule);
  const deleteModule = useAdminStore((s) => s.deleteModule);

  const editorFile = useAdminStore((s) => s.editorFile);
  const openEditor = useAdminStore((s) => s.openEditor);
  const closeEditor = useAdminStore((s) => s.closeEditor);
  const editorContent = useAdminStore((s) => s.editorContent);
  const editorOriginal = useAdminStore((s) => s.editorOriginal);

  // Auto-select first tenant
  useEffect(() => {
    if (!selectedTenant && tenants.length > 0) {
      selectTenant(tenants[0]!.name);
    }
  }, [tenants, selectedTenant, selectTenant]);

  // Load all YAML files when tenant changes
  useEffect(() => {
    if (selectedTenant) {
      loadTemplates(selectedTenant);
      loadPageTypes(selectedTenant);
      loadModules(selectedTenant);
    }
  }, [selectedTenant, loadTemplates, loadPageTypes, loadModules]);

  // Close editor when tenant changes
  useEffect(() => {
    if (editorFile && editorFile.tenant !== selectedTenant) {
      closeEditor();
    }
  }, [selectedTenant, editorFile, closeEditor]);

  function handleEdit(category: YamlCategory, filename: string) {
    if (!selectedTenant) return;

    // Warn if switching away from unsaved changes
    if (editorFile && editorContent !== editorOriginal) {
      if (!confirm("Je hebt onopgeslagen wijzigingen. Ander bestand openen?")) {
        return;
      }
    }
    void openEditor(selectedTenant, category, filename);
  }

  return (
    <div>
      {/* Tenant selector */}
      <div className="flex items-center gap-4 mb-6">
        <label className="text-sm font-medium text-gray-700">Tenant:</label>
        <select
          value={selectedTenant ?? ""}
          onChange={(e) => selectTenant(e.target.value || null)}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm shadow-sm focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
        >
          <option value="">Selecteer tenant...</option>
          {tenants.map((t) => (
            <option key={t.name} value={t.name}>{t.name}</option>
          ))}
        </select>
      </div>

      {!selectedTenant ? (
        <p className="text-sm text-gray-500 py-8 text-center">
          Selecteer een tenant om YAML bestanden te beheren
        </p>
      ) : (
        <>
          {/* Editor panel (above file lists when active) */}
          <YamlEditorPanel />

          <YamlFileSection
            title="Templates"
            category="templates"
            files={templates}
            loading={templatesLoading}
            tenant={selectedTenant}
            onUpload={uploadTemplate}
            onDelete={deleteTemplate}
            onEdit={(filename) => handleEdit("templates", filename)}
          />
          <YamlFileSection
            title="Page Types"
            category="page-types"
            files={pageTypes}
            loading={pageTypesLoading}
            tenant={selectedTenant}
            onUpload={uploadPageType}
            onDelete={deletePageType}
            onEdit={(filename) => handleEdit("page-types", filename)}
          />
          <YamlFileSection
            title="Modules"
            category="modules"
            files={modules}
            loading={modulesLoading}
            tenant={selectedTenant}
            onUpload={uploadModule}
            onDelete={deleteModule}
            onEdit={(filename) => handleEdit("modules", filename)}
          />
        </>
      )}
    </div>
  );
}
