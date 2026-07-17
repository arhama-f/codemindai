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
    return <p className="text-sm text-gray-500">No symbols in this file.</p>;
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
                className="flex-1 rounded px-2 py-1 text-left text-sm hover:bg-gray-800"
              >
                <span className="font-mono text-blue-400">{symbol.name}</span>{" "}
                <span className="text-gray-500">({symbol.kind})</span>
              </button>
              <button
                onClick={() => handleViewImpact(symbol.id)}
                className="rounded px-1.5 py-1 text-xs text-gray-500 hover:bg-gray-800 hover:text-gray-300"
                title="What breaks if I change this?"
              >
                impact
              </button>
            </div>
            {expandedSymbolId === symbol.id && (
              <div className="ml-2 mt-1 rounded border border-gray-800 p-2 text-xs">
                {loadingSymbolId === symbol.id && <p className="text-gray-500">Loading...</p>}
                {impact && (
                  <>
                    <p className="mb-1 text-gray-500">
                      Direct dependents ({impact.direct_dependent_files.length})
                    </p>
                    {impact.direct_dependent_files.length === 0 && (
                      <p className="text-gray-600">None found.</p>
                    )}
                    <ul className="flex flex-col gap-0.5">
                      {impact.direct_dependent_files.map((file) => (
                        <li key={file.file_id} className="font-mono text-gray-400">
                          {file.file_path}{" "}
                          <span className="text-gray-600">({file.confidence})</span>
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
