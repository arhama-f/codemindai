"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { Breadcrumbs } from "@/components/app/breadcrumbs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiClient } from "@/lib/apiClient";

export default function NewOrganizationPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const { data, error: apiError } = await apiClient.POST("/api/organizations", {
      body: { name },
    });

    setIsSubmitting(false);
    if (apiError || !data) {
      setError((apiError as { detail?: string })?.detail ?? "Failed to create organization");
      return;
    }
    router.push(`/orgs/${data.id}`);
  }

  return (
    <main className="mx-auto flex max-w-sm flex-col gap-4 px-6 py-16">
      <Breadcrumbs items={[{ label: "Organizations", href: "/orgs" }, { label: "New" }]} />
      <h1 className="text-2xl font-semibold tracking-tight">New organization</h1>
      <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="org-name">Organization name</Label>
          <Input
            id="org-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>
        {error && (
          <p className="text-sm text-destructive" role="alert">
            {error}
          </p>
        )}
        <Button type="submit" disabled={isSubmitting} className="self-start">
          {isSubmitting ? "Creating..." : "Create organization"}
        </Button>
      </form>
    </main>
  );
}
