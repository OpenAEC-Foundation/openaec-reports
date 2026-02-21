import { useState, useRef, useEffect } from 'react';
import { useReportStore } from '@/stores/reportStore';
import { BlockIcon } from '@/components/shared/BlockIcons';
import type { EditableBlockType } from '@/types/report';

interface BlockTypeOption {
  type: EditableBlockType;
  label: string;
  accent: string;
}

const BLOCK_OPTIONS: BlockTypeOption[] = [
  { type: 'paragraph', label: 'Tekst', accent: 'text-gray-500' },
  { type: 'calculation', label: 'Berekening', accent: 'text-blue-500' },
  { type: 'check', label: 'Toets', accent: 'text-green-500' },
  { type: 'table', label: 'Tabel', accent: 'text-gray-500' },
  { type: 'image', label: 'Afbeelding', accent: 'text-purple-500' },
  { type: 'map', label: 'Kaart', accent: 'text-emerald-500' },
  { type: 'bullet_list', label: 'Opsomming', accent: 'text-gray-500' },
  { type: 'heading_2', label: 'Subkop (H2)', accent: 'text-indigo-500' },
  { type: 'spacer', label: 'Witruimte', accent: 'text-gray-400' },
  { type: 'page_break', label: 'Pagina-einde', accent: 'text-orange-400' },
];

interface BlockToolboxProps {
  sectionId?: string;
  onAdd?: (blockType: EditableBlockType) => void;
}

export function BlockToolbox({ sectionId, onAdd }: BlockToolboxProps) {
  const [open, setOpen] = useState(false);
  const addNewBlock = useReportStore((s) => s.addNewBlock);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [open]);

  function handleAdd(type: EditableBlockType) {
    if (onAdd) {
      onAdd(type);
    } else if (sectionId) {
      addNewBlock(sectionId, type);
    }
    setOpen(false);
  }

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 rounded-md border border-dashed border-gray-300 px-3 py-2 text-sm text-gray-500 hover:border-brand-primary hover:text-brand-primary-dark transition-colors"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        Block toevoegen
      </button>

      {open && (
        <div className="absolute left-0 top-full z-20 mt-1 w-56 rounded-lg border border-gray-200 bg-white py-1 shadow-lg">
          {BLOCK_OPTIONS.map((opt) => (
            <button
              key={opt.type}
              onClick={() => handleAdd(opt.type)}
              className="flex w-full items-center gap-3 px-3 py-2 text-left text-sm hover:bg-gray-50 transition-colors"
            >
              <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded bg-gray-100 ${opt.accent}`}>
                <BlockIcon type={opt.type} className="h-3.5 w-3.5" />
              </span>
              <span className="text-gray-700">{opt.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
