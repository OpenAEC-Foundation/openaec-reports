import { useEffect, useRef } from "react";
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
}

function YamlFileSection({
  title,
  category,
  files,
  loading,
  tenant,
  onUpload,
  onDelete,
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
          <YamlFileSection
            title="Templates"
            category="templates"
            files={templates}
            loading={templatesLoading}
            tenant={selectedTenant}
            onUpload={uploadTemplate}
            onDelete={deleteTemplate}
          />
          <YamlFileSection
            title="Page Types"
            category="page-types"
            files={pageTypes}
            loading={pageTypesLoading}
            tenant={selectedTenant}
            onUpload={uploadPageType}
            onDelete={deletePageType}
          />
          <YamlFileSection
            title="Modules"
            category="modules"
            files={modules}
            loading={modulesLoading}
            tenant={selectedTenant}
            onUpload={uploadModule}
            onDelete={deleteModule}
          />
        </>
      )}
    </div>
  );
}
