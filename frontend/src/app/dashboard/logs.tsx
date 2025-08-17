import { useState } from "react";
import { useLogs } from "@/api/hooks/logs/use-logs";
import { LogItemCard } from "@/components/log-item-card";
import { LogsFilterBar } from "@/components/logs-filter-bar";
import { PageHeader } from "@/components/page-header";
import { ErrorAlert } from "@/components/ui/error-alert";
import { useDownloadLogs } from "@/api/hooks/logs/use-download-logs";
import {
  LogsContainer,
  LogsContainerSkeleton,
  LogsPagination,
} from "@/components/logs";

const DEFAULT_PAGE_SIZE = 20;

export const Logs = () => {
  const [fromDate, setFromDate] = useState<Date | undefined>(undefined);
  const [toDate, setToDate] = useState<Date | undefined>(undefined);
  const [type, setType] = useState<LogType | "ALL">("ALL");
  const [lastHours, setLastHours] = useState<number | undefined>(undefined);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);

  // Calculate offset for pagination
  const offset = (currentPage - 1) * pageSize;

  // Pass Date objects directly to the API
  const logsParams = {
    fromDate,
    toDate,
    type: type === "ALL" ? undefined : type,
    offset,
    limit: pageSize,
  };

  const { data: logsResponse, isPending, isError } = useLogs(logsParams);
  const downloadLogs = useDownloadLogs();

  if (isPending) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex-shrink-0 p-8 pb-0">
          <PageHeader
            title="Logs"
            description="View and download app activity logs"
          />
        </div>

        <div className="flex-1 overflow-hidden px-8 pt-6">
          <LogsContainerSkeleton />
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex-shrink-0 p-8 pb-0">
          <PageHeader
            title="Logs"
            description="View and download app activity logs"
          />
        </div>

        <div className="flex-1 overflow-hidden px-8 pt-6">
          <ErrorAlert
            message="Something went wrong"
            description="Failed to load logs. Please try again later."
          />
        </div>
      </div>
    );
  }

  const logs = logsResponse?.results || [];
  const totalCount = logsResponse?.count || 0;

  const handleDownload = () => {
    downloadLogs.mutate({
      fromDate,
      toDate,
      type: type === "ALL" ? undefined : type,
    });
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setCurrentPage(1); // Reset to first page when changing page size
  };

  // Reset pagination when filters change
  const resetPagination = () => {
    setCurrentPage(1);
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex-shrink-0 p-8 pb-0">
        <PageHeader
          title="Logs"
          description="View and download app activity logs"
        />

        <div className="mt-6">
          <LogsFilterBar
            fromDate={fromDate}
            toDate={toDate}
            type={type}
            lastHours={lastHours}
            onFromDateChange={(date) => {
              setFromDate(date);
              resetPagination();
            }}
            onToDateChange={(date) => {
              setToDate(date);
              resetPagination();
            }}
            onTypeChange={(newType) => {
              setType(newType);
              resetPagination();
            }}
            onLastHoursChange={(hours) => {
              setLastHours(hours);
              resetPagination();
            }}
            onDownload={handleDownload}
          />
        </div>
      </div>

      <div className="flex-1 overflow-hidden px-8 py-6">
        <LogsContainer>
          <div className="flex h-full flex-col">
            <div className="flex-1 overflow-y-auto">
              <div className="space-y-3">
                {logs.length === 0 ? (
                  <div className="text-muted-foreground py-12 text-center">
                    No logs found for the selected criteria.
                  </div>
                ) : (
                  logs.map((log) => <LogItemCard key={log.id} log={log} />)
                )}
              </div>
            </div>

            {/* Pagination */}
            {totalCount > 0 && (
              <div className="mt-6 flex-shrink-0">
                <LogsPagination
                  currentPage={currentPage}
                  totalCount={totalCount}
                  pageSize={pageSize}
                  onPageChange={handlePageChange}
                  onPageSizeChange={handlePageSizeChange}
                />
              </div>
            )}
          </div>
        </LogsContainer>
      </div>
    </div>
  );
};
