import Link from "next/link";

export default function HomePage() {
  return (
    <main className="mx-auto flex max-w-2xl flex-col items-start gap-6 px-6 py-24">
      <h1 className="text-3xl font-semibold">CodeMind AI</h1>
      <p className="text-gray-400">
        Connect a repository, index it, and ask questions with cited answers.
      </p>
      <div className="flex gap-4">
        <Link href="/register" className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-500">
          Get started
        </Link>
        <Link href="/login" className="rounded border border-gray-700 px-4 py-2 hover:bg-gray-800">
          Sign in
        </Link>
      </div>
    </main>
  );
}
