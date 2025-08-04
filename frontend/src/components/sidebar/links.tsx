import { paths } from "@/paths";
import {
  FiFileText,
  FiGitMerge,
  FiHelpCircle,
  FiHome,
  FiPieChart,
  FiSettings,
  FiShoppingCart,
  FiTrendingUp,
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
    text: "Trades",
    href: paths.dashboard.TRADES,
    icon: FiPieChart,
    description: "Manage your open trades",
  },
  {
    text: "Orders",
    href: paths.dashboard.ORDERS,
    icon: FiShoppingCart,
    description: "Manage your pending orders",
  },
  {
    text: "Instruments",
    href: paths.dashboard.INSTRUMENTS,
    icon: FiTrendingUp,
    description: "View and manage trading instruments",
  },
  {
    text: "Rules",
    href: paths.dashboard.RULES,
    icon: FiGitMerge,
    description: "Define and manage trading rules",
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
