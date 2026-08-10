"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import { Breadcrumbs } from "@/components/app/breadcrumbs";
import { PRReviewsList } from "@/components/PRReviewsList";
import { apiClient } from "@/lib/apiClient";

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
    <main className="mx-auto max-w-3xl px-6 py-12">
      <Breadcrumbs
        items={[{ label: "Organization", href: `/orgs/${orgId}` }, { label: "PR reviews" }]}
      />
      <h1 className="mb-6 text-2xl font-semibold tracking-tight">PR reviews</h1>
      {prReviewsQuery.data && <PRReviewsList orgId={orgId} prReviews={prReviewsQuery.data} />}
    </main>
  );
}
