import { images } from "@/constants/images";
import React from "react";
import { NavLink, useNavigate } from "react-router";
import { cn } from "../../lib/utils";
import { sidebarLinks } from "./links";
import { useDashboardContext } from "@/hooks/contexts/use-dashboard-context";
import { useLogout } from "@/api/hooks/authentication/use-logout";
import { paths } from "@/paths";
import { FiLogOut } from "react-icons/fi";

interface DesktopSidebarProps {
  className?: string;
}

export const DesktopSidebar: React.FC<DesktopSidebarProps> = ({
  className,
}) => {
  const { user, settings } = useDashboardContext();
  const navigate = useNavigate();
  const logoutMutation = useLogout();
  const userInitial = `${user.firstName[0]}${user.lastName[0]}`.toUpperCase();

  const handleLogout = () => {
    logoutMutation.mutate(undefined, {
      onSuccess: () => {
        navigate(paths.authentication.LOGIN);
      },
    });
  };

  return (
    <div
      className={cn(
        "hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-64 lg:flex-col",
        "border-r border-gray-200 bg-white",
        className,
      )}
    >
      <div className="flex h-16 items-center justify-center gap-2 border-b border-gray-200 px-4">
        <img
          src={images.candlestick}
          alt="AutoTrader Logo"
          className="aspect-square h-8"
        />
        <h1 className="text-lg font-semibold text-neutral-800">AutoTrader</h1>
        <span
          className={cn(
            "rounded-full px-2 py-0.5 text-xs font-medium",
            settings.mode === "DEMO"
              ? "bg-green-100 text-green-800"
              : "bg-red-100 text-red-800",
          )}
        >
          {settings.mode}
        </span>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-2 py-4">
        {sidebarLinks.map((link) => {
          const Icon = link.icon;

          return (
            <NavLink
              key={link.href}
              to={link.href}
              className={({ isActive }) =>
                cn(
                  "group flex items-center rounded-md px-2 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-blue-50 text-blue-700"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900",
                )
              }
            >
              {({ isActive }) => (
                <>
                  <Icon
                    className={cn(
                      "mr-3 h-5 w-5 flex-shrink-0 transition-colors",
                      isActive
                        ? "text-blue-700"
                        : "text-gray-400 group-hover:text-gray-500",
                    )}
                  />
                  {link.text}
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      <div className="flex-shrink-0 border-t border-gray-200 px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-rose-500">
              <span className="text-sm font-medium text-white">
                {userInitial}
              </span>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-700">
                {user.firstName} {user.lastName}
              </p>
              <p className="text-xs text-gray-500">Admin</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            disabled={logoutMutation.isPending}
            className="rounded-md p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-500 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none disabled:opacity-50"
            title="Logout"
          >
            <FiLogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
