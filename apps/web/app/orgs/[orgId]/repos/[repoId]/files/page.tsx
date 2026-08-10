"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { Breadcrumbs } from "@/components/app/breadcrumbs";
import { FileTree } from "@/components/FileTree";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { apiClient } from "@/lib/apiClient";

export default function FilesPage() {
  const { orgId, repoId } = useParams<{ orgId: string; repoId: string }>();
  const [query, setQuery] = useState("");

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

  const symbolsQuery = useQuery({
    queryKey: ["symbols", orgId, repoId, query],
    queryFn: async () => {
      const { data, error } = await apiClient.GET(
        "/api/organizations/{org_id}/repositories/{repo_id}/symbols",
        { params: { path: { org_id: orgId, repo_id: repoId }, query: { query } } },
      );
      if (error) throw error;
      return data;
    },
    enabled: query.length > 0,
  });

  return (
    <main className="mx-auto max-w-2xl px-6 py-12">
      <Breadcrumbs
        items={[
          { label: "Organization", href: `/orgs/${orgId}` },
          { label: "Repository", href: `/orgs/${orgId}/repos/${repoId}` },
          { label: "Files" },
        ]}
      />
      <h1 className="mb-4 text-2xl font-semibold tracking-tight">Files</h1>

      <Input
        placeholder="Search symbols..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      {query && (
        <div className="mt-3 flex flex-col gap-2">
          {symbolsQuery.data?.map((symbol) => (
            <Link
              key={symbol.id}
              href={`/orgs/${orgId}/repos/${repoId}/files/${symbol.file_id}?start=${symbol.start_line}&end=${symbol.end_line}`}
            >
              <Card className="p-3 text-sm shadow-none transition-colors hover:bg-muted/40">
                <span className="font-mono text-primary">{symbol.name}</span>{" "}
                <span className="text-muted-foreground">({symbol.kind})</span>{" "}
                <span className="text-muted-foreground/70">
                  {symbol.file_path}:{symbol.start_line}
                </span>
              </Card>
            </Link>
          ))}
          {symbolsQuery.data?.length === 0 && (
            <p className="text-sm text-muted-foreground">No symbols match &quot;{query}&quot;.</p>
          )}
        </div>
      )}

      <Card className="mt-6 gap-0 py-2 shadow-none">
        {filesQuery.data && <FileTree files={filesQuery.data} orgId={orgId} repoId={repoId} />}
      </Card>
    </main>
  );
}
