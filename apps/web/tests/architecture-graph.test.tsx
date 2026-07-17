import { describe, expect, it } from "vitest";

import { buildGraphElements } from "@/lib/architectureGraph";

describe("buildGraphElements", () => {
  it("creates one node per api node", () => {
    const { nodes } = buildGraphElements(
      [
        { id: "f1", type: "file", label: "src/index.ts", file_id: "f1", subsystem: "root" },
        { id: "f2", type: "file", label: "src/utils/math.ts", file_id: "f2", subsystem: "utils" },
      ],
      [],
    );

    expect(nodes).toHaveLength(2);
    expect(nodes.map((n) => n.id).sort()).toEqual(["f1", "f2"]);
  });

  it("styles resolved edges as solid and external edges as dashed with a label", () => {
    const { edges } = buildGraphElements(
      [
        { id: "f1", type: "file", label: "src/index.ts", file_id: "f1", subsystem: "root" },
        { id: "f2", type: "file", label: "src/utils/math.ts", file_id: "f2", subsystem: "utils" },
        { id: "external", type: "external", label: "External dependencies" },
      ],
      [
        { id: "e1", source: "f1", target: "f2", kind: "resolved" },
        { id: "e2", source: "f1", target: "external", kind: "external", raw_specifier: "react" },
      ],
    );

    const resolvedEdge = edges.find((e) => e.id === "e1")!;
    const externalEdge = edges.find((e) => e.id === "e2")!;

    expect(resolvedEdge.style?.strokeDasharray).toBeUndefined();
    expect(externalEdge.style?.strokeDasharray).toBe("4 4");
    expect(externalEdge.label).toBe("react");
  });

  it("gives nodes in the same subsystem the same background color", () => {
    const { nodes } = buildGraphElements(
      [
        { id: "f1", type: "file", label: "src/utils/math.ts", file_id: "f1", subsystem: "utils" },
        { id: "f2", type: "file", label: "src/utils/string.ts", file_id: "f2", subsystem: "utils" },
        { id: "f3", type: "file", label: "src/models/user.ts", file_id: "f3", subsystem: "models" },
      ],
      [],
    );

    const utilsNodes = nodes.filter((n) => n.id === "f1" || n.id === "f2");
    const modelsNode = nodes.find((n) => n.id === "f3")!;

    expect(utilsNodes[0].style?.background).toBe(utilsNodes[1].style?.background);
    expect(utilsNodes[0].style?.background).not.toBe(modelsNode.style?.background);
  });

  it("gives the external node a distinct dashed border style", () => {
    const { nodes } = buildGraphElements(
      [
        { id: "f1", type: "file", label: "src/index.ts", file_id: "f1", subsystem: "root" },
        { id: "external", type: "external", label: "External dependencies" },
      ],
      [],
    );

    const externalNode = nodes.find((n) => n.id === "external")!;
    expect(externalNode.style?.border).toContain("dashed");
  });
});
