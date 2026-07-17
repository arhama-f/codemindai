"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import { apiClient } from "@/lib/apiClient";
import { ArchitectureGraph } from "@/components/ArchitectureGraph";

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
    return <main className="p-6 text-gray-400">Loading...</main>;
  }

  const nodes = architectureQuery.data?.nodes ?? [];
  const edges = architectureQuery.data?.edges ?? [];
  const subsystems = architectureQuery.data?.subsystems ?? [];

  return (
    <main className="mx-auto max-w-5xl px-6 py-16">
      <h1 className="mb-2 text-2xl font-semibold">Architecture</h1>
      <p className="mb-4 text-sm text-gray-500">
        Solid edges are resolved imports within the repository; dashed edges point to
        external dependencies.
      </p>

      {nodes.length === 0 ? (
        <p className="text-gray-500">This repository hasn&apos;t been indexed yet.</p>
      ) : (
        <>
          <ArchitectureGraph orgId={orgId} repoId={repoId} apiNodes={nodes} apiEdges={edges} />
          {subsystems.length > 0 && (
            <ul className="mt-4 flex flex-wrap gap-3 text-sm text-gray-400">
              {subsystems.map((subsystem) => (
                <li key={subsystem.name}>
                  {subsystem.name} ({subsystem.file_ids.length})
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </main>
  );
}
