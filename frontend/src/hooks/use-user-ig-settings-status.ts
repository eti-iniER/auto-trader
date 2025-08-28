export const useUserIGSettingsStatus = (settings: UserSettings) => {
  const demoSettingsComplete =
    settings.demoApiKey &&
    settings.demoPassword &&
    settings.demoUsername &&
    settings.demoAccountId;
  const liveSettingsComplete =
    settings.liveApiKey &&
    settings.livePassword &&
    settings.liveUsername &&
    settings.liveAccountId;

  if (settings.mode == "DEMO") {
    return demoSettingsComplete ? "complete" : "incomplete";
  } else {
    return liveSettingsComplete ? "complete" : "incomplete";
  }
};
