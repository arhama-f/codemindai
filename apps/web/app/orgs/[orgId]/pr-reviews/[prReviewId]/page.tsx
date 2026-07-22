"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";

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

  if (prReviewQuery.isLoading) return <main className="p-6 text-gray-400">Loading...</main>;
  const prReview = prReviewQuery.data;
  if (!prReview) return null;

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <Link
        href={`/orgs/${orgId}/pr-reviews`}
        className="mb-4 inline-block text-sm text-gray-500 hover:text-gray-300"
      >
        &larr; Back to PR reviews
      </Link>

      <h1 className="mb-4 text-2xl font-semibold">
        {prReview.owner}/{prReview.repo} #{prReview.pr_number}
      </h1>

      <p className="mb-4 text-gray-300">{describeStatus(prReview)}</p>

      <div className="mb-4 rounded border border-gray-800 p-4">
        <dl className="flex flex-col gap-2 text-sm">
          <div className="flex justify-between">
            <dt className="text-gray-500">Status</dt>
            <dd>{prReview.status}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">Commit</dt>
            <dd className="font-mono text-xs">{prReview.commit_sha}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">Findings</dt>
            <dd>{prReview.findings_count}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">Comments posted</dt>
            <dd>{prReview.comments_posted}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">Reviewed</dt>
            <dd>{new Date(prReview.created_at).toLocaleString()}</dd>
          </div>
        </dl>
      </div>

      <div className="flex flex-col gap-2 text-sm">
        <a
          href={prReview.pr_url}
          target="_blank"
          rel="noreferrer"
          className="text-blue-400 underline"
        >
          View pull request on GitHub
        </a>
        {prReview.review_url && (
          <a
            href={prReview.review_url}
            target="_blank"
            rel="noreferrer"
            className="text-blue-400 underline"
          >
            View posted review
          </a>
        )}
      </div>
    </main>
  );
}
