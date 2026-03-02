import { useState, useEffect } from 'react';
import { useReportStore } from '@/stores/reportStore';
import { TemplateSelector } from './TemplateSelector';
import type { Format, Orientation, Status } from '@/types/report';

const inputClass =
  'w-full rounded border border-gray-200 px-2 py-1.5 text-sm focus:border-blue-300 focus:ring-2 focus:ring-blue-100 outline-none';

const labelClass = 'block text-xs font-medium text-gray-500 mb-1';

const REPORT_TYPE_SUGGESTIONS = [
  'BBL-toetsingsrapportage',
  'Constructief adviesrapport',
  'Daglichttoetreding',
  'Ventilatieberekening',
  'Geluidsberekening',
];

const STATUS_OPTIONS: { value: Status; label: string }[] = [
  { value: 'CONCEPT', label: 'Concept' },
  { value: 'DEFINITIEF', label: 'Definitief' },
  { value: 'REVISIE', label: 'Revisie' },
];

export function MetadataForm() {
  const report = useReportStore((s) => s.report);
  const setMetadata = useReportStore((s) => s.setMetadata);

  // Local state for text inputs (commit on blur)
  const [local, setLocal] = useState({
    project: report.project,
    project_number: report.project_number,
    client: report.client,
    author: report.author,
    report_type: report.report_type,
    date: report.date,
    version: report.version,
  });

  // Sync local state when store changes externally (import/load)
  useEffect(() => {
    setLocal({
      project: report.project,
      project_number: report.project_number,
      client: report.client,
      author: report.author,
      report_type: report.report_type,
      date: report.date,
      version: report.version,
    });
  }, [report.project, report.project_number, report.client, report.author, report.report_type, report.date, report.version]);

  function handleLocalChange(field: keyof typeof local, value: string) {
    setLocal((prev) => ({ ...prev, [field]: value }));
  }

  function handleBlur(field: keyof typeof local) {
    if (local[field] !== report[field]) {
      setMetadata({ [field]: local[field] });
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2">
        <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.298 1.466l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 010 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.298 1.466l-1.296 2.247a1.125 1.125 0 01-1.37.49l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.298-1.466l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 010-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 01-.298-1.466l1.297-2.247a1.125 1.125 0 011.37-.49l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28z" />
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <h2 className="text-lg font-semibold text-gray-800">Rapport instellingen</h2>
      </div>

      {/* Template selector */}
      <TemplateSelector />
      <hr className="border-gray-100" />

      {/* Row 1: Project (2/3) + Project number (1/3) */}
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2">
          <label className={labelClass}>Project</label>
          <input
            type="text"
            className={inputClass}
            value={local.project}
            onChange={(e) => handleLocalChange('project', e.target.value)}
            onBlur={() => handleBlur('project')}
            placeholder="Projectnaam"
          />
        </div>
        <div>
          <label className={labelClass}>Projectnummer</label>
          <input
            type="text"
            className={inputClass}
            value={local.project_number}
            onChange={(e) => handleLocalChange('project_number', e.target.value)}
            onBlur={() => handleBlur('project_number')}
            placeholder="bijv. 2026-031"
          />
        </div>
      </div>

      {/* Row 1b: Report type */}
      <div>
        <label className={labelClass}>Rapporttype</label>
        <input
          type="text"
          list="report-type-suggestions"
          className={inputClass}
          value={local.report_type}
          onChange={(e) => handleLocalChange('report_type', e.target.value)}
          onBlur={() => handleBlur('report_type')}
          placeholder="bijv. Constructief adviesrapport"
        />
        <datalist id="report-type-suggestions">
          {REPORT_TYPE_SUGGESTIONS.map((s) => (
            <option key={s} value={s} />
          ))}
        </datalist>
      </div>

      {/* Row 2: Client (1/2) + Author (1/2) */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={labelClass}>Opdrachtgever</label>
          <input
            type="text"
            className={inputClass}
            value={local.client}
            onChange={(e) => handleLocalChange('client', e.target.value)}
            onBlur={() => handleBlur('client')}
            placeholder="Opdrachtgever"
          />
        </div>
        <div>
          <label className={labelClass}>Auteur</label>
          <input
            type="text"
            className={inputClass}
            value={local.author}
            onChange={(e) => handleLocalChange('author', e.target.value)}
            onBlur={() => handleBlur('author')}
            placeholder="Auteur"
          />
        </div>
      </div>

      {/* Row 3: Date (1/3) + Version (1/3) + Status (1/3) */}
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className={labelClass}>Datum</label>
          <input
            type="date"
            className={inputClass}
            value={local.date}
            onChange={(e) => {
              handleLocalChange('date', e.target.value);
              setMetadata({ date: e.target.value });
            }}
          />
        </div>
        <div>
          <label className={labelClass}>Versie</label>
          <input
            type="text"
            className={inputClass}
            value={local.version}
            onChange={(e) => handleLocalChange('version', e.target.value)}
            onBlur={() => handleBlur('version')}
            placeholder="1.0"
          />
        </div>
        <div>
          <label className={labelClass}>Status</label>
          <select
            className={inputClass}
            value={report.status}
            onChange={(e) => setMetadata({ status: e.target.value as Status })}
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Row 4: Format + Orientation */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={labelClass}>Formaat</label>
          <div className="flex gap-3 mt-1">
            {(['A4', 'A3'] as Format[]).map((fmt) => (
              <label key={fmt} className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="radio"
                  name="format"
                  checked={report.format === fmt}
                  onChange={() => setMetadata({ format: fmt })}
                  className="h-3.5 w-3.5 text-blue-500 focus:ring-blue-200"
                />
                <span className="text-sm text-gray-700">{fmt}</span>
              </label>
            ))}
          </div>
        </div>
        <div>
          <label className={labelClass}>Orientatie</label>
          <div className="flex gap-3 mt-1">
            {([
              { value: 'portrait' as Orientation, label: 'Staand' },
              { value: 'landscape' as Orientation, label: 'Liggend' },
            ]).map((opt) => (
              <label key={opt.value} className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="radio"
                  name="orientation"
                  checked={report.orientation === opt.value}
                  onChange={() => setMetadata({ orientation: opt.value })}
                  className="h-3.5 w-3.5 text-blue-500 focus:ring-blue-200"
                />
                <span className="text-sm text-gray-700">{opt.label}</span>
              </label>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
