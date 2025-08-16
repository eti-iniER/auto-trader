import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { toast } from "sonner";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export async function copyToClipboard(text: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard!");
  } catch {
    toast.error("Failed to copy to clipboard");
  }
}

export const pluralize = (
  count: number,
  singular: string,
  plural?: string,
): string => {
  if (count === 1) {
    return `${singular}`;
  }
  return `${plural || singular + "s"}`;
};
