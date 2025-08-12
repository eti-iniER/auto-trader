import { api } from "@/api/config";
import { useMutation, useQueryClient } from "@tanstack/react-query";

const logout = async () => {
  const response = await api.post("auth/logout");
  return response.json();
};

export const useLogout = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: logout,
    onSettled: () => {
      queryClient.clear();
    },
  });
};
