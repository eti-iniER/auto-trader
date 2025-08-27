export const paths = {
  authentication: {
    LOGIN: "/auth/login",
    REGISTER: "/auth/register",
    RESET_PASSWORD: "/auth/reset-password",
    CHANGE_PASSWORD: "/auth/change-password",
  },
  dashboard: {
    OVERVIEW: "/dashboard/overview",
    POSITIONS: "/dashboard/positions",
    ORDERS: "/dashboard/orders",
    INSTRUMENTS: "/dashboard/instruments",
    LOGS: "/dashboard/logs",
    PROFILE: "/dashboard/profile",
    SETTINGS: "/dashboard/settings",
    HELP: "/dashboard/help",
    admin: {
      USERS: "/dashboard/admin/users",
      APP_SETTINGS: "/dashboard/admin/app-settings",
    },
  },
  errors: {
    NOT_FOUND: "/404",
  },
} as const;
