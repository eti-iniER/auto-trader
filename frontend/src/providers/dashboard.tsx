import { useAppSettings } from "@/api/hooks/app-settings.ts/use-app-settings";
import { useCurrentUser } from "@/api/hooks/authentication/use-current-user";
import { useUserSettings } from "@/api/hooks/user-settings/use-user-settings";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { DashboardContext } from "@/contexts/dashboard";
import { paths } from "@/paths";
import { AnimatePresence, motion } from "motion/react";
import { type PropsWithChildren } from "react";
import { Navigate } from "react-router";
import { toast } from "sonner";

export const DashboardProvider = ({ children }: PropsWithChildren) => {
  const {
    data: user,
    isPending: isUserPending,
    isError: isUserError,
  } = useCurrentUser();
  const {
    data: settings,
    isPending: isSettingsPending,
    isError: isSettingsError,
  } = useUserSettings();
  const {
    data: appSettings,
    isPending: isAppSettingsPending,
    isError: isAppSettingsError,
  } = useAppSettings();

  const isError = isUserError || isSettingsError || isAppSettingsError;
  const isPending = isUserPending || isSettingsPending || isAppSettingsPending;

  if (isError) {
    toast.error("Authentication failed. Please sign in again.");
    return <Navigate to={paths.authentication.LOGIN} replace />;
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
        <DashboardContext.Provider value={{ user, settings, appSettings }}>
          <motion.div
            key="content"
            initial={{ opacity: 0, filter: "blur(10px)" }}
            animate={{ opacity: 1, filter: "blur(0)" }}
            exit={{ opacity: 0, filter: "blur(10px)" }}
            transition={{ duration: 0.2 }}
            className="flex h-screen w-full bg-gray-50"
          >
            {children}
          </motion.div>
        </DashboardContext.Provider>
      )}
    </AnimatePresence>
  );
};
