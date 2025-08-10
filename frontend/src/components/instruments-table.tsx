import { type ColumnDef } from "@tanstack/react-table";
import { VirtualizedTable } from "@/components/ui/virtualized-table";
import { formatDecimal, formatDateOnly, formatNumber } from "@/lib/formatting";

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
      <div className="text-center">{row.getValue("atrStopLossPeriod")}</div>
    ),
  },
  {
    accessorKey: "atrstopLossMultiplePercentage",
    header: "ATR Stop Loss Multiple Percentage",
    size: 180,
    cell: ({ row }) => (
      <div className="text-center">
        {formatDecimal(row.getValue("atrstopLossMultiplePercentage"))}
      </div>
    ),
  },
  {
    accessorKey: "atrProfitTargetPeriod",
    header: "ATR Profit Target Period",
    size: 180,
    cell: ({ row }) => (
      <div className="text-center">{row.getValue("atrProfitTargetPeriod")}</div>
    ),
  },
  {
    accessorKey: "atrProfitMultiplePercentage",
    header: "ATR Profit Multiple Percentage",
    cell: ({ row }) => (
      <div className="text-center">
        {formatDecimal(row.getValue("atrProfitMultiplePercentage"))}
      </div>
    ),
  },
  {
    accessorKey: "positionSize",
    header: "Position Size",
    cell: ({ row }) => (
      <div className="text-center">{row.getValue("positionSize")}</div>
    ),
  },
  {
    accessorKey: "maxPositionSize",
    header: "Max Position Size",
    cell: ({ row }) => (
      <div className="text-center">
        {formatNumber(row.getValue("maxPositionSize"))}
      </div>
    ),
  },
  {
    accessorKey: "openingPriceMultiplePercentage",
    header: "Opening Price Multiple Percentage",
    cell: ({ row }) => (
      <div className="text-center">
        {formatDecimal(row.getValue("openingPriceMultiplePercentage"))}
      </div>
    ),
  },
  {
    accessorKey: "nextDividendDate",
    header: "Next Dividend Date",
    cell: ({ row }) => {
      const dateValue = row.getValue("nextDividendDate") as
        | Date
        | string
        | null;
      const formattedDate = formatDateOnly(dateValue);
      return (
        <div className="text-center">
          {formattedDate === "N/A" ? (
            <span className="text-muted-foreground text-sm">
              {formattedDate}
            </span>
          ) : (
            formattedDate
          )}
        </div>
      );
    },
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
