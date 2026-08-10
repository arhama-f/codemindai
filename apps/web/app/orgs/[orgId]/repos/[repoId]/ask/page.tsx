"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import { AskForm } from "@/components/AskForm";
import { Breadcrumbs } from "@/components/app/breadcrumbs";
import { apiClient } from "@/lib/apiClient";

export default function AskPage() {
  const { orgId, repoId } = useParams<{ orgId: string; repoId: string }>();

  const filesQuery = useQuery({
    queryKey: ["files", orgId, repoId],
    queryFn: async () => {
      const { data, error } = await apiClient.GET(
        "/api/organizations/{org_id}/repositories/{repo_id}/files",
        { params: { path: { org_id: orgId, repo_id: repoId } } },
      );
      if (error) throw error;
      return data;
    },
  });

  const filePathToId = Object.fromEntries(
    (filesQuery.data ?? []).map((file) => [file.path, file.id]),
  );

  return (
    <main className="mx-auto max-w-2xl px-6 py-12">
      <Breadcrumbs
        items={[
          { label: "Organization", href: `/orgs/${orgId}` },
          { label: "Repository", href: `/orgs/${orgId}/repos/${repoId}` },
          { label: "Ask" },
        ]}
      />
      <h1 className="mb-6 text-2xl font-semibold tracking-tight">Ask this repository</h1>
      <AskForm orgId={orgId} repoId={repoId} filePathToId={filePathToId} />
    </main>
  );
}
