import { useEffect, useRef, useState } from "react";
import { useAdminStore } from "@/stores/adminStore";
import type { AssetCategory, TenantAsset } from "@/services/api";
import { BrandExtractWizard } from "./BrandExtractWizard";

const ASSET_ACCEPT: Record<AssetCategory, string> = {
  stationery: ".pdf,.png",
  logos: ".svg,.png",
  fonts: ".ttf,.otf",
};

const ASSET_LABELS: Record<AssetCategory, { title: string; description: string }> = {
  stationery: {
    title: "Stationery",
    description: "Achtergrond-PDF's en PNG's voor pagina-templates (bijv. colofon.pdf, standaard.pdf)",
  },
  logos: {
    title: "Logo's",
    description: "Logo bestanden in SVG of PNG formaat",
  },
  fonts: {
    title: "Fonts",
    description: "Lettertype bestanden in TTF of OTF formaat",
  },
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface AssetSectionProps {
  tenant: string;
  category: AssetCategory;
  assets: TenantAsset[];
}

function AssetSection({ tenant, category, assets }: AssetSectionProps) {
  const uploadAsset = useAdminStore((s) => s.uploadAsset);
  const deleteAsset = useAdminStore((s) => s.deleteAsset);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const replaceInputRef = useRef<HTMLInputElement>(null);
  const [replaceTarget, setReplaceTarget] = useState<string | null>(null);
  const info = ASSET_LABELS[category];

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    for (const file of Array.from(files)) {
      await uploadAsset(tenant, category, file);
    }
    e.target.value = "";
  }

  async function handleReplace(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !replaceTarget) return;
    const renamedFile = new File([file], replaceTarget, { type: file.type });
    await uploadAsset(tenant, category, renamedFile);
    setReplaceTarget(null);
    e.target.value = "";
  }

  function startReplace(filename: string) {
    setReplaceTarget(filename);
    setTimeout(() => replaceInputRef.current?.click(), 0);
  }

  async function handleDelete(filename: string) {
    if (!confirm(`'${filename}' verwijderen?`)) return;
    await deleteAsset(tenant, category, filename);
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="text-sm font-semibold text-gray-700">{info.title}</h4>
          <p className="text-xs text-gray-400">{info.description}</p>
        </div>
        <button
          onClick={() => fileInputRef.current?.click()}
          className="rounded-md bg-purple-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-purple-700 transition-colors"
        >
          Uploaden
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept={ASSET_ACCEPT[category]}
          multiple
          className="hidden"
          onChange={handleUpload}
        />
        <input
          ref={replaceInputRef}
          type="file"
          accept={ASSET_ACCEPT[category]}
          className="hidden"
          onChange={handleReplace}
        />
      </div>

      {assets.length === 0 ? (
        <p className="text-xs text-gray-400 italic py-2">Geen bestanden</p>
      ) : (
        <ul className="divide-y divide-gray-100">
          {assets.map((asset) => (
            <li
              key={asset.filename}
              className="flex items-center justify-between py-1.5 text-sm"
            >
              <div className="flex items-center gap-2 min-w-0">
                <span className="text-gray-700 truncate">{asset.filename}</span>
                <span className="text-xs text-gray-400 shrink-0">
                  {formatFileSize(asset.size)}
                </span>
              </div>
              <div className="flex items-center gap-2 shrink-0 ml-2">
                <button
                  onClick={() => startReplace(asset.filename)}
                  className="text-xs text-purple-600 hover:text-purple-800"
                  title="Vervangen"
                >
                  Vervangen
                </button>
                <button
                  onClick={() => handleDelete(asset.filename)}
                  className="text-xs text-red-500 hover:text-red-700"
                  title="Verwijderen"
                >
                  Verwijder
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function BrandManagement() {
  const tenants = useAdminStore((s) => s.tenants);
  const selectedTenant = useAdminStore((s) => s.selectedTenant);
  const selectTenant = useAdminStore((s) => s.selectTenant);
  const brandData = useAdminStore((s) => s.brandData);
  const brandLoading = useAdminStore((s) => s.brandLoading);
  const loadBrand = useAdminStore((s) => s.loadBrand);
  const uploadBrand = useAdminStore((s) => s.uploadBrand);
  const stationeryFiles = useAdminStore((s) => s.stationeryFiles);
  const logoFiles = useAdminStore((s) => s.logoFiles);
  const fontFiles = useAdminStore((s) => s.fontFiles);
  const assetsLoading = useAdminStore((s) => s.assetsLoading);
  const loadAllAssets = useAdminStore((s) => s.loadAllAssets);
  const extractionStep = useAdminStore((s) => s.extractionStep);
  const setExtractionStep = useAdminStore((s) => s.setExtractionStep);

  const brandInputRef = useRef<HTMLInputElement>(null);

  // Auto-select first tenant
  useEffect(() => {
    if (!selectedTenant && tenants.length > 0) {
      selectTenant(tenants[0]!.name);
    }
  }, [tenants, selectedTenant, selectTenant]);

  // Load brand + assets when tenant changes
  useEffect(() => {
    if (selectedTenant) {
      loadBrand(selectedTenant);
      loadAllAssets(selectedTenant);
    }
  }, [selectedTenant, loadBrand, loadAllAssets]);

  async function handleBrandUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !selectedTenant) return;
    await uploadBrand(selectedTenant, file);
    e.target.value = "";
  }

  const isLoading = brandLoading || assetsLoading;

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
          Selecteer een tenant om de brand configuratie te bekijken
        </p>
      ) : isLoading ? (
        <div className="flex items-center gap-2 text-sm text-gray-500 py-8">
          <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Brand laden...
        </div>
      ) : (
        <div className="space-y-6">
          {/* Brand Extractie Wizard */}
          {extractionStep > 0 ? (
            <BrandExtractWizard tenant={selectedTenant} />
          ) : (
            <div className="flex justify-end">
              <button
                onClick={() => setExtractionStep(1)}
                className="rounded-md border border-purple-300 bg-purple-50 px-3 py-1.5 text-xs font-medium text-purple-700 hover:bg-purple-100 transition-colors"
              >
                Brand extractie starten
              </button>
            </div>
          )}

          {/* Brand YAML sectie */}
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h4 className="text-sm font-semibold text-gray-700">Brand configuratie</h4>
                <p className="text-xs text-gray-400">Hoofd brand.yaml bestand met kleuren, fonts, header/footer</p>
              </div>
              <button
                onClick={() => brandInputRef.current?.click()}
                className="rounded-md bg-purple-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-purple-700 transition-colors"
              >
                {brandData?.exists ? "Vervangen" : "Uploaden"}
              </button>
              <input
                ref={brandInputRef}
                type="file"
                accept=".yaml,.yml"
                className="hidden"
                onChange={handleBrandUpload}
              />
            </div>

            {!brandData?.exists ? (
              <p className="text-xs text-gray-400 italic py-2">
                Geen brand.yaml gevonden — upload een bestand om te beginnen
              </p>
            ) : (
              <div>
                {/* Parsed summary */}
                {brandData.parsed && (
                  <div className="mb-3 rounded-md border border-gray-100 bg-gray-50 p-3">
                    <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
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
                <details className="group">
                  <summary className="text-xs font-medium text-gray-500 cursor-pointer hover:text-gray-700">
                    brand.yaml bekijken
                  </summary>
                  <pre className="mt-2 max-h-64 overflow-auto rounded-md border border-gray-200 bg-gray-900 p-3 text-xs text-gray-100 font-mono">
                    {brandData.raw}
                  </pre>
                </details>
              </div>
            )}
          </div>

          {/* Asset secties */}
          <AssetSection
            tenant={selectedTenant}
            category="stationery"
            assets={stationeryFiles}
          />
          <AssetSection
            tenant={selectedTenant}
            category="logos"
            assets={logoFiles}
          />
          <AssetSection
            tenant={selectedTenant}
            category="fonts"
            assets={fontFiles}
          />
        </div>
      )}
    </div>
  );
}
