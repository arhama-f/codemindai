import Link from "next/link";

export interface Citation {
  file_id?: string;
  file_path: string;
  start_line: number;
  end_line: number;
  snippet: string;
}

export function CitationChip({
  orgId,
  repoId,
  citation,
  fileId,
}: {
  orgId: string;
  repoId: string;
  citation: Citation;
  fileId?: string;
}) {
  const href = fileId
    ? `/orgs/${orgId}/repos/${repoId}/files/${fileId}?start=${citation.start_line}&end=${citation.end_line}`
    : `/orgs/${orgId}/repos/${repoId}/files`;

  return (
    <Link
      href={href}
      className="block rounded-lg border border-border bg-card px-3 py-2 text-sm transition-colors hover:bg-muted/40"
    >
      <div className="font-mono text-primary">
        {citation.file_path}:{citation.start_line}-{citation.end_line}
      </div>
      <div className="mt-1 truncate text-muted-foreground">{citation.snippet}</div>
    </Link>
  );
}
