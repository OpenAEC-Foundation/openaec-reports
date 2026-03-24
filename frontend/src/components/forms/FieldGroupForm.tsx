/**
 * Dynamisch formulier voor template-driven veldgroepen (BIC rapport).
 * Rendert scalar velden als invoervelden en tabel-groepen als spreadsheet.
 */
import { useReportStore } from '@/stores/reportStore';
import type { ScalarFieldGroup, TableFieldGroup } from '@/types/report';

// ---------- Scalar field group ----------

function ScalarFieldGroupForm({ group }: { group: ScalarFieldGroup }) {
  const flat_data = useReportStore((s) => s.report.flat_data);
  const setFlatField = useReportStore((s) => s.setFlatField);

  const groupData = (flat_data[group.key] || {}) as Record<string, string>;

  return (
    <div className="space-y-4">
      {group.fields.map((field) => {
        const value = groupData[field.field] ?? '';

        return (
          <div key={field.bind}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {field.label}
            </label>
            {field.input_type === 'textarea' ? (
              <textarea
                value={value}
                onChange={(e) => setFlatField(group.key, field.field, e.target.value)}
                rows={3}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary"
              />
            ) : field.input_type === 'number' ? (
              <input
                type="text"
                inputMode="decimal"
                value={value}
                onChange={(e) => setFlatField(group.key, field.field, e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm font-mono focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary"
              />
            ) : field.input_type === 'image' ? (
              <div className="space-y-2">
                <input
                  type="text"
                  value={value}
                  onChange={(e) => setFlatField(group.key, field.field, e.target.value)}
                  placeholder="Pad naar afbeelding of base64"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary"
                />
                {value && (
                  <div className="text-xs text-gray-400 truncate">{value.slice(0, 80)}...</div>
                )}
              </div>
            ) : (
              <input
                type="text"
                value={value}
                onChange={(e) => setFlatField(group.key, field.field, e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary"
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ---------- Table field group ----------

function TableFieldGroupForm({ group }: { group: TableFieldGroup }) {
  const flat_data = useReportStore((s) => s.report.flat_data);
  const setFlatTableRow = useReportStore((s) => s.setFlatTableRow);
  const addFlatTableRow = useReportStore((s) => s.addFlatTableRow);
  const removeFlatTableRow = useReportStore((s) => s.removeFlatTableRow);

  const rows = (flat_data[group.key] || []) as Record<string, unknown>[];

  function handleCellChange(rowIndex: number, field: string, value: string) {
    const row = { ...rows[rowIndex], [field]: value };
    setFlatTableRow(group.key, rowIndex, row);
  }

  function handleAddRow() {
    const emptyRow: Record<string, unknown> = {};
    for (const col of group.columns) {
      emptyRow[col.field] = '';
    }
    addFlatTableRow(group.key, emptyRow);
  }

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto border border-gray-200 rounded-lg">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="px-2 py-2 text-left text-xs font-semibold text-gray-500 w-8">#</th>
              {group.columns.map((col) => (
                <th
                  key={col.field}
                  className="px-2 py-2 text-left text-xs font-semibold text-gray-500"
                >
                  {col.header}
                </th>
              ))}
              <th className="px-2 py-2 w-8" />
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIdx) => (
              <tr
                key={rowIdx}
                className={`border-b border-gray-100 ${rowIdx % 2 === 1 ? 'bg-gray-50/50' : ''}`}
              >
                <td className="px-2 py-1 text-xs text-gray-400 font-mono">{rowIdx + 1}</td>
                {group.columns.map((col) => (
                  <td key={col.field} className="px-1 py-1">
                    <input
                      type="text"
                      value={String(row[col.field] ?? '')}
                      onChange={(e) => handleCellChange(rowIdx, col.field, e.target.value)}
                      className="w-full rounded border border-transparent px-1.5 py-1 text-sm hover:border-gray-200 focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary"
                    />
                  </td>
                ))}
                <td className="px-1 py-1">
                  <button
                    onClick={() => removeFlatTableRow(group.key, rowIdx)}
                    className="flex h-6 w-6 items-center justify-center rounded text-gray-300 hover:bg-red-50 hover:text-red-500"
                    title="Verwijder rij"
                  >
                    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <button
        onClick={handleAddRow}
        className="flex items-center gap-1.5 rounded-md border border-dashed border-gray-300 px-3 py-2 text-sm text-gray-500 hover:border-brand-primary hover:text-brand-primary transition-colors"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        Rij toevoegen
      </button>
    </div>
  );
}

// ---------- Main component ----------

export function FieldGroupForm({ groupKey }: { groupKey: string }) {
  const fieldGroups = useReportStore((s) => s.report.field_groups);
  const group = fieldGroups.find((g) => g.key === groupKey);

  if (!group) {
    return (
      <div className="px-6 py-8 text-center text-gray-400">
        <p className="text-sm">Veldgroep &ldquo;{groupKey}&rdquo; niet gevonden</p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="sticky top-0 z-10 border-b border-gray-200 bg-white/95 backdrop-blur px-6 py-4">
        <div className="flex items-center gap-3">
          <span className="flex h-7 w-7 items-center justify-center rounded bg-amber-100 text-sm">
            {group.type === 'table' ? (
              <svg className="h-4 w-4 text-amber-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0112 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M2.25 5.625v1.5c0 .621.504 1.125 1.125 1.125m0 0h17.25m-17.25 0h7.5c.621 0 1.125.504 1.125 1.125M3.375 8.25c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m17.25-3.75h-7.5c-.621 0-1.125.504-1.125 1.125m8.625-1.125c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125M12 10.875v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 10.875c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125M13.125 12h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125M20.625 12c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5M12 14.625v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 14.625c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125m0 0v1.5c0 .621-.504 1.125-1.125 1.125" />
              </svg>
            ) : (
              <svg className="h-4 w-4 text-amber-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
              </svg>
            )}
          </span>
          <h2 className="text-lg font-semibold text-gray-900">{group.label}</h2>
          {group.type === 'table' && (
            <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-500">
              Tabel
            </span>
          )}
        </div>
        <p className="mt-1 text-xs text-gray-400">
          Pagina: {group.page_type}
        </p>
      </div>
      <div className="px-6 py-6">
        {group.type === 'table' ? (
          <TableFieldGroupForm group={group} />
        ) : (
          <ScalarFieldGroupForm group={group} />
        )}
      </div>
    </div>
  );
}
