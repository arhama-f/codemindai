import { Skeleton } from "@/components/ui/skeleton";

export default function OrgsLoading() {
  return (
    <main className="mx-auto max-w-2xl px-6 py-12">
      <Skeleton className="mb-6 h-8 w-48" />
      <div className="flex flex-col gap-2">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
      </div>
    </main>
  );
}
