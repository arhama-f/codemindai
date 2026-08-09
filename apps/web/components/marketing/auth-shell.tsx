import Link from "next/link";

import { Logo } from "@/components/logo";

export function AuthShell({ children }: { children: React.ReactNode }) {
  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col items-center justify-center gap-6 px-6 py-24">
      <Link href="/" className="flex items-center gap-2.5">
        <Logo size={32} />
        <span className="font-semibold tracking-tight">CodeMind AI</span>
      </Link>
      <div className="w-full">{children}</div>
    </main>
  );
}
