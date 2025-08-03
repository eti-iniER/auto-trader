import { createContext } from "react";

interface DashboardContextValue {
  user: User;
}

export const DashboardContext = createContext<DashboardContextValue | null>(
  null,
);
