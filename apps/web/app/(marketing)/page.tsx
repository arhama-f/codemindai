import Link from "next/link";

const FEATURES = [
  {
    title: "Cited answers, not guesses",
    description:
      "Ask a question about your codebase and get an answer with exact file paths and line ranges backing it up — never a confident-sounding hallucination.",
  },
  {
    title: "Real architecture graph",
    description:
      "Indexing resolves every import to build an actual dependency graph, then groups files into labeled subsystems you can drill into.",
  },
  {
    title: "Evidence-backed bug detection",
    description:
      "Findings come from targeted checks against real code, not an open-ended \"find bugs\" prompt — every finding links back to the exact evidence that triggered it.",
  },
  {
    title: "PR review that only comments on what changed",
    description:
      "Reviews analyze just the diff's added lines and post real inline comments plus a commit status — no noise on code you didn't touch.",
  },
];

export default function HomePage() {
  return (
    <main className="mx-auto max-w-4xl px-6 py-24">
      <div className="flex flex-col items-start gap-6">
        <h1 className="text-4xl font-semibold">
          An AI staff engineer that actually reads your code
        </h1>
        <p className="max-w-2xl text-lg text-gray-400">
          CodeMind AI indexes your repository, builds a real dependency graph, and answers
          questions with citations — so you can trust what it tells you, not just believe it.
        </p>
        <div className="flex gap-4">
          <Link
            href="/register"
            className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-500"
          >
            Get started
          </Link>
          <Link
            href="/pricing"
            className="rounded border border-gray-700 px-4 py-2 hover:bg-gray-800"
          >
            View pricing
          </Link>
        </div>
      </div>

      <div className="mt-20 grid gap-8 sm:grid-cols-2">
        {FEATURES.map((feature) => (
          <div key={feature.title} className="rounded border border-gray-800 p-6">
            <h2 className="mb-2 font-medium">{feature.title}</h2>
            <p className="text-sm text-gray-400">{feature.description}</p>
          </div>
        ))}
      </div>
    </main>
  );
}
