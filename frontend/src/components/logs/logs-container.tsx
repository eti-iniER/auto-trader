import type { ReactNode } from "react";

interface LogsContainerProps {
  children: ReactNode;
}

export const LogsContainer = ({ children }: LogsContainerProps) => (
  <div className="flex h-full flex-col">
    <div className="min-h-0 flex-1">{children}</div>
  </div>
);
