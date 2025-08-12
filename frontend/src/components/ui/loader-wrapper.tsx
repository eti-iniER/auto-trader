import type { ReactNode } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Loader } from "./loader";

interface LoaderWrapperProps {
  isLoading: boolean;
  children: ReactNode;
  loadingText?: string;
  className?: string;
}

export const LoaderWrapper = ({
  isLoading,
  children,
  loadingText,
  className = "",
}: LoaderWrapperProps) => {
  return (
    <div
      className={`relative flex min-h-[1.5rem] items-center justify-center ${className}`}
    >
      <AnimatePresence mode="wait">
        {isLoading ? (
          <motion.div
            key="loader"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
            className="absolute inset-0 flex items-center justify-center gap-2"
          >
            <Loader />
            {loadingText && <span>{loadingText}</span>}
          </motion.div>
        ) : (
          <motion.div
            key="content"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
            className="flex items-center justify-center"
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
