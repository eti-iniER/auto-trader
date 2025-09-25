import { useDownloadLogs } from "@/api/hooks/logs/use-download-logs";
import { useDeleteLogs } from "@/api/hooks/logs/use-delete-logs";
import { useLogs } from "@/api/hooks/logs/use-logs";
import {
  LogItemCard,
  LogsContainer,
  LogsContainerSkeleton,
  LogsFilterBar,
  LogsPagination,
} from "@/components/logs";
import { PageHeader } from "@/components/page-header";
import { ErrorAlert } from "@/components/ui/error-alert";
import { usePagination } from "@/hooks/use-pagination";
import { useModal } from "@/hooks/use-modal";
import { useState } from "react";
import { DeleteAllLogsDialog } from "./delete-all-logs-dialog";

export const Logs = () => {
  const [fromDate, setFromDate] = useState<Date | undefined>(undefined);
  const [toDate, setToDate] = useState<Date | undefined>(undefined);
  const [type, setType] = useState<LogType | "ALL">("ALL");
  const [lastHours, setLastHours] = useState<number | undefined>(undefined);
  const pagination = usePagination({ initialPageSize: 20 });
  const deleteAllDialog = useModal();

  // Pass Date objects directly to the API
  const logsParams = {
    fromDate,
    toDate,
    type: type === "ALL" ? undefined : type,
    offset: pagination.offset,
    limit: pagination.pageSize,
  };

  const { data: logsResponse, isPending, isError } = useLogs(logsParams);
  const downloadLogs = useDownloadLogs();
  const deleteLogs = useDeleteLogs();

  if (isPending) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex-shrink-0 p-4 pb-0 lg:p-8 lg:pb-0">
          <PageHeader
            title="Logs"
            description="View and download app activity logs"
          />
        </div>

        <div className="min-h-0 flex-1 overflow-hidden p-4 pt-4 lg:px-8 lg:pt-6">
          <LogsContainerSkeleton />
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex-shrink-0 p-4 pb-0 lg:p-8 lg:pb-0">
          <PageHeader
            title="Logs"
            description="View and download app activity logs"
          />
        </div>

        <div className="min-h-0 flex-1 overflow-hidden p-4 pt-4 lg:px-8 lg:pt-6">
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

  // Reset pagination when filters change
  const resetPagination = () => {
    pagination.setPage(1);
  };

  const handleReset = () => {
    setFromDate(undefined);
    setToDate(undefined);
    setType("ALL");
    setLastHours(undefined);
    pagination.reset();
  };

  const handleDeleteAllLogs = () => {
    deleteAllDialog.openModal();
  };

  const handleConfirmDeleteAll = () => {
    deleteLogs.mutate();
    deleteAllDialog.closeModal();
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header - always visible */}
      <div className="flex-shrink-0 p-4 pb-0 lg:p-8 lg:pb-0">
        <PageHeader
          title="Logs"
          description="View and download app activity logs"
        />

        {/* Filter bar - reduced padding on mobile */}
        <div className="mt-4 lg:mt-6">
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
            onReset={handleReset}
            onDeleteAllLogs={handleDeleteAllLogs}
          />
        </div>
      </div>

      {/* Logs container - scrollable area with minimum height */}
      <div className="min-h-0 flex-1 overflow-hidden p-4 pt-4 lg:px-8 lg:py-6">
        <LogsContainer>
          <div className="flex h-full flex-col">
            <div className="min-h-0 flex-1 overflow-y-auto">
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
              <div className="mt-4 flex-shrink-0 lg:mt-6">
                <LogsPagination
                  currentPage={pagination.page}
                  totalCount={totalCount}
                  pageSize={pagination.pageSize}
                  onPageChange={pagination.handlePageChange}
                  onPageSizeChange={pagination.handlePageSizeChange}
                />
              </div>
            )}
          </div>
        </LogsContainer>
      </div>

      {/* Delete All Logs Dialog */}
      <DeleteAllLogsDialog
        isOpen={deleteAllDialog.isOpen}
        onClose={deleteAllDialog.closeModal}
        onConfirm={handleConfirmDeleteAll}
        loading={deleteLogs.isPending}
      />
    </div>
  );
};
