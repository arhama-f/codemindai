"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { Breadcrumbs } from "@/components/app/breadcrumbs";
import { VerificationBanner } from "@/components/VerificationBanner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { apiClient } from "@/lib/apiClient";

export default function OrgsPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["organizations"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/api/organizations");
      if (error) throw error;
      return data;
    },
  });

  if (isLoading) {
    return <main className="mx-auto max-w-2xl px-6 py-12 text-sm text-muted-foreground">Loading...</main>;
  }
  if (isError) {
    return (
      <main className="mx-auto max-w-2xl px-6 py-12 text-sm text-muted-foreground">
        Failed to load organizations.{" "}
        <Link href="/login" className="text-primary hover:underline">
          Sign in
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-12">
      <Breadcrumbs items={[{ label: "Organizations" }]} />
      <VerificationBanner />
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Organizations</h1>
        <Button size="sm" nativeButton={false} render={<Link href="/orgs/new" />}>
          New organization
        </Button>
      </div>
      <div className="flex flex-col gap-2">
        {data?.map((org) => (
          <Link key={org.id} href={`/orgs/${org.id}`}>
            <Card className="p-4 shadow-none transition-colors hover:bg-muted/40">
              <span className="font-medium">{org.name}</span>{" "}
              <span className="text-sm text-muted-foreground">({org.role})</span>
            </Card>
          </Link>
        ))}
        {data?.length === 0 && <p className="text-sm text-muted-foreground">No organizations yet.</p>}
      </div>
    </main>
  );
}
