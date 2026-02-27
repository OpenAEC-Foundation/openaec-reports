import { useState, useCallback, useRef } from "react";
import { useBrandWizardStore } from "@/stores/brandWizardStore";

function toSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

export function StepUpload() {
  const {
    brandName,
    brandSlug,
    pairs,
    uploading,
    uploadError,
    setBrandName,
    uploadFiles,
    setStep,
  } = useBrandWizardStore();

  const [dragOver, setDragOver] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [localName, setLocalName] = useState(brandName);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const hasCompletePair = pairs.some((p) => p.complete);

  const handleFiles = useCallback((files: FileList | null) => {
    if (!files) return;
    const pdfFiles = Array.from(files).filter(
      (f) => f.type === "application/pdf" || f.name.endsWith(".pdf"),
    );
    setSelectedFiles((prev) => [...prev, ...pdfFiles]);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles],
  );

  const handleUpload = async () => {
    if (selectedFiles.length === 0 || !localName.trim()) return;
    setBrandName(localName.trim());
    await uploadFiles(selectedFiles, localName.trim());
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      {/* Brand name input */}
      <div className="space-y-3">
        <div>
          <label
            htmlFor="brand-name"
            className="block text-sm font-medium text-gray-700"
          >
            Brand naam
          </label>
          <input
            id="brand-name"
            type="text"
            value={localName}
            onChange={(e) => setLocalName(e.target.value)}
            placeholder="Bijv. Customer B.V."
            className="mt-1 w-full rounded border border-gray-200 px-3 py-2 text-sm focus:border-blue-300 focus:ring-2 focus:ring-blue-100 focus:outline-none"
          />
        </div>
        <div>
          <label
            htmlFor="brand-slug"
            className="block text-sm font-medium text-gray-500"
          >
            Slug (auto)
          </label>
          <input
            id="brand-slug"
            type="text"
            value={localName ? toSlug(localName) : brandSlug}
            readOnly
            className="mt-1 w-full rounded border border-gray-100 bg-gray-50 px-3 py-2 text-sm text-gray-500"
          />
        </div>
      </div>

      {/* Drop zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") fileInputRef.current?.click();
        }}
        className={`cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
          dragOver
            ? "border-blue-400 bg-blue-50"
            : "border-gray-300 hover:border-gray-400 hover:bg-gray-50"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          multiple
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        <svg
          className="mx-auto h-10 w-10 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m6.75 12l-3-3m0 0l-3 3m3-3v6m-1.5-15H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
          />
        </svg>
        <p className="mt-3 text-sm font-medium text-gray-700">
          Sleep PDF bestanden hierheen of klik om te selecteren
        </p>
        <p className="mt-1 text-xs text-gray-500">
          Naamconventie: {"{type}"}_reference.pdf + {"{type}"}_stationery.pdf
        </p>
      </div>

      {/* Selected files */}
      {selectedFiles.length > 0 && (
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-2 text-sm font-medium text-gray-700">
            Geselecteerde bestanden ({selectedFiles.length})
          </h3>
          <ul className="space-y-1">
            {selectedFiles.map((file, i) => (
              <li
                key={`${file.name}-${i}`}
                className="flex items-center justify-between rounded px-2 py-1 text-sm text-gray-600 hover:bg-gray-50"
              >
                <span className="truncate">{file.name}</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(i);
                  }}
                  className="ml-2 text-gray-400 hover:text-red-500"
                  aria-label={`Verwijder ${file.name}`}
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </li>
            ))}
          </ul>

          <button
            onClick={handleUpload}
            disabled={uploading || !localName.trim()}
            className="mt-3 w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {uploading ? (
              <span className="flex items-center justify-center gap-2">
                <Spinner />
                Uploaden...
              </span>
            ) : (
              "Upload bestanden"
            )}
          </button>
        </div>
      )}

      {/* Upload error */}
      {uploadError && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {uploadError}
        </div>
      )}

      {/* Detected pairs */}
      {pairs.length > 0 && (
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-3 text-sm font-medium text-gray-700">
            Gedetecteerde paren
          </h3>
          <div className="space-y-2">
            {pairs.map((pair) => (
              <div
                key={pair.page_type}
                className="flex items-center gap-3 rounded px-3 py-2 text-sm"
              >
                <span
                  className={
                    pair.complete ? "text-green-600" : "text-amber-500"
                  }
                >
                  {pair.complete ? (
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  ) : (
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                    </svg>
                  )}
                </span>
                <span className="w-32 font-medium text-gray-700">
                  {pair.page_type}
                </span>
                <span className="flex items-center gap-1 text-xs">
                  <span>reference</span>
                  <span className={pair.has_reference ? "text-green-600" : "text-red-400"}>
                    {pair.has_reference ? "\u2713" : "\u2717"}
                  </span>
                </span>
                <span className="flex items-center gap-1 text-xs">
                  <span>stationery</span>
                  <span className={pair.has_stationery ? "text-green-600" : "text-red-400"}>
                    {pair.has_stationery ? "\u2713" : "\u2717"}
                  </span>
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Next button */}
      <div className="flex justify-end">
        <button
          onClick={() => setStep(2)}
          disabled={!hasCompletePair}
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
