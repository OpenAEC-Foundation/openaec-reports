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
import { BlockIcon } from '@/components/shared/BlockIcons';
import type { EditorSection, EditorAppendix } from '@/types/report';

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

function blockCountLabel(count: number): string {
  return `${count} block${count !== 1 ? 's' : ''}`;
}

// ---------- Sortable section item ----------

interface SortableSectionItemProps {
  section: EditorSection;
  isActive: boolean;
  isCollapsed: boolean;
  onSelect: () => void;
  onRemove: () => void;
  onToggleCollapse: () => void;
}

function SortableSectionItem({ section, isActive, isCollapsed, onSelect, onRemove, onToggleCollapse }: SortableSectionItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: section.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : undefined,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`group flex w-full items-start gap-1 rounded-md text-sm transition-colors ${
        isActive
          ? 'bg-brand-primary-light text-brand-primary-dark'
          : 'text-gray-700 hover:bg-gray-50'
      }`}
    >
      {/* Collapse chevron */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onToggleCollapse();
        }}
        className="mt-2 flex h-5 w-5 shrink-0 items-center justify-center rounded text-gray-400 hover:text-gray-600 transition-transform"
        aria-label={isCollapsed ? 'Uitklappen' : 'Inklappen'}
      >
        <svg
          className={`h-3 w-3 transition-transform ${isCollapsed ? '' : 'rotate-90'}`}
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path d="M6.293 4.293a1 1 0 011.414 0L12.414 9a1 1 0 010 1.414l-4.707 4.707a1 1 0 01-1.414-1.414L10.586 10 6.293 5.707a1 1 0 010-1.414z" />
        </svg>
      </button>

      {/* Drag handle */}
      <button
        className="mt-2 flex h-5 w-5 shrink-0 cursor-grab items-center justify-center rounded text-gray-300 hover:text-gray-500 active:cursor-grabbing"
        {...attributes}
        {...listeners}
        aria-label="Versleep sectie"
      >
        <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
          <path d="M7 2a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm6 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM7 8a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm6 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM7 14a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm6 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4z" />
        </svg>
      </button>

      {/* Section content - clickable */}
      <button
        onClick={onSelect}
        className="flex flex-1 items-start gap-2 py-2 pr-1 text-left"
      >
        <span
          className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded text-xs font-medium ${
            isActive
              ? 'bg-brand-primary/20 text-brand-primary-dark'
              : 'bg-gray-100 text-gray-500'
          }`}
        >
          H{section.level}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="truncate font-medium">{section.title}</p>
            {isCollapsed && section.content.length > 0 && (
              <span className="shrink-0 rounded-full bg-gray-200 px-1.5 py-0.5 text-[10px] font-medium text-gray-500">
                {section.content.length}
              </span>
            )}
          </div>
          {!isCollapsed && (
            <div className="mt-0.5 flex flex-wrap gap-1">
              <span className="text-xs text-gray-400">
                {blockCountLabel(section.content.length)}
              </span>
              {section.content.slice(0, 4).map((block) => (
                <span
                  key={block.id}
                  className="inline-flex items-center rounded bg-gray-100 px-1 py-0.5 text-gray-500"
                  title={BLOCK_TYPE_LABELS[block.type] ?? block.type}
                >
                  <BlockIcon type={block.type} className="h-3 w-3" />
                </span>
              ))}
              {section.content.length > 4 && (
                <span className="text-[10px] text-gray-400">
                  +{section.content.length - 4}
                </span>
              )}
            </div>
          )}
        </div>
      </button>

      {/* Delete button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onRemove();
        }}
        className="mr-1 mt-2 flex h-5 w-5 shrink-0 items-center justify-center rounded text-gray-300 opacity-0 transition-opacity hover:bg-red-50 hover:text-red-500 group-hover:opacity-100"
        aria-label="Verwijder sectie"
        title="Verwijder sectie"
      >
        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}

// ---------- Sortable appendix item ----------

interface SortableAppendixItemProps {
  appendix: EditorAppendix;
  isActive: boolean;
  onSelect: () => void;
  onRemove: () => void;
}

function SortableAppendixItem({ appendix, isActive, onSelect, onRemove }: SortableAppendixItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: appendix.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : undefined,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`group flex w-full items-start gap-1 rounded-md text-sm transition-colors ${
        isActive
          ? 'bg-teal-50 text-teal-700'
          : 'text-gray-700 hover:bg-gray-50'
      }`}
    >
      {/* Drag handle */}
      <button
        className="mt-2 flex h-5 w-5 shrink-0 cursor-grab items-center justify-center rounded text-gray-300 hover:text-gray-500 active:cursor-grabbing"
        {...attributes}
        {...listeners}
        aria-label="Versleep bijlage"
      >
        <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
          <path d="M7 2a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm6 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM7 8a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm6 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM7 14a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm6 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4z" />
        </svg>
      </button>

      {/* Appendix content - clickable */}
      <button
        onClick={onSelect}
        className="flex flex-1 items-start gap-2 py-2 pr-1 text-left"
      >
        <span
          className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded text-xs font-medium ${
            isActive
              ? 'bg-teal-100 text-teal-600'
              : 'bg-teal-50 text-teal-500'
          }`}
        >
          {appendix.number}
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate font-medium">{appendix.title}</p>
          {appendix.content.length > 0 && (
            <div className="mt-0.5 flex flex-wrap gap-1">
              <span className="text-xs text-gray-400">
                {blockCountLabel(appendix.content.length)}
              </span>
              {appendix.content.slice(0, 4).map((block) => (
                <span
                  key={block.id}
                  className="inline-flex items-center rounded bg-gray-100 px-1 py-0.5 text-gray-500"
                  title={BLOCK_TYPE_LABELS[block.type] ?? block.type}
                >
                  <BlockIcon type={block.type} className="h-3 w-3" />
                </span>
              ))}
              {appendix.content.length > 4 && (
                <span className="text-[10px] text-gray-400">
                  +{appendix.content.length - 4}
                </span>
              )}
            </div>
          )}
        </div>
      </button>

      {/* Delete button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onRemove();
        }}
        className="mr-1 mt-2 flex h-5 w-5 shrink-0 items-center justify-center rounded text-gray-300 opacity-0 transition-opacity hover:bg-red-50 hover:text-red-500 group-hover:opacity-100"
        aria-label="Verwijder bijlage"
        title="Verwijder bijlage"
      >
        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}

// ---------- Sidebar ----------

export function Sidebar() {
  const sections = useReportStore((s) => s.report.sections);
  const appendices = useReportStore((s) => s.report.appendices);
  const activeSection = useReportStore((s) => s.activeSection);
  const activeAppendix = useReportStore((s) => s.activeAppendix);
  const setActiveSection = useReportStore((s) => s.setActiveSection);
  const setActiveAppendix = useReportStore((s) => s.setActiveAppendix);
  const addNewSection = useReportStore((s) => s.addNewSection);
  const removeSection = useReportStore((s) => s.removeSection);
  const reorderSections = useReportStore((s) => s.reorderSections);
  const addNewAppendix = useReportStore((s) => s.addNewAppendix);
  const removeAppendix = useReportStore((s) => s.removeAppendix);
  const reorderAppendices = useReportStore((s) => s.reorderAppendices);
  const isDirty = useReportStore((s) => s.isDirty);
  const reset = useReportStore((s) => s.reset);
  const project = useReportStore((s) => s.report.project);
  const status = useReportStore((s) => s.report.status);

  const connected = useApiStore((s) => s.connected);
  const checking = useApiStore((s) => s.checking);
  const backendVersion = useApiStore((s) => s.backendVersion);

  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

  // Auto-expand active section
  useEffect(() => {
    if (activeSection) {
      setCollapsed((prev) => {
        if (prev.has(activeSection)) {
          const next = new Set(prev);
          next.delete(activeSection);
          return next;
        }
        return prev;
      });
    }
  }, [activeSection]);

  function toggleCollapse(id: string) {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const sectionSensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor),
  );

  const appendixSensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor),
  );

  function handleSectionDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const fromIndex = sections.findIndex((s) => s.id === active.id);
    const toIndex = sections.findIndex((s) => s.id === over.id);
    if (fromIndex !== -1 && toIndex !== -1) {
      reorderSections(fromIndex, toIndex);
    }
  }

  function handleAppendixDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const fromIndex = appendices.findIndex((a) => a.id === active.id);
    const toIndex = appendices.findIndex((a) => a.id === over.id);
    if (fromIndex !== -1 && toIndex !== -1) {
      reorderAppendices(fromIndex, toIndex);
    }
  }

  function handleConfirmDelete(id: string, removeFn: (id: string) => void) {
    if (confirmDeleteId === id) {
      removeFn(id);
      setConfirmDeleteId(null);
    } else {
      setConfirmDeleteId(id);
      setTimeout(() => setConfirmDeleteId((current) => (current === id ? null : current)), 3000);
    }
  }

  const totalBlocks =
    sections.reduce((sum, s) => sum + s.content.length, 0) +
    appendices.reduce((sum, a) => sum + a.content.length, 0);

  return (
    <aside className="flex h-full w-72 flex-col border-r border-gray-200 bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 px-4 py-3">
        {project ? (
          <p className="text-sm font-medium text-gray-900 truncate">{project}</p>
        ) : (
          <p className="text-sm text-gray-400 italic">Geen project</p>
        )}
        {status && (
          <span
            className={`mt-1 inline-block rounded px-1.5 py-0.5 text-xs font-medium ${
              status === 'DEFINITIEF'
                ? 'bg-green-100 text-green-700'
                : status === 'REVISIE'
                  ? 'bg-amber-100 text-amber-700'
                  : 'bg-gray-100 text-gray-600'
            }`}
          >
            {status}
          </span>
        )}
      </div>

      {/* Actions */}
      <div className="px-3 pt-3 pb-1 space-y-1">
        {/* Nieuw rapport */}
        <button
          onClick={() => {
            if (isDirty) {
              if (!confirm('Huidig rapport verwijderen? Onopgeslagen wijzigingen gaan verloren.')) return;
            }
            reset();
          }}
          className="w-full flex items-center gap-2 rounded-md px-2 py-2 text-sm text-gray-500 hover:bg-gray-50 hover:text-gray-700 transition-colors"
        >
          <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          Nieuw rapport
        </button>

        {/* Rapport instellingen */}
        <button
          onClick={() => { setActiveSection(null); }}
          className={`w-full flex items-center gap-2 rounded-md px-2 py-2 text-sm transition-colors ${
            activeSection === null && activeAppendix === null
              ? 'bg-brand-primary-light text-brand-primary-dark font-medium'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.298 1.466l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 010 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.298 1.466l-1.296 2.247a1.125 1.125 0 01-1.37.49l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.298-1.466l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 010-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 01-.298-1.466l1.297-2.247a1.125 1.125 0 011.37-.49l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28z" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          Rapport instellingen
        </button>
      </div>

      {/* Divider */}
      <div className="mx-4 border-t border-gray-100" />

      {/* Scrollable area for sections + appendices */}
      <div className="flex-1 overflow-y-auto">
        {/* Section list header + add button */}
        <div className="flex items-center justify-between px-4 pt-3 pb-1">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Secties
          </p>
          <button
            onClick={() => addNewSection()}
            className="flex items-center gap-1 rounded px-1.5 py-0.5 text-xs text-gray-400 hover:bg-brand-primary-light hover:text-brand-primary-dark transition-colors"
            title="Sectie toevoegen"
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Toevoegen
          </button>
        </div>

        {/* Sortable section list */}
        <nav className="px-2 py-1">
          {sections.length === 0 && (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <div className="rounded-full bg-gray-100 p-3 mb-3">
                <svg className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
              </div>
              <p className="text-sm text-gray-500">Geen secties</p>
              <button
                onClick={() => addNewSection()}
                className="mt-2 text-sm text-brand-primary hover:text-brand-primary-dark font-medium"
              >
                Eerste sectie toevoegen
              </button>
            </div>
          )}
          <DndContext
            sensors={sectionSensors}
            collisionDetection={closestCenter}
            onDragEnd={handleSectionDragEnd}
          >
            <SortableContext
              items={sections.map((s) => s.id)}
              strategy={verticalListSortingStrategy}
            >
              {sections.map((section) => (
                <div key={section.id} className="relative">
                  <SortableSectionItem
                    section={section}
                    isActive={activeSection === section.id}
                    isCollapsed={collapsed.has(section.id)}
                    onSelect={() => setActiveSection(section.id)}
                    onRemove={() => handleConfirmDelete(section.id, removeSection)}
                    onToggleCollapse={() => toggleCollapse(section.id)}
                  />
                  {confirmDeleteId === section.id && (
                    <div className="absolute right-0 top-0 z-10 rounded bg-red-600 px-2 py-1 text-xs text-white shadow-md">
                      Nogmaals klikken om te verwijderen
                    </div>
                  )}
                </div>
              ))}
            </SortableContext>
          </DndContext>
        </nav>

        {/* Divider between sections and appendices */}
        <div className="mx-4 my-1 border-t border-gray-100" />

        {/* Appendix list header + add button */}
        <div className="flex items-center justify-between px-4 pt-2 pb-1">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Bijlagen
          </p>
          <button
            onClick={() => addNewAppendix()}
            className="flex items-center gap-1 rounded px-1.5 py-0.5 text-xs text-gray-400 hover:bg-teal-50 hover:text-teal-600 transition-colors"
            title="Bijlage toevoegen"
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Toevoegen
          </button>
        </div>

        {/* Sortable appendix list */}
        <nav className="px-2 py-1">
          {appendices.length === 0 && (
            <div className="px-2 py-4 text-center">
              <p className="text-sm text-gray-400 italic">Geen bijlagen</p>
            </div>
          )}
          <DndContext
            sensors={appendixSensors}
            collisionDetection={closestCenter}
            onDragEnd={handleAppendixDragEnd}
          >
            <SortableContext
              items={appendices.map((a) => a.id)}
              strategy={verticalListSortingStrategy}
            >
              {appendices.map((appendix) => (
                <div key={appendix.id} className="relative">
                  <SortableAppendixItem
                    appendix={appendix}
                    isActive={activeAppendix === appendix.id}
                    onSelect={() => setActiveAppendix(appendix.id)}
                    onRemove={() => handleConfirmDelete(appendix.id, removeAppendix)}
                  />
                  {confirmDeleteId === appendix.id && (
                    <div className="absolute right-0 top-0 z-10 rounded bg-red-600 px-2 py-1 text-xs text-white shadow-md">
                      Nogmaals klikken om te verwijderen
                    </div>
                  )}
                </div>
              ))}
            </SortableContext>
          </DndContext>
        </nav>
      </div>

      {/* Footer with connection indicator */}
      <div className="border-t border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <p className="text-xs text-gray-400">
            {sections.length} sectie{sections.length !== 1 ? 's' : ''} &middot;{' '}
            {appendices.length > 0 && (
              <>{appendices.length} bijlage{appendices.length !== 1 ? 'n' : ''} &middot; </>
            )}
            {totalBlocks} blocks
          </p>
          <div className="flex items-center gap-1.5">
            <span
              className={`h-2 w-2 rounded-full ${
                checking
                  ? 'bg-amber-400'
                  : connected
                    ? 'bg-green-400'
                    : 'bg-red-400'
              }`}
            />
            <span className="text-[10px] text-gray-400">
              {checking
                ? 'Verbinden...'
                : connected
                  ? `v${backendVersion}`
                  : 'Offline'}
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}
