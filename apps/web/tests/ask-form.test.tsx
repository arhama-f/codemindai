import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AskForm } from "@/components/AskForm";
import { apiClient } from "@/lib/apiClient";

vi.mock("@/lib/apiClient", () => ({
  apiClient: { POST: vi.fn() },
  API_URL: "http://localhost:8010",
}));

describe("AskForm", () => {
  beforeEach(() => {
    vi.mocked(apiClient.POST).mockReset();
  });

  it("submits the question to the ask endpoint with the correct payload", async () => {
    vi.mocked(apiClient.POST).mockResolvedValue({
      data: { answer: "It's in math.ts.", citations: [] },
      error: undefined,
    } as never);

    render(<AskForm orgId="org-1" repoId="repo-1" filePathToId={{}} />);

    fireEvent.change(screen.getByPlaceholderText(/ask a question/i), {
      target: { value: "Where is divide?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /ask/i }));

    await waitFor(() => {
      expect(apiClient.POST).toHaveBeenCalledWith(
        "/api/organizations/{org_id}/repositories/{repo_id}/ask",
        {
          params: { path: { org_id: "org-1", repo_id: "repo-1" } },
          body: { question: "Where is divide?" },
        },
      );
    });

    expect(await screen.findByText("It's in math.ts.")).toBeInTheDocument();
  });

  it("renders citations as links using the resolved file id", async () => {
    vi.mocked(apiClient.POST).mockResolvedValue({
      data: {
        answer: "In src/utils/math.ts:14-16 ...",
        citations: [
          {
            file_path: "src/utils/math.ts",
            start_line: 14,
            end_line: 16,
            snippet: "export function divide...",
          },
        ],
      },
      error: undefined,
    } as never);

    render(
      <AskForm
        orgId="org-1"
        repoId="repo-1"
        filePathToId={{ "src/utils/math.ts": "file-42" }}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText(/ask a question/i), {
      target: { value: "Where is divide?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /ask/i }));

    const link = await screen.findByRole("link");
    expect(link).toHaveAttribute(
      "href",
      "/orgs/org-1/repos/repo-1/files/file-42?start=14&end=16",
    );
  });
});
