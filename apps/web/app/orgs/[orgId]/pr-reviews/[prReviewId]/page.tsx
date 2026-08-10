"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import { Breadcrumbs } from "@/components/app/breadcrumbs";
import { Card, CardContent } from "@/components/ui/card";
import { apiClient } from "@/lib/apiClient";
import { describeStatus } from "@/lib/prReviews";

export default function PRReviewDetailPage() {
  const { orgId, prReviewId } = useParams<{ orgId: string; prReviewId: string }>();

  const prReviewQuery = useQuery({
    queryKey: ["pr-review", orgId, prReviewId],
    queryFn: async () => {
      const { data, error } = await apiClient.GET(
        "/api/organizations/{org_id}/pr-reviews/{pr_review_id}",
        { params: { path: { org_id: orgId, pr_review_id: prReviewId } } },
      );
      if (error) throw error;
      return data;
    },
  });

  if (prReviewQuery.isLoading) {
    return <main className="mx-auto max-w-3xl px-6 py-12 text-sm text-muted-foreground">Loading...</main>;
  }
  const prReview = prReviewQuery.data;
  if (!prReview) return null;

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <Breadcrumbs
        items={[
          { label: "Organization", href: `/orgs/${orgId}` },
          { label: "PR reviews", href: `/orgs/${orgId}/pr-reviews` },
          { label: `#${prReview.pr_number}` },
        ]}
      />

      <h1 className="mb-4 text-2xl font-semibold tracking-tight">
        {prReview.owner}/{prReview.repo} #{prReview.pr_number}
      </h1>

      <p className="mb-4 text-sm text-foreground/90">{describeStatus(prReview)}</p>

      <Card className="mb-4 p-4 shadow-none">
        <CardContent className="p-0">
          <dl className="flex flex-col gap-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Status</dt>
              <dd>{prReview.status}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Commit</dt>
              <dd className="font-mono text-xs">{prReview.commit_sha}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Findings</dt>
              <dd>{prReview.findings_count}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Comments posted</dt>
              <dd>{prReview.comments_posted}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Reviewed</dt>
              <dd>{new Date(prReview.created_at).toLocaleString()}</dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      <div className="flex flex-col gap-2 text-sm">
        <a
          href={prReview.pr_url}
          target="_blank"
          rel="noreferrer"
          className="text-primary hover:underline"
        >
          View pull request on GitHub
        </a>
        {prReview.review_url && (
          <a
            href={prReview.review_url}
            target="_blank"
            rel="noreferrer"
            className="text-primary hover:underline"
          >
            View posted review
          </a>
        )}
      </div>
    </main>
  );
}
