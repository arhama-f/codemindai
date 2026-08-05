import Link from "next/link";

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-gray-800">
        <nav className="mx-auto flex max-w-4xl items-center justify-between px-6 py-4">
          <Link href="/" className="font-semibold">
            CodeMind AI
          </Link>
          <div className="flex items-center gap-6 text-sm">
            <Link href="/blog" className="text-gray-400 hover:text-gray-200">
              Blog
            </Link>
            <Link href="/login" className="text-gray-400 hover:text-gray-200">
              Sign in
            </Link>
            <Link
              href="/register"
              className="rounded bg-blue-600 px-3 py-1.5 text-white hover:bg-blue-500"
            >
              Get started
            </Link>
          </div>
        </nav>
      </header>
      <div className="flex-1">{children}</div>
      <footer className="border-t border-gray-800">
        <div className="mx-auto max-w-4xl px-6 py-8 text-sm text-gray-500">
          &copy; {new Date().getFullYear()} CodeMind AI
        </div>
      </footer>
    </div>
  );
}
