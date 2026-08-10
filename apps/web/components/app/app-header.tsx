import Link from "next/link";

import { OrgSwitcher } from "@/components/app/org-switcher";
import { UserMenu } from "@/components/app/user-menu";
import { Logo } from "@/components/logo";

export function AppHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
        <div className="flex items-center gap-2">
          <Link href="/orgs" className="flex items-center gap-2.5">
            <Logo size={24} />
          </Link>
          <span className="text-muted-foreground/40">/</span>
          <OrgSwitcher />
        </div>
        <UserMenu />
      </div>
    </header>
  );
}
