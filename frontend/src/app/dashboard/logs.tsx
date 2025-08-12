import { useState } from "react";
import { useLogs } from "@/api/hooks/logs/use-logs";
import { LogItemCard } from "@/components/log-item-card";
import { LogsFilterBar } from "@/components/logs-filter-bar";
import { PageHeader } from "@/components/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorAlert } from "@/components/ui/error-alert";
import { useDownloadLogs } from "@/api/hooks/logs/use-download-logs";

export const Logs = () => {
  const [fromDate, setFromDate] = useState<Date | undefined>(undefined);
  const [toDate, setToDate] = useState<Date | undefined>(undefined);
  const [type, setType] = useState<LogType | "ALL">("ALL");
  const [lastHours, setLastHours] = useState<number | undefined>(undefined);

  // Pass Date objects directly to the API
  const logsParams = {
    fromDate,
    toDate,
    type: type === "ALL" ? undefined : type,
  };

  const { data: logsResponse, isPending, isError } = useLogs(logsParams);
  const downloadLogs = useDownloadLogs();

  if (isPending) {
    return <Skeleton className="h-full w-full" />;
  }

  if (isError) {
    return (
      <ErrorAlert
        message="Something went wrong"
        description="Failed to load logs. Please try again later."
      />
    );
  }

  const logs = logsResponse?.results || [];

  const handleDownload = () => {
    downloadLogs.mutate({
      fromDate,
      toDate,
      type: type === "ALL" ? undefined : type,
    });
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
            onFromDateChange={setFromDate}
            onToDateChange={setToDate}
            onTypeChange={setType}
            onLastHoursChange={setLastHours}
            onDownload={handleDownload}
          />
        </div>
      </div>

      <div className="flex-1 overflow-hidden px-8 pt-6">
        <div className="h-full overflow-y-auto">
          <div className="space-y-3 pb-8">
            {logs.length === 0 ? (
              <div className="text-muted-foreground py-8 text-center">
                No logs found.
              </div>
            ) : (
              logs.map((log) => <LogItemCard key={log.id} log={log} />)
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
