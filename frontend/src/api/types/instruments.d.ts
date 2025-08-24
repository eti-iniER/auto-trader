interface Instrument {
  marketAndSymbol: string;
  igEpic: string;
  yahooSymbol: string;
  atrStopLossPeriod: number;
  atrStopLossMultiplePercentage: number;
  atrProfitTargetPeriod: number;
  atrProfitMultiplePercentage: number;
  maxPositionSize: number;
  openingPriceMultiplePercentage: number;
  nextDividendDate: Date | null;
}

interface InstrumentUploadResponse {
  message: string;
  instrumentsCreated: number;
}

interface DividendFetchResponse {
  message: string;
}
