/**
 * TypeScript types voor projecten en rapport-metadata (server-side opslag).
 */

export interface Project {
  id: string;
  name: string;
  description: string;
  reportCount?: number;
  createdAt: string;
  updatedAt: string;
}

export interface ReportSummary {
  id: string;
  title: string;
  template: string;
  projectId: string | null;
  createdAt: string;
  updatedAt: string;
}

/** API response mapping (snake_case → camelCase) */
export function mapProject(raw: Record<string, unknown>): Project {
  return {
    id: raw.id as string,
    name: raw.name as string,
    description: (raw.description as string) || "",
    reportCount: (raw.report_count as number) ?? undefined,
    createdAt: raw.created_at as string,
    updatedAt: raw.updated_at as string,
  };
}

export function mapReportSummary(
  raw: Record<string, unknown>,
): ReportSummary {
  return {
    id: raw.id as string,
    title: raw.title as string,
    template: (raw.template as string) || "",
    projectId: (raw.project_id as string) || null,
    createdAt: raw.created_at as string,
    updatedAt: raw.updated_at as string,
  };
}
