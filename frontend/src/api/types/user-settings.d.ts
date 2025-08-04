interface UserSettings {
  mode: "live" | "demo";
  demoApiKey: string | null;
  demoUsername: string | null;
  demoPassword: string | null;
  demoWebhookUrl: string | null;
  liveApiKey: string | null;
  liveUsername: string | null;
  livePassword: string | null;
  liveWebhookUrl: string | null;
}
