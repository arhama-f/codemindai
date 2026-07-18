"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { apiClient } from "@/lib/apiClient";
import { DismissFindingForm } from "@/components/DismissFindingForm";
import { ProposedFixPanel } from "@/components/ProposedFixPanel";
import { SeverityBadge } from "@/components/SeverityBadge";
import { SourceViewer } from "@/components/SourceViewer";

export default function FindingDetailPage() {
  const { orgId, repoId, findingId } = useParams<{
    orgId: string;
    repoId: string;
    findingId: string;
  }>();
  const router = useRouter();
  const queryClient = useQueryClient();

  const findingQuery = useQuery({
    queryKey: ["finding", orgId, repoId, findingId],
    queryFn: async () => {
      const { data, error } = await apiClient.GET(
        "/api/organizations/{org_id}/repositories/{repo_id}/findings/{finding_id}",
        { params: { path: { org_id: orgId, repo_id: repoId, finding_id: findingId } } },
      );
      if (error) throw error;
      return data;
    },
  });

  const fileQuery = useQuery({
    queryKey: ["file", orgId, repoId, findingQuery.data?.file_id],
    queryFn: async () => {
      const { data, error } = await apiClient.GET(
        "/api/organizations/{org_id}/repositories/{repo_id}/files/{file_id}",
        {
          params: {
            path: { org_id: orgId, repo_id: repoId, file_id: findingQuery.data!.file_id },
          },
        },
      );
      if (error) throw error;
      return data;
    },
    enabled: Boolean(findingQuery.data),
  });

  if (findingQuery.isLoading) return <main className="p-6 text-gray-400">Loading...</main>;
  const finding = findingQuery.data;
  if (!finding) return null;

  return (
    <main className="mx-auto max-w-4xl px-6 py-16">
      <Link
        href={`/orgs/${orgId}/repos/${repoId}/findings`}
        className="mb-4 inline-block text-sm text-gray-500 hover:text-gray-300"
      >
        &larr; Back to findings
      </Link>

      <div className="mb-4 flex items-center gap-3">
        <SeverityBadge severity={finding.severity} />
        <span className="text-sm text-gray-500">
          {finding.category} &middot; confidence: {finding.confidence}
        </span>
        {finding.status === "dismissed" && (
          <span className="rounded border border-gray-700 px-2 py-0.5 text-xs text-gray-400">
            dismissed
          </span>
        )}
      </div>

      <h1 className="mb-4 text-2xl font-semibold">{finding.title}</h1>

      <p className="mb-4 text-gray-300">{finding.explanation}</p>

      <div className="mb-4 rounded border border-gray-800 p-4">
        <h2 className="mb-1 text-sm font-medium text-gray-500">Recommended fix</h2>
        <p className="text-gray-300">{finding.recommended_fix}</p>
      </div>

      {finding.suggested_test && (
        <div className="mb-4 rounded border border-gray-800 p-4">
          <h2 className="mb-1 text-sm font-medium text-gray-500">Suggested test</h2>
          <p className="text-gray-300">{finding.suggested_test}</p>
        </div>
      )}

      {finding.execution_path && (
        <div className="mb-4 rounded border border-gray-800 p-4">
          <h2 className="mb-1 text-sm font-medium text-gray-500">Execution path</h2>
          <p className="text-gray-300">{finding.execution_path}</p>
        </div>
      )}

      {fileQuery.data && (
        <div className="mb-6">
          <h2 className="mb-2 text-sm font-medium text-gray-500">
            {finding.file_path}:{finding.start_line}-{finding.end_line}
          </h2>
          <SourceViewer
            content={fileQuery.data.content}
            language={fileQuery.data.language}
            highlightStart={finding.start_line}
            highlightEnd={finding.end_line}
          />
        </div>
      )}

      {fileQuery.data && (
        <ProposedFixPanel
          orgId={orgId}
          repoId={repoId}
          findingId={findingId}
          filePath={finding.file_path}
          language={fileQuery.data.language}
          originalContent={fileQuery.data.content}
        />
      )}

      {finding.status === "open" && (
        <DismissFindingForm
          orgId={orgId}
          repoId={repoId}
          findingId={findingId}
          onDismissed={() => {
            queryClient.invalidateQueries({ queryKey: ["finding", orgId, repoId, findingId] });
            queryClient.invalidateQueries({ queryKey: ["findings", orgId, repoId] });
            router.push(`/orgs/${orgId}/repos/${repoId}/findings`);
          }}
        />
      )}
    </main>
  );
}
