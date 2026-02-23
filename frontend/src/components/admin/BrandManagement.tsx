import { useEffect, useRef } from "react";
import { useAdminStore } from "@/stores/adminStore";

export function BrandManagement() {
  const tenants = useAdminStore((s) => s.tenants);
  const selectedTenant = useAdminStore((s) => s.selectedTenant);
  const selectTenant = useAdminStore((s) => s.selectTenant);
  const brandData = useAdminStore((s) => s.brandData);
  const brandLoading = useAdminStore((s) => s.brandLoading);
  const loadBrand = useAdminStore((s) => s.loadBrand);
  const uploadBrand = useAdminStore((s) => s.uploadBrand);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-select first tenant
  useEffect(() => {
    if (!selectedTenant && tenants.length > 0) {
      selectTenant(tenants[0]!.name);
    }
  }, [tenants, selectedTenant, selectTenant]);

  // Load brand when tenant changes
  useEffect(() => {
    if (selectedTenant) {
      loadBrand(selectedTenant);
    }
  }, [selectedTenant, loadBrand]);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !selectedTenant) return;
    await uploadBrand(selectedTenant, file);
    e.target.value = "";
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
            {brandData?.exists ? "Brand vervangen" : "Brand uploaden"}
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

      {/* Brand content */}
      {!selectedTenant ? (
        <p className="text-sm text-gray-500 py-8 text-center">
          Selecteer een tenant om de brand configuratie te bekijken
        </p>
      ) : brandLoading ? (
        <div className="flex items-center gap-2 text-sm text-gray-500 py-8">
          <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Brand laden...
        </div>
      ) : !brandData?.exists ? (
        <div className="rounded-lg border-2 border-dashed border-gray-300 py-12 text-center">
          <p className="text-sm text-gray-500">Geen brand.yaml gevonden voor {selectedTenant}</p>
          <p className="text-xs text-gray-400 mt-1">Upload een brand.yaml bestand om te beginnen</p>
        </div>
      ) : (
        <div>
          {/* Parsed summary */}
          {brandData.parsed && (
            <div className="mb-4 rounded-lg border border-gray-200 bg-gray-50 p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Samenvatting</h3>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                {Object.entries(brandData.parsed).map(([key, value]) => {
                  if (typeof value === "object" && value !== null) return null;
                  return (
                    <div key={key} className="contents">
                      <dt className="text-gray-500">{key}</dt>
                      <dd className="text-gray-700 font-medium">{String(value)}</dd>
                    </div>
                  );
                })}
              </dl>
            </div>
          )}

          {/* Raw YAML */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">brand.yaml (read-only)</h3>
            <pre className="max-h-96 overflow-auto rounded-lg border border-gray-200 bg-gray-900 p-4 text-xs text-gray-100 font-mono">
              {brandData.raw}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
