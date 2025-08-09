type UserSettingsMode = "DEMO" | "LIVE";

interface UserSettings {
  mode: UserSettingsMode;
  demoApiKey: string | null;
  demoUsername: string | null;
  demoPassword: string | null;
  demoAccountId: string | null;
  demoWebhookSecret: string;
  liveApiKey: string | null;
  liveUsername: string | null;
  livePassword: string | null;
  liveAccountId: string | null;
  liveWebhookSecret: string;
  maximumOrderAgeInMinutes: number;
  maximumOpenPositions: number;
  maximumOpenPositionsAndPendingOrders: number;
  maximumAlertAgeInSeconds: number;
  avoidDividendDates: boolean;
  maximumTradesPerInstrumentPerDay: number;
  enforceMaximumOpenPositions: boolean;
  enforceMaximumOpenPositionsAndPendingOrders: boolean;
  enforceMaximumAlertAgeInSeconds: boolean;
  preventDuplicatePositionsForInstrument: boolean;
}
