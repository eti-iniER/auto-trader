import { cn } from "@/lib/utils";
import type { IconType } from "react-icons";
import { LuTriangleAlert } from "react-icons/lu";

interface ErrorAlertProps {
  message: string;
  description?: string;
  icon?: IconType;
  className?: string;
}

export const ErrorAlert = ({
  message,
  description,
  icon: Icon = LuTriangleAlert,
  className,
}: ErrorAlertProps) => {
  return (
    <div
      className={cn(
        "flex flex-1 items-center gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-red-800",
        className,
      )}
    >
      <Icon className="h-5 w-5 flex-shrink-0" />
      <div className="flex-1">
        <div className="font-medium">{message}</div>
        {description && (
          <div className="mt-1 text-sm text-red-600">{description}</div>
        )}
      </div>
    </div>
  );
};
