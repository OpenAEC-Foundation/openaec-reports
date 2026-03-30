import { useCallback, useEffect, useState } from "react";
import jsYaml from "js-yaml";
import type { PageTypeYaml, TextZoneYaml, LineZoneYaml, ImageZoneYaml, ContentFrameYaml, TableConfigYaml } from "@/types/pageType";
import { TextZoneSection } from "./TextZoneSection";
import { LineZoneSection } from "./LineZoneSection";
import { ImageZoneSection } from "./ImageZoneSection";
import { ContentFrameSection } from "./ContentFrameSection";
import { TableConfigSection } from "./TableConfigSection";
import { Field, TextInput } from "./ZoneRow";

interface YamlFormEditorProps {
  yamlContent: string;
  onChange: (yamlContent: string) => void;
  brandColors?: Record<string, string> | null;
}

/** YAML dump opties — leesbare output. */
const DUMP_OPTIONS: jsYaml.DumpOptions = {
  indent: 2,
  lineWidth: 120,
  noRefs: true,
  sortKeys: false,
};

/**
 * Visuele formulier-editor voor page_type YAMLs.
 *
 * Parse YAML → formulier state → dump terug naar YAML bij elke wijziging.
 * Waarschuwing: YAML commentaar gaat verloren bij gebruik van dit formulier.
 */
export function YamlFormEditor({ yamlContent, onChange, brandColors }: YamlFormEditorProps) {
  const [formData, setFormData] = useState<PageTypeYaml | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);

  // Parse YAML → form state (alleen bij initialisatie of externe wijziging)
  useEffect(() => {
    try {
      const parsed = jsYaml.load(yamlContent);
      if (typeof parsed === "object" && parsed !== null) {
        setFormData(parsed as PageTypeYaml);
        setParseError(null);
      } else {
        setParseError("YAML moet een object opleveren");
      }
    } catch (e) {
      if (e instanceof jsYaml.YAMLException) {
        setParseError(e.message);
      }
    }
  // We doen dit alleen bij mount — daarna beheert het formulier de state
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Form → YAML sync
  const syncToYaml = useCallback(
    (data: PageTypeYaml) => {
      try {
        const yaml = jsYaml.dump(data, DUMP_OPTIONS);
        onChange(yaml);
      } catch {
        // Ignore dump errors
      }
    },
    [onChange]
  );

  function updateField(patch: Partial<PageTypeYaml>) {
    if (!formData) return;
    const updated = { ...formData, ...patch };
    setFormData(updated);
    syncToYaml(updated);
  }

  function handleTextZonesChange(zones: TextZoneYaml[]) {
    updateField({ text_zones: zones });
  }

  function handleLineZonesChange(zones: LineZoneYaml[]) {
    updateField({ line_zones: zones });
  }

  function handleImageZonesChange(zones: ImageZoneYaml[]) {
    updateField({ image_zones: zones });
  }

  function handleContentFrameChange(frame: ContentFrameYaml | undefined) {
    if (frame === undefined) {
      const { content_frame: _removed, ...rest } = formData!;
      const updated = rest as PageTypeYaml;
      setFormData(updated);
      syncToYaml(updated);
    } else {
      updateField({ content_frame: frame });
    }
  }

  function handleTableChange(table: TableConfigYaml | undefined) {
    if (table === undefined) {
      const { table: _removed, ...rest } = formData!;
      const updated = rest as PageTypeYaml;
      setFormData(updated);
      syncToYaml(updated);
    } else {
      updateField({ table });
    }
  }

  if (parseError) {
    return (
      <div className="rounded-md border border-oaec-border bg-oaec-danger-soft p-3">
        <p className="text-xs font-semibold text-oaec-danger mb-1">
          YAML parse fout — schakel terug naar Raw YAML om te herstellen
        </p>
        <p className="text-xs text-oaec-danger font-mono">{parseError}</p>
      </div>
    );
  }

  if (!formData) {
    return <div className="text-xs text-oaec-text-faint">Laden...</div>;
  }

  return (
    <div className="space-y-1">
      {/* Metadata */}
      <div className="rounded border border-oaec-border bg-oaec-bg-lighter px-3 py-2 mb-3">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
          <Field label="name" className="flex-1 min-w-[120px]">
            <TextInput
              value={formData.name ?? ""}
              onChange={(v) => updateField({ name: v })}
              placeholder="page type naam"
              className="w-full min-w-[80px]"
            />
          </Field>
          <Field label="stationery">
            <TextInput
              value={formData.stationery ?? ""}
              onChange={(v) => updateField({ stationery: v || null })}
              placeholder="achtergrond.pdf"
              className="w-40"
            />
          </Field>
        </div>
      </div>

      {/* Text Zones */}
      <TextZoneSection
        zones={formData.text_zones ?? []}
        onChange={handleTextZonesChange}
        brandColors={brandColors}
      />

      {/* Line Zones */}
      <LineZoneSection
        zones={formData.line_zones ?? []}
        onChange={handleLineZonesChange}
        brandColors={brandColors}
      />

      {/* Image Zones */}
      <ImageZoneSection
        zones={formData.image_zones ?? []}
        onChange={handleImageZonesChange}
      />

      {/* Content Frame */}
      <ContentFrameSection
        frame={formData.content_frame}
        onChange={handleContentFrameChange}
      />

      {/* Table */}
      <TableConfigSection
        table={formData.table}
        onChange={handleTableChange}
        brandColors={brandColors}
      />

      {/* Hint */}
      <p className="text-[10px] text-oaec-text-faint mt-2">
        Wijzigingen worden automatisch gesynchroniseerd naar de YAML. Preview update live.
      </p>
    </div>
  );
}
