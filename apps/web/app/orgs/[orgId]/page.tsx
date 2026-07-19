"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { apiClient } from "@/lib/apiClient";
import { PRReviewPanel } from "@/components/PRReviewPanel";

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
    <main className="mx-auto max-w-2xl px-6 py-16">
      <h1 className="text-2xl font-semibold">{orgQuery.data?.name ?? "Organization"}</h1>

      <section className="mt-8">
        <h2 className="mb-2 text-lg font-medium">Repositories</h2>
        <ul className="flex flex-col gap-2">
          {reposQuery.data?.map((repo) => (
            <li key={repo.id}>
              <Link
                href={`/orgs/${orgId}/repos/${repo.id}`}
                className="block rounded border border-gray-800 px-4 py-3 hover:bg-gray-900"
              >
                <span className="font-medium">{repo.full_name}</span>{" "}
                <span className="text-sm text-gray-500">
                  ({repo.latest_index_status ?? "not indexed"})
                </span>
              </Link>
            </li>
          ))}
          {reposQuery.data?.length === 0 && (
            <p className="text-gray-500">No repositories added yet.</p>
          )}
        </ul>
      </section>

      <section className="mt-8">
        <h2 className="mb-2 text-lg font-medium">Connect GitHub</h2>
        {availableReposQuery.data?.length ? (
          <ul className="flex flex-col gap-2">
            {availableReposQuery.data
              .filter((repo) => !addedExternalIds.has(repo.full_name))
              .map((repo) => (
                <li
                  key={repo.external_repo_id}
                  className="flex items-center justify-between rounded border border-gray-800 px-4 py-3"
                >
                  <span>{repo.full_name}</span>
                  <button
                    onClick={() => handleAddRepository(repo.external_repo_id)}
                    disabled={addingRepoId === repo.external_repo_id}
                    className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-500 disabled:opacity-50"
                  >
                    {addingRepoId === repo.external_repo_id ? "Adding..." : "Add"}
                  </button>
                </li>
              ))}
          </ul>
        ) : (
          <button
            onClick={handleConnectGithub}
            disabled={isConnecting}
            className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-500 disabled:opacity-50"
          >
            {isConnecting ? "Connecting..." : "Connect GitHub (mock)"}
          </button>
        )}
      </section>

      <section className="mt-8">
        <PRReviewPanel orgId={orgId} />
      </section>
    </main>
  );
}
