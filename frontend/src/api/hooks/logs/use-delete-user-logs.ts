import { api } from "@/api/config";
import { useMutation, useQueryClient } from "@tanstack/react-query";

const deleteUserLogs = async (userId: string) => {
  const response = await api.delete<SimpleResponse>(`logs/${userId}`);
  return response.json();
};

export const useDeleteUserLogs = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteUserLogs,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["logs"] });
    },
  });
};
