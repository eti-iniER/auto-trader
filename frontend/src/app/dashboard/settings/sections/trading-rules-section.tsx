import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  SegmentedControl,
  SegmentedControlItem,
} from "@/components/ui/segmented-control";
import { Switch } from "@/components/ui/switch";
import { useFormContext } from "react-hook-form";
import type { SettingsFormData } from "../schema";

export const TradingRulesSection = () => {
  const { control } = useFormContext<SettingsFormData>();

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg leading-none font-semibold">Trading rules</h3>
        <p className="text-muted-foreground mt-1.5 text-sm">
          Configure timing constraints, position limits, and risk management
          rules
        </p>
      </div>

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
          <FormField
            control={control}
            name="orderType"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Order type</FormLabel>
                <FormControl>
                  <SegmentedControl
                    value={field.value}
                    onValueChange={field.onChange}
                    variant="default"
                    size="lg"
                    className="h-fit min-h-16"
                  >
                    <SegmentedControlItem
                      value="LIMIT"
                      selectedClassName="bg-slate-600 text-white shadow-sm hover:bg-slate-800"
                      unselectedClassName="text-muted-foreground hover:text-foreground hover:bg-muted/50"
                    >
                      <div className="text-center">
                        <div className="font-medium">Limit</div>
                        <div className="text-xs opacity-90">
                          Execute at specific price or better
                        </div>
                      </div>
                    </SegmentedControlItem>
                    <SegmentedControlItem
                      value="MARKET"
                      selectedClassName="bg-slate-600 text-white shadow-sm hover:bg-slate-800"
                      unselectedClassName="text-muted-foreground hover:text-foreground hover:bg-muted/50"
                    >
                      <div className="text-center">
                        <div className="font-medium">Market</div>
                        <div className="text-xs opacity-90">
                          Execute immediately at current price
                        </div>
                      </div>
                    </SegmentedControlItem>
                  </SegmentedControl>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <div className="grid gap-6 md:grid-cols-2">
            <FormField
              control={control}
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
                          e.target.value ? parseInt(e.target.value) : undefined,
                        )
                      }
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={control}
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
                          e.target.value ? parseInt(e.target.value) : undefined,
                        )
                      }
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={control}
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
                          e.target.value ? parseInt(e.target.value) : undefined,
                        )
                      }
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={control}
              name="maximumOpenPositionsAndPendingOrders"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Maximum open positions + pending orders</FormLabel>
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
                          e.target.value ? parseInt(e.target.value) : undefined,
                        )
                      }
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={control}
              name="maximumTradesPerInstrumentPerDay"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Maximum trades per instrument per day</FormLabel>
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
                          e.target.value ? parseInt(e.target.value) : undefined,
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
              control={control}
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
              control={control}
              name="preventDuplicatePositionsForInstrument"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">
                      Block if position already exists
                    </FormLabel>
                    <FormDescription className="text-muted-foreground text-sm">
                      Prevents duplicate positions for the same instrument
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
              control={control}
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
              control={control}
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
              control={control}
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
  );
};
