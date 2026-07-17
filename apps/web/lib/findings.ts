export interface FindingSummary {
  id: string;
  check_id: string;
  category: string;
  title: string;
  severity: string;
  confidence: string;
  file_id: string;
  file_path: string;
  start_line: number;
  end_line: number;
  status: string;
}

export interface FindingFilters {
  category?: string;
  severity?: string;
  status?: string;
}

const SEVERITY_ORDER = ["critical", "high", "medium", "low"];

export function filterFindings(
  findings: FindingSummary[],
  filters: FindingFilters,
): FindingSummary[] {
  return findings
    .filter((f) => !filters.category || f.category === filters.category)
    .filter((f) => !filters.severity || f.severity === filters.severity)
    .filter((f) => !filters.status || f.status === filters.status)
    .sort((a, b) => SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity));
}
