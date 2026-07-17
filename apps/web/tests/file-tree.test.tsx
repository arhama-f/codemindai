import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { buildTree, sortedEntries } from "@/lib/fileTree";
import { FileTree } from "@/components/FileTree";

describe("buildTree", () => {
  it("nests files under their directory path", () => {
    const tree = buildTree([
      { id: "f1", path: "src/index.ts" },
      { id: "f2", path: "src/utils/math.ts" },
      { id: "f3", path: "src/utils/string.ts" },
    ]);

    const src = tree.children.get("src")!;
    expect(src.children.has("index.ts")).toBe(true);
    expect(src.children.get("index.ts")!.file?.id).toBe("f1");

    const utils = src.children.get("utils")!;
    expect(utils.file).toBeUndefined();
    expect(Array.from(utils.children.keys())).toEqual(["math.ts", "string.ts"]);
  });
});

describe("sortedEntries", () => {
  it("lists directories before files, both alphabetically", () => {
    const tree = buildTree([
      { id: "f1", path: "src/zeta.ts" },
      { id: "f2", path: "src/alpha/nested.ts" },
      { id: "f3", path: "src/beta.ts" },
    ]);

    const entries = sortedEntries(tree.children.get("src")!);
    expect(entries.map((e) => e.name)).toEqual(["alpha", "beta.ts", "zeta.ts"]);
  });
});

describe("FileTree", () => {
  it("renders a link for each file, nested under collapsible directories", () => {
    render(
      <FileTree
        files={[
          { id: "f1", path: "src/index.ts" },
          { id: "f2", path: "src/utils/math.ts" },
        ]}
        orgId="org-1"
        repoId="repo-1"
      />,
    );

    expect(screen.getByText("src/")).toBeInTheDocument();
    expect(screen.getByText("index.ts")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "index.ts" })).toHaveAttribute(
      "href",
      "/orgs/org-1/repos/repo-1/files/f1",
    );
  });
});
