import type {
  EditorReport,
  EditorSection,
  EditorAppendix,
  EditorBlock,
  ContentBlock,
  EditableBlockType,
  ParagraphBlock,
  CalculationBlock,
  CheckBlock,
  TableBlock,
  ImageBlock,
  MapBlock,
  SpacerBlock,
  PageBreakBlock,
  BulletListBlock,
  Heading2Block,
  SpreadsheetBlock,
} from '@/types/report';
import { generateId } from './idGenerator';
export function createDefaultReport(): EditorReport {
  return {
    template: 'custom',
    brand: '',
    format: 'A4',
    orientation: 'portrait',
    project: '',
    project_number: '',
    client: '',
    author: '',
    report_type: '',
    date: new Date().toISOString().slice(0, 10),
    version: '1.0',
    status: 'CONCEPT',
    cover: {},
    colofon: { enabled: true, revision_history: [] },
    toc: { enabled: true, title: 'Inhoudsopgave', max_depth: 3 },
    sections: [],
    appendices: [],
    backcover: { enabled: true },
    metadata: {},
    field_groups: [],
    flat_data: {},
  };
}

export function createDefaultSection(overrides?: Partial<EditorSection>): EditorSection {
  return {
    id: generateId(),
    title: 'Nieuwe sectie',
    level: 1,
    content: [],
    page_break_before: false,
    ...overrides,
  };
}

export function createDefaultAppendix(overrides?: Partial<EditorAppendix>): EditorAppendix {
  return {
    id: generateId(),
    title: 'Nieuwe bijlage',
    number: 0,
    content: [],
    ...overrides,
  };
}

const blockDefaults: Record<EditableBlockType, () => ContentBlock> = {
  paragraph: (): ParagraphBlock => ({ type: 'paragraph', text: '' }),
  calculation: (): CalculationBlock => ({ type: 'calculation', title: '' }),
  check: (): CheckBlock => ({ type: 'check', description: '', limit: 1.0 }),
  table: (): TableBlock => ({ type: 'table', headers: ['Kolom 1', 'Kolom 2'], rows: [['', '']] }),
  spreadsheet: (): SpreadsheetBlock => ({
    type: 'spreadsheet',
    title: '',
    headers: ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'],
    rows: Array.from({ length: 25 }, () => Array(10).fill('') as string[]),
    column_widths: Array(10).fill(34) as number[],
    show_grid: true,
    zebra: false,
  }),
  image: (): ImageBlock => ({ type: 'image', src: '', alignment: 'center' }),
  map: (): MapBlock => ({ type: 'map', address: '', layers: ['percelen'], zoom: 16 }),
  spacer: (): SpacerBlock => ({ type: 'spacer', height_mm: 5 }),
  page_break: (): PageBreakBlock => ({ type: 'page_break' }),
  bullet_list: (): BulletListBlock => ({ type: 'bullet_list', items: [''] }),
  heading_2: (): Heading2Block => ({ type: 'heading_2', number: '', title: '' }),
};

export function createDefaultBlock(blockType: EditableBlockType): EditorBlock {
  const factory = blockDefaults[blockType];
  return { ...factory(), id: generateId() } as EditorBlock;
}
