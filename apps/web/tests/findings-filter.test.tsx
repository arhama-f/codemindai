import { describe, expect, it } from "vitest";

import { filterFindings, type FindingSummary } from "@/lib/findings";

const FINDINGS: FindingSummary[] = [
  {
    id: "1",
    check_id: "unsafe-division",
    category: "bug",
    title: "Unguarded division",
    severity: "high",
    confidence: "medium",
    file_id: "f1",
    file_path: "src/utils/math.ts",
    start_line: 15,
    end_line: 15,
    status: "open",
  },
  {
    id: "2",
    check_id: "hardcoded-secret",
    category: "security",
    title: "Hardcoded secret",
    severity: "critical",
    confidence: "medium",
    file_id: "f2",
    file_path: "src/config.ts",
    start_line: 3,
    end_line: 3,
    status: "open",
  },
  {
    id: "3",
    check_id: "array-scan-in-loop",
    category: "performance",
    title: "Linear scan in loop",
    severity: "low",
    confidence: "medium",
    file_id: "f3",
    file_path: "src/utils/collections.ts",
    start_line: 19,
    end_line: 19,
    status: "dismissed",
  },
];

describe("filterFindings", () => {
  it("returns all findings sorted by severity when no filters are set", () => {
    const result = filterFindings(FINDINGS, {});
    expect(result.map((f) => f.id)).toEqual(["2", "1", "3"]);
  });

  it("filters by category", () => {
    const result = filterFindings(FINDINGS, { category: "security" });
    expect(result.map((f) => f.id)).toEqual(["2"]);
  });

  it("filters by severity", () => {
    const result = filterFindings(FINDINGS, { severity: "low" });
    expect(result.map((f) => f.id)).toEqual(["3"]);
  });

  it("filters by status", () => {
    const result = filterFindings(FINDINGS, { status: "dismissed" });
    expect(result.map((f) => f.id)).toEqual(["3"]);
  });

  it("combines multiple filters", () => {
    const result = filterFindings(FINDINGS, { category: "bug", status: "open" });
    expect(result.map((f) => f.id)).toEqual(["1"]);
  });
});
