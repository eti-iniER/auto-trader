import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/formatting";

interface LogItemCardProps {
  log: Log;
}

export const LogItemCard: React.FC<LogItemCardProps> = ({ log }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const hasExtraData = log.extra && Object.keys(log.extra).length > 0;

  const toggleExpanded = () => {
    if (hasExtraData) {
      setIsExpanded(!isExpanded);
    }
  };

  return (
    <div className="border-border w-full rounded-lg border bg-white p-4">
      {/* Date at the top */}
      <div className="text-muted-foreground mb-3 text-xs">
        {formatDate(log.createdAt)}
      </div>

      {/* Main content */}
      <div className="space-y-2">
        <h3 className="text-foreground text-base leading-tight font-medium">
          {log.message}
        </h3>
        {log.description && (
          <p className="text-muted-foreground text-sm leading-relaxed">
            {log.description}
          </p>
        )}
      </div>

      {/* Extra data section */}
      {hasExtraData && isExpanded && (
        <div className="mt-4">
          <div className="bg-muted rounded-md p-3">
            <h4 className="text-muted-foreground mb-2 text-xs font-medium tracking-wide uppercase">
              Additional Data
            </h4>
            <pre className="text-foreground overflow-x-auto font-mono text-xs break-words whitespace-pre-wrap">
              {JSON.stringify(log.extra, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {/* Bottom button for extra data */}
      {hasExtraData && (
        <div className="mt-3 flex justify-start">
          <Button
            variant="outline"
            size="sm"
            onClick={toggleExpanded}
            className="h-8 px-3 text-xs"
          >
            {isExpanded ? "Hide extra data" : "View extra data"}
          </Button>
        </div>
      )}
    </div>
  );
};
