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
      className="block rounded border border-gray-800 px-3 py-2 text-sm hover:bg-gray-900"
    >
      <div className="font-mono text-blue-400">
        {citation.file_path}:{citation.start_line}-{citation.end_line}
      </div>
      <div className="mt-1 truncate text-gray-400">{citation.snippet}</div>
    </Link>
  );
}
