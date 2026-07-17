"use client";

import { FormEvent, useState } from "react";

import { apiClient } from "@/lib/apiClient";

export function DismissFindingForm({
  orgId,
  repoId,
  findingId,
  onDismissed,
}: {
  orgId: string;
  repoId: string;
  findingId: string;
  onDismissed: () => void;
}) {
  const [reason, setReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setIsSubmitting(true);

    const { error } = await apiClient.POST(
      "/api/organizations/{org_id}/repositories/{repo_id}/findings/{finding_id}/dismiss",
      {
        params: { path: { org_id: orgId, repo_id: repoId, finding_id: findingId } },
        body: { reason },
      },
    );

    setIsSubmitting(false);
    if (!error) {
      onDismissed();
    }
  }

  return (
    <form className="flex flex-col gap-2" onSubmit={handleSubmit}>
      <textarea
        className="rounded border border-gray-700 bg-gray-900 px-3 py-2 text-sm"
        placeholder="Why is this being dismissed? (e.g. false positive, accepted risk)"
        value={reason}
        onChange={(e) => setReason(e.target.value)}
        required
      />
      <button
        type="submit"
        disabled={isSubmitting}
        className="self-start rounded bg-red-900 px-4 py-2 text-sm text-white hover:bg-red-800 disabled:opacity-50"
      >
        {isSubmitting ? "Dismissing..." : "Dismiss finding"}
      </button>
    </form>
  );
}
