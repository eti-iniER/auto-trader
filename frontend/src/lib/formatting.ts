import { defaultCurrency } from "@/constants/defaults";

/**
 * Format a number as currency using en-GB locale
 */
export const formatCurrency = (value: number) => {
  return new Intl.NumberFormat("en-GB", {
    localeMatcher: "best fit",
    style: "currency",
    currency: defaultCurrency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

/**
 * Format a number as decimal using en-GB locale (no currency symbol)
 */
export const formatDecimal = (value: number) => {
  return new Intl.NumberFormat("en-GB", {
    style: "decimal",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

/**
 * Format a date using en-GB locale
 */
export const formatDate = (date: Date | string) => {
  const dateObj = typeof date === "string" ? new Date(date) : date;

  return new Intl.DateTimeFormat("en-GB", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
  })
    .format(dateObj)
    .replace(/am|pm/g, (match) => match.toUpperCase());
};

/**
 * Format a date (date only, no time) using en-GB locale
 */
export const formatDateOnly = (date: Date | string | null) => {
  if (!date) {
    return "N/A";
  }

  const dateObj = typeof date === "string" ? new Date(date) : date;

  return new Intl.DateTimeFormat("en-GB", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(dateObj);
};

/**
 * Format a number using en-GB locale with thousand separators
 */
export const formatNumber = (value: number) => {
  return Number(value).toLocaleString("en-GB");
};
