import { useState, useCallback, useRef, useEffect } from 'react';
import type { MapBlock, MapLayer } from '@/types/report';

interface MapEditorProps {
  block: MapBlock & { id: string };
  onChange: (updates: Partial<MapBlock>) => void;
}

const inputClass =
  'w-full rounded border border-gray-200 px-2 py-1.5 text-sm focus:border-blue-300 focus:ring-2 focus:ring-blue-100 outline-none';
const labelClass = 'text-xs font-medium text-gray-500 mb-1';

const ALL_LAYERS: { value: MapLayer; label: string; desc: string }[] = [
  { value: 'brt', label: 'Topografie', desc: 'Standaard kaart' },
  { value: 'brt_grijs', label: 'Topo grijs', desc: 'Grijze variant' },
  { value: 'luchtfoto', label: 'Luchtfoto', desc: 'Meest recente' },
  { value: 'kadastraal', label: 'Kadastraal', desc: 'Perceel grenzen' },
];

const ZOOM_LABELS: Record<number, string> = {
  13: 'Regio (~1:50k)',
  14: 'Wijk (~1:25k)',
  15: 'Buurt (~1:10k)',
  16: 'Straat (~1:5k)',
  17: 'Blok (~1:2k)',
  18: 'Perceel (~1:1k)',
};

// PDOK Locatieserver — publieke API, CORS-enabled
const PDOK_SUGGEST_URL = 'https://api.pdok.nl/bzk/locatieserver/search/v3_1/suggest';

interface GeoResult {
  id: string;
  weergavenaam: string;
  type: string;
  lat: number;
  lon: number;
}

export function MapEditor({ block, onChange }: MapEditorProps) {
  const [address, setAddress] = useState(block.address ?? '');
  const [zoom, setZoom] = useState(block.zoom ?? 16);
  const [layers, setLayers] = useState<MapLayer[]>(block.layers ?? ['brt']);
  const [caption, setCaption] = useState(block.caption ?? '');
  const [widthMm, setWidthMm] = useState(block.width_mm ?? 170);

  // Geocoding state
  const [suggestions, setSuggestions] = useState<GeoResult[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [resolvedName, setResolvedName] = useState('');
  const [resolvedCoords, setResolvedCoords] = useState<{ lat: number; lon: number } | null>(
    block.center?.lat && block.center?.lon ? { lat: block.center.lat, lon: block.center.lon } : null
  );
  const [isGeocoding, setIsGeocoding] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const debounceRef = useRef<ReturnType<typeof setTimeout>>();
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // --- PDOK suggest (type-ahead) ---
  const fetchSuggestions = useCallback(async (q: string) => {
    if (q.length < 3) {
      setSuggestions([]);
      return;
    }
    try {
      const res = await fetch(`${PDOK_SUGGEST_URL}?q=${encodeURIComponent(q)}&rows=5`);
      const data = await res.json();
      const docs = data?.response?.docs ?? [];
      const results: GeoResult[] = [];
      for (const doc of docs) {
        const centroid = doc.centroide_ll ?? '';
        if (centroid.startsWith('POINT(')) {
          const coords = centroid.slice(6, -1).split(' ');
          results.push({
            id: doc.id,
            weergavenaam: doc.weergavenaam ?? '',
            type: doc.type ?? '',
            lat: parseFloat(coords[1]),
            lon: parseFloat(coords[0]),
          });
        }
      }
      setSuggestions(results);
      setShowSuggestions(results.length > 0);
    } catch {
      setSuggestions([]);
    }
  }, []);

  function handleAddressInput(value: string) {
    setAddress(value);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchSuggestions(value), 300);
  }

  function selectSuggestion(result: GeoResult) {
    setAddress(result.weergavenaam);
    setResolvedName(result.weergavenaam);
    setResolvedCoords({ lat: result.lat, lon: result.lon });
    setShowSuggestions(false);
    setSuggestions([]);

    onChange({
      address: result.weergavenaam,
      center: { lat: result.lat, lon: result.lon },
    });

    // Generate preview
    updatePreview(result.lat, result.lon, zoom, layers[0] ?? 'brt');
  }

  function handleAddressBlur() {
    // Delay to allow click on suggestion
    setTimeout(() => setShowSuggestions(false), 200);

    if (address !== (block.address ?? '')) {
      onChange({ address });

      // If no coords yet, try geocoding the typed address
      if (!resolvedCoords && address.length >= 3) {
        geocodeAddress(address);
      }
    }
  }

  async function geocodeAddress(q: string) {
    setIsGeocoding(true);
    try {
      const res = await fetch(
        `https://api.pdok.nl/bzk/locatieserver/search/v3_1/free?q=${encodeURIComponent(q)}&rows=1&fl=*`
      );
      const data = await res.json();
      const docs = data?.response?.docs ?? [];
      if (docs.length > 0) {
        const doc = docs[0];
        const centroid = doc.centroide_ll ?? '';
        if (centroid.startsWith('POINT(')) {
          const coords = centroid.slice(6, -1).split(' ');
          const lat = parseFloat(coords[1]);
          const lon = parseFloat(coords[0]);
          setResolvedName(doc.weergavenaam ?? q);
          setResolvedCoords({ lat, lon });
          onChange({ center: { lat, lon } });
          updatePreview(lat, lon, zoom, layers[0] ?? 'brt');
        }
      }
    } catch {
      // Geocoding fails silently — backend will retry
    } finally {
      setIsGeocoding(false);
    }
  }

  // --- WMS preview ---
  function updatePreview(lat: number, lon: number, z: number, layer: string) {
    const metersPerPx = (156543.03 * Math.cos((lat * Math.PI) / 180)) / Math.pow(2, z);
    const halfW = 200 * metersPerPx;
    const halfH = 133 * metersPerPx;
    const dlat = halfH / 111320.0;
    const dlon = halfW / (111320.0 * Math.cos((lat * Math.PI) / 180));
    const bbox = `${lat - dlat},${lon - dlon},${lat + dlat},${lon + dlon}`;

    const serviceUrls: Record<string, { url: string; layers: string }> = {
      brt: { url: 'https://service.pdok.nl/brt/achtergrondkaart/wms/v2_0', layers: 'standaard' },
      brt_grijs: { url: 'https://service.pdok.nl/brt/achtergrondkaart/wms/v2_0', layers: 'grijs' },
      luchtfoto: { url: 'https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0', layers: 'Actueel_orthoHR' },
      kadastraal: { url: 'https://service.pdok.nl/kadaster/kadastralekaart/wms/v5_0', layers: 'Kadastralekaart' },
    };

    const svc = serviceUrls[layer] ?? serviceUrls['brt'];
    const params = new URLSearchParams({
      SERVICE: 'WMS',
      VERSION: '1.3.0',
      REQUEST: 'GetMap',
      LAYERS: svc!.layers,
      CRS: 'EPSG:4326',
      BBOX: bbox,
      WIDTH: '400',
      HEIGHT: '266',
      FORMAT: 'image/png',
      STYLES: '',
    });
    setPreviewUrl(`${svc!.url}?${params.toString()}`);
  }

  // Update preview when zoom or layers change
  useEffect(() => {
    if (resolvedCoords) {
      updatePreview(resolvedCoords.lat, resolvedCoords.lon, zoom, layers[0] ?? 'brt');
    }
  }, [zoom, layers, resolvedCoords]);

  // --- Layer toggle ---
  function handleLayerToggle(layer: MapLayer) {
    const newLayers = layers.includes(layer)
      ? layers.filter((l) => l !== layer)
      : [...layers, layer];
    if (newLayers.length === 0) return; // Minimaal 1 laag
    setLayers(newLayers);
    onChange({ layers: newLayers });
  }

  // --- Zoom ---
  function handleZoomChange(value: number) {
    setZoom(value);
    onChange({ zoom: value });
  }

  // --- Caption ---
  function handleCaptionBlur() {
    if (caption !== (block.caption ?? '')) {
      onChange({ caption: caption || undefined });
    }
  }

  // --- Width ---
  function handleWidthCommit() {
    onChange({ width_mm: widthMm });
  }

  // Close suggestions on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (suggestionsRef.current && !suggestionsRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="space-y-3">
      {/* Address with autocomplete */}
      <div className="relative" ref={suggestionsRef}>
        <label className={labelClass}>
          Adres / locatie
          {isGeocoding && <span className="ml-2 text-blue-400 animate-pulse">zoeken…</span>}
        </label>
        <div className="relative">
          <input
            type="text"
            className={inputClass}
            value={address}
            onChange={(e) => handleAddressInput(e.target.value)}
            onBlur={handleAddressBlur}
            onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
            placeholder="Bijv. Kijkduinsestraat 100, Den Haag"
          />
          <svg className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
        </div>

        {/* Suggestions dropdown */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute z-50 mt-1 w-full rounded-md border border-gray-200 bg-white shadow-lg max-h-48 overflow-y-auto">
            {suggestions.map((s) => (
              <button
                key={s.id}
                type="button"
                className="w-full px-3 py-2 text-left text-sm hover:bg-emerald-50 transition-colors flex items-start gap-2"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => selectSuggestion(s)}
              >
                <svg className="h-4 w-4 text-emerald-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
                </svg>
                <div>
                  <div className="text-gray-800">{s.weergavenaam}</div>
                  <div className="text-[10px] text-gray-400">{s.type}</div>
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Resolved location indicator */}
        {resolvedCoords && resolvedName && (
          <div className="mt-1 flex items-center gap-1.5 text-[11px] text-emerald-600">
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
            {resolvedName}
            <span className="text-gray-400 ml-1">
              ({resolvedCoords.lat.toFixed(4)}, {resolvedCoords.lon.toFixed(4)})
            </span>
          </div>
        )}
      </div>

      {/* Map preview */}
      {previewUrl && (
        <div className="rounded-md overflow-hidden border border-gray-200 bg-gray-100">
          <img
            src={previewUrl}
            alt="Kaart preview"
            className="w-full h-auto"
            style={{ aspectRatio: '3/2' }}
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        </div>
      )}

      {/* Layers */}
      <div>
        <label className={labelClass}>Kaartlagen (elke laag wordt een apart kaartje)</label>
        <div className="flex flex-wrap gap-2">
          {ALL_LAYERS.map(({ value, label, desc }) => (
            <label
              key={value}
              title={desc}
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

      {/* Zoom */}
      <div>
        <label className={labelClass}>
          Zoom: {zoom} — {ZOOM_LABELS[zoom] ?? ''}
        </label>
        <input
          type="range"
          min={13}
          max={18}
          step={1}
          value={zoom}
          onChange={(e) => handleZoomChange(Number(e.target.value))}
          className="w-full accent-emerald-400"
        />
        <div className="flex justify-between text-[10px] text-gray-400">
          <span>Regio</span>
          <span>Perceel</span>
        </div>
      </div>

      {/* Caption */}
      <div>
        <label className={labelClass}>Bijschrift</label>
        <input
          type="text"
          className={inputClass}
          value={caption}
          onChange={(e) => setCaption(e.target.value)}
          onBlur={handleCaptionBlur}
          placeholder="Optioneel bijschrift onder de kaart"
        />
      </div>

      {/* Width slider */}
      <div>
        <label className={labelClass}>Breedte: {widthMm} mm</label>
        <input
          type="range"
          min={80}
          max={170}
          step={5}
          value={widthMm}
          onChange={(e) => setWidthMm(Number(e.target.value))}
          onPointerUp={handleWidthCommit}
          onKeyUp={handleWidthCommit}
          className="w-full accent-emerald-400"
        />
        <div className="flex justify-between text-[10px] text-gray-400">
          <span>80 mm</span>
          <span>170 mm</span>
        </div>
      </div>

      {/* Manual coordinates (collapsible) */}
      <ManualCoords
        lat={resolvedCoords?.lat}
        lon={resolvedCoords?.lon}
        onUpdate={(lat, lon) => {
          setResolvedCoords({ lat, lon });
          onChange({ center: { lat, lon } });
          updatePreview(lat, lon, zoom, layers[0] ?? 'brt');
        }}
      />
    </div>
  );
}

// --- Collapsible manual coordinates ---
function ManualCoords({
  lat,
  lon,
  onUpdate,
}: {
  lat?: number;
  lon?: number;
  onUpdate: (lat: number, lon: number) => void;
}) {
  const [open, setOpen] = useState(false);
  const [latVal, setLatVal] = useState(lat ?? 52.0907);
  const [lonVal, setLonVal] = useState(lon ?? 5.1214);

  // Sync when parent changes
  useEffect(() => {
    if (lat !== undefined) setLatVal(lat);
    if (lon !== undefined) setLonVal(lon);
  }, [lat, lon]);

  return (
    <div className="border-t border-gray-100 pt-2">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-[11px] text-gray-400 hover:text-gray-600 transition-colors"
      >
        <svg
          className={`h-3 w-3 transition-transform ${open ? 'rotate-90' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2}
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
        </svg>
        Handmatige coördinaten
      </button>
      {open && (
        <div className="mt-2 grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs font-medium text-gray-500 mb-1">Latitude</label>
            <input
              type="number"
              step={0.0001}
              className="w-full rounded border border-gray-200 px-2 py-1.5 text-sm focus:border-blue-300 focus:ring-2 focus:ring-blue-100 outline-none"
              value={latVal}
              onChange={(e) => setLatVal(parseFloat(e.target.value) || 0)}
              onBlur={() => onUpdate(latVal, lonVal)}
            />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 mb-1">Longitude</label>
            <input
              type="number"
              step={0.0001}
              className="w-full rounded border border-gray-200 px-2 py-1.5 text-sm focus:border-blue-300 focus:ring-2 focus:ring-blue-100 outline-none"
              value={lonVal}
              onChange={(e) => setLonVal(parseFloat(e.target.value) || 0)}
              onBlur={() => onUpdate(latVal, lonVal)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
