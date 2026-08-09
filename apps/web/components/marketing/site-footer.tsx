import Link from "next/link";

import { Logo } from "@/components/logo";
import { Separator } from "@/components/ui/separator";

const PRODUCT_LINKS = [
  { href: "/pricing", label: "Pricing" },
  { href: "/blog", label: "Blog" },
  { href: "/login", label: "Sign in" },
];

export function SiteFooter() {
  return (
    <footer className="border-t border-border/40">
      <div className="mx-auto max-w-6xl px-6 py-16">
        <div className="flex flex-col gap-10 sm:flex-row sm:justify-between">
          <div className="flex flex-col gap-3">
            <Link href="/" className="flex items-center gap-2.5">
              <Logo size={24} />
              <span className="font-semibold tracking-tight">CodeMind AI</span>
            </Link>
            <p className="max-w-xs text-sm text-muted-foreground">
              An AI staff engineer that indexes your repository and answers questions with
              citations.
            </p>
          </div>

          <div>
            <h3 className="mb-3 text-sm font-medium">Product</h3>
            <ul className="flex flex-col gap-2">
              {PRODUCT_LINKS.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <Separator className="my-10" />

        <p className="text-sm text-muted-foreground">
          &copy; {new Date().getFullYear()} CodeMind AI. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
