"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { apiClient } from "@/lib/apiClient";
import { JobProgressBar } from "@/components/JobProgressBar";

export default function RepositoryDetailPage() {
  const { orgId, repoId } = useParams<{ orgId: string; repoId: string }>();
  const queryClient = useQueryClient();
  const [jobId, setJobId] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);

  const repoQuery = useQuery({
    queryKey: ["repository", orgId, repoId],
    queryFn: async () => {
      const { data, error } = await apiClient.GET(
        "/api/organizations/{org_id}/repositories/{repo_id}",
        { params: { path: { org_id: orgId, repo_id: repoId } } },
      );
      if (error) throw error;
      return data;
    },
  });

  const summaryQuery = useQuery({
    queryKey: ["summary", orgId, repoId],
    queryFn: async () => {
      const { data, error } = await apiClient.GET(
        "/api/organizations/{org_id}/repositories/{repo_id}/summary",
        { params: { path: { org_id: orgId, repo_id: repoId } } },
      );
      if (error) throw error;
      return data;
    },
    enabled: repoQuery.data?.latest_index_status === "completed",
  });

  async function handleStartIndexing() {
    setIsStarting(true);
    const { data } = await apiClient.POST(
      "/api/organizations/{org_id}/repositories/{repo_id}/index",
      { params: { path: { org_id: orgId, repo_id: repoId } } },
    );
    setIsStarting(false);
    if (data) setJobId(data.job_id);
  }

  function handleStatusChange(status: string) {
    if (status === "completed" || status === "failed") {
      queryClient.invalidateQueries({ queryKey: ["repository", orgId, repoId] });
      queryClient.invalidateQueries({ queryKey: ["summary", orgId, repoId] });
    }
  }

  const status = repoQuery.data?.latest_index_status;

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <h1 className="text-2xl font-semibold">{repoQuery.data?.full_name}</h1>
      <p className="mt-1 text-sm text-gray-500">Default branch: {repoQuery.data?.default_branch}</p>

      <section className="mt-8">
        <h2 className="mb-2 text-lg font-medium">Indexing</h2>
        {status === "completed" ? (
          <p className="text-sm text-green-400">Indexed</p>
        ) : (
          <button
            onClick={handleStartIndexing}
            disabled={isStarting || status === "running" || status === "pending"}
            className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-500 disabled:opacity-50"
          >
            {isStarting ? "Starting..." : "Run indexing"}
          </button>
        )}
        {jobId && (
          <div className="mt-3">
            <JobProgressBar orgId={orgId} jobId={jobId} onStatusChange={handleStatusChange} />
          </div>
        )}
      </section>

      {status === "completed" && (
        <>
          <section className="mt-8">
            <h2 className="mb-2 text-lg font-medium">Summary</h2>
            <p className="text-gray-300">{summaryQuery.data?.repository_summary}</p>
            <ul className="mt-3 flex flex-col gap-2">
              {summaryQuery.data?.directories.map((dir) => (
                <li key={dir.path} className="text-sm text-gray-400">
                  <span className="font-mono text-gray-300">{dir.path}</span>: {dir.summary}
                </li>
              ))}
            </ul>
          </section>

          <section className="mt-8 flex gap-4">
            <Link
              href={`/orgs/${orgId}/repos/${repoId}/files`}
              className="rounded border border-gray-700 px-4 py-2 hover:bg-gray-800"
            >
              Explore files
            </Link>
            <Link
              href={`/orgs/${orgId}/repos/${repoId}/ask`}
              className="rounded border border-gray-700 px-4 py-2 hover:bg-gray-800"
            >
              Ask a question
            </Link>
            <Link
              href={`/orgs/${orgId}/repos/${repoId}/architecture`}
              className="rounded border border-gray-700 px-4 py-2 hover:bg-gray-800"
            >
              Architecture
            </Link>
          </section>
        </>
      )}
    </main>
  );
}
