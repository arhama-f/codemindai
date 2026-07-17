import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CitationChip } from "@/components/CitationChip";

describe("CitationChip", () => {
  it("renders the file path and line range", () => {
    render(
      <CitationChip
        orgId="org-1"
        repoId="repo-1"
        fileId="file-1"
        citation={{
          file_path: "src/utils/math.ts",
          start_line: 14,
          end_line: 16,
          snippet: "export function divide(a: number, b: number): number {",
        }}
      />,
    );

    expect(screen.getByText("src/utils/math.ts:14-16")).toBeInTheDocument();
  });

  it("links to the file viewer with the highlighted line range", () => {
    render(
      <CitationChip
        orgId="org-1"
        repoId="repo-1"
        fileId="file-1"
        citation={{
          file_path: "src/utils/math.ts",
          start_line: 14,
          end_line: 16,
          snippet: "export function divide...",
        }}
      />,
    );

    const link = screen.getByRole("link");
    expect(link).toHaveAttribute(
      "href",
      "/orgs/org-1/repos/repo-1/files/file-1?start=14&end=16",
    );
  });

  it("falls back to the files list when no fileId is resolved", () => {
    render(
      <CitationChip
        orgId="org-1"
        repoId="repo-1"
        citation={{
          file_path: "src/utils/math.ts",
          start_line: 14,
          end_line: 16,
          snippet: "export function divide...",
        }}
      />,
    );

    expect(screen.getByRole("link")).toHaveAttribute(
      "href",
      "/orgs/org-1/repos/repo-1/files",
    );
  });
});
