import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { LoaderWrapper } from "@/components/ui/loader-wrapper";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { RotateCcw, Copy } from "lucide-react";
import { useFormContext } from "react-hook-form";
import { copyToClipboard } from "@/lib/utils";
import type { SettingsFormData } from "../schema";
import type { NewWebhookSecretMutationType } from "../types";

interface IGCredentialsSectionProps {
  newWebhookSecret: NewWebhookSecretMutationType;
  onRotateWebhookSecret: (
    fieldName: "demoWebhookSecret" | "liveWebhookSecret",
  ) => void;
}

export const IGCredentialsSection = ({
  newWebhookSecret,
  onRotateWebhookSecret,
}: IGCredentialsSectionProps) => {
  const { control } = useFormContext<SettingsFormData>();

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg leading-none font-semibold">IG credentials</h3>
        <p className="text-muted-foreground mt-1.5 text-sm">
          Configure your IG trading account credentials for demo and live
          trading
        </p>
      </div>

      {/* Demo credentials */}
      <div className="bg-card text-card-foreground rounded-lg border p-6 shadow-xs">
        <div className="mb-6">
          <h4 className="text-base leading-none font-medium">
            Demo credentials
          </h4>
          <p className="text-muted-foreground mt-1.5 text-sm">
            Configure your demo IG trading account credentials for testing and
            simulation
          </p>
        </div>
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2">
            <FormField
              control={control}
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

            <FormField
              control={control}
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
          </div>

          <div className="grid gap-4 md:grid-cols-1">
            <FormField
              control={control}
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
          </div>

          <div className="grid gap-4 md:grid-cols-1">
            <FormField
              control={control}
              name="demoAccountId"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Account ID</FormLabel>
                  <FormDescription>
                    The ID of the account (either spreadbet or CFD) to be used
                    for trading
                  </FormDescription>
                  <FormControl>
                    <Input
                      type="text"
                      placeholder="Enter demo account ID"
                      autoComplete="off"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <div className="grid gap-4 md:grid-cols-1">
            <FormField
              control={control}
              name="demoWebhookSecret"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Webhook secret</FormLabel>
                  <FormDescription>
                    Unique key used to verify the origin of the webhook
                  </FormDescription>
                  <FormControl>
                    <div className="flex gap-2">
                      <Input
                        type="text"
                        placeholder="my-demo-webhook-secret-123"
                        autoComplete="off"
                        {...field}
                        className="flex-1"
                      />
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              type="button"
                              variant="outline"
                              onClick={() => copyToClipboard(field.value || "")}
                              disabled={!field.value}
                              className="h-9.4 w-10 shrink-0 p-0"
                            >
                              <Copy className="h-4 w-4" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>Copy secret</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              type="button"
                              variant="default"
                              onClick={() =>
                                onRotateWebhookSecret("demoWebhookSecret")
                              }
                              disabled={newWebhookSecret.isPending}
                              className="h-9.4 w-10 shrink-0 p-0"
                            >
                              <LoaderWrapper
                                isLoading={newWebhookSecret.isPending}
                              >
                                <RotateCcw className="h-4 w-4" />
                              </LoaderWrapper>
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>Rotate secret</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
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
            Configure your live IG trading account credentials for real trading
          </p>
        </div>
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2">
            <FormField
              control={control}
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

            <FormField
              control={control}
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
          </div>

          <div className="grid gap-4 md:grid-cols-1">
            <FormField
              control={control}
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
          </div>

          <div className="grid gap-4 md:grid-cols-1">
            <FormField
              control={control}
              name="liveAccountId"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Account ID</FormLabel>
                  <FormDescription>
                    The ID of the account (either spreadbet or CFD) to be used
                    for trading
                  </FormDescription>
                  <FormControl>
                    <Input
                      type="text"
                      placeholder="Enter live account ID"
                      autoComplete="off"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <div className="grid gap-4 md:grid-cols-1">
            <FormField
              control={control}
              name="liveWebhookSecret"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Webhook secret</FormLabel>
                  <FormDescription>
                    Unique key used to verify the origin of the webhook
                  </FormDescription>
                  <FormControl>
                    <div className="flex gap-2">
                      <Input
                        type="text"
                        placeholder="my-live-webhook-secret-123"
                        {...field}
                        className="flex-1"
                      />
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              type="button"
                              variant="outline"
                              onClick={() => copyToClipboard(field.value || "")}
                              disabled={!field.value}
                              className="h-9.4 w-10 shrink-0 p-0"
                            >
                              <Copy className="h-4 w-4" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>Copy secret</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              type="button"
                              variant="default"
                              onClick={() =>
                                onRotateWebhookSecret("liveWebhookSecret")
                              }
                              disabled={newWebhookSecret.isPending}
                              className="h-9.4 w-10 shrink-0 p-0"
                            >
                              <LoaderWrapper
                                isLoading={newWebhookSecret.isPending}
                              >
                                <RotateCcw className="h-4 w-4" />
                              </LoaderWrapper>
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>Rotate secret</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
