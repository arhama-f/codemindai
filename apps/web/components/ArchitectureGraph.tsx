"use client";

import { Background, Controls, ReactFlow, ReactFlowProvider, type Node } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useRouter } from "next/navigation";
import { useMemo } from "react";

import {
  buildGraphElements,
  type ArchitectureApiEdge,
  type ArchitectureApiNode,
} from "@/lib/architectureGraph";

export function ArchitectureGraph({
  orgId,
  repoId,
  apiNodes,
  apiEdges,
}: {
  orgId: string;
  repoId: string;
  apiNodes: ArchitectureApiNode[];
  apiEdges: ArchitectureApiEdge[];
}) {
  const router = useRouter();
  const { nodes, edges } = useMemo(
    () => buildGraphElements(apiNodes, apiEdges),
    [apiNodes, apiEdges],
  );

  function handleNodeClick(_event: unknown, node: Node) {
    const apiNode = apiNodes.find((n) => n.id === node.id);
    if (apiNode?.file_id) {
      router.push(`/orgs/${orgId}/repos/${repoId}/files/${apiNode.file_id}`);
    }
  }

  return (
    <div style={{ height: 520 }} className="rounded border border-gray-800">
      <ReactFlowProvider>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodeClick={handleNodeClick}
          fitView
          proOptions={{ hideAttribution: true }}
        >
          <Background />
          <Controls />
        </ReactFlow>
      </ReactFlowProvider>
    </div>
  );
}
