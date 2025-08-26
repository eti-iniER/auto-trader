import { paths } from "@/paths";
import {
  FiFileText,
  FiHelpCircle,
  FiHome,
  FiPieChart,
  FiSettings,
  FiShoppingCart,
  FiTrendingUp,
  FiUsers,
} from "react-icons/fi";

export interface SidebarLink {
  text: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

export const sidebarLinks: SidebarLink[] = [
  {
    text: "Overview",
    href: paths.dashboard.OVERVIEW,
    icon: FiHome,
    description: "View app statistics and general info",
  },
  {
    text: "Positions",
    href: paths.dashboard.POSITIONS,
    icon: FiPieChart,
    description: "Manage your open positions",
  },
  {
    text: "Orders",
    href: paths.dashboard.ORDERS,
    icon: FiShoppingCart,
    description: "Manage your pending/working orders",
  },
  {
    text: "Instruments",
    href: paths.dashboard.INSTRUMENTS,
    icon: FiTrendingUp,
    description: "View and manage trading instruments",
  },
  {
    text: "Logs",
    href: paths.dashboard.LOGS,
    icon: FiFileText,
    description: "View trading logs and history",
  },

  {
    text: "Settings",
    href: paths.dashboard.SETTINGS,
    icon: FiSettings,
    description: "Configure application settings and preferences",
  },
  {
    text: "Help",
    href: paths.dashboard.HELP,
    icon: FiHelpCircle,
    description: "Info and how-tos for the app",
  },
];

export const adminSidebarLinks: SidebarLink[] = [
  {
    text: "Users",
    href: paths.dashboard.admin.USERS,
    icon: FiUsers,
    description: "Manage application users",
  },
];
