import { Skeleton } from "@/components/ui/skeleton";

export const LogItemSkeleton = () => (
  <div className="rounded-lg border bg-white p-4">
    {/* Date at the top */}
    <Skeleton className="mb-3 h-3 w-32" />

    {/* Main content */}
    <div className="space-y-2">
      <Skeleton className="h-5 w-3/4" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-2/3" />
    </div>

    {/* Bottom button area */}
    <div className="mt-3">
      <Skeleton className="h-8 w-28" />
    </div>
  </div>
);
