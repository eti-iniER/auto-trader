type PositionDirection = "BUY" | "SELL";

interface Position {
  dealId: string;
  igEpic: string;
  marketAndSymbol: string | null;
  direction: PositionDirection;
  size: number;
  openLevel: number;
  currentLevel: number | null;
  profitLoss: number | null;
  profitLossPercentage: number | null;
  createdAt: Date;
  stopLevel: number | null;
  limitLevel: number | null;
  controlledRisk: boolean;
}
