/* eslint-disable @typescript-eslint/no-explicit-any */
type ActivityChannel = string;
type ActivityType = string;
type DealStatus = string;

interface Activity {
  date: Date;
  epic: string;
  period: string;
  dealId: string;
  channel: ActivityChannel;
  type: ActivityType;
  status: DealStatus;
  description: string;
  details: Record<string, any> | null;
}

interface UserQuickStatsResponse {
  openPositionsCount: number;
  openOrdersCount: number;
  recentActivities: Activity[];
  statsTimestamp: Date;
}
