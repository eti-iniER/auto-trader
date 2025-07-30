import React from "react";
import { Outlet } from "react-router";
import { DesktopSidebar, MobileSidebar } from "../components/sidebar";

const DashboardLayout: React.FC = () => {
  return (
    <div className="flex h-screen w-full bg-gray-50">
      <DesktopSidebar />

      <div className="flex min-w-0 flex-1 flex-col lg:pl-64">
        <div className="sticky top-0 z-10 flex h-16 flex-shrink-0 bg-white shadow lg:hidden">
          <MobileSidebar className="flex items-center px-4" />
        </div>

        <main className="relative flex-1 overflow-x-hidden overflow-y-auto focus:outline-none">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
