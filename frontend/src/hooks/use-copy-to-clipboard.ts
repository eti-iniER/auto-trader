import { useState } from "react";
import { copyToClipboard } from "@/lib/utils";

export const useCopyToClipboard = () => {
  const [copied, setCopied] = useState(false);

  const copy = async (text: string) => {
    try {
      await copyToClipboard(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error("Failed to copy to clipboard:", error);
      setCopied(false);
    }
  };

  return { copied, copy };
};
