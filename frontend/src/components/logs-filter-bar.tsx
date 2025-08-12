import { DownloadIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DatePicker } from "@/components/ui/date-picker";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface LogsFilterBarProps {
  fromDate?: Date;
  toDate?: Date;
  type?: LogType | "ALL";
  onFromDateChange: (date: Date | undefined) => void;
  onToDateChange: (date: Date | undefined) => void;
  onTypeChange: (logType: LogType | "ALL") => void;
  onDownload: () => void;
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
  onFromDateChange,
  onToDateChange,
  onTypeChange,
  onDownload,
}: LogsFilterBarProps) => {
  return (
    <div className="bg-background flex items-center gap-4 rounded-lg border p-4">
      <div className="flex items-center gap-2">
        <label htmlFor="from-date" className="text-sm font-medium">
          From
        </label>
        <DatePicker
          date={fromDate}
          onDateChange={onFromDateChange}
          placeholder="Select start date"
        />
      </div>

      <div className="flex items-center gap-2">
        <label htmlFor="to-date" className="text-sm font-medium">
          To
        </label>
        <DatePicker
          date={toDate}
          onDateChange={onToDateChange}
          placeholder="Select end date"
        />
      </div>

      <div className="flex items-center gap-2">
        <label htmlFor="log-type" className="text-sm font-medium">
          Type
        </label>
        <Select
          value={type || "ALL"}
          onValueChange={(value) => onTypeChange(value as LogType | "ALL")}
        >
          <SelectTrigger className="w-40" id="log-type">
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

      <div className="ml-auto">
        <Button onClick={onDownload} variant="default">
          <DownloadIcon className="h-4 w-4" />
          Download
        </Button>
      </div>
    </div>
  );
};
