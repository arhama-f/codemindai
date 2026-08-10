"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useState } from "react";

import { Breadcrumbs } from "@/components/app/breadcrumbs";
import { FindingsList } from "@/components/FindingsList";
import { JobProgressBar } from "@/components/JobProgressBar";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/apiClient";

export default function FindingsPage() {
  const { orgId, repoId } = useParams<{ orgId: string; repoId: string }>();
  const queryClient = useQueryClient();
  const [jobId, setJobId] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);

  const findingsQuery = useQuery({
    queryKey: ["findings", orgId, repoId],
    queryFn: async () => {
      const { data, error } = await apiClient.GET(
        "/api/organizations/{org_id}/repositories/{repo_id}/findings",
        { params: { path: { org_id: orgId, repo_id: repoId } } },
      );
      if (error) throw error;
      return data;
    },
  });

  async function handleRunAnalysis() {
    setIsStarting(true);
    const { data } = await apiClient.POST(
      "/api/organizations/{org_id}/repositories/{repo_id}/analyses",
      { params: { path: { org_id: orgId, repo_id: repoId } } },
    );
    setIsStarting(false);
    if (data) setJobId(data.job_id);
  }

  function handleStatusChange(status: string) {
    if (status === "completed" || status === "failed") {
      queryClient.invalidateQueries({ queryKey: ["findings", orgId, repoId] });
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <Breadcrumbs
        items={[
          { label: "Organization", href: `/orgs/${orgId}` },
          { label: "Repository", href: `/orgs/${orgId}/repos/${repoId}` },
          { label: "Findings" },
        ]}
      />

      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Findings</h1>
        <Button onClick={handleRunAnalysis} disabled={isStarting}>
          {isStarting ? "Starting..." : "Run analysis"}
        </Button>
      </div>

      {jobId && (
        <div className="mb-6">
          <JobProgressBar orgId={orgId} jobId={jobId} onStatusChange={handleStatusChange} />
        </div>
      )}

      {findingsQuery.data && (
        <FindingsList orgId={orgId} repoId={repoId} findings={findingsQuery.data} />
      )}
    </main>
  );
}
