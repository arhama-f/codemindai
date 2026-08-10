"use client";

import { Button } from "@/components/ui/button";

export default function OrgsError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="mx-auto flex max-w-2xl flex-col items-center gap-4 px-6 py-24 text-center">
      <p className="text-sm font-medium text-muted-foreground">Error</p>
      <h1 className="text-2xl font-semibold tracking-tight">Something went wrong</h1>
      <p className="text-sm text-muted-foreground">
        An unexpected error occurred while loading this page.
      </p>
      <Button className="mt-2" onClick={reset}>
        Try again
      </Button>
    </main>
  );
}
