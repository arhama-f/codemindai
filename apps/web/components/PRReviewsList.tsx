"use client";

import Link from "next/link";

import type { PRReview } from "@/lib/prReviews";

const STATUS_STYLES: Record<string, string> = {
  success: "bg-green-950 text-green-300 border-green-800",
  failure: "bg-red-950 text-red-300 border-red-800",
};

export function PRReviewsList({
  orgId,
  prReviews,
}: {
  orgId: string;
  prReviews: PRReview[];
}) {
  if (prReviews.length === 0) {
    return <p className="text-gray-500">No PR reviews yet.</p>;
  }

  return (
    <ul className="flex flex-col gap-2">
      {prReviews.map((prReview) => (
        <li key={prReview.id}>
          <Link
            href={`/orgs/${orgId}/pr-reviews/${prReview.id}`}
            className="flex items-center gap-3 rounded border border-gray-800 px-4 py-3 hover:bg-gray-900"
          >
            <span
              className={`rounded border px-2 py-0.5 text-xs font-medium ${
                STATUS_STYLES[prReview.status] ?? STATUS_STYLES.failure
              }`}
            >
              {prReview.status}
            </span>
            <span className="flex-1">
              {prReview.owner}/{prReview.repo} #{prReview.pr_number}
            </span>
            <span className="text-xs text-gray-500">
              {prReview.findings_count} finding(s)
            </span>
            <span className="text-xs text-gray-600">
              {new Date(prReview.created_at).toLocaleString()}
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
