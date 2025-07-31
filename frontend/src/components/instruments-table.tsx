import { type ColumnDef } from "@tanstack/react-table";
import { VirtualizedTable } from "@/components/ui/virtualized-table";

// The Instrument type is available globally from api/types/global.d.ts

interface InstrumentsTableProps {
  data: Instrument[];
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
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat("en-US", {
    style: "decimal",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

const formatDate = (date: Date | null) => {
  if (!date) {
    return <span className="text-muted-foreground text-sm">N/A</span>;
  }

  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(date);
};

const columns: ColumnDef<Instrument>[] = [
  {
    accessorKey: "marketAndSymbol",
    header: "Market & Symbol",
    size: 150,
    cell: ({ row }) => (
      <div className="font-medium">{row.getValue("marketAndSymbol")}</div>
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
    accessorKey: "yahooSymbol",
    header: "Yahoo Symbol",
    size: 130,
    cell: ({ row }) => (
      <div className="font-mono text-sm">{row.getValue("yahooSymbol")}</div>
    ),
  },
  {
    accessorKey: "atrStopLossPeriod",
    header: "ATR Stop Loss Period",
    size: 160,
    cell: ({ row }) => (
      <div className="text-right">{row.getValue("atrStopLossPeriod")}</div>
    ),
  },
  {
    accessorKey: "atrStopLossMultiple",
    header: "ATR Stop Loss Multiple",
    size: 180,
    cell: ({ row }) => (
      <div className="text-right">
        {formatCurrency(row.getValue("atrStopLossMultiple"))}
      </div>
    ),
  },
  {
    accessorKey: "atrProfitTargetPeriod",
    header: "ATR Profit Target Period",
    size: 180,
    cell: ({ row }) => (
      <div className="text-right">{row.getValue("atrProfitTargetPeriod")}</div>
    ),
  },
  {
    accessorKey: "atrProfitMultiple",
    header: "ATR Profit Multiple",
    cell: ({ row }) => (
      <div className="text-right">
        {formatCurrency(row.getValue("atrProfitMultiple"))}
      </div>
    ),
  },
  {
    accessorKey: "positionSize",
    header: "Position Size",
    cell: ({ row }) => (
      <div className="text-right">
        {formatCurrency(row.getValue("positionSize"))}
      </div>
    ),
  },
  {
    accessorKey: "maxPositionSize",
    header: "Max Position Size",
    cell: ({ row }) => (
      <div className="text-right">
        {formatCurrency(row.getValue("maxPositionSize"))}
      </div>
    ),
  },
  {
    accessorKey: "openingPriceMultiple",
    header: "Opening Price Multiple",
    cell: ({ row }) => (
      <div className="text-right">
        {formatCurrency(row.getValue("openingPriceMultiple"))}
      </div>
    ),
  },
  {
    accessorKey: "nextDividendDate",
    header: "Next Dividend Date",
    cell: ({ row }) => (
      <div className="text-center">
        {formatDate(row.getValue("nextDividendDate"))}
      </div>
    ),
  },
];

function InstrumentsTable({
  data,
  loading = false,
  pagination,
  className,
  additionalInputs,
}: InstrumentsTableProps) {
  return (
    <VirtualizedTable
      columns={columns}
      data={data}
      loading={loading}
      searchPlaceholder="Search instruments by symbol, IG Epic, or Yahoo symbol..."
      pagination={pagination}
      className={className}
      rowHeight={50}
      fillAvailableHeight={true}
      additionalInputs={additionalInputs}
    />
  );
}

export { InstrumentsTable };
