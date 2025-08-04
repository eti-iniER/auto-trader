import { api } from "@/api/config";
import { useQuery } from "@tanstack/react-query";

const getUserSettings = async () => {
  const response = await api.get<UserSettings>("users/me/settings");
  return response.json();
};

export const useUserSettings = () => {
  return useQuery({
    queryKey: ["settings"],
    queryFn: getUserSettings,
  });
};
