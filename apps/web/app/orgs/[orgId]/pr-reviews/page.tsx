"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";

import { apiClient } from "@/lib/apiClient";
import { PRReviewsList } from "@/components/PRReviewsList";

export default function PRReviewsPage() {
  const { orgId } = useParams<{ orgId: string }>();

  const prReviewsQuery = useQuery({
    queryKey: ["pr-reviews", orgId],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/api/organizations/{org_id}/pr-reviews", {
        params: { path: { org_id: orgId } },
      });
      if (error) throw error;
      return data;
    },
  });

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <Link
        href={`/orgs/${orgId}`}
        className="mb-4 inline-block text-sm text-gray-500 hover:text-gray-300"
      >
        &larr; Back to organization
      </Link>

      <h1 className="mb-6 text-2xl font-semibold">PR reviews</h1>

      {prReviewsQuery.data && <PRReviewsList orgId={orgId} prReviews={prReviewsQuery.data} />}
    </main>
  );
}
