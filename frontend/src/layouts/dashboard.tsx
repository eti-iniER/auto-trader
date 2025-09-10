import { DashboardProvider } from "@/providers/dashboard";
import { Outlet } from "react-router";
import { DesktopSidebar, MobileSidebar } from "../components/sidebar";

export const DashboardLayout = () => {
  return (
    <DashboardProvider>
      <DesktopSidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="sticky top-0 z-10 flex h-16 flex-shrink-0 bg-white shadow lg:hidden">
          <MobileSidebar className="flex items-center px-4" />
        </div>

        <main className="relative flex-1 overflow-x-hidden overflow-y-auto focus:outline-none lg:pl-64">
          <Outlet />
        </main>
      </div>
    </DashboardProvider>
  );
};
