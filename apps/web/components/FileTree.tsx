"use client";

import Link from "next/link";
import { useState } from "react";

import { buildTree, sortedEntries, type FileTreeFile, type TreeNode } from "@/lib/fileTree";

function DirectoryListing({
  node,
  orgId,
  repoId,
}: {
  node: TreeNode;
  orgId: string;
  repoId: string;
}) {
  return (
    <ul className="pl-4">
      {sortedEntries(node).map((entry) => (
        <TreeEntry key={entry.fullPath} entry={entry} orgId={orgId} repoId={repoId} />
      ))}
    </ul>
  );
}

function TreeEntry({
  entry,
  orgId,
  repoId,
}: {
  entry: TreeNode;
  orgId: string;
  repoId: string;
}) {
  const [collapsed, setCollapsed] = useState(false);
  const isDirectory = entry.children.size > 0;

  if (!isDirectory) {
    return (
      <li>
        <Link
          href={`/orgs/${orgId}/repos/${repoId}/files/${entry.file!.id}`}
          className="block py-0.5 font-mono text-sm text-gray-400 hover:text-blue-400"
        >
          {entry.name}
        </Link>
      </li>
    );
  }

  return (
    <li>
      <button
        onClick={() => setCollapsed((v) => !v)}
        className="flex items-center gap-1 py-0.5 text-sm text-gray-300 hover:text-white"
      >
        <span>{collapsed ? "▸" : "▾"}</span>
        <span>{entry.name}/</span>
      </button>
      {!collapsed && <DirectoryListing node={entry} orgId={orgId} repoId={repoId} />}
    </li>
  );
}

export function FileTree({
  files,
  orgId,
  repoId,
}: {
  files: FileTreeFile[];
  orgId: string;
  repoId: string;
}) {
  const tree = buildTree(files);
  return <DirectoryListing node={tree} orgId={orgId} repoId={repoId} />;
}
