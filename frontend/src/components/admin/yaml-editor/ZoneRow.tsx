import type { ReactNode } from "react";

interface ZoneRowProps {
  index: number;
  onDelete: (index: number) => void;
  children: ReactNode;
}

/**
 * Gedeeld compact rij-layout component voor zone-editors.
 *
 * Toont een genummerde rij met verwijder-knop en inline form fields.
 */
export function ZoneRow({ index, onDelete, children }: ZoneRowProps) {
  return (
    <div className="flex items-start gap-2 rounded border border-oaec-border bg-oaec-bg-lighter px-2 py-1.5 mb-1.5">
      <span className="flex-shrink-0 mt-0.5 text-[10px] font-mono text-oaec-text-faint w-4 text-right">
        {index + 1}
      </span>
      <div className="flex-1 flex flex-wrap items-center gap-x-3 gap-y-1 min-w-0">
        {children}
      </div>
      <button
        type="button"
        onClick={() => onDelete(index)}
        className="flex-shrink-0 mt-0.5 rounded p-0.5 text-oaec-danger hover:text-oaec-danger hover:bg-oaec-danger-soft transition-colors"
        title="Verwijderen"
      >
        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}

/** Compact form field label + input wrapper. */
export function Field({
  label,
  children,
  className = "",
}: {
  label: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`flex items-center gap-1 ${className}`}>
      <label className="text-[10px] font-medium text-oaec-text-muted whitespace-nowrap">
        {label}
      </label>
      {children}
    </div>
  );
}

/** Compact number input. */
export function NumberInput({
  value,
  onChange,
  step = 1,
  min,
  max,
  className = "w-14",
}: {
  value: number | undefined;
  onChange: (v: number) => void;
  step?: number;
  min?: number;
  max?: number;
  className?: string;
}) {
  return (
    <input
      type="number"
      value={value ?? ""}
      onChange={(e) => onChange(Number(e.target.value))}
      step={step}
      min={min}
      max={max}
      className={`rounded border border-oaec-border px-1 py-0.5 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-oaec-accent ${className}`}
    />
  );
}

/** Compact text input. */
export function TextInput({
  value,
  onChange,
  placeholder,
  className = "w-24",
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  className?: string;
}) {
  return (
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className={`rounded border border-oaec-border px-1 py-0.5 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-oaec-accent ${className}`}
    />
  );
}

/** Compact select. */
export function SelectInput({
  value,
  onChange,
  options,
  className = "w-16",
}: {
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  className?: string;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={`rounded border border-oaec-border px-1 py-0.5 text-xs focus:outline-none focus:ring-1 focus:ring-oaec-accent ${className}`}
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  );
}
