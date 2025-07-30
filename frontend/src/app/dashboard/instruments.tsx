import { useState, useEffect } from "react";
import { PageHeader } from "@/components/page-header";
import { InstrumentsTable } from "@/components/instruments-table";

// Define the Instrument type to match the API
type Instrument = {
  marketAndSymbol: string;
  igEpic: string;
  yahooSymbol: string;
  atrStopLossPeriod: number;
  atrStopLossMultiple: number;
  atrProfitTargetPeriod: number;
  atrProfitMultiple: number;
  positionSize: number;
  maxPositionSize: number;
  openingPriceMultiple: number;
  nextDividendDate: Date | null;
};

// Mock data for demonstration - replace with real API call
const mockInstruments: Instrument[] = [
  {
    marketAndSymbol: "AAPL",
    igEpic: "UA.D.AAPL.CASH.IP",
    yahooSymbol: "AAPL",
    atrStopLossPeriod: 14,
    atrStopLossMultiple: 2.0,
    atrProfitTargetPeriod: 14,
    atrProfitMultiple: 3.0,
    positionSize: 100,
    maxPositionSize: 500,
    openingPriceMultiple: 1.02,
    nextDividendDate: new Date("2025-02-15"),
  },
  {
    marketAndSymbol: "GOOGL",
    igEpic: "UA.D.GOOGL.CASH.IP",
    yahooSymbol: "GOOGL",
    atrStopLossPeriod: 14,
    atrStopLossMultiple: 2.5,
    atrProfitTargetPeriod: 14,
    atrProfitMultiple: 3.5,
    positionSize: 50,
    maxPositionSize: 200,
    openingPriceMultiple: 1.015,
    nextDividendDate: null,
  },
  {
    marketAndSymbol: "MSFT",
    igEpic: "UA.D.MSFT.CASH.IP",
    yahooSymbol: "MSFT",
    atrStopLossPeriod: 20,
    atrStopLossMultiple: 1.8,
    atrProfitTargetPeriod: 20,
    atrProfitMultiple: 2.8,
    positionSize: 75,
    maxPositionSize: 300,
    openingPriceMultiple: 1.025,
    nextDividendDate: new Date("2025-03-10"),
  },
  {
    marketAndSymbol: "TSLA",
    igEpic: "UA.D.TSLA.CASH.IP",
    yahooSymbol: "TSLA",
    atrStopLossPeriod: 10,
    atrStopLossMultiple: 3.0,
    atrProfitTargetPeriod: 10,
    atrProfitMultiple: 4.0,
    positionSize: 25,
    maxPositionSize: 100,
    openingPriceMultiple: 1.03,
    nextDividendDate: null,
  },
  {
    marketAndSymbol: "AMZN",
    igEpic: "UA.D.AMZN.CASH.IP",
    yahooSymbol: "AMZN",
    atrStopLossPeriod: 14,
    atrStopLossMultiple: 2.2,
    atrProfitTargetPeriod: 14,
    atrProfitMultiple: 3.2,
    positionSize: 30,
    maxPositionSize: 150,
    openingPriceMultiple: 1.018,
    nextDividendDate: new Date("2025-04-20"),
  },
];

export const Instruments = () => {
  const [loading, setLoading] = useState(true);
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  // Simulate API call
  useEffect(() => {
    const loadInstruments = async () => {
      setLoading(true);
      // Simulate API delay
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setInstruments(mockInstruments);
      setLoading(false);
    };

    loadInstruments();
  }, []);

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    // In a real app, you might trigger an API call here
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setPage(1); // Reset to first page
    // In a real app, you might trigger an API call here
  };

  return (
    <div className="min-w-0 flex-1 space-y-8 p-8">
      <PageHeader
        title="Instruments"
        description="View and edit your trading instruments and ticker data"
      />

      <div className="h-full w-full overflow-hidden">
        <InstrumentsTable
          data={instruments}
          loading={loading}
          pagination={{
            page,
            pageSize,
            totalCount: instruments.length,
            onPageChange: handlePageChange,
            onPageSizeChange: handlePageSizeChange,
          }}
        />
      </div>
    </div>
  );
};
