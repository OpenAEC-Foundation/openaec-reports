import { useState } from 'react';
import { useApiStore } from '@/stores/apiStore';
import { useReportStore, reportHasContent } from '@/stores/reportStore';

const inputClass =
  'w-full rounded border border-oaec-border px-2 py-1.5 text-sm focus:border-oaec-accent focus:ring-2 focus:ring-oaec-accent/20 outline-none';

const labelClass = 'block text-xs font-medium text-oaec-text-muted mb-1';

export function TemplateSelector() {
  const connected = useApiStore((s) => s.connected);
  const templates = useApiStore((s) => s.templates);
  const loadScaffold = useApiStore((s) => s.loadScaffold);
  const currentTemplate = useReportStore((s) => s.report.template);

  const [loading, setLoading] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [pendingTemplate, setPendingTemplate] = useState<string | null>(null);

  async function handleChange(value: string) {
    if (!connected || value === currentTemplate) return;

    const report = useReportStore.getState().report;
    if (reportHasContent(report)) {
      setPendingTemplate(value);
      setShowConfirm(true);
    } else {
      setLoading(true);
      await loadScaffold(value);
      setLoading(false);
    }
  }

  async function handleConfirm() {
    if (!pendingTemplate) return;
    setShowConfirm(false);
    setLoading(true);
    await loadScaffold(pendingTemplate);
    setLoading(false);
    setPendingTemplate(null);
  }

  function handleCancel() {
    setShowConfirm(false);
    setPendingTemplate(null);
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
            <p className="mt-1 text-xs text-oaec-text-faint">
              Backend niet beschikbaar — templates laden niet mogelijk
            </p>
          )}
        </div>
      )}

      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div className="bg-oaec-bg-lighter rounded-lg shadow-xl p-6 max-w-sm mx-4">
            <div className="flex items-center gap-3 mb-3">
              <svg className="h-6 w-6 text-oaec-accent flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
              </svg>
              <h3 className="text-sm font-semibold text-oaec-text">Template wijzigen</h3>
            </div>
            <p className="text-sm text-oaec-text-secondary mb-4">
              Template wijzigen wist je huidige rapport inclusief alle secties en instellingen. Wil je doorgaan?
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={handleCancel}
                className="px-3 py-1.5 text-sm text-oaec-text-secondary border border-oaec-border rounded hover:bg-oaec-bg"
              >
                Annuleren
              </button>
              <button
                onClick={handleConfirm}
                className="px-3 py-1.5 text-sm text-oaec-accent-text bg-oaec-danger-soft0 rounded hover:bg-oaec-danger"
              >
                Doorgaan
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Spinner() {
  return (
    <svg className="h-4 w-4 animate-spin text-oaec-accent" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}
