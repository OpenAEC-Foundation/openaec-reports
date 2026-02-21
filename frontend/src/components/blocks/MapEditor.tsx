import { useState, useCallback, useRef, useEffect } from 'react';
import type { MapBlock, MapLayer, CadastralInfo } from '@/types/report';

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

const PDOK_SUGGEST_URL = 'https://api.pdok.nl/bzk/locatieserver/search/v3_1/suggest';
const PDOK_REVERSE_URL = 'https://api.pdok.nl/bzk/locatieserver/search/v3_1/reverse';

interface GeoResult {
  id: string;
  weergavenaam: string;
  type: string;
  lat: number;
  lon: number;
  gekoppeld_perceel?: string[];
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

  // Cadastral state
  const [cadastral, setCadastral] = useState<CadastralInfo | null>(block.cadastral ?? null);
  const [isCadastralLoading, setIsCadastralLoading] = useState(false);
  const [cadastralError, setCadastralError] = useState('');
  const [linkedPerceel, setLinkedPerceel] = useState<string | null>(null);

  const debounceRef = useRef<ReturnType<typeof setTimeout>>();
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // --- PDOK suggest (type-ahead) ---
  const fetchSuggestions = useCallback(async (q: string) => {
    if (q.length < 3) {
      setSuggestions([]);
      return;
    }
    try {
      const res = await fetch(`${PDOK_SUGGEST_URL}?q=${encodeURIComponent(q)}&rows=5&fl=*`);
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
            gekoppeld_perceel: doc.gekoppeld_perceel ?? undefined,
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
    // Clear cadastral when address changes
    setCadastral(null);
    setCadastralError('');
    // Store linked parcel ID from BAG for accurate cadastral lookup
    setLinkedPerceel(result.gekoppeld_perceel?.[0] ?? null);

    onChange({
      address: result.weergavenaam,
      center: { lat: result.lat, lon: result.lon },
      cadastral: undefined,
    });

    updatePreview(result.lat, result.lon, zoom, layers[0] ?? 'brt');
  }

  function handleAddressBlur() {
    setTimeout(() => setShowSuggestions(false), 200);

    if (address !== (block.address ?? '')) {
      onChange({ address });
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
      // silent
    } finally {
      setIsGeocoding(false);
    }
  }

  // --- Cadastral lookup ---
  async function lookupCadastral() {
    if (!resolvedCoords) return;
    setIsCadastralLoading(true);
    setCadastralError('');
    try {
      let doc: Record<string, unknown> | null = null;

      // Strategy 1: Use gekoppeld_perceel from BAG (accurate, linked to address)
      if (linkedPerceel) {
        const res = await fetch(
          `https://api.pdok.nl/bzk/locatieserver/search/v3_1/free?q=${encodeURIComponent(linkedPerceel)}&fq=type:perceel&rows=1&fl=*`
        );
        const data = await res.json();
        const docs = data?.response?.docs ?? [];
        // Verify we got the right parcel (exact match on identificatie)
        if (docs.length > 0 && docs[0].identificatie === linkedPerceel) {
          doc = docs[0];
        }
      }

      // Strategy 2: Fallback to reverse geocode on coordinates
      if (!doc) {
        const res = await fetch(
          `${PDOK_REVERSE_URL}?lat=${resolvedCoords.lat}&lon=${resolvedCoords.lon}&type=perceel&rows=1&fl=*`
        );
        const data = await res.json();
        const docs = data?.response?.docs ?? [];
        if (docs.length > 0) {
          doc = docs[0];
        }
      }

      if (!doc) {
        setCadastralError('Geen kadastraal perceel gevonden op deze locatie.');
        return;
      }

      const info: CadastralInfo = {
        identificatie: (doc.identificatie as string) ?? '',
        gemeentecode: (doc.kadastrale_gemeentecode as string) ?? '',
        gemeentenaam: (doc.kadastrale_gemeentenaam as string) ?? '',
        sectie: (doc.kadastrale_sectie as string) ?? '',
        perceelnummer: (doc.perceelnummer as string) ?? '',
        grootte: (doc.kadastrale_grootte as number) ?? 0,
        weergavenaam: (doc.weergavenaam as string) ?? '',
      };
      setCadastral(info);
      onChange({ cadastral: info });
    } catch {
      setCadastralError('Fout bij ophalen kadastrale gegevens.');
    } finally {
      setIsCadastralLoading(false);
    }
  }

  function removeCadastral() {
    setCadastral(null);
    setCadastralError('');
    onChange({ cadastral: undefined });
  }

  // --- Map preview ---
  function updatePreview(lat: number, lon: number, z: number, layer: string) {
    const wmtsLayers: Record<string, string> = {
      brt: 'standaard',
      brt_grijs: 'grijs',
    };

    const wmtsLayer = wmtsLayers[layer];
    if (wmtsLayer) {
      const latRad = (lat * Math.PI) / 180;
      const pz = Math.max(z - 1, 10);
      const pn = Math.pow(2, pz);
      const px = Math.floor(((lon + 180) / 360) * pn);
      const py = Math.floor((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2 * pn);
      setPreviewUrl(
        `https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/${wmtsLayer}/EPSG:3857/${pz}/${px}/${py}.png`
      );
      return;
    }

    const wmsServices: Record<string, { url: string; layers: string }> = {
      luchtfoto: { url: 'https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0', layers: 'Actueel_orthoHR' },
      kadastraal: { url: 'https://service.pdok.nl/kadaster/kadastralekaart/wms/v5_0', layers: 'Kadastralekaart' },
    };

    const svc = wmsServices[layer];
    if (!svc) {
      setPreviewUrl(null);
      return;
    }

    const metersPerPx = (156543.03 * Math.cos((lat * Math.PI) / 180)) / Math.pow(2, z);
    const halfW = 200 * metersPerPx;
    const halfH = 133 * metersPerPx;
    const dlat = halfH / 111320.0;
    const dlon = halfW / (111320.0 * Math.cos((lat * Math.PI) / 180));
    const bbox = `${lat - dlat},${lon - dlon},${lat + dlat},${lon + dlon}`;

    const params = new URLSearchParams({
      SERVICE: 'WMS', VERSION: '1.3.0', REQUEST: 'GetMap',
      LAYERS: svc.layers, CRS: 'EPSG:4326', BBOX: bbox,
      WIDTH: '400', HEIGHT: '266', FORMAT: 'image/png', STYLES: '',
    });
    setPreviewUrl(`${svc.url}?${params.toString()}`);
  }

  useEffect(() => {
    if (resolvedCoords) {
      updatePreview(resolvedCoords.lat, resolvedCoords.lon, zoom, layers[0] ?? 'brt');
    }
  }, [zoom, layers, resolvedCoords]);

  function handleLayerToggle(layer: MapLayer) {
    const newLayers = layers.includes(layer)
      ? layers.filter((l) => l !== layer)
      : [...layers, layer];
    if (newLayers.length === 0) return;
    setLayers(newLayers);
    onChange({ layers: newLayers });
  }

  function handleZoomChange(value: number) {
    setZoom(value);
    onChange({ zoom: value });
  }

  function handleCaptionBlur() {
    if (caption !== (block.caption ?? '')) {
      onChange({ caption: caption || undefined });
    }
  }

  function handleWidthCommit() {
    onChange({ width_mm: widthMm });
  }

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
        <div className="rounded-md overflow-hidden border border-gray-200 bg-gray-100 relative">
          <img
            src={previewUrl}
            alt="Kaart preview"
            className="w-full h-auto"
            style={{ aspectRatio: '3/2' }}
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
          {/* Red POI marker overlay (center of preview) */}
          {resolvedCoords && (
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-full pointer-events-none">
              <svg width="28" height="40" viewBox="0 0 28 40" fill="none">
                <path d="M14 0C6.268 0 0 6.268 0 14c0 10.5 14 26 14 26s14-15.5 14-26C28 6.268 21.732 0 14 0z" fill="#DC2626" stroke="#fff" strokeWidth="2"/>
                <circle cx="14" cy="14" r="5" fill="#fff"/>
              </svg>
            </div>
          )}
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

      {/* Cadastral lookup */}
      <div className="border-t border-gray-100 pt-3">
        <label className={labelClass}>Kadastrale gegevens</label>

        {!cadastral ? (
          <div className="space-y-2">
            <button
              type="button"
              disabled={!resolvedCoords || isCadastralLoading}
              onClick={lookupCadastral}
              className={`flex items-center gap-2 rounded border px-3 py-2 text-xs font-medium transition-colors ${
                resolvedCoords && !isCadastralLoading
                  ? 'border-amber-300 bg-amber-50 text-amber-700 hover:bg-amber-100'
                  : 'border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed'
              }`}
            >
              {isCadastralLoading ? (
                <>
                  <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Ophalen…
                </>
              ) : (
                <>
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />
                  </svg>
                  Kadastrale gegevens ophalen
                </>
              )}
            </button>
            {!resolvedCoords && (
              <p className="text-[10px] text-gray-400">Selecteer eerst een adres om kadastrale gegevens op te halen.</p>
            )}
            {cadastralError && (
              <p className="text-[11px] text-red-500">{cadastralError}</p>
            )}
          </div>
        ) : (
          <div className="rounded-md border border-amber-200 bg-amber-50 p-3 space-y-1.5">
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-amber-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />
                  </svg>
                  <span className="text-sm font-bold text-amber-800 font-mono tracking-wide">
                    {cadastral.identificatie}
                  </span>
                </div>
                <div className="text-[11px] text-amber-700 pl-6 space-y-0.5">
                  <div>
                    <span className="text-amber-500">Gemeente:</span>{' '}
                    {cadastral.gemeentenaam}
                    {cadastral.gemeentecode && (
                      <span className="text-amber-400 ml-1">({cadastral.gemeentecode})</span>
                    )}
                  </div>
                  <div>
                    <span className="text-amber-500">Sectie:</span> {cadastral.sectie}
                    {' · '}
                    <span className="text-amber-500">Perceelnr:</span> {cadastral.perceelnummer}
                  </div>
                  {cadastral.grootte > 0 && (
                    <div>
                      <span className="text-amber-500">Oppervlakte:</span>{' '}
                      {cadastral.grootte.toLocaleString('nl-NL')} m²
                    </div>
                  )}
                </div>
              </div>
              <button
                type="button"
                onClick={removeCadastral}
                title="Kadastrale gegevens verwijderen"
                className="text-amber-400 hover:text-red-500 transition-colors p-1"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <p className="text-[10px] text-amber-500 pl-6">
              Wordt onder de kaartafbeelding(en) in het rapport getoond.
            </p>
          </div>
        )}
      </div>

      {/* Manual coordinates (collapsible) */}
      <ManualCoords
        lat={resolvedCoords?.lat}
        lon={resolvedCoords?.lon}
        onUpdate={(lat, lon) => {
          setResolvedCoords({ lat, lon });
          setCadastral(null);
          setCadastralError('');
          setLinkedPerceel(null);
          onChange({ center: { lat, lon }, cadastral: undefined });
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
