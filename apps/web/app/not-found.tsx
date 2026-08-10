import Link from "next/link";

import { AuthShell } from "@/components/marketing/auth-shell";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <AuthShell>
      <div className="flex flex-col items-center gap-4 text-center">
        <p className="text-sm font-medium text-muted-foreground">404</p>
        <h1 className="text-2xl font-semibold tracking-tight">Page not found</h1>
        <p className="text-sm text-muted-foreground">
          The page you&apos;re looking for doesn&apos;t exist or may have moved.
        </p>
        <Button className="mt-2" nativeButton={false} render={<Link href="/" />}>
          Back home
        </Button>
      </div>
    </AuthShell>
  );
}
