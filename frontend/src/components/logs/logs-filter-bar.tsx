import { useState } from "react";
import { Button } from "@/components/ui/button";
import { DatePicker } from "@/components/ui/date-picker";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  LuChevronDown,
  LuDownload,
  LuRotateCcw,
  LuTrash2,
} from "react-icons/lu";

interface LogsFilterBarProps {
  fromDate?: Date;
  toDate?: Date;
  type?: LogType | "ALL";
  lastHours?: number;
  onFromDateChange: (date: Date | undefined) => void;
  onToDateChange: (date: Date | undefined) => void;
  onTypeChange: (logType: LogType | "ALL") => void;
  onLastHoursChange: (hours: number | undefined) => void;
  onDownload: () => void;
  onReset: () => void;
  onDeleteAllLogs: () => void;
}

const LOG_TYPE_OPTIONS: { value: LogType | "ALL"; label: string }[] = [
  { value: "ALL", label: "All types" },
  { value: "UNSPECIFIED", label: "Unspecified" },
  { value: "AUTHENTICATION", label: "Authentication" },
  { value: "ALERT", label: "Alert" },
  { value: "TRADE", label: "Trade" },
  { value: "ORDER", label: "Order" },
  { value: "ERROR", label: "Error" },
];

export const LogsFilterBar = ({
  fromDate,
  toDate,
  type,
  lastHours,
  onFromDateChange,
  onToDateChange,
  onTypeChange,
  onLastHoursChange,
  onDownload,
  onReset,
  onDeleteAllLogs,
}: LogsFilterBarProps) => {
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const handleLastHoursChange = (value: string) => {
    const hours = value === "" ? undefined : parseInt(value, 10);
    if (hours && hours > 0) {
      const now = new Date();
      const from = new Date(now.getTime() - hours * 60 * 60 * 1000);
      onFromDateChange(from);
      onToDateChange(now);
    }
    onLastHoursChange(hours);
  };

  return (
    <div className="bg-background rounded-lg border p-3 lg:p-4">
      {/* Mobile layout: collapsible */}
      <div className="lg:hidden">
        <button
          type="button"
          className="bg-card flex w-full items-center justify-between rounded-md border px-3 py-2 text-sm font-medium"
          onClick={() => setIsMobileOpen((o) => !o)}
          aria-expanded={isMobileOpen}
          aria-controls="logs-filter-mobile"
        >
          <span>Filter</span>
          <LuChevronDown
            className={`h-4 w-4 transition-transform ${isMobileOpen ? "rotate-180" : "rotate-0"}`}
          />
        </button>

        <div
          id="logs-filter-mobile"
          className={`${isMobileOpen ? "mt-3" : "hidden"}`}
        >
          <div className="flex flex-col gap-3">
            {/* Date filters */}
            <div className="flex flex-col gap-2">
              <div className="flex flex-col gap-1.5">
                <label htmlFor="from-date" className="text-sm font-medium">
                  From
                </label>
                <DatePicker
                  date={fromDate}
                  onDateChange={onFromDateChange}
                  placeholder="Select start date"
                  className="w-full"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="to-date" className="text-sm font-medium">
                  To
                </label>
                <DatePicker
                  date={toDate}
                  onDateChange={onToDateChange}
                  placeholder="Select end date"
                  className="w-full"
                />
              </div>
            </div>

            {/* Quick filters */}
            <div className="flex flex-col gap-2">
              <div className="flex flex-col gap-1.5">
                <label htmlFor="last-hours" className="text-sm font-medium">
                  Last (hours)
                </label>
                <Input
                  id="last-hours"
                  type="number"
                  min="1"
                  placeholder="24"
                  value={lastHours || ""}
                  onChange={(e) => handleLastHoursChange(e.target.value)}
                  className="w-full"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label htmlFor="log-type" className="text-sm font-medium">
                  Type
                </label>
                <Select
                  value={type || "ALL"}
                  onValueChange={(value) =>
                    onTypeChange(value as LogType | "ALL")
                  }
                >
                  <SelectTrigger className="w-full" id="log-type">
                    <SelectValue placeholder="All types" />
                  </SelectTrigger>
                  <SelectContent>
                    {LOG_TYPE_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Action buttons row */}
            <div className="flex flex-col gap-2 sm:flex-row sm:gap-2">
              <Button
                onClick={onReset}
                variant="default"
                className="w-full sm:w-auto"
              >
                <LuRotateCcw className="h-4 w-4" />
                Reset filters
              </Button>
              <Button
                onClick={onDownload}
                variant="default"
                className="w-full sm:w-auto"
              >
                <LuDownload className="h-4 w-4" />
                Download
              </Button>
              <Button
                onClick={onDeleteAllLogs}
                variant="destructive"
                className="w-full sm:w-auto"
              >
                <LuTrash2 className="h-4 w-4" />
                Delete all
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Desktop layout: horizontal */}
      <div className="hidden lg:flex lg:flex-wrap lg:items-center lg:gap-4 xl:flex-nowrap">
        <div className="flex items-center gap-2">
          <label htmlFor="from-date-desktop" className="text-sm font-medium">
            From
          </label>
          <DatePicker
            date={fromDate}
            onDateChange={onFromDateChange}
            placeholder="Select start date"
          />
        </div>

        <div className="flex items-center gap-2">
          <label htmlFor="to-date-desktop" className="text-sm font-medium">
            To
          </label>
          <DatePicker
            date={toDate}
            onDateChange={onToDateChange}
            placeholder="Select end date"
          />
        </div>

        {/* Vertical separator */}
        <div className="bg-border hidden h-6 w-px xl:block"></div>

        <div className="flex items-center gap-2">
          <label htmlFor="last-hours-desktop" className="text-sm font-medium">
            Last
          </label>
          <Input
            id="last-hours-desktop"
            type="number"
            min="1"
            placeholder="24"
            value={lastHours || ""}
            onChange={(e) => handleLastHoursChange(e.target.value)}
            className="w-20"
          />
          <span className="text-muted-foreground text-sm">hours</span>
        </div>

        <div className="flex items-center gap-2">
          <label htmlFor="log-type-desktop" className="text-sm font-medium">
            Type
          </label>
          <Select
            value={type || "ALL"}
            onValueChange={(value) => onTypeChange(value as LogType | "ALL")}
          >
            <SelectTrigger className="w-40" id="log-type-desktop">
              <SelectValue placeholder="All types" />
            </SelectTrigger>
            <SelectContent>
              {LOG_TYPE_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="ml-auto flex flex-wrap items-center gap-2 lg:w-auto lg:min-w-0">
          <Button
            onClick={onReset}
            variant="default"
            className="whitespace-nowrap"
          >
            <LuRotateCcw className="h-4 w-4" />
            <span className="hidden xl:inline">Reset filters</span>
          </Button>
          <Button
            onClick={onDownload}
            variant="default"
            className="whitespace-nowrap"
          >
            <LuDownload className="h-4 w-4" />
            <span className="hidden xl:inline">Download</span>
          </Button>
          <Button
            onClick={onDeleteAllLogs}
            variant="destructive"
            className="whitespace-nowrap"
          >
            <LuTrash2 className="h-4 w-4" />
            <span className="hidden xl:inline">Delete all</span>
          </Button>
        </div>
      </div>
    </div>
  );
};
