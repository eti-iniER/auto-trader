import {
  FormControl,
  FormField,
  FormItem,
  FormMessage,
} from "@/components/ui/form";
import {
  SegmentedControl,
  SegmentedControlItem,
} from "@/components/ui/segmented-control";
import { useFormContext } from "react-hook-form";
import type { SettingsFormData } from "../schema";
import type { UpdateSettingsMutationType } from "../types";

interface AppModeSectionProps {
  updateSettings: UpdateSettingsMutationType;
}

export const AppModeSection = ({ updateSettings }: AppModeSectionProps) => {
  const { control } = useFormContext<SettingsFormData>();

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg leading-none font-semibold">App mode</h3>
        <p className="text-muted-foreground mt-1.5 text-sm">
          Select whether to use demo or live trading credentials
        </p>
      </div>
      <div className="bg-card text-card-foreground rounded-lg border p-6 shadow-xs">
        <FormField
          control={control}
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
  );
};
