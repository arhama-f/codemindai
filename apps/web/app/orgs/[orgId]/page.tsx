"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { Breadcrumbs } from "@/components/app/breadcrumbs";
import { PRReviewPanel } from "@/components/PRReviewPanel";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { apiClient } from "@/lib/apiClient";

export default function OrganizationDetailPage() {
  const { orgId } = useParams<{ orgId: string }>();
  const queryClient = useQueryClient();
  const [isConnecting, setIsConnecting] = useState(false);
  const [addingRepoId, setAddingRepoId] = useState<string | null>(null);

  const orgQuery = useQuery({
    queryKey: ["organization", orgId],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/api/organizations/{org_id}", {
        params: { path: { org_id: orgId } },
      });
      if (error) throw error;
      return data;
    },
  });

  const reposQuery = useQuery({
    queryKey: ["repositories", orgId],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/api/organizations/{org_id}/repositories", {
        params: { path: { org_id: orgId } },
      });
      if (error) throw error;
      return data;
    },
  });

  const availableReposQuery = useQuery({
    queryKey: ["available-repositories", orgId],
    queryFn: async () => {
      const { data, error } = await apiClient.GET(
        "/api/organizations/{org_id}/github/repositories",
        { params: { path: { org_id: orgId } } },
      );
      if (error) throw error;
      return data;
    },
  });

  async function handleConnectGithub() {
    setIsConnecting(true);
    await apiClient.POST("/api/organizations/{org_id}/github/connect", {
      params: { path: { org_id: orgId } },
    });
    setIsConnecting(false);
    queryClient.invalidateQueries({ queryKey: ["available-repositories", orgId] });
  }

  async function handleAddRepository(externalRepoId: string) {
    setAddingRepoId(externalRepoId);
    await apiClient.POST("/api/organizations/{org_id}/repositories", {
      params: { path: { org_id: orgId } },
      body: { external_repo_id: externalRepoId },
    });
    setAddingRepoId(null);
    queryClient.invalidateQueries({ queryKey: ["repositories", orgId] });
  }

  const addedExternalIds = new Set(reposQuery.data?.map((r) => r.full_name));

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <Breadcrumbs items={[{ label: orgQuery.data?.name ?? "Organization" }]} />

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">{orgQuery.data?.name ?? "Organization"}</h1>
        <Button variant="ghost" size="sm" nativeButton={false} render={<Link href={`/orgs/${orgId}/billing`} />}>
          Billing
        </Button>
      </div>

      <section className="mt-8">
        <h2 className="mb-3 text-sm font-medium text-muted-foreground">Repositories</h2>
        <div className="flex flex-col gap-2">
          {reposQuery.data?.map((repo) => (
            <Link key={repo.id} href={`/orgs/${orgId}/repos/${repo.id}`}>
              <Card className="flex-row items-center justify-between p-4 shadow-none transition-colors hover:bg-muted/40">
                <span className="font-medium">{repo.full_name}</span>
                <span className="text-sm text-muted-foreground">
                  {repo.latest_index_status ?? "not indexed"}
                </span>
              </Card>
            </Link>
          ))}
          {reposQuery.data?.length === 0 && (
            <p className="text-sm text-muted-foreground">No repositories added yet.</p>
          )}
        </div>
      </section>

      <section className="mt-8">
        <h2 className="mb-3 text-sm font-medium text-muted-foreground">Connect GitHub</h2>
        {availableReposQuery.data?.length ? (
          <div className="flex flex-col gap-2">
            {availableReposQuery.data
              .filter((repo) => !addedExternalIds.has(repo.full_name))
              .map((repo) => (
                <Card
                  key={repo.external_repo_id}
                  className="flex-row items-center justify-between p-4 shadow-none"
                >
                  <span className="text-sm">{repo.full_name}</span>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => handleAddRepository(repo.external_repo_id)}
                    disabled={addingRepoId === repo.external_repo_id}
                  >
                    {addingRepoId === repo.external_repo_id ? "Adding..." : "Add"}
                  </Button>
                </Card>
              ))}
          </div>
        ) : (
          <Button variant="outline" onClick={handleConnectGithub} disabled={isConnecting}>
            {isConnecting ? "Connecting..." : "Connect GitHub (mock)"}
          </Button>
        )}
      </section>

      <section className="mt-8">
        <div className="mb-3 flex justify-end">
          <Link
            href={`/orgs/${orgId}/pr-reviews`}
            className="text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            View past reviews &rarr;
          </Link>
        </div>
        <PRReviewPanel orgId={orgId} />
      </section>
    </main>
  );
}
