import { useState } from 'react';
import {
  DndContext,
  closestCenter,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import type { DragEndEvent } from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { useReportStore } from '@/stores/reportStore';
import { BlockToolbox } from './BlockToolbox';
import { BlockEditor } from './BlockEditor';
import type { EditorBlock, EditorAppendix } from '@/types/report';

const BLOCK_TYPE_LABELS: Record<string, string> = {
  paragraph: 'Tekst',
  calculation: 'Berekening',
  check: 'Toets',
  table: 'Tabel',
  image: 'Afbeelding',
  map: 'Kaart',
  spacer: 'Witruimte',
  page_break: 'Pagina-einde',
  raw_flowable: 'Raw (library)',
};

const BLOCK_TYPE_COLORS: Record<string, string> = {
  paragraph: 'border-l-gray-300',
  calculation: 'border-l-blue-400',
  check: 'border-l-green-400',
  table: 'border-l-gray-400',
  image: 'border-l-purple-400',
  map: 'border-l-emerald-400',
  spacer: 'border-l-gray-200',
  page_break: 'border-l-orange-300',
  raw_flowable: 'border-l-red-300',
};

// ---------- Block summary (duplicated from MainPanel for now) ----------

function BlockSummary({ block }: { block: EditorBlock }) {
  switch (block.type) {
    case 'paragraph':
      return (
        <p className="text-sm text-gray-600 line-clamp-2">
          {block.text || <span className="italic text-gray-400">Lege tekst</span>}
        </p>
      );
    case 'calculation':
      return (
        <div className="text-sm text-gray-600">
          <p className="font-medium">{block.title || 'Naamloze berekening'}</p>
          {block.formula && <p className="font-mono text-xs text-gray-500">{block.formula}</p>}
        </div>
      );
    case 'check':
      return (
        <p className="text-sm text-gray-600">{block.description || 'Naamloze toets'}</p>
      );
    case 'table':
      return (
        <p className="text-xs text-gray-400">
          {block.headers.length} kolommen &middot; {block.rows.length} rij{block.rows.length !== 1 ? 'en' : ''}
        </p>
      );
    case 'image':
      return (
        <p className="text-xs text-gray-400">{block.caption || 'Afbeelding'}</p>
      );
    case 'spacer':
      return <p className="text-xs text-gray-400">{block.height_mm ?? 5} mm</p>;
    case 'page_break':
      return <p className="text-xs text-gray-400">Nieuwe pagina</p>;
    default:
      return null;
  }
}

// ---------- Sortable block item ----------

interface SortableBlockItemProps {
  block: EditorBlock;
  appendixId: string;
  isActive: boolean;
  onSelect: () => void;
}

function SortableBlockItem({ block, appendixId, isActive, onSelect }: SortableBlockItemProps) {
  const removeAppendixBlock = useReportStore((s) => s.removeAppendixBlock);
  const duplicateAppendixBlock = useReportStore((s) => s.duplicateAppendixBlock);

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: block.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : undefined,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      onClick={onSelect}
      className={`group relative w-full text-left rounded-lg border-l-4 border bg-white p-4 shadow-sm transition-all cursor-pointer ${
        BLOCK_TYPE_COLORS[block.type] ?? 'border-l-gray-300'
      } ${
        isActive
          ? 'border-blue-300 ring-2 ring-blue-100'
          : 'border-gray-100 hover:border-gray-200'
      }`}
    >
      <div className="mb-1 flex items-center gap-2">
        <button
          className="flex h-5 w-5 shrink-0 cursor-grab items-center justify-center rounded text-gray-300 hover:text-gray-500 active:cursor-grabbing"
          {...attributes}
          {...listeners}
          onClick={(e) => e.stopPropagation()}
          aria-label="Versleep block"
        >
          <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
            <path d="M7 2a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm6 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM7 8a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm6 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM7 14a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm6 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4z" />
          </svg>
        </button>

        <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-gray-500">
          {BLOCK_TYPE_LABELS[block.type] ?? block.type}
        </span>

        <div className="flex-1" />

        <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
          <button
            onClick={(e) => {
              e.stopPropagation();
              duplicateAppendixBlock(appendixId, block.id);
            }}
            className="flex h-6 w-6 items-center justify-center rounded text-gray-400 hover:bg-blue-50 hover:text-blue-500"
            title="Dupliceer block"
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 00-3.375-3.375h-1.5a1.125 1.125 0 01-1.125-1.125v-1.5a3.375 3.375 0 00-3.375-3.375H9.75" />
            </svg>
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              removeAppendixBlock(appendixId, block.id);
            }}
            className="flex h-6 w-6 items-center justify-center rounded text-gray-400 hover:bg-red-50 hover:text-red-500"
            title="Verwijder block"
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
            </svg>
          </button>
        </div>
      </div>

      {isActive ? (
        <BlockEditor block={block} sectionId={appendixId} isAppendix />
      ) : (
        <BlockSummary block={block} />
      )}
    </div>
  );
}

// ---------- Appendix header ----------

function AppendixHeader({ appendix }: { appendix: EditorAppendix }) {
  const updateAppendix = useReportStore((s) => s.updateAppendix);
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(appendix.title);

  function handleSave() {
    const trimmed = title.trim();
    if (trimmed && trimmed !== appendix.title) {
      updateAppendix(appendix.id, { title: trimmed });
    } else {
      setTitle(appendix.title);
    }
    setEditing(false);
  }

  if (editing) {
    return (
      <div className="flex items-center gap-3">
        <span className="flex h-7 w-7 items-center justify-center rounded bg-teal-100 text-xs font-semibold text-teal-600">
          B{appendix.number}
        </span>
        <input
          autoFocus
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onBlur={handleSave}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSave();
            if (e.key === 'Escape') {
              setTitle(appendix.title);
              setEditing(false);
            }
          }}
          className="flex-1 rounded border border-teal-300 px-2 py-1 text-lg font-semibold text-gray-900 outline-none ring-2 ring-teal-100"
        />
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <span className="flex h-7 w-7 items-center justify-center rounded bg-teal-100 text-xs font-semibold text-teal-600">
        B{appendix.number}
      </span>
      <h2
        className="flex-1 text-lg font-semibold text-gray-900 cursor-pointer hover:text-teal-700 transition-colors"
        onClick={() => setEditing(true)}
        title="Klik om te bewerken"
      >
        {appendix.title}
      </h2>
    </div>
  );
}

// ---------- Appendix editor ----------

interface AppendixEditorProps {
  appendixId: string;
}

export function AppendixEditor({ appendixId }: AppendixEditorProps) {
  const appendices = useReportStore((s) => s.report.appendices);
  const activeBlock = useReportStore((s) => s.activeBlock);
  const setActiveBlock = useReportStore((s) => s.setActiveBlock);
  const reorderAppendixBlocks = useReportStore((s) => s.reorderAppendixBlocks);
  const addNewAppendixBlock = useReportStore((s) => s.addNewAppendixBlock);

  const appendix = appendices.find((a) => a.id === appendixId);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor),
  );

  function handleDragEnd(event: DragEndEvent) {
    if (!appendix) return;
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const fromIndex = appendix.content.findIndex((b) => b.id === active.id);
    const toIndex = appendix.content.findIndex((b) => b.id === over.id);
    if (fromIndex !== -1 && toIndex !== -1) {
      reorderAppendixBlocks(appendix.id, fromIndex, toIndex);
    }
  }

  if (!appendix) return null;

  return (
    <div className="flex-1 overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 z-10 border-b border-gray-200 bg-white/95 backdrop-blur px-6 py-4">
        <AppendixHeader appendix={appendix} />
      </div>

      {/* Divider preview hint */}
      <div className="mx-6 mt-4 rounded-lg border border-dashed border-teal-300 bg-teal-50 p-4 text-center">
        <p className="text-sm text-teal-700 font-medium">
          Bijlage {appendix.number} — Scheidingspagina
        </p>
        <p className="text-xs text-teal-500 mt-1">
          Turquoise divider wordt automatisch gegenereerd in de PDF
        </p>
      </div>

      {/* Content blocks */}
      <div className="px-6 py-4 space-y-3">
        {appendix.content.length === 0 && (
          <p className="py-4 text-center text-sm text-gray-400 italic">
            Optioneel: voeg content toe die na de divider komt
          </p>
        )}

        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext
            items={appendix.content.map((b) => b.id)}
            strategy={verticalListSortingStrategy}
          >
            {appendix.content.map((block) => (
              <SortableBlockItem
                key={block.id}
                block={block}
                appendixId={appendix.id}
                isActive={activeBlock === block.id}
                onSelect={() => setActiveBlock(block.id)}
              />
            ))}
          </SortableContext>
        </DndContext>

        <div className="pt-2">
          <BlockToolbox
            onAdd={(blockType) => addNewAppendixBlock(appendixId, blockType)}
          />
        </div>
      </div>
    </div>
  );
}
