import { describe, expect, it } from "vitest";

import {
  canPublish,
  extractErrorDetail,
  publishConfirmationMessage,
  type ProposedChange,
} from "@/lib/proposedChanges";

const DRAFT: ProposedChange = {
  id: "pc-1",
  finding_id: "f-1",
  file_id: "file-1",
  explanation: "Adds a zero guard before the division.",
  updated_content: "export function divide(a, b) {\n  if (b === 0) return 0;\n  return a / b;\n}\n",
  test_file_path: null,
  test_file_content: null,
  generated_by: "mock",
  status: "draft",
  pr_url: null,
  pr_number: null,
  published_at: null,
};

describe("canPublish", () => {
  it("returns true for a draft proposed change", () => {
    expect(canPublish(DRAFT)).toBe(true);
  });

  it("returns false once the proposed change has been published", () => {
    expect(canPublish({ ...DRAFT, status: "published" })).toBe(false);
  });
});

describe("publishConfirmationMessage", () => {
  it("mentions the file path being changed", () => {
    expect(publishConfirmationMessage("src/utils/math.ts")).toContain("src/utils/math.ts");
  });
});

describe("extractErrorDetail", () => {
  it("returns the detail string when present", () => {
    expect(extractErrorDetail({ detail: "already published" })).toBe("already published");
  });

  it("returns null when detail is missing", () => {
    expect(extractErrorDetail({})).toBeNull();
  });

  it("returns null when detail is not a string (e.g. validation error array)", () => {
    expect(extractErrorDetail({ detail: [{ msg: "invalid" }] })).toBeNull();
  });

  it("returns null for non-object errors", () => {
    expect(extractErrorDetail(null)).toBeNull();
    expect(extractErrorDetail(undefined)).toBeNull();
    expect(extractErrorDetail("plain string error")).toBeNull();
  });
});
