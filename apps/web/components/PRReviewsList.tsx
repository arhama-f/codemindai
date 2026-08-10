"use client";

import Link from "next/link";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { PRReview } from "@/lib/prReviews";

const STATUS_STYLES: Record<string, string> = {
  success: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  failure: "bg-red-500/10 text-red-400 border-red-500/20",
};

export function PRReviewsList({
  orgId,
  prReviews,
}: {
  orgId: string;
  prReviews: PRReview[];
}) {
  if (prReviews.length === 0) {
    return <p className="text-sm text-muted-foreground">No PR reviews yet.</p>;
  }

  return (
    <div className="flex flex-col gap-2">
      {prReviews.map((prReview) => (
        <Link key={prReview.id} href={`/orgs/${orgId}/pr-reviews/${prReview.id}`}>
          <Card className="flex-row items-center gap-3 p-4 shadow-none transition-colors hover:bg-muted/40">
            <span
              className={cn(
                "inline-flex shrink-0 items-center rounded-full border px-2 py-0.5 text-xs font-medium",
                STATUS_STYLES[prReview.status] ?? STATUS_STYLES.failure,
              )}
            >
              {prReview.status}
            </span>
            <span className="flex-1 truncate text-sm font-medium">
              {prReview.owner}/{prReview.repo} #{prReview.pr_number}
            </span>
            <span className="hidden shrink-0 text-xs text-muted-foreground sm:inline">
              {prReview.findings_count} finding(s)
            </span>
            <span className="hidden shrink-0 text-xs text-muted-foreground sm:inline">
              {new Date(prReview.created_at).toLocaleString()}
            </span>
          </Card>
        </Link>
      ))}
    </div>
  );
}
