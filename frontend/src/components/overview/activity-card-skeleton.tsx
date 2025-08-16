import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

const ActivitySkeleton = () => (
  <div className="rounded-lg border p-4">
    <div className="mb-2 flex items-center gap-2">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-5 w-16" />
    </div>
    <Skeleton className="mb-2 h-4 w-full" />
    <div className="flex items-center gap-2">
      <Skeleton className="h-3 w-3" />
      <Skeleton className="h-3 w-20" />
      <Skeleton className="h-3 w-1" />
      <Skeleton className="h-3 w-16" />
    </div>
  </div>
);

export const ActivityCardSkeleton = () => (
  <Card className="flex h-full flex-col border shadow-none">
    <CardHeader className="flex-shrink-0">
      <div className="flex items-center gap-2">
        <Skeleton className="h-5 w-5" />
        <Skeleton className="h-6 w-32" />
      </div>
    </CardHeader>
    <CardContent className="min-h-0 flex-1 space-y-4">
      <ActivitySkeleton />
      <ActivitySkeleton />
      <ActivitySkeleton />
    </CardContent>
  </Card>
);
