type UserSettingsMode = "DEMO" | "LIVE";

interface UserSettings {
  mode: UserSettingsMode;
  demoApiKey: string | null;
  demoUsername: string | null;
  demoPassword: string | null;
  demoWebhookUrl: string | null;
  liveApiKey: string | null;
  liveUsername: string | null;
  livePassword: string | null;
  liveWebhookUrl: string | null;
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
