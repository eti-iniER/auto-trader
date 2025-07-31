const DATE_KEYS = new Set(["createdAt", "updatedAt", "timestamp"]);

export function dateReviver(_key: string, value: string) {
  const isDate =
    DATE_KEYS.has(_key) &&
    typeof value === "string" &&
    /^\d{4}-\d{2}-\d{2}T/.test(value);

  if (isDate) {
    const date = new Date(value);
    return isNaN(date.getTime()) ? value : date;
  }

  return value;
}
