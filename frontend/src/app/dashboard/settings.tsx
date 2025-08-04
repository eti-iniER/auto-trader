import { useUpdateUserSettings } from "@/api/hooks/user-settings/use-update-user-settings";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { LoaderWrapper } from "@/components/ui/loader-wrapper";
import {
  SegmentedControl,
  SegmentedControlItem,
} from "@/components/ui/segmented-control";
import { useDashboardContext } from "@/hooks/contexts/use-dashboard-context";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
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
});

type SettingsFormData = z.infer<typeof settingsSchema>;

export const Settings = () => {
  const { settings } = useDashboardContext();
  const updateSettings = useUpdateUserSettings();

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
    };

    updateSettings.mutate(processedData, {
      onSuccess: () => {
        toast.success("Settings updated successfully!");
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
            <div className="flex justify-end">
              <Button
                type="submit"
                disabled={updateSettings.isPending}
                className="min-w-32"
              >
                <LoaderWrapper isLoading={updateSettings.isPending}>
                  Update settings
                </LoaderWrapper>
              </Button>
            </div>

            <div className="bg-card text-card-foreground rounded-lg border p-6 shadow-xs">
              <div className="mb-6">
                <h3 className="text-lg leading-none font-semibold">Mode</h3>
                <p className="text-muted-foreground mt-1.5 text-sm">
                  Select whether to use demo or live trading credentials
                </p>
              </div>
              <FormField
                control={form.control}
                name="mode"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Mode</FormLabel>
                    <FormControl>
                      <SegmentedControl
                        value={field.value}
                        onValueChange={field.onChange}
                        disabled={updateSettings.isPending}
                        variant="colored"
                      >
                        <SegmentedControlItem value="DEMO">
                          Demo
                        </SegmentedControlItem>
                        <SegmentedControlItem value="LIVE">
                          Live
                        </SegmentedControlItem>
                      </SegmentedControl>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="bg-card text-card-foreground rounded-lg border p-6 shadow-xs">
              <div className="mb-6">
                <h3 className="text-lg leading-none font-semibold">
                  Demo credentials
                </h3>
                <p className="text-muted-foreground mt-1.5 text-sm">
                  Configure your demo IG trading account credentials for testing
                  and simulation
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

            <div className="bg-card text-card-foreground rounded-lg border p-6 shadow-xs">
              <div className="mb-6">
                <h3 className="text-lg leading-none font-semibold">
                  Live credentials
                </h3>
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
          </form>
        </Form>
      </div>
    </div>
  );
};
