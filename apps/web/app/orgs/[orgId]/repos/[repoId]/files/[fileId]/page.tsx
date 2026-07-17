"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams, useSearchParams } from "next/navigation";

import { apiClient } from "@/lib/apiClient";
import { SourceViewer } from "@/components/SourceViewer";
import { SymbolOutline } from "@/components/SymbolOutline";

export default function FileDetailPage() {
  const { orgId, repoId, fileId } = useParams<{
    orgId: string;
    repoId: string;
    fileId: string;
  }>();
  const searchParams = useSearchParams();
  const start = searchParams.get("start");
  const end = searchParams.get("end");

  const fileQuery = useQuery({
    queryKey: ["file", orgId, repoId, fileId],
    queryFn: async () => {
      const { data, error } = await apiClient.GET(
        "/api/organizations/{org_id}/repositories/{repo_id}/files/{file_id}",
        { params: { path: { org_id: orgId, repo_id: repoId, file_id: fileId } } },
      );
      if (error) throw error;
      return data;
    },
  });

  if (fileQuery.isLoading) return <main className="p-6 text-gray-400">Loading...</main>;

  return (
    <main className="mx-auto max-w-5xl px-6 py-16">
      <h1 className="mb-4 font-mono text-xl font-semibold">{fileQuery.data?.path}</h1>
      {fileQuery.data && (
        <div className="flex gap-6">
          <aside className="w-48 shrink-0">
            <h2 className="mb-2 text-sm font-medium text-gray-500">Symbols</h2>
            <SymbolOutline symbols={fileQuery.data.symbols} />
          </aside>
          <div className="min-w-0 flex-1">
            <SourceViewer
              content={fileQuery.data.content}
              language={fileQuery.data.language}
              highlightStart={start ? Number(start) : undefined}
              highlightEnd={end ? Number(end) : undefined}
            />
          </div>
        </div>
      )}
    </main>
  );
}
