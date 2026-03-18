import { useState, useCallback, useRef, useEffect } from 'react';
import type { SpreadsheetBlock, CellStyle, MergedCell } from '@/types/report';

interface SpreadsheetEditorProps {
  block: SpreadsheetBlock & { id: string };
  onChange: (updates: Partial<SpreadsheetBlock>) => void;
}

const btnClass =
  'rounded border border-gray-200 px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 transition-colors';
const btnActiveClass =
  'rounded border border-blue-300 px-2 py-1 text-xs text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors';

type Selection = { row: number; col: number };
type SelectionRange = {
  startRow: number;
  startCol: number;
  endRow: number;
  endCol: number;
};

function normalizeRange(r: SelectionRange) {
  return {
    r1: Math.min(r.startRow, r.endRow),
    c1: Math.min(r.startCol, r.endCol),
    r2: Math.max(r.startRow, r.endRow),
    c2: Math.max(r.startCol, r.endCol),
  };
}

function isInRange(row: number, col: number, range: SelectionRange | null) {
  if (!range) return false;
  const { r1, c1, r2, c2 } = normalizeRange(range);
  return row >= r1 && row <= r2 && col >= c1 && col <= c2;
}

/** Check of een cel verborgen is door een merge. */
function isMergedHidden(
  row: number,
  col: number,
  merges: MergedCell[],
): boolean {
  for (const m of merges) {
    if (
      row >= m.row &&
      row < m.row + m.rowspan &&
      col >= m.col &&
      col < m.col + m.colspan &&
      !(row === m.row && col === m.col)
    ) {
      return true;
    }
  }
  return false;
}

/** Haal merge info op voor een ankercel. */
function getMergeAt(
  row: number,
  col: number,
  merges: MergedCell[],
): MergedCell | null {
  return merges.find((m) => m.row === row && m.col === col) ?? null;
}

const COLORS = [
  '#ffffff', '#f3f4f6', '#fef3c7', '#d1fae5',
  '#dbeafe', '#ede9fe', '#fce7f3', '#fee2e2',
  '#40124A', '#38BDA0',
];

export function SpreadsheetEditor({ block, onChange }: SpreadsheetEditorProps) {
  const [title, setTitle] = useState(block.title ?? '');
  const [headers, setHeaders] = useState<string[]>([...block.headers]);
  const [rows, setRows] = useState<string[][]>(
    block.rows.map((row) => row.map((cell) => String(cell ?? ''))),
  );
  const [colWidths, setColWidths] = useState<number[]>(
    block.column_widths ?? block.headers.map(() => 34),
  );
  const [rowHeights, setRowHeights] = useState<number[]>(
    block.row_heights ?? block.rows.map(() => block.default_row_height ?? 7),
  );
  const [mergedCells, setMergedCells] = useState<MergedCell[]>(
    block.merged_cells ?? [],
  );
  const [cellStyles, setCellStyles] = useState<Record<string, CellStyle>>(
    block.cell_styles ?? {},
  );
  const [showGrid, setShowGrid] = useState(block.show_grid ?? true);
  const [activeCell, setActiveCell] = useState<Selection | null>(null);
  const [selRange, setSelRange] = useState<SelectionRange | null>(null);
  const [editingCell, setEditingCell] = useState<Selection | null>(null);
  const [copied, setCopied] = useState(false);
  const [showColorPicker, setShowColorPicker] = useState(false);
  const [resizingCol, setResizingCol] = useState<number | null>(null);
  const [resizingRow, setResizingRow] = useState<number | null>(null);
  const gridRef = useRef<HTMLTableElement>(null);
  const resizeStartX = useRef(0);
  const resizeStartY = useRef(0);
  const resizeStartSize = useRef(0);

  const colCount = headers.length;
  const rowCount = rows.length;

  // Commit all data to parent
  const commit = useCallback(
    (
      h: string[],
      r: string[][],
      cw: number[],
      rh: number[],
      mc: MergedCell[],
      cs: Record<string, CellStyle>,
    ) => {
      onChange({
        headers: h,
        rows: r,
        column_widths: cw,
        row_heights: rh,
        merged_cells: mc.length > 0 ? mc : undefined,
        cell_styles: Object.keys(cs).length > 0 ? cs : undefined,
      });
    },
    [onChange],
  );

  // --- Cell editing ---
  function setCellValue(row: number, col: number, value: string) {
    const newRows = rows.map((r) => [...r]);
    // Expand row if needed
    while (newRows.length <= row) newRows.push(Array(colCount).fill(''));
    while ((newRows[row]?.length ?? 0) <= col) newRows[row]!.push('');
    newRows[row]![col] = value;
    setRows(newRows);
  }

  function commitAll() {
    commit(headers, rows, colWidths, rowHeights, mergedCells, cellStyles);
  }

  // --- Selection ---
  function handleCellMouseDown(row: number, col: number, e: React.MouseEvent) {
    if (e.shiftKey && activeCell) {
      setSelRange({
        startRow: activeCell.row,
        startCol: activeCell.col,
        endRow: row,
        endCol: col,
      });
    } else {
      setActiveCell({ row, col });
      setSelRange({ startRow: row, startCol: col, endRow: row, endCol: col });
    }
    // Stop editing other cell
    if (editingCell && (editingCell.row !== row || editingCell.col !== col)) {
      setEditingCell(null);
      commitAll();
    }
  }

  function handleCellDoubleClick(row: number, col: number) {
    setEditingCell({ row, col });
  }

  // --- Keyboard ---
  function handleKeyDown(e: React.KeyboardEvent) {
    if (!activeCell) return;
    const { row, col } = activeCell;

    if (e.key === 'Tab') {
      e.preventDefault();
      const nextCol = e.shiftKey ? col - 1 : col + 1;
      if (nextCol >= 0 && nextCol < colCount) {
        setActiveCell({ row, col: nextCol });
        setSelRange({ startRow: row, startCol: nextCol, endRow: row, endCol: nextCol });
      }
      if (editingCell) {
        setEditingCell(null);
        commitAll();
      }
      return;
    }
    if (e.key === 'Enter') {
      e.preventDefault();
      if (editingCell) {
        setEditingCell(null);
        commitAll();
        const nextRow = e.shiftKey ? row - 1 : row + 1;
        if (nextRow >= 0 && nextRow < rowCount) {
          setActiveCell({ row: nextRow, col });
          setSelRange({ startRow: nextRow, startCol: col, endRow: nextRow, endCol: col });
        }
      } else {
        setEditingCell({ row, col });
      }
      return;
    }
    if (e.key === 'Escape') {
      setEditingCell(null);
      commitAll();
      return;
    }
    if (e.key === 'Delete' || e.key === 'Backspace') {
      if (!editingCell && selRange) {
        const { r1, c1, r2, c2 } = normalizeRange(selRange);
        const newRows = rows.map((r) => [...r]);
        for (let ri = r1; ri <= r2; ri++) {
          for (let ci = c1; ci <= c2; ci++) {
            if (newRows[ri]) newRows[ri]![ci] = '';
          }
        }
        setRows(newRows);
        commit(headers, newRows, colWidths, rowHeights, mergedCells, cellStyles);
        return;
      }
    }

    // Arrow navigation when not editing
    if (!editingCell) {
      const arrows: Record<string, [number, number]> = {
        ArrowUp: [-1, 0],
        ArrowDown: [1, 0],
        ArrowLeft: [0, -1],
        ArrowRight: [0, 1],
      };
      const dir = arrows[e.key];
      if (dir) {
        e.preventDefault();
        const nr = Math.max(0, Math.min(rowCount - 1, row + dir[0]));
        const nc = Math.max(0, Math.min(colCount - 1, col + dir[1]));
        setActiveCell({ row: nr, col: nc });
        if (e.shiftKey && selRange) {
          setSelRange({ ...selRange, endRow: nr, endCol: nc });
        } else {
          setSelRange({ startRow: nr, startCol: nc, endRow: nr, endCol: nc });
        }
        return;
      }

      // Start editing on any printable character
      if (e.key.length === 1 && !e.ctrlKey && !e.metaKey) {
        setCellValue(row, col, '');
        setEditingCell({ row, col });
        // Don't prevent default — let the character appear in the input
      }
    }
  }

  // --- Paste ---
  function handlePaste(e: React.ClipboardEvent) {
    const target = e.target as HTMLElement;
    if (target.tagName === 'INPUT' && editingCell) return;
    e.preventDefault();
    const text = e.clipboardData.getData('text/plain');
    const lines = text
      .trim()
      .split('\n')
      .map((line) => line.split('\t'));
    if (lines.length === 0) return;

    const startRow = activeCell?.row ?? 0;
    const startCol = activeCell?.col ?? 0;

    const newRows = rows.map((r) => [...r]);
    const newHeaders = [...headers];
    const newColWidths = [...colWidths];
    const newRowHeights = [...rowHeights];

    // Expand grid if needed
    const neededCols = startCol + (lines[0]?.length ?? 0);
    while (newHeaders.length < neededCols) {
      const idx = newHeaders.length + 1;
      newHeaders.push(`Kolom ${idx}`);
      newColWidths.push(34);
      newRows.forEach((r) => r.push(''));
    }
    const neededRows = startRow + lines.length;
    while (newRows.length < neededRows) {
      newRows.push(Array(newHeaders.length).fill(''));
      newRowHeights.push(block.default_row_height ?? 7);
    }

    for (let ri = 0; ri < lines.length; ri++) {
      for (let ci = 0; ci < (lines[ri]?.length ?? 0); ci++) {
        const tr = startRow + ri;
        const tc = startCol + ci;
        if (tr < newRows.length && tc < newHeaders.length) {
          newRows[tr]![tc] = lines[ri]![ci]?.trim() ?? '';
        }
      }
    }

    setHeaders(newHeaders);
    setRows(newRows);
    setColWidths(newColWidths);
    setRowHeights(newRowHeights);
    commit(newHeaders, newRows, newColWidths, newRowHeights, mergedCells, cellStyles);
  }

  // --- Copy ---
  function handleCopy() {
    const r1 = 0, c1 = 0, r2 = rowCount - 1, c2 = colCount - 1;
    const headerLine = headers.slice(c1, c2 + 1).join('\t');
    const dataLines = rows
      .slice(r1, r2 + 1)
      .map((row) => row.slice(c1, c2 + 1).join('\t'));
    const tsv = [headerLine, ...dataLines].join('\n');
    navigator.clipboard.writeText(tsv).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  // --- Column resize ---
  function startColResize(colIdx: number, e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    setResizingCol(colIdx);
    resizeStartX.current = e.clientX;
    resizeStartSize.current = colWidths[colIdx] ?? 34;
  }

  useEffect(() => {
    if (resizingCol === null && resizingRow === null) return;

    function onMouseMove(e: MouseEvent) {
      if (resizingCol !== null) {
        const delta = (e.clientX - resizeStartX.current) / 2.83; // px → mm approx
        const newWidth = Math.max(15, resizeStartSize.current + delta);
        const newWidths = [...colWidths];
        newWidths[resizingCol] = Math.round(newWidth);
        setColWidths(newWidths);
      }
      if (resizingRow !== null) {
        const delta = (e.clientY - resizeStartY.current) / 2.83;
        const newHeight = Math.max(5, resizeStartSize.current + delta);
        const newHeights = [...rowHeights];
        newHeights[resizingRow] = Math.round(newHeight);
        setRowHeights(newHeights);
      }
    }

    function onMouseUp() {
      setResizingCol(null);
      setResizingRow(null);
      commit(headers, rows, colWidths, rowHeights, mergedCells, cellStyles);
    }

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
    return () => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    };
  });

  // --- Row resize ---
  function startRowResize(rowIdx: number, e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    setResizingRow(rowIdx);
    resizeStartY.current = e.clientY;
    resizeStartSize.current = rowHeights[rowIdx] ?? 7;
  }

  // --- Row/Column add/remove ---
  function addRow() {
    const newRows = [...rows, Array(colCount).fill('')];
    const newHeights = [...rowHeights, block.default_row_height ?? 7];
    setRows(newRows);
    setRowHeights(newHeights);
    commit(headers, newRows, colWidths, newHeights, mergedCells, cellStyles);
  }

  function removeRow() {
    if (rowCount <= 1) return;
    const newRows = rows.slice(0, -1);
    const newHeights = rowHeights.slice(0, -1);
    setRows(newRows);
    setRowHeights(newHeights);
    // Clean up merges and styles that reference removed rows
    const newMerges = mergedCells.filter((m) => m.row + m.rowspan <= newRows.length);
    const newStyles = filterStyles(cellStyles, newRows.length, colCount);
    setMergedCells(newMerges);
    setCellStyles(newStyles);
    commit(headers, newRows, colWidths, newHeights, newMerges, newStyles);
  }

  function addColumn() {
    const newHeaders = [...headers, `Kolom ${colCount + 1}`];
    const newRows = rows.map((r) => [...r, '']);
    const newWidths = [...colWidths, 34];
    setHeaders(newHeaders);
    setRows(newRows);
    setColWidths(newWidths);
    commit(newHeaders, newRows, newWidths, rowHeights, mergedCells, cellStyles);
  }

  function removeColumn() {
    if (colCount <= 1) return;
    const newHeaders = headers.slice(0, -1);
    const newRows = rows.map((r) => r.slice(0, -1));
    const newWidths = colWidths.slice(0, -1);
    const newMerges = mergedCells.filter((m) => m.col + m.colspan <= newHeaders.length);
    const newStyles = filterStyles(cellStyles, rowCount, newHeaders.length);
    setHeaders(newHeaders);
    setRows(newRows);
    setColWidths(newWidths);
    setMergedCells(newMerges);
    setCellStyles(newStyles);
    commit(newHeaders, newRows, newWidths, rowHeights, newMerges, newStyles);
  }

  // --- Cell styling ---
  function getSelectionStyle(): CellStyle {
    if (!activeCell) return {};
    return cellStyles[`${activeCell.row},${activeCell.col}`] ?? {};
  }

  function applyStyleToSelection(updates: Partial<CellStyle>) {
    if (!selRange) return;
    const { r1, c1, r2, c2 } = normalizeRange(selRange);
    const newStyles = { ...cellStyles };
    for (let r = r1; r <= r2; r++) {
      for (let c = c1; c <= c2; c++) {
        const key = `${r},${c}`;
        const existing = newStyles[key] ?? {};
        const merged = { ...existing, ...updates };
        // Remove falsy values
        const cleaned: CellStyle = {};
        if (merged.bold) cleaned.bold = true;
        if (merged.italic) cleaned.italic = true;
        if (merged.align && merged.align !== 'left') cleaned.align = merged.align;
        if (merged.bg_color && merged.bg_color !== '#ffffff') cleaned.bg_color = merged.bg_color;
        if (merged.text_color) cleaned.text_color = merged.text_color;
        if (merged.font_size) cleaned.font_size = merged.font_size;
        if (Object.keys(cleaned).length > 0) {
          newStyles[key] = cleaned;
        } else {
          delete newStyles[key];
        }
      }
    }
    setCellStyles(newStyles);
    commit(headers, rows, colWidths, rowHeights, mergedCells, newStyles);
  }

  function toggleBold() {
    const current = getSelectionStyle();
    applyStyleToSelection({ bold: !current.bold });
  }

  function toggleItalic() {
    const current = getSelectionStyle();
    applyStyleToSelection({ italic: !current.italic });
  }

  function setAlignment(align: 'left' | 'center' | 'right') {
    applyStyleToSelection({ align });
  }

  function setBgColor(color: string) {
    applyStyleToSelection({ bg_color: color });
    setShowColorPicker(false);
  }

  // --- Merge ---
  function mergeCells() {
    if (!selRange) return;
    const { r1, c1, r2, c2 } = normalizeRange(selRange);
    if (r1 === r2 && c1 === c2) return; // Single cell, nothing to merge

    // Remove existing merges in this area
    const newMerges = mergedCells.filter(
      (m) =>
        m.row + m.rowspan <= r1 ||
        m.row > r2 ||
        m.col + m.colspan <= c1 ||
        m.col > c2,
    );
    newMerges.push({
      row: r1,
      col: c1,
      rowspan: r2 - r1 + 1,
      colspan: c2 - c1 + 1,
    });
    setMergedCells(newMerges);
    commit(headers, rows, colWidths, rowHeights, newMerges, cellStyles);
  }

  function unmergeCells() {
    if (!activeCell) return;
    const { row, col } = activeCell;
    const newMerges = mergedCells.filter(
      (m) => !(m.row === row && m.col === col),
    );
    setMergedCells(newMerges);
    commit(headers, rows, colWidths, rowHeights, newMerges, cellStyles);
  }

  const activeMerge = activeCell
    ? getMergeAt(activeCell.row, activeCell.col, mergedCells)
    : null;

  const selStyle = getSelectionStyle();
  const hasMultiSelection = selRange
    ? (() => {
        const { r1, c1, r2, c2 } = normalizeRange(selRange);
        return r1 !== r2 || c1 !== c2;
      })()
    : false;

  return (
    <div
      className="space-y-2"
      onPaste={handlePaste}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      style={{ outline: 'none' }}
    >
      {/* Title */}
      <input
        type="text"
        className="w-full rounded border border-gray-200 px-2 py-1.5 text-sm focus:border-blue-300 focus:ring-2 focus:ring-blue-100 outline-none"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        onBlur={() => {
          if (title !== (block.title ?? '')) onChange({ title: title || undefined });
        }}
        placeholder="Titel (optioneel)"
      />

      {/* Toolbar */}
      <div className="flex items-center gap-1 flex-wrap border border-gray-200 rounded px-2 py-1 bg-gray-50">
        <button
          type="button"
          onClick={toggleBold}
          className={selStyle.bold ? btnActiveClass : btnClass}
          title="Vet (Ctrl+B)"
        >
          <strong>B</strong>
        </button>
        <button
          type="button"
          onClick={toggleItalic}
          className={selStyle.italic ? btnActiveClass : btnClass}
          title="Cursief"
        >
          <em>I</em>
        </button>
        <span className="mx-1 h-4 w-px bg-gray-300" />
        <button
          type="button"
          onClick={() => setAlignment('left')}
          className={(!selStyle.align || selStyle.align === 'left') ? btnActiveClass : btnClass}
          title="Links uitlijnen"
        >
          ≡
        </button>
        <button
          type="button"
          onClick={() => setAlignment('center')}
          className={selStyle.align === 'center' ? btnActiveClass : btnClass}
          title="Centreren"
        >
          ≡
        </button>
        <button
          type="button"
          onClick={() => setAlignment('right')}
          className={selStyle.align === 'right' ? btnActiveClass : btnClass}
          title="Rechts uitlijnen"
        >
          ≡
        </button>
        <span className="mx-1 h-4 w-px bg-gray-300" />
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowColorPicker(!showColorPicker)}
            className={btnClass}
            title="Achtergrondkleur"
          >
            <span
              className="inline-block w-4 h-3 rounded border border-gray-300"
              style={{ backgroundColor: selStyle.bg_color ?? '#ffffff' }}
            />
          </button>
          {showColorPicker && (
            <div className="absolute top-full left-0 mt-1 z-10 bg-white border border-gray-200 rounded shadow-lg p-2 grid grid-cols-5 gap-1">
              {COLORS.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setBgColor(c)}
                  className="w-6 h-6 rounded border border-gray-200 hover:ring-2 hover:ring-blue-300"
                  style={{ backgroundColor: c }}
                />
              ))}
            </div>
          )}
        </div>
        <span className="mx-1 h-4 w-px bg-gray-300" />
        {hasMultiSelection && !activeMerge && (
          <button type="button" onClick={mergeCells} className={btnClass} title="Cellen samenvoegen">
            Samenvoegen
          </button>
        )}
        {activeMerge && (
          <button type="button" onClick={unmergeCells} className={btnClass} title="Samenvoegen opheffen">
            Splitsen
          </button>
        )}
        <label className="flex items-center gap-1.5 text-xs text-gray-600 cursor-pointer ml-2">
          <input
            type="checkbox"
            checked={showGrid}
            onChange={(e) => {
              setShowGrid(e.target.checked);
              onChange({ show_grid: e.target.checked });
            }}
            className="rounded border-gray-300"
          />
          Raster
        </label>
      </div>

      {/* Grid */}
      <div className="overflow-x-auto border border-gray-300 rounded">
        <table
          ref={gridRef}
          className="border-collapse"
          style={{ tableLayout: 'fixed' }}
        >
          <colgroup>
            {/* Row number column */}
            <col style={{ width: '28px' }} />
            {headers.map((_, ci) => (
              <col key={ci} style={{ width: `${(colWidths[ci] ?? 34) * 2.83}px` }} />
            ))}
          </colgroup>
          {/* Column header row */}
          <thead>
            <tr className="bg-gray-100">
              <th className="border-r border-b border-gray-300 text-[10px] text-gray-400 w-7" />
              {headers.map((header, ci) => (
                <th
                  key={ci}
                  className="relative border-r border-b border-gray-300 p-0 group"
                >
                  <input
                    type="text"
                    className="w-full bg-transparent px-1.5 py-1 text-xs font-semibold text-gray-700 outline-none text-center"
                    value={header}
                    onChange={(e) => {
                      const nh = [...headers];
                      nh[ci] = e.target.value;
                      setHeaders(nh);
                    }}
                    onBlur={commitAll}
                  />
                  {/* Column resize handle */}
                  <div
                    className="absolute right-0 top-0 w-1.5 h-full cursor-col-resize hover:bg-blue-400 opacity-0 group-hover:opacity-50"
                    onMouseDown={(e) => startColResize(ci, e)}
                  />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, ri) => (
              <tr key={ri} className="relative group/row">
                {/* Row number */}
                <td
                  className="border-r border-b border-gray-200 text-[10px] text-gray-400 text-center bg-gray-50 relative select-none"
                  style={{ height: `${(rowHeights[ri] ?? 7) * 2.83}px` }}
                >
                  {ri + 1}
                  {/* Row resize handle */}
                  <div
                    className="absolute left-0 bottom-0 w-full h-1 cursor-row-resize hover:bg-blue-400 opacity-0 group-hover/row:opacity-50"
                    onMouseDown={(e) => startRowResize(ri, e)}
                  />
                </td>
                {row.map((cell, ci) => {
                  if (isMergedHidden(ri, ci, mergedCells)) return null;
                  const merge = getMergeAt(ri, ci, mergedCells);
                  const isActive =
                    activeCell?.row === ri && activeCell?.col === ci;
                  const isSelected = isInRange(ri, ci, selRange);
                  const cs = cellStyles[`${ri},${ci}`];

                  return (
                    <td
                      key={ci}
                      rowSpan={merge?.rowspan}
                      colSpan={merge?.colspan}
                      className={[
                        'p-0 relative',
                        showGrid ? 'border border-gray-200' : 'border border-transparent',
                        isActive ? 'ring-2 ring-blue-500 z-10' : '',
                        isSelected && !isActive ? 'bg-blue-50' : '',
                      ].join(' ')}
                      style={{
                        backgroundColor: cs?.bg_color ?? undefined,
                        color: cs?.text_color ?? undefined,
                        minHeight: `${(rowHeights[ri] ?? 7) * 2.83}px`,
                      }}
                      onMouseDown={(e) => handleCellMouseDown(ri, ci, e)}
                      onDoubleClick={() => handleCellDoubleClick(ri, ci)}
                    >
                      {editingCell?.row === ri && editingCell?.col === ci ? (
                        <input
                          type="text"
                          autoFocus
                          className="w-full h-full bg-white px-1.5 py-0.5 text-sm outline-none border-0"
                          style={{
                            fontWeight: cs?.bold ? 'bold' : undefined,
                            fontStyle: cs?.italic ? 'italic' : undefined,
                            textAlign: (cs?.align as React.CSSProperties['textAlign']) ?? 'left',
                            fontSize: cs?.font_size ? `${cs.font_size}pt` : undefined,
                          }}
                          value={cell}
                          onChange={(e) => setCellValue(ri, ci, e.target.value)}
                          onBlur={() => {
                            setEditingCell(null);
                            commitAll();
                          }}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault();
                              setEditingCell(null);
                              commitAll();
                              const next = ri + 1;
                              if (next < rowCount) {
                                setActiveCell({ row: next, col: ci });
                                setSelRange({ startRow: next, startCol: ci, endRow: next, endCol: ci });
                              }
                            }
                            if (e.key === 'Tab') {
                              e.preventDefault();
                              setEditingCell(null);
                              commitAll();
                              const next = e.shiftKey ? ci - 1 : ci + 1;
                              if (next >= 0 && next < colCount) {
                                setActiveCell({ row: ri, col: next });
                                setSelRange({ startRow: ri, startCol: next, endRow: ri, endCol: next });
                              }
                            }
                            if (e.key === 'Escape') {
                              setEditingCell(null);
                              commitAll();
                            }
                          }}
                        />
                      ) : (
                        <div
                          className="w-full h-full px-1.5 py-0.5 text-sm truncate select-none"
                          style={{
                            fontWeight: cs?.bold ? 'bold' : undefined,
                            fontStyle: cs?.italic ? 'italic' : undefined,
                            textAlign: (cs?.align as React.CSSProperties['textAlign']) ?? 'left',
                            fontSize: cs?.font_size ? `${cs.font_size}pt` : undefined,
                          }}
                        >
                          {cell || '\u00A0'}
                        </div>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 flex-wrap">
        <button type="button" onClick={addRow} className={btnClass}>
          + Rij
        </button>
        <button
          type="button"
          onClick={removeRow}
          disabled={rowCount <= 1}
          className={`${btnClass} ${rowCount <= 1 ? 'opacity-40 cursor-not-allowed' : ''}`}
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
        <button
          type="button"
          onClick={handleCopy}
          className={`${btnClass} ${copied ? 'bg-green-50 border-green-300 text-green-700' : ''}`}
          title="Kopieer als TSV"
        >
          {copied ? 'Gekopieerd!' : 'Kopieer TSV'}
        </button>
        <span className="text-[10px] text-gray-400">
          {colCount}×{rowCount} · Plak vanuit Excel met Ctrl+V
        </span>
      </div>
    </div>
  );
}

/** Filter cell_styles to only include valid row,col coordinates. */
function filterStyles(
  styles: Record<string, CellStyle>,
  maxRows: number,
  maxCols: number,
): Record<string, CellStyle> {
  const result: Record<string, CellStyle> = {};
  for (const [key, val] of Object.entries(styles)) {
    const [r, c] = key.split(',').map(Number);
    if (r !== undefined && c !== undefined && r < maxRows && c < maxCols) {
      result[key] = val;
    }
  }
  return result;
}
