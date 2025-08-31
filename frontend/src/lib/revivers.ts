const DATE_KEYS = new Set([
  "createdAt",
  "lastLogin",
  "updatedAt",
  "timestamp",
  "nextDividendDate",
]);

const DECIMAL_KEYS = new Set([
  "price",
  "dividendYield",
  "marketCap",
  "peRatio",
  "eps",
  "atrStopLossMultiplePercentage",
  "atrProfitMultiplePercentage",
  "openingPriceMultiplePercentage",
  "size",
  "openLevel",
  "currentLevel",
  "profitLoss",
  "profitLossPercentage",
  "maxPositionSize",
  "entryLevel",
  "stopLevel",
  "profitLevel",
]);

export function revivers(_key: string, value: string) {
  const isDate =
    DATE_KEYS.has(_key) &&
    typeof value === "string" &&
    /^\d{4}-\d{2}-\d{2}T/.test(value);
  const isDecimal =
    DECIMAL_KEYS.has(_key) &&
    typeof value === "string" &&
    /^-?\d+(\.\d+)?$/.test(value);

  if (isDate) {
    const date = new Date(value);
    return isNaN(date.getTime()) ? value : date;
  } else if (isDecimal) {
    const decimal = parseFloat(value);
    return isNaN(decimal) ? value : decimal;
  }

  return value;
}
