import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { LogItemSkeleton } from "./log-item-skeleton";

export const LogsContainerSkeleton = () => (
  <Card className="flex h-full flex-col">
    <CardHeader className="flex-shrink-0">
      <Skeleton className="h-6 w-32" />
      <Skeleton className="h-4 w-64" />
    </CardHeader>
    <CardContent className="min-h-0 flex-1 space-y-4">
      <LogItemSkeleton />
      <LogItemSkeleton />
      <LogItemSkeleton />
      <LogItemSkeleton />
      <LogItemSkeleton />
    </CardContent>
  </Card>
);
