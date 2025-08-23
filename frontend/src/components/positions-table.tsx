import { VirtualizedTable } from "@/components/ui/virtualized-table";
import { formatCurrency, formatDate, formatDecimal } from "@/lib/formatting";
import { type ColumnDef } from "@tanstack/react-table";

interface PositionsTableProps {
  data: Position[];
  loading?: boolean;
  pagination?: {
    page: number;
    pageSize: number;
    totalCount: number;
    onPageChange: (page: number) => void;
    onPageSizeChange: (pageSize: number) => void;
  };
  className?: string;
  additionalInputs?: React.ReactNode;
}

const getDirectionColor = (direction: PositionDirection) => {
  return direction === "BUY"
    ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300"
    : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300";
};

const getProfitLossColor = (profitLoss: number | null) => {
  if (profitLoss === null) return "text-gray-500";
  return profitLoss >= 0
    ? "text-green-600 dark:text-green-400"
    : "text-red-600 dark:text-red-400";
};

const columns: ColumnDef<Position>[] = [
  {
    accessorKey: "dealId",
    header: "Deal ID",
    size: 150,
    cell: ({ row }) => (
      <div className="font-mono text-sm">{row.getValue("dealId")}</div>
    ),
  },
  {
    accessorKey: "igEpic",
    header: "IG Epic",
    size: 180,
    cell: ({ row }) => (
      <div className="font-mono text-sm">{row.getValue("igEpic")}</div>
    ),
  },
  {
    accessorKey: "marketAndSymbol",
    header: "Market & Symbol",
    size: 200,
    cell: ({ row }) => {
      const marketAndSymbol = row.getValue("marketAndSymbol") as string;
      return <div className="text-sm">{marketAndSymbol || "—"}</div>;
    },
  },
  {
    accessorKey: "direction",
    header: "Direction",
    size: 100,
    cell: ({ row }) => {
      const direction = row.getValue("direction") as PositionDirection;
      return (
        <span
          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getDirectionColor(direction)}`}
        >
          {direction}
        </span>
      );
    },
  },
  {
    accessorKey: "size",
    header: "Size",
    size: 100,
    cell: ({ row }) => (
      <div className="text-center">{formatDecimal(row.getValue("size"))}</div>
    ),
  },
  {
    accessorKey: "openLevel",
    header: "Open Level",
    size: 120,
    cell: ({ row }) => {
      const openLevel = row.getValue("openLevel") as number;
      return <div className="text-center">{formatDecimal(openLevel)}</div>;
    },
  },
  {
    accessorKey: "currentLevel",
    header: "Current Level",
    size: 120,
    cell: ({ row }) => {
      const currentLevel = row.getValue("currentLevel") as number;
      return (
        <div className="text-center">
          {currentLevel ? formatDecimal(currentLevel) : "—"}
        </div>
      );
    },
  },
  {
    accessorKey: "profitLoss",
    header: "P&L",
    size: 120,
    cell: ({ row }) => {
      const profitLoss = row.getValue("profitLoss") as number;
      return (
        <div
          className={`text-center font-medium ${getProfitLossColor(profitLoss)}`}
        >
          {profitLoss !== null ? formatCurrency(profitLoss) : "—"}
        </div>
      );
    },
  },
  {
    accessorKey: "profitLossPercentage",
    header: "P&L %",
    size: 100,
    cell: ({ row }) => {
      const profitLossPercentage = row.getValue(
        "profitLossPercentage",
      ) as number;
      return (
        <div
          className={`text-center font-medium ${getProfitLossColor(profitLossPercentage)}`}
        >
          {profitLossPercentage !== null
            ? `${profitLossPercentage.toFixed(2)}%`
            : "—"}
        </div>
      );
    },
  },
  {
    accessorKey: "stopLevel",
    header: "Stop Level",
    size: 120,
    cell: ({ row }) => {
      const stopLevel = row.getValue("stopLevel") as number;
      return (
        <div className="text-center">
          {stopLevel ? formatDecimal(stopLevel) : "—"}
        </div>
      );
    },
  },
  {
    accessorKey: "limitLevel",
    header: "Limit Level",
    size: 120,
    cell: ({ row }) => {
      const limitLevel = row.getValue("limitLevel") as number;
      return (
        <div className="text-center">
          {limitLevel ? formatDecimal(limitLevel) : "—"}
        </div>
      );
    },
  },
  {
    accessorKey: "controlledRisk",
    header: "Controlled Risk",
    size: 130,
    cell: ({ row }) => {
      const controlledRisk = row.getValue("controlledRisk") as boolean;
      return (
        <div className="text-center">
          <span
            className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
              controlledRisk
                ? "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300"
                : "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300"
            }`}
          >
            {controlledRisk ? "Yes" : "No"}
          </span>
        </div>
      );
    },
  },
  {
    accessorKey: "createdAt",
    header: "Created At",
    size: 160,
    cell: ({ row }) => (
      <div className="text-sm">{formatDate(row.getValue("createdAt"))}</div>
    ),
  },
];

function PositionsTable({
  data,
  loading = false,
  pagination,
  className,
  additionalInputs,
}: PositionsTableProps) {
  return (
    <VirtualizedTable
      columns={columns}
      data={data}
      loading={loading}
      searchPlaceholder="Search positions by IG Epic, Deal ID..."
      pagination={pagination}
      className={className}
      rowHeight={50}
      fillAvailableHeight={true}
      additionalInputs={additionalInputs}
    />
  );
}

export { PositionsTable };
