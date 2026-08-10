"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";

import { Breadcrumbs } from "@/components/app/breadcrumbs";
import { DismissFindingForm } from "@/components/DismissFindingForm";
import { FindingExplanationPanel } from "@/components/FindingExplanationPanel";
import { ProposedFixPanel } from "@/components/ProposedFixPanel";
import { SeverityBadge } from "@/components/SeverityBadge";
import { SourceViewer } from "@/components/SourceViewer";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/lib/apiClient";

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

  if (findingQuery.isLoading) return <main className="p-6 text-muted-foreground">Loading...</main>;
  const finding = findingQuery.data;
  if (!finding) return null;

  return (
    <main className="mx-auto max-w-4xl px-6 py-12">
      <Breadcrumbs
        items={[
          { label: "Organization", href: `/orgs/${orgId}` },
          { label: "Repository", href: `/orgs/${orgId}/repos/${repoId}` },
          { label: "Findings", href: `/orgs/${orgId}/repos/${repoId}/findings` },
          { label: finding.title },
        ]}
      />

      <div className="mb-4 flex items-center gap-3">
        <SeverityBadge severity={finding.severity} />
        <span className="text-sm text-muted-foreground">
          {finding.category} &middot; confidence: {finding.confidence}
        </span>
        {finding.status === "dismissed" && <Badge variant="outline">dismissed</Badge>}
      </div>

      <h1 className="mb-4 text-2xl font-semibold tracking-tight">{finding.title}</h1>

      <p className="mb-6 text-sm text-foreground/90">{finding.explanation}</p>

      <FindingExplanationPanel orgId={orgId} repoId={repoId} findingId={findingId} />

      <Card className="mb-4 gap-1 p-4 shadow-none">
        <CardHeader className="p-0">
          <CardTitle className="text-sm font-medium text-muted-foreground">Recommended fix</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <p className="text-sm text-foreground/90">{finding.recommended_fix}</p>
        </CardContent>
      </Card>

      {finding.suggested_test && (
        <Card className="mb-4 gap-1 p-4 shadow-none">
          <CardHeader className="p-0">
            <CardTitle className="text-sm font-medium text-muted-foreground">Suggested test</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <p className="text-sm text-foreground/90">{finding.suggested_test}</p>
          </CardContent>
        </Card>
      )}

      {finding.execution_path && (
        <Card className="mb-4 gap-1 p-4 shadow-none">
          <CardHeader className="p-0">
            <CardTitle className="text-sm font-medium text-muted-foreground">Execution path</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <p className="text-sm text-foreground/90">{finding.execution_path}</p>
          </CardContent>
        </Card>
      )}

      {fileQuery.data && (
        <div className="mb-6">
          <h2 className="mb-2 text-sm font-medium text-muted-foreground">
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
