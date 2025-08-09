import type { UseMutationResult } from "@tanstack/react-query";

export type UpdateSettingsMutationType = UseMutationResult<
  UserSettings,
  Error,
  UserSettings,
  unknown
>;

export type NewWebhookSecretMutationType = UseMutationResult<
  { secret: string },
  Error,
  void,
  unknown
>;

export interface WebhookSecretResponse {
  secret: string;
}
