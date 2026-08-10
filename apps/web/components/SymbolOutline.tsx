"use client";

import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

import { apiClient } from "@/lib/apiClient";

export interface OutlineSymbol {
  id: string;
  name: string;
  kind: string;
  start_line: number;
  end_line: number;
}

interface ImpactedFile {
  file_id: string;
  file_path: string;
  confidence: string;
  raw_specifier?: string | null;
}

interface SymbolImpact {
  direct_dependent_files: ImpactedFile[];
  transitive_dependent_files: ImpactedFile[];
}

export function SymbolOutline({
  symbols,
  orgId,
  repoId,
}: {
  symbols: OutlineSymbol[];
  orgId: string;
  repoId: string;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [expandedSymbolId, setExpandedSymbolId] = useState<string | null>(null);
  const [impactBySymbolId, setImpactBySymbolId] = useState<Record<string, SymbolImpact>>({});
  const [loadingSymbolId, setLoadingSymbolId] = useState<string | null>(null);

  if (symbols.length === 0) {
    return <p className="text-sm text-muted-foreground">No symbols in this file.</p>;
  }

  async function handleViewImpact(symbolId: string) {
    if (expandedSymbolId === symbolId) {
      setExpandedSymbolId(null);
      return;
    }
    setExpandedSymbolId(symbolId);
    if (impactBySymbolId[symbolId]) return;

    setLoadingSymbolId(symbolId);
    const { data } = await apiClient.GET(
      "/api/organizations/{org_id}/repositories/{repo_id}/symbols/{symbol_id}/impact",
      { params: { path: { org_id: orgId, repo_id: repoId, symbol_id: symbolId } } },
    );
    setLoadingSymbolId(null);
    if (data) {
      setImpactBySymbolId((prev) => ({ ...prev, [symbolId]: data }));
    }
  }

  return (
    <ul className="flex flex-col gap-1">
      {symbols.map((symbol) => {
        const impact = impactBySymbolId[symbol.id];
        return (
          <li key={symbol.id}>
            <div className="flex items-center gap-1">
              <button
                onClick={() =>
                  router.push(`${pathname}?start=${symbol.start_line}&end=${symbol.end_line}`)
                }
                className="flex-1 rounded-md px-2 py-1 text-left text-sm transition-colors hover:bg-muted"
              >
                <span className="font-mono text-primary">{symbol.name}</span>{" "}
                <span className="text-muted-foreground">({symbol.kind})</span>
              </button>
              <button
                onClick={() => handleViewImpact(symbol.id)}
                className="rounded-md px-1.5 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                title="What breaks if I change this?"
              >
                impact
              </button>
            </div>
            {expandedSymbolId === symbol.id && (
              <div className="mt-1 ml-2 rounded-lg border border-border bg-muted/30 p-2 text-xs">
                {loadingSymbolId === symbol.id && (
                  <p className="text-muted-foreground">Loading...</p>
                )}
                {impact && (
                  <>
                    <p className="mb-1 text-muted-foreground">
                      Direct dependents ({impact.direct_dependent_files.length})
                    </p>
                    {impact.direct_dependent_files.length === 0 && (
                      <p className="text-muted-foreground/70">None found.</p>
                    )}
                    <ul className="flex flex-col gap-0.5">
                      {impact.direct_dependent_files.map((file) => (
                        <li key={file.file_id} className="font-mono text-muted-foreground">
                          {file.file_path}{" "}
                          <span className="text-muted-foreground/70">({file.confidence})</span>
                        </li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
            )}
          </li>
        );
      })}
    </ul>
  );
}
