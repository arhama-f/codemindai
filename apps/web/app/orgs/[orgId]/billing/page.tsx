"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useState } from "react";

import { Breadcrumbs } from "@/components/app/breadcrumbs";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/lib/apiClient";

const PLAN_LABELS: Record<string, string> = { free: "Free", pro: "Pro", team: "Team" };

function UsageBar({ label, used, limit }: { label: string; used: number; limit: number | null }) {
  const pct = limit ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  return (
    <div className="mb-4 last:mb-0">
      <div className="mb-1.5 flex justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className="text-foreground/90">
          {used} {limit === null ? "" : `/ ${limit}`}
        </span>
      </div>
      {limit !== null && (
        <div className="h-1.5 rounded-full bg-muted">
          <div className="h-full rounded-full bg-primary" style={{ width: `${pct}%` }} />
        </div>
      )}
    </div>
  );
}

export default function BillingPage() {
  const { orgId } = useParams<{ orgId: string }>();
  const [actionError, setActionError] = useState<string | null>(null);
  const [isRedirecting, setIsRedirecting] = useState(false);

  const billingQuery = useQuery({
    queryKey: ["billing", orgId],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/api/organizations/{org_id}/billing", {
        params: { path: { org_id: orgId } },
      });
      if (error) throw error;
      return data;
    },
  });

  async function handleUpgrade(plan: "pro" | "team") {
    setActionError(null);
    setIsRedirecting(true);
    const { data, error } = await apiClient.POST("/api/organizations/{org_id}/billing/checkout", {
      params: { path: { org_id: orgId }, query: { plan } },
    });
    setIsRedirecting(false);
    if (error) {
      setActionError((error as { detail?: string }).detail ?? "Unable to start checkout");
      return;
    }
    window.location.href = data.url;
  }

  async function handleManage() {
    setActionError(null);
    setIsRedirecting(true);
    const { data, error } = await apiClient.POST("/api/organizations/{org_id}/billing/portal", {
      params: { path: { org_id: orgId } },
    });
    setIsRedirecting(false);
    if (error) {
      setActionError((error as { detail?: string }).detail ?? "Unable to open the billing portal");
      return;
    }
    window.location.href = data.url;
  }

  if (billingQuery.isLoading) {
    return <main className="mx-auto max-w-2xl px-6 py-12 text-sm text-muted-foreground">Loading...</main>;
  }
  const billing = billingQuery.data;
  if (!billing) return null;

  return (
    <main className="mx-auto max-w-2xl px-6 py-12">
      <Breadcrumbs
        items={[{ label: "Organization", href: `/orgs/${orgId}` }, { label: "Billing" }]}
      />

      <h1 className="mb-1 text-2xl font-semibold tracking-tight">Billing</h1>
      <p className="mb-8 text-muted-foreground">
        Current plan: <span className="font-medium text-foreground">{PLAN_LABELS[billing.plan]}</span>{" "}
        <span className="text-sm">({billing.status})</span>
      </p>

      <Card className="mb-8 gap-2 p-4 shadow-none">
        <CardHeader className="p-0">
          <CardTitle className="text-sm font-medium text-muted-foreground">Usage this month</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <UsageBar
            label="Repositories"
            used={billing.usage.repositories.used}
            limit={billing.usage.repositories.limit}
          />
          <UsageBar
            label="AI actions"
            used={billing.usage.ai_actions_per_month.used}
            limit={billing.usage.ai_actions_per_month.limit}
          />
        </CardContent>
      </Card>

      {actionError && (
        <p className="mb-4 text-sm text-destructive" role="alert">
          {actionError}
        </p>
      )}

      <div className="flex flex-wrap gap-3">
        {billing.plan !== "pro" && (
          <Button onClick={() => handleUpgrade("pro")} disabled={isRedirecting}>
            Upgrade to Pro
          </Button>
        )}
        {billing.plan !== "team" && (
          <Button onClick={() => handleUpgrade("team")} disabled={isRedirecting}>
            Upgrade to Team
          </Button>
        )}
        {billing.plan !== "free" && (
          <Button variant="outline" onClick={handleManage} disabled={isRedirecting}>
            Manage subscription
          </Button>
        )}
      </div>
    </main>
  );
}
