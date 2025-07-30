interface Instrument {
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
}
