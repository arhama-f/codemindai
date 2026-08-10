"use client";

import { AuthShell } from "@/components/marketing/auth-shell";
import { Button } from "@/components/ui/button";

export default function MarketingError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <AuthShell>
      <div className="flex flex-col items-center gap-4 text-center">
        <p className="text-sm font-medium text-muted-foreground">Error</p>
        <h1 className="text-2xl font-semibold tracking-tight">Something went wrong</h1>
        <p className="text-sm text-muted-foreground">
          An unexpected error occurred while loading this page.
        </p>
        <Button className="mt-2" onClick={reset}>
          Try again
        </Button>
      </div>
    </AuthShell>
  );
}
