import type { TableColumnYaml, TableConfigYaml } from "@/types/pageType";
import { ColorPicker } from "./ColorPicker";
import { Field, NumberInput, SelectInput, TextInput, ZoneRow } from "./ZoneRow";

interface TableConfigSectionProps {
  table: TableConfigYaml | undefined;
  onChange: (table: TableConfigYaml | undefined) => void;
  brandColors?: Record<string, string> | null;
}

const ALIGN_OPTIONS = [
  { value: "left", label: "Links" },
  { value: "center", label: "Midden" },
  { value: "right", label: "Rechts" },
];

function newColumn(): TableColumnYaml {
  return { field: "", width_mm: 40, align: "left", font: "body", size: 9, color: "text" };
}

function newTable(): TableConfigYaml {
  return {
    data_bind: "items",
    columns: [newColumn()],
    origin: { x_mm: 20, y_mm: 60 },
    row_height_mm: 5.6,
    max_y_mm: 260,
  };
}

/**
 * Tabel configuratie editor + kolommen sub-editor.
 */
export function TableConfigSection({ table, onChange, brandColors }: TableConfigSectionProps) {
  if (!table) {
    return (
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1.5">
          <h4 className="text-xs font-semibold text-gray-700">Tabel</h4>
          <button
            type="button"
            onClick={() => onChange(newTable())}
            className="rounded bg-purple-50 px-2 py-0.5 text-[10px] font-medium text-purple-600 hover:bg-purple-100 transition-colors"
          >
            + Tabel toevoegen
          </button>
        </div>
        <p className="text-xs text-gray-400 italic">Geen tabel geconfigureerd</p>
      </div>
    );
  }

  function update(patch: Partial<TableConfigYaml>) {
    onChange({ ...table!, ...patch });
  }

  function updateOrigin(patch: Partial<{ x_mm: number; y_mm: number }>) {
    onChange({ ...table!, origin: { ...(table!.origin ?? {}), ...patch } });
  }

  function updateColumn(index: number, patch: Partial<TableColumnYaml>) {
    const cols = (table!.columns ?? []).map((c, i) => (i === index ? { ...c, ...patch } : c));
    onChange({ ...table!, columns: cols });
  }

  function deleteColumn(index: number) {
    onChange({ ...table!, columns: (table!.columns ?? []).filter((_, i) => i !== index) });
  }

  function addColumn() {
    onChange({ ...table!, columns: [...(table!.columns ?? []), newColumn()] });
  }

  function removeTable() {
    if (confirm("Tabelconfiguratie verwijderen?")) {
      onChange(undefined);
    }
  }

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-1.5">
        <h4 className="text-xs font-semibold text-gray-700">Tabel</h4>
        <button
          type="button"
          onClick={removeTable}
          className="rounded bg-red-50 px-2 py-0.5 text-[10px] font-medium text-red-600 hover:bg-red-100 transition-colors"
        >
          Verwijderen
        </button>
      </div>

      {/* Tabel metadata */}
      <div className="rounded border border-gray-200 bg-white px-3 py-2 mb-2">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
          <Field label="data_bind" className="flex-1 min-w-[120px]">
            <TextInput
              value={table.data_bind}
              onChange={(v) => update({ data_bind: v })}
              placeholder="items"
              className="w-full min-w-[80px]"
            />
          </Field>
          <Field label="origin x">
            <NumberInput value={table.origin?.x_mm} onChange={(v) => updateOrigin({ x_mm: v })} step={0.5} min={0} />
          </Field>
          <Field label="origin y">
            <NumberInput value={table.origin?.y_mm} onChange={(v) => updateOrigin({ y_mm: v })} step={0.5} min={0} />
          </Field>
          <Field label="rij h">
            <NumberInput value={table.row_height_mm} onChange={(v) => update({ row_height_mm: v })} step={0.1} min={2} className="w-12" />
          </Field>
          <Field label="max y">
            <NumberInput value={table.max_y_mm} onChange={(v) => update({ max_y_mm: v })} step={1} min={50} />
          </Field>
        </div>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1.5">
          <Field label="header">
            <input
              type="checkbox"
              checked={table.show_header ?? false}
              onChange={(e) => update({ show_header: e.target.checked })}
              className="h-3 w-3"
            />
          </Field>
          {table.header_bg !== undefined && (
            <Field label="header bg">
              <ColorPicker
                value={table.header_bg ?? ""}
                onChange={(v) => update({ header_bg: v || null })}
                brandColors={brandColors}
              />
            </Field>
          )}
          {table.grid_color !== undefined && (
            <Field label="grid kleur">
              <ColorPicker
                value={table.grid_color ?? ""}
                onChange={(v) => update({ grid_color: v || null })}
                brandColors={brandColors}
              />
            </Field>
          )}
        </div>
      </div>

      {/* Kolommen */}
      <div className="ml-2">
        <div className="flex items-center justify-between mb-1">
          <h5 className="text-[10px] font-semibold text-gray-600 uppercase tracking-wider">
            Kolommen ({(table.columns ?? []).length})
          </h5>
          <button
            type="button"
            onClick={addColumn}
            className="rounded bg-purple-50 px-2 py-0.5 text-[10px] font-medium text-purple-600 hover:bg-purple-100 transition-colors"
          >
            + Kolom
          </button>
        </div>

        {(table.columns ?? []).map((col, i) => (
          <ZoneRow key={i} index={i} onDelete={deleteColumn}>
            <Field label="field" className="flex-1 min-w-[80px]">
              <TextInput
                value={col.field}
                onChange={(v) => updateColumn(i, { field: v })}
                placeholder="amount"
                className="w-full min-w-[60px]"
              />
            </Field>
            <Field label="header">
              <TextInput
                value={col.header ?? ""}
                onChange={(v) => updateColumn(i, { header: v || null })}
                placeholder="Kop"
                className="w-16"
              />
            </Field>
            <Field label="w (mm)">
              <NumberInput value={col.width_mm} onChange={(v) => updateColumn(i, { width_mm: v })} step={1} min={5} className="w-12" />
            </Field>
            <Field label="align">
              <SelectInput
                value={col.align ?? "left"}
                onChange={(v) => updateColumn(i, { align: v as TableColumnYaml["align"] })}
                options={ALIGN_OPTIONS}
                className="w-16"
              />
            </Field>
            <Field label="size">
              <NumberInput value={col.size} onChange={(v) => updateColumn(i, { size: v })} step={0.5} min={4} max={72} className="w-12" />
            </Field>
          </ZoneRow>
        ))}
      </div>
    </div>
  );
}
