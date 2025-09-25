import { api } from "@/api/config";
import { useMutation, useQueryClient } from "@tanstack/react-query";

const deleteLogs = async () => {
  const response = await api.delete<SimpleResponse>(`logs`);
  return response.json();
};

export const useDeleteLogs = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteLogs,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["logs"] });
    },
  });
};
