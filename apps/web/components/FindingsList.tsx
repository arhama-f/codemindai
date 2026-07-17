"use client";

import Link from "next/link";
import { useState } from "react";

import { filterFindings, type FindingSummary } from "@/lib/findings";
import { SeverityBadge } from "@/components/SeverityBadge";

const CATEGORIES = ["bug", "security", "performance"];
const SEVERITIES = ["critical", "high", "medium", "low"];

export function FindingsList({
  orgId,
  repoId,
  findings,
}: {
  orgId: string;
  repoId: string;
  findings: FindingSummary[];
}) {
  const [category, setCategory] = useState("");
  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("open");

  const filtered = filterFindings(findings, {
    category: category || undefined,
    severity: severity || undefined,
    status: status || undefined,
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-3">
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="rounded border border-gray-700 bg-gray-900 px-2 py-1 text-sm"
        >
          <option value="">All categories</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <select
          value={severity}
          onChange={(e) => setSeverity(e.target.value)}
          className="rounded border border-gray-700 bg-gray-900 px-2 py-1 text-sm"
        >
          <option value="">All severities</option>
          {SEVERITIES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="rounded border border-gray-700 bg-gray-900 px-2 py-1 text-sm"
        >
          <option value="open">Open</option>
          <option value="dismissed">Dismissed</option>
          <option value="">All</option>
        </select>
      </div>

      {filtered.length === 0 && <p className="text-gray-500">No findings match these filters.</p>}

      <ul className="flex flex-col gap-2">
        {filtered.map((finding) => (
          <li key={finding.id}>
            <Link
              href={`/orgs/${orgId}/repos/${repoId}/findings/${finding.id}`}
              className="flex items-center gap-3 rounded border border-gray-800 px-4 py-3 hover:bg-gray-900"
            >
              <SeverityBadge severity={finding.severity} />
              <span className="text-xs text-gray-500">{finding.category}</span>
              <span className="flex-1">{finding.title}</span>
              <span className="font-mono text-xs text-gray-600">
                {finding.file_path}:{finding.start_line}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
