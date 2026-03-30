import { useState, useEffect } from 'react';
import { useReportStore } from '@/stores/reportStore';
import { ToggleSwitch } from './ToggleSwitch';
import type { TocConfig } from '@/types/report';

const inputClass =
  'w-full rounded border border-oaec-border px-2 py-1.5 text-sm focus:border-oaec-accent focus:ring-2 focus:ring-oaec-accent/20 outline-none';

const labelClass = 'block text-xs font-medium text-oaec-text-muted mb-1';

export function OptionsPanel() {
  const toc = useReportStore((s) => s.report.toc);
  const backcover = useReportStore((s) => s.report.backcover);
  const setToc = useReportStore((s) => s.setToc);
  const setBackcover = useReportStore((s) => s.setBackcover);

  const [tocTitle, setTocTitle] = useState(toc.title ?? 'Inhoudsopgave');

  // Bug 1 fix: sync local state when store changes externally
  useEffect(() => {
    setTocTitle(toc.title ?? 'Inhoudsopgave');
  }, [toc.title]);

  function updateToc(updates: Partial<TocConfig>) {
    setToc({ ...toc, ...updates });
  }

  function handleTocTitleBlur() {
    if (tocTitle !== (toc.title ?? 'Inhoudsopgave')) {
      updateToc({ title: tocTitle });
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* TOC settings */}
      <div>
        <div className="flex items-center justify-between border-b border-oaec-border-subtle pb-2 mb-4">
          <h3 className="text-sm font-semibold text-oaec-text-secondary">Inhoudsopgave</h3>
          <ToggleSwitch
            checked={toc.enabled !== false}
            onChange={() => updateToc({ enabled: !(toc.enabled !== false) })}
            label="Tonen"
          />
        </div>

        {toc.enabled !== false && (
          <div className="space-y-4 pl-1">
            <div>
              <label className={labelClass}>Titel</label>
              <input
                type="text"
                className={inputClass}
                value={tocTitle}
                onChange={(e) => setTocTitle(e.target.value)}
                onBlur={handleTocTitleBlur}
                placeholder="Inhoudsopgave"
              />
            </div>
            <div>
              <label className={labelClass}>Maximum diepte</label>
              <select
                className={inputClass}
                value={toc.max_depth ?? 3}
                onChange={(e) => updateToc({ max_depth: Number(e.target.value) })}
              >
                <option value={1}>1 niveau (alleen H1)</option>
                <option value={2}>2 niveaus (H1 + H2)</option>
                <option value={3}>3 niveaus (H1 + H2 + H3)</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Backcover */}
      <div>
        <div className="flex items-center justify-between border-b border-oaec-border-subtle pb-2">
          <h3 className="text-sm font-semibold text-oaec-text-secondary">Achterblad</h3>
          <ToggleSwitch
            checked={backcover.enabled !== false}
            onChange={() =>
              setBackcover({ ...backcover, enabled: !(backcover.enabled !== false) })
            }
            label="Tonen"
          />
        </div>
      </div>
    </div>
  );
}
