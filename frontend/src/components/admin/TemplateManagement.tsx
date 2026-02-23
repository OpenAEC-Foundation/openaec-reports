import { useEffect, useRef } from "react";
import { useAdminStore } from "@/stores/adminStore";

export function TemplateManagement() {
  const tenants = useAdminStore((s) => s.tenants);
  const selectedTenant = useAdminStore((s) => s.selectedTenant);
  const selectTenant = useAdminStore((s) => s.selectTenant);
  const templates = useAdminStore((s) => s.templates);
  const templatesLoading = useAdminStore((s) => s.templatesLoading);
  const loadTemplates = useAdminStore((s) => s.loadTemplates);
  const uploadTemplate = useAdminStore((s) => s.uploadTemplate);
  const deleteTemplate = useAdminStore((s) => s.deleteTemplate);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-select first tenant
  useEffect(() => {
    if (!selectedTenant && tenants.length > 0) {
      selectTenant(tenants[0]!.name);
    }
  }, [tenants, selectedTenant, selectTenant]);

  // Load templates when tenant changes
  useEffect(() => {
    if (selectedTenant) {
      loadTemplates(selectedTenant);
    }
  }, [selectedTenant, loadTemplates]);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !selectedTenant) return;
    await uploadTemplate(selectedTenant, file);
    e.target.value = "";
  }

  async function handleDelete(filename: string) {
    if (!selectedTenant) return;
    if (!confirm(`Template "${filename}" verwijderen?`)) return;
    await deleteTemplate(selectedTenant, filename);
  }

  function formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    return `${(bytes / 1024).toFixed(1)} KB`;
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

        {selectedTenant && (
          <button
            onClick={() => fileInputRef.current?.click()}
            className="rounded-md bg-purple-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-purple-700 transition-colors"
          >
            Upload template
          </button>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept=".yaml,.yml"
          className="hidden"
          onChange={handleUpload}
        />
      </div>

      {/* Template list */}
      {!selectedTenant ? (
        <p className="text-sm text-gray-500 py-8 text-center">
          Selecteer een tenant om templates te beheren
        </p>
      ) : templatesLoading ? (
        <div className="flex items-center gap-2 text-sm text-gray-500 py-8">
          <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Templates laden...
        </div>
      ) : templates.length === 0 ? (
        <div className="rounded-lg border-2 border-dashed border-gray-300 py-12 text-center">
          <p className="text-sm text-gray-500">Geen templates gevonden</p>
          <p className="text-xs text-gray-400 mt-1">Upload een .yaml bestand om te beginnen</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Bestandsnaam
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Grootte
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                  Acties
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {templates.map((t) => (
                <tr key={t.filename}>
                  <td className="px-4 py-3 text-sm font-medium text-gray-700">
                    {t.filename}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {formatSize(t.size)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleDelete(t.filename)}
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
