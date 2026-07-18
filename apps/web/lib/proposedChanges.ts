export interface ProposedChange {
  id: string;
  finding_id: string;
  file_id: string;
  explanation: string;
  updated_content: string;
  test_file_path: string | null;
  test_file_content: string | null;
  generated_by: string;
  status: string;
  pr_url: string | null;
  pr_number: number | null;
  published_at: string | null;
}

export function canPublish(proposedChange: ProposedChange): boolean {
  return proposedChange.status === "draft";
}

export function publishConfirmationMessage(filePath: string): string {
  return (
    `This creates a real branch and opens a draft pull request on the configured GitHub ` +
    `repository, updating ${filePath}. This can't be undone from here. Continue?`
  );
}

/** FastAPI's default HTTPException handler returns `{"detail": "..."}` for
 * plain string details (our 400/404/409 responses) even though the generated
 * OpenAPI types only model the 422 validation-error shape — so this reads the
 * field defensively at runtime instead of trusting the generated error type. */
export function extractErrorDetail(error: unknown): string | null {
  if (error && typeof error === "object" && "detail" in error) {
    const detail = (error as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
  }
  return null;
}
