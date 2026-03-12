import type { TextZoneYaml } from "@/types/pageType";
import { ColorPicker } from "./ColorPicker";
import { Field, NumberInput, SelectInput, TextInput, ZoneRow } from "./ZoneRow";

interface TextZoneSectionProps {
  zones: TextZoneYaml[];
  onChange: (zones: TextZoneYaml[]) => void;
  brandColors?: Record<string, string> | null;
}

const ALIGN_OPTIONS = [
  { value: "left", label: "Links" },
  { value: "center", label: "Midden" },
  { value: "right", label: "Rechts" },
];

const FONT_OPTIONS = [
  { value: "body", label: "body" },
  { value: "heading", label: "heading" },
  { value: "heading_bold", label: "heading_bold" },
  { value: "body_bold", label: "body_bold" },
];

function newTextZone(): TextZoneYaml {
  return { bind: "", x_mm: 20, y_mm: 20, font: "body", size: 10, color: "text", align: "left" };
}

/**
 * Lijst van TextZone rijen (bind, x/y, font, size, color, align).
 */
export function TextZoneSection({ zones, onChange, brandColors }: TextZoneSectionProps) {
  function updateZone(index: number, patch: Partial<TextZoneYaml>) {
    const updated = zones.map((z, i) => (i === index ? { ...z, ...patch } : z));
    onChange(updated);
  }

  function deleteZone(index: number) {
    onChange(zones.filter((_, i) => i !== index));
  }

  function addZone() {
    onChange([...zones, newTextZone()]);
  }

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-1.5">
        <h4 className="text-xs font-semibold text-gray-700">Text Zones ({zones.length})</h4>
        <button
          type="button"
          onClick={addZone}
          className="rounded bg-purple-50 px-2 py-0.5 text-[10px] font-medium text-purple-600 hover:bg-purple-100 transition-colors"
        >
          + Toevoegen
        </button>
      </div>

      {zones.length === 0 ? (
        <p className="text-xs text-gray-400 italic">Geen text zones</p>
      ) : (
        zones.map((zone, i) => (
          <ZoneRow key={i} index={i} onDelete={deleteZone}>
            <Field label="bind" className="flex-1 min-w-[120px]">
              <TextInput
                value={zone.bind}
                onChange={(v) => updateZone(i, { bind: v })}
                placeholder="client.name"
                className="w-full min-w-[80px]"
              />
            </Field>
            <Field label="x">
              <NumberInput value={zone.x_mm} onChange={(v) => updateZone(i, { x_mm: v })} step={0.5} min={0} />
            </Field>
            <Field label="y">
              <NumberInput value={zone.y_mm} onChange={(v) => updateZone(i, { y_mm: v })} step={0.5} min={0} />
            </Field>
            <Field label="font">
              <SelectInput
                value={zone.font ?? "body"}
                onChange={(v) => updateZone(i, { font: v })}
                options={FONT_OPTIONS}
                className="w-24"
              />
            </Field>
            <Field label="size">
              <NumberInput value={zone.size} onChange={(v) => updateZone(i, { size: v })} step={0.5} min={4} max={72} className="w-12" />
            </Field>
            <Field label="kleur">
              <ColorPicker
                value={zone.color ?? "text"}
                onChange={(v) => updateZone(i, { color: v })}
                brandColors={brandColors}
              />
            </Field>
            <Field label="align">
              <SelectInput
                value={zone.align ?? "left"}
                onChange={(v) => updateZone(i, { align: v as TextZoneYaml["align"] })}
                options={ALIGN_OPTIONS}
                className="w-16"
              />
            </Field>
          </ZoneRow>
        ))
      )}
    </div>
  );
}
