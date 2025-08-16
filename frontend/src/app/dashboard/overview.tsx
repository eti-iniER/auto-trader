import { useStats } from "@/api/hooks/stats/use-stats";
import {
  ActivityCard,
  ActivityCardSkeleton,
  StatCard,
  StatCardSkeleton,
} from "@/components/overview";
import { PageHeader } from "@/components/page-header";
import { FileChartColumn } from "lucide-react";
import { FiPieChart, FiShoppingCart } from "react-icons/fi";
import { MdAccessTime, MdErrorOutline } from "react-icons/md";

export const Overview = () => {
  const { data: stats, isPending, isError } = useStats();

  if (isError) {
    return (
      <div className="flex-1 p-4 sm:p-8">
        <PageHeader
          title="Overview"
          description="Everything you need to know at a glance"
        />
        <div className="flex h-64 items-center justify-center">
          <div className="text-center">
            <MdErrorOutline className="mx-auto mb-4 h-12 w-12 text-red-500" />
            <p className="mb-2 font-medium text-red-600">
              Error loading overview data
            </p>
            <p className="text-muted-foreground text-sm">
              Please check your connection and try again
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (isPending) {
    return (
      <div className="flex min-h-0 flex-1 flex-col p-4 sm:p-8">
        <PageHeader
          title="Overview"
          description="Everything you need to know at a glance"
        />
        <div className="flex min-h-0 flex-1 flex-col space-y-6">
          {/* Stats Cards Skeleton */}
          <div className="grid flex-shrink-0 grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
          </div>

          {/* Recent Activity Skeleton */}
          <div className="min-h-0 flex-1">
            <ActivityCardSkeleton />
          </div>
        </div>
      </div>
    );
  }

  const formatTimestamp = (timestamp: Date) => {
    return new Date(timestamp).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col p-4 sm:p-8">
      <PageHeader
        title="Overview"
        description="Everything you need to know at a glance"
      />

      <div className="flex min-h-0 flex-1 flex-col space-y-6">
        {/* Stats Cards */}
        <div className="grid flex-shrink-0 grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Open positions"
            value={stats?.openPositionsCount || 0}
            icon={FiPieChart}
            description="Currently active trades"
            variant={stats?.openPositionsCount ? "success" : "default"}
          />
          <StatCard
            title="Pending orders"
            value={stats?.openOrdersCount || 0}
            icon={FiShoppingCart}
            description="Orders waiting execution"
            variant={stats?.openOrdersCount ? "warning" : "default"}
          />
          <StatCard
            title="Activities in the last 6 hours"
            value={stats?.recentActivities?.length || 0}
            icon={FileChartColumn}
            description="Latest activities"
          />
          <StatCard
            title="Last updated"
            value={
              stats?.statsTimestamp
                ? formatTimestamp(stats.statsTimestamp)
                : "—"
            }
            icon={MdAccessTime}
            description="Data refresh time"
          />
        </div>

        {/* Recent Activity */}
        <div className="min-h-0 flex-1">
          <ActivityCard activities={stats?.recentActivities} />
        </div>
      </div>
    </div>
  );
};
