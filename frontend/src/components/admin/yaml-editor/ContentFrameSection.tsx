import type { ContentFrameYaml } from "@/types/pageType";
import { Field, NumberInput } from "./ZoneRow";

interface ContentFrameSectionProps {
  frame: ContentFrameYaml | undefined;
  onChange: (frame: ContentFrameYaml | undefined) => void;
}

const DEFAULT_FRAME: ContentFrameYaml = {
  x_mm: 20,
  y_mm: 40,
  width_mm: 170,
  height_mm: 240,
};

/**
 * Content frame editor — definieert het tekstgebied op de pagina.
 */
export function ContentFrameSection({ frame, onChange }: ContentFrameSectionProps) {
  function handleToggle() {
    if (frame) {
      onChange(undefined);
    } else {
      onChange({ ...DEFAULT_FRAME });
    }
  }

  function updateField(patch: Partial<ContentFrameYaml>) {
    if (!frame) return;
    onChange({ ...frame, ...patch });
  }

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-1.5">
        <h4 className="text-xs font-semibold text-gray-700">Content Frame</h4>
        <button
          type="button"
          onClick={handleToggle}
          className={`rounded px-2 py-0.5 text-[10px] font-medium transition-colors ${
            frame
              ? "bg-red-50 text-red-600 hover:bg-red-100"
              : "bg-purple-50 text-purple-600 hover:bg-purple-100"
          }`}
        >
          {frame ? "Verwijderen" : "+ Toevoegen"}
        </button>
      </div>

      {frame ? (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 rounded border border-gray-200 bg-white px-3 py-2">
          <Field label="x">
            <NumberInput value={frame.x_mm} onChange={(v) => updateField({ x_mm: v })} step={0.5} min={0} />
          </Field>
          <Field label="y">
            <NumberInput value={frame.y_mm} onChange={(v) => updateField({ y_mm: v })} step={0.5} min={0} />
          </Field>
          <Field label="breedte">
            <NumberInput value={frame.width_mm} onChange={(v) => updateField({ width_mm: v })} step={0.5} min={10} />
          </Field>
          <Field label="hoogte">
            <NumberInput value={frame.height_mm} onChange={(v) => updateField({ height_mm: v })} step={0.5} min={10} />
          </Field>
          <p className="text-[10px] text-gray-400 w-full mt-1">
            Definieert het bereik waar rapport-inhoud (secties) wordt geplaatst.
          </p>
        </div>
      ) : (
        <p className="text-xs text-gray-400 italic">Geen content frame — hele pagina beschikbaar</p>
      )}
    </div>
  );
}
