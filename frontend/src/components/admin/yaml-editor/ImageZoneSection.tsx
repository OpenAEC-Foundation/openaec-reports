import type { ImageZoneYaml } from "@/types/pageType";
import { Field, NumberInput, TextInput, ZoneRow } from "./ZoneRow";

interface ImageZoneSectionProps {
  zones: ImageZoneYaml[];
  onChange: (zones: ImageZoneYaml[]) => void;
}

function newImageZone(): ImageZoneYaml {
  return { bind: "", x_mm: 20, y_mm: 20, width_mm: 60, height_mm: 40 };
}

/**
 * Lijst van ImageZone rijen (bind, x/y, width/height, fallback).
 */
export function ImageZoneSection({ zones, onChange }: ImageZoneSectionProps) {
  function updateZone(index: number, patch: Partial<ImageZoneYaml>) {
    const updated = zones.map((z, i) => (i === index ? { ...z, ...patch } : z));
    onChange(updated);
  }

  function deleteZone(index: number) {
    onChange(zones.filter((_, i) => i !== index));
  }

  function addZone() {
    onChange([...zones, newImageZone()]);
  }

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-1.5">
        <h4 className="text-xs font-semibold text-oaec-text-secondary">Image Zones ({zones.length})</h4>
        <button
          type="button"
          onClick={addZone}
          className="rounded bg-oaec-accent-soft px-2 py-0.5 text-[10px] font-medium text-oaec-accent hover:bg-oaec-accent-soft transition-colors"
        >
          + Toevoegen
        </button>
      </div>

      {zones.length === 0 ? (
        <p className="text-xs text-oaec-text-faint italic">Geen image zones</p>
      ) : (
        zones.map((zone, i) => (
          <ZoneRow key={i} index={i} onDelete={deleteZone}>
            <Field label="bind" className="flex-1 min-w-[120px]">
              <TextInput
                value={zone.bind}
                onChange={(v) => updateZone(i, { bind: v })}
                placeholder="project.photo"
                className="w-full min-w-[80px]"
              />
            </Field>
            <Field label="x">
              <NumberInput value={zone.x_mm} onChange={(v) => updateZone(i, { x_mm: v })} step={0.5} min={0} />
            </Field>
            <Field label="y">
              <NumberInput value={zone.y_mm} onChange={(v) => updateZone(i, { y_mm: v })} step={0.5} min={0} />
            </Field>
            <Field label="w">
              <NumberInput value={zone.width_mm} onChange={(v) => updateZone(i, { width_mm: v })} step={0.5} min={1} />
            </Field>
            <Field label="h">
              <NumberInput value={zone.height_mm} onChange={(v) => updateZone(i, { height_mm: v })} step={0.5} min={1} />
            </Field>
            <Field label="fallback" className="min-w-[100px]">
              <TextInput
                value={zone.fallback ?? ""}
                onChange={(v) => updateZone(i, { fallback: v || undefined })}
                placeholder="placeholder.png"
                className="w-28"
              />
            </Field>
          </ZoneRow>
        ))
      )}
    </div>
  );
}
