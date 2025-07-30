export const paths = {
  authentication: {
    LOGIN: "/auth/login",
    RESET_PASSWORD: "/auth/reset-password",
  },
  dashboard: {
    OVERVIEW: "/dashboard/overview",
    TRADES: "/dashboard/trades",
    ORDERS: "/dashboard/orders",
    INSTRUMENTS: "/dashboard/instruments",
    RULES: "/dashboard/rules",
    LOGS: "/dashboard/logs",
    PROFILE: "/dashboard/profile",
    SETTINGS: "/dashboard/settings",
    HELP: "/dashboard/help",
  },
} as const;
