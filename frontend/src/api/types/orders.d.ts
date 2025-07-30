type OrderDirection = "BUY" | "SELL";

interface Order {
  dealId: string;
  igEpic: string;
  direction: OrderDirection;
  type: string;
  size: number;
  createdAt: Date;
  stopLevel: number;
  profitLevel: number;
}
