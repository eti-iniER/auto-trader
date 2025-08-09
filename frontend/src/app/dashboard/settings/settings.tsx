import { useLogout } from "@/api/hooks/authentication/use-logout";
import { useNewWebhookSecret } from "@/api/hooks/user-settings/use-new-webhook-secret";
import { useUpdateUserSettings } from "@/api/hooks/user-settings/use-update-user-settings";
import { PageHeader } from "@/components/page-header";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Form } from "@/components/ui/form";
import { LoaderWrapper } from "@/components/ui/loader-wrapper";
import { useDashboardContext } from "@/hooks/contexts/use-dashboard-context";
import { useModal } from "@/hooks/use-modal";
import { paths } from "@/paths";
import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { FormProvider, useForm } from "react-hook-form";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { settingsSchema, type SettingsFormData } from "./schema";
import {
  AppModeSection,
  IGCredentialsSection,
  TradingRulesSection,
} from "./sections";

export const Settings = () => {
  const { settings } = useDashboardContext();
  const updateSettings = useUpdateUserSettings();
  const newWebhookSecret = useNewWebhookSecret();
  const logoutMutation = useLogout();
  const navigate = useNavigate();
  const webhookModal = useModal();
  const [pendingData, setPendingData] = useState<SettingsFormData | null>(null);

  const form = useForm<SettingsFormData>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      mode: settings.mode,
      demoApiKey: settings.demoApiKey || "",
      demoUsername: settings.demoUsername || "",
      demoPassword: settings.demoPassword || "",
      demoAccountId: settings.demoAccountId || "",
      demoWebhookSecret: settings.demoWebhookSecret,
      liveApiKey: settings.liveApiKey || "",
      liveUsername: settings.liveUsername || "",
      livePassword: settings.livePassword || "",
      liveAccountId: settings.liveAccountId || "",
      liveWebhookSecret: settings.liveWebhookSecret,
      maximumOrderAgeInMinutes: settings.maximumOrderAgeInMinutes,
      maximumOpenPositions: settings.maximumOpenPositions,
      maximumOpenPositionsAndPendingOrders:
        settings.maximumOpenPositionsAndPendingOrders,
      maximumAlertAgeInSeconds: settings.maximumAlertAgeInSeconds,
      avoidDividendDates: settings.avoidDividendDates,
      maximumTradesPerInstrumentPerDay:
        settings.maximumTradesPerInstrumentPerDay,
      enforceMaximumOpenPositions: settings.enforceMaximumOpenPositions,
      enforceMaximumOpenPositionsAndPendingOrders:
        settings.enforceMaximumOpenPositionsAndPendingOrders,
      enforceMaximumAlertAgeInSeconds: settings.enforceMaximumAlertAgeInSeconds,
      preventDuplicatePositionsForInstrument:
        settings.preventDuplicatePositionsForInstrument,
    },
    disabled: updateSettings.isPending,
  });

  const onSubmit = (data: SettingsFormData) => {
    const webhookSecretsChanged =
      data.demoWebhookSecret !== settings.demoWebhookSecret ||
      data.liveWebhookSecret !== settings.liveWebhookSecret;

    if (webhookSecretsChanged) {
      setPendingData(data);
      webhookModal.openModal();
      return;
    }

    processUpdate(data);
  };

  const processUpdate = (data: SettingsFormData) => {
    const processedData: UserSettings = {
      mode: data.mode,
      demoApiKey: data.demoApiKey || null,
      demoUsername: data.demoUsername || null,
      demoPassword: data.demoPassword || null,
      demoAccountId: data.demoAccountId || null,
      demoWebhookSecret: data.demoWebhookSecret,
      liveApiKey: data.liveApiKey || null,
      liveUsername: data.liveUsername || null,
      livePassword: data.livePassword || null,
      liveAccountId: data.liveAccountId || null,
      liveWebhookSecret: data.liveWebhookSecret,
      maximumOrderAgeInMinutes: data.maximumOrderAgeInMinutes,
      maximumOpenPositions: data.maximumOpenPositions,
      maximumOpenPositionsAndPendingOrders:
        data.maximumOpenPositionsAndPendingOrders,
      maximumAlertAgeInSeconds: data.maximumAlertAgeInSeconds,
      avoidDividendDates: data.avoidDividendDates,
      maximumTradesPerInstrumentPerDay: data.maximumTradesPerInstrumentPerDay,
      enforceMaximumOpenPositions: data.enforceMaximumOpenPositions,
      enforceMaximumOpenPositionsAndPendingOrders:
        data.enforceMaximumOpenPositionsAndPendingOrders,
      enforceMaximumAlertAgeInSeconds: data.enforceMaximumAlertAgeInSeconds,
      preventDuplicatePositionsForInstrument:
        data.preventDuplicatePositionsForInstrument,
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

  const handleRotateWebhookSecret = (
    fieldName: "demoWebhookSecret" | "liveWebhookSecret",
  ) => {
    newWebhookSecret.mutate(undefined, {
      onSuccess: (response) => {
        form.setValue(fieldName, response.secret);
        toast.success("Webhook secret rotated successfully!");
      },
      onError: (error) => {
        toast.error("Failed to rotate webhook secret", {
          description: error.message || "An unexpected error occurred.",
        });
      },
    });
  };

  const handleConfirmWebhookUpdate = () => {
    if (pendingData) {
      processUpdate(pendingData);
      webhookModal.closeModal();
      setPendingData(null);
    }
  };

  const handleCancelWebhookUpdate = () => {
    webhookModal.closeModal();
    setPendingData(null);
  };

  return (
    <div className="flex-1 p-8">
      <PageHeader
        title="Settings"
        description="Manage user-specific app settings and configurations"
      />

      <div className="mt-8 w-full">
        <FormProvider {...form}>
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

              <AppModeSection updateSettings={updateSettings} />

              <IGCredentialsSection
                newWebhookSecret={newWebhookSecret}
                onRotateWebhookSecret={handleRotateWebhookSecret}
              />

              <TradingRulesSection />

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
        </FormProvider>
      </div>

      <Dialog open={webhookModal.isOpen} onOpenChange={webhookModal.closeModal}>
        <DialogContent showCloseButton={false}>
          <DialogHeader>
            <DialogTitle>Update webhook secret</DialogTitle>
            <DialogDescription>
              Since you rotated your webhook secret, you will have to update the
              webhook secret in the TradingView webhook body as well.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={handleCancelWebhookUpdate}
              disabled={updateSettings.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={handleConfirmWebhookUpdate}
              disabled={updateSettings.isPending}
            >
              <LoaderWrapper isLoading={updateSettings.isPending}>
                Yes, I understand
              </LoaderWrapper>
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
