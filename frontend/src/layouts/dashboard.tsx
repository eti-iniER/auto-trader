import { useCurrentUser } from "@/api/hooks/authentication/use-current-user";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { DashboardContext } from "@/contexts/dashboard";
import { paths } from "@/paths";
import { AnimatePresence, motion } from "motion/react";
import React from "react";
import { Outlet, useNavigate } from "react-router";
import { toast } from "sonner";
import { DesktopSidebar, MobileSidebar } from "../components/sidebar";

const DashboardLayout: React.FC = () => {
  const { data: user, isPending, isError } = useCurrentUser();
  const navigate = useNavigate();

  if (isError) {
    toast.error("Authentication failed. Please sign in again.");
    navigate(paths.authentication.LOGIN);
    return null;
  }

  return (
    <AnimatePresence mode="wait">
      {isPending ? (
        <motion.div
          key="loading"
          initial={{ opacity: 0, filter: "blur(10px)" }}
          animate={{ opacity: 1, filter: "blur(0)" }}
          exit={{ opacity: 0, filter: "blur(10px)" }}
          transition={{ duration: 0.2 }}
          className="flex h-screen w-full flex-1 bg-gray-50"
        >
          <div className="flex flex-1 flex-col items-center justify-center gap-2">
            <LoadingSpinner />
            <motion.p
              className="text-center text-sm font-medium text-neutral-700"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                duration: 0.3,
                delay: 0.2,
              }}
            >
              Loading
            </motion.p>
          </div>
        </motion.div>
      ) : (
        <DashboardContext.Provider value={{ user }}>
          <motion.div
            key="content"
            initial={{ opacity: 0, filter: "blur(10px)" }}
            animate={{ opacity: 1, filter: "blur(0)" }}
            exit={{ opacity: 0, filter: "blur(10px)" }}
            transition={{ duration: 0.2 }}
            className="flex h-screen w-full bg-gray-50"
          >
            <DesktopSidebar />

            <div className="flex min-w-0 flex-1 flex-col">
              <div className="sticky top-0 z-10 flex h-16 flex-shrink-0 bg-white shadow lg:hidden">
                <MobileSidebar className="flex items-center px-4" />
              </div>

              <main className="relative flex-1 overflow-x-hidden overflow-y-auto focus:outline-none lg:pl-64">
                <Outlet />
              </main>
            </div>
          </motion.div>
        </DashboardContext.Provider>
      )}
    </AnimatePresence>
  );
};

export default DashboardLayout;
