"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { apiClient } from "@/lib/apiClient";
import { FileTree } from "@/components/FileTree";

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
    <main className="mx-auto max-w-2xl px-6 py-16">
      <h1 className="text-2xl font-semibold">Files</h1>

      <input
        className="mt-4 w-full rounded border border-gray-700 bg-gray-900 px-3 py-2"
        placeholder="Search symbols..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      {query && (
        <ul className="mt-3 flex flex-col gap-2">
          {symbolsQuery.data?.map((symbol) => (
            <li key={symbol.id}>
              <Link
                href={`/orgs/${orgId}/repos/${repoId}/files/${symbol.file_id}?start=${symbol.start_line}&end=${symbol.end_line}`}
                className="block rounded border border-gray-800 px-3 py-2 text-sm hover:bg-gray-900"
              >
                <span className="font-mono text-blue-400">{symbol.name}</span>{" "}
                <span className="text-gray-500">({symbol.kind})</span>{" "}
                <span className="text-gray-600">
                  {symbol.file_path}:{symbol.start_line}
                </span>
              </Link>
            </li>
          ))}
          {symbolsQuery.data?.length === 0 && (
            <p className="text-sm text-gray-500">No symbols match &quot;{query}&quot;.</p>
          )}
        </ul>
      )}

      <div className="mt-6 rounded border border-gray-800 py-2">
        {filesQuery.data && (
          <FileTree files={filesQuery.data} orgId={orgId} repoId={repoId} />
        )}
      </div>
    </main>
  );
}
