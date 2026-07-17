import type { Edge, Node } from "@xyflow/react";

export interface ArchitectureApiNode {
  id: string;
  type: string;
  label: string;
  file_id?: string | null;
  language?: string | null;
  symbol_count?: number;
  subsystem?: string | null;
}

export interface ArchitectureApiEdge {
  id: string;
  source: string;
  target: string;
  kind: string;
  raw_specifier?: string | null;
}

const PALETTE = ["#3b82f6", "#22c55e", "#f97316", "#a855f7", "#ef4444", "#14b8a6"];
const COLUMN_WIDTH = 220;
const ROW_HEIGHT = 90;

function colorForSubsystem(subsystem: string | null, sortedNames: string[]): string {
  if (!subsystem) return "#6b7280";
  const index = sortedNames.indexOf(subsystem);
  return PALETTE[index % PALETTE.length];
}

export function buildGraphElements(
  apiNodes: ArchitectureApiNode[],
  apiEdges: ArchitectureApiEdge[],
): { nodes: Node[]; edges: Edge[] } {
  const subsystemNames = Array.from(
    new Set(apiNodes.map((n) => n.subsystem).filter((s): s is string => Boolean(s))),
  ).sort();

  // Deterministic grid layout keyed by subsystem — a real multi-hundred-file
  // repo would need a real layout engine (dagre/elkjs); unnecessary here.
  const groups = new Map<string, ArchitectureApiNode[]>();
  for (const node of apiNodes) {
    const key = node.type === "external" ? "~external" : (node.subsystem ?? "~none");
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(node);
  }
  const groupKeys = Array.from(groups.keys()).sort();

  const nodes: Node[] = [];
  groupKeys.forEach((key, columnIndex) => {
    const groupNodes = groups.get(key) ?? [];
    groupNodes.forEach((apiNode, rowIndex) => {
      const isExternal = apiNode.type === "external";
      nodes.push({
        id: apiNode.id,
        position: { x: columnIndex * COLUMN_WIDTH, y: rowIndex * ROW_HEIGHT },
        data: { label: apiNode.label },
        style: {
          background: isExternal
            ? "#1f2937"
            : colorForSubsystem(apiNode.subsystem ?? null, subsystemNames),
          color: "#fff",
          border: isExternal ? "1px dashed #6b7280" : "1px solid rgba(255,255,255,0.2)",
          borderRadius: 6,
          fontSize: 12,
          padding: 8,
        },
      });
    });
  });

  const edges: Edge[] = apiEdges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    label: e.kind === "external" ? (e.raw_specifier ?? undefined) : undefined,
    style:
      e.kind === "external"
        ? { strokeDasharray: "4 4", stroke: "#6b7280" }
        : { stroke: "#58a6ff" },
  }));

  return { nodes, edges };
}
