import { VirtualizedTable } from "@/components/ui/virtualized-table";
import { formatDate, formatDecimal } from "@/lib/formatting";
import { type ColumnDef } from "@tanstack/react-table";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";

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
  additionalInputs?: React.ReactNode; // For any additional inputs like search
  onDeleteOrder?: (order: Order) => void;
}

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
      <div className="text-center">{formatDecimal(row.getValue("size"))}</div>
    ),
  },
  {
    accessorKey: "entryLevel",
    header: "Entry Level",
    size: 120,
    cell: ({ row }) => {
      const entryLevel = row.getValue("entryLevel") as number;
      return <div className="text-center">{formatDecimal(entryLevel)}</div>;
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
    accessorKey: "profitLevel",
    header: "Profit Level",
    size: 120,
    cell: ({ row }) => {
      const profitLevel = row.getValue("profitLevel") as number;
      return (
        <div className="text-center">
          {profitLevel ? formatDecimal(profitLevel) : "—"}
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
  additionalInputs,
  onDeleteOrder,
}: OrdersTableProps) {
  // Create ActionsCell component
  const ActionsCell = ({ order }: { order: Order }) => (
    <Button
      variant="outline"
      size="sm"
      className="h-8 w-8 p-0 text-red-600 hover:bg-red-50 hover:text-red-700"
      onClick={() => onDeleteOrder?.(order)}
    >
      <Trash2 className="h-4 w-4" />
    </Button>
  );

  // Add actions column to the existing columns
  const columnsWithActions: ColumnDef<Order>[] = [
    ...columns,
    {
      id: "actions",
      header: "",
      size: 80,
      cell: ({ row }) => <ActionsCell order={row.original} />,
    },
  ];

  return (
    <VirtualizedTable
      columns={columnsWithActions}
      data={data}
      loading={loading}
      searchPlaceholder="Search orders by IG Epic, Deal ID..."
      pagination={pagination}
      className={className}
      rowHeight={50}
      fillAvailableHeight={true}
      additionalInputs={additionalInputs}
    />
  );
}

export { OrdersTable };
