import {
  FileSearch,
  GitPullRequest,
  Network,
  ShieldCheck,
  Sparkles,
  Wrench,
} from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const FEATURES = [
  {
    icon: FileSearch,
    title: "Cited answers, not guesses",
    description:
      "Ask a question about your codebase and get an answer with exact file paths and line ranges backing it up — never a confident-sounding hallucination.",
  },
  {
    icon: Network,
    title: "Real architecture graph",
    description:
      "Indexing resolves every import to build an actual dependency graph, then groups files into labeled subsystems you can drill into.",
  },
  {
    icon: ShieldCheck,
    title: "Evidence-backed bug detection",
    description:
      "Findings come from targeted checks against real code, not an open-ended \"find bugs\" prompt — every finding links back to the exact evidence that triggered it.",
  },
  {
    icon: GitPullRequest,
    title: "PR review that only comments on what changed",
    description:
      "Reviews analyze just the diff's added lines and post real inline comments plus a commit status — no noise on code you didn't touch.",
  },
  {
    icon: Wrench,
    title: "Propose-fix draft PRs",
    description:
      "Turn a finding into a draft pull request with a working fix and a test, ready for you to review before it ever touches your branch.",
  },
  {
    icon: Sparkles,
    title: "Bug, security & performance scanning",
    description:
      "Targeted checks for unguarded operations, unsanitized input, and missed batching — each one grounded in the code that triggered it.",
  },
];

const STEPS = [
  {
    number: "01",
    title: "Connect a repository",
    description: "Point CodeMind AI at a GitHub repo — no config files, no setup scripts.",
  },
  {
    number: "02",
    title: "Index it",
    description: "Tree-sitter parses every file, extracting symbols, imports, and a real dependency graph.",
  },
  {
    number: "03",
    title: "Ask, scan, and review",
    description: "Get cited answers, evidence-backed findings, and PR reviews — all grounded in your actual code.",
  },
];

export default function HomePage() {
  return (
    <main>
      <section className="mx-auto max-w-6xl px-6 pt-20 pb-24 md:pt-28 md:pb-32">
        <div className="mx-auto flex max-w-3xl flex-col items-center gap-6 text-center">
          <Badge variant="secondary" className="h-auto px-3 py-1 text-xs">
            Now indexing repositories with real citations
          </Badge>
          <h1 className="text-5xl font-semibold tracking-tight text-balance md:text-6xl lg:text-7xl lg:leading-[1.05]">
            An AI staff engineer that actually reads your code
          </h1>
          <p className="max-w-2xl text-lg text-muted-foreground md:text-xl">
            CodeMind AI indexes your repository, builds a real dependency graph, and answers
            questions with citations — so you can trust what it tells you, not just believe it.
          </p>
          <div className="mt-2 flex flex-col gap-3 sm:flex-row">
            <Button size="lg" nativeButton={false} render={<Link href="/register" />}>
              Get started
            </Button>
            <Button size="lg" variant="outline" nativeButton={false} render={<Link href="/pricing" />}>
              View pricing
            </Button>
          </div>
        </div>

        <Card className="mx-auto mt-16 max-w-2xl border-border/60 p-6 text-left shadow-sm md:p-8">
          <p className="mb-4 text-sm font-medium text-muted-foreground">
            You asked: <span className="text-foreground">&quot;Why does checkout fail for zero-quantity carts?&quot;</span>
          </p>
          <p className="mb-4 text-sm leading-relaxed text-foreground">
            The checkout total is computed by dividing the cart subtotal by item count without
            guarding against zero, which throws before the payment step ever runs.
          </p>
          <div className="flex items-center gap-2 rounded-lg border border-border bg-muted/40 px-3 py-2 font-mono text-xs text-muted-foreground">
            <FileSearch className="size-3.5 shrink-0" />
            src/checkout/pricing.ts:42-47
          </div>
        </Card>
      </section>

      <section className="border-t border-border/40 bg-card/30">
        <div className="mx-auto max-w-6xl px-6 py-24 md:py-32">
          <div className="mx-auto mb-16 max-w-2xl text-center">
            <h2 className="text-3xl font-semibold tracking-tight md:text-4xl">
              Everything grounded in your actual code
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              No open-ended prompts guessing at problems — every answer, finding, and review
              traces back to real evidence.
            </p>
          </div>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((feature) => (
              <Card
                key={feature.title}
                className="gap-3 border-border/60 p-6 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg md:p-8"
              >
                <feature.icon className="size-5 text-primary" />
                <h3 className="text-xl font-semibold">{feature.title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {feature.description}
                </p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-24 md:py-32">
        <div className="mx-auto mb-16 max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight md:text-4xl">How it works</h2>
        </div>
        <div className="grid gap-10 md:grid-cols-3 md:gap-8">
          {STEPS.map((step) => (
            <div key={step.number} className="flex flex-col gap-3">
              <span className="text-sm font-medium text-primary">{step.number}</span>
              <h3 className="text-xl font-semibold">{step.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{step.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-t border-border/40">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-6 px-6 py-24 text-center md:py-32">
          <h2 className="text-3xl font-semibold tracking-tight md:text-4xl">
            Understand your codebase in minutes, not weeks
          </h2>
          <Button size="lg" nativeButton={false} render={<Link href="/register" />}>
            Get started
          </Button>
        </div>
      </section>
    </main>
  );
}
