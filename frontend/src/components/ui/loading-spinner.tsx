import { motion } from "motion/react";

export const LoadingSpinner = () => (
  <motion.div
    className="relative size-8"
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    transition={{ duration: 0.3 }}
  >
    <div className="absolute inset-0 rounded-full border-2 border-white/10" />

    <motion.div
      className="absolute inset-0 rounded-full border-2 border-transparent border-t-neutral-300 border-r-emerald-700"
      animate={{ rotate: 360 }}
      transition={{
        duration: 1,
        repeat: Infinity,
        ease: "linear",
      }}
    />

    <motion.div
      className="absolute top-1/2 left-1/2 size-2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-rose-700"
      animate={{
        scale: [1, 1.2, 1],
        opacity: [0.8, 1, 0.8],
      }}
      transition={{
        duration: 1.5,
        repeat: Infinity,
        ease: "easeInOut",
      }}
    />
  </motion.div>
);
