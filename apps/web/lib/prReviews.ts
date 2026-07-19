export interface PRReview {
  id: string;
  owner: string;
  repo: string;
  pr_number: number;
  pr_url: string;
  commit_sha: string;
  findings_count: number;
  comments_posted: number;
  status: string;
  review_url: string | null;
  created_at: string;
}

export function describeStatus(prReview: PRReview): string {
  if (prReview.findings_count === 0) {
    return "No issues found in this PR's diff.";
  }
  const plural = prReview.findings_count === 1 ? "issue" : "issues";
  return `${prReview.findings_count} ${plural} found — ${prReview.comments_posted} comment(s) posted.`;
}

export function reviewConfirmationMessage(prNumber: number): string {
  return (
    `This posts a real review comment (if any issues are found) and sets a real commit ` +
    `status on the configured GitHub repository's PR #${prNumber}. Continue?`
  );
}
