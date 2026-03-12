/**
 * TypeScript interfaces voor page_type YAML structuur.
 *
 * Spiegelen de Python dataclasses in core/template_config.py.
 */

export interface TextZoneYaml {
  bind: string;
  x_mm?: number;
  y_mm?: number;
  font?: string;
  size?: number;
  color?: string;
  align?: "left" | "right" | "center";
}

export interface LineZoneYaml {
  x0_mm?: number;
  y_mm?: number;
  x1_mm?: number;
  width_pt?: number;
  color?: string;
}

export interface ImageZoneYaml {
  bind: string;
  x_mm?: number;
  y_mm?: number;
  width_mm?: number;
  height_mm?: number;
  fallback?: string;
}

export interface TableColumnYaml {
  field: string;
  width_mm?: number;
  align?: "left" | "right" | "center";
  format?: string | null;
  font?: string;
  size?: number;
  color?: string;
  header?: string | null;
}

export interface TableConfigYaml {
  data_bind: string;
  columns?: TableColumnYaml[];
  origin?: { x_mm?: number; y_mm?: number };
  row_height_mm?: number;
  max_y_mm?: number;
  header_font?: string;
  header_size?: number;
  header_color?: string;
  show_header?: boolean;
  header_bg?: string | null;
  body_font?: string | null;
  body_size?: number | null;
  body_color?: string | null;
  alt_row_bg?: string | null;
  grid_color?: string | null;
}

export interface ContentFrameYaml {
  x_mm?: number;
  y_mm?: number;
  width_mm?: number;
  height_mm?: number;
}

export interface PageTypeYaml {
  name?: string;
  stationery?: string | null;
  text_zones?: TextZoneYaml[];
  image_zones?: ImageZoneYaml[];
  line_zones?: LineZoneYaml[];
  table?: TableConfigYaml;
  content_frame?: ContentFrameYaml;
}
