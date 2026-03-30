import { useState, useCallback, useRef, useEffect } from "react";
import type { SpreadsheetBlock, CellStyle, MergedCell } from "@/types/report";

interface SpreadsheetEditorProps {
  block: SpreadsheetBlock & { id: string };
  onChange: (updates: Partial<SpreadsheetBlock>) => void;
}

// --- Constants ---

const DEFAULT_COL_WIDTH = 34;
const DEFAULT_ROW_HEIGHT = 7;
const MIN_COL_WIDTH = 15;
const MIN_ROW_HEIGHT = 5;
const PX_PER_MM = 2.83;

const BG_COLORS = [
  "#ffffff", "#f3f4f6", "#fef3c7", "#d1fae5",
  "#dbeafe", "#ede9fe", "#fce7f3", "#fee2e2",
  "#40124A", "#38BDA0",
];

const TEXT_COLORS = [
  "#000000", "#374151", "#991b1b", "#92400e",
  "#065f46", "#1e40af", "#5b21b6", "#9d174d",
  "#ffffff", "#40124A",
];

const FONT_SIZES = [7, 8, 9, 10, 11, 12, 14, 16, 18, 24];

// --- Helpers ---

type Selection = { row: number; col: number };
type SelectionRange = {
  startRow: number;
  startCol: number;
  endRow: number;
  endCol: number;
};

function colLabel(index: number): string {
  let label = "";
  let n = index;
  while (n >= 0) {
    label = String.fromCharCode(65 + (n % 26)) + label;
    n = Math.floor(n / 26) - 1;
  }
  return label;
}

function cellRef(row: number, col: number): string {
  return `${colLabel(col)}${row + 1}`;
}

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

function isMergedHidden(row: number, col: number, merges: MergedCell[]): boolean {
  for (const m of merges) {
    if (
      row >= m.row && row < m.row + m.rowspan &&
      col >= m.col && col < m.col + m.colspan &&
      !(row === m.row && col === m.col)
    ) {
      return true;
    }
  }
  return false;
}

function getMergeAt(row: number, col: number, merges: MergedCell[]): MergedCell | null {
  return merges.find((m) => m.row === row && m.col === col) ?? null;
}


/** Shift cell style keys when inserting/deleting rows or columns. */
function shiftStyles(
  styles: Record<string, CellStyle>,
  axis: "row" | "col",
  index: number,
  delta: 1 | -1,
): Record<string, CellStyle> {
  const result: Record<string, CellStyle> = {};
  for (const [key, val] of Object.entries(styles)) {
    const [r, c] = key.split(",").map(Number);
    if (r === undefined || c === undefined) continue;
    let nr = r, nc = c;
    if (axis === "row") {
      if (delta === -1 && r === index) continue;
      if (r >= index) nr = r + delta;
    } else {
      if (delta === -1 && c === index) continue;
      if (c >= index) nc = c + delta;
    }
    if (nr >= 0 && nc >= 0) result[`${nr},${nc}`] = val;
  }
  return result;
}

/** Shift merge definitions when inserting/deleting rows or columns. */
function shiftMerges(
  merges: MergedCell[],
  axis: "row" | "col",
  index: number,
  delta: 1 | -1,
): MergedCell[] {
  return merges
    .map((m) => {
      const newM = { ...m };
      if (axis === "row") {
        if (delta === -1 && m.row <= index && index < m.row + m.rowspan) {
          newM.rowspan = Math.max(1, m.rowspan - 1);
        }
        if (m.row >= index) newM.row = m.row + delta;
      } else {
        if (delta === -1 && m.col <= index && index < m.col + m.colspan) {
          newM.colspan = Math.max(1, m.colspan - 1);
        }
        if (m.col >= index) newM.col = m.col + delta;
      }
      return newM;
    })
    .filter((m) => m.row >= 0 && m.col >= 0 && m.rowspan > 0 && m.colspan > 0);
}

// --- SVG Icon components (inline, no dependency) ---

function IconAlignLeft({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="currentColor">
      <rect x="1" y="2" width="14" height="1.5" rx="0.5" />
      <rect x="1" y="6" width="10" height="1.5" rx="0.5" />
      <rect x="1" y="10" width="12" height="1.5" rx="0.5" />
      <rect x="1" y="14" width="8" height="1.5" rx="0.5" />
    </svg>
  );
}

function IconAlignCenter({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="currentColor">
      <rect x="1" y="2" width="14" height="1.5" rx="0.5" />
      <rect x="3" y="6" width="10" height="1.5" rx="0.5" />
      <rect x="2" y="10" width="12" height="1.5" rx="0.5" />
      <rect x="4" y="14" width="8" height="1.5" rx="0.5" />
    </svg>
  );
}

function IconAlignRight({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="currentColor">
      <rect x="1" y="2" width="14" height="1.5" rx="0.5" />
      <rect x="5" y="6" width="10" height="1.5" rx="0.5" />
      <rect x="3" y="10" width="12" height="1.5" rx="0.5" />
      <rect x="7" y="14" width="8" height="1.5" rx="0.5" />
    </svg>
  );
}

// --- Context Menu ---

interface ContextMenuProps {
  x: number;
  y: number;
  items: { label: string; onClick: () => void; danger?: boolean }[];
  onClose: () => void;
}

function ContextMenu({ x, y, items, onClose }: ContextMenuProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [onClose]);

  return (
    <div
      ref={ref}
      className="fixed z-50 min-w-[160px] rounded-md border border-oaec-border bg-oaec-bg-lighter py-1 shadow-lg"
      style={{ left: x, top: y }}
    >
      {items.map((item, i) => (
        <button
          key={i}
          type="button"
          onClick={() => { item.onClick(); onClose(); }}
          className={`w-full px-3 py-1.5 text-left text-xs hover:bg-oaec-hover transition-colors ${
            item.danger ? "text-oaec-danger hover:bg-oaec-danger-soft" : "text-oaec-text-secondary"
          }`}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}

// --- Color Picker Popover ---

interface ColorPickerProps {
  colors: string[];
  value?: string;
  onSelect: (color: string) => void;
  onClose: () => void;
}

function ColorPicker({ colors, value, onSelect, onClose }: ColorPickerProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [onClose]);

  return (
    <div
      ref={ref}
      className="absolute bottom-full left-0 mb-1 z-50 bg-oaec-bg-lighter border border-oaec-border rounded-md shadow-lg p-2.5 grid grid-cols-5 gap-1.5"
    >
      {colors.map((c) => (
        <button
          key={c}
          type="button"
          onClick={() => onSelect(c)}
          className={`w-8 h-8 rounded border hover:ring-2 hover:ring-oaec-accent/30 ${
            c === value ? "ring-2 ring-oaec-accent" : "border-oaec-border"
          }`}
          style={{ backgroundColor: c }}
        />
      ))}
    </div>
  );
}

// --- Main Component ---

const btnBase = "rounded border px-1.5 py-1 text-xs transition-colors flex items-center justify-center";
const btnNormal = `${btnBase} border-oaec-border text-oaec-text-secondary hover:bg-oaec-hover`;
const btnActive = `${btnBase} border-oaec-accent text-oaec-accent bg-oaec-accent-soft hover:bg-oaec-accent-soft`;

export function SpreadsheetEditor({ block, onChange }: SpreadsheetEditorProps) {
  // --- State ---
  const [title, setTitle] = useState(block.title ?? "");
  const [headers, setHeaders] = useState<string[]>([...block.headers]);
  const [rows, setRows] = useState<string[][]>(
    block.rows.map((row) => row.map((cell) => String(cell ?? ""))),
  );
  const [colWidths, setColWidths] = useState<number[]>(
    block.column_widths ?? block.headers.map(() => DEFAULT_COL_WIDTH),
  );
  const [rowHeights, setRowHeights] = useState<number[]>(
    block.row_heights ?? block.rows.map(() => block.default_row_height ?? DEFAULT_ROW_HEIGHT),
  );
  const [mergedCells, setMergedCells] = useState<MergedCell[]>(block.merged_cells ?? []);
  const [cellStyles, setCellStyles] = useState<Record<string, CellStyle>>(block.cell_styles ?? {});
  const [showGrid, setShowGrid] = useState(block.show_grid ?? true);

  const [activeCell, setActiveCell] = useState<Selection | null>(null);
  const [selRange, setSelRange] = useState<SelectionRange | null>(null);
  const [editingCell, setEditingCell] = useState<Selection | null>(null);
  const [copied, setCopied] = useState(false);
  const [showBgPicker, setShowBgPicker] = useState(false);
  const [showTextColorPicker, setShowTextColorPicker] = useState(false);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; row: number; col: number } | null>(null);

  const [resizingCol, setResizingCol] = useState<number | null>(null);
  const [resizingRow, setResizingRow] = useState<number | null>(null);
  const resizeStartX = useRef(0);
  const resizeStartY = useRef(0);
  const resizeStartSize = useRef(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const colCount = headers.length;
  const rowCount = rows.length;

  // --- Commit ---
  const commit = useCallback(
    (h: string[], r: string[][], cw: number[], rh: number[], mc: MergedCell[], cs: Record<string, CellStyle>) => {
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

  function commitAll() {
    commit(headers, rows, colWidths, rowHeights, mergedCells, cellStyles);
  }

  // --- Cell editing ---
  function setCellValue(row: number, col: number, value: string) {
    const newRows = rows.map((r) => [...r]);
    while (newRows.length <= row) newRows.push(Array(colCount).fill(""));
    while ((newRows[row]?.length ?? 0) <= col) newRows[row]!.push("");
    newRows[row]![col] = value;
    setRows(newRows);
  }

  // --- Selection ---
  function selectCell(row: number, col: number) {
    setActiveCell({ row, col });
    setSelRange({ startRow: row, startCol: col, endRow: row, endCol: col });
  }

  function handleCellMouseDown(row: number, col: number, e: React.MouseEvent) {
    if (e.button === 2) return; // right-click handled by context menu
    if (e.shiftKey && activeCell) {
      setSelRange({ startRow: activeCell.row, startCol: activeCell.col, endRow: row, endCol: col });
    } else {
      selectCell(row, col);
    }
    if (editingCell && (editingCell.row !== row || editingCell.col !== col)) {
      setEditingCell(null);
      commitAll();
    }
  }

  function handleCellDoubleClick(row: number, col: number) {
    setEditingCell({ row, col });
  }

  function handleContextMenu(row: number, col: number, e: React.MouseEvent) {
    e.preventDefault();
    if (!activeCell || activeCell.row !== row || activeCell.col !== col) {
      selectCell(row, col);
    }
    setContextMenu({ x: e.clientX, y: e.clientY, row, col });
  }

  // --- Keyboard ---
  function handleKeyDown(e: React.KeyboardEvent) {
    const mod = e.ctrlKey || e.metaKey;

    // Ctrl+B / Ctrl+I — always (even without active cell selection in grid)
    if (mod && activeCell) {
      if (e.key === "b" || e.key === "B") {
        e.preventDefault();
        toggleBold();
        return;
      }
      if (e.key === "i" || e.key === "I") {
        e.preventDefault();
        toggleItalic();
        return;
      }
    }

    if (!activeCell) return;
    const { row, col } = activeCell;

    if (e.key === "Tab") {
      e.preventDefault();
      const nextCol = e.shiftKey ? col - 1 : col + 1;
      if (nextCol >= 0 && nextCol < colCount) {
        selectCell(row, nextCol);
      }
      if (editingCell) { setEditingCell(null); commitAll(); }
      return;
    }
    if (e.key === "Enter") {
      e.preventDefault();
      if (editingCell) {
        setEditingCell(null);
        commitAll();
        const nextRow = e.shiftKey ? row - 1 : row + 1;
        if (nextRow >= 0 && nextRow < rowCount) selectCell(nextRow, col);
      } else {
        setEditingCell({ row, col });
      }
      return;
    }
    if (e.key === "F2") {
      e.preventDefault();
      setEditingCell({ row, col });
      return;
    }
    if (e.key === "Escape") {
      setEditingCell(null);
      commitAll();
      return;
    }
    if ((e.key === "Delete" || e.key === "Backspace") && !editingCell && selRange) {
      const { r1, c1, r2, c2 } = normalizeRange(selRange);
      const newRows = rows.map((r) => [...r]);
      for (let ri = r1; ri <= r2; ri++) {
        for (let ci = c1; ci <= c2; ci++) {
          if (newRows[ri]) newRows[ri]![ci] = "";
        }
      }
      setRows(newRows);
      commit(headers, newRows, colWidths, rowHeights, mergedCells, cellStyles);
      return;
    }

    // Arrow navigation when not editing
    if (!editingCell) {
      const arrows: Record<string, [number, number]> = {
        ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1],
      };
      const dir = arrows[e.key];
      if (dir) {
        e.preventDefault();
        const nr = Math.max(0, Math.min(rowCount - 1, row + dir[0]));
        const nc = Math.max(0, Math.min(colCount - 1, col + dir[1]));
        if (e.shiftKey && selRange) {
          setSelRange({ ...selRange, endRow: nr, endCol: nc });
        } else {
          selectCell(nr, nc);
        }
        setActiveCell({ row: nr, col: nc });
        return;
      }

      // Start editing on printable character
      if (e.key.length === 1 && !mod) {
        setCellValue(row, col, "");
        setEditingCell({ row, col });
      }
    }
  }

  // --- Paste ---
  function handlePaste(e: React.ClipboardEvent) {
    const target = e.target as HTMLElement;
    if (target.tagName === "INPUT" && editingCell) return;
    e.preventDefault();
    const text = e.clipboardData.getData("text/plain");
    const lines = text.trim().split("\n").map((line) => line.split("\t"));
    if (lines.length === 0) return;

    const startRow = activeCell?.row ?? 0;
    const startCol = activeCell?.col ?? 0;

    const newRows = rows.map((r) => [...r]);
    const newHeaders = [...headers];
    const newColWidths = [...colWidths];
    const newRowHeights = [...rowHeights];

    const neededCols = startCol + (lines[0]?.length ?? 0);
    while (newHeaders.length < neededCols) {
      const idx = newHeaders.length;
      newHeaders.push(colLabel(idx));
      newColWidths.push(DEFAULT_COL_WIDTH);
      newRows.forEach((r) => r.push(""));
    }
    const neededRows = startRow + lines.length;
    while (newRows.length < neededRows) {
      newRows.push(Array(newHeaders.length).fill(""));
      newRowHeights.push(block.default_row_height ?? DEFAULT_ROW_HEIGHT);
    }

    for (let ri = 0; ri < lines.length; ri++) {
      for (let ci = 0; ci < (lines[ri]?.length ?? 0); ci++) {
        const tr = startRow + ri;
        const tc = startCol + ci;
        if (tr < newRows.length && tc < newHeaders.length) {
          newRows[tr]![tc] = lines[ri]![ci]?.trim() ?? "";
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
    if (selRange) {
      const { r1, c1, r2, c2 } = normalizeRange(selRange);
      const lines = [];
      for (let ri = r1; ri <= r2; ri++) {
        const cells = [];
        for (let ci = c1; ci <= c2; ci++) {
          cells.push(rows[ri]?.[ci] ?? "");
        }
        lines.push(cells.join("\t"));
      }
      navigator.clipboard.writeText(lines.join("\n")).catch(() => {});
    } else {
      // Copy all
      const headerLine = headers.join("\t");
      const dataLines = rows.map((row) => row.join("\t"));
      navigator.clipboard.writeText([headerLine, ...dataLines].join("\n")).catch(() => {});
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  // --- Resize ---
  function startColResize(colIdx: number, e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    setResizingCol(colIdx);
    resizeStartX.current = e.clientX;
    resizeStartSize.current = colWidths[colIdx] ?? DEFAULT_COL_WIDTH;
  }

  function startRowResize(rowIdx: number, e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    setResizingRow(rowIdx);
    resizeStartY.current = e.clientY;
    resizeStartSize.current = rowHeights[rowIdx] ?? DEFAULT_ROW_HEIGHT;
  }

  useEffect(() => {
    if (resizingCol === null && resizingRow === null) return;

    function onMouseMove(e: MouseEvent) {
      if (resizingCol !== null) {
        const delta = (e.clientX - resizeStartX.current) / PX_PER_MM;
        setColWidths((prev) => {
          const copy = [...prev];
          copy[resizingCol] = Math.max(MIN_COL_WIDTH, Math.round(resizeStartSize.current + delta));
          return copy;
        });
      }
      if (resizingRow !== null) {
        const delta = (e.clientY - resizeStartY.current) / PX_PER_MM;
        setRowHeights((prev) => {
          const copy = [...prev];
          copy[resizingRow] = Math.max(MIN_ROW_HEIGHT, Math.round(resizeStartSize.current + delta));
          return copy;
        });
      }
    }

    function onMouseUp() {
      setResizingCol(null);
      setResizingRow(null);
    }

    document.body.style.cursor = resizingCol !== null ? "col-resize" : "row-resize";
    document.body.style.userSelect = "none";
    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
    return () => {
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resizingCol, resizingRow]);

  // Commit widths/heights after resize ends
  const prevResizingCol = useRef(resizingCol);
  const prevResizingRow = useRef(resizingRow);
  useEffect(() => {
    if (prevResizingCol.current !== null && resizingCol === null) {
      commit(headers, rows, colWidths, rowHeights, mergedCells, cellStyles);
    }
    if (prevResizingRow.current !== null && resizingRow === null) {
      commit(headers, rows, colWidths, rowHeights, mergedCells, cellStyles);
    }
    prevResizingCol.current = resizingCol;
    prevResizingRow.current = resizingRow;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resizingCol, resizingRow]);

  // --- Insert / Delete at position ---
  function insertRowAt(index: number) {
    const newRows = [...rows];
    newRows.splice(index, 0, Array(colCount).fill(""));
    const newHeights = [...rowHeights];
    newHeights.splice(index, 0, block.default_row_height ?? DEFAULT_ROW_HEIGHT);
    const newStyles = shiftStyles(cellStyles, "row", index, 1);
    const newMerges = shiftMerges(mergedCells, "row", index, 1);
    setRows(newRows);
    setRowHeights(newHeights);
    setCellStyles(newStyles);
    setMergedCells(newMerges);
    commit(headers, newRows, colWidths, newHeights, newMerges, newStyles);
  }

  function deleteRowAt(index: number) {
    if (rowCount <= 1) return;
    const newRows = [...rows];
    newRows.splice(index, 1);
    const newHeights = [...rowHeights];
    newHeights.splice(index, 1);
    const newStyles = shiftStyles(cellStyles, "row", index, -1);
    const newMerges = shiftMerges(mergedCells, "row", index, -1);
    setRows(newRows);
    setRowHeights(newHeights);
    setCellStyles(newStyles);
    setMergedCells(newMerges);
    commit(headers, newRows, colWidths, newHeights, newMerges, newStyles);
  }

  function insertColAt(index: number) {
    const newHeaders = [...headers];
    newHeaders.splice(index, 0, colLabel(colCount));
    const newRows = rows.map((r) => { const copy = [...r]; copy.splice(index, 0, ""); return copy; });
    const newWidths = [...colWidths];
    newWidths.splice(index, 0, DEFAULT_COL_WIDTH);
    const newStyles = shiftStyles(cellStyles, "col", index, 1);
    const newMerges = shiftMerges(mergedCells, "col", index, 1);
    setHeaders(newHeaders);
    setRows(newRows);
    setColWidths(newWidths);
    setCellStyles(newStyles);
    setMergedCells(newMerges);
    commit(newHeaders, newRows, newWidths, rowHeights, newMerges, newStyles);
  }

  function deleteColAt(index: number) {
    if (colCount <= 1) return;
    const newHeaders = [...headers];
    newHeaders.splice(index, 1);
    const newRows = rows.map((r) => { const copy = [...r]; copy.splice(index, 1); return copy; });
    const newWidths = [...colWidths];
    newWidths.splice(index, 1);
    const newStyles = shiftStyles(cellStyles, "col", index, -1);
    const newMerges = shiftMerges(mergedCells, "col", index, -1);
    setHeaders(newHeaders);
    setRows(newRows);
    setColWidths(newWidths);
    setCellStyles(newStyles);
    setMergedCells(newMerges);
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
        const cleaned: CellStyle = {};
        if (merged.bold) cleaned.bold = true;
        if (merged.italic) cleaned.italic = true;
        if (merged.align && merged.align !== "left") cleaned.align = merged.align;
        if (merged.bg_color && merged.bg_color !== "#ffffff") cleaned.bg_color = merged.bg_color;
        if (merged.text_color && merged.text_color !== "#000000") cleaned.text_color = merged.text_color;
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
    applyStyleToSelection({ bold: !getSelectionStyle().bold });
  }

  function toggleItalic() {
    applyStyleToSelection({ italic: !getSelectionStyle().italic });
  }

  function setAlignment(align: "left" | "center" | "right") {
    applyStyleToSelection({ align });
  }

  function setFontSize(size: number | undefined) {
    applyStyleToSelection({ font_size: size });
  }

  // --- Merge ---
  function mergeCells() {
    if (!selRange) return;
    const { r1, c1, r2, c2 } = normalizeRange(selRange);
    if (r1 === r2 && c1 === c2) return;
    const newMerges = mergedCells.filter(
      (m) => m.row + m.rowspan <= r1 || m.row > r2 || m.col + m.colspan <= c1 || m.col > c2,
    );
    newMerges.push({ row: r1, col: c1, rowspan: r2 - r1 + 1, colspan: c2 - c1 + 1 });
    setMergedCells(newMerges);
    commit(headers, rows, colWidths, rowHeights, newMerges, cellStyles);
  }

  function unmergeCells() {
    if (!activeCell) return;
    const newMerges = mergedCells.filter((m) => !(m.row === activeCell.row && m.col === activeCell.col));
    setMergedCells(newMerges);
    commit(headers, rows, colWidths, rowHeights, newMerges, cellStyles);
  }

  const activeMerge = activeCell ? getMergeAt(activeCell.row, activeCell.col, mergedCells) : null;
  const selStyle = getSelectionStyle();
  const hasMultiSelection = selRange
    ? (() => { const { r1, c1, r2, c2 } = normalizeRange(selRange); return r1 !== r2 || c1 !== c2; })()
    : false;

  // Cell value for formula bar
  const activeCellValue = activeCell ? (rows[activeCell.row]?.[activeCell.col] ?? "") : "";

  // Context menu items
  const ctxItems = contextMenu ? [
    { label: "Rij invoegen boven", onClick: () => insertRowAt(contextMenu.row) },
    { label: "Rij invoegen onder", onClick: () => insertRowAt(contextMenu.row + 1) },
    { label: "Rij verwijderen", onClick: () => deleteRowAt(contextMenu.row), danger: rowCount <= 1 },
    { label: "Kolom invoegen links", onClick: () => insertColAt(contextMenu.col) },
    { label: "Kolom invoegen rechts", onClick: () => insertColAt(contextMenu.col + 1) },
    { label: "Kolom verwijderen", onClick: () => deleteColAt(contextMenu.col), danger: colCount <= 1 },
  ] : [];

  return (
    <div
      ref={containerRef}
      className="space-y-0"
      onPaste={handlePaste}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      style={{ outline: "none" }}
    >
      {/* Title */}
      <input
        type="text"
        className="w-full rounded-t border border-oaec-border bg-oaec-bg px-2 py-1.5 text-sm focus:border-oaec-accent focus:ring-1 focus:ring-oaec-accent/20 outline-none"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        onBlur={() => {
          if (title !== (block.title ?? "")) onChange({ title: title || undefined });
        }}
        placeholder="Titel (optioneel)"
      />

      {/* Toolbar */}
      <div className="flex items-center gap-0.5 flex-wrap border-x border-b border-oaec-border px-1.5 py-1 bg-oaec-bg">
        {/* Cell reference */}
        <span className="inline-flex items-center rounded border border-oaec-border bg-oaec-bg-lighter px-1.5 py-0.5 text-[11px] font-mono text-oaec-text-secondary min-w-[36px] text-center mr-1">
          {activeCell ? cellRef(activeCell.row, activeCell.col) : "—"}
        </span>

        {/* Bold / Italic */}
        <button type="button" onClick={toggleBold} className={selStyle.bold ? btnActive : btnNormal} title="Vet (Ctrl+B)">
          <span className="font-bold text-[11px] w-4">B</span>
        </button>
        <button type="button" onClick={toggleItalic} className={selStyle.italic ? btnActive : btnNormal} title="Cursief (Ctrl+I)">
          <span className="italic text-[11px] w-4">I</span>
        </button>

        <span className="mx-0.5 h-4 w-px bg-oaec-hover-strong" />

        {/* Font size */}
        <select
          className="rounded border border-oaec-border bg-oaec-bg-lighter px-1 py-0.5 text-[11px] text-oaec-text-secondary outline-none hover:bg-oaec-hover"
          value={selStyle.font_size ?? ""}
          onChange={(e) => setFontSize(e.target.value ? Number(e.target.value) : undefined)}
          title="Lettergrootte"
        >
          <option value="">Auto</option>
          {FONT_SIZES.map((s) => (
            <option key={s} value={s}>{s}pt</option>
          ))}
        </select>

        <span className="mx-0.5 h-4 w-px bg-oaec-hover-strong" />

        {/* Alignment */}
        <button
          type="button"
          onClick={() => setAlignment("left")}
          className={(!selStyle.align || selStyle.align === "left") ? btnActive : btnNormal}
          title="Links uitlijnen"
        >
          <IconAlignLeft className="h-3.5 w-3.5" />
        </button>
        <button
          type="button"
          onClick={() => setAlignment("center")}
          className={selStyle.align === "center" ? btnActive : btnNormal}
          title="Centreren"
        >
          <IconAlignCenter className="h-3.5 w-3.5" />
        </button>
        <button
          type="button"
          onClick={() => setAlignment("right")}
          className={selStyle.align === "right" ? btnActive : btnNormal}
          title="Rechts uitlijnen"
        >
          <IconAlignRight className="h-3.5 w-3.5" />
        </button>

        <span className="mx-0.5 h-4 w-px bg-oaec-hover-strong" />

        {/* Background color */}
        <div className="relative">
          <button
            type="button"
            onClick={() => { setShowBgPicker(!showBgPicker); setShowTextColorPicker(false); }}
            className={btnNormal}
            title="Achtergrondkleur"
          >
            <span className="flex flex-col items-center">
              <svg className="h-3 w-3" viewBox="0 0 16 16" fill="currentColor">
                <path d="M5.7 2.3a1 1 0 011.4 0l5 5a1 1 0 010 1.4l-5 5a1 1 0 01-1.4 0l-5-5a1 1 0 010-1.4l5-5z" />
              </svg>
              <span
                className="w-4 h-1 rounded-sm mt-px"
                style={{ backgroundColor: selStyle.bg_color ?? "#f3f4f6" }}
              />
            </span>
          </button>
          {showBgPicker && (
            <ColorPicker
              colors={BG_COLORS}
              value={selStyle.bg_color}
              onSelect={(c) => { applyStyleToSelection({ bg_color: c }); setShowBgPicker(false); }}
              onClose={() => setShowBgPicker(false)}
            />
          )}
        </div>

        {/* Text color */}
        <div className="relative">
          <button
            type="button"
            onClick={() => { setShowTextColorPicker(!showTextColorPicker); setShowBgPicker(false); }}
            className={btnNormal}
            title="Tekstkleur"
          >
            <span className="flex flex-col items-center">
              <span className="text-[11px] font-bold leading-none" style={{ color: selStyle.text_color ?? "#000000" }}>A</span>
              <span
                className="w-4 h-1 rounded-sm mt-px"
                style={{ backgroundColor: selStyle.text_color ?? "#000000" }}
              />
            </span>
          </button>
          {showTextColorPicker && (
            <ColorPicker
              colors={TEXT_COLORS}
              value={selStyle.text_color}
              onSelect={(c) => { applyStyleToSelection({ text_color: c }); setShowTextColorPicker(false); }}
              onClose={() => setShowTextColorPicker(false)}
            />
          )}
        </div>

        <span className="mx-0.5 h-4 w-px bg-oaec-hover-strong" />

        {/* Merge / split */}
        {hasMultiSelection && !activeMerge && (
          <button type="button" onClick={mergeCells} className={btnNormal} title="Cellen samenvoegen">
            <svg className="h-3.5 w-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
              <rect x="1" y="1" width="14" height="14" rx="1" />
              <line x1="8" y1="1" x2="8" y2="15" strokeDasharray="2 2" />
              <line x1="1" y1="8" x2="15" y2="8" strokeDasharray="2 2" />
            </svg>
          </button>
        )}
        {activeMerge && (
          <button type="button" onClick={unmergeCells} className={btnNormal} title="Splitsen">
            <svg className="h-3.5 w-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
              <rect x="1" y="1" width="14" height="14" rx="1" />
              <line x1="8" y1="1" x2="8" y2="15" />
              <line x1="1" y1="8" x2="15" y2="8" />
            </svg>
          </button>
        )}

        <div className="flex-1" />

        {/* Grid toggle */}
        <label className="flex items-center gap-1 text-[11px] text-oaec-text-muted cursor-pointer">
          <input
            type="checkbox"
            checked={showGrid}
            onChange={(e) => { setShowGrid(e.target.checked); onChange({ show_grid: e.target.checked }); }}
            className="rounded border-oaec-border h-3 w-3"
          />
          Raster
        </label>

        {/* Copy */}
        <button
          type="button"
          onClick={handleCopy}
          className={`${btnNormal} ml-1 ${copied ? "!bg-oaec-success-soft !border-oaec-success !text-oaec-success" : ""}`}
          title="Kopieer selectie als TSV (plakbaar in Excel)"
        >
          <span className="text-[11px]">{copied ? "Gekopieerd!" : "Kopieer"}</span>
        </button>
      </div>

      {/* Formula bar */}
      <div className="flex items-center border-x border-b border-oaec-border bg-oaec-bg-lighter">
        <span className="shrink-0 border-r border-oaec-border px-2 py-1 text-[11px] text-oaec-text-faint">
          <em>fx</em>
        </span>
        <input
          type="text"
          className="flex-1 px-2 py-1 text-sm outline-none"
          value={editingCell ? (rows[editingCell.row]?.[editingCell.col] ?? "") : activeCellValue}
          onChange={(e) => {
            if (activeCell) setCellValue(activeCell.row, activeCell.col, e.target.value);
          }}
          onFocus={() => {
            if (activeCell && !editingCell) setEditingCell(activeCell);
          }}
          onBlur={() => {
            setEditingCell(null);
            commitAll();
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              setEditingCell(null);
              commitAll();
              if (activeCell && activeCell.row + 1 < rowCount) {
                selectCell(activeCell.row + 1, activeCell.col);
              }
              containerRef.current?.focus();
            }
            if (e.key === "Escape") {
              setEditingCell(null);
              commitAll();
              containerRef.current?.focus();
            }
          }}
          placeholder={activeCell ? `Inhoud van ${cellRef(activeCell.row, activeCell.col)}` : "Selecteer een cel"}
        />
      </div>

      {/* Grid */}
      <div className="overflow-x-auto overflow-y-scroll border-x border-b border-oaec-border rounded-b" style={{ maxHeight: "500px" }}>
        <table className="border-collapse" style={{ tableLayout: "fixed" }}>
          <colgroup>
            <col style={{ width: "32px" }} />
            {headers.map((_, ci) => (
              <col key={ci} style={{ width: `${(colWidths[ci] ?? DEFAULT_COL_WIDTH) * PX_PER_MM}px` }} />
            ))}
          </colgroup>
          {/* Column letter header row */}
          <thead className="sticky top-0 z-20">
            <tr className="bg-oaec-hover">
              <th className="border-r border-b border-oaec-border bg-oaec-hover" />
              {headers.map((_, ci) => (
                <th
                  key={ci}
                  className="relative border-r border-b border-oaec-border bg-oaec-hover py-0.5 text-[10px] font-medium text-oaec-text-muted text-center select-none group"
                >
                  {colLabel(ci)}
                  <div
                    className="absolute right-0 top-0 w-1.5 h-full cursor-col-resize hover:bg-oaec-accent/50"
                    onMouseDown={(e) => startColResize(ci, e)}
                  />
                </th>
              ))}
            </tr>
            {/* Header row (PDF table headers) */}
            <tr className="bg-oaec-bg">
              <td className="border-r border-b border-oaec-border bg-oaec-hover text-[10px] text-oaec-text-faint text-center select-none font-medium">
                H
              </td>
              {headers.map((header, ci) => (
                <td key={ci} className="border-r border-b border-oaec-border bg-oaec-bg p-0">
                  <input
                    type="text"
                    className="w-full bg-transparent px-1.5 py-1 text-xs font-semibold text-oaec-text-secondary outline-none"
                    value={header}
                    onChange={(e) => {
                      const nh = [...headers];
                      nh[ci] = e.target.value;
                      setHeaders(nh);
                    }}
                    onBlur={commitAll}
                    placeholder={colLabel(ci)}
                  />
                </td>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, ri) => (
              <tr key={ri} className="group/row">
                {/* Row number */}
                <td
                  className="sticky left-0 z-10 border-r border-b border-oaec-border bg-oaec-hover text-[10px] text-oaec-text-muted text-center select-none relative font-medium"
                  style={{ height: `${(rowHeights[ri] ?? DEFAULT_ROW_HEIGHT) * PX_PER_MM}px` }}
                >
                  {ri + 1}
                  <div
                    className="absolute left-0 bottom-0 w-full h-1 cursor-row-resize hover:bg-oaec-accent/50"
                    onMouseDown={(e) => startRowResize(ri, e)}
                  />
                </td>
                {row.map((cell, ci) => {
                  if (isMergedHidden(ri, ci, mergedCells)) return null;
                  const merge = getMergeAt(ri, ci, mergedCells);
                  const isActive = activeCell?.row === ri && activeCell?.col === ci;
                  const isSelected = isInRange(ri, ci, selRange);
                  const cs = cellStyles[`${ri},${ci}`];

                  return (
                    <td
                      key={ci}
                      rowSpan={merge?.rowspan}
                      colSpan={merge?.colspan}
                      className={[
                        "p-0 relative",
                        showGrid ? "border border-oaec-border" : "border border-transparent",
                        isActive ? "outline outline-2 outline-blue-500 outline-offset-[-2px] z-10" : "",
                        isSelected && !isActive ? "bg-oaec-accent-soft/60" : "",
                      ].join(" ")}
                      style={{
                        backgroundColor: isSelected && !isActive
                          ? undefined
                          : (cs?.bg_color ?? undefined),
                        color: cs?.text_color ?? undefined,
                      }}
                      onMouseDown={(e) => handleCellMouseDown(ri, ci, e)}
                      onDoubleClick={() => handleCellDoubleClick(ri, ci)}
                      onContextMenu={(e) => handleContextMenu(ri, ci, e)}
                    >
                      {editingCell?.row === ri && editingCell?.col === ci ? (
                        <input
                          type="text"
                          autoFocus
                          className="w-full h-full bg-oaec-bg-lighter px-1.5 py-0.5 text-sm outline-none border-0"
                          style={{
                            fontWeight: cs?.bold ? "bold" : undefined,
                            fontStyle: cs?.italic ? "italic" : undefined,
                            textAlign: (cs?.align as React.CSSProperties["textAlign"]) ?? "left",
                            fontSize: cs?.font_size ? `${cs.font_size}pt` : undefined,
                          }}
                          value={cell}
                          onChange={(e) => setCellValue(ri, ci, e.target.value)}
                          onBlur={() => { setEditingCell(null); commitAll(); }}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") {
                              e.preventDefault();
                              setEditingCell(null);
                              commitAll();
                              if (ri + 1 < rowCount) selectCell(ri + 1, ci);
                            }
                            if (e.key === "Tab") {
                              e.preventDefault();
                              setEditingCell(null);
                              commitAll();
                              const next = e.shiftKey ? ci - 1 : ci + 1;
                              if (next >= 0 && next < colCount) selectCell(ri, next);
                            }
                            if (e.key === "Escape") { setEditingCell(null); commitAll(); }
                          }}
                        />
                      ) : (
                        <div
                          className="w-full h-full px-1.5 py-0.5 text-sm truncate select-none"
                          style={{
                            fontWeight: cs?.bold ? "bold" : undefined,
                            fontStyle: cs?.italic ? "italic" : undefined,
                            textAlign: (cs?.align as React.CSSProperties["textAlign"]) ?? "left",
                            fontSize: cs?.font_size ? `${cs.font_size}pt` : undefined,
                          }}
                        >
                          {cell || "\u00A0"}
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

      {/* Footer actions */}
      <div className="flex items-center gap-1.5 flex-wrap border-x border-b border-oaec-border rounded-b px-2 py-1.5 bg-oaec-bg">
        <button type="button" onClick={() => insertRowAt(rowCount)} className={btnNormal}>
          + Rij
        </button>
        <button type="button" onClick={() => insertColAt(colCount)} className={btnNormal}>
          + Kolom
        </button>
        <div className="flex-1" />
        <span className="text-[10px] text-oaec-text-faint">
          {colCount} kolommen &times; {rowCount} rijen &middot; Plak vanuit Excel met Ctrl+V
        </span>
      </div>

      {/* Context menu */}
      {contextMenu && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          items={ctxItems}
          onClose={() => setContextMenu(null)}
        />
      )}
    </div>
  );
}
