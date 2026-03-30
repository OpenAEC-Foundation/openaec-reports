import { useState, useEffect, useRef, useCallback } from 'react';
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
import type { MetadataPanel } from '@/stores/reportStore';
import { BlockIcon } from '@/components/shared/BlockIcons';
import type { EditorSection, EditorAppendix } from '@/types/report';

const SIDEBAR_MIN_WIDTH = 200;
const SIDEBAR_MAX_WIDTH = 480;
const SIDEBAR_DEFAULT_WIDTH = 288; // w-72
const SIDEBAR_STORAGE_KEY = "openaec-sidebar-width";

function loadSidebarWidth(): number {
  try {
    const stored = localStorage.getItem(SIDEBAR_STORAGE_KEY);
    if (stored) {
      const w = parseInt(stored, 10);
      if (w >= SIDEBAR_MIN_WIDTH && w <= SIDEBAR_MAX_WIDTH) return w;
    }
  } catch {
    // localStorage not available
  }
  return SIDEBAR_DEFAULT_WIDTH;
}

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

// ---------- Sidebar navigation items ----------

interface SidebarNavItem {
  id: MetadataPanel;
  label: string;
  icon: JSX.Element;
}

const NAV_ITEMS: SidebarNavItem[] = [
  {
    id: 'rapport',
    label: 'Rapport',
    icon: (
      <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.298 1.466l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 010 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.298 1.466l-1.296 2.247a1.125 1.125 0 01-1.37.49l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.298-1.466l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 010-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 01-.298-1.466l1.297-2.247a1.125 1.125 0 011.37-.49l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
  {
    id: 'voorblad',
    label: 'Voorblad',
    icon: (
      <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5A1.5 1.5 0 0021.75 19.5V4.5A1.5 1.5 0 0020.25 3H3.75A1.5 1.5 0 002.25 4.5v15A1.5 1.5 0 003.75 21z" />
      </svg>
    ),
  },
  {
    id: 'colofon',
    label: 'Colofon',
    icon: (
      <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
      </svg>
    ),
  },
  {
    id: 'opties',
    label: 'Opties',
    icon: (
      <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75" />
      </svg>
    ),
  },
];

// ---------- Sortable section item ----------

interface SortableSectionItemProps {
  section: EditorSection;
  chapterNumber: number;
  isActive: boolean;
  isCollapsed: boolean;
  onSelect: () => void;
  onRemove: () => void;
  onToggleCollapse: () => void;
}

function SortableSectionItem({ section, chapterNumber, isActive, isCollapsed, onSelect, onRemove, onToggleCollapse }: SortableSectionItemProps) {
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
          ? 'bg-oaec-hover-strong text-oaec-accent'
          : 'text-oaec-text-secondary hover:bg-oaec-hover'
      }`}
    >
      {/* Collapse chevron */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onToggleCollapse();
        }}
        className="mt-2 flex h-5 w-5 shrink-0 items-center justify-center rounded text-oaec-text-muted hover:text-oaec-text transition-transform"
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
        className="mt-2 flex h-5 w-5 shrink-0 cursor-grab items-center justify-center rounded text-oaec-text-faint hover:text-oaec-text-muted active:cursor-grabbing"
        {...attributes}
        {...listeners}
        aria-label="Versleep hoofdstuk"
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
          className={`mt-0.5 flex h-5 min-w-[1.25rem] shrink-0 items-center justify-center rounded text-xs font-bold ${
            isActive
              ? 'bg-oaec-accent-soft text-oaec-accent'
              : 'bg-oaec-hover text-oaec-text-muted'
          }`}
        >
          {chapterNumber}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="truncate font-medium">{section.title}</p>
            {isCollapsed && section.content.length > 0 && (
              <span className="shrink-0 rounded-full bg-oaec-hover px-1.5 py-0.5 text-[10px] font-medium text-oaec-text-muted">
                {section.content.length}
              </span>
            )}
          </div>
          {!isCollapsed && (
            <div className="mt-0.5 flex flex-wrap gap-1">
              <span className="text-xs text-oaec-text-faint">
                {blockCountLabel(section.content.length)}
              </span>
              {section.content.slice(0, 4).map((block) => (
                <span
                  key={block.id}
                  className="inline-flex items-center rounded bg-oaec-hover px-1 py-0.5 text-oaec-text-muted"
                  title={BLOCK_TYPE_LABELS[block.type] ?? block.type}
                >
                  <BlockIcon type={block.type} className="h-3 w-3" />
                </span>
              ))}
              {section.content.length > 4 && (
                <span className="text-[10px] text-oaec-text-faint">
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
        className="mr-1 mt-2 flex h-5 w-5 shrink-0 items-center justify-center rounded text-oaec-text-faint opacity-0 transition-opacity hover:bg-oaec-danger-soft hover:text-oaec-danger group-hover:opacity-100"
        aria-label="Verwijder hoofdstuk"
        title="Verwijder hoofdstuk"
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
          ? 'bg-oaec-hover-strong text-oaec-accent'
          : 'text-oaec-text-secondary hover:bg-oaec-hover'
      }`}
    >
      {/* Drag handle */}
      <button
        className="mt-2 flex h-5 w-5 shrink-0 cursor-grab items-center justify-center rounded text-oaec-text-faint hover:text-oaec-text-muted active:cursor-grabbing"
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
              ? 'bg-oaec-accent-soft text-oaec-accent'
              : 'bg-oaec-hover text-oaec-text-muted'
          }`}
        >
          {appendix.number}
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate font-medium">{appendix.title}</p>
          {appendix.content.length > 0 && (
            <div className="mt-0.5 flex flex-wrap gap-1">
              <span className="text-xs text-oaec-text-faint">
                {blockCountLabel(appendix.content.length)}
              </span>
              {appendix.content.slice(0, 4).map((block) => (
                <span
                  key={block.id}
                  className="inline-flex items-center rounded bg-oaec-hover px-1 py-0.5 text-oaec-text-muted"
                  title={BLOCK_TYPE_LABELS[block.type] ?? block.type}
                >
                  <BlockIcon type={block.type} className="h-3 w-3" />
                </span>
              ))}
              {appendix.content.length > 4 && (
                <span className="text-[10px] text-oaec-text-faint">
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
        className="mr-1 mt-2 flex h-5 w-5 shrink-0 items-center justify-center rounded text-oaec-text-faint opacity-0 transition-opacity hover:bg-oaec-danger-soft hover:text-oaec-danger group-hover:opacity-100"
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
  const fieldGroups = useReportStore((s) => s.report.field_groups);
  const activeSection = useReportStore((s) => s.activeSection);
  const activeAppendix = useReportStore((s) => s.activeAppendix);
  const activeFieldGroup = useReportStore((s) => s.activeFieldGroup);
  const activePanel = useReportStore((s) => s.activePanel);
  const setActiveSection = useReportStore((s) => s.setActiveSection);
  const setActiveAppendix = useReportStore((s) => s.setActiveAppendix);
  const setActiveFieldGroup = useReportStore((s) => s.setActiveFieldGroup);
  const setActivePanel = useReportStore((s) => s.setActivePanel);
  const addNewSection = useReportStore((s) => s.addNewSection);
  const removeSection = useReportStore((s) => s.removeSection);
  const reorderSections = useReportStore((s) => s.reorderSections);
  const addNewAppendix = useReportStore((s) => s.addNewAppendix);
  const removeAppendix = useReportStore((s) => s.removeAppendix);
  const reorderAppendices = useReportStore((s) => s.reorderAppendices);
  const project = useReportStore((s) => s.report.project);
  const status = useReportStore((s) => s.report.status);

  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

  // Resizable sidebar
  const [width, setWidth] = useState(loadSidebarWidth);
  const isResizing = useRef(false);
  const startX = useRef(0);
  const startWidth = useRef(0);
  const widthRef = useRef(width);
  widthRef.current = width;

  useEffect(() => {
    function handleResizeMove(e: MouseEvent) {
      if (!isResizing.current) return;
      const delta = e.clientX - startX.current;
      const newWidth = Math.min(
        SIDEBAR_MAX_WIDTH,
        Math.max(SIDEBAR_MIN_WIDTH, startWidth.current + delta)
      );
      setWidth(newWidth);
    }

    function handleResizeEnd() {
      if (!isResizing.current) return;
      isResizing.current = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      try {
        localStorage.setItem(SIDEBAR_STORAGE_KEY, String(widthRef.current));
      } catch {
        // localStorage not available
      }
    }

    window.addEventListener("mousemove", handleResizeMove);
    window.addEventListener("mouseup", handleResizeEnd);
    return () => {
      window.removeEventListener("mousemove", handleResizeMove);
      window.removeEventListener("mouseup", handleResizeEnd);
    };
  }, []);

  const handleResizeStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    isResizing.current = true;
    startX.current = e.clientX;
    startWidth.current = widthRef.current;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  }, []);

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

  const isNavActive = activeSection === null && activeAppendix === null && activeFieldGroup === null;

  return (
    <aside
      className="relative flex h-full flex-col border-r border-oaec-border-subtle bg-oaec-bg"
      style={{ width, minWidth: SIDEBAR_MIN_WIDTH, maxWidth: SIDEBAR_MAX_WIDTH }}
    >
      {/* Header */}
      <div className="border-b border-oaec-border-subtle px-4 py-3">
        {project ? (
          <p className="text-sm font-medium text-oaec-text truncate">{project}</p>
        ) : (
          <p className="text-sm text-oaec-text-faint italic">Geen project</p>
        )}
        {status && (
          <span
            className={`mt-1 inline-block rounded px-1.5 py-0.5 text-xs font-medium ${
              status === 'DEFINITIEF'
                ? 'text-oaec-success'
                : status === 'REVISIE'
                  ? 'text-oaec-accent'
                  : 'text-oaec-text-muted'
            }`}
            style={{
              background: status === 'DEFINITIEF'
                ? 'var(--oaec-success-soft)'
                : status === 'REVISIE'
                  ? 'var(--oaec-accent-soft)'
                  : 'var(--oaec-hover)',
            }}
          >
            {status}
          </span>
        )}
      </div>

      {/* Scrollable area */}
      <div className="flex-1 overflow-y-auto">
        {/* Navigation items: Rapport, Voorblad, Colofon, Opties */}
        <nav className="px-2 pt-2 pb-1 space-y-0.5">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              onClick={() => setActivePanel(item.id)}
              className={`w-full flex items-center gap-2 rounded-md px-2 py-2 text-sm transition-colors ${
                isNavActive && activePanel === item.id
                  ? 'bg-oaec-hover-strong text-oaec-accent font-medium'
                  : 'text-oaec-text-secondary hover:bg-oaec-hover'
              }`}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </nav>

        {/* Field groups (BIC / template-driven forms) */}
        {fieldGroups.length > 0 && (
          <>
            <div className="mx-4 my-1 border-t border-oaec-border-subtle" />
            <div className="flex items-center justify-between px-4 pt-2 pb-1">
              <p className="text-xs font-semibold text-oaec-text-faint uppercase tracking-wider">
                Formulier
              </p>
              <span className="text-[10px] text-oaec-text-faint">
                {fieldGroups.length} groepen
              </span>
            </div>
            <nav className="px-2 py-1 space-y-0.5">
              {fieldGroups.map((group) => (
                <button
                  key={group.key}
                  onClick={() => setActiveFieldGroup(group.key)}
                  className={`w-full flex items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors text-left ${
                    activeFieldGroup === group.key
                      ? 'bg-oaec-hover-strong text-oaec-accent font-medium'
                      : 'text-oaec-text-secondary hover:bg-oaec-hover'
                  }`}
                >
                  {group.type === 'table' ? (
                    <svg className="h-3.5 w-3.5 shrink-0 text-oaec-text-faint" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0112 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M2.25 5.625v1.5c0 .621.504 1.125 1.125 1.125m0 0h17.25m-17.25 0h7.5c.621 0 1.125.504 1.125 1.125M3.375 8.25c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m17.25-3.75h-7.5c-.621 0-1.125.504-1.125 1.125m8.625-1.125c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125M12 10.875v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 10.875c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125M13.125 12h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125M20.625 12c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5M12 14.625v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 14.625c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125m0 0v1.5c0 .621-.504 1.125-1.125 1.125" />
                    </svg>
                  ) : (
                    <svg className="h-3.5 w-3.5 shrink-0 text-oaec-text-faint" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
                    </svg>
                  )}
                  <span className="truncate">{group.label}</span>
                </button>
              ))}
            </nav>
          </>
        )}

        {/* Divider */}
        <div className="mx-4 my-1 border-t border-oaec-border-subtle" />

        {/* Chapter list header + add button */}
        <div className="flex items-center justify-between px-4 pt-2 pb-1">
          <p className="text-xs font-semibold text-oaec-text-faint uppercase tracking-wider">
            Hoofdstukken
          </p>
          <button
            onClick={() => addNewSection()}
            className="flex items-center gap-1 rounded px-1.5 py-0.5 text-xs text-oaec-text-faint hover:bg-oaec-hover hover:text-oaec-accent transition-colors"
            title="Hoofdstuk toevoegen"
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
              <div className="rounded-full bg-oaec-hover p-3 mb-3">
                <svg className="h-6 w-6 text-oaec-text-faint" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
              </div>
              <p className="text-sm text-oaec-text-muted">Geen hoofdstukken</p>
              <button
                onClick={() => addNewSection()}
                className="mt-2 text-sm text-oaec-accent hover:text-oaec-accent-hover font-medium"
              >
                Eerste hoofdstuk toevoegen
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
              {sections.map((section, index) => (
                <div key={section.id} className="relative">
                  <SortableSectionItem
                    section={section}
                    chapterNumber={index + 1}
                    isActive={activeSection === section.id}
                    isCollapsed={collapsed.has(section.id)}
                    onSelect={() => setActiveSection(section.id)}
                    onRemove={() => handleConfirmDelete(section.id, removeSection)}
                    onToggleCollapse={() => toggleCollapse(section.id)}
                  />
                  {confirmDeleteId === section.id && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        removeSection(section.id);
                        setConfirmDeleteId(null);
                      }}
                      className="absolute right-7 top-1 z-10 rounded px-2 py-1 text-xs shadow-md transition-colors cursor-pointer"
                      style={{ background: 'var(--oaec-danger)', color: 'var(--oaec-accent-text)' }}
                    >
                      Klik om te verwijderen
                    </button>
                  )}
                </div>
              ))}
            </SortableContext>
          </DndContext>
        </nav>

        {/* Divider between chapters and appendices */}
        <div className="mx-4 my-1 border-t border-oaec-border-subtle" />

        {/* Appendix list header + add button */}
        <div className="flex items-center justify-between px-4 pt-2 pb-1">
          <p className="text-xs font-semibold text-oaec-text-faint uppercase tracking-wider">
            Bijlagen
          </p>
          <button
            onClick={() => addNewAppendix()}
            className="flex items-center gap-1 rounded px-1.5 py-0.5 text-xs text-oaec-text-faint hover:bg-oaec-hover hover:text-oaec-accent transition-colors"
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
              <p className="text-sm text-oaec-text-faint italic">Geen bijlagen</p>
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
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        removeAppendix(appendix.id);
                        setConfirmDeleteId(null);
                      }}
                      className="absolute right-7 top-1 z-10 rounded px-2 py-1 text-xs shadow-md transition-colors cursor-pointer"
                      style={{ background: 'var(--oaec-danger)', color: 'var(--oaec-accent-text)' }}
                    >
                      Klik om te verwijderen
                    </button>
                  )}
                </div>
              ))}
            </SortableContext>
          </DndContext>
        </nav>
      </div>

      {/* Resize handle */}
      <div
        onMouseDown={handleResizeStart}
        className="absolute right-0 top-0 h-full w-1 cursor-col-resize hover:bg-brand-primary/30 active:bg-brand-primary/50 transition-colors z-10"
      />
    </aside>
  );
}
