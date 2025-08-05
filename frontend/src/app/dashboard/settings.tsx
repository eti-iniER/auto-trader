import { useLogout } from "@/api/hooks/authentication/use-logout";
import { useUpdateUserSettings } from "@/api/hooks/user-settings/use-update-user-settings";
import { PageHeader } from "@/components/page-header";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { LoaderWrapper } from "@/components/ui/loader-wrapper";
import {
  SegmentedControl,
  SegmentedControlItem,
} from "@/components/ui/segmented-control";
import { Switch } from "@/components/ui/switch";
import { defaultUserSettings } from "@/constants/defaults";
import { useDashboardContext } from "@/hooks/contexts/use-dashboard-context";
import { paths } from "@/paths";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { z } from "zod";

const settingsSchema = z.object({
  mode: z.enum(["DEMO", "LIVE"], {
    message: "Please select a trading mode",
  }),
  // Demo credentials
  demoApiKey: z.string().optional(),
  demoUsername: z.string().optional(),
  demoPassword: z.string().optional(),
  demoWebhookUrl: z.url().optional().or(z.literal("")),
  // Live credentials
  liveApiKey: z.string().optional(),
  liveUsername: z.string().optional(),
  livePassword: z.string().optional(),
  liveWebhookUrl: z.string().url().optional().or(z.literal("")),
  // Trading settings
  maximumOrderAgeInMinutes: z.number().int().min(1).max(1440).optional(),
  maximumOpenPositions: z.number().int().min(0).max(100).optional(),
  maximumOpenPositionsAndPendingOrders: z
    .number()
    .int()
    .min(0)
    .max(100)
    .optional(),
  maximumAlertAgeInSeconds: z.number().int().min(1).max(86400).optional(),
  avoidDividendDates: z.boolean().optional(),
  maximumTradesPerInstrumentPerDay: z.number().int().min(0).max(100).optional(),
  enforceMaximumOpenPositions: z.boolean().optional(),
  enforceMaximumOpenPositionsAndPendingOrders: z.boolean().optional(),
  enforceMaximumAlertAgeInSeconds: z.boolean().optional(),
  preventDuplicatePositionsForInstrument: z.boolean().optional(),
});

type SettingsFormData = z.infer<typeof settingsSchema>;

export const Settings = () => {
  const { settings } = useDashboardContext();
  const updateSettings = useUpdateUserSettings();
  const logoutMutation = useLogout();
  const navigate = useNavigate();

  const form = useForm<SettingsFormData>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      mode: settings.mode,
      demoApiKey: settings.demoApiKey || "",
      demoUsername: settings.demoUsername || "",
      demoPassword: settings.demoPassword || "",
      demoWebhookUrl: settings.demoWebhookUrl || "",
      liveApiKey: settings.liveApiKey || "",
      liveUsername: settings.liveUsername || "",
      livePassword: settings.livePassword || "",
      liveWebhookUrl: settings.liveWebhookUrl || "",
      maximumOrderAgeInMinutes:
        settings.maximumOrderAgeInMinutes ||
        defaultUserSettings.maximumOrderAgeInMinutes,
      maximumOpenPositions:
        settings.maximumOpenPositions ||
        defaultUserSettings.maximumOpenPositions,
      maximumOpenPositionsAndPendingOrders:
        settings.maximumOpenPositionsAndPendingOrders ||
        defaultUserSettings.maximumOpenPositionsAndPendingOrders,
      maximumAlertAgeInSeconds:
        settings.maximumAlertAgeInSeconds ||
        defaultUserSettings.maximumAlertAgeInSeconds,
      avoidDividendDates:
        settings.avoidDividendDates ?? defaultUserSettings.avoidDividendDates,
      maximumTradesPerInstrumentPerDay:
        settings.maximumTradesPerInstrumentPerDay ||
        defaultUserSettings.maximumTradesPerInstrumentPerDay,
      enforceMaximumOpenPositions:
        settings.enforceMaximumOpenPositions ??
        defaultUserSettings.enforceMaximumOpenPositions,
      enforceMaximumOpenPositionsAndPendingOrders:
        settings.enforceMaximumOpenPositionsAndPendingOrders ??
        defaultUserSettings.enforceMaximumOpenPositionsAndPendingOrders,
      enforceMaximumAlertAgeInSeconds:
        settings.enforceMaximumAlertAgeInSeconds ??
        defaultUserSettings.enforceMaximumAlertAgeInSeconds,
      preventDuplicatePositionsForInstrument:
        settings.preventDuplicatePositionsForInstrument ??
        defaultUserSettings.preventDuplicatePositionsForInstrument,
    },
    disabled: updateSettings.isPending,
  });

  const onSubmit = (data: SettingsFormData) => {
    const processedData: UserSettings = {
      mode: data.mode,
      demoApiKey: data.demoApiKey || null,
      demoUsername: data.demoUsername || null,
      demoPassword: data.demoPassword || null,
      demoWebhookUrl: data.demoWebhookUrl || null,
      liveApiKey: data.liveApiKey || null,
      liveUsername: data.liveUsername || null,
      livePassword: data.livePassword || null,
      liveWebhookUrl: data.liveWebhookUrl || null,
      maximumOrderAgeInMinutes:
        data.maximumOrderAgeInMinutes ||
        defaultUserSettings.maximumOrderAgeInMinutes,
      maximumOpenPositions:
        data.maximumOpenPositions || defaultUserSettings.maximumOpenPositions,
      maximumOpenPositionsAndPendingOrders:
        data.maximumOpenPositionsAndPendingOrders ||
        defaultUserSettings.maximumOpenPositionsAndPendingOrders,
      maximumAlertAgeInSeconds:
        data.maximumAlertAgeInSeconds ||
        defaultUserSettings.maximumAlertAgeInSeconds,
      avoidDividendDates:
        data.avoidDividendDates ?? defaultUserSettings.avoidDividendDates,
      maximumTradesPerInstrumentPerDay:
        data.maximumTradesPerInstrumentPerDay ||
        defaultUserSettings.maximumTradesPerInstrumentPerDay,
      enforceMaximumOpenPositions:
        data.enforceMaximumOpenPositions ??
        defaultUserSettings.enforceMaximumOpenPositions,
      enforceMaximumOpenPositionsAndPendingOrders:
        data.enforceMaximumOpenPositionsAndPendingOrders ??
        defaultUserSettings.enforceMaximumOpenPositionsAndPendingOrders,
      enforceMaximumAlertAgeInSeconds:
        data.enforceMaximumAlertAgeInSeconds ??
        defaultUserSettings.enforceMaximumAlertAgeInSeconds,
      preventDuplicatePositionsForInstrument:
        data.preventDuplicatePositionsForInstrument ??
        defaultUserSettings.preventDuplicatePositionsForInstrument,
    };

    updateSettings.mutate(processedData, {
      onSuccess: () => {
        toast.success("Settings updated successfully!");
        logoutMutation.mutate(undefined, {
          onSettled: () => {
            navigate(paths.authentication.LOGIN);
          },
        });
      },
      onError: (error) => {
        toast.error("Failed to update settings", {
          description: error.message || "An unexpected error occurred.",
        });
      },
    });
  };

  return (
    <div className="flex-1 p-8">
      <PageHeader
        title="Settings"
        description="Manage user-specific app settings and configurations"
      />

      <div className="mt-8 w-full">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <Alert className="border-amber-200 bg-amber-50">
              <AlertDescription className="text-amber-800">
                <span>
                  <span className="font-bold">Note:</span> You will be logged
                  out after updating your settings.
                </span>
              </AlertDescription>
            </Alert>

            {/* App mode section */}
            <div className="space-y-4">
              <div>
                <h3 className="text-lg leading-none font-semibold">App mode</h3>
                <p className="text-muted-foreground mt-1.5 text-sm">
                  Select whether to use demo or live trading credentials
                </p>
              </div>
              <div className="bg-card text-card-foreground rounded-lg border p-6 shadow-xs">
                <FormField
                  control={form.control}
                  name="mode"
                  render={({ field }) => (
                    <FormItem>
                      <FormControl>
                        <SegmentedControl
                          value={field.value}
                          onValueChange={field.onChange}
                          disabled={updateSettings.isPending}
                          variant="default"
                        >
                          <SegmentedControlItem
                            value="DEMO"
                            selectedClassName="bg-green-700 text-white shadow-sm hover:bg-green-800"
                            unselectedClassName="text-muted-foreground hover:text-foreground hover:bg-muted/50"
                          >
                            Demo
                          </SegmentedControlItem>
                          <SegmentedControlItem
                            value="LIVE"
                            selectedClassName="bg-red-600 text-white shadow-sm hover:bg-red-700"
                            unselectedClassName="text-muted-foreground hover:text-foreground hover:bg-muted/50"
                          >
                            Live
                          </SegmentedControlItem>
                        </SegmentedControl>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </div>

            {/* IG credentials section */}
            <div className="space-y-6">
              <div>
                <h3 className="text-lg leading-none font-semibold">
                  IG credentials
                </h3>
                <p className="text-muted-foreground mt-1.5 text-sm">
                  Configure your IG trading account credentials for demo and
                  live trading
                </p>
              </div>

              {/* Demo credentials */}
              <div className="bg-card text-card-foreground rounded-lg border p-6 shadow-xs">
                <div className="mb-6">
                  <h4 className="text-base leading-none font-medium">
                    Demo credentials
                  </h4>
                  <p className="text-muted-foreground mt-1.5 text-sm">
                    Configure your demo IG trading account credentials for
                    testing and simulation
                  </p>
                </div>
                <div className="space-y-6">
                  <div className="grid gap-4 md:grid-cols-2">
                    <FormField
                      control={form.control}
                      name="demoApiKey"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>API key</FormLabel>
                          <FormControl>
                            <Input
                              type="text"
                              placeholder="Enter demo API key"
                              autoComplete="off"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="demoUsername"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Username</FormLabel>
                          <FormControl>
                            <Input
                              type="text"
                              placeholder="Enter demo username"
                              autoComplete="off"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <div className="grid gap-4 md:grid-cols-2">
                    <FormField
                      control={form.control}
                      name="demoPassword"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Password</FormLabel>
                          <FormControl>
                            <Input
                              type="text"
                              placeholder="Enter demo password"
                              autoComplete="off"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="demoWebhookUrl"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Webhook URL</FormLabel>
                          <FormControl>
                            <Input
                              type="url"
                              placeholder="https://example.com/webhook"
                              autoComplete="off"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </div>
              </div>

              {/* Live credentials */}
              <div className="bg-card text-card-foreground rounded-lg border p-6 shadow-xs">
                <div className="mb-6">
                  <h4 className="text-base leading-none font-medium">
                    Live credentials
                  </h4>
                  <p className="text-muted-foreground mt-1.5 text-sm">
                    Configure your live IG trading account credentials for real
                    trading
                  </p>
                </div>
                <div className="space-y-6">
                  <div className="grid gap-4 md:grid-cols-2">
                    <FormField
                      control={form.control}
                      name="liveApiKey"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>API key</FormLabel>
                          <FormControl>
                            <Input
                              type="password"
                              placeholder="Enter live API key"
                              autoComplete="off"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="liveUsername"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Username</FormLabel>
                          <FormControl>
                            <Input
                              type="text"
                              placeholder="Enter live username"
                              autoComplete="off"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <div className="grid gap-4 md:grid-cols-2">
                    <FormField
                      control={form.control}
                      name="livePassword"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Password</FormLabel>
                          <FormControl>
                            <Input
                              type="password"
                              placeholder="Enter live password"
                              autoComplete="off"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="liveWebhookUrl"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Webhook URL</FormLabel>
                          <FormControl>
                            <Input
                              type="url"
                              placeholder="https://example.com/webhook"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Trading rules section */}
            <div className="space-y-6">
              <div>
                <h3 className="text-lg leading-none font-semibold">
                  Trading rules
                </h3>
                <p className="text-muted-foreground mt-1.5 text-sm">
                  Configure timing constraints, position limits, and risk
                  management rules
                </p>
              </div>

              {/* Timing & limits */}
              <div className="bg-card text-card-foreground rounded-lg border p-6 shadow-xs">
                <div className="mb-6">
                  <h4 className="text-base leading-none font-medium">
                    Timing & limits
                  </h4>
                  <p className="text-muted-foreground mt-1.5 text-sm">
                    Configure timing constraints and position limits for trading
                  </p>
                </div>
                <div className="space-y-6">
                  <div className="grid gap-6 md:grid-cols-2">
                    <FormField
                      control={form.control}
                      name="maximumOrderAgeInMinutes"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Maximum order age (minutes)</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              placeholder="10"
                              min="1"
                              max="1440"
                              {...field}
                              value={field.value || ""}
                              onChange={(e) =>
                                field.onChange(
                                  e.target.value
                                    ? parseInt(e.target.value)
                                    : undefined,
                                )
                              }
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="maximumAlertAgeInSeconds"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Maximum alert age (seconds)</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              placeholder="60"
                              min="1"
                              max="86400"
                              {...field}
                              value={field.value || ""}
                              onChange={(e) =>
                                field.onChange(
                                  e.target.value
                                    ? parseInt(e.target.value)
                                    : undefined,
                                )
                              }
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="maximumOpenPositions"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Maximum open positions</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              placeholder="10"
                              min="0"
                              max="100"
                              {...field}
                              value={field.value || ""}
                              onChange={(e) =>
                                field.onChange(
                                  e.target.value
                                    ? parseInt(e.target.value)
                                    : undefined,
                                )
                              }
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="maximumOpenPositionsAndPendingOrders"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>
                            Maximum open positions + pending orders
                          </FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              placeholder="10"
                              min="0"
                              max="100"
                              {...field}
                              value={field.value || ""}
                              onChange={(e) =>
                                field.onChange(
                                  e.target.value
                                    ? parseInt(e.target.value)
                                    : undefined,
                                )
                              }
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="maximumTradesPerInstrumentPerDay"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>
                            Maximum trades per instrument per day
                          </FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              placeholder="1"
                              min="0"
                              max="100"
                              {...field}
                              value={field.value || ""}
                              onChange={(e) =>
                                field.onChange(
                                  e.target.value
                                    ? parseInt(e.target.value)
                                    : undefined,
                                )
                              }
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </div>
              </div>

              {/* Risk management */}
              <div className="bg-card text-card-foreground rounded-lg border p-6 shadow-xs">
                <div className="mb-6">
                  <h4 className="text-base leading-none font-medium">
                    Risk management
                  </h4>
                  <p className="text-muted-foreground mt-1.5 text-sm">
                    Configure risk management rules and trading restrictions
                  </p>
                </div>
                <div className="space-y-6">
                  <div className="grid gap-6">
                    <FormField
                      control={form.control}
                      name="avoidDividendDates"
                      render={({ field }) => (
                        <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                          <div className="space-y-0.5">
                            <FormLabel className="text-base">
                              Avoid dividend dates
                            </FormLabel>
                            <FormDescription className="text-muted-foreground text-sm">
                              Prevent trading on or around dividend dates
                            </FormDescription>
                          </div>
                          <FormControl>
                            <Switch
                              checked={field.value}
                              onCheckedChange={field.onChange}
                            />
                          </FormControl>
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="preventDuplicatePositionsForInstrument"
                      render={({ field }) => (
                        <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                          <div className="space-y-0.5">
                            <FormLabel className="text-base">
                              Block if position already exists
                            </FormLabel>
                            <FormDescription className="text-muted-foreground text-sm">
                              Prevents duplicate positions for the same
                              instrument
                            </FormDescription>
                          </div>
                          <FormControl>
                            <Switch
                              checked={field.value}
                              onCheckedChange={field.onChange}
                            />
                          </FormControl>
                        </FormItem>
                      )}
                    />
                  </div>
                </div>
              </div>

              {/* Enforcement rules */}
              <div className="bg-card text-card-foreground rounded-lg border p-6 shadow-xs">
                <div className="mb-6">
                  <h4 className="text-base leading-none font-medium">
                    Enforcement rules
                  </h4>
                  <p className="text-muted-foreground mt-1.5 text-sm">
                    Control which limits and restrictions are actively enforced
                  </p>
                </div>
                <div className="space-y-6">
                  <div className="grid gap-6">
                    <FormField
                      control={form.control}
                      name="enforceMaximumOpenPositions"
                      render={({ field }) => (
                        <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                          <div className="space-y-0.5">
                            <FormLabel className="text-base">
                              Enforce maximum positions limit
                            </FormLabel>
                            <FormDescription className="text-muted-foreground text-sm">
                              Won't open more positions than allowed
                            </FormDescription>
                          </div>
                          <FormControl>
                            <Switch
                              checked={field.value}
                              onCheckedChange={field.onChange}
                            />
                          </FormControl>
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="enforceMaximumOpenPositionsAndPendingOrders"
                      render={({ field }) => (
                        <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                          <div className="space-y-0.5">
                            <FormLabel className="text-base">
                              Check total positions and orders
                            </FormLabel>
                            <FormDescription className="text-muted-foreground text-sm">
                              Limits total open positions + pending orders
                            </FormDescription>
                          </div>
                          <FormControl>
                            <Switch
                              checked={field.value}
                              onCheckedChange={field.onChange}
                            />
                          </FormControl>
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="enforceMaximumAlertAgeInSeconds"
                      render={({ field }) => (
                        <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                          <div className="space-y-0.5">
                            <FormLabel className="text-base">
                              Enforce alert age limit
                            </FormLabel>
                            <FormDescription className="text-muted-foreground text-sm">
                              Reject alerts that are too old
                            </FormDescription>
                          </div>
                          <FormControl>
                            <Switch
                              checked={field.value}
                              onCheckedChange={field.onChange}
                            />
                          </FormControl>
                        </FormItem>
                      )}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom update button */}
            <div className="flex justify-start pt-4">
              <Button
                type="submit"
                disabled={updateSettings.isPending}
                size="lg"
                className="min-w-40"
              >
                <LoaderWrapper isLoading={updateSettings.isPending}>
                  Update settings
                </LoaderWrapper>
              </Button>
            </div>
          </form>
        </Form>
      </div>
    </div>
  );
};
