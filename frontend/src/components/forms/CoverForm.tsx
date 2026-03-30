import { useState, useEffect, useRef } from 'react';
import { useReportStore } from '@/stores/reportStore';
import { ExtraFieldRow } from './ExtraFieldRow';
import type { Cover, ImageSourceBase64, ImageMediaType } from '@/types/report';

const inputClass =
  'w-full rounded border border-oaec-border px-2 py-1.5 text-sm focus:border-oaec-accent focus:ring-2 focus:ring-oaec-accent/20 outline-none';

const labelClass = 'block text-xs font-medium text-oaec-text-muted mb-1';

const ACCEPTED_TYPES: Record<string, ImageMediaType> = {
  'image/png': 'image/png',
  'image/jpeg': 'image/jpeg',
  'image/svg+xml': 'image/svg+xml',
};

export function CoverForm() {
  const cover = useReportStore((s) => s.report.cover);
  const setCover = useReportStore((s) => s.setCover);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [subtitle, setSubtitle] = useState(cover.subtitle ?? '');

  // Bug 1 fix: sync local state when store changes externally
  useEffect(() => {
    setSubtitle(cover.subtitle ?? '');
  }, [cover.subtitle]);

  function updateCover(updates: Partial<Cover>) {
    setCover({ ...cover, ...updates });
  }

  function handleSubtitleBlur() {
    if (subtitle !== (cover.subtitle ?? '')) {
      updateCover({ subtitle: subtitle || undefined });
    }
  }

  // --- Image handling ---

  function handleFileSelect(file: File) {
    const mediaType = ACCEPTED_TYPES[file.type];
    if (!mediaType) return;

    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      const base64 = result.split(',')[1] ?? result;
      const imageSource: ImageSourceBase64 = {
        data: base64,
        media_type: mediaType,
        filename: file.name,
      };
      updateCover({ image: imageSource });
    };
    reader.readAsDataURL(file);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  }

  function removeImage() {
    updateCover({ image: undefined });
  }

  // --- Extra fields ---

  const extraFields = cover.extra_fields ?? {};
  const entries = Object.entries(extraFields);

  function updateExtraFields(newFields: Record<string, string>) {
    updateCover({ extra_fields: Object.keys(newFields).length > 0 ? newFields : undefined });
  }

  function addExtraField() {
    if ('' in extraFields) return;
    updateExtraFields({ ...extraFields, '': '' });
  }

  // Bug 3 fix: prevent overwriting existing keys
  function updateExtraFieldKey(oldKey: string, newKey: string) {
    if (newKey === oldKey) return;
    if (newKey in extraFields) return;
    const newFields: Record<string, string> = {};
    for (const [k, v] of Object.entries(extraFields)) {
      newFields[k === oldKey ? newKey : k] = v;
    }
    updateExtraFields(newFields);
  }

  function updateExtraFieldValue(key: string, value: string) {
    updateExtraFields({ ...extraFields, [key]: value });
  }

  function removeExtraField(key: string) {
    const newFields = { ...extraFields };
    delete newFields[key];
    updateExtraFields(newFields);
  }

  // --- Image preview ---

  const hasImage = cover.image !== undefined;
  let imagePreviewSrc: string | null = null;
  if (hasImage) {
    if (typeof cover.image === 'string') {
      // URL or data URI — show if valid, ignore file paths
      if (cover.image.startsWith('data:') || cover.image.startsWith('http')) {
        imagePreviewSrc = cover.image;
      }
      // else: local file path like "renders/gevel_west.png" — can't preview in browser
    } else if (cover.image) {
      imagePreviewSrc = `data:${cover.image.media_type};base64,${cover.image.data}`;
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <h3 className="text-sm font-semibold text-oaec-text-secondary border-b border-oaec-border-subtle pb-2">
        Voorblad configuratie
      </h3>

      {/* Subtitle */}
      <div>
        <label className={labelClass}>Ondertitel</label>
        <input
          type="text"
          className={inputClass}
          value={subtitle}
          onChange={(e) => setSubtitle(e.target.value)}
          onBlur={handleSubtitleBlur}
          placeholder="Ondertitel op voorblad"
        />
      </div>

      {/* Cover image */}
      <div>
        <label className={labelClass}>Cover afbeelding</label>
        {imagePreviewSrc ? (
          <div className="relative rounded-lg border border-oaec-border bg-oaec-bg p-2">
            <img
              src={imagePreviewSrc}
              alt="Cover preview"
              className="max-h-48 w-full rounded object-cover"
            />
            <button
              onClick={removeImage}
              className="absolute top-3 right-3 flex h-6 w-6 items-center justify-center rounded-full bg-oaec-bg-lighter/80 text-oaec-text-muted shadow hover:bg-oaec-danger-soft hover:text-oaec-danger"
              title="Verwijder afbeelding"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        ) : (
          <div
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            onClick={() => fileInputRef.current?.click()}
            className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-oaec-border bg-oaec-bg px-4 py-8 cursor-pointer hover:border-oaec-accent hover:bg-oaec-accent-soft/30 transition-colors"
          >
            <svg className="h-8 w-8 text-oaec-text-faint mb-2" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.41a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0022.5 18.75V5.25A2.25 2.25 0 0020.25 3H3.75A2.25 2.25 0 001.5 5.25v13.5A2.25 2.25 0 003.75 21z" />
            </svg>
            <p className="text-sm text-oaec-text-faint">
              Klik of sleep een afbeelding hierheen
            </p>
            <p className="text-xs text-oaec-text-faint mt-1">PNG, JPG of SVG</p>
            {typeof cover.image === 'string' && !imagePreviewSrc && (
              <p className="text-xs text-oaec-accent mt-2">
                Huidig pad: {cover.image} (niet beschikbaar in browser)
              </p>
            )}
          </div>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg,image/svg+xml"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFileSelect(file);
            e.target.value = '';
          }}
        />
      </div>

      {/* Extra fields */}
      <div>
        <label className={labelClass}>Extra velden</label>
        <div className="space-y-2">
          {/* Bug 5 fix: use key+index for stable React key */}
          {entries.map(([key, value], idx) => (
            <ExtraFieldRow
              key={`${idx}-${key}`}
              fieldKey={key}
              fieldValue={value}
              onKeyChange={(newKey) => updateExtraFieldKey(key, newKey)}
              onValueChange={(newValue) => updateExtraFieldValue(key, newValue)}
              onRemove={() => removeExtraField(key)}
            />
          ))}
          <button
            onClick={addExtraField}
            className="flex items-center gap-1 rounded px-2 py-1 text-xs text-oaec-text-faint hover:bg-oaec-accent-soft hover:text-oaec-accent transition-colors"
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Veld toevoegen
          </button>
        </div>
      </div>
    </div>
  );
}
