import { useState, useEffect } from 'react';
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
import { useApiStore } from '@/stores/apiStore';
import { BlockToolbox } from '@/components/editor/BlockToolbox';
import { BlockEditor } from '@/components/editor/BlockEditor';
import { AppendixEditor } from '@/components/editor/AppendixEditor';
import { MetadataForm } from '@/components/forms/MetadataForm';
import { CoverForm } from '@/components/forms/CoverForm';
import { ColofonForm } from '@/components/forms/ColofonForm';
import { OptionsPanel } from '@/components/forms/OptionsPanel';
import { FieldGroupForm } from '@/components/forms/FieldGroupForm';
import { ToggleSwitch } from '@/components/forms/ToggleSwitch';
import { BlockIcon } from '@/components/shared/BlockIcons';
import type { EditorBlock, EditorSection } from '@/types/report';

const BLOCK_TYPE_LABELS: Record<string, string> = {
  paragraph: 'Tekst',
  calculation: 'Berekening',
  check: 'Toets',
  table: 'Tabel',
  image: 'Afbeelding',
  map: 'Kaart',
  bullet_list: 'Opsomming',
  heading_2: 'Subkop',
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
  bullet_list: 'border-l-gray-300',
  heading_2: 'border-l-indigo-400',
  spacer: 'border-l-gray-200',
  page_break: 'border-l-orange-300',
  raw_flowable: 'border-l-red-300',
};

// ---------- Block summary ----------

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
          {block.result && block.unit && (
            <p className="text-xs">
              = {block.result} {block.unit}
            </p>
          )}
        </div>
      );
    case 'check': {
      const uc = block.unity_check;
      const limit = block.limit ?? 1.0;
      const pass = uc !== undefined && uc <= limit;
      return (
        <div className="text-sm text-gray-600">
          <p>{block.description || 'Naamloze toets'}</p>
          {uc !== undefined && (
            <span
              className={`inline-block mt-1 rounded px-1.5 py-0.5 text-xs font-semibold ${
                pass ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
              }`}
            >
              UC = {uc.toFixed(2)} {pass ? 'VOLDOET' : 'VOLDOET NIET'}
            </span>
          )}
        </div>
      );
    }
    case 'table':
      return (
        <div className="text-sm text-gray-600">
          {block.title && <p className="font-medium">{block.title}</p>}
          <p className="text-xs text-gray-400">
            {block.headers.length} kolommen &middot; {block.rows.length} rij
            {block.rows.length !== 1 ? 'en' : ''}
          </p>
        </div>
      );
    case 'image':
      return (
        <div className="text-sm text-gray-600">
          <p className="text-xs text-gray-400">
            {typeof block.src === 'string'
              ? block.src || 'Geen bron'
              : `Base64 ${block.src.media_type}`}
          </p>
          {block.caption && <p className="text-xs">{block.caption}</p>}
        </div>
      );
    case 'map':
      return (
        <div className="text-sm text-gray-600">
          {block.center && (
            <p className="text-xs font-mono text-gray-400">
              {block.center.lat.toFixed(4)}, {block.center.lon.toFixed(4)}
            </p>
          )}
          {block.caption && <p className="text-xs">{block.caption}</p>}
          {block.layers && (
            <p className="text-xs text-gray-400">{block.layers.join(', ')}</p>
          )}
        </div>
      );
    case 'spacer':
      return (
        <p className="text-xs text-gray-400">{block.height_mm ?? 5} mm</p>
      );
    case 'bullet_list':
      return (
        <div className="text-sm text-gray-600">
          <p className="text-xs text-gray-400">{block.items.length} item{block.items.length !== 1 ? 's' : ''}</p>
          {block.items.slice(0, 3).map((item, i) => (
            <p key={i} className="text-xs text-gray-500 truncate">&bull; {item || <span className="italic text-gray-400">Leeg</span>}</p>
          ))}
          {block.items.length > 3 && <p className="text-xs text-gray-400">+{block.items.length - 3} meer</p>}
        </div>
      );
    case 'heading_2':
      return (
        <p className="text-sm font-semibold text-gray-700">
          {block.number && <span className="text-gray-400 mr-1">{block.number}</span>}
          {block.title || <span className="italic text-gray-400">Naamloze subkop</span>}
        </p>
      );
    case 'page_break':
      return <p className="text-xs text-gray-400">Nieuwe pagina</p>;
    case 'raw_flowable':
      return (
        <p className="text-xs text-gray-400 italic">
          {block.class_name} (library-only)
        </p>
      );
    default:
      return null;
  }
}

// ---------- Sortable block item ----------

interface SortableBlockItemProps {
  block: EditorBlock;
  sectionId: string;
  isActive: boolean;
  onSelect: () => void;
}

function SortableBlockItem({ block, sectionId, isActive, onSelect }: SortableBlockItemProps) {
  const removeBlock = useReportStore((s) => s.removeBlock);
  const duplicateBlock = useReportStore((s) => s.duplicateBlock);

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
          ? 'border-brand-primary ring-2 ring-brand-primary/20'
          : 'border-gray-100 hover:border-gray-200 hover:shadow-md'
      }`}
    >
      {/* Top bar: type label + actions */}
      <div className="mb-1 flex items-center gap-2">
        {/* Drag handle */}
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

        <span className="flex items-center gap-1.5 rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-gray-500">
          <BlockIcon type={block.type} className="h-3 w-3" />
          {BLOCK_TYPE_LABELS[block.type] ?? block.type}
        </span>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Action buttons - visible on hover */}
        <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
          {/* Duplicate */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              duplicateBlock(sectionId, block.id);
            }}
            className="flex h-6 w-6 items-center justify-center rounded text-gray-400 hover:bg-blue-50 hover:text-blue-500"
            title="Dupliceer block"
            aria-label="Dupliceer block"
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 00-3.375-3.375h-1.5a1.125 1.125 0 01-1.125-1.125v-1.5a3.375 3.375 0 00-3.375-3.375H9.75" />
            </svg>
          </button>

          {/* Delete */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              removeBlock(sectionId, block.id);
            }}
            className="flex h-6 w-6 items-center justify-center rounded text-gray-400 hover:bg-red-50 hover:text-red-500"
            title="Verwijder block"
            aria-label="Verwijder block"
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
            </svg>
          </button>
        </div>
      </div>

      {isActive ? (
        <BlockEditor block={block} sectionId={sectionId} />
      ) : (
        <BlockSummary block={block} />
      )}
    </div>
  );
}

// ---------- Section title editor ----------

function SectionHeader({ section, chapterNumber }: { section: EditorSection; chapterNumber: number }) {
  const updateSection = useReportStore((s) => s.updateSection);
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(section.title);

  function handleSave() {
    const trimmed = title.trim();
    if (trimmed && trimmed !== section.title) {
      updateSection(section.id, { title: trimmed });
    } else {
      setTitle(section.title);
    }
    setEditing(false);
  }

  if (editing) {
    return (
      <div className="flex items-center gap-3">
        <span className="flex h-7 w-7 items-center justify-center rounded bg-brand-primary/15 text-sm font-bold text-brand-primary-dark">
          {chapterNumber}
        </span>
        <input
          autoFocus
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onBlur={handleSave}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSave();
            if (e.key === 'Escape') {
              setTitle(section.title);
              setEditing(false);
            }
          }}
          className="flex-1 rounded border border-brand-primary px-2 py-1 text-lg font-semibold text-gray-900 outline-none ring-2 ring-brand-primary/20"
        />
        {/* Level selector */}
        <select
          value={section.level}
          onChange={(e) => updateSection(section.id, { level: Number(e.target.value) })}
          className="rounded border border-gray-200 px-2 py-1 text-sm text-gray-600"
        >
          {[1, 2, 3, 4].map((l) => (
            <option key={l} value={l}>H{l}</option>
          ))}
        </select>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <span className="flex h-7 w-7 items-center justify-center rounded bg-brand-primary/15 text-sm font-bold text-brand-primary-dark">
        {chapterNumber}
      </span>
      <h2
        className="flex-1 text-lg font-semibold text-gray-900 cursor-pointer hover:text-brand-primary-dark transition-colors"
        onClick={() => setEditing(true)}
        title="Klik om te bewerken"
      >
        {section.title}
      </h2>
      {section.page_break_before && (
        <span className="rounded bg-orange-100 px-1.5 py-0.5 text-xs text-orange-600">
          page break
        </span>
      )}
    </div>
  );
}

// ---------- Main panel ----------

export function MainPanel() {
  const activeSection = useReportStore((s) => s.activeSection);
  const activeAppendix = useReportStore((s) => s.activeAppendix);
  const sections = useReportStore((s) => s.report.sections);
  const activeBlock = useReportStore((s) => s.activeBlock);
  const setActiveBlock = useReportStore((s) => s.setActiveBlock);
  const reorderBlocks = useReportStore((s) => s.reorderBlocks);
  const viewMode = useReportStore((s) => s.viewMode);

  const section = sections.find((s) => s.id === activeSection);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor),
  );

  function handleDragEnd(event: DragEndEvent) {
    if (!section) return;
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const fromIndex = section.content.findIndex((b) => b.id === active.id);
    const toIndex = section.content.findIndex((b) => b.id === over.id);
    if (fromIndex !== -1 && toIndex !== -1) {
      reorderBlocks(section.id, fromIndex, toIndex);
    }
  }

  // JSON view mode
  if (viewMode === 'json') {
    return <JsonEditor />;
  }

  // Preview mode
  if (viewMode === 'preview') {
    return <PdfPreview />;
  }

  // Split mode: editor left, preview right
  if (viewMode === 'split') {
    return (
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 overflow-y-auto border-r border-gray-200">
          <EditorContent
            section={section}
            activeAppendix={activeAppendix}
            activeBlock={activeBlock}
            setActiveBlock={setActiveBlock}
            sensors={sensors}
            handleDragEnd={handleDragEnd}
          />
        </div>
        <div className="flex-1 flex flex-col">
          <PdfPreview />
        </div>
      </div>
    );
  }

  // Editor mode
  return (
    <EditorContent
      section={section}
      activeAppendix={activeAppendix}
      activeBlock={activeBlock}
      setActiveBlock={setActiveBlock}
      sensors={sensors}
      handleDragEnd={handleDragEnd}
    />
  );
}

// ---------- Panel titles ----------

const PANEL_TITLES: Record<string, string> = {
  rapport: 'Rapport instellingen',
  voorblad: 'Voorblad',
  colofon: 'Colofon',
  opties: 'Opties',
};

// ---------- Editor content (reusable in full + split) ----------

function EditorContent({
  section,
  activeAppendix,
  activeBlock,
  setActiveBlock,
  sensors,
  handleDragEnd,
}: {
  section: EditorSection | undefined;
  activeAppendix: string | null;
  activeBlock: string | null;
  setActiveBlock: (id: string | null) => void;
  sensors: ReturnType<typeof useSensors>;
  handleDragEnd: (event: DragEndEvent) => void;
}) {
  const activePanel = useReportStore((s) => s.activePanel);
  const activeFieldGroup = useReportStore((s) => s.activeFieldGroup);
  const sections = useReportStore((s) => s.report.sections);

  // Field group editor (BIC forms)
  if (activeFieldGroup) {
    return <FieldGroupForm groupKey={activeFieldGroup} />;
  }

  // Appendix editor
  if (activeAppendix) {
    return <AppendixEditor appendixId={activeAppendix} />;
  }

  // No section selected — show active metadata panel
  if (!section) {
    return (
      <div className="flex-1 overflow-y-auto">
        <div className="sticky top-0 z-10 border-b border-gray-200 bg-white/95 backdrop-blur px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">
            {PANEL_TITLES[activePanel] ?? activePanel}
          </h2>
        </div>
        <div className="px-6 py-6">
          {activePanel === 'rapport' && <MetadataForm />}
          {activePanel === 'voorblad' && <CoverForm />}
          {activePanel === 'colofon' && <ColofonForm />}
          {activePanel === 'opties' && <OptionsPanel />}
        </div>
      </div>
    );
  }

  const chapterNumber = sections.findIndex((s) => s.id === section.id) + 1;

  return (
    <div className="flex-1 overflow-y-auto">
      {/* Section header */}
      <div className="sticky top-0 z-10 border-b border-gray-200 bg-white/95 backdrop-blur px-6 py-4">
        <SectionHeader section={section} chapterNumber={chapterNumber} />
      </div>

      {/* Content blocks */}
      <div className="px-6 py-4 space-y-3">
        {section.content.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="rounded-full bg-gray-100 p-4 mb-4">
              <svg className="h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m3.75 9v6m3-3H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
            </div>
            <p className="text-sm font-medium text-gray-500">Geen content blocks</p>
            <p className="text-xs text-gray-400 mt-1">
              Gebruik de toolbar hieronder om tekst, berekeningen of tabellen toe te voegen
            </p>
          </div>
        )}

        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext
            items={section.content.map((b) => b.id)}
            strategy={verticalListSortingStrategy}
          >
            {section.content.map((block) => (
              <SortableBlockItem
                key={block.id}
                block={block}
                sectionId={section.id}
                isActive={activeBlock === block.id}
                onSelect={() => setActiveBlock(block.id)}
              />
            ))}
          </SortableContext>
        </DndContext>

        {/* Block toolbox */}
        <div className="pt-2">
          <BlockToolbox sectionId={section.id} />
        </div>
      </div>
    </div>
  );
}

// ---------- Editable JSON view ----------

function JsonEditor() {
  const exportJson = useReportStore((s) => s.exportJson);
  const importJson = useReportStore((s) => s.importJson);
  const [jsonText, setJsonText] = useState(() => exportJson());
  const [jsonError, setJsonError] = useState<string | null>(null);

  // Sync when store changes externally (e.g. undo)
  const report = useReportStore((s) => s.report);
  useEffect(() => {
    setJsonText(exportJson());
    setJsonError(null);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [report]);

  function handleApply() {
    const result = importJson(jsonText);
    if (result.ok) {
      setJsonError(null);
    } else {
      setJsonError(result.errors[0] ?? 'Ongeldige JSON');
    }
  }

  function handleFormat() {
    try {
      const parsed = JSON.parse(jsonText);
      setJsonText(JSON.stringify(parsed, null, 2));
      setJsonError(null);
    } catch (e) {
      setJsonError(e instanceof Error ? e.message : 'Ongeldige JSON');
    }
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-gray-900">
      {/* Toolbar */}
      <div className="flex items-center gap-2 border-b border-gray-700 px-4 py-2">
        <button
          onClick={handleApply}
          className="rounded-md bg-brand-primary px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-primary-dark transition-colors"
        >
          Toepassen
        </button>
        <button
          onClick={handleFormat}
          className="rounded-md border border-gray-600 px-3 py-1.5 text-xs font-medium text-gray-300 hover:bg-gray-800 transition-colors"
        >
          Formatteren
        </button>
        {jsonError && (
          <span className="text-xs text-red-400 ml-2">{jsonError}</span>
        )}
      </div>

      <textarea
        value={jsonText}
        onChange={(e) => setJsonText(e.target.value)}
        className="flex-1 bg-gray-900 p-6 text-sm text-green-300 font-mono resize-none outline-none"
        spellCheck={false}
      />
    </div>
  );
}

// ---------- PDF Preview ----------

// ---------- Preview outline (clickable TOC for navigation) ----------

function PreviewOutline() {
  const sections = useReportStore((s) => s.report.sections);
  const appendices = useReportStore((s) => s.report.appendices);
  const activeSection = useReportStore((s) => s.activeSection);
  const activeAppendix = useReportStore((s) => s.activeAppendix);
  const setActiveSection = useReportStore((s) => s.setActiveSection);
  const setActiveAppendix = useReportStore((s) => s.setActiveAppendix);
  const setActivePanel = useReportStore((s) => s.setActivePanel);
  const activePanel = useReportStore((s) => s.activePanel);
  const [expanded, setExpanded] = useState(true);

  const isNavActive = activeSection === null && activeAppendix === null;

  if (!expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="absolute top-2 left-2 z-20 rounded-md bg-white/90 border border-gray-200 px-2 py-1 text-xs text-gray-500 hover:bg-white shadow-sm"
        title="Toon navigatie"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
        </svg>
      </button>
    );
  }

  return (
    <div className="absolute top-2 left-2 z-20 w-56 max-h-[60%] overflow-y-auto rounded-lg bg-white/95 border border-gray-200 shadow-lg backdrop-blur">
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-100">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Navigatie</span>
        <button
          onClick={() => setExpanded(false)}
          className="text-gray-400 hover:text-gray-600"
        >
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <nav className="p-1.5 space-y-0.5">
        {/* Meta panels */}
        {(['rapport', 'voorblad', 'colofon', 'opties'] as const).map((panel) => (
          <button
            key={panel}
            onClick={() => setActivePanel(panel)}
            className={`w-full text-left rounded px-2 py-1 text-xs transition-colors ${
              isNavActive && activePanel === panel
                ? 'bg-brand-primary-light text-brand-primary-dark font-medium'
                : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
            }`}
          >
            {panel === 'rapport' ? 'Rapport' : panel === 'voorblad' ? 'Voorblad' : panel === 'colofon' ? 'Colofon' : 'Opties'}
          </button>
        ))}

        {sections.length > 0 && (
          <div className="border-t border-gray-100 pt-1 mt-1">
            {sections.map((s, i) => (
              <button
                key={s.id}
                onClick={() => setActiveSection(s.id)}
                className={`w-full text-left rounded px-2 py-1 text-xs transition-colors ${
                  activeSection === s.id
                    ? 'bg-brand-primary-light text-brand-primary-dark font-medium'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <span className="font-bold mr-1">{i + 1}.</span>
                <span className="truncate">{s.title}</span>
              </button>
            ))}
          </div>
        )}

        {appendices.length > 0 && (
          <div className="border-t border-gray-100 pt-1 mt-1">
            {appendices.map((a) => (
              <button
                key={a.id}
                onClick={() => setActiveAppendix(a.id)}
                className={`w-full text-left rounded px-2 py-1 text-xs transition-colors ${
                  activeAppendix === a.id
                    ? 'bg-teal-50 text-teal-700 font-medium'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <span className="font-bold mr-1">B{a.number}.</span>
                <span className="truncate">{a.title}</span>
              </button>
            ))}
          </div>
        )}
      </nav>
    </div>
  );
}

// ---------- PDF Preview ----------

function PdfPreview() {
  const lastPdfUrl = useApiStore((s) => s.lastPdfUrl);
  const isGenerating = useApiStore((s) => s.isGenerating);
  const generatePdf = useApiStore((s) => s.generatePdf);
  const connected = useApiStore((s) => s.connected);
  const autoPreview = useApiStore((s) => s.autoPreview);
  const setAutoPreview = useApiStore((s) => s.setAutoPreview);
  const previewPage = useApiStore((s) => s.previewPage);
  const setPreviewPage = useApiStore((s) => s.setPreviewPage);
  const viewMode = useReportStore((s) => s.viewMode);

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Preview toolbar */}
      <div className="flex items-center gap-3 border-b border-gray-200 px-4 py-2 shrink-0">
        <ToggleSwitch checked={autoPreview} onChange={() => setAutoPreview(!autoPreview)} label="Auto-preview" />
        {isGenerating && (
          <span className="flex items-center gap-1.5 text-xs text-gray-400">
            <svg className="h-3 w-3 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Genereren...
          </span>
        )}
        {lastPdfUrl && (
          <div className="flex items-center gap-1 text-xs text-gray-500">
            <label htmlFor="preview-page" className="whitespace-nowrap">Pagina</label>
            <input
              id="preview-page"
              type="number"
              min={1}
              value={previewPage}
              onChange={(e) => setPreviewPage(Number(e.target.value))}
              className="w-12 rounded border border-gray-300 px-1.5 py-0.5 text-xs text-center font-mono focus:outline-none focus:ring-1 focus:ring-purple-400"
            />
          </div>
        )}
        <button
          onClick={generatePdf}
          disabled={!connected || isGenerating}
          className="rounded-md border border-gray-200 px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-40 flex items-center gap-1.5"
          title="Regenereer PDF"
        >
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
          </svg>
          {isGenerating ? "Genereren..." : "Regenereer"}
        </button>
      </div>

      {/* Preview content */}
      {lastPdfUrl ? (
        <div className="relative flex-1">
          {viewMode === 'split' && <PreviewOutline />}
          <iframe
            src={lastPdfUrl}
            className="absolute inset-0 w-full h-full border-0"
            title="PDF Preview"
          />
        </div>
      ) : (
        <div className="flex flex-1 flex-col items-center justify-center text-gray-400 gap-4">
          <div className="rounded-full bg-gray-100 p-4">
            <svg className="h-10 w-10 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
          </div>
          <p className="text-sm font-medium text-gray-500">Nog geen PDF gegenereerd</p>
          <button
            onClick={generatePdf}
            disabled={!connected}
            className="rounded-md bg-brand-primary px-4 py-2 text-sm font-medium text-white hover:bg-brand-primary-dark transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Genereer PDF
          </button>
        </div>
      )}
    </div>
  );
}
