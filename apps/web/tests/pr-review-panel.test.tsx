import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/lib/apiClient", () => ({
  apiClient: { GET: vi.fn(), POST: vi.fn() },
  API_URL: "http://localhost:8010",
}));

import { PRReviewPanel } from "@/components/PRReviewPanel";
import { apiClient } from "@/lib/apiClient";

const SUCCESS_RESULT = {
  id: "pr-review-1",
  owner: "acme",
  repo: "widgets",
  pr_number: 42,
  pr_url: "https://github.com/acme/widgets/pull/42",
  commit_sha: "deadbeef",
  findings_count: 0,
  comments_posted: 0,
  status: "success",
  review_url: null,
  created_at: "2026-07-19T00:00:00Z",
};

const FAILURE_RESULT = {
  ...SUCCESS_RESULT,
  findings_count: 1,
  comments_posted: 1,
  status: "failure",
  review_url: "https://github.com/acme/widgets/pull/42#pullrequestreview-1",
};

function renderPanel() {
  return render(<PRReviewPanel orgId="org-1" />);
}

describe("PRReviewPanel", () => {
  it("renders a PR number input and a review button", () => {
    renderPanel();
    expect(screen.getByLabelText("PR number")).toBeInTheDocument();
    expect(screen.getByText("Review PR")).toBeInTheDocument();
  });

  it("shows a validation error for a non-numeric PR number", () => {
    renderPanel();
    fireEvent.change(screen.getByLabelText("PR number"), { target: { value: "0" } });
    fireEvent.click(screen.getByText("Review PR"));
    expect(screen.getByText("Enter a valid PR number.")).toBeInTheDocument();
    expect(apiClient.POST).not.toHaveBeenCalled();
  });

  it("requires confirmation before calling the API, then shows the result", async () => {
    vi.mocked(apiClient.POST).mockResolvedValue({
      data: SUCCESS_RESULT,
      error: undefined,
    } as never);

    renderPanel();
    fireEvent.change(screen.getByLabelText("PR number"), { target: { value: "42" } });
    fireEvent.click(screen.getByText("Review PR"));

    expect(screen.getByText(/PR #42/)).toBeInTheDocument();
    expect(apiClient.POST).not.toHaveBeenCalled();

    fireEvent.click(screen.getByText("Confirm review"));

    expect(apiClient.POST).toHaveBeenCalledWith("/api/organizations/{org_id}/pr-reviews", {
      params: { path: { org_id: "org-1" } },
      body: { pr_number: 42 },
    });

    await waitFor(() => {
      expect(screen.getByText("commit status: success")).toBeInTheDocument();
    });
    expect(screen.getByText("No issues found in this PR's diff.")).toBeInTheDocument();
    expect(screen.queryByText("View review")).not.toBeInTheDocument();
  });

  it("shows the review link and failure status when issues are found", async () => {
    vi.mocked(apiClient.POST).mockResolvedValue({
      data: FAILURE_RESULT,
      error: undefined,
    } as never);

    renderPanel();
    fireEvent.change(screen.getByLabelText("PR number"), { target: { value: "42" } });
    fireEvent.click(screen.getByText("Review PR"));
    fireEvent.click(screen.getByText("Confirm review"));

    await waitFor(() => {
      expect(screen.getByText("commit status: failure")).toBeInTheDocument();
    });
    expect(screen.getByText("View review")).toBeInTheDocument();
  });

  it("shows an error message when the request fails", async () => {
    vi.mocked(apiClient.POST).mockResolvedValue({
      data: undefined,
      error: { detail: "No target repo configured" },
    } as never);

    renderPanel();
    fireEvent.change(screen.getByLabelText("PR number"), { target: { value: "42" } });
    fireEvent.click(screen.getByText("Review PR"));
    fireEvent.click(screen.getByText("Confirm review"));

    await waitFor(() => {
      expect(screen.getByText("No target repo configured")).toBeInTheDocument();
    });
  });
});
