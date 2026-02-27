import { useState, useEffect, useRef } from "react";
import { useBrandWizardStore } from "@/stores/brandWizardStore";
import { brandApi } from "@/api/brandApi";
import { FieldOverlay } from "./FieldOverlay";

// ---------- Field role options ----------
// Gegroepeerd per context. Values matchen met suggest_role() in diff_engine.py
// en de text_zone namen in brand.yaml pages sectie.

const FIELD_ROLES = [
  // -- Cover --
  { value: "title", label: "Titel" },
  { value: "subtitle", label: "Subtitel" },
  { value: "report_type", label: "Rapporttype" },
  { value: "tagline", label: "Tagline" },
  { value: "cover_image", label: "Cover afbeelding" },

  // -- Document --
  { value: "project_name", label: "Projectnaam" },
  { value: "project_number", label: "Projectnummer" },
  { value: "document_number", label: "Documentnummer" },
  { value: "kenmerk", label: "Kenmerk" },
  { value: "date", label: "Datum" },
  { value: "version", label: "Versie" },
  { value: "status", label: "Status" },
  { value: "fase", label: "Fase" },

  // -- Personen --
  { value: "client", label: "Opdrachtgever" },
  { value: "client_contact", label: "Contactpersoon opdrachtgever" },
  { value: "client_address", label: "Adres opdrachtgever" },
  { value: "author", label: "Auteur" },
  { value: "company_name", label: "Bedrijfsnaam" },

  // -- Locatie --
  { value: "location", label: "Locatie" },
  { value: "location_code", label: "Locatiecode" },
  { value: "location_address", label: "Locatie adres" },

  // -- Pagina-elementen --
  { value: "page_number", label: "Paginanummer" },
  { value: "section_header", label: "Sectie header" },
  { value: "footer_project", label: "Footer projectnaam" },
  { value: "footer_code", label: "Footer projectcode" },
  { value: "footer_text", label: "Footer tekst" },

  // -- Content --
  { value: "label", label: "Label" },
  { value: "value", label: "Waarde" },
  { value: "contact", label: "Contactgegevens" },
  { value: "phone", label: "Telefoon" },
  { value: "email", label: "E-mail" },
  { value: "website", label: "Website" },
  { value: "address", label: "Adres" },
  { value: "photo", label: "Foto placeholder" },
  { value: "disclaimer", label: "Disclaimer" },
  { value: "overlay_text", label: "Overlay tekst" },

  // -- Overig --
  { value: "custom", label: "Custom..." },
  { value: "ignore", label: "Negeren" },
] as const;

/** Set van bekende role values voor snelle lookup. */
const KNOWN_ROLE_VALUES: Set<string> = new Set(FIELD_ROLES.map((r) => r.value));

type ViewType = "diff" | "ref" | "st";

export function StepDiffReview() {
  const {
    pairs,
    sessionId,
    activePageType,
    diffResults,
    diffLoading,
    diffError,
    activeFieldId,
    setActivePageType,
    setActiveFieldId,
    runDiff,
    updateFieldRole,
    saveFieldRoles,
    setStep,
  } = useBrandWizardStore();

  const [viewType, setViewType] = useState<ViewType>("diff");
  const [savingFields, setSavingFields] = useState(false);
  const fieldListRef = useRef<HTMLDivElement>(null);

  const completePairs = pairs.filter((p) => p.complete);
  const currentDiff = activePageType ? diffResults[activePageType] : null;

  // Auto-run diff on first page type if not yet loaded
  useEffect(() => {
    if (completePairs.length > 0 && !activePageType && completePairs[0]) {
      const first = completePairs[0].page_type;
      setActivePageType(first);
      if (!diffResults[first]) {
        runDiff(first);
      }
    }
  }, [completePairs, activePageType, diffResults, setActivePageType, runDiff]);

  const handleTabClick = (pageType: string) => {
    setActivePageType(pageType);
    setActiveFieldId(null);
    if (!diffResults[pageType]) {
      runDiff(pageType);
    }
  };

  const handleFieldClick = (fieldId: string) => {
    setActiveFieldId(fieldId);
    // Scroll to field in list
    const el = document.getElementById(`field-item-${fieldId}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  };

  const handleSaveFields = async () => {
    if (!activePageType) return;
    setSavingFields(true);
    try {
      await saveFieldRoles(activePageType);
    } finally {
      setSavingFields(false);
    }
  };

  const getImageUrl = (): string => {
    if (!sessionId || !activePageType) return "";
    switch (viewType) {
      case "diff":
        return brandApi.getDiffImageUrl(sessionId, activePageType);
      case "ref":
        return brandApi.getReferenceImageUrl(sessionId, activePageType);
      case "st":
        return brandApi.getStationeryImageUrl(sessionId, activePageType);
    }
  };

  return (
    <div className="flex h-full flex-col gap-4">
      {/* Page type tabs */}
      <div className="flex gap-1 border-b border-gray-200 pb-0">
        {completePairs.map((pair) => (
          <button
            key={pair.page_type}
            onClick={() => handleTabClick(pair.page_type)}
            className={`rounded-t-md px-4 py-2 text-sm font-medium transition-colors ${
              activePageType === pair.page_type
                ? "border-b-2 border-blue-500 text-blue-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {pair.page_type}
            {diffResults[pair.page_type] && (
              <span className="ml-1.5 inline-block h-1.5 w-1.5 rounded-full bg-green-400" />
            )}
          </button>
        ))}
      </div>

      {/* Diff error */}
      {diffError && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {diffError}
        </div>
      )}

      {/* Loading state */}
      {diffLoading && (
        <div className="flex flex-1 items-center justify-center">
          <div className="text-center">
            <Spinner />
            <p className="mt-2 text-sm text-gray-500">Diff berekenen...</p>
          </div>
        </div>
      )}

      {/* Content: PDF preview + fields */}
      {currentDiff && !diffLoading && (
        <div className="flex flex-1 gap-4 overflow-hidden">
          {/* Left: PDF Preview */}
          <div className="flex flex-1 flex-col">
            <div className="flex-1 overflow-auto rounded-lg border border-gray-200 bg-gray-100 p-2">
              {viewType === "diff" ? (
                <FieldOverlay
                  fields={currentDiff.detected_fields}
                  imageUrl={getImageUrl()}
                  pdfWidth={currentDiff.page_size.width_pt}
                  pdfHeight={currentDiff.page_size.height_pt}
                  activeFieldId={activeFieldId}
                  onFieldClick={handleFieldClick}
                  onFieldHover={setActiveFieldId}
                />
              ) : (
                <img
                  src={getImageUrl()}
                  alt={`${activePageType} ${viewType}`}
                  className="w-full"
                  draggable={false}
                />
              )}
            </div>

            {/* View switcher */}
            <div className="mt-2 flex gap-1">
              {(["diff", "ref", "st"] as const).map((vt) => (
                <button
                  key={vt}
                  onClick={() => setViewType(vt)}
                  className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
                    viewType === vt
                      ? "bg-blue-100 text-blue-700"
                      : "bg-gray-100 text-gray-500 hover:bg-gray-200"
                  }`}
                >
                  {vt === "diff" ? "Diff" : vt === "ref" ? "Ref" : "St"}
                </button>
              ))}
            </div>
          </div>

          {/* Right: Fields panel */}
          <div
            ref={fieldListRef}
            className="w-80 shrink-0 overflow-auto rounded-lg border border-gray-200 bg-white"
          >
            {/* Fields list */}
            <div className="border-b border-gray-100 px-4 py-3">
              <h3 className="text-sm font-semibold text-gray-700">
                Velden ({currentDiff.detected_fields.length})
              </h3>
            </div>
            <div className="max-h-[50%] overflow-auto">
              {currentDiff.detected_fields.map((field) => (
                <div
                  id={`field-item-${field.id}`}
                  key={field.id}
                  className={`border-b border-gray-50 px-4 py-3 transition-colors ${
                    activeFieldId === field.id ? "bg-red-50" : "hover:bg-gray-50"
                  }`}
                  onClick={() => setActiveFieldId(field.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") setActiveFieldId(field.id);
                  }}
                  role="button"
                  tabIndex={0}
                >
                  <div className="flex items-start gap-2">
                    <span className="mt-0.5 inline-block h-3 w-3 shrink-0 rounded-full bg-red-400" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-xs font-medium text-gray-700">
                        {field.id}
                      </p>
                      <p className="truncate text-xs text-gray-500">
                        &quot;{field.sample_text}&quot;
                      </p>
                      <div className="mt-2 space-y-1.5">
                        <select
                          value={field.role ?? field.suggested_role ?? ""}
                          onChange={(e) =>
                            updateFieldRole(
                              activePageType ?? "",
                              field.id,
                              e.target.value,
                              field.name ?? "",
                            )
                          }
                          className="w-full rounded border border-gray-200 px-2 py-1 text-xs focus:border-blue-300 focus:ring-1 focus:ring-blue-100 focus:outline-none"
                        >
                          <option value="">-- Selecteer rol --</option>
                          {/* Toon suggested_role als die niet in de standaardlijst zit */}
                          {field.suggested_role &&
                            !KNOWN_ROLE_VALUES.has(field.suggested_role) && (
                              <option value={field.suggested_role}>
                                {field.suggested_role} (gesuggereerd)
                              </option>
                            )}
                          {FIELD_ROLES.map((r) => (
                            <option key={r.value} value={r.value}>
                              {r.label}
                            </option>
                          ))}
                        </select>
                        <input
                          type="text"
                          value={field.name ?? ""}
                          onChange={(e) =>
                            updateFieldRole(
                              activePageType ?? "",
                              field.id,
                              field.role ?? "",
                              e.target.value,
                            )
                          }
                          placeholder="Naam (optioneel)"
                          className="w-full rounded border border-gray-200 px-2 py-1 text-xs focus:border-blue-300 focus:ring-1 focus:ring-blue-100 focus:outline-none"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Colors section */}
            <div className="border-t border-gray-200 px-4 py-3">
              <h4 className="mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Kleuren
              </h4>
              <div className="space-y-1">
                {currentDiff.detected_colors.slice(0, 8).map((color) => (
                  <div
                    key={color.hex}
                    className="flex items-center gap-2 text-xs text-gray-600"
                  >
                    <span
                      className="inline-block h-3 w-3 rounded border border-gray-200"
                      style={{ backgroundColor: color.hex }}
                    />
                    <span className="font-mono">{color.hex}</span>
                    <span className="text-gray-400">({color.count})</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Fonts section */}
            <div className="border-t border-gray-200 px-4 py-3">
              <h4 className="mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Fonts
              </h4>
              <div className="space-y-1">
                {currentDiff.detected_fonts.map((font) => (
                  <div
                    key={font.name}
                    className="flex items-center justify-between text-xs text-gray-600"
                  >
                    <span className="truncate">{font.name}</span>
                    <span className="text-gray-400">({font.count})</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Save fields button */}
            <div className="border-t border-gray-200 px-4 py-3">
              <button
                onClick={handleSaveFields}
                disabled={savingFields}
                className="w-full rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:opacity-50"
              >
                {savingFields ? "Opslaan..." : "Velden opslaan"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between border-t border-gray-200 pt-4">
        <button
          onClick={() => setStep(1)}
          className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
        >
          \u2190 Terug
        </button>
        <button
          onClick={() => setStep(3)}
          disabled={Object.keys(diffResults).length === 0}
          className="rounded-md bg-blue-600 px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Volgende \u2192
        </button>
      </div>
    </div>
  );
}

function Spinner() {
  return (
    <svg
      className="mx-auto h-8 w-8 animate-spin text-gray-400"
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
