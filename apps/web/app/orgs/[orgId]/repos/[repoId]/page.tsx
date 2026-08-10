"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { FolderTree, MessageCircle, Network, ShieldAlert } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { Breadcrumbs } from "@/components/app/breadcrumbs";
import { JobProgressBar } from "@/components/JobProgressBar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/lib/apiClient";

const SECTIONS = [
  { key: "files", label: "Explore files", description: "Browse the indexed file tree.", icon: FolderTree },
  { key: "ask", label: "Ask a question", description: "Ask anything about this repository.", icon: MessageCircle },
  { key: "architecture", label: "Architecture", description: "View the dependency graph.", icon: Network },
  { key: "findings", label: "Findings", description: "Bugs, security, and performance issues.", icon: ShieldAlert },
];

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
    <main className="mx-auto max-w-3xl px-6 py-12">
      <Breadcrumbs
        items={[
          { label: "Organization", href: `/orgs/${orgId}` },
          { label: repoQuery.data?.full_name ?? "Repository" },
        ]}
      />

      <h1 className="text-2xl font-semibold tracking-tight">{repoQuery.data?.full_name}</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Default branch: {repoQuery.data?.default_branch}
      </p>

      <section className="mt-8">
        <h2 className="mb-3 text-sm font-medium text-muted-foreground">Indexing</h2>
        {status === "completed" ? (
          <Badge variant="outline" className="border-emerald-500/30 text-emerald-400">
            Indexed
          </Badge>
        ) : (
          <Button
            onClick={handleStartIndexing}
            disabled={isStarting || status === "running" || status === "pending"}
          >
            {isStarting ? "Starting..." : "Run indexing"}
          </Button>
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
            <h2 className="mb-3 text-sm font-medium text-muted-foreground">Summary</h2>
            <p className="text-sm text-foreground/90">{summaryQuery.data?.repository_summary}</p>
            <ul className="mt-3 flex flex-col gap-2">
              {summaryQuery.data?.directories.map((dir) => (
                <li key={dir.path} className="text-sm text-muted-foreground">
                  <span className="font-mono text-foreground/90">{dir.path}</span>: {dir.summary}
                </li>
              ))}
            </ul>
          </section>

          <section className="mt-8 grid gap-3 sm:grid-cols-2">
            {SECTIONS.map((section) => (
              <Link key={section.key} href={`/orgs/${orgId}/repos/${repoId}/${section.key}`}>
                <Card className="h-full gap-2 p-4 shadow-none transition-all hover:-translate-y-0.5 hover:shadow-md">
                  <CardContent className="flex items-start gap-3 p-0">
                    <section.icon className="mt-0.5 size-5 shrink-0 text-primary" />
                    <div>
                      <CardTitle className="text-sm">{section.label}</CardTitle>
                      <p className="mt-1 text-sm text-muted-foreground">{section.description}</p>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </section>
        </>
      )}
    </main>
  );
}
