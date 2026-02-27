import { useEffect, useMemo } from "react";
import { useBrandWizardStore } from "@/stores/brandWizardStore";

// ---------- Known modules ----------

const KNOWN_MODULES = [
  { value: "bic_table", label: "BIC Controles tabel" },
  { value: "cost_summary", label: "Kostenopgave" },
  { value: "location_detail", label: "Locatie details" },
  { value: "object_description", label: "Object beschrijving" },
  { value: "structural_check", label: "Constructieve toetsing" },
  { value: "daylight_calc", label: "Daglichtberekening" },
] as const;

// ---------- Color config ----------

const COLOR_KEYS = [
  { key: "primary", label: "Primary" },
  { key: "secondary", label: "Secondary" },
  { key: "text", label: "Text" },
  { key: "text_light", label: "Text light" },
  { key: "accent", label: "Accent" },
  { key: "line", label: "Line" },
] as const;

export function StepGenerate() {
  const {
    brandName,
    brandSlug,
    colors,
    modules,
    diffResults,
    generatedYaml,
    downloadUrl,
    generating,
    generateError,
    setColors,
    setColor,
    toggleModule,
    generateBrand,
    setStep,
  } = useBrandWizardStore();

  // Auto-populate colors from first diff result
  useEffect(() => {
    if (Object.keys(colors).length > 0) return;

    const firstDiff = Object.values(diffResults)[0];
    if (!firstDiff) return;

    const autoColors: Record<string, string> = {};
    const detectedColors = firstDiff.detected_colors;
    const c0 = detectedColors[0];
    const c1 = detectedColors[1];
    const c2 = detectedColors[2];
    if (c0) autoColors.primary = c0.hex;
    if (c1) autoColors.secondary = c1.hex;
    if (c2) autoColors.text = c2.hex;

    setColors(autoColors);
  }, [diffResults, colors, setColors]);

  // Generate YAML preview
  const yamlPreview = useMemo(() => {
    if (generatedYaml) return generatedYaml;

    const lines: string[] = [
      `brand:`,
      `  name: "${brandName}"`,
      `  slug: ${brandSlug}`,
      `  tenant: ${brandSlug}`,
      ``,
      `colors:`,
    ];

    for (const { key } of COLOR_KEYS) {
      if (colors[key]) {
        lines.push(`  ${key}: '${colors[key]}'`);
      }
    }

    if (modules.length > 0) {
      lines.push(``, `tenant_modules:`);
      for (const mod of modules) {
        lines.push(`  - ${mod}`);
      }
    }

    // Stationery from detected pairs
    const pageTypes = Object.keys(diffResults);
    if (pageTypes.length > 0) {
      lines.push(``, `stationery:`);
      for (const pt of pageTypes) {
        lines.push(`  ${pt}:`);
        lines.push(`    source: stationery/${pt}.pdf`);
      }
    }

    return lines.join("\n");
  }, [brandName, brandSlug, colors, modules, diffResults, generatedYaml]);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Colors */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <h3 className="mb-3 text-sm font-semibold text-gray-700">Kleuren</h3>
        <p className="mb-4 text-xs text-gray-500">
          Auto-detected van diff. Klik het kleurvak om aan te passen.
        </p>
        <div className="grid grid-cols-2 gap-3">
          {COLOR_KEYS.map(({ key, label }) => (
            <div key={key} className="flex items-center gap-3">
              <label
                htmlFor={`color-${key}`}
                className="w-24 text-sm text-gray-600"
              >
                {label}:
              </label>
              <div className="flex items-center gap-2">
                <input
                  id={`color-${key}`}
                  type="color"
                  value={colors[key] ?? "#000000"}
                  onChange={(e) => setColor(key, e.target.value)}
                  className="h-8 w-8 cursor-pointer rounded border border-gray-200"
                />
                <input
                  type="text"
                  value={colors[key] ?? ""}
                  onChange={(e) => setColor(key, e.target.value)}
                  placeholder="#000000"
                  className="w-24 rounded border border-gray-200 px-2 py-1 font-mono text-xs focus:border-blue-300 focus:ring-1 focus:ring-blue-100 focus:outline-none"
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Modules */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <h3 className="mb-3 text-sm font-semibold text-gray-700">
          Tenant Modules
        </h3>
        <div className="space-y-2">
          {KNOWN_MODULES.map((mod) => (
            <label
              key={mod.value}
              className="flex items-center gap-3 rounded px-2 py-1.5 text-sm hover:bg-gray-50 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={modules.includes(mod.value)}
                onChange={() => toggleModule(mod.value)}
                className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="font-mono text-xs text-gray-700">
                {mod.value}
              </span>
              <span className="text-xs text-gray-500">{mod.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* YAML Preview */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <h3 className="mb-3 text-sm font-semibold text-gray-700">
          YAML Preview
        </h3>
        <textarea
          value={yamlPreview}
          readOnly
          rows={18}
          className="w-full rounded border border-gray-200 bg-gray-50 p-3 font-mono text-xs text-gray-700 focus:outline-none"
        />
      </div>

      {/* Generate error */}
      {generateError && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {generateError}
        </div>
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between border-t border-gray-200 pt-4">
        <button
          onClick={() => setStep(2)}
          className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
        >
          \u2190 Terug
        </button>
        <div className="flex gap-3">
          {downloadUrl && (
            <a
              href={downloadUrl}
              download
              className="inline-flex items-center gap-1.5 rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
              Download ZIP
            </a>
          )}
          <button
            onClick={generateBrand}
            disabled={generating}
            className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {generating ? (
              <>
                <Spinner />
                Genereren...
              </>
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
                </svg>
                Genereer Brand
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

function Spinner() {
  return (
    <svg
      className="h-4 w-4 animate-spin text-white/70"
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
  );
}
