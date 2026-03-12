import type { LineZoneYaml } from "@/types/pageType";
import { ColorPicker } from "./ColorPicker";
import { Field, NumberInput, ZoneRow } from "./ZoneRow";

interface LineZoneSectionProps {
  zones: LineZoneYaml[];
  onChange: (zones: LineZoneYaml[]) => void;
  brandColors?: Record<string, string> | null;
}

function newLineZone(): LineZoneYaml {
  return { x0_mm: 20, y_mm: 50, x1_mm: 190, width_pt: 1, color: "primary" };
}

/**
 * Lijst van LineZone rijen (x0, y, x1, width, color).
 */
export function LineZoneSection({ zones, onChange, brandColors }: LineZoneSectionProps) {
  function updateZone(index: number, patch: Partial<LineZoneYaml>) {
    const updated = zones.map((z, i) => (i === index ? { ...z, ...patch } : z));
    onChange(updated);
  }

  function deleteZone(index: number) {
    onChange(zones.filter((_, i) => i !== index));
  }

  function addZone() {
    onChange([...zones, newLineZone()]);
  }

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-1.5">
        <h4 className="text-xs font-semibold text-gray-700">Line Zones ({zones.length})</h4>
        <button
          type="button"
          onClick={addZone}
          className="rounded bg-purple-50 px-2 py-0.5 text-[10px] font-medium text-purple-600 hover:bg-purple-100 transition-colors"
        >
          + Toevoegen
        </button>
      </div>

      {zones.length === 0 ? (
        <p className="text-xs text-gray-400 italic">Geen line zones</p>
      ) : (
        zones.map((zone, i) => (
          <ZoneRow key={i} index={i} onDelete={deleteZone}>
            <Field label="x0">
              <NumberInput value={zone.x0_mm} onChange={(v) => updateZone(i, { x0_mm: v })} step={0.5} min={0} />
            </Field>
            <Field label="y">
              <NumberInput value={zone.y_mm} onChange={(v) => updateZone(i, { y_mm: v })} step={0.5} min={0} />
            </Field>
            <Field label="x1">
              <NumberInput value={zone.x1_mm} onChange={(v) => updateZone(i, { x1_mm: v })} step={0.5} min={0} />
            </Field>
            <Field label="dikte (pt)">
              <NumberInput value={zone.width_pt} onChange={(v) => updateZone(i, { width_pt: v })} step={0.25} min={0.25} max={10} className="w-12" />
            </Field>
            <Field label="kleur">
              <ColorPicker
                value={zone.color ?? "primary"}
                onChange={(v) => updateZone(i, { color: v })}
                brandColors={brandColors}
              />
            </Field>
          </ZoneRow>
        ))
      )}
    </div>
  );
}
