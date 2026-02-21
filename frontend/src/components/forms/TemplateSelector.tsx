import { useState } from 'react';
import { useApiStore } from '@/stores/apiStore';
import { useReportStore } from '@/stores/reportStore';

const inputClass =
  'w-full rounded border border-gray-200 px-2 py-1.5 text-sm focus:border-blue-300 focus:ring-2 focus:ring-blue-100 outline-none';

const labelClass = 'block text-xs font-medium text-gray-500 mb-1';

export function TemplateSelector() {
  const connected = useApiStore((s) => s.connected);
  const templates = useApiStore((s) => s.templates);
  const loadScaffold = useApiStore((s) => s.loadScaffold);
  const currentTemplate = useReportStore((s) => s.report.template);

  const [loading, setLoading] = useState(false);

  async function handleChange(value: string) {
    if (!connected || value === currentTemplate) return;
    setLoading(true);
    await loadScaffold(value);
    setLoading(false);
  }

  return (
    <div>
      <label className={labelClass}>Template</label>
      {connected && templates.length > 0 ? (
        <div className="relative">
          <select
            className={inputClass}
            value={currentTemplate}
            onChange={(e) => handleChange(e.target.value)}
            disabled={loading}
          >
            {templates.map((t) => (
              <option key={t.name} value={t.name}>
                {t.name} ({t.report_type})
              </option>
            ))}
          </select>
          {loading && (
            <div className="absolute right-2 top-1/2 -translate-y-1/2">
              <Spinner />
            </div>
          )}
        </div>
      ) : (
        <div>
          <input
            type="text"
            className={inputClass}
            value={currentTemplate}
            readOnly
            placeholder="Template"
          />
          {!connected && (
            <p className="mt-1 text-xs text-gray-400">
              Backend niet beschikbaar — templates laden niet mogelijk
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function Spinner() {
  return (
    <svg className="h-4 w-4 animate-spin text-blue-500" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}
