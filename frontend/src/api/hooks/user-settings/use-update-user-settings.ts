import { api } from "@/api/config";
import { useMutation, useQueryClient } from "@tanstack/react-query";

const updateUserSettings = async (settings: UserSettings) => {
  const response = await api.patch<UserSettings>("users/me/settings", {
    json: settings,
  });
  return response.json();
};

export const useUpdateUserSettings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateUserSettings,
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
  });
};
