import { describe, expect, it } from "vitest";

import { describeStatus, reviewConfirmationMessage, type PRReview } from "@/lib/prReviews";

const BASE: PRReview = {
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

describe("describeStatus", () => {
  it("reports no issues when findings_count is zero", () => {
    expect(describeStatus(BASE)).toBe("No issues found in this PR's diff.");
  });

  it("uses singular 'issue' for exactly one finding", () => {
    const review = { ...BASE, findings_count: 1, comments_posted: 1 };
    expect(describeStatus(review)).toBe("1 issue found — 1 comment(s) posted.");
  });

  it("uses plural 'issues' for more than one finding", () => {
    const review = { ...BASE, findings_count: 3, comments_posted: 3 };
    expect(describeStatus(review)).toBe("3 issues found — 3 comment(s) posted.");
  });
});

describe("reviewConfirmationMessage", () => {
  it("mentions the PR number", () => {
    expect(reviewConfirmationMessage(42)).toContain("#42");
  });
});
