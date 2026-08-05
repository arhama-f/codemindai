"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { apiClient } from "@/lib/apiClient";

const PLAN_LABELS: Record<string, string> = { free: "Free", pro: "Pro", team: "Team" };

function UsageBar({ label, used, limit }: { label: string; used: number; limit: number | null }) {
  const pct = limit ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  return (
    <div className="mb-4">
      <div className="mb-1 flex justify-between text-sm text-gray-400">
        <span>{label}</span>
        <span>
          {used} {limit === null ? "" : `/ ${limit}`}
        </span>
      </div>
      {limit !== null && (
        <div className="h-2 rounded bg-gray-800">
          <div
            className="h-2 rounded bg-blue-600"
            style={{ width: `${pct}%` }}
          />
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

  if (billingQuery.isLoading) return <main className="p-6 text-gray-400">Loading...</main>;
  const billing = billingQuery.data;
  if (!billing) return null;

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <Link
        href={`/orgs/${orgId}`}
        className="mb-4 inline-block text-sm text-gray-500 hover:text-gray-300"
      >
        &larr; Back to organization
      </Link>

      <h1 className="mb-1 text-2xl font-semibold">Billing</h1>
      <p className="mb-8 text-gray-400">
        Current plan: <span className="font-medium">{PLAN_LABELS[billing.plan]}</span>{" "}
        <span className="text-sm text-gray-500">({billing.status})</span>
      </p>

      <section className="mb-8 rounded border border-gray-800 p-4">
        <h2 className="mb-3 text-sm font-medium text-gray-500">Usage this month</h2>
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
      </section>

      {actionError && <p className="mb-4 text-sm text-red-400">{actionError}</p>}

      <div className="flex flex-wrap gap-3">
        {billing.plan !== "pro" && (
          <button
            onClick={() => handleUpgrade("pro")}
            disabled={isRedirecting}
            className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-500 disabled:opacity-50"
          >
            Upgrade to Pro
          </button>
        )}
        {billing.plan !== "team" && (
          <button
            onClick={() => handleUpgrade("team")}
            disabled={isRedirecting}
            className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-500 disabled:opacity-50"
          >
            Upgrade to Team
          </button>
        )}
        {billing.plan !== "free" && (
          <button
            onClick={handleManage}
            disabled={isRedirecting}
            className="rounded border border-gray-700 px-4 py-2 hover:bg-gray-900 disabled:opacity-50"
          >
            Manage subscription
          </button>
        )}
      </div>
    </main>
  );
}
