import { useState, useRef, useCallback } from 'react';
import type { ImageBlock, ImageSourceBase64, ImageAlignment, ImageMediaType } from '@/types/report';

interface ImageEditorProps {
  block: ImageBlock & { id: string };
  onChange: (updates: Partial<ImageBlock>) => void;
}

const inputClass =
  'w-full rounded border border-gray-200 px-2 py-1.5 text-sm focus:border-blue-300 focus:ring-2 focus:ring-blue-100 outline-none';
const labelClass = 'text-xs font-medium text-gray-500 mb-1';

const ALIGNMENTS: { value: ImageAlignment; label: string }[] = [
  { value: 'left', label: 'Links' },
  { value: 'center', label: 'Midden' },
  { value: 'right', label: 'Rechts' },
];

function getMediaType(file: File): ImageMediaType {
  if (file.type === 'image/png') return 'image/png';
  if (file.type === 'image/svg+xml') return 'image/svg+xml';
  return 'image/jpeg';
}

function getPreviewUrl(src: ImageBlock['src']): string | null {
  if (!src) return null;
  if (typeof src === 'string') return src || null;
  return `data:${src.media_type};base64,${src.data}`;
}

export function ImageEditor({ block, onChange }: ImageEditorProps) {
  const [urlInput, setUrlInput] = useState(typeof block.src === 'string' ? block.src : '');
  const [caption, setCaption] = useState(block.caption ?? '');
  const [width, setWidth] = useState(block.width_mm ?? 150);
  const [alignment, setAlignment] = useState<ImageAlignment>(block.alignment ?? 'center');
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const previewUrl = getPreviewUrl(block.src);

  const handleFile = useCallback(
    (file: File) => {
      // Validatie: max 10MB
      if (file.size > 10 * 1024 * 1024) {
        setError('Bestand is te groot (max 10 MB)');
        return;
      }

      const reader = new FileReader();
      reader.onload = () => {
        const dataUrl = reader.result as string;
        // Extract base64 data (remove "data:image/...;base64," prefix)
        const base64Data = dataUrl.split(',')[1];
        if (base64Data) {
          const source: ImageSourceBase64 = {
            data: base64Data,
            media_type: getMediaType(file),
            filename: file.name,
          };
          onChange({ src: source });
          setUrlInput('');
          setError(null);
        }
      };
      reader.onerror = () => {
        setError('Kon bestand niet lezen. Probeer een ander bestand.');
      };
      reader.readAsDataURL(file);
    },
    [onChange],
  );

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      handleFile(file);
    }
  }

  function handleFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
  }

  function handleUrlBlur() {
    if (urlInput !== (typeof block.src === 'string' ? block.src : '')) {
      onChange({ src: urlInput });
    }
  }

  function handleCaptionBlur() {
    if (caption !== (block.caption ?? '')) {
      onChange({ caption: caption || undefined });
    }
  }

  function handleWidthInput(value: number) {
    setWidth(value);
  }

  function handleWidthCommit() {
    onChange({ width_mm: width });
  }

  function handleAlignmentChange(value: ImageAlignment) {
    setAlignment(value);
    onChange({ alignment: value });
  }

  return (
    <div className="space-y-3">
      {/* Drop zone / preview */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`flex min-h-[80px] cursor-pointer items-center justify-center rounded-lg border-2 border-dashed transition-colors ${
          isDragOver
            ? 'border-purple-400 bg-purple-50'
            : 'border-gray-200 bg-gray-50 hover:border-gray-300'
        }`}
      >
        {previewUrl ? (
          <img
            src={previewUrl}
            alt={caption || 'Preview'}
            className="max-h-40 max-w-full rounded object-contain"
          />
        ) : (
          <div className="py-4 text-center">
            <p className="text-sm text-gray-500">
              Sleep een afbeelding hierheen of klik om te uploaden
            </p>
            <p className="mt-1 text-[10px] text-gray-400">PNG, JPEG, SVG</p>
          </div>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg,image/svg+xml"
          onChange={handleFileInput}
          className="hidden"
        />
      </div>

      {error && (
        <p className="text-xs text-red-500 mt-1">{error}</p>
      )}

      {/* URL input */}
      <div>
        <label className={labelClass}>Of URL</label>
        <input
          type="text"
          className={inputClass}
          value={urlInput}
          onChange={(e) => setUrlInput(e.target.value)}
          onBlur={handleUrlBlur}
          placeholder="https://example.com/afbeelding.png"
        />
      </div>

      {/* Caption */}
      <div>
        <label className={labelClass}>Bijschrift</label>
        <textarea
          className={`${inputClass} resize-none`}
          value={caption}
          onChange={(e) => setCaption(e.target.value)}
          onBlur={handleCaptionBlur}
          placeholder="Optioneel bijschrift"
          rows={2}
        />
      </div>

      {/* Width slider + alignment */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={labelClass}>Breedte: {width} mm</label>
          <input
            type="range"
            min={50}
            max={210}
            step={1}
            value={width}
            onChange={(e) => handleWidthInput(Number(e.target.value))}
            onPointerUp={handleWidthCommit}
            onKeyUp={handleWidthCommit}
            className="w-full accent-purple-400"
          />
          <div className="flex justify-between text-[10px] text-gray-400">
            <span>50 mm</span>
            <span>210 mm</span>
          </div>
        </div>

        <div>
          <label className={labelClass}>Uitlijning</label>
          <div className="flex gap-1">
            {ALIGNMENTS.map(({ value, label }) => (
              <button
                key={value}
                type="button"
                onClick={() => handleAlignmentChange(value)}
                className={`flex-1 rounded border px-2 py-1.5 text-xs font-medium transition-colors ${
                  alignment === value
                    ? 'border-purple-300 bg-purple-50 text-purple-700'
                    : 'border-gray-200 text-gray-500 hover:bg-gray-50'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
