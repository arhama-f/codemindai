import type { Metadata } from "next";
import { Check } from "lucide-react";
import Link from "next/link";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export const metadata: Metadata = {
  title: "Pricing — CodeMind AI",
  description: "Simple, usage-based pricing for CodeMind AI.",
  openGraph: {
    title: "Pricing — CodeMind AI",
    description: "Simple, usage-based pricing for CodeMind AI.",
  },
};

const PLANS = [
  {
    name: "Free",
    price: "$0",
    period: "",
    description: "Try CodeMind AI on a single repository.",
    features: [
      "1 repository",
      "20 AI actions / month",
      "Cited Q&A and architecture graph",
      "Bug, security, and performance scanning",
    ],
    cta: "Get started",
    href: "/register",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "$29",
    period: "/month",
    description: "For a small team shipping regularly.",
    features: [
      "10 repositories",
      "500 AI actions / month",
      "Everything in Free",
      "PR review with inline comments",
      "Propose-fix draft PRs",
    ],
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

const FAQS = [
  {
    question: "What counts as an AI action?",
    answer:
      "Any on-demand AI call: asking a question, explaining a finding, proposing a fix, or reviewing a PR. Indexing a repository also uses a small number of AI actions for summarization.",
  },
  {
    question: "Can I change plans later?",
    answer:
      "Yes — upgrade or downgrade at any time from your organization's billing page. Changes take effect immediately and are prorated.",
  },
  {
    question: "Do you offer a trial?",
    answer:
      "The Free plan itself works as an open-ended trial — one repository, no time limit, no credit card required.",
  },
  {
    question: "What happens if I go over my plan's limits?",
    answer:
      "You'll be prompted to upgrade before any action that would exceed your plan's repository or AI-action limit — nothing is throttled or billed unexpectedly.",
  },
];

export default function PricingPage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-24 md:py-32">
      <div className="mx-auto mb-16 max-w-2xl text-center">
        <h1 className="text-4xl font-semibold tracking-tight md:text-5xl">Pricing</h1>
        <p className="mt-4 text-lg text-muted-foreground">
          Every plan includes cited answers, the architecture graph, and evidence-backed
          findings. Upgrade for more repositories and AI actions per month.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {PLANS.map((plan) => (
          <div key={plan.name} className="relative">
            {plan.highlighted && (
              <Badge className="absolute -top-3 left-1/2 z-10 -translate-x-1/2">
                Most popular
              </Badge>
            )}
            <Card
              className={`flex h-full flex-col gap-0 p-6 shadow-sm md:p-8 ${
                plan.highlighted ? "border-primary" : "border-border/60"
              }`}
            >
              <h2 className="mb-1 text-xl font-semibold">{plan.name}</h2>
              <p className="mb-6 text-sm text-muted-foreground">{plan.description}</p>
              <p className="mb-6">
                <span className="text-4xl font-semibold tracking-tight">{plan.price}</span>
                <span className="text-muted-foreground">{plan.period}</span>
              </p>
              <ul className="mb-8 flex flex-1 flex-col gap-3 text-sm">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2">
                    <Check className="mt-0.5 size-4 shrink-0 text-primary" />
                    <span className="text-muted-foreground">{feature}</span>
                  </li>
                ))}
              </ul>
              <Button
                variant={plan.highlighted ? "default" : "outline"}
                nativeButton={false}
                render={<Link href={plan.href} />}
              >
                {plan.cta}
              </Button>
            </Card>
          </div>
        ))}
      </div>

      <div className="mx-auto mt-32 max-w-2xl">
        <h2 className="mb-8 text-center text-3xl font-semibold tracking-tight">
          Frequently asked questions
        </h2>
        <Accordion>
          {FAQS.map((faq) => (
            <AccordionItem key={faq.question} value={faq.question}>
              <AccordionTrigger>{faq.question}</AccordionTrigger>
              <AccordionContent>
                <p className="text-muted-foreground">{faq.answer}</p>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>

      <p className="mt-16 text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link href="/orgs" className="text-primary hover:underline">
          Manage billing from your organization
        </Link>
        .
      </p>
    </main>
  );
}
