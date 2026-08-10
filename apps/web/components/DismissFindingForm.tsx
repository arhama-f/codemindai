"use client";

import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
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
      <Textarea
        placeholder="Why is this being dismissed? (e.g. false positive, accepted risk)"
        value={reason}
        onChange={(e) => setReason(e.target.value)}
        required
      />
      <Button type="submit" variant="destructive" disabled={isSubmitting} className="self-start">
        {isSubmitting ? "Dismissing..." : "Dismiss finding"}
      </Button>
    </form>
  );
}
