import { useUserSettings } from "@/api/hooks/user-settings/use-user-settings";
import { PageHeader } from "@/components/page-header";

export const Settings = () => {
  const { data: userSettings } = useUserSettings();

  console.log("User Settings:", userSettings);

  return (
    <div className="flex-1 p-8">
      <PageHeader
        title="Settings"
        description="Manage user-specific app settings and configurations"
      />
    </div>
  );
};
