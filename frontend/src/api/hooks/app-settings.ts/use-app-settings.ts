import { api } from "@/api/config";
import { useQuery } from "@tanstack/react-query";

const getAppSettings = async () => {
  const response = await api.get<AppSettings>("admin/settings");
  return response.json();
};

export const useAppSettings = () => {
  return useQuery({
    queryKey: ["app-settings"],
    queryFn: getAppSettings,
  });
};
