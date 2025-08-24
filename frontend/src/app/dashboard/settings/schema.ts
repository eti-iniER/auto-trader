import { z } from "zod";

export const settingsSchema = z.object({
  mode: z.enum(["DEMO", "LIVE"], {
    message: "Please select a trading mode",
  }),
  // Demo credentials
  demoApiKey: z.string().optional(),
  demoUsername: z.string().optional(),
  demoPassword: z.string().optional(),
  demoAccountId: z.string().optional(),
  demoWebhookSecret: z.string(),
  // Live credentials
  liveApiKey: z.string().optional(),
  liveUsername: z.string().optional(),
  livePassword: z.string().optional(),
  liveAccountId: z.string().optional(),
  liveWebhookSecret: z.string(),
  // Trading settings
  orderType: z.enum(["LIMIT", "MARKET"], {
    message: "Please select an order type",
  }),
  instrumentTradeCooldownPeriodInHours: z.number().int().min(0).max(120),
  maximumOrderAgeInMinutes: z.number().int().min(1).max(1440),
  maximumOpenPositions: z.number().int().min(0).max(100),
  maximumOpenPositionsAndPendingOrders: z.number().int().min(0).max(100),
  maximumAlertAgeInSeconds: z.number().int().min(1).max(86400),
  avoidDividendDates: z.boolean(),
  enforceMaximumOpenPositions: z.boolean(),
  enforceMaximumOpenPositionsAndPendingOrders: z.boolean(),
  enforceMaximumAlertAgeInSeconds: z.boolean(),
  preventDuplicatePositionsForInstrument: z.boolean(),
});

export type SettingsFormData = z.infer<typeof settingsSchema>;
