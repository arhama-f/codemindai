"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import { Breadcrumbs } from "@/components/app/breadcrumbs";
import { ArchitectureGraph } from "@/components/ArchitectureGraph";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/apiClient";

export default function ArchitecturePage() {
  const { orgId, repoId } = useParams<{ orgId: string; repoId: string }>();

  const architectureQuery = useQuery({
    queryKey: ["architecture", orgId, repoId],
    queryFn: async () => {
      const { data, error } = await apiClient.GET(
        "/api/organizations/{org_id}/repositories/{repo_id}/architecture",
        { params: { path: { org_id: orgId, repo_id: repoId } } },
      );
      if (error) throw error;
      return data;
    },
  });

  if (architectureQuery.isLoading) {
    return <main className="mx-auto max-w-5xl px-6 py-12 text-sm text-muted-foreground">Loading...</main>;
  }

  const nodes = architectureQuery.data?.nodes ?? [];
  const edges = architectureQuery.data?.edges ?? [];
  const subsystems = architectureQuery.data?.subsystems ?? [];

  return (
    <main className="mx-auto max-w-5xl px-6 py-12">
      <Breadcrumbs
        items={[
          { label: "Organization", href: `/orgs/${orgId}` },
          { label: "Repository", href: `/orgs/${orgId}/repos/${repoId}` },
          { label: "Architecture" },
        ]}
      />
      <h1 className="mb-2 text-2xl font-semibold tracking-tight">Architecture</h1>
      <p className="mb-4 text-sm text-muted-foreground">
        Solid edges are resolved imports within the repository; dashed edges point to external
        dependencies.
      </p>

      {nodes.length === 0 ? (
        <p className="text-sm text-muted-foreground">This repository hasn&apos;t been indexed yet.</p>
      ) : (
        <>
          <ArchitectureGraph orgId={orgId} repoId={repoId} apiNodes={nodes} apiEdges={edges} />
          {subsystems.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {subsystems.map((subsystem) => (
                <Badge key={subsystem.name} variant="outline">
                  {subsystem.name} ({subsystem.file_ids.length})
                </Badge>
              ))}
            </div>
          )}
        </>
      )}
    </main>
  );
}
