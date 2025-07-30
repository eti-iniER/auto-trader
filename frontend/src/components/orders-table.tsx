import { type ColumnDef } from "@tanstack/react-table";
import { VirtualizedTable } from "@/components/ui/virtualized-table";

interface OrdersTableProps {
  data: Order[];
  loading?: boolean;
  pagination?: {
    page: number;
    pageSize: number;
    totalCount: number;
    onPageChange: (page: number) => void;
    onPageSizeChange: (pageSize: number) => void;
  };
  className?: string;
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat("en-US", {
    style: "decimal",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

const formatDate = (date: Date | string) => {
  const dateObj = typeof date === "string" ? new Date(date) : date;

  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(dateObj);
};

const getDirectionColor = (direction: OrderDirection) => {
  return direction === "BUY"
    ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300"
    : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300";
};

const columns: ColumnDef<Order>[] = [
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
    accessorKey: "direction",
    header: "Direction",
    size: 100,
    cell: ({ row }) => {
      const direction = row.getValue("direction") as OrderDirection;
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
    accessorKey: "type",
    header: "Type",
    size: 120,
    cell: ({ row }) => <div className="text-sm">{row.getValue("type")}</div>,
  },
  {
    accessorKey: "size",
    header: "Size",
    size: 100,
    cell: ({ row }) => (
      <div className="text-right">{formatCurrency(row.getValue("size"))}</div>
    ),
  },
  {
    accessorKey: "stopLevel",
    header: "Stop Level",
    size: 120,
    cell: ({ row }) => {
      const stopLevel = row.getValue("stopLevel") as number;
      return (
        <div className="text-right">
          {stopLevel ? formatCurrency(stopLevel) : "—"}
        </div>
      );
    },
  },
  {
    accessorKey: "profitLevel",
    header: "Profit Level",
    size: 120,
    cell: ({ row }) => {
      const profitLevel = row.getValue("profitLevel") as number;
      return (
        <div className="text-right">
          {profitLevel ? formatCurrency(profitLevel) : "—"}
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

function OrdersTable({
  data,
  loading = false,
  pagination,
  className,
}: OrdersTableProps) {
  return (
    <VirtualizedTable
      columns={columns}
      data={data}
      loading={loading}
      searchPlaceholder="Search orders by deal ID, IG Epic..."
      pagination={pagination}
      className={className}
      rowHeight={50}
      maxHeight={600}
    />
  );
}

export { OrdersTable };
