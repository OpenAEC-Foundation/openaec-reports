import { useState, useCallback } from 'react';
import type { SpreadsheetBlock } from '@/types/report';

interface SpreadsheetEditorProps {
  block: SpreadsheetBlock & { id: string };
  onChange: (updates: Partial<SpreadsheetBlock>) => void;
}

const cellClass =
  'w-full border-0 bg-transparent px-2 py-1 text-sm outline-none focus:bg-blue-50';
const labelClass = 'text-xs font-medium text-gray-500 mb-1';
const btnClass =
  'rounded border border-gray-200 px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 transition-colors';

export function SpreadsheetEditor({ block, onChange }: SpreadsheetEditorProps) {
  const [title, setTitle] = useState(block.title ?? '');
  const [headers, setHeaders] = useState<string[]>([...block.headers]);
  const [rows, setRows] = useState<string[][]>(
    block.rows.map((row) => row.map((cell) => String(cell ?? ''))),
  );
  const [rowHeaders, setRowHeaders] = useState<string[]>(
    block.row_headers ? [...block.row_headers] : [],
  );
  const [showGrid, setShowGrid] = useState(block.show_grid ?? true);
  const [zebra, setZebra] = useState(block.zebra ?? true);
  const [copied, setCopied] = useState(false);

  const hasRowHeaders = rowHeaders.length > 0;
  const colCount = headers.length;

  const commitChanges = useCallback(
    (newHeaders: string[], newRows: string[][], newRowHeaders: string[]) => {
      onChange({
        headers: newHeaders,
        rows: newRows,
        row_headers: newRowHeaders.length > 0 ? newRowHeaders : undefined,
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
    commitChanges(headers, rows, rowHeaders);
  }

  function handleCellChange(rowIdx: number, colIdx: number, value: string) {
    const newRows = rows.map((row) => [...row]);
    newRows[rowIdx]![colIdx] = value;
    setRows(newRows);
  }

  function handleCellBlur() {
    commitChanges(headers, rows, rowHeaders);
  }

  function handleRowHeaderChange(rowIdx: number, value: string) {
    const newRowHeaders = [...rowHeaders];
    newRowHeaders[rowIdx] = value;
    setRowHeaders(newRowHeaders);
  }

  function handleRowHeaderBlur() {
    commitChanges(headers, rows, rowHeaders);
  }

  function addColumn() {
    const newHeaders = [...headers, `Kolom ${colCount + 1}`];
    const newRows = rows.map((row) => [...row, '']);
    setHeaders(newHeaders);
    setRows(newRows);
    commitChanges(newHeaders, newRows, rowHeaders);
  }

  function removeColumn() {
    if (colCount <= 1) return;
    const newHeaders = headers.slice(0, -1);
    const newRows = rows.map((row) => row.slice(0, -1));
    setHeaders(newHeaders);
    setRows(newRows);
    commitChanges(newHeaders, newRows, rowHeaders);
  }

  function addRow() {
    const newRow = Array.from<string>({ length: colCount }).fill('');
    const newRows = [...rows, newRow];
    const newRowHeaders = hasRowHeaders ? [...rowHeaders, ''] : rowHeaders;
    setRows(newRows);
    setRowHeaders(newRowHeaders);
    commitChanges(headers, newRows, newRowHeaders);
  }

  function removeRow() {
    if (rows.length <= 1) return;
    const newRows = rows.slice(0, -1);
    const newRowHeaders = hasRowHeaders ? rowHeaders.slice(0, -1) : rowHeaders;
    setRows(newRows);
    setRowHeaders(newRowHeaders);
    commitChanges(headers, newRows, newRowHeaders);
  }

  function toggleRowHeaders() {
    if (hasRowHeaders) {
      setRowHeaders([]);
      commitChanges(headers, rows, []);
    } else {
      const newRowHeaders = rows.map(() => '');
      setRowHeaders(newRowHeaders);
      commitChanges(headers, rows, newRowHeaders);
    }
  }

  function handleTitleBlur() {
    if (title !== (block.title ?? '')) {
      onChange({ title: title || undefined });
    }
  }

  function handleShowGridChange(value: boolean) {
    setShowGrid(value);
    onChange({ show_grid: value });
  }

  function handleZebraChange(value: boolean) {
    setZebra(value);
    onChange({ zebra: value });
  }

  function handleCopy() {
    const headerRow = (hasRowHeaders ? [''] : []).concat(headers).join('\t');
    const dataRows = rows.map((row, rowIdx) => {
      const rowHeader = hasRowHeaders ? [rowHeaders[rowIdx] ?? ''] : [];
      return rowHeader.concat(row).join('\t');
    });
    const tsv = [headerRow, ...dataRows].join('\n');
    navigator.clipboard.writeText(tsv).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handlePaste(e: React.ClipboardEvent<HTMLDivElement>) {
    // Only handle paste when the zone itself (not an input) is the target
    const target = e.target as HTMLElement;
    if (target.tagName === 'INPUT') return;
    e.preventDefault();
    const text = e.clipboardData.getData('text/plain');
    const lines = text
      .trim()
      .split('\n')
      .map((line) => line.split('\t'));
    if (lines.length === 0) return;
    const newHeaders = lines[0]!.map((h) => h.trim());
    const newRows = lines.slice(1).map((row) =>
      // Pad or trim to match header count
      Array.from({ length: newHeaders.length }, (_, i) => row[i]?.trim() ?? ''),
    );
    setHeaders(newHeaders);
    setRows(newRows.length > 0 ? newRows : [Array.from({ length: newHeaders.length }).fill('') as string[]]);
    setRowHeaders([]);
    commitChanges(
      newHeaders,
      newRows.length > 0 ? newRows : [Array.from({ length: newHeaders.length }).fill('') as string[]],
      [],
    );
  }

  return (
    <div className="space-y-3" onPaste={handlePaste}>
      {/* Title + options */}
      <div className="grid grid-cols-3 gap-3">
        <div className="col-span-2">
          <label className={labelClass}>Titel</label>
          <input
            type="text"
            className="w-full rounded border border-gray-200 px-2 py-1.5 text-sm focus:border-blue-300 focus:ring-2 focus:ring-blue-100 outline-none"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onBlur={handleTitleBlur}
            placeholder="Optionele spreadsheet titel"
          />
        </div>
        <div className="flex flex-col gap-2 justify-end pb-1">
          <label className="flex items-center gap-2 text-xs text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={showGrid}
              onChange={(e) => handleShowGridChange(e.target.checked)}
              className="rounded border-gray-300"
            />
            Rasterlijnen
          </label>
          <label className="flex items-center gap-2 text-xs text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={zebra}
              onChange={(e) => handleZebraChange(e.target.checked)}
              className="rounded border-gray-300"
            />
            Zebra-rijen
          </label>
        </div>
      </div>

      {/* Spreadsheet grid */}
      <div className="overflow-x-auto rounded border border-gray-200">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-gray-50">
              {hasRowHeaders && (
                <th className="border-b border-r border-gray-200 w-28" />
              )}
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
              <tr
                key={rowIdx}
                className={`border-b border-gray-100 last:border-b-0 ${
                  zebra && rowIdx % 2 === 1 ? 'bg-gray-50/50' : ''
                }`}
              >
                {hasRowHeaders && (
                  <td className="border-r border-gray-200 bg-gray-50">
                    <input
                      type="text"
                      className={`${cellClass} font-medium`}
                      value={rowHeaders[rowIdx] ?? ''}
                      onChange={(e) => handleRowHeaderChange(rowIdx, e.target.value)}
                      onBlur={handleRowHeaderBlur}
                      placeholder={`Rij ${rowIdx + 1}`}
                    />
                  </td>
                )}
                {row.map((cell, colIdx) => (
                  <td
                    key={colIdx}
                    className={`border-r border-gray-100 last:border-r-0 ${showGrid ? 'border-gray-200' : ''}`}
                  >
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

      {/* Actions row */}
      <div className="flex items-center gap-2 flex-wrap">
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
        <span className="mx-1 h-4 w-px bg-gray-200" />
        <button
          type="button"
          onClick={toggleRowHeaders}
          className={`${btnClass} ${hasRowHeaders ? 'bg-blue-50 border-blue-200 text-blue-700' : ''}`}
        >
          {hasRowHeaders ? 'Rijkoppen verbergen' : 'Rijkoppen tonen'}
        </button>
        <div className="flex-1" />
        <button
          type="button"
          onClick={handleCopy}
          className={`${btnClass} ${copied ? 'bg-green-50 border-green-300 text-green-700' : ''}`}
          title="Kopieer als TSV (plak in LibreOffice Calc)"
        >
          {copied ? 'Gekopieerd!' : 'Kopieer TSV'}
        </button>
        <span className="text-[10px] text-gray-400">
          {colCount} kolommen &middot; {rows.length} rij{rows.length !== 1 ? 'en' : ''}
        </span>
      </div>

      {/* Paste hint */}
      <p className="text-[10px] text-gray-400">
        Tip: plak data uit LibreOffice Calc direct op dit blok (Ctrl+V)
      </p>
    </div>
  );
}
