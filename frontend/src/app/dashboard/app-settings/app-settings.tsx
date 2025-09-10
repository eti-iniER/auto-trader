import { useUpdateAppSettings } from "@/api/hooks/app-settings.ts/use-update-app-settings";
import { useLogout } from "@/api/hooks/authentication/use-logout";
import { PageHeader } from "@/components/page-header";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import { LoaderWrapper } from "@/components/ui/loader-wrapper";
import { Switch } from "@/components/ui/switch";
import { useDashboard } from "@/hooks/contexts/use-dashboard";
import { paths } from "@/paths";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Navigate, useNavigate } from "react-router";
import { toast } from "sonner";
import { appSettingsSchema, type AppSettingsFormData } from "./schema";

export const AppSettings = () => {
  const { user, appSettings } = useDashboard();
  const updateAppSettings = useUpdateAppSettings();
  const navigate = useNavigate();
  const logout = useLogout();

  const form = useForm<AppSettingsFormData>({
    resolver: zodResolver(appSettingsSchema),
    defaultValues: {
      allowUserRegistration: appSettings.allowUserRegistration,
      allowMultipleAdmins: appSettings.allowMultipleAdmins,
    },
    disabled: updateAppSettings.isPending,
  });

  if (user.role !== "ADMIN") {
    return <Navigate to="/dashboard/overview" replace />;
  }

  const onSubmit = (data: AppSettingsFormData) => {
    updateAppSettings.mutate(data, {
      onSuccess: () => {
        toast.success("App settings updated successfully!");
        logout.mutate(undefined, {
          onSettled: () => {
            navigate(paths.authentication.LOGIN);
          },
        });
      },
      onError: (error) => {
        toast.error("Failed to update app settings", {
          description: error.message || "An unexpected error occurred.",
        });
      },
    });
  };

  return (
    <div className="flex h-full flex-col space-y-6 p-8">
      <PageHeader
        title="App settings"
        description="Manage global application settings"
      />

      <div className="w-full">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <Alert className="border-amber-200 bg-amber-50">
              <AlertDescription className="text-amber-800">
                <span>
                  <span className="font-bold">Note:</span> You will be logged
                  out after updating app settings.
                </span>
              </AlertDescription>
            </Alert>

            <div className="space-y-4">
              <div>
                <h3 className="text-lg leading-none font-semibold">
                  User settings
                </h3>
                <p className="text-muted-foreground mt-1.5 text-sm">
                  Control user registration and admin access
                </p>
              </div>

              <div className="bg-card text-card-foreground space-y-6 rounded-lg border p-6 shadow-xs">
                <FormField
                  control={form.control}
                  name="allowUserRegistration"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                      <div className="space-y-0.5">
                        <FormLabel className="text-base">
                          Allow user registration
                        </FormLabel>
                        <FormDescription className="text-muted-foreground text-sm">
                          Enable new users to register for accounts
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
                  name="allowMultipleAdmins"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                      <div className="space-y-0.5">
                        <FormLabel className="text-base">
                          Allow multiple admins
                        </FormLabel>
                        <FormDescription className="text-muted-foreground text-sm">
                          Permit more than one admin user in the system
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

            <div className="flex justify-start pt-4">
              <Button
                type="submit"
                disabled={updateAppSettings.isPending}
                size="lg"
                className="min-w-40"
              >
                <LoaderWrapper isLoading={updateAppSettings.isPending}>
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
