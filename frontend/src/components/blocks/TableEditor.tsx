import { useState, useCallback } from 'react';
import type { TableBlock, TableStyle } from '@/types/report';

interface TableEditorProps {
  block: TableBlock & { id: string };
  onChange: (updates: Partial<TableBlock>) => void;
}

const cellClass =
  'w-full border-0 bg-transparent px-2 py-1 text-sm outline-none focus:bg-blue-50';
const labelClass = 'text-xs font-medium text-gray-500 mb-1';
const btnClass =
  'rounded border border-gray-200 px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 transition-colors';

const STYLES: { value: TableStyle; label: string }[] = [
  { value: 'default', label: 'Standaard' },
  { value: 'minimal', label: 'Minimaal' },
  { value: 'striped', label: 'Gestreept' },
];

export function TableEditor({ block, onChange }: TableEditorProps) {
  const [title, setTitle] = useState(block.title ?? '');
  const [headers, setHeaders] = useState<string[]>([...block.headers]);
  const [rows, setRows] = useState<string[][]>(
    block.rows.map((row) => row.map((cell) => String(cell ?? ''))),
  );
  const [style, setStyle] = useState<TableStyle>(block.style ?? 'default');

  const colCount = headers.length;

  const commitChanges = useCallback(
    (newHeaders: string[], newRows: string[][]) => {
      onChange({
        headers: newHeaders,
        rows: newRows,
      });
    },
    [onChange],
  );

  function handleHeaderChange(colIdx: number, value: string) {
    const newHeaders = [...headers];
    newHeaders[colIdx] = value;
    setHeaders(newHeaders);
  }

  function handleHeaderBlur() {
    commitChanges(headers, rows);
  }

  function handleCellChange(rowIdx: number, colIdx: number, value: string) {
    const newRows = rows.map((row) => [...row]);
    newRows[rowIdx]![colIdx] = value;
    setRows(newRows);
  }

  function handleCellBlur() {
    commitChanges(headers, rows);
  }

  function addColumn() {
    const newHeaders = [...headers, `Kolom ${colCount + 1}`];
    const newRows = rows.map((row) => [...row, '']);
    setHeaders(newHeaders);
    setRows(newRows);
    commitChanges(newHeaders, newRows);
  }

  function removeColumn() {
    if (colCount <= 1) return;
    const newHeaders = headers.slice(0, -1);
    const newRows = rows.map((row) => row.slice(0, -1));
    setHeaders(newHeaders);
    setRows(newRows);
    commitChanges(newHeaders, newRows);
  }

  function addRow() {
    const newRow = Array.from<string>({ length: colCount }).fill('');
    const newRows = [...rows, newRow];
    setRows(newRows);
    commitChanges(headers, newRows);
  }

  function removeRow() {
    if (rows.length <= 1) return;
    const newRows = rows.slice(0, -1);
    setRows(newRows);
    commitChanges(headers, newRows);
  }

  function handleTitleBlur() {
    if (title !== (block.title ?? '')) {
      onChange({ title: title || undefined });
    }
  }

  function handleStyleChange(newStyle: TableStyle) {
    setStyle(newStyle);
    onChange({ style: newStyle });
  }

  return (
    <div className="space-y-3">
      {/* Title + style */}
      <div className="grid grid-cols-3 gap-3">
        <div className="col-span-2">
          <label className={labelClass}>Titel</label>
          <input
            type="text"
            className="w-full rounded border border-gray-200 px-2 py-1.5 text-sm focus:border-blue-300 focus:ring-2 focus:ring-blue-100 outline-none"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onBlur={handleTitleBlur}
            placeholder="Optionele tabel titel"
          />
        </div>
        <div>
          <label className={labelClass}>Stijl</label>
          <select
            value={style}
            onChange={(e) => handleStyleChange(e.target.value as TableStyle)}
            className="w-full rounded border border-gray-200 px-2 py-1.5 text-sm focus:border-blue-300 focus:ring-2 focus:ring-blue-100 outline-none"
          >
            {STYLES.map(({ value, label }) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Table grid */}
      <div className="overflow-x-auto rounded border border-gray-200">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-gray-50">
              {headers.map((header, colIdx) => (
                <th key={colIdx} className="border-b border-r border-gray-200 last:border-r-0">
                  <input
                    type="text"
                    className={`${cellClass} font-semibold`}
                    value={header}
                    onChange={(e) => handleHeaderChange(colIdx, e.target.value)}
                    onBlur={handleHeaderBlur}
                  />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIdx) => (
              <tr key={rowIdx} className="border-b border-gray-100 last:border-b-0">
                {row.map((cell, colIdx) => (
                  <td key={colIdx} className="border-r border-gray-100 last:border-r-0">
                    <input
                      type="text"
                      className={cellClass}
                      value={cell}
                      onChange={(e) => handleCellChange(rowIdx, colIdx, e.target.value)}
                      onBlur={handleCellBlur}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        <button type="button" onClick={addRow} className={btnClass}>
          + Rij
        </button>
        <button
          type="button"
          onClick={removeRow}
          disabled={rows.length <= 1}
          className={`${btnClass} ${rows.length <= 1 ? 'opacity-40 cursor-not-allowed' : ''}`}
        >
          − Rij
        </button>
        <span className="mx-1 h-4 w-px bg-gray-200" />
        <button type="button" onClick={addColumn} className={btnClass}>
          + Kolom
        </button>
        <button
          type="button"
          onClick={removeColumn}
          disabled={colCount <= 1}
          className={`${btnClass} ${colCount <= 1 ? 'opacity-40 cursor-not-allowed' : ''}`}
        >
          − Kolom
        </button>
        <div className="flex-1" />
        <span className="text-[10px] text-gray-400">
          {colCount} kolommen &middot; {rows.length} rij{rows.length !== 1 ? 'en' : ''}
        </span>
      </div>
    </div>
  );
}
