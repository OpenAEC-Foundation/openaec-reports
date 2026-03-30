import { useRef, useState } from "react";

interface ColorPickerProps {
  value: string;
  onChange: (color: string) => void;
  brandColors?: Record<string, string> | null;
}

/**
 * Kleurenpicker met brand-swatches + custom hex input.
 *
 * Toont brand kleuren als visuele knoppen. Onderaan een hex input
 * voor custom kleuren. Fallback: alleen hex input als geen brand.
 */
export function ColorPicker({ value, onChange, brandColors }: ColorPickerProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const hasSwatches = brandColors && Object.keys(brandColors).length > 0;

  // Bepaal display: als value een brand alias is, toon de naam
  const displayLabel = hasSwatches && brandColors[value]
    ? value
    : value;

  const displayColor = hasSwatches && brandColors[value]
    ? brandColors[value]
    : value.startsWith("#") ? value : "#000000";

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 rounded border border-oaec-border px-2 py-0.5 text-xs hover:border-oaec-accent transition-colors"
      >
        <span
          className="inline-block h-3 w-3 rounded-sm border border-oaec-border"
          style={{ backgroundColor: displayColor }}
        />
        <span className="font-mono text-oaec-text-secondary">{displayLabel}</span>
      </button>

      {open && (
        <div className="absolute z-20 mt-1 rounded-md border border-oaec-border bg-oaec-bg-lighter p-2 shadow-lg min-w-[180px]">
          {/* Brand swatches */}
          {hasSwatches && (
            <div className="mb-2">
              <p className="text-[10px] font-semibold text-oaec-text-muted uppercase tracking-wider mb-1">
                Brand kleuren
              </p>
              <div className="flex flex-col gap-1">
                {Object.entries(brandColors).map(([name, hex]) => (
                  <button
                    key={name}
                    type="button"
                    onClick={() => { onChange(name); setOpen(false); }}
                    className={`flex items-center gap-2 rounded px-1.5 py-0.5 text-xs hover:bg-oaec-bg ${
                      value === name ? "bg-oaec-accent-soft ring-1 ring-oaec-accent/30" : ""
                    }`}
                  >
                    <span
                      className="inline-block h-3 w-3 rounded-sm border border-oaec-border"
                      style={{ backgroundColor: hex }}
                    />
                    <span className="text-oaec-text-secondary">{name}</span>
                    <span className="text-oaec-text-faint font-mono ml-auto">{hex}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Custom hex input */}
          <div>
            <p className="text-[10px] font-semibold text-oaec-text-muted uppercase tracking-wider mb-1">
              Custom
            </p>
            <div className="flex items-center gap-1">
              <input
                type="text"
                value={value.startsWith("#") ? value : ""}
                placeholder="#000000"
                onChange={(e) => {
                  const v = e.target.value;
                  if (/^#[0-9a-fA-F]{0,6}$/.test(v) || v === "") {
                    onChange(v || "#000000");
                  }
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") setOpen(false);
                }}
                className="w-full rounded border border-oaec-border px-1.5 py-0.5 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-oaec-accent"
              />
              <input
                type="color"
                value={displayColor}
                onChange={(e) => { onChange(e.target.value); }}
                className="h-6 w-6 cursor-pointer rounded border-0 p-0"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
