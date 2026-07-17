import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
  usePathname: () => "/orgs/org-1/repos/repo-1/files/file-1",
}));

vi.mock("@/lib/apiClient", () => ({
  apiClient: { GET: vi.fn() },
  API_URL: "http://localhost:8010",
}));

import { SymbolOutline } from "@/components/SymbolOutline";
import { apiClient } from "@/lib/apiClient";

describe("SymbolOutline", () => {
  it("renders a message when there are no symbols", () => {
    render(<SymbolOutline symbols={[]} orgId="org-1" repoId="repo-1" />);
    expect(screen.getByText(/no symbols/i)).toBeInTheDocument();
  });

  it("renders each symbol's name and kind", () => {
    render(
      <SymbolOutline
        symbols={[
          { id: "s1", name: "divide", kind: "function", start_line: 14, end_line: 16 },
          { id: "s2", name: "UserService", kind: "class", start_line: 3, end_line: 18 },
        ]}
        orgId="org-1"
        repoId="repo-1"
      />,
    );

    expect(screen.getByText("divide")).toBeInTheDocument();
    expect(screen.getByText("(function)")).toBeInTheDocument();
    expect(screen.getByText("UserService")).toBeInTheDocument();
  });

  it("navigates to the symbol's line range when clicked", () => {
    render(
      <SymbolOutline
        symbols={[{ id: "s1", name: "divide", kind: "function", start_line: 14, end_line: 16 }]}
        orgId="org-1"
        repoId="repo-1"
      />,
    );

    fireEvent.click(screen.getByText("divide"));

    expect(pushMock).toHaveBeenCalledWith("/orgs/org-1/repos/repo-1/files/file-1?start=14&end=16");
  });

  it("fetches and displays impact when the impact button is clicked", async () => {
    vi.mocked(apiClient.GET).mockResolvedValue({
      data: {
        direct_dependent_files: [
          { file_id: "f1", file_path: "src/index.ts", confidence: "confirmed_static", raw_specifier: null },
        ],
        transitive_dependent_files: [],
      },
      error: undefined,
    } as never);

    render(
      <SymbolOutline
        symbols={[{ id: "s1", name: "divide", kind: "function", start_line: 14, end_line: 16 }]}
        orgId="org-1"
        repoId="repo-1"
      />,
    );

    fireEvent.click(screen.getByText("impact"));

    expect(apiClient.GET).toHaveBeenCalledWith(
      "/api/organizations/{org_id}/repositories/{repo_id}/symbols/{symbol_id}/impact",
      { params: { path: { org_id: "org-1", repo_id: "repo-1", symbol_id: "s1" } } },
    );

    await waitFor(() => {
      expect(screen.getByText("src/index.ts")).toBeInTheDocument();
    });
  });
});
