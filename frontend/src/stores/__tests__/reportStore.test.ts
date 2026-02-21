import { describe, it, expect, beforeEach } from 'vitest';
import { useReportStore } from '../reportStore';

describe('reportStore', () => {
  beforeEach(() => {
    useReportStore.getState().reset();
  });

  describe('sections', () => {
    it('adds a new section', () => {
      useReportStore.getState().addNewSection();
      expect(useReportStore.getState().report.sections).toHaveLength(1);
    });

    it('removes a section', () => {
      useReportStore.getState().addNewSection();
      const id = useReportStore.getState().report.sections[0]!.id;
      useReportStore.getState().removeSection(id);
      expect(useReportStore.getState().report.sections).toHaveLength(0);
    });

    it('reorders sections', () => {
      useReportStore.getState().addNewSection();
      useReportStore.getState().addNewSection();
      const [a, b] = useReportStore.getState().report.sections;
      useReportStore.getState().reorderSections(0, 1);
      const reordered = useReportStore.getState().report.sections;
      expect(reordered[0]!.id).toBe(b!.id);
      expect(reordered[1]!.id).toBe(a!.id);
    });

    it('updates section title', () => {
      useReportStore.getState().addNewSection();
      const id = useReportStore.getState().report.sections[0]!.id;
      useReportStore.getState().updateSection(id, { title: 'Nieuwe titel' });
      expect(useReportStore.getState().report.sections[0]!.title).toBe('Nieuwe titel');
    });
  });

  describe('blocks', () => {
    let sectionId: string;

    beforeEach(() => {
      useReportStore.getState().addNewSection();
      sectionId = useReportStore.getState().report.sections[0]!.id;
    });

    it('adds a paragraph block', () => {
      useReportStore.getState().addNewBlock(sectionId, 'paragraph');
      const section = useReportStore.getState().report.sections[0]!;
      expect(section.content).toHaveLength(1);
      expect(section.content[0]!.type).toBe('paragraph');
    });

    it('adds a calculation block', () => {
      useReportStore.getState().addNewBlock(sectionId, 'calculation');
      const section = useReportStore.getState().report.sections[0]!;
      expect(section.content[0]!.type).toBe('calculation');
    });

    it('removes a block', () => {
      useReportStore.getState().addNewBlock(sectionId, 'paragraph');
      const blockId = useReportStore.getState().report.sections[0]!.content[0]!.id;
      useReportStore.getState().removeBlock(sectionId, blockId);
      expect(useReportStore.getState().report.sections[0]!.content).toHaveLength(0);
    });

    it('duplicates a block with new ID', () => {
      useReportStore.getState().addNewBlock(sectionId, 'paragraph');
      const originalId = useReportStore.getState().report.sections[0]!.content[0]!.id;
      useReportStore.getState().duplicateBlock(sectionId, originalId);
      const content = useReportStore.getState().report.sections[0]!.content;
      expect(content).toHaveLength(2);
      expect(content[0]!.id).not.toBe(content[1]!.id);
      expect(content[0]!.type).toBe(content[1]!.type);
    });

    it('adds a bullet_list block', () => {
      useReportStore.getState().addNewBlock(sectionId, 'bullet_list');
      const section = useReportStore.getState().report.sections[0]!;
      expect(section.content[0]!.type).toBe('bullet_list');
    });

    it('adds a heading_2 block', () => {
      useReportStore.getState().addNewBlock(sectionId, 'heading_2');
      const section = useReportStore.getState().report.sections[0]!;
      expect(section.content[0]!.type).toBe('heading_2');
    });

    it('reorders blocks', () => {
      useReportStore.getState().addNewBlock(sectionId, 'paragraph');
      useReportStore.getState().addNewBlock(sectionId, 'calculation');
      const content = useReportStore.getState().report.sections[0]!.content;
      const [a, b] = content;
      useReportStore.getState().reorderBlocks(sectionId, 0, 1);
      const reordered = useReportStore.getState().report.sections[0]!.content;
      expect(reordered[0]!.id).toBe(b!.id);
      expect(reordered[1]!.id).toBe(a!.id);
    });
  });

  describe('appendices', () => {
    it('adds and renumbers appendices', () => {
      useReportStore.getState().addNewAppendix();
      useReportStore.getState().addNewAppendix();
      const appendices = useReportStore.getState().report.appendices;
      expect(appendices).toHaveLength(2);
      expect(appendices[0]!.number).toBe(1);
      expect(appendices[1]!.number).toBe(2);
    });

    it('renumbers after removal', () => {
      useReportStore.getState().addNewAppendix();
      useReportStore.getState().addNewAppendix();
      useReportStore.getState().addNewAppendix();
      const firstId = useReportStore.getState().report.appendices[0]!.id;
      useReportStore.getState().removeAppendix(firstId);
      const appendices = useReportStore.getState().report.appendices;
      expect(appendices).toHaveLength(2);
      expect(appendices[0]!.number).toBe(1);
      expect(appendices[1]!.number).toBe(2);
    });
  });

  describe('undo/redo', () => {
    it('undoes a section add', () => {
      useReportStore.getState().addNewSection();
      expect(useReportStore.getState().report.sections).toHaveLength(1);
      useReportStore.getState().undo();
      expect(useReportStore.getState().report.sections).toHaveLength(0);
    });

    it('redoes after undo', () => {
      useReportStore.getState().addNewSection();
      useReportStore.getState().undo();
      useReportStore.getState().redo();
      expect(useReportStore.getState().report.sections).toHaveLength(1);
    });
  });

  describe('metadata', () => {
    it('sets metadata fields', () => {
      useReportStore.getState().setMetadata({
        project: 'Nieuw Project',
        project_number: '2503.30',
        status: 'DEFINITIEF',
      });
      const report = useReportStore.getState().report;
      expect(report.project).toBe('Nieuw Project');
      expect(report.project_number).toBe('2503.30');
      expect(report.status).toBe('DEFINITIEF');
    });
  });

  describe('import/export', () => {
    it('exports and re-imports without data loss', () => {
      useReportStore.getState().setMetadata({ project: 'Round Trip Test', client: 'Klant BV' });
      useReportStore.getState().addNewSection();
      const sectionId = useReportStore.getState().report.sections[0]!.id;
      useReportStore.getState().addNewBlock(sectionId, 'paragraph');

      const json = useReportStore.getState().exportJson();
      useReportStore.getState().reset();

      const result = useReportStore.getState().importJson(json);
      expect(result.ok).toBe(true);
      expect(useReportStore.getState().report.project).toBe('Round Trip Test');
      expect(useReportStore.getState().report.sections).toHaveLength(1);
    });

    it('rejects invalid JSON', () => {
      const result = useReportStore.getState().importJson('not json');
      expect(result.ok).toBe(false);
    });

    it('rejects JSON without required fields', () => {
      const result = useReportStore.getState().importJson('{"foo": "bar"}');
      expect(result.ok).toBe(false);
    });
  });
});
