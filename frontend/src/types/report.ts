/**
 * TypeScript types afgeleid uit schemas/report.schema.json
 * Uitgebreid voor renderer_v2 compatibiliteit.
 */

// ---------- Enums & literals ----------

export type Format = 'A4' | 'A3';
export type Orientation = 'portrait' | 'landscape';
export type Status = 'CONCEPT' | 'DEFINITIEF' | 'REVISIE';
export type TableStyle = 'default' | 'minimal' | 'striped';
export type ImageAlignment = 'left' | 'center' | 'right';
export type MapLayer = 'percelen' | 'bebouwing' | 'bestemmingsplan' | 'luchtfoto';
export type CheckResult = 'VOLDOET' | 'VOLDOET NIET';
export type ImageMediaType = 'image/png' | 'image/jpeg' | 'image/svg+xml';

// ---------- Image source ----------

export interface ImageSourceBase64 {
  data: string;
  media_type: ImageMediaType;
  filename?: string;
}

export type ImageSource = string | ImageSourceBase64;

// ---------- Cover ----------

export interface Cover {
  subtitle?: string;
  image?: ImageSource;
  extra_fields?: Record<string, string>;
}

// ---------- Colofon ----------

export interface RevisionEntry {
  version: string;
  date: string;
  author?: string;
  description: string;
}

export interface Colofon {
  enabled?: boolean;
  // Renderer_v2 specifieke velden:
  opdrachtgever_contact?: string;
  opdrachtgever_naam?: string;
  opdrachtgever_adres?: string;
  adviseur_bedrijf?: string;
  adviseur_naam?: string;
  normen?: string;
  documentgegevens?: string;
  datum?: string;
  fase?: string;
  status_colofon?: string;
  kenmerk?: string;
  // Adviseur profiel velden (auto-fill vanuit SSO):
  adviseur_email?: string;
  adviseur_telefoon?: string;
  adviseur_functie?: string;
  adviseur_registratie?: string;
  // Legacy:
  extra_fields?: Record<string, string>;
  revision_history?: RevisionEntry[];
  disclaimer?: string;
}

// ---------- TOC ----------

export interface TocConfig {
  enabled?: boolean;
  title?: string;
  max_depth?: number;
}

// ---------- Content blocks ----------

export interface ParagraphBlock {
  type: 'paragraph';
  text: string;    // HTML content (van Tiptap editor)
  style?: string;  // 'Normal' | 'Heading1' | 'Heading2' | 'Heading3'
}

export interface CalculationBlock {
  type: 'calculation';
  title: string;
  formula?: string;
  substitution?: string;
  result?: string;
  unit?: string;
  reference?: string;
}

export interface CheckBlock {
  type: 'check';
  description: string;
  required_value?: string;
  calculated_value?: string;
  unity_check?: number;
  limit?: number;
  result?: CheckResult;
  reference?: string;
}

export interface TableBlock {
  type: 'table';
  title?: string;
  headers: string[];
  rows: unknown[][];
  column_widths?: number[];
  style?: TableStyle;
}

export interface ImageBlock {
  type: 'image';
  src: ImageSource;
  caption?: string;
  width_mm?: number;
  alignment?: ImageAlignment;
}

export interface MapCenter {
  lat: number;
  lon: number;
}

export interface MapBBox {
  min_x?: number;
  min_y?: number;
  max_x?: number;
  max_y?: number;
}

export interface CadastralInfo {
  identificatie: string;     // "LDN03-H-8575"
  gemeentecode: string;      // "LDN03"
  gemeentenaam: string;      // "Loosduinen"
  sectie: string;            // "H"
  perceelnummer: number | string;
  grootte: number;           // m²
  weergavenaam?: string;
}

export interface MapBlock {
  type: 'map';
  address?: string;
  center?: MapCenter;
  bbox?: MapBBox;
  zoom?: number;
  layers?: MapLayer[];
  width_mm?: number;
  height_mm?: number;
  caption?: string;
  cadastral?: CadastralInfo;
}

export interface SpacerBlock {
  type: 'spacer';
  height_mm?: number;
}

export interface PageBreakBlock {
  type: 'page_break';
}

export interface BulletListBlock {
  type: 'bullet_list';
  items: string[];
}

/** Subkop (H2) — wordt ook gebruikt als sectie-delimiter in bijlagen. */
export interface Heading2Block {
  type: 'heading_2';
  number: string;    // bijv. "2.1"
  title: string;
}

export interface RawFlowableBlock {
  type: 'raw_flowable';
  class_name: string;
  kwargs?: Record<string, unknown>;
}

/** Discriminated union van alle block types */
export type ContentBlock =
  | ParagraphBlock
  | CalculationBlock
  | CheckBlock
  | TableBlock
  | ImageBlock
  | MapBlock
  | SpacerBlock
  | PageBreakBlock
  | BulletListBlock
  | Heading2Block
  | RawFlowableBlock;

/** Block types die de frontend kan aanmaken (exclusief raw_flowable) */
export type EditableBlockType = Exclude<ContentBlock['type'], 'raw_flowable'>;

// ---------- Section ----------

export interface Section {
  number?: string;  // Auto-genummerd bij export: "1", "2", etc.
  title: string;
  level?: number;
  content?: ContentBlock[];
  page_break_before?: boolean;
}

// ---------- Backcover ----------

export interface BackcoverConfig {
  enabled?: boolean;
}

// ---------- Appendix ----------

export interface AppendixSection {
  number: string;
  title: string;
  level: number;
  content: ContentBlock[];
}

export interface Appendix {
  title: string;
  number?: number;
  label?: string;              // bijv. "Bijlage 1"
  content_sections?: AppendixSection[];  // renderer_v2 sub-secties
  content?: ContentBlock[];    // legacy flat content
}

// ---------- Root report definition ----------

export interface ReportDefinition {
  template: string;
  brand?: string;
  format?: Format;
  orientation?: Orientation;
  project: string;
  project_number?: string;
  client?: string;
  author?: string;
  report_type?: string;  // "BBL-toetsingsrapportage", "Constructief adviesrapport", etc.
  date?: string;
  version?: string;
  status?: Status;
  cover?: Cover;
  colofon?: Colofon;
  toc?: TocConfig;
  sections?: Section[];
  appendices?: Appendix[];
  backcover?: BackcoverConfig;
  metadata?: Record<string, unknown>;
}

// ---------- Editor-internal types (met IDs) ----------

/** Content block met een uniek ID voor de editor */
export type EditorBlock = ContentBlock & { id: string };

/** Section met uniek ID en editor blocks */
export interface EditorSection {
  id: string;
  title: string;
  level: number;
  content: EditorBlock[];
  page_break_before: boolean;
}

/** Bijlage met uniek ID en editor blocks */
export interface EditorAppendix {
  id: string;
  title: string;
  number: number;
  content: EditorBlock[];
}

/** Volledige report state in de editor (met IDs op sections en blocks) */
export interface EditorReport {
  template: string;
  brand: string;
  format: Format;
  orientation: Orientation;
  project: string;
  project_number: string;
  client: string;
  author: string;
  report_type: string;
  date: string;
  version: string;
  status: Status;
  cover: Cover;
  colofon: Colofon;
  toc: TocConfig;
  sections: EditorSection[];
  appendices: EditorAppendix[];
  backcover: BackcoverConfig;
  metadata: Record<string, unknown>;
}
