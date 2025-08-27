import { createContext } from "react";

interface DashboardContextValue {
  user: User;
  settings: UserSettings;
  appSettings: AppSettings;
}

export const DashboardContext = createContext<DashboardContextValue | null>(
  null,
);
