/**
 * Conversie tussen het JSON schema formaat (zonder IDs) en het editor formaat (met IDs).
 * Compatibel met renderer_v2 backend.
 */
import type {
  ReportDefinition,
  EditorReport,
  EditorSection,
  EditorAppendix,
  EditorBlock,
  Section,
  Appendix,
  AppendixSection,
  ContentBlock,
  Colofon,
} from '@/types/report';
import { generateId } from './idGenerator';
import { createDefaultReport } from './defaults';
import brand from '@/config/brand';

// ==================== IMPORT (schema → editor) ====================

/** Voeg IDs toe aan een ContentBlock voor gebruik in de editor */
function toEditorBlock(block: ContentBlock): EditorBlock {
  return { ...block, id: generateId() } as EditorBlock;
}

/** Voeg IDs toe aan een Section voor gebruik in de editor */
function toEditorSection(section: Section): EditorSection {
  return {
    id: generateId(),
    title: section.title,
    level: section.level ?? 1,
    content: (section.content ?? []).map(toEditorBlock),
    page_break_before: section.page_break_before ?? false,
  };
}

/** Voeg IDs toe aan een Appendix voor gebruik in de editor.
 *  Ondersteunt zowel flat `content` als renderer_v2 `content_sections`. */
function toEditorAppendix(appendix: Appendix, index: number): EditorAppendix {
  let blocks: EditorBlock[];

  if (appendix.content_sections && appendix.content_sections.length > 0) {
    // Flatten content_sections → flat editor blocks
    blocks = flattenAppendixSections(appendix.content_sections);
  } else {
    blocks = (appendix.content ?? []).map(toEditorBlock);
  }

  return {
    id: generateId(),
    title: appendix.title,
    number: appendix.number ?? index + 1,
    content: blocks,
  };
}

/** Flatten AppendixSection[] → EditorBlock[].
 *  Elke section wordt een heading_2 block gevolgd door de content blocks. */
function flattenAppendixSections(sections: AppendixSection[]): EditorBlock[] {
  const blocks: EditorBlock[] = [];
  for (const section of sections) {
    // Voeg een heading_2 block toe voor de sectietitel
    blocks.push({
      id: generateId(),
      type: 'heading_2',
      number: section.number,
      title: section.title,
    } as EditorBlock);
    // Voeg de content blocks toe
    for (const block of section.content) {
      blocks.push(toEditorBlock(block));
    }
  }
  return blocks;
}

/** Converteer een ReportDefinition (schema JSON) naar EditorReport (met IDs en defaults) */
export function toEditorReport(def: ReportDefinition): EditorReport {
  const defaults = createDefaultReport();
  return {
    template: def.template,
    brand: def.brand ?? defaults.brand,
    format: def.format ?? defaults.format,
    orientation: def.orientation ?? defaults.orientation,
    project: def.project,
    project_number: def.project_number ?? defaults.project_number,
    client: def.client ?? defaults.client,
    author: def.author ?? defaults.author,
    report_type: def.report_type ?? defaults.report_type,
    date: def.date ?? defaults.date,
    version: def.version ?? defaults.version,
    status: def.status ?? defaults.status,
    cover: def.cover ?? defaults.cover,
    colofon: def.colofon ?? defaults.colofon,
    toc: def.toc ?? defaults.toc,
    sections: (def.sections ?? []).map(toEditorSection),
    appendices: (def.appendices ?? []).map(toEditorAppendix),
    backcover: def.backcover ?? defaults.backcover,
    metadata: def.metadata ?? defaults.metadata,
  };
}

// ==================== EXPORT (editor → schema) ====================

/** Strip IDs van een EditorBlock terug naar schema ContentBlock */
function toSchemaBlock(block: EditorBlock): ContentBlock {
  const { id: _id, ...rest } = block;
  return rest as ContentBlock;
}

/** Strip IDs van een EditorSection terug naar schema Section.
 *  Voegt automatisch section number toe (1-indexed). */
function toSchemaSection(section: EditorSection, index: number): Section {
  const result: Section = {
    number: String(index + 1),
    title: section.title,
  };
  if (section.level !== 1) result.level = section.level;
  if (section.content.length > 0) result.content = section.content.map(toSchemaBlock);
  if (section.page_break_before) result.page_break_before = true;
  return result;
}

/** Converteer flat editor blocks naar AppendixSection[].
 *  Elke heading_2 block start een nieuwe content_section.
 *  Blocks voor de eerste heading_2 komen in een "default" section. */
function toContentSections(blocks: EditorBlock[]): AppendixSection[] {
  const sections: AppendixSection[] = [];
  let currentSection: AppendixSection | null = null;

  for (const block of blocks) {
    if (block.type === 'heading_2') {
      // Start nieuwe section
      currentSection = {
        number: block.number,
        title: block.title,
        level: 1,
        content: [],
      };
      sections.push(currentSection);
    } else {
      if (!currentSection) {
        // Blocks voor eerste heading → default section
        currentSection = {
          number: 'B0',
          title: 'Inhoud',
          level: 1,
          content: [],
        };
        sections.push(currentSection);
      }
      currentSection.content.push(toSchemaBlock(block));
    }
  }

  return sections;
}

/** Strip IDs van een EditorAppendix terug naar schema Appendix.
 *  Exporteert als content_sections voor renderer_v2. */
function toSchemaAppendix(appendix: EditorAppendix): Appendix {
  const result: Appendix = {
    number: appendix.number,
    label: `Bijlage ${appendix.number}`,
    title: appendix.title,
  };

  if (appendix.content.length > 0) {
    const sections = toContentSections(appendix.content);
    if (sections.length > 0) {
      result.content_sections = sections;
    }
  }

  return result;
}

/** Filter colofon: verwijder lege velden en enabled-only objecten */
function buildColofon(colofon: Colofon): Colofon | undefined {
  const result: Colofon = {};
  let hasContent = false;

  if (colofon.enabled !== undefined) { result.enabled = colofon.enabled; hasContent = true; }
  if (colofon.opdrachtgever_contact) { result.opdrachtgever_contact = colofon.opdrachtgever_contact; hasContent = true; }
  if (colofon.opdrachtgever_naam) { result.opdrachtgever_naam = colofon.opdrachtgever_naam; hasContent = true; }
  if (colofon.opdrachtgever_adres) { result.opdrachtgever_adres = colofon.opdrachtgever_adres; hasContent = true; }
  if (colofon.adviseur_bedrijf) { result.adviseur_bedrijf = colofon.adviseur_bedrijf; hasContent = true; }
  if (colofon.adviseur_naam) { result.adviseur_naam = colofon.adviseur_naam; hasContent = true; }
  if (colofon.adviseur_email) { result.adviseur_email = colofon.adviseur_email; hasContent = true; }
  if (colofon.adviseur_telefoon) { result.adviseur_telefoon = colofon.adviseur_telefoon; hasContent = true; }
  if (colofon.adviseur_functie) { result.adviseur_functie = colofon.adviseur_functie; hasContent = true; }
  if (colofon.adviseur_registratie) { result.adviseur_registratie = colofon.adviseur_registratie; hasContent = true; }
  if (colofon.normen) { result.normen = colofon.normen; hasContent = true; }
  if (colofon.documentgegevens) { result.documentgegevens = colofon.documentgegevens; hasContent = true; }
  if (colofon.datum) { result.datum = colofon.datum; hasContent = true; }
  if (colofon.fase) { result.fase = colofon.fase; hasContent = true; }
  if (colofon.status_colofon) { result.status_colofon = colofon.status_colofon; hasContent = true; }
  if (colofon.kenmerk) { result.kenmerk = colofon.kenmerk; hasContent = true; }
  if (colofon.disclaimer) { result.disclaimer = colofon.disclaimer; hasContent = true; }
  if (colofon.revision_history && colofon.revision_history.length > 0) {
    result.revision_history = colofon.revision_history;
    hasContent = true;
  }
  // Legacy extra_fields
  if (colofon.extra_fields && Object.keys(colofon.extra_fields).length > 0) {
    result.extra_fields = colofon.extra_fields;
    hasContent = true;
  }

  return hasContent ? result : undefined;
}

/** Converteer een EditorReport terug naar schema-conforme ReportDefinition */
export function toReportDefinition(report: EditorReport): ReportDefinition {
  const def: ReportDefinition = {
    template: report.template,
    project: report.project,
  };

  if (report.brand) def.brand = report.brand;
  if (report.format !== 'A4') def.format = report.format;
  if (report.orientation !== 'portrait') def.orientation = report.orientation;
  if (report.project_number) def.project_number = report.project_number;
  if (report.client) def.client = report.client;
  if (report.author && report.author !== brand.fullName) def.author = report.author;
  if (report.report_type) def.report_type = report.report_type;
  if (report.date) def.date = report.date;
  if (report.version && report.version !== '1.0') def.version = report.version;
  if (report.status && report.status !== 'CONCEPT') def.status = report.status;

  if (Object.keys(report.cover).length > 0) def.cover = report.cover;

  const colofon = buildColofon(report.colofon);
  if (colofon) def.colofon = colofon;

  if (report.toc.enabled !== undefined) def.toc = report.toc;
  if (report.sections.length > 0) def.sections = report.sections.map(toSchemaSection);
  if (report.appendices.length > 0) def.appendices = report.appendices.map(toSchemaAppendix);
  if (report.backcover.enabled !== undefined) def.backcover = report.backcover;
  if (Object.keys(report.metadata).length > 0) def.metadata = report.metadata;

  return def;
}
