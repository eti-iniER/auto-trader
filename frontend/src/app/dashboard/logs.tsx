import { useState } from "react";
import { useLogs } from "@/api/hooks/logs/use-logs";
import { LogItemCard } from "@/components/log-item-card";
import { LogsFilterBar } from "@/components/logs-filter-bar";
import { PageHeader } from "@/components/page-header";
import { Skeleton } from "@/components/ui/skeleton";

export const Logs = () => {
  const [fromDate, setFromDate] = useState<Date | undefined>(undefined);
  const [toDate, setToDate] = useState<Date | undefined>(undefined);
  const [type, setType] = useState<LogType | "ALL">("ALL");

  // Pass Date objects directly to the API
  const logsParams = {
    from_date: fromDate,
    to_date: toDate,
    type: type === "ALL" ? undefined : type,
  };

  const { data: logsResponse, isPending, isError } = useLogs(logsParams);

  if (isPending) {
    return <Skeleton className="h-full w-full" />;
  }

  if (isError) {
    return (
      <div>
        <h1>Something went wrong</h1>
      </div>
    );
  }

  const logs = logsResponse?.results || [];

  const handleDownload = () => {
    // TODO: Implement download logic
    console.log("Download logs functionality to be implemented");
  };

  return (
    <div className="flex h-full flex-col p-8">
      <PageHeader
        title="Logs"
        description="View and download app activity logs"
      />

      <div className="mt-6">
        <LogsFilterBar
          fromDate={fromDate}
          toDate={toDate}
          type={type}
          onFromDateChange={setFromDate}
          onToDateChange={setToDate}
          onTypeChange={setType}
          onDownload={handleDownload}
        />
      </div>

      <div className="mt-6 flex-1 overflow-y-auto">
        <div className="space-y-3 p-4">
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
  );
};
