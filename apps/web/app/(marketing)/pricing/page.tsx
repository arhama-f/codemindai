import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Pricing — CodeMind AI",
  description: "Simple, usage-based pricing for CodeMind AI.",
};

const PLANS = [
  {
    name: "Free",
    price: "$0",
    period: "",
    description: "Try CodeMind AI on a single repository.",
    features: ["1 repository", "20 AI actions / month", "Cited Q&A and architecture graph", "Bug, security, and performance scanning"],
    cta: "Get started",
    href: "/register",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "$29",
    period: "/month",
    description: "For a small team shipping regularly.",
    features: ["10 repositories", "500 AI actions / month", "Everything in Free", "PR review with inline comments", "Propose-fix draft PRs"],
    cta: "Get started",
    href: "/register",
    highlighted: true,
  },
  {
    name: "Team",
    price: "$99",
    period: "/month",
    description: "For teams that have outgrown per-repo limits.",
    features: ["Unlimited repositories", "Unlimited AI actions", "Everything in Pro", "Priority support"],
    cta: "Get started",
    href: "/register",
    highlighted: false,
  },
];

export default function PricingPage() {
  return (
    <main className="mx-auto max-w-4xl px-6 py-24">
      <div className="mb-16 text-center">
        <h1 className="mb-3 text-3xl font-semibold">Pricing</h1>
        <p className="text-gray-400">
          Every plan includes cited answers, the architecture graph, and evidence-backed
          findings. Upgrade for more repositories and AI actions per month.
        </p>
      </div>

      <div className="grid gap-6 sm:grid-cols-3">
        {PLANS.map((plan) => (
          <div
            key={plan.name}
            className={`flex flex-col rounded border p-6 ${
              plan.highlighted ? "border-blue-600" : "border-gray-800"
            }`}
          >
            <h2 className="mb-1 font-medium">{plan.name}</h2>
            <p className="mb-4 text-sm text-gray-500">{plan.description}</p>
            <p className="mb-6">
              <span className="text-3xl font-semibold">{plan.price}</span>
              <span className="text-gray-500">{plan.period}</span>
            </p>
            <ul className="mb-8 flex flex-1 flex-col gap-2 text-sm text-gray-400">
              {plan.features.map((feature) => (
                <li key={feature}>{feature}</li>
              ))}
            </ul>
            <Link
              href={plan.href}
              className={`rounded px-4 py-2 text-center ${
                plan.highlighted
                  ? "bg-blue-600 text-white hover:bg-blue-500"
                  : "border border-gray-700 hover:bg-gray-800"
              }`}
            >
              {plan.cta}
            </Link>
          </div>
        ))}
      </div>

      <p className="mt-12 text-center text-sm text-gray-500">
        Already have an account?{" "}
        <Link href="/orgs" className="text-blue-400 hover:text-blue-300">
          Manage billing from your organization
        </Link>
        .
      </p>
    </main>
  );
}
