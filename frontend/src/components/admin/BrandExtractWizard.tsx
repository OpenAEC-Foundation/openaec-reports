import { useRef, useState } from "react";
import { useAdminStore } from "@/stores/adminStore";
import { adminApi } from "@/services/api";

const STEP_LABELS = [
  { num: 1, label: "Upload" },
  { num: 2, label: "Review" },
  { num: 3, label: "Prompt" },
  { num: 4, label: "Finalize" },
];

// ============================================================
// Shared UI helpers
// ============================================================

function StepIndicator({ current }: { current: number }) {
  return (
    <div className="flex items-center gap-1 mb-6">
      {STEP_LABELS.map((step, i) => (
        <div key={step.num} className="flex items-center">
          <div
            className={`flex items-center justify-center w-7 h-7 rounded-full text-xs font-medium ${
              current === step.num
                ? "bg-oaec-accent text-oaec-accent-text"
                : current > step.num
                  ? "bg-oaec-accent-soft text-oaec-accent"
                  : "bg-oaec-hover text-oaec-text-faint"
            }`}
          >
            {current > step.num ? "\u2713" : step.num}
          </div>
          <span
            className={`ml-1.5 text-xs font-medium ${
              current === step.num ? "text-oaec-text" : "text-oaec-text-faint"
            }`}
          >
            {step.label}
          </span>
          {i < STEP_LABELS.length - 1 && (
            <div className="w-8 h-px bg-oaec-hover-strong mx-2" />
          )}
        </div>
      ))}
    </div>
  );
}

function Spinner() {
  return (
    <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}

// ============================================================
// Step 1: Upload
// ============================================================

function StepUpload({ tenant }: { tenant: string }) {
  const startExtraction = useAdminStore((s) => s.startExtraction);
  const extractionLoading = useAdminStore((s) => s.extractionLoading);
  const pdfRef = useRef<HTMLInputElement>(null);
  const stamkaartRef = useRef<HTMLInputElement>(null);

  const [brandName, setBrandName] = useState("");
  const [brandSlug, setBrandSlug] = useState("");
  const [dpi, setDpi] = useState(150);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [stamkaart, setStamkaart] = useState<File | null>(null);

  async function handleStart() {
    if (!pdfFile) return;
    const name = brandName || tenant;
    const slug = brandSlug || tenant;
    await startExtraction(tenant, pdfFile, name, slug, dpi, stamkaart ?? undefined);
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-oaec-text-secondary">
        Upload een referentie-rapport PDF om de huisstijl te extraheren.
        Optioneel: voeg een stamkaart toe voor extra kleurinformatie.
      </p>

      {/* PDF upload */}
      <div>
        <label className="block text-sm font-medium text-oaec-text-secondary mb-1">
          Referentie-rapport (PDF) *
        </label>
        <div className="flex items-center gap-3">
          <button
            onClick={() => pdfRef.current?.click()}
            className="rounded-md bg-oaec-accent px-3 py-1.5 text-xs font-medium text-oaec-accent-text hover:bg-oaec-accent-hover transition-colors"
          >
            Selecteer PDF
          </button>
          <span className="text-sm text-oaec-text-muted">
            {pdfFile ? pdfFile.name : "Geen bestand geselecteerd"}
          </span>
          <input
            ref={pdfRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={(e) => setPdfFile(e.target.files?.[0] ?? null)}
          />
        </div>
      </div>

      {/* Stamkaart */}
      <div>
        <label className="block text-sm font-medium text-oaec-text-secondary mb-1">
          Stamkaart (optioneel)
        </label>
        <div className="flex items-center gap-3">
          <button
            onClick={() => stamkaartRef.current?.click()}
            className="rounded-md border border-oaec-border px-3 py-1.5 text-xs font-medium text-oaec-text-secondary hover:bg-oaec-bg transition-colors"
          >
            Selecteer PDF
          </button>
          <span className="text-sm text-oaec-text-muted">
            {stamkaart ? stamkaart.name : "Geen bestand"}
          </span>
          <input
            ref={stamkaartRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={(e) => setStamkaart(e.target.files?.[0] ?? null)}
          />
        </div>
      </div>

      {/* Brand info */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-oaec-text-secondary mb-1">Merknaam</label>
          <input
            type="text"
            value={brandName}
            onChange={(e) => setBrandName(e.target.value)}
            placeholder={tenant}
            className="w-full rounded-md border border-oaec-border px-3 py-1.5 text-sm shadow-sm focus:border-oaec-accent focus:ring-1 focus:ring-oaec-accent"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-oaec-text-secondary mb-1">Slug</label>
          <input
            type="text"
            value={brandSlug}
            onChange={(e) => setBrandSlug(e.target.value)}
            placeholder={tenant}
            className="w-full rounded-md border border-oaec-border px-3 py-1.5 text-sm shadow-sm focus:border-oaec-accent focus:ring-1 focus:ring-oaec-accent"
          />
        </div>
      </div>

      {/* DPI */}
      <div>
        <label className="block text-sm font-medium text-oaec-text-secondary mb-1">
          Render DPI: {dpi}
        </label>
        <input
          type="range"
          min={72}
          max={300}
          step={1}
          value={dpi}
          onChange={(e) => setDpi(Number(e.target.value))}
          className="w-48"
        />
        <span className="ml-2 text-xs text-oaec-text-faint">72 (snel) - 300 (hoog detail)</span>
      </div>

      {/* Start button */}
      <div className="pt-2">
        <button
          onClick={handleStart}
          disabled={!pdfFile || extractionLoading}
          className="rounded-md bg-oaec-accent px-4 py-2 text-sm font-medium text-oaec-accent-text hover:bg-oaec-accent-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {extractionLoading && <Spinner />}
          {extractionLoading ? "Extractie bezig..." : "Start extractie"}
        </button>
      </div>
    </div>
  );
}

// ============================================================
// Step 2: Review & Edit
// ============================================================

function ColorInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <input
        type="color"
        value={value || "#000000"}
        onChange={(e) => onChange(e.target.value)}
        className="h-7 w-7 rounded border border-oaec-border cursor-pointer"
      />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-24 rounded-md border border-oaec-border px-2 py-1 text-xs font-mono"
      />
      <span className="text-xs text-oaec-text-muted">{label}</span>
    </div>
  );
}

function StepReview({ tenant }: { tenant: string }) {
  const extractionResult = useAdminStore((s) => s.extractionResult);
  const editedExtraction = useAdminStore((s) => s.editedExtraction);
  const setEditedExtraction = useAdminStore((s) => s.setEditedExtraction);
  const setExtractionStep = useAdminStore((s) => s.setExtractionStep);
  const generatePrompt = useAdminStore((s) => s.generatePrompt);
  const extractionLoading = useAdminStore((s) => s.extractionLoading);

  if (!editedExtraction || !extractionResult) return null;

  function updateColor(key: string, value: string) {
    if (!editedExtraction) return;
    setEditedExtraction({
      ...editedExtraction,
      colors: { ...editedExtraction.colors, [key]: value },
    });
  }

  function addColor() {
    const name = prompt("Kleur naam (bijv. accent, warning, separator):");
    if (!name || !editedExtraction) return;
    setEditedExtraction({
      ...editedExtraction,
      colors: { ...editedExtraction.colors, [name]: "#808080" },
    });
  }

  function updateFont(key: string, value: string) {
    if (!editedExtraction) return;
    setEditedExtraction({
      ...editedExtraction,
      fonts: { ...editedExtraction.fonts, [key]: value },
    });
  }

  function updateStyle(
    styleName: string,
    field: string,
    value: string | number
  ) {
    if (!editedExtraction) return;
    const current = editedExtraction.styles[styleName] ?? {
      fontName: "",
      fontSize: 10,
      leading: 12,
      textColor: "#000000",
    };
    setEditedExtraction({
      ...editedExtraction,
      styles: {
        ...editedExtraction.styles,
        [styleName]: { ...current, [field]: value },
      },
    });
  }

  async function handleNext() {
    await generatePrompt(tenant);
  }

  // Page image thumbnails
  const pageImages = extractionResult.page_images;

  return (
    <div className="space-y-6">
      {/* Pagina thumbnails */}
      {Object.keys(pageImages).length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-oaec-text-secondary mb-2">
            Gedetecteerde pagina-types
          </h4>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {Object.entries(pageImages).map(([type, filename]) => (
              <div key={type} className="flex-shrink-0 text-center">
                <img
                  src={adminApi.getAnalysisPageUrl(tenant, filename)}
                  alt={type}
                  className="h-32 rounded border border-oaec-border shadow-sm"
                />
                <span className="text-xs text-oaec-text-muted mt-1 block">{type}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Kleuren */}
      <div className="rounded-lg border border-oaec-border bg-oaec-bg-lighter p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-semibold text-oaec-text-secondary">Kleuren</h4>
          <button
            onClick={addColor}
            className="text-xs text-oaec-accent hover:text-oaec-accent"
          >
            + Kleur toevoegen
          </button>
        </div>
        <div className="grid grid-cols-2 gap-2">
          {Object.entries(editedExtraction.colors).map(([key, val]) => (
            <ColorInput
              key={key}
              label={key}
              value={val}
              onChange={(v) => updateColor(key, v)}
            />
          ))}
        </div>
      </div>

      {/* Fonts */}
      <div className="rounded-lg border border-oaec-border bg-oaec-bg-lighter p-4">
        <h4 className="text-sm font-semibold text-oaec-text-secondary mb-3">Fonts</h4>
        <div className="grid grid-cols-2 gap-3">
          {Object.entries(editedExtraction.fonts).map(([role, name]) => (
            <div key={role}>
              <label className="text-xs text-oaec-text-muted">{role}</label>
              <input
                type="text"
                value={name}
                onChange={(e) => updateFont(role, e.target.value)}
                className="w-full rounded-md border border-oaec-border px-2 py-1 text-sm"
              />
            </div>
          ))}
        </div>
        <p className="text-xs text-oaec-text-faint mt-2">
          Tip: PyMuPDF meldt "Inter-Book", ReportLab verwacht "Inter-Regular"
        </p>
      </div>

      {/* Styles */}
      <div className="rounded-lg border border-oaec-border bg-oaec-bg-lighter p-4">
        <h4 className="text-sm font-semibold text-oaec-text-secondary mb-3">Tekststijlen</h4>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-oaec-border">
                <th className="text-left py-1.5 pr-3 text-oaec-text-muted font-medium">Stijl</th>
                <th className="text-left py-1.5 pr-3 text-oaec-text-muted font-medium">Font</th>
                <th className="text-left py-1.5 pr-3 text-oaec-text-muted font-medium">Size</th>
                <th className="text-left py-1.5 pr-3 text-oaec-text-muted font-medium">Leading</th>
                <th className="text-left py-1.5 text-oaec-text-muted font-medium">Kleur</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(editedExtraction.styles).map(([name, style]) => (
                <tr key={name} className="border-b border-oaec-border-subtle">
                  <td className="py-1.5 pr-3 font-medium text-oaec-text-secondary">{name}</td>
                  <td className="py-1.5 pr-3">
                    <input
                      type="text"
                      value={style.fontName}
                      onChange={(e) => updateStyle(name, "fontName", e.target.value)}
                      className="w-28 rounded border border-oaec-border px-1.5 py-0.5 text-xs"
                    />
                  </td>
                  <td className="py-1.5 pr-3">
                    <input
                      type="number"
                      value={style.fontSize}
                      step={0.5}
                      onChange={(e) => updateStyle(name, "fontSize", Number(e.target.value))}
                      className="w-16 rounded border border-oaec-border px-1.5 py-0.5 text-xs"
                    />
                  </td>
                  <td className="py-1.5 pr-3">
                    <input
                      type="number"
                      value={style.leading}
                      step={0.1}
                      onChange={(e) => updateStyle(name, "leading", Number(e.target.value))}
                      className="w-16 rounded border border-oaec-border px-1.5 py-0.5 text-xs"
                    />
                  </td>
                  <td className="py-1.5">
                    <div className="flex items-center gap-1">
                      <input
                        type="color"
                        value={style.textColor}
                        onChange={(e) => updateStyle(name, "textColor", e.target.value)}
                        className="h-5 w-5 rounded border border-oaec-border cursor-pointer"
                      />
                      <input
                        type="text"
                        value={style.textColor}
                        onChange={(e) => updateStyle(name, "textColor", e.target.value)}
                        className="w-20 rounded border border-oaec-border px-1.5 py-0.5 text-xs font-mono"
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Draft YAML preview */}
      <details className="group">
        <summary className="text-xs font-medium text-oaec-text-muted cursor-pointer hover:text-oaec-text-secondary">
          Auto-generated draft YAML bekijken
        </summary>
        <pre className="mt-2 max-h-48 overflow-auto rounded-md border border-oaec-border bg-oaec-bg-input p-3 text-xs text-oaec-text font-mono">
          {extractionResult.draft_yaml}
        </pre>
      </details>

      {/* Navigation */}
      <div className="flex justify-between pt-2">
        <button
          onClick={() => setExtractionStep(1)}
          className="rounded-md border border-oaec-border px-4 py-2 text-sm font-medium text-oaec-text-secondary hover:bg-oaec-bg transition-colors"
        >
          Terug
        </button>
        <button
          onClick={handleNext}
          disabled={extractionLoading}
          className="rounded-md bg-oaec-accent px-4 py-2 text-sm font-medium text-oaec-accent-text hover:bg-oaec-accent-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {extractionLoading && <Spinner />}
          Genereer prompt
        </button>
      </div>
    </div>
  );
}

// ============================================================
// Step 3: Prompt Package
// ============================================================

function StepPrompt({ tenant }: { tenant: string }) {
  const promptPackage = useAdminStore((s) => s.promptPackage);
  const extractionResult = useAdminStore((s) => s.extractionResult);
  const setExtractionStep = useAdminStore((s) => s.setExtractionStep);
  const [copied, setCopied] = useState(false);

  if (!promptPackage) return null;

  async function handleCopy() {
    await navigator.clipboard.writeText(promptPackage ?? "");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const pageImages = extractionResult?.page_images ?? {};

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-oaec-border bg-oaec-accent-soft p-4">
        <h4 className="text-sm font-semibold text-oaec-accent mb-2">Instructies</h4>
        <ol className="text-sm text-oaec-accent space-y-1 list-decimal list-inside">
          <li>Kopieer de prompt hieronder</li>
          <li>Open Claude Desktop</li>
          <li>Plak de prompt en voeg de pagina-afbeeldingen toe als bijlage</li>
          <li>Claude genereert een <code className="bg-oaec-accent-soft px-1 rounded">pages:</code> YAML artifact</li>
          <li>Kopieer het artifact en ga naar stap 4</li>
        </ol>
      </div>

      {/* Page images for download */}
      {Object.keys(pageImages).length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-oaec-text-secondary mb-2">
            Pagina-afbeeldingen (bijvoegen in Claude Desktop)
          </h4>
          <div className="flex gap-3 flex-wrap">
            {Object.entries(pageImages).map(([type, filename]) => {
              const url = adminApi.getAnalysisPageUrl(tenant, filename);
              return (
                <a
                  key={type}
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-shrink-0 text-center group"
                >
                  <img
                    src={url}
                    alt={type}
                    className="h-24 rounded border border-oaec-border shadow-sm group-hover:border-oaec-accent transition-colors"
                  />
                  <span className="text-xs text-oaec-text-muted mt-1 block">{type}</span>
                  <span className="text-xs text-oaec-accent">{filename}</span>
                </a>
              );
            })}
          </div>
        </div>
      )}

      {/* Prompt text */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-semibold text-oaec-text-secondary">Prompt</h4>
          <button
            onClick={handleCopy}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              copied
                ? "bg-oaec-success-soft text-oaec-success"
                : "bg-oaec-accent text-oaec-accent-text hover:bg-oaec-accent-hover"
            }`}
          >
            {copied ? "Gekopieerd!" : "Kopieer naar klembord"}
          </button>
        </div>
        <pre className="max-h-96 overflow-auto rounded-md border border-oaec-border bg-oaec-bg-input p-4 text-xs text-oaec-text font-mono whitespace-pre-wrap">
          {promptPackage}
        </pre>
      </div>

      {/* Navigation */}
      <div className="flex justify-between pt-2">
        <button
          onClick={() => setExtractionStep(2)}
          className="rounded-md border border-oaec-border px-4 py-2 text-sm font-medium text-oaec-text-secondary hover:bg-oaec-bg transition-colors"
        >
          Terug
        </button>
        <button
          onClick={() => setExtractionStep(4)}
          className="rounded-md bg-oaec-accent px-4 py-2 text-sm font-medium text-oaec-accent-text hover:bg-oaec-accent-hover transition-colors"
        >
          Volgende: artifact plakken
        </button>
      </div>
    </div>
  );
}

// ============================================================
// Step 4: Finalize
// ============================================================

function StepFinalize({ tenant }: { tenant: string }) {
  const editedExtraction = useAdminStore((s) => s.editedExtraction);
  const mergeBrand = useAdminStore((s) => s.mergeBrand);
  const extractionLoading = useAdminStore((s) => s.extractionLoading);
  const setExtractionStep = useAdminStore((s) => s.setExtractionStep);

  const [pagesYaml, setPagesYaml] = useState("");
  const [saved, setSaved] = useState(false);

  if (!editedExtraction) return null;

  const brandName = editedExtraction.brand?.name || tenant;
  const brandSlug = editedExtraction.brand?.slug || tenant;

  async function handleSave() {
    const yaml = pagesYaml.trim() || null;
    const success = await mergeBrand(tenant, yaml, brandName, brandSlug);
    if (success) {
      setSaved(true);
    }
  }

  if (saved) {
    return (
      <div className="rounded-lg border border-oaec-border bg-oaec-success-soft p-6 text-center">
        <div className="text-3xl mb-2">{"\u2705"}</div>
        <h4 className="text-lg font-semibold text-oaec-success mb-1">
          Brand configuratie opgeslagen
        </h4>
        <p className="text-sm text-oaec-success">
          brand.yaml voor tenant "{tenant}" is succesvol aangemaakt.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-oaec-border bg-oaec-accent-soft p-4">
        <p className="text-sm text-oaec-accent">
          Plak het <code className="bg-oaec-accent-soft px-1 rounded">pages:</code> YAML
          artifact uit Claude Desktop hieronder. Dit wordt samengevoegd met de
          gecorrigeerde extractie data tot een complete brand.yaml.
        </p>
        <p className="text-xs text-oaec-accent mt-1">
          Zonder pages YAML wordt alleen de basis-configuratie opgeslagen
          (kleuren, fonts, styles). Je kunt de pages later handmatig toevoegen.
        </p>
      </div>

      {/* Pages YAML textarea */}
      <div>
        <label className="block text-sm font-medium text-oaec-text-secondary mb-1">
          Claude Desktop artifact (pages: YAML)
        </label>
        <textarea
          value={pagesYaml}
          onChange={(e) => setPagesYaml(e.target.value)}
          placeholder={"pages:\n  cover:\n    purple_rect_y_ref: 218.0\n    ..."}
          rows={16}
          className="w-full rounded-md border border-oaec-border px-3 py-2 text-xs font-mono shadow-sm focus:border-oaec-accent focus:ring-1 focus:ring-oaec-accent"
        />
      </div>

      {/* Navigation */}
      <div className="flex justify-between pt-2">
        <button
          onClick={() => setExtractionStep(3)}
          className="rounded-md border border-oaec-border px-4 py-2 text-sm font-medium text-oaec-text-secondary hover:bg-oaec-bg transition-colors"
        >
          Terug
        </button>
        <button
          onClick={handleSave}
          disabled={extractionLoading}
          className="rounded-md bg-oaec-accent px-4 py-2 text-sm font-medium text-oaec-accent-text hover:bg-oaec-accent-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {extractionLoading && <Spinner />}
          Opslaan als brand.yaml
        </button>
      </div>
    </div>
  );
}

// ============================================================
// Main Wizard
// ============================================================

export function BrandExtractWizard({ tenant }: { tenant: string }) {
  const extractionStep = useAdminStore((s) => s.extractionStep);
  const resetExtraction = useAdminStore((s) => s.resetExtraction);

  return (
    <div className="rounded-lg border border-oaec-border bg-oaec-accent-soft/30 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold text-oaec-text">Brand Extractie Wizard</h3>
        <button
          onClick={resetExtraction}
          className="text-xs text-oaec-text-faint hover:text-oaec-text-secondary"
          title="Wizard sluiten"
        >
          Annuleren
        </button>
      </div>

      <StepIndicator current={extractionStep} />

      {extractionStep === 1 && <StepUpload tenant={tenant} />}
      {extractionStep === 2 && <StepReview tenant={tenant} />}
      {extractionStep === 3 && <StepPrompt tenant={tenant} />}
      {extractionStep === 4 && <StepFinalize tenant={tenant} />}
    </div>
  );
}
