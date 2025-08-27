import { api } from "@/api/config";
import { useMutation, useQueryClient } from "@tanstack/react-query";

const updateAppSettings = async (settings: AppSettings) => {
  const response = await api.patch<SimpleResponse>("admin/settings", {
    json: settings,
  });
  return response.json();
};

export const useUpdateAppSettings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateAppSettings,
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["app-settings"] });
    },
  });
};
