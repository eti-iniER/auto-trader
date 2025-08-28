import { usePositions } from "@/api/hooks/positions/use-positions";
import { PageHeader } from "@/components/page-header";
import { PositionsTable } from "@/components/positions-table";
import { useDashboardContext } from "@/hooks/contexts/use-dashboard-context";
import { useUserIGSettingsStatus } from "@/hooks/use-user-ig-settings-status";
import { useState } from "react";
import { MdErrorOutline } from "react-icons/md";

export const Positions = () => {
  const { settings } = useDashboardContext();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const offset = (page - 1) * pageSize;
  const status = useUserIGSettingsStatus(settings);

  const {
    data: positionsResponse,
    isPending,
    isError,
    error,
  } = usePositions(
    {
      offset,
      limit: pageSize,
    },
    status === "complete",
  );

  const positions = positionsResponse?.results || [];
  const totalCount = positionsResponse?.count || 0;

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setPage(1);
  };

  if (status === "incomplete") {
    return (
      <div className="flex-1 p-4 sm:p-8">
        <PageHeader title="Positions" description="View your open positions" />
        <div className="flex h-64 items-center justify-center">
          <div className="text-center">
            <MdErrorOutline className="mx-auto mb-4 h-12 w-12 text-yellow-500" />
            <p className="mb-2 font-medium text-yellow-600">
              IG settings incomplete
            </p>
            <p className="text-muted-foreground text-sm">
              Please complete your IG settings to view positions data
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="min-w-0 flex-1 space-y-8 p-8">
        <PageHeader title="Positions" description="View your open positions" />
        <div className="flex h-64 items-center justify-center">
          <div className="text-center">
            <p className="mb-2 text-red-600">Error loading positions</p>
            <p className="text-sm text-gray-500">
              {error?.message || "Something went wrong"}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col space-y-8 p-8">
      <PageHeader title="Positions" description="View your open positions" />

      <div className="min-h-0 flex-1">
        <PositionsTable
          data={positions}
          loading={isPending}
          pagination={{
            page,
            pageSize,
            totalCount,
            onPageChange: handlePageChange,
            onPageSizeChange: handlePageSizeChange,
          }}
        />
      </div>
    </div>
  );
};
