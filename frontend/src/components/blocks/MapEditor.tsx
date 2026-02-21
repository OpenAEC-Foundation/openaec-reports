import { useState } from 'react';
import type { MapBlock, MapLayer } from '@/types/report';

interface MapEditorProps {
  block: MapBlock & { id: string };
  onChange: (updates: Partial<MapBlock>) => void;
}

const inputClass =
  'w-full rounded border border-gray-200 px-2 py-1.5 text-sm focus:border-blue-300 focus:ring-2 focus:ring-blue-100 outline-none';
const labelClass = 'text-xs font-medium text-gray-500 mb-1';

const ALL_LAYERS: { value: MapLayer; label: string }[] = [
  { value: 'percelen', label: 'Percelen' },
  { value: 'bebouwing', label: 'Bebouwing' },
  { value: 'bestemmingsplan', label: 'Bestemmingsplan' },
  { value: 'luchtfoto', label: 'Luchtfoto' },
];

export function MapEditor({ block, onChange }: MapEditorProps) {
  const [lat, setLat] = useState(block.center?.lat ?? 52.0907);
  const [lon, setLon] = useState(block.center?.lon ?? 5.1214);
  const [radius, setRadius] = useState(block.radius_m ?? 100);
  const [layers, setLayers] = useState<MapLayer[]>(block.layers ?? ['percelen', 'bebouwing']);
  const [caption, setCaption] = useState(block.caption ?? '');
  const [width, setWidth] = useState(block.width_mm ?? 150);

  function handleCoordBlur() {
    onChange({ center: { lat, lon } });
  }

  function handleRadiusBlur() {
    onChange({ radius_m: radius });
  }

  function handleLayerToggle(layer: MapLayer) {
    const newLayers = layers.includes(layer)
      ? layers.filter((l) => l !== layer)
      : [...layers, layer];
    setLayers(newLayers);
    onChange({ layers: newLayers });
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

  return (
    <div className="space-y-3">
      {/* Coordinates */}
      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className={labelClass}>Latitude</label>
          <input
            type="number"
            step={0.0001}
            className={inputClass}
            value={lat}
            onChange={(e) => setLat(parseFloat(e.target.value) || 0)}
            onBlur={handleCoordBlur}
          />
        </div>
        <div>
          <label className={labelClass}>Longitude</label>
          <input
            type="number"
            step={0.0001}
            className={inputClass}
            value={lon}
            onChange={(e) => setLon(parseFloat(e.target.value) || 0)}
            onBlur={handleCoordBlur}
          />
        </div>
        <div>
          <label className={labelClass}>Radius (m)</label>
          <input
            type="number"
            step={10}
            min={10}
            className={inputClass}
            value={radius}
            onChange={(e) => setRadius(parseInt(e.target.value) || 100)}
            onBlur={handleRadiusBlur}
          />
        </div>
      </div>

      {/* Layers */}
      <div>
        <label className={labelClass}>Kaartlagen</label>
        <div className="flex flex-wrap gap-2">
          {ALL_LAYERS.map(({ value, label }) => (
            <label
              key={value}
              className={`flex cursor-pointer items-center gap-1.5 rounded border px-2.5 py-1.5 text-xs transition-colors ${
                layers.includes(value)
                  ? 'border-emerald-300 bg-emerald-50 text-emerald-700'
                  : 'border-gray-200 text-gray-500 hover:bg-gray-50'
              }`}
            >
              <input
                type="checkbox"
                checked={layers.includes(value)}
                onChange={() => handleLayerToggle(value)}
                className="sr-only"
              />
              <span
                className={`h-3 w-3 rounded-sm border flex items-center justify-center ${
                  layers.includes(value)
                    ? 'border-emerald-500 bg-emerald-500'
                    : 'border-gray-300'
                }`}
              >
                {layers.includes(value) && (
                  <svg className="h-2 w-2 text-white" fill="none" viewBox="0 0 24 24" strokeWidth={3} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                )}
              </span>
              {label}
            </label>
          ))}
        </div>
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

      {/* Width slider */}
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
          className="w-full accent-emerald-400"
        />
        <div className="flex justify-between text-[10px] text-gray-400">
          <span>50 mm</span>
          <span>210 mm</span>
        </div>
      </div>
    </div>
  );
}
