import { images } from "@/constants/images";
import React, { useState } from "react";
import { FiMenu, FiX, FiLogOut } from "react-icons/fi";
import { NavLink, useNavigate } from "react-router";
import { cn } from "../../lib/utils";
import { sidebarLinks, adminSidebarLinks } from "./links";
import { useDashboardContext } from "@/hooks/contexts/use-dashboard-context";
import { useLogout } from "@/api/hooks/authentication/use-logout";
import { paths } from "@/paths";

interface MobileSidebarProps {
  className?: string;
}

export const MobileSidebar: React.FC<MobileSidebarProps> = ({ className }) => {
  const [isOpen, setIsOpen] = useState(false);
  const { user, settings } = useDashboardContext();
  const navigate = useNavigate();
  const logoutMutation = useLogout();
  const userInitial = `${user.firstName[0]}${user.lastName[0]}`.toUpperCase();

  const toggleSidebar = () => setIsOpen(!isOpen);
  const closeSidebar = () => setIsOpen(false);

  const handleLogout = () => {
    logoutMutation.mutate(undefined, {
      onSuccess: () => {
        navigate(paths.authentication.LOGIN);
      },
    });
  };

  return (
    <>
      <div className={cn("lg:hidden", className)}>
        <button
          onClick={toggleSidebar}
          className="inline-flex items-center justify-center rounded-md p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-500 focus:ring-2 focus:ring-blue-500 focus:outline-none focus:ring-inset"
          aria-controls="mobile-menu"
          aria-expanded="false"
        >
          <span className="sr-only">Open main menu</span>
          {isOpen ? (
            <FiX className="block h-6 w-6" aria-hidden="true" />
          ) : (
            <FiMenu className="block h-6 w-6" aria-hidden="true" />
          )}
        </button>
      </div>

      {isOpen && (
        <div className="fixed inset-0 z-40 lg:hidden" onClick={closeSidebar}>
          <div className="bg-opacity-75 fixed inset-0 bg-gray-600" />
        </div>
      )}

      <div
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 transform bg-white transition-transform duration-300 ease-in-out lg:hidden",
          isOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-full flex-col">
          <div className="flex h-16 items-center justify-between border-b border-gray-200 px-4">
            <div className="flex items-center gap-2">
              <img
                src={images.candlestick}
                alt="AutoTrader Logo"
                className="aspect-square h-8"
              />
              <h1 className="text-lg font-semibold text-neutral-800">
                AutoTrader
              </h1>
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
            <button
              onClick={closeSidebar}
              className="rounded-md p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-500"
            >
              <FiX className="h-6 w-6" />
            </button>
          </div>

          <nav className="flex-1 space-y-1 overflow-y-auto px-2 py-4">
            {sidebarLinks.map((link) => {
              const Icon = link.icon;

              return (
                <NavLink
                  key={link.href}
                  to={link.href}
                  onClick={closeSidebar}
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

            {user.role === "ADMIN" && (
              <>
                <div className="px-5 py-2">
                  <div className="relative">
                    <div
                      className="absolute inset-0 flex items-center"
                      aria-hidden="true"
                    >
                      <div className="w-full border-t border-gray-200" />
                    </div>
                    <div className="relative flex justify-center">
                      <span className="bg-white px-2 text-xs font-semibold text-gray-400 uppercase">
                        Admin
                      </span>
                    </div>
                  </div>
                </div>

                {adminSidebarLinks.map((link) => {
                  const Icon = link.icon;

                  return (
                    <NavLink
                      key={link.href}
                      to={link.href}
                      onClick={closeSidebar}
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
              </>
            )}
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
      </div>
    </>
  );
};
