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
  searchValue?: string;
  onSearchChange?: (value: string) => void;
}

const columns: ColumnDef<Instrument>[] = [
  {
    accessorKey: "marketAndSymbol",
    header: () => (
      <div className="text-center leading-tight">
        Market &<br />
        Symbol
      </div>
    ),
    size: 120,
    cell: ({ row }) => (
      <div className="font-medium">{row.getValue("marketAndSymbol")}</div>
    ),
  },
  {
    accessorKey: "igEpic",
    header: () => <div className="text-center leading-tight">IG Epic</div>,
    size: 120,
    cell: ({ row }) => (
      <div className="font-mono text-sm">{row.getValue("igEpic")}</div>
    ),
  },
  {
    accessorKey: "yahooSymbol",
    header: () => (
      <div className="text-center leading-tight">
        Yahoo
        <br />
        Symbol
      </div>
    ),
    size: 100,
    cell: ({ row }) => (
      <div className="text-center font-mono text-sm">
        {row.getValue("yahooSymbol")}
      </div>
    ),
  },
  {
    accessorKey: "atrStopLossPeriod",
    header: () => (
      <div className="text-center leading-tight">
        ATR Stop Loss
        <br />
        Period
      </div>
    ),
    size: 120,
    cell: ({ row }) => (
      <div className="text-center">{row.getValue("atrStopLossPeriod")}</div>
    ),
  },
  {
    accessorKey: "atrStopLossMultiplePercentage",
    header: () => (
      <div className="text-center leading-tight">
        ATR Stop
        <br />
        Loss Multiple %
      </div>
    ),
    size: 120,
    cell: ({ row }) => (
      <div className="text-center">
        {formatDecimal(row.getValue("atrStopLossMultiplePercentage"))}
      </div>
    ),
  },
  {
    accessorKey: "atrProfitTargetPeriod",
    header: () => (
      <div className="text-center leading-tight">
        ATR Profit
        <br />
        Target Period
      </div>
    ),
    size: 120,
    cell: ({ row }) => (
      <div className="text-center">{row.getValue("atrProfitTargetPeriod")}</div>
    ),
  },
  {
    accessorKey: "atrProfitMultiplePercentage",
    header: () => (
      <div className="text-center leading-tight">
        ATR Profit
        <br />
        Multiple %
      </div>
    ),
    size: 120,
    cell: ({ row }) => (
      <div className="text-center">
        {formatDecimal(row.getValue("atrProfitMultiplePercentage"))}
      </div>
    ),
  },
  {
    accessorKey: "maxPositionSize",
    header: () => (
      <div className="py-2 text-center leading-tight">
        Max Position
        <br />
        Size
      </div>
    ),
    size: 110,
    cell: ({ row }) => (
      <div className="text-center">
        {formatNumber(row.getValue("maxPositionSize"))}
      </div>
    ),
  },
  {
    accessorKey: "openingPriceMultiplePercentage",
    header: () => (
      <div className="text-center leading-tight">
        Opening Price
        <br />
        Multiple %
      </div>
    ),
    size: 120,
    cell: ({ row }) => (
      <div className="text-center">
        {formatDecimal(row.getValue("openingPriceMultiplePercentage"))}
      </div>
    ),
  },
  {
    accessorKey: "nextDividendDate",
    header: () => (
      <div className="text-center leading-tight">
        Next Dividend
        <br />
        Date
      </div>
    ),
    size: 110,
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
  searchValue,
  onSearchChange,
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
      externalSearch={
        searchValue !== undefined && onSearchChange
          ? {
              value: searchValue,
              onChange: onSearchChange,
            }
          : undefined
      }
    />
  );
}

export { InstrumentsTable };
