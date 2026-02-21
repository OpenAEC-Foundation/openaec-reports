import { describe, it, expect } from 'vitest';
import { toEditorReport, toReportDefinition } from '../conversion';
import type { ReportDefinition } from '@/types/report';

const MINIMAL: ReportDefinition = {
  template: 'openaec-bbl',
  project: 'Test Project',
};

const FULL: ReportDefinition = {
  template: 'openaec-bbl',
  project: 'Test Project',
  project_number: '2503.30',
  client: 'Opdrachtgever BV',
  author: 'Ir. J. Test',
  report_type: 'Constructief adviesrapport',
  date: '2025-03-01',
  version: '2.0',
  status: 'DEFINITIEF',
  format: 'A4',
  orientation: 'portrait',
  cover: {
    subtitle: 'Constructief rapport',
    extra_fields: { 'Kenmerk': 'ABC-123' },
  },
  colofon: {
    enabled: true,
    opdrachtgever_contact: 'Dhr. P. van der Berg',
    opdrachtgever_naam: 'Bedrijfsnaam B.V.',
    adviseur_bedrijf: 'OpenAEC',
    adviseur_naam: 'Ir. S. de Vries',
    normen: 'Eurocode, NEN-EN 1990',
    fase: 'Definitief Ontwerp',
    kenmerk: '2801-CA-01',
    disclaimer: 'Standaard disclaimer',
    revision_history: [
      { version: '1.0', date: '2025-01-01', description: 'Eerste versie' },
      { version: '2.0', date: '2025-03-01', author: 'JT', description: 'Revisie' },
    ],
  },
  toc: { enabled: true, title: 'Inhoudsopgave', max_depth: 3 },
  sections: [
    {
      title: 'Inleiding',
      level: 1,
      content: [
        { type: 'paragraph', text: 'Dit is een <b>test</b> paragraaf.' },
        { type: 'bullet_list', items: ['Item A', 'Item B', 'Item C'] },
        { type: 'heading_2', number: '1.1', title: 'Subtitel' },
        { type: 'calculation', title: 'Calc 1', formula: 'F = m * a', result: '100', unit: 'kN' },
      ],
    },
    {
      title: 'Toetsing',
      level: 1,
      page_break_before: true,
      content: [
        { type: 'check', description: 'UC toets', unity_check: 0.85, limit: 1.0, result: 'VOLDOET' },
        { type: 'table', headers: ['Kolom A', 'Kolom B'], rows: [[1, 'x'], [2, 'y']] },
        { type: 'spacer', height_mm: 10 },
        { type: 'page_break' },
        { type: 'image', src: 'test.png', caption: 'Figuur 1' },
      ],
    },
  ],
  appendices: [
    {
      title: 'Bijlage A',
      number: 1,
      label: 'Bijlage 1',
      content_sections: [
        {
          number: 'B1',
          title: 'Sonderingsgegevens',
          level: 1,
          content: [{ type: 'paragraph', text: 'Bijlage inhoud' }],
        },
      ],
    },
  ],
  backcover: { enabled: true },
};

describe('conversion round-trip', () => {
  it('round-trips a minimal report', () => {
    const editor = toEditorReport(MINIMAL);
    const output = toReportDefinition(editor);
    expect(output.template).toBe(MINIMAL.template);
    expect(output.project).toBe(MINIMAL.project);
  });

  it('round-trips a full report preserving all data', () => {
    const editor = toEditorReport(FULL);
    const output = toReportDefinition(editor);

    // Top-level fields
    expect(output.template).toBe(FULL.template);
    expect(output.project).toBe(FULL.project);
    expect(output.project_number).toBe(FULL.project_number);
    expect(output.client).toBe(FULL.client);
    expect(output.status).toBe(FULL.status);
    expect(output.report_type).toBe(FULL.report_type);

    // Cover
    expect(output.cover?.subtitle).toBe(FULL.cover?.subtitle);
    expect(output.cover?.extra_fields).toEqual(FULL.cover?.extra_fields);

    // Colofon — specific fields
    expect(output.colofon?.opdrachtgever_contact).toBe('Dhr. P. van der Berg');
    expect(output.colofon?.adviseur_naam).toBe('Ir. S. de Vries');
    expect(output.colofon?.normen).toBe('Eurocode, NEN-EN 1990');
    expect(output.colofon?.kenmerk).toBe('2801-CA-01');
    expect(output.colofon?.revision_history).toHaveLength(2);
    expect(output.colofon?.disclaimer).toBe(FULL.colofon?.disclaimer);

    // Sections — with auto-numbering
    expect(output.sections).toHaveLength(2);
    expect(output.sections![0]!.number).toBe('1');
    expect(output.sections![0]!.title).toBe('Inleiding');
    expect(output.sections![0]!.content).toHaveLength(4);
    expect(output.sections![1]!.number).toBe('2');
    expect(output.sections![1]!.page_break_before).toBe(true);

    // Block content preserved
    const para = output.sections![0]!.content![0]!;
    expect(para.type).toBe('paragraph');
    if (para.type === 'paragraph') {
      expect(para.text).toBe('Dit is een <b>test</b> paragraaf.');
    }

    // Appendices — with content_sections and label
    expect(output.appendices).toHaveLength(1);
    expect(output.appendices![0]!.title).toBe('Bijlage A');
    expect(output.appendices![0]!.label).toBe('Bijlage 1');
    expect(output.appendices![0]!.content_sections).toHaveLength(1);
    expect(output.appendices![0]!.content_sections![0]!.number).toBe('B1');

    // Backcover
    expect(output.backcover?.enabled).toBe(true);
  });

  it('preserves bullet_list and heading_2 blocks', () => {
    const editor = toEditorReport(FULL);
    const output = toReportDefinition(editor);
    const content = output.sections![0]!.content!;

    const bulletList = content.find((b) => b.type === 'bullet_list');
    expect(bulletList).toBeDefined();
    if (bulletList && bulletList.type === 'bullet_list') {
      expect(bulletList.items).toEqual(['Item A', 'Item B', 'Item C']);
    }

    const heading = content.find((b) => b.type === 'heading_2');
    expect(heading).toBeDefined();
    if (heading && heading.type === 'heading_2') {
      expect(heading.number).toBe('1.1');
      expect(heading.title).toBe('Subtitel');
    }
  });

  it('strips editor IDs from output', () => {
    const editor = toEditorReport(FULL);
    const output = toReportDefinition(editor);
    const json = JSON.stringify(output);
    for (const section of editor.sections) {
      expect(json).not.toContain(`"id":"${section.id}"`);
      for (const block of section.content) {
        expect(json).not.toContain(`"id":"${block.id}"`);
      }
    }
  });

  it('assigns unique IDs to editor sections and blocks', () => {
    const editor = toEditorReport(FULL);
    const allIds = new Set<string>();
    for (const section of editor.sections) {
      expect(allIds.has(section.id)).toBe(false);
      allIds.add(section.id);
      for (const block of section.content) {
        expect(allIds.has(block.id)).toBe(false);
        allIds.add(block.id);
      }
    }
    for (const appendix of editor.appendices) {
      expect(allIds.has(appendix.id)).toBe(false);
      allIds.add(appendix.id);
    }
  });

  it('flattens content_sections on import and reconstructs on export', () => {
    const editor = toEditorReport(FULL);
    // Import: appendix content_sections → flat blocks with heading_2
    const appendix = editor.appendices[0]!;
    expect(appendix.content.length).toBe(2); // 1 heading_2 + 1 paragraph
    expect(appendix.content[0]!.type).toBe('heading_2');
    expect(appendix.content[1]!.type).toBe('paragraph');

    // Export: flat blocks → content_sections
    const output = toReportDefinition(editor);
    const sections = output.appendices![0]!.content_sections!;
    expect(sections).toHaveLength(1);
    expect(sections[0]!.content).toHaveLength(1);
    expect(sections[0]!.content[0]!.type).toBe('paragraph');
  });
});
