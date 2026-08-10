"use client";

import Link from "next/link";
import { useState } from "react";

import { SeverityBadge } from "@/components/SeverityBadge";
import { Card } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { filterFindings, type FindingSummary } from "@/lib/findings";

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
      <div className="flex flex-wrap gap-2">
        <Select value={category || "all"} onValueChange={(v) => setCategory(v && v !== "all" ? v : "")}>
          <SelectTrigger size="sm">
            <SelectValue placeholder="All categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All categories</SelectItem>
            {CATEGORIES.map((c) => (
              <SelectItem key={c} value={c}>
                {c}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={severity || "all"} onValueChange={(v) => setSeverity(v && v !== "all" ? v : "")}>
          <SelectTrigger size="sm">
            <SelectValue placeholder="All severities" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All severities</SelectItem>
            {SEVERITIES.map((s) => (
              <SelectItem key={s} value={s}>
                {s}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={status || "all"} onValueChange={(v) => setStatus(v && v !== "all" ? v : "")}>
          <SelectTrigger size="sm">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="open">Open</SelectItem>
            <SelectItem value="dismissed">Dismissed</SelectItem>
            <SelectItem value="all">All</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {filtered.length === 0 && (
        <p className="text-sm text-muted-foreground">No findings match these filters.</p>
      )}

      <div className="flex flex-col gap-2">
        {filtered.map((finding) => (
          <Link key={finding.id} href={`/orgs/${orgId}/repos/${repoId}/findings/${finding.id}`}>
            <Card className="flex-row items-center gap-3 p-4 shadow-none transition-colors hover:bg-muted/40">
              <SeverityBadge severity={finding.severity} />
              <span className="text-xs text-muted-foreground">{finding.category}</span>
              <span className="flex-1 truncate text-sm font-medium">{finding.title}</span>
              <span className="hidden shrink-0 font-mono text-xs text-muted-foreground sm:inline">
                {finding.file_path}:{finding.start_line}
              </span>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
