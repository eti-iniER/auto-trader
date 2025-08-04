import { createContext } from "react";

interface DashboardContextValue {
  user: User;
  settings: UserSettings;
}

export const DashboardContext = createContext<DashboardContextValue | null>(
  null,
);
